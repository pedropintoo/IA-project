import heapq
import random
import time
from collections import defaultdict
from src.exploration_path import ExplorationPath
from src.matrix_operations import MatrixOperations
from consts import Tiles

class Mapping:
    def __init__(self, domain):
        self.state = None
        
        self.domain = domain

        self.objects_updated = False
        self.observed_objects = None
        self.observation_duration = 15

        self.super_foods = []
        self.exploration_map = []
        
        self.exploration_path = ExplorationPath(
            internal_walls=domain.internal_walls, 
            dead_ends=domain.dead_ends, 
            height=domain.height, 
            width=domain.width
        )
        # TODO: change the ignore_objects
        self.ignored_objects = {Tiles.PASSAGE, Tiles.STONE, Tiles.SNAKE}

     
    def next_exploration(self) -> tuple:
        return self.exploration_path.next_exploration_point(
            self.state["body"], 
            self.state["range"],
            self.state["traverse"], 
            self.super_foods,
            self.exploration_map
        )

    def update(self, state):
        self.objects_updated = False

        print("Old:", self.observed_objects)
        ## Update the state
        self.state = {
            "body": state["body"] + [state["body"][-1]], # add the tail
            "range": state["range"],
            "traverse": state["traverse"],
            "observed_objects": self.state["observed_objects"] if self.state else dict(),
        }

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
        
        print("New:", self.observed_objects)

    def nothing_new_observed(self):
        return not self.objects_updated

    def observed(self, obj_type):
        return any(obj_type == object_type for [object_type, _] in self.observed_objects.values())
        
    def closest_object(self, obj_type):
        """Find the closest object based on the heuristic"""
        closest = None
        min_heuristic = None

        for position in self.observed_objects.keys():
            heuristic = self.domain.heuristic(self.state, position)
            
            if min_heuristic is None or heuristic < min_heuristic:
                min_heuristic = heuristic
                closest = position
        print(f"Closest {obj_type}: {closest}")
        return list(closest)                    
        
