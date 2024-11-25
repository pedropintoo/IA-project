'''
 # @ Authors: 
 #  - Pedro Pinto (pmap@ua.pt)
 #  - Joao Pinto (jpapinto@ua.pt)
 #  - Guilherme Santos (gui.santos91@ua.pt)
 # @ Create Time: 2024-10-13
 '''
from src.search.search_domain import SearchDomain
from consts import Tiles
import time

DIRECTIONS = {
    "NORTH": [0, -1],
    "EAST": [1, 0],
    "WEST": [-1, 0],
    "SOUTH": [0, 1] 
}

class SnakeGame(SearchDomain):
    def __init__(self, logger, width, height, internal_walls, dead_ends):
        self.logger = logger
        self.width = width
        self.height = height
        self.internal_walls = internal_walls
        self.dead_ends = dead_ends
    
    def is_perfect_effects(self, state):
        return (state["range"] >= 4 and state["traverse"]) and not self._has_n_super_observed(state, 7) and not state["step"] > 2700
    
    def _has_n_super_observed(self, state, n):
        return len([p for p in state.get("observed_objects", []) if state["observed_objects"][p][0] == Tiles.SUPER]) >= n
    
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

        sight_range = state["range"]
        cells_mapping = state["cells_mapping"]
        
        cells_mapping = self.update_cells_mapping(body[0], cells_mapping, sight_range)

        return {
                "body": new_body,
                "range": state["range"],
                "traverse": state["traverse"],
                "observed_objects": state["observed_objects"],
                "step": state["step"] + 1,
                "cells_mapping": cells_mapping
                }
    
    def update_cells_mapping(self, head, cells_mapping, sight_range):
        for x in range(-sight_range, sight_range + 1):
            for y in range(-sight_range, sight_range + 1):
                if x + y > sight_range:
                    continue
                x_new = (head[0] + x) % self.width
                y_new = (head[1] + y) % self.height
                seen, timestamp = cells_mapping[(x_new, y_new)]
                cells_mapping[(x_new, y_new)] = (seen + 1, time.time())
        
        cells_mapping = self.expire_cells_mapping(cells_mapping, sight_range)
        return cells_mapping
    
    def expire_cells_mapping(self, cells_mapping, sight_range):
        duration = 30 / sight_range

        for position, (seen, timestamp) in cells_mapping.copy().items():
            if timestamp is not None and time.time() - timestamp > duration:
                cells_mapping[position] = (0, None)
        return cells_mapping

    def cost(self, state, action):
        return 1
    
    def count_obstacles_between(self, start_pos, end_pos, body, body_weight, walls_weight):
        x1, y1 = start_pos
        x2, y2 = end_pos

        traverse = body["traverse"]

        x_start, x_end = sorted([x1, x2])
        y_start, y_end = sorted([y1, y2])

        obstacle_count = 0
        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end + 1):
                position = (x % self.width, y % self.height) if traverse else (x, y)
                if not traverse and position in self.internal_walls:
                    obstacle_count += walls_weight
                elif position in body["body"]:
                    obstacle_count += body_weight

        return obstacle_count
    
    def heuristic(self, state, goal_state):
        goal_state = goal_state[0] # TODO: CHANGE THIS
        head = state["body"][0]
        traverse = state["traverse"]
        cells_mapping = state["cells_mapping"]
        # Internal walls are not considered
        total_value = 0
        
        ## Manhattan distance
        dx_no_crossing_walls = abs(head[0] - goal_state[0])
        dx = min(dx_no_crossing_walls, self.width - dx_no_crossing_walls) if traverse else dx_no_crossing_walls

        dy_no_crossing_walls = abs(head[1] - goal_state[1])
        dy = min(dy_no_crossing_walls, self.height - dy_no_crossing_walls) if traverse else dy_no_crossing_walls

        total_value = dx + dy
        
        ## Include wall density in heuristic
        obstacle_count = self.count_obstacles_between(
            head, 
            goal_state, 
            state, 
            body_weight=3, 
            walls_weight=1
        )

        total_value += obstacle_count
        
        if self.is_perfect_effects(state) and any([head[0] == p[0] and head[1] == p[1] and state["observed_objects"][p][0] == Tiles.SUPER for p in state["observed_objects"]]):
            total_value += 20

        ## Include cells exploration in heuristic
        unseen = 0
        for x in range(self.width):
            for y in range(self.height):
                seen, _ = cells_mapping[(x, y)]
                if seen == 0:
                    unseen += 1

        total_value += int(unseen / state["range"]) # TODO: change this...
        
        return total_value

    def satisfies(self, state, goal_state):
        # TODO: add logic for different types of goals
        # e.g.: if the goal is of type explore, check if we have passed through the nearby position (maybe with some range defined in the goal)
        # e.g.: if the goal is of type eat, check if we have passed through the exact position
        head = state["body"][0]
        return head == goal_state

