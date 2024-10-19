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

from src.search_problem import SearchProblem
from src.snake_game import SnakeGame
from src.search_tree import SearchTree

from datetime import datetime, timedelta

DIRECTION_TO_KEY = {
    "NORTH": "w",
    "WEST": "a",
    "SOUTH": "s",
    "EAST": "d"
}

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

wslogger = logging.getLogger("websockets")
wslogger.setLevel(logging.INFO)

logger = logging.getLogger("Server")
logger.setLevel(logging.INFO)


def find_ones(matrix):
    ones_coordinates = []
    for row_idx, row in enumerate(matrix):
        for col_idx, value in enumerate(row):
            if value == 1:
                ones_coordinates.append([row_idx, col_idx])
    return ones_coordinates

class Agent:
    """Autonomous AI client."""
    
    def __init__(self, server_address, agent_name):
        self.server_address = server_address
        self.agent_name = agent_name
        
        self.search_enable = True
        self.step = 0
        self.food = None
        self.ts = None
        self.body = None
        self.sight = None
        self.range = None
        

    async def run(self):
        await self.connect()
        await self.play()

    async def connect(self):
        self.websocket = await websockets.connect(f"ws://{self.server_address}/player")
        await self.websocket.send(json.dumps({"cmd": "join", "name": self.agent_name}))

        logger.info(f"Connected to server {self.server_address}")
        logger.info(f"Waiting for game information")
        
        map_info = json.loads(await self.websocket.recv())
        self.width, self.height = map_info["size"]
        self.map = map_info["map"]
        self.fps = map_info["fps"]
        self.timeout = map_info["timeout"]
        self.level = map_info["level"] # not used        
        self.internal_walls = find_ones(self.map)
        
        self.domain = SnakeGame(
            self.width, 
            self.height, 
            self.internal_walls, 
            traverse=True
        )
    
    async def observe(self, state):
        self.step = state["step"]
        self.food = state["food"]
        self.ts = state["ts"]
        self.body = state["body"]
        self.sight = state["sight"]
        self.range = state["range"]
        self.traverse = state["traverse"]
        self.domain.traverse = self.traverse
    
    async def think(self):
        self.action = ""
        
        if self.search_enable:
            self.search_enable = False
            self.problem = SearchProblem(self.domain, initial=self.body, goal=[self.food[0][0], self.food[0][1]])
            self.tree = SearchTree(self.problem, 'A*')
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.tree.search)
            
            self.directions = self.tree.inverse_plan
            self.action = DIRECTION_TO_KEY[self.directions.pop()]
            logger.info("Solution founded!")
            return
        
        if self.directions:
            self.action = DIRECTION_TO_KEY[self.directions.pop()]
            logger.info(f"Following solution! [{self.action}]")
            return
        else:
            self.search_enable = True
        
    
    async def act(self):
        logger.info(f"Action: [{self.action}, {self.traverse}]")
        await self.websocket.send(
            json.dumps({"cmd": "key", "key": self.action})
        )

    def fast_action(self):
        return "" # TODO: Implement a fast action to prevent collisions
    
    async def play(self):

        while True:
            try:
                
                state = json.loads(
                    await self.websocket.recv()
                )
                logger.info("Received state: [%s]", state["step"])
                
                if game_over := state.get("map"):
                    logger.info("Game Over!")
                    return
                
                logger.info("Observing state")
                await self.observe(state)
                try:
                    logger.info("Thinking...")
                    await asyncio.wait_for(self.think(), timeout=1/(self.fps+1))
                except asyncio.TimeoutError:
                    self.search_enable = True
                    self.action = self.fast_action()
                    logger.info(f"Timeout [{1/(self.fps+1)} seconds]! Fast action!")
                finally:
                    await self.act()
                                
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return
                  
        return
        

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 student.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())

agent = Agent(f"{SERVER}:{PORT}", NAME)
loop.run_until_complete(agent.run())
