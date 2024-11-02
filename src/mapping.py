import heapq
import random
from collections import defaultdict
from src.exploration_path import ExplorationPath
from src.matrix_operations import MatrixOperations
from consts import Tiles

class Mapping:
    def __init__(self, domain):
        self.state = None
        
        self.domain = domain

        self.last_observed_objects = None
        self.observed_objects = defaultdict(list)
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
        self.last_observed_objects = self.observed_objects.copy()
        
        self.state = {
            "body": state["body"] + [state["body"][-1]], # add the tail
            "range": state["range"],
            "traverse": state["traverse"],
            "observed_objects": defaultdict(list),
        }
        
        self.observed_objects = self.state["observed_objects"] # as a reference
        
        ## Unpack the sight matrix
        for x_str, y_dict in state["sight"].items():
            x = int(x_str)
            for y_str, obj_type in y_dict.items():
                y = int(y_str)
                if obj_type in self.ignored_objects:
                    continue 
                last_observed_objects = None
                self.observed_objects[obj_type].append([x, y])
        

    def nothing_new_observed(self, perfect_effects):
        return all(
            self.last_observed_objects[obj_type] == self.observed_objects[obj_type] 
            for obj_type in self.observed_objects
            if not perfect_effects or obj_type != Tiles.SUPER
        )

    def observed(self, obj_type):
        return obj_type in self.observed_objects
        
    def closest_object(self, obj_type):
        """Find the closest object based on the heuristic"""
        closest = None
        min_heuristic = None

        for obj in self.observed_objects[obj_type]:
            heuristic = self.domain.heuristic(self.state, obj)
            
            if min_heuristic is None or heuristic < min_heuristic:
                min_heuristic = heuristic
                closest = obj

        return closest                    
        
