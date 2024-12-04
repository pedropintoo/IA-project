'''
 # @ Authors: 
 #  - Pedro Pinto (pmap@ua.pt)
 #  - Joao Pinto (jpapinto@ua.pt)
 #  - Guilherme Santos (gui.santos91@ua.pt)
 # @ Create Time: 2024-10-13
 '''
import asyncio
import getpass
import os
import websockets
import json
import logging
import random
from datetime import datetime, timedelta
from src.utils._consts import get_num_future_goals, get_future_goals_priority, get_future_goals_range, get_num_max_present_goals
import sys

## Search
from src.search.search_problem import SearchProblem
from src.search.search_tree import SearchTree
from src.snake_game import SnakeGame
from src.goal import Goal

## Mapping & Exploration
from src.matrix_operations import MatrixOperations
from src.mapping import Mapping

## Utils
from src.utils.logger import Logger, MAPPING_LEVEL
from src.utils.exceptions import TimeLimitExceeded
from consts import Tiles

DIRECTION_TO_KEY = {
    "NORTH": "w",
    "WEST":  "a",
    "SOUTH": "s",
    "EAST":  "d"
}

wslogger = logging.getLogger("websockets")
wslogger.setLevel(logging.INFO)

class Agent:
    """Autonomous AI client."""
    
    def __init__(self, server_address, agent_name):
        
        ## Utils
        print(f"Agent: {agent_name}")
        self.logger = Logger(f"[{agent_name}]", logFile=None)
        
        ## Activate the mapping level (comment the next line to disable mapping logging)
        # self.logger.activate_mapping()
        
        ## Disable logging (comment the next line to enable logging)
        self.logger.disable()
        
        self.server_address = server_address
        self.agent_name = agent_name
        self.websocket = None
        
        ## Defined by the start of the game
        self.mapping = None 
        self.fps = None
        self.timeout = None
        self.domain = None
        
        ## Action controller
        self.ts = None
        self.actions_plan = []
        self.action = None
        self.current_goals = []
        self.future_goals = []
        self.perfect_effects = False
        
    
    # ----- Main Loop -----
    
    async def close(self):
        """Close the websocket connection"""
        await self.websocket.close()
        self.logger.info("Websocket connection closed")
    
    async def run(self):
        """Start the execution of the agent"""
        try:
            await self.connect()
            await self.play()
        finally:
            await self.close()
    
    async def connect(self):
        """Connect to the server via websocket"""
        self.websocket = await websockets.connect(f"ws://{self.server_address}/player")
        await self.websocket.send(json.dumps({"cmd": "join", "name": self.agent_name}))

        self.logger.info(f"Connected to server {self.server_address}")
        self.logger.debug(f"Waiting for game information")
        
        map_info = json.loads(await self.websocket.recv())
        
        self.fps = map_info["fps"]
        self.timeout = map_info["timeout"]
        
        self.domain = SnakeGame(
            logger=self.logger,
            width=map_info["size"][0], 
            height=map_info["size"][1], 
            internal_walls=MatrixOperations.find_ones(map_info['map']),
            max_steps=map_info["timeout"]
        )        
        self.mapping = Mapping(
            logger=self.logger,
            domain=self.domain,
            fps=self.fps,
        )
        
    async def play(self):
        """Main loop of the agent, where the game is played"""
        while True:
            try:
                state = json.loads(await self.websocket.recv())

                if not state.get("body"):
                    self.logger.warning("Game Over!")
                    continue
                
                self.logger.debug(f"Received state. Step: [{state["step"]}]")
                
                ## --- Main Logic ---
                self.observe(state)
                self.think(time_limit = ( self.ts + timedelta(seconds=1/(self.fps+0.6)) ))
                await self.act()
                ## ------------------
                
                self.logger.mapping(f"Time elapsed: {(datetime.now() - self.ts).total_seconds()}")
            except websockets.exceptions.ConnectionClosedOK:
                self.logger.warning("Server has cleanly disconnected us")      
                sys.exit(0)            
    
    # ------ Observe ------
    
    def observe(self, state):
        self.ts = datetime.fromisoformat(state["ts"])
        self.perfect_effects = self.domain.is_perfect_effects(state)
        
        ## Update the mapping
        self.mapping.update(state, self.perfect_effects, self.current_goals + self.future_goals, self.actions_plan)
    
    # ------- Act --------

    async def act(self):
        """Send the action to the server"""
        self.logger.debug(f"Action: [{self.action}] in [{self.domain.actions(self.mapping.state)}]")
        
        if self._action_not_possible():
            # Big problem, because the agent is trying to do something that is not possible
            # Can happen if the sync between the agent and the server is not perfect
            # TODO: understand why this is happening. Maybe is masking some bigger problem
            self.logger.critical(f"\33[31mAction not possible! [{self.action}]\33[0m")
            self.action = self._get_fast_action(warning=True)
        
        await self.websocket.send(json.dumps({"cmd": "key", "key": DIRECTION_TO_KEY[self.action]})) # mapping to the server key
        
    def _action_not_possible(self):
        return self.action not in self.domain.actions(self.mapping.state)
    
    # ------ Think -------
    
    def think(self, time_limit):
        ## Follow the action plain (nothing new observed)            
        if len(self.actions_plan) != 0 and self.mapping.nothing_new_observed(self.current_goals):
            self.action = self.actions_plan.pop()
            self.logger.debug(f"Following action plan: {self.action}")
            self.logger.debug(f"Current action plan length: {len(self.actions_plan)}")
            return
        
        ## Reset the action plan
        self.actions_plan = []
        self.action = None
        
        ## Get a new goal
        self.current_goals, force_traverse_disabled = self._find_goals() # Find a new goal
        self.logger.mapping(f"New goals {[goal.position for goal in self.current_goals]}")
        
        ## Get a safe path
        self.future_goals = self._find_future_goals(self.current_goals, force_traverse_disabled)
        self.logger.mapping(f"Future goals {[goal.position for goal in self.future_goals]}")
                
        ## Store a safe path to future goals
        safe_action = None
        while safe_action is None and len(self.future_goals) > 0:
            ## Search structure
            problem = SearchProblem(self.domain, self.mapping.state, self.future_goals)
            temp_tree = SearchTree(problem)
            
            try:
                ## Search for the given goals
                safe_action = temp_tree.search(
                    first_action=True,
                    time_limit=min(datetime.now() + timedelta(seconds=self.future_goals[0].max_time), time_limit)
                )
            except TimeLimitExceeded as e:
                self.logger.mapping(e.args[0])
                                
                ## Check max execution time
                if datetime.now() > time_limit:
                    self.mapping.ignore_goal(self.future_goals[0].position)
                    self.future_goals.pop(0)
                    break
            
            if safe_action is None:
                self.logger.mapping(f"[NOT FOUND] Safe path to {self.future_goals[0]}")
                self.mapping.ignore_goal(self.future_goals[0].position)
                self.future_goals.pop(0)
            else:
                self.logger.mapping(f"Safe path to {self.future_goals[0]} found!")
                
        ## If no safe path found, get a fast action
        if safe_action is None: 
            self.logger.mapping("No safe path found! (using not perfect solution)")
            # best_node = temp_tree.best_solution["node"]
            # self.action = temp_tree.first_action_to(best_node)
            return
        
        ## Try to get a path to goal and then to the first future goal
        present_goals = self.current_goals + self.future_goals
        num_goals = len(self.current_goals)
        
        ## Search structure
        problem = SearchProblem(self.domain, self.mapping.state, present_goals, num_present_goals=num_goals)
        temp_tree = SearchTree(problem)
            
        while num_goals > 0 and self._is_empty(self.actions_plan):
            try:
                ## Search for the given goals
                self.actions_plan = temp_tree.search(time_limit=min(datetime.now() + timedelta(seconds=present_goals[0].max_time), time_limit))
            except TimeLimitExceeded as e:
                self.logger.mapping(e.args[0])
                
                ## Check max execution time
                if datetime.now() > time_limit:
                    num_goals = 1 # last goal
            
            num_goals -= 1
            
            if self._is_empty(self.actions_plan):
                self.logger.mapping(f"Ignore goal {present_goals[num_goals].position}")
                
                ## Clear the last present goal from search tree (and all affected)
                self.mapping.ignore_goal(present_goals[num_goals].position)
                temp_tree.remove_goal(idx=num_goals)
                problem.num_present_goals = len(present_goals)
        
        ## If no path found, set the safe path
        if self._is_empty(self.actions_plan):
            self.logger.mapping("Safe action set! After all, no path found.")
            self.actions_plan = []
            self.action = safe_action
            return
        
        ## Set the next action
        self.logger.mapping(f"Goal action plan: {self.actions_plan}")
        self.action = self.actions_plan.pop()
    
    def _is_empty(self, obj):
        return obj is None or len(obj) == 0
    
    def _find_future_goals(self, goals, force_traverse_disabled):
        safe_point = self.mapping.peek_next_exploration()
        
        visited_range = 0
        if tuple(safe_point) in self.mapping.observed_objects and self.mapping.observed_objects[tuple(safe_point)][0] == Tiles.SUPER:
            self.logger.mapping("Safe point is a super food! (expanding range)")
            visited_range = 1
        
        return [Goal(
            goal_type="exploration",
            max_time=0.09,
            visited_range=visited_range,
            priority=10,
            position=safe_point
        )]

    def _find_goals(self, ):
        """Find a new goal based on mapping and state"""
        goals = []
        max_goals = get_num_max_present_goals()
        force_traverse_disabled = False

        ## Insert super goals, if any
        if self.mapping.observed(Tiles.SUPER) and not self.perfect_effects:
            for obj_position in self.mapping.closest_objects(Tiles.SUPER):
                if len(goals) >= max_goals:
                    break
                goals.append(Goal(
                    goal_type="super", 
                    max_time=0.07, 
                    visited_range=0,
                    priority=10, 
                    position=obj_position
                ))
            force_traverse_disabled = True # worst case scenario
        
        ## Insert food goals, if any
        elif len(goals) < max_goals and self.mapping.observed(Tiles.FOOD):
            for obj_position in self.mapping.closest_objects(Tiles.FOOD):
                if len(goals) >= max_goals:
                    break
                goals.append(Goal(
                    goal_type="food", 
                    max_time=0.07, 
                    visited_range=0,
                    priority=10, 
                    position=obj_position
                ))
        
        ## In case of no goals, go for exploration
        if len(goals) == 0:
            exploration_pos = self.mapping.next_exploration(force_traverse_disabled)
            
            visited_range = 0
            if tuple(exploration_pos) in self.mapping.observed_objects and self.mapping.observed_objects[tuple(exploration_pos)][0] == Tiles.SUPER:
                self.logger.mapping("Safe point is a super food! (expanding range)")
                visited_range = 1
                
            goals.append(Goal(
                goal_type="exploration", 
                max_time=0.07, 
                visited_range=visited_range,
                priority=10, 
                position=exploration_pos
            ))
    
        self.logger.mapping(f"Goal type: {goals[0].goal_type}")
        self.mapping.current_goal = goals[0].position
        
        return goals, force_traverse_disabled

    def _get_fast_action(self, warning=True):
        """Non blocking fast action"""
        self.actions_plan = []
        
        if warning:
            self.logger.mapping("Fast action!")

        ## If there are no actions available, return None
        if self.domain.actions(self.mapping.state) == []:
            self.logger.warning("No actions available!") # you're dead ;(
            return random.choice(["NORTH", "WEST", "SOUTH", "EAST"])

        ## Use heuristics to choose the best action
        min_heuristic = None
        for action in self.domain.actions(self.mapping.state):
            next_state = self.domain.result(self.mapping.state, action, self.current_goals)
            heuristic = self.domain.heuristic(next_state, self.current_goals) # change this!
            if min_heuristic is None or heuristic < min_heuristic:
                min_heuristic = heuristic
                best_action = action

        return best_action

