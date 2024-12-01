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
import heapq
from datetime import datetime, timedelta
from src.utils._consts import get_num_future_goals, get_future_goals_priority, get_future_goals_range
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
        self.logger.activate_mapping()
        
        ## Disable logging (comment the next line to enable logging)
        #self.logger.disable()
        
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
            dead_ends=MatrixOperations.find_dead_ends(map_info['map']),
            max_steps=map_info["timeout"]
        )        
        self.mapping = Mapping(
            logger=self.logger,
            domain=self.domain
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
                
                self.logger.info(f"Time elapsed: {(datetime.now() - self.ts).total_seconds()}")
            except websockets.exceptions.ConnectionClosedOK:
                self.logger.warning("Server has cleanly disconnected us")      
                sys.exit(0)            
    
    # ------ Observe ------
    
    def observe(self, state):
        self.ts = datetime.fromisoformat(state["ts"])
        self.perfect_effects = self.domain.is_perfect_effects(state)
        
        ## Update the mapping
        self.mapping.update(state, self.perfect_effects, self.current_goals + self.future_goals)
    
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
        self.logger.info(f"New goals {[goal.position for goal in self.current_goals]}")
        
        ## Get a safe path
        future_goals = self._find_future_goals(force_traverse_disabled)
        self.logger.info(f"Future goals {[goal.position for goal in future_goals]}")
        
        
        ## Store a safe path to future goals
        safe_path = []
        num_present_goals = len(self.current_goals)
        while len(safe_path) == 0 and len(future_goals) > 0:
            
            ## Search structure
            problem = SearchProblem(self.domain, self.mapping.state, future_goals)
            temp_tree = SearchTree(problem)
            
            try:
                ## Search for the given goals
                safe_path = temp_tree.search(time_limit=min(datetime.now() + timedelta(seconds=future_goals[0].max_time), time_limit))
            except TimeLimitExceeded as e:
                self.logger.warning(e.args[0])
                
                ## Check max execution time
                if datetime.now() > time_limit:
                    break
            
            if len(safe_path) == 0:
                self.logger.debug(f"[NOT FOUND] Safe path to {future_goals[0]}")
                self.mapping.ignore_goal(future_goals[0].position)
                future_goals.pop(0)
            else:
                self.logger.info(f"Safe path to {future_goals[0]} found!")
        
        self.future_goals = future_goals
        
        ## If no safe path found, get a fast action
        if len(safe_path) == 0:
            self.logger.critical("No safe path found!")
            return
        
        if self.current_goals[0] == None:
            self.logger.critical("Goal is None!!!")
            self.actions_plan = [safe_path.pop() for _ in range(self.mapping.state["range"]) if len(safe_path) > 0]
            self.logger.info("Safe path set!")
            self.action = self.actions_plan.pop()
            return
        
        
        ## Normalize priority
        last_goal_priority = self.current_goals[-1].priority
        future_goals[0].priority = last_goal_priority // 2
        future_goals[0].visited_range = 1
        
        ## Try to get a path to goal and then to the first future goal
        present_goals = self.current_goals[:] + [future_goals[0]]
        while len(present_goals) > 1 and len(self.actions_plan) == 0:
            
            ## Search structure
            problem = SearchProblem(self.domain, self.mapping.state, present_goals)
            temp_tree = SearchTree(problem)
            
            try:
                ## Search for the given goals
                self.actions_plan = temp_tree.search(time_limit=min(datetime.now() + timedelta(seconds=present_goals[0].max_time), time_limit))
            except TimeLimitExceeded as e:
                self.logger.warning(e.args[0])
                
                ## Check max execution time
                if datetime.now() > time_limit:
                    break
            
            if len(self.actions_plan) == 0:
                self.logger.debug(f"[NOT FOUND] Path to {present_goals[0]}")
                self.mapping.ignore_goal(present_goals[0].position)
                present_goals.pop(0)
            else:
                self.logger.info(f"Path to {present_goals[0]} found!")
        
        ## If no path found, set the safe path
        if len(self.actions_plan) == 0:
            # set only a part of the safe path
            self.actions_plan = [safe_path.pop() for _ in range(self.mapping.state["range"]) if len(safe_path) > 0]
            self.logger.info("Safe path set!")
        
        self.action = self.actions_plan.pop()
            
    def _find_future_goals(self, force_traverse_disabled):
        future_goals = []
        
        ## Create the list with future goals
        num_future_goals = get_num_future_goals(self.mapping.state["range"])
        future_priority = get_future_goals_priority(num_future_goals)
        future_range = get_future_goals_range(num_future_goals, self.mapping.state["range"])
        idx = 0
        for future_position in self.mapping.peek_next_exploration(num_future_goals, force_traverse_disabled):
            future_goal = Goal(
                goal_type="exploration",
                max_time=0.04, # TODO: change this
                visited_range=future_range[idx],
                priority=future_priority[idx],
                position=future_position
            )
            idx += 1
            future_goals.append(future_goal)
        
        return future_goals


    def _find_goals(self, ):
        """Find a new goal based on mapping and state"""
        goals = []
        force_traverse_disabled = False
        
        # if self.mapping.opponent.is_to_attack_opponent():
        #     for goal in self.mapping.opponent.attack_opponent():
        #         goals.append(goal)

        if self.mapping.observed(Tiles.FOOD):
            goals.append(Goal(None, None, None, None, None))
            goals[0].goal_type = "food"
            goals[0].max_time = 0.07
            goals[0].visited_range = 0
            goals[0].priority = 10
            goals[0].position = self.mapping.closest_object(Tiles.FOOD)
            
        elif self.mapping.observed(Tiles.SUPER) and not self.perfect_effects:
            goals.append(Goal(None, None, None, None, None))
            goals[0].goal_type = "super"
            goals[0].max_time = 0.07
            goals[0].visited_range = 0
            goals[0].priority = 10
            goals[0].position = self.mapping.closest_object(Tiles.SUPER)
            force_traverse_disabled = True # worst case scenario
            
        else:
            goals.append(Goal(None, None, None, None, None))
            goals[0].goal_type = "exploration"
            goals[0].max_time = 0.07
            goals[0].visited_range = 0 #(self.mapping.state["range"] + 1) // 2 - 1 # ( 2 -> 0, 3 -> 1, 4 -> 1, 5 -> 2, 6 -> 2)
            goals[0].priority = 10
            goals[0].position = self.mapping.next_exploration()
        
        self.mapping.current_goal = goals[0].position
        
        return goals, force_traverse_disabled

    def _get_fast_action(self, warning=True):
        """Non blocking fast action"""
        self.actions_plan = []
        self.mapping.ignore_goal(self.current_goals[0].position)
        
        if warning:
            self.logger.critical("Fast action!")

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

