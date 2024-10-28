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
from src.matrix_operations import Matrix
from consts import Tiles

from datetime import datetime, timedelta
from collections import defaultdict

        

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 student.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())

agent = Agent(f"{SERVER}:{PORT}", NAME)
loop.run_until_complete(agent.run())
