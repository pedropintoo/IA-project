'''
 # @ Authors: 
 #  - Pedro Pinto (pmap@ua.pt)
 #  - Joao Pinto (jpapinto@ua.pt)
 #  - Guilherme Santos (gui.santos91@ua.pt)
 # @ Create Time: 2024-10-13
 '''
import heapq
from src.search.search_domain import SearchDomain
from consts import Tiles
import time
import datetime
from src.utils._consts import is_snake_in_perfect_effects

DIRECTIONS = {
    "NORTH": [0, -1],
    "EAST": [1, 0],
    "WEST": [-1, 0],
    "SOUTH": [0, 1] 
}

class SnakeGame(SearchDomain):
    def __init__(self, logger, width, height, internal_walls, max_steps, opponent_head=None, opponent_direction=None):
        self.logger = logger
        self.width = width
        self.height = height
        self.internal_walls = internal_walls
        self.max_steps = max_steps
        self.opponent_head = opponent_head
        self.opponent_direction = opponent_direction
    
    def is_perfect_effects(self, state):
        return is_snake_in_perfect_effects(state, self.max_steps)
    
    def _check_collision(self, state, action):
        """Check if the action will result in a collision"""
        body = state["body"]
        vector = DIRECTIONS[action]
        new_head = [(body[0][0] + vector[0]) % self.width, (body[0][1] + vector[1]) % self.height]
        
        if new_head in body:
            return True
        
        head_tuple = tuple(new_head)
        
        if head_tuple in state["observed_objects"]:
            if state["observed_objects"][head_tuple][0] == Tiles.SNAKE:
                print("TESTE!!!!!!!!")
                return True # collision with other snake
        
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

    def result(self, state, action, goals): # Given a state and an action, what is the next state?
        body = state["body"]
        vector = DIRECTIONS[action]
        new_head = [(body[0][0] + vector[0]) % self.width, (body[0][1] + vector[1]) % self.height]
        
        new_body = [new_head] + body[:-1]

        sight_range = state["range"]
                
        traverse = state["traverse"]
        visited_goals = state["visited_goals"].copy()
        for goal in goals:
            if tuple(goal.position) not in visited_goals:
                if self.is_goal_visited(new_head, goal, traverse):
                    if goal.goal_type == "super":
                        traverse = False # worst case scenario
                    elif goal.goal_type == "food":
                        new_body.append(body[-1]) # grow the snake
                    visited_goals.add(tuple(goal.position))
                else:
                    break # if one goal is not visited, we break the loop

        return {
                "body": new_body,
                "range": state["range"],
                "traverse": traverse,
                "observed_objects": state["observed_objects"],
                "step": state["step"] + 1,
                "visited_goals": visited_goals
                }

    def cost(self, state, action):
        return 1
    
    def heuristic(self, state, goals):        
        head = state["body"][0]
        traverse = state["traverse"]
        visited_goals = state.get("visited_goals") # check if this is correct
        
        heuristic_value = 0   
        previous_goal_position = head
        priority = 50

        snake_length = len(state["body"])
        body_weight = 1 # + snake_length // 10
        walls_weight = 1 # + snake_length // 5

        ## Manhattan distance to the goals
        for goal in goals: 
            if tuple(goal.position) in visited_goals:
                priority /= 5
                if goal.goal_type == "super":
                    traverse = False # worst case scenario
                continue
            self.logger.critical(f"GOAL POSITION: {goal.position}")
            
            goal_position = goal.position
            goal_range = goal.visited_range

            ## Manhattan distance (not counting walls)
            distance = self.manhattan_distance(previous_goal_position, goal_position, traverse) - goal_range

            heuristic_value += distance * priority
            priority /= 5
            
            previous_goal_position = goal_position
            
            if goal.goal_type == "super":
                traverse = False # worst case scenario
                    
        ## Count how many walls or body rounded by the snake
        rounded_obstacles = 0 
        for x in range(-2, 3):
            for y in range(-2, 3):
                if (x, y) == (0, 0):
                    continue # skip the head
                neighbor_x = (head[0] + x) % self.width if traverse else head[0] + x
                neighbor_y = (head[1] + y) % self.height if traverse else head[1] + y
                
                # Border walls
                if neighbor_x < 0 or neighbor_x >= self.width or neighbor_y < 0 or neighbor_y >= self.height:
                    rounded_obstacles += 1 
                    
                elif [neighbor_x, neighbor_y] in state["body"]:
                    rounded_obstacles += 1 # at least one body part is in the neighborhood
                
                if not traverse and [neighbor_x, neighbor_y] in self.internal_walls:
                    rounded_obstacles += 1
        
        self.logger.critical(f"ROUNDED OBSTACLES: {rounded_obstacles}")
        heuristic_value *= 1 + (((rounded_obstacles-3) // 3)  / 100)
        
        if self.is_perfect_effects(state) and any([head[0] == p[0] and head[1] == p[1] and state["observed_objects"][p][0] == Tiles.SUPER for p in state["observed_objects"]]):
            heuristic_value *= 50
        
        self.logger.critical(f"HEURISTIC VALUE: {heuristic_value} {len(visited_goals)}")

        return heuristic_value

    def manhattan_distance(self, head, goal_position, traverse):
        dx_no_crossing_walls = abs(head[0] - goal_position[0])
        dx = min(dx_no_crossing_walls, self.width - dx_no_crossing_walls) if traverse else dx_no_crossing_walls

        dy_no_crossing_walls = abs(head[1] - goal_position[1])
        dy = min(dy_no_crossing_walls, self.height - dy_no_crossing_walls) if traverse else dy_no_crossing_walls

        return dx + dy

    def satisfies(self, state, goal):
        return tuple(goal.position) in state["visited_goals"]

    def is_goal_visited(self, head, goal, traverse): 
        visited_range = goal.visited_range
        goal_position = goal.position
                
        distance = self.manhattan_distance(head, goal_position, traverse)

        return distance <= visited_range

    def is_goal_available(self, goal):
        return datetime.datetime.now() >= goal.max_time
    