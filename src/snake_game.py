'''
 # @ Authors: 
 #  - Pedro Pinto (pmap@ua.pt)
 #  - Joao Pinto (jpapinto@ua.pt)
 #  - Guilherme Santos (gui.santos91@ua.pt)
 # @ Create Time: 2024-10-13
 '''
from src.search_domain import SearchDomain
import numpy as np
import math

DIRECTIONS = {
    "NORTH": [0, 1],
    "EAST": [1, 0],
    "WEST": [-1, 0],
    "SOUTH": [0, -1] 
}

class SnakeGame(SearchDomain):
    def __init__(self, body_coords, food_coords):
        self.body_coords = body_coords
        self.food_coords = food_coords
    
    def actions(self, state): # given a state, what direction can I go
        actlist = ["NORTH", "EAST", "WEST", "SOUTH"]
        return actlist 
    
    def result(self,state, action): # Given a state and an action, what is the next state?
        vector = DIRECTIONS[action]
        # print(state, action, " = ", [state[0] + vector[0], state[1] + vector[1]])
        return [state[0] + vector[0], state[1] + vector[1]]

    def cost(self, state, action):
        return 1
    
    def heuristic(self, state, goal_state):
        return (abs(state[0] - goal_state[0]) + abs(state[1] - goal_state[1])) * 10

    def satisfies(self, state, goal_state):
        return state == goal_state

