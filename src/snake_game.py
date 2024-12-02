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
import datetime
from src.utils._consts import is_snake_in_perfect_effects

DIRECTIONS = {
    "NORTH": [0, -1],
    "EAST": [1, 0],
    "WEST": [-1, 0],
    "SOUTH": [0, 1] 
}

class SnakeGame(SearchDomain):
    def __init__(self, logger, width, height, internal_walls, dead_ends, max_steps):
        self.logger = logger
        self.width = width
        self.height = height
        self.internal_walls = internal_walls
        self.dead_ends = dead_ends
        self.max_steps = max_steps
    
    def is_perfect_effects(self, state):
        return is_snake_in_perfect_effects(state, self.max_steps)
    
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
    
    def heuristic(self, state, goals):        
        head = state["body"][0]
        traverse = state["traverse"]
        visited_goals = state.get("visited_goals") # check if this is correct
        
        heuristic_value = 0   
        previous_goal_position = head
        priority = 25
        for goal in goals: # TODO: change this to consider all goals   
            if tuple(goal.position) in visited_goals:
                # print("\33[33mGoal already visited\33[0m")
                priority /= 10
                continue
            
            goal_position = goal.position
            goal_range = goal.visited_range

            ## Manhattan distance (not counting walls)
            distance = self.manhattan_distance(previous_goal_position, goal_position, traverse)

            # Include wall density in heuristic
            obstacle_count = self.count_obstacles_between(
                previous_goal_position, 
                goal_position, 
                state, 
                body_weight=1,  # This can became overly cautious. Suggestion: Dynamically adjust weights based on the snake’s size or current safety margin.
                walls_weight=1  
            )
            distance += obstacle_count

            heuristic_value += distance * priority
            print(priority)
            priority /= 5
            
            previous_goal_position = goal_position
                    
        ## Count how many walls or body rounded by the snake
        rounded_obstacles = 0 
        for x in range(-1, 2):
            for y in range(-1, 2):
                if (x, y) == (0, 0):
                    continue # skip the head
                neighbor_x = (head[0] + x) % self.width if traverse else head[0] + x
                neighbor_y = (head[1] + y) % self.height if traverse else head[1] + y
                if [neighbor_x, neighbor_y] in state["body"]:
                    rounded_obstacles += 1 # at least one body part is in the neighborhood
                if not traverse and [neighbor_x, neighbor_y] in self.internal_walls:
                    rounded_obstacles += 1
        
        heuristic_value += rounded_obstacles * 3
        
        
        if self.is_perfect_effects(state) and any([head[0] == p[0] and head[1] == p[1] and state["observed_objects"][p][0] == Tiles.SUPER for p in state["observed_objects"]]):
            heuristic_value += 50
        
        self.logger.mapping(f"heuristic_value: {heuristic_value} {len(visited_goals)}")
        
        return heuristic_value

    def satisfies(self, state, goal):
        # TODO: add logic for different types of goals
        # e.g.: if the goal is of type explore, check if we have passed through the nearby position (maybe with some range defined in the goal)
        # e.g.: if the goal is of type eat, check if we have passed through the exact position
        return tuple(goal.position) in state["visited_goals"]

    def manhattan_distance(self, head, goal_position, traverse):
        dx_no_crossing_walls = abs(head[0] - goal_position[0])
        dx = min(dx_no_crossing_walls, self.width - dx_no_crossing_walls) if traverse else dx_no_crossing_walls

        dy_no_crossing_walls = abs(head[1] - goal_position[1])
        dy = min(dy_no_crossing_walls, self.height - dy_no_crossing_walls) if traverse else dy_no_crossing_walls

        return dx + dy

    def is_goal_visited(self, head, goal, traverse): 
        visited_range = goal.visited_range
        goal_position = goal.position
                
        distance = self.manhattan_distance(head, goal_position, traverse)
        print(f"Distance to goal: {distance} - {visited_range}")
        return distance <= visited_range

    def is_goal_available(self, goal):
        return datetime.datetime.now() >= goal.max_time
    