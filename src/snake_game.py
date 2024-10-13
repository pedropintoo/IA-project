'''
 # @ Authors: 
 #  - Pedro Pinto (pmap@ua.pt)
 #  - Joao Pinto (jpapinto@ua.pt)
 #  - Guilherme Santos (gui.santos91@ua.pt)
 # @ Create Time: 2024-10-13
 '''
from src.search_domain import SearchDomain

DIRECTIONS = {
    "NORTH": [0, -1],
    "EAST": [1, 0],
    "WEST": [-1, 0],
    "SOUTH": [0, 1] 
}

class SnakeGame(SearchDomain):
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    def actions(self, state): # given a state, what direction can I go
        _actlist = []
        for direction in DIRECTIONS:
            new_head = self.result(state,direction)[0]
            if (new_head not in state):
                _actlist.append(direction)

        return _actlist 

    def result(self, state, action): # Given a state and an action, what is the next state?
        vector = DIRECTIONS[action]
        head = [(state[0][0] + vector[0]) % self.width, (state[0][1] + vector[1]) % self.height]
        body = state[:]
        body.pop()
        body[:0] = [head]
        print(state, action, body)
        return body

    def cost(self, state, action):
        return 1
    
    def heuristic(self, state, goal_state):
        return (abs(state[0][0] - goal_state[0]) + abs(state[0][1] - goal_state[1])) * 10

    def satisfies(self, state, goal_state):
        return state[0] == goal_state

