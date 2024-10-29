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

from src.search_problem import SearchProblem
from src.snake_game import SnakeGame
from src.search_tree import SearchTree
from src.matrix_operations import MatrixOperations
from src.mapping import Mapping
from consts import Tiles
from src.utils.logger import Logger

from datetime import datetime, timedelta
from collections import defaultdict

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
        self.logger = Logger(f"[{agent_name}]", f"logs/{agent_name}.log")
        
        self.server_address = server_address
        self.agent_name = agent_name
        
        self.mapping = None
        self.directions = []
        
        self.fps = None
        self.timeout = None
        self.domain = None
        
        self.state = None
        self.action = None
        
        self.last_observed_objects = None
        self.observed_objects = defaultdict(list)

        self.current_goal = None
    
    def _ignore_object(self, obj):
        if obj == Tiles.PASSAGE or obj == Tiles.STONE:
            return True
        if obj == Tiles.SNAKE:
            return True
        return False   

    def _update_observed_objects(self):
        self.last_observed_objects = self.observed_objects.copy()
        self.observed_objects = defaultdict(list)
        
        for x_str, y_dict in self.state["sight"].items():
            x = int(x_str)
            for y_str, value in y_dict.items():
                y = int(y_str)
                if self._ignore_object(value):
                    continue
                self.observed_objects[value].append([x, y])

        self.logger.debug(f"Observed objects: {self.observed_objects}")

    def _nothing_new_observed(self):
        if self.domain.is_perfect_effects(self.state):
            return all(
                self.last_observed_objects[obj] == self.observed_objects[obj] 
                for obj in self.observed_objects
                if obj != Tiles.SUPER
            )
            
        return all(
            self.last_observed_objects[obj] == self.observed_objects[obj] 
            for obj in self.observed_objects
        )    
        
    def observe(self, state):
        self.state = state
        self.ts = datetime.fromisoformat(state["ts"])
        self._update_observed_objects()

    def _find_goal(self):
        """Find the goal to reach"""
        self.current_goal = {"strategy": "food/super", "position": None}
        if Tiles.FOOD in self.observed_objects:
            self.current_goal["position"] = random.choice(self.observed_objects[Tiles.FOOD])
            return
            
        if Tiles.SUPER in self.observed_objects and not self.domain.is_perfect_effects(self.state):
            self.current_goal["position"] = random.choice(self.observed_objects[Tiles.SUPER])
            return
        
        self.current_goal = {
            "strategy": "exploration", 
            "position": self.mapping.next_exploration(self.state["body"], self.state["range"], self.state["traverse"])
        }
        return 

    def _get_fast_action(self, warning=True):
        """Non blocking fast action"""
        if warning:
            print("\33[31mFast action!\33[0m")

        return DIRECTION_TO_KEY[random.choice(self.domain.actions(self.state))]

    def think(self, time_limit):
        # Follow a solution (nothing new observed)
        if len(self.directions) != 0:
            if self._nothing_new_observed():
                self.logger.debug(f"Following solution! [{self.action}]")
                self.action = DIRECTION_TO_KEY[self.directions.pop()]
                return
            else:
                self.logger.info("\033[94mNew objects observed!\33[0m")
                
        # Search for a new one
        initial_state = {
            "body": self.state["body"][:], 
            "observed_objects": self.observed_objects, 
            "range": self.state["range"], 
            "traverse": self.state["traverse"]
        }
        initial_state["body"].append(self.state["body"][-1]) # Append the last element to avoid tail collision 
        
        self.current_goal = None
        while self.current_goal is None or self.current_goal["position"] == self.state["body"][0]:
            self._find_goal()
        self.logger.debug(f"Searching a path to {self.current_goal}")
        
        self.problem = SearchProblem(self.domain, initial=initial_state, goal=self.current_goal["position"])
        self.tree = SearchTree(self.problem, 'greedy')
        
        solution = self.tree.search(time_limit=time_limit)
        self.logger.debug(f"Average branching: {self.tree.avg_branching}")

        if solution is None:
            self.action = self._get_fast_action(warning=True)
            return

        self.directions = self.tree.inverse_plan
        self.logger.debug(f"Plan: {len(self.directions)} from {self.state["body"][0]}")
        self.action = DIRECTION_TO_KEY[self.directions.pop()]
        self.logger.debug(f"Following solution! [{self.action}]")

    def _action_not_possible(self):
        return self.action not in [DIRECTION_TO_KEY[direction] for direction in self.domain.actions(self.state)]
    
    async def act(self):
        self.logger.debug(f"Action: {self.action}")
        if self._action_not_possible():
            self.logger.critical(f"\33[31mAction not possible! [{self.action}]\33[0m")
            self.action = self._get_fast_action(warning=True)
        
        await self.websocket.send(
            json.dumps({"cmd": "key", "key": self.action})
        )
    
    async def run(self):
        await self.connect()
        await self.play()

    async def connect(self):
        self.websocket = await websockets.connect(f"ws://{self.server_address}/player")
        await self.websocket.send(json.dumps({"cmd": "join", "name": self.agent_name}))

        self.logger.info(f"Connected to server {self.server_address}")
        self.logger.debug(f"Waiting for game information")
        
        map_info = json.loads(await self.websocket.recv())
        self.mapping = Mapping(matrix=map_info["map"])
        
        self.fps = map_info["fps"]
        self.timeout = map_info["timeout"]
        
        self.domain = SnakeGame(
            width=self.mapping.width, 
            height=self.mapping.height, 
            internal_walls=self.mapping.walls
        )
    
    async def play(self):

        while True:
            try:
                
                state = json.loads(
                    await self.websocket.recv()
                )
                
                if state.get("body") is None:
                    self.logger.info("Game Over!")
                    return
                
                self.logger.debug(f"Received state. Step: [{state["step"]}]")
                
                self.observe(state)
                self.think(time_limit=self.ts + timedelta(seconds=1/(self.fps+1)))
                await self.act()
                self.logger.debug(f"Time elapsed: {(datetime.now() - self.ts).total_seconds()}")
                                
            except websockets.exceptions.ConnectionClosedOK:
                self.logger.warning("Server has cleanly disconnected us")
                return
                  
        return
        