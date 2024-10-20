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

from src.search_problem import SearchProblem
from src.snake_game import SnakeGame
from src.search_tree import SearchTree
from src.matrix_operations import Matrix
from consts import Tiles

from datetime import datetime, timedelta
from collections import defaultdict

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


class Agent:
    """Autonomous AI client."""
    
    def __init__(self, server_address, agent_name):
        self.server_address = server_address
        self.agent_name = agent_name
        
        self.matrix = None
        self.exploration_path = []
        self.directions = []
        
        self.search_enable = True
        self.current_step = 0
        self.ts = datetime.now()
        self.body = None
        self.sight = None
        self.range = None
        
        self.available_objects = [Tiles.FOOD, Tiles.SUPER, Tiles.SNAKE]
        self.objects_saw = {}
        self.last_objects_saw = {}

    async def run(self):
        await self.connect()
        await self.play()

    async def connect(self):
        self.websocket = await websockets.connect(f"ws://{self.server_address}/player")
        await self.websocket.send(json.dumps({"cmd": "join", "name": self.agent_name}))

        logger.info(f"Connected to server {self.server_address}")
        logger.info(f"Waiting for game information")
        
        map_info = json.loads(await self.websocket.recv())
        self.matrix = Matrix(map_info["map"])
        
        self.width = self.matrix.width
        self.height = self.matrix.height
        self.internal_walls = self.matrix.find_ones()
        
        self.fps = map_info["fps"]
        self.timeout = map_info["timeout"]
        self.level = map_info["level"] # not used        
        
        self.domain = SnakeGame(
            self.width, 
            self.height, 
            self.internal_walls
        )
    
    async def observe(self, state):
        self.current_step = state["step"]
        self.ts =  datetime.fromisoformat(state["ts"])
        self.body = state["body"]
        self.sight = state["sight"]
        self.traverse = state["traverse"]
        
        # Recalculate the exploration path if the range changes
        if self.range != state["range"]:
            self.range = state["range"]
            self.exploration_path = self.matrix.get_exploration_path(self.range)
            logger.info(f"Exploration path recalculated! [{self.range}]")
    
    def find_objects(self, sight):
        objects = defaultdict(list)
        for x, y_dict in self.sight.items():
            x = int(x) 
            for y, value in y_dict.items():
                y = int(y)
                if [x, y] in self.body or value not in self.available_objects:
                    continue
                objects[value].append([x, y])
        return objects
    
    def body_perfect_effects(self):
        return self.range == 6 or (self.range == 5 and self.traverse)
    
    async def think(self):
        self.action = self.fast_action(error=False)
        self.objects_saw = self.find_objects(self.sight)
        
        if self.body_perfect_effects() and Tiles.SUPER.value in self.objects_saw.keys():
            del self.objects_saw[Tiles.SUPER.value] # TODO: Implement a better strategy
        
        if Tiles.SNAKE.value in self.objects_saw.keys():
            del self.objects_saw[Tiles.SNAKE.value] # TODO: Implement a better strategy
        
        if self.directions != [] and all([self.objects_saw[obj] == [] for obj in self.available_objects]):
            self.action = DIRECTION_TO_KEY[self.directions.pop()]
            logger.info(f"Following solution! [{self.action}]")
        else:
            
            initial_state = {
                "body": self.body + [self.body[0]], # extend the body to avoid collision with tail 
                "sight": self.sight, 
                "range": self.range, 
                "traverse": self.traverse
            }
            
            logger.info(f"Saw objects: {self.objects_saw}")
            if self.objects_saw != {}:
                goal = random.choice(list(self.objects_saw.values())[0]) # TODO: Implement a better strategy
            else:
                if self.exploration_path == []:
                    self.exploration_path = self.matrix.get_exploration_path(self.range)
                goal = self.exploration_path.pop()
                
            logger.info(f"Searching for solution! {goal}")
            self.problem = SearchProblem(self.domain, initial=initial_state, goal=goal)
            self.tree = SearchTree(self.problem, 'A*')
            
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.tree.search)
                logger.info(f"Average branching: {self.tree.avg_branching}")
            except Exception as e:
                logger.error(f"Error: {e}")
                
            if self.tree.solution:
                self.directions = self.tree.inverse_plan
                if self.directions != []:
                    d = self.directions.pop()
                    if d in DIRECTION_TO_KEY.keys():
                        self.action = DIRECTION_TO_KEY[d]
                        logger.info(f"Following solution! [{self.action}]")
                        logger.info("Solution founded!")
        
        self.last_objects_saw = self.objects_saw
        self.objects_saw = {}
    
    async def act(self):
        logger.info(f"Action: [{self.action}, {self.traverse}] in [{self.domain.actions({'body': self.body, 'sight': self.sight, 'range': self.range, 'traverse': self.traverse})}]")
        if self.action not in [DIRECTION_TO_KEY[d] for d in self.domain.actions({'body': self.body, 'sight': self.sight, 'range': self.range, 'traverse': self.traverse})]:
            self.action = self.fast_action(error=True)
        await self.websocket.send(
            json.dumps({"cmd": "key", "key": self.action})
        )

    def fast_action(self, error=True):
        if error:
            print("\33[31mFast action!\33[0m")
            self.directions = []
            self.objects_saw = {}
        return DIRECTION_TO_KEY[random.choice(self.domain.actions({
                                                  "body": self.body,
                                                  "sight": self.sight,
                                                  "range": self.range,
                                                  "traverse": self.traverse
                                                  }))] # TODO: Implement a better strategy
    
    async def play(self):

        while True:
            try:
                
                state = json.loads(
                    await self.websocket.recv()
                )
                logger.info("Received state: [%s]", state["step"])
                
                if state.get("body") is None:
                    logger.info("Game Over!")
                    return
                
                await self.observe(state)
                start = self.ts
                try:
                    logger.info("Thinking...")
                    await asyncio.wait_for(self.think(), timeout=1/(self.fps*2) - (datetime.now() - self.ts).total_seconds())
                except asyncio.TimeoutError:
                    self.action = self.fast_action()
                finally:
                    logger.info(f"Time elapsed: {(datetime.now() - start).total_seconds()}")
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
