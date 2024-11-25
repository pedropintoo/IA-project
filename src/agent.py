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
import sys

## Search
from src.search.search_problem import SearchProblem
from src.search.search_tree import SearchTree
from src.snake_game import SnakeGame

## Mapping & Exploration
from src.matrix_operations import MatrixOperations
from src.mapping import Mapping

## Utils
from src.utils.logger import Logger, MAPPING_LEVEL
from src.utils.exceptions import TimeLimitExceeded
from consts import Tiles

DIRECTION_TO_KEY = {
    "NORTH": "w",
    "WEST": "a",
    "SOUTH": "s",
    "EAST": "d"
}

wslogger = logging.getLogger("websockets")
wslogger.setLevel(logging.INFO)

class Agent:
    """Autonomous AI client."""
    
    def __init__(self, server_address, agent_name):
        
        ## Utils
        self.logger = Logger(f"[{agent_name}]", f"logs/{agent_name}.log")
        
        ## Activate the mapping level (comment the next line to disable mapping logging)
        self.logger.log.setLevel(MAPPING_LEVEL)
        
        ## Disable logging (comment the next line to enable logging)
        # self.logger.log.setLevel(logging.CRITICAL)
        
        self.server_address = server_address
        self.agent_name = agent_name
        self.websocket = None
        
        ## Defined by the start of the game
        self.mapping = None 
        self.fps = None
        self.timeout = None
        self.domain = None
        
        ## Action controller
        self.actions_plan = []
        self.action = None
        self.current_goal = None
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
            dead_ends=MatrixOperations.find_dead_ends(map_info['map'])
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
                self.think(time_limit = ( self.ts + timedelta(seconds=1/(self.fps+0.5)) ))
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
        self.mapping.update(state)
    
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
        if len(self.actions_plan) != 0 and self.mapping.nothing_new_observed(self.current_goal["strategy"]):
            self.action = self.actions_plan.pop()
            self.logger.debug(f"Following action plan: {self.action}")
            self.logger.debug(f"Current action plan length: {len(self.actions_plan)}")
            return
        
        ## Find a new goal
        all_goals = self._find_goals() # including the future goals
        self.current_goal = all_goals[0]
        self.logger.info(f"New goal {self.current_goal}")
        
        ## Create search structures
        self.problem = SearchProblem(
            domain=self.domain, 
            initial=self.mapping.state, 
            goals=all_goals
        )
        self.tree = SearchTree(self.problem)
        
        ## Search for the solution
        try: 
            self.actions_plan = self.tree.search(time_limit=time_limit)
            self.logger.debug(f"Actions plan founded!")
            
        except TimeLimitExceeded as e:
            self.logger.warning(e.args[0])
            self.mapping.ignore_goal(self.tree.ignored_positions)
            best_solution = self.tree.best_solution
            
            if best_solution:
                self.actions_plan = self.tree.inverse_plan(best_solution)
            else:
                self.actions_plan = []
                return
                        
        self.action = self.actions_plan.pop() # get the next first action

    def _find_goals(self, ):
        """Find a new goal based on mapping and state"""
        new_goal = {}
        
        if self.mapping.observed(Tiles.FOOD):
            new_goal["strategy"] = "food"
            new_goal["visit_range"] = 1
            new_goal["max_time"] = 0.05 # TODO: change this
            new_goal["position"] = self.mapping.closest_object(Tiles.FOOD)
            
        elif self.mapping.observed(Tiles.SUPER) and not self.perfect_effects:
            new_goal["strategy"] = "super"
            new_goal["max_time"] = 0.05 # TODO: change this
            new_goal["visit_range"] = 1
            new_goal["position"] = self.mapping.closest_object(Tiles.SUPER)
            
        else:
            new_goal["strategy"] = "exploration"
            new_goal["max_time"] = 0.05 # TODO: change this
            new_goal["visit_range"] = 2
            new_goal["position"] = self.mapping.next_exploration()
        
        return [new_goal] # TODO: change this, make this function return a list of goals ([present_goal, future_goal1, future_goal2, ...]) 

    def _get_fast_action(self, warning=True):
        """Non blocking fast action"""
        self.actions_plan = []
        self.mapping.ignore_goal(self.current_goal["position"])
        
        if warning:
            self.logger.critical("Fast action!")

        ## If there are no actions available, return None
        if self.domain.actions(self.mapping.state) == []:
            self.logger.warning("No actions available!") # you're dead ;(
            return random.choice(["NORTH", "WEST", "SOUTH", "EAST"])

        ## Use heuristics to choose the best action
        goal = self.current_goal["position"]
        min_heuristic = None
        for action in self.domain.actions(self.mapping.state):
            next_state = self.domain.result(self.mapping.state, action)
            heuristic = self.domain.heuristic(next_state, [goal]) # change this!
            if min_heuristic is None or heuristic < min_heuristic:
                min_heuristic = heuristic
                best_action = action

        return best_action

