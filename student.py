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

from src.search_problem import SearchProblem
from src.snake_game import SnakeGame
from src.search_tree import SearchTree

DIRECTION_TO_KEY = {
    "NORTH": "w",
    "WEST": "a",
    "SOUTH": "s",
    "EAST": "d"
}

def find_ones(matrix):
    ones_coordinates = []
    for row_idx, row in enumerate(matrix):
        for col_idx, value in enumerate(row):
            if value == 1:
                ones_coordinates.append([row_idx, col_idx])
    return ones_coordinates

async def agent_loop(server_address="localhost:8000", agent_name="student"):
    """Autonomous AI client loop."""
    print(f"Hello world! I'm {agent_name} and I'm ready to play in {server_address}.")

    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        map_info = json.loads(
            await websocket.recv() ###
        )
        
        width, height = map_info["size"]
        internal_walls = find_ones(map_info["map"])

        domain = SnakeGame(width, height, internal_walls, traverse=True)
        
        directions = None
        # last_direction = None
        
        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game update, this must be called timely or your game will get out of sync with the server
                print("PIP")
                # print(
                #     state
                # )  # print the state, you can use this to further process the game state
                key = ""
                
                if directions == None or len(directions) == 0:
                    body = state["body"]
                    body = body + body[0]
                    food = [state["food"][0][0],state["food"][0][1]]
                    domain.traverse = state["traverse"]
                    
                    problem = SearchProblem(domain, initial=body, goal=food)
                    tree = SearchTree(problem, 'A*')
                    solution = tree.search() # lista pa la chegar

                    directions = tree.inverse_plan

                direction = directions.pop()
                
                # if last_direction != None and last_direction != direction:
                
                key = DIRECTION_TO_KEY[direction]
                print(domain.traverse, direction)                
                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )  # send key command to server - you must implement this send in the AI agent
                    # last_direction = direction
                
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

        

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 student.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
