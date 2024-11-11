import heapq
import random
import time
from collections import defaultdict
from src.exploration_path import ExplorationPath
from src.matrix_operations import MatrixOperations
from consts import Tiles

class Mapping:
    def __init__(self, domain, logger):
        self.state = None
        
        self.domain = domain
        self.logger = logger

        self.objects_updated = False
        self.observed_objects = None
        self.observation_duration = 15

        self.super_foods = []
        
        self.exploration_path = ExplorationPath(
            internal_walls=domain.internal_walls, 
            dead_ends=domain.dead_ends, 
            height=domain.height, 
            width=domain.width
        )
        # TODO: change the ignore_objects
        self.ignored_objects = {Tiles.PASSAGE, Tiles.STONE, Tiles.SNAKE}

        # Cells mapping: 0 - unseen, 1 - seen
        self.cells_mapping = {
            (x, y): (0, None)
            for x in range(self.domain.width)
            for y in range(self.domain.height)
        }   
         
        self.ignored_duration = 3
        self.temp_ignored_goals = set() # ([x, y], observed_timestamp) 

    @property
    def ignored_goals(self):
        for goal, timestamp in self.temp_ignored_goals.copy():
            if time.time() - timestamp > self.ignored_duration:
                self.temp_ignored_goals.remove((goal, timestamp))
        return self.temp_ignored_goals

    def ignore_goal(self, obj_pos):
        self.temp_ignored_goals.add((tuple(obj_pos), time.time()))
    
    def is_ignored_goal(self, obj_pos):
        return any(obj_pos[0] == x and obj_pos[1] == y for ((x, y), ts) in self.ignored_goals)
     
    def next_exploration(self) -> tuple:
        self.current_goal = self.exploration_path.next_exploration_point(
            self.state["body"], 
            self.state["range"],
            self.state["traverse"], 
            self.cells_mapping
        )
        return self.current_goal
    
    def peek_next_exploration(self) -> tuple:
        return self.exploration_path.peek_exploration_point(
            self.state["body"], 
            self.state["range"],
            self.state["traverse"], 
            self.cells_mapping
        )
        
        

    def update(self, state):
        self.objects_updated = False

        self.logger.debug(f"Old: {self.observed_objects}")
        ## Update the state
        self.state = {
            "body": state["body"] + [state["body"][-1]], # add the tail
            "range": state["range"],
            "traverse": state["traverse"],
            "observed_objects": self.state["observed_objects"] if self.state else dict(),
        }
        self.update_cells_mapping(state["sight"]) 

        ## Copy for better readability
        self.observed_objects = self.state["observed_objects"] # as a reference

        ## Clear the expired observed objects
        for position, [obj_type, timestamp] in self.observed_objects.copy().items():
            if time.time() - timestamp > self.observation_duration:
                del self.observed_objects[position]

        currently_observed = defaultdict(list)

        for x_str, y_dict in state["sight"].items():
            x = int(x_str)
            for y_str, obj_type in y_dict.items():
                y = int(y_str)
                position = (x, y)
                timestamp = time.time()
                currently_observed[position] = [obj_type, timestamp]                 

        ## Update the observed objects
        for position, [obj_type, timestamp] in currently_observed.items():
            
            # This position has a object
            if position in self.observed_objects:
                
                # In case, the object is the same
                if obj_type == self.observed_objects[position][0]:
                    self.observed_objects[position][1] = timestamp # update the timestamp
                else:
                    if obj_type in self.ignored_objects:
                        del self.observed_objects[position] # ignore the empty space
                    else:
                        # Update the object type (and current ts)
                        self.observed_objects[position] = [obj_type, timestamp]
                        if not (self.domain.is_perfect_effects(self.state) and obj_type == Tiles.SUPER):
                            self.objects_updated = True
            else:
                # This position is new
                if obj_type not in self.ignored_objects:
                    self.observed_objects[position] = [obj_type, timestamp]
                    if not (self.domain.is_perfect_effects(self.state) and obj_type == Tiles.SUPER):
                        self.objects_updated = True
        
        self.print_mapping()
        self.logger.debug(f"New: {self.observed_objects}")

    def nothing_new_observed(self):
        if not self.objects_updated:
            x, y = self.current_goal
            threshold = self.state["range"] * 2
            if self.cells_mapping[(x, y)][0] >= threshold:
                print(f"Threshold {threshold} reached - clearing the exploration path")
                self.exploration_path.exploration_path = []
                return False
            return True
        return False

    def observed(self, obj_type):
        return any(obj_type == object_type and not self.is_ignored_goal(position)
                     for position, [object_type, timestamp] in self.observed_objects.items())
        
    def closest_object(self, obj_type):
        """Find the closest object based on the heuristic"""
        closest = None
        min_heuristic = None

        for position in self.observed_objects.keys():
            if self.is_ignored_goal(position):
                continue
            
            heuristic = self.domain.heuristic(self.state, position)
            
            if min_heuristic is None or heuristic < min_heuristic:
                min_heuristic = heuristic
                closest = position
        
        # self.logger.debug(f"Closest {obj_type}: {closest}")
        return list(closest)                    
        
    def update_cells_mapping(self, sight):
        for x_str, y_dict in sight.items():
            x = int(x_str)
            for y_str, obj_type in y_dict.items():
                y = int(y_str)
                seen, timestamp = self.cells_mapping[(x, y)]
                self.cells_mapping[(x, y)] = (seen + 1, time.time())
        
        self.expire_cells_mapping()
    
    def expire_cells_mapping(self):
        duration = 30 / self.state["range"]

        for position, (seen, timestamp) in self.cells_mapping.copy().items():
            if timestamp is not None and time.time() - timestamp > duration:
                self.cells_mapping[position] = (0, None)

    def print_mapping(self):
        for y in range(self.domain.height):
            row = ""
            for x in range(self.domain.width):
                if (x, y) in self.observed_objects:
                    row += f"\033[34m{' F' if self.is_ignored_goal((x,y)) else ' X':2}\033[0m " 
                else:
                    seen = self.cells_mapping[(x, y)][0]
                    if seen == 0:
                        r = 255
                        g = 255
                        b = 255
                    else:
                        normalized_seen = min(seen / 30, 1.0)
                        if normalized_seen <= 0.5:
                            r = int(255 * (normalized_seen * 2))
                            g = int(255 * (1 - normalized_seen * 2))
                            b = 0
                        elif normalized_seen <= 0.85:
                            r = 255
                            g = 0
                            b = int(255 * ((normalized_seen - 0.5) * 4))
                        else:
                            r = int(255 * (1 - (normalized_seen - 0.85) * 4))
                            g = 0
                            b = 255
                    row += f"\033[38;2;{r};{g};{b}m{seen:2}\033[0m "
            self.logger.mapping(row)