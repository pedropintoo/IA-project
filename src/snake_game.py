'''
 # @ Authors: 
 #  - Pedro Pinto (pmap@ua.pt)
 #  - Joao Pinto (jpapinto@ua.pt)
 #  - Guilherme Santos (gui.santos91@ua.pt)
 # @ Create Time: 2024-10-13
 '''
from search_domain import SearchDomain
from consts import Direction
import math

class SnakeGame(SearchDomain):
    def __init__(self, body_coords, food_coords):
        self.body_coords = body_coords
        self.food_coords = food_coords
    
    def actions(self, state): # given a state, what direction can I go
        actlist = [Direction.NORTH, Direction.EAST, Direction.WEST, Direction.SOUTH]
        return actlist 
    
    def result(self,city,action): # Given a city and an action, what is the next city?
        (C1,C2) = action
        if C1==city:
            return C2 # TODO: ...
    
    def cost(self, city, action):
        # city1,city2 = action
        
        # if city1 == city2:
        #     return None # or assert..
        
        # for (c1, c2, cost) in self.connections:
        #     if action in [(c1,c2), (c2,c1)]:
        #         return cost
        
        return None
        
    def heuristic(self, city, goal_city):
        pass

    def satisfies(self, city, goal_state):
        return goal_state==city
    