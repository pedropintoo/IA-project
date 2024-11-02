'''
 # @ Authors: 
 #  - Pedro Pinto (pmap@ua.pt)
 #  - Joao Pinto (jpapinto@ua.pt)
 #  - Guilherme Santos (gui.santos91@ua.pt)
 # @ Create Time: 2024-10-13
 '''
from src.search.search_domain import SearchDomain
from consts import Tiles

DIRECTIONS = {
    "NORTH": [0, -1],
    "EAST": [1, 0],
    "WEST": [-1, 0],
    "SOUTH": [0, 1] 
}

class SnakeGame(SearchDomain):
    def __init__(self, width, height, internal_walls, dead_ends):
        self.width = width
        self.height = height
        self.internal_walls = internal_walls
        self.dead_ends = dead_ends
    
    def is_perfect_effects(self, state):
        return state["range"] >= 5 and state["traverse"]
    
    def _check_collision(self, state, action):
        """Check if the action will result in a collision"""
        body = state["body"]
        vector = DIRECTIONS[action]
        new_head = [(body[0][0] + vector[0]) % self.width, (body[0][1] + vector[1]) % self.height]
        
        if new_head in body:
            return True
        
        if not state["traverse"]:
            if new_head in self.internal_walls:
                return True
            
            head = body[0]
            distance = [abs(new_head[0] - head[0]), abs(new_head[1] - head[1])]
            if distance[0] > 1 or distance[1] > 1:
                return True
            
        return False
    
    def actions(self, state):
        """Return the list of possible actions in a given state"""
        _actlist = []
        for action in DIRECTIONS:
            if not self._check_collision(state, action):
                _actlist.append(action)
        return _actlist 

    def result(self, state, action): # Given a state and an action, what is the next state?
        body = state["body"]
        vector = DIRECTIONS[action]
        new_head = [(body[0][0] + vector[0]) % self.width, (body[0][1] + vector[1]) % self.height]
        
        new_body = [new_head] + body[:-1]

        return {
                "body": new_body,
                "range": state["range"],
                "traverse": state["traverse"],
                "observed_objects": state["observed_objects"]
                }

    def cost(self, state, action):
        return 1
    
    def heuristic(self, state, goal_state):
        head = state["body"][0]
        traverse = state["traverse"]
        # Internal walls are not considered
        total_value = 0
        
        dx_no_crossing_walls = abs(head[0] - goal_state[0])
        if traverse:
            dx = min(dx_no_crossing_walls, self.width - dx_no_crossing_walls)
        else:
            dx = dx_no_crossing_walls
            
        dy_no_crossing_walls = abs(head[1] - goal_state[1])
        if traverse:
            dy = min(dy_no_crossing_walls, self.height - dy_no_crossing_walls)
        else:
            dy = dy_no_crossing_walls

        total_value = (dx + dy)
        
        if self.is_perfect_effects(state) and head in state["observed_objects"].get(Tiles.SUPER.value, []):
            total_value += 20

        return total_value * 10

    def satisfies(self, state, goal_state):
        head = state["body"][0]
        return head == goal_state

