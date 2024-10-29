import heapq
import random
from collections import defaultdict
from src.exploration_path import ExplorationPath
from src.matrix_operations import MatrixOperations
from consts import Tiles

class Mapping:
    def __init__(self, matrix):
        self.state = None
        
        self.last_observed_objects = None
        self.observed_objects = defaultdict(list)
        self.super_foods = []
        self.exploration_map = []
        
        self.height = len(matrix)
        self.width = len(matrix[0])
        self.walls = MatrixOperations.find_ones(matrix)
        
        self.exploration_path = ExplorationPath(
            walls=self.walls, 
            dead_ends=MatrixOperations.find_dead_ends(matrix), 
            height=self.height, 
            width=self.width
        )
        
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
        self.state = state
        self.last_observed_objects = self.observed_objects.copy()
        self.observed_objects = defaultdict(list)
        
        for x_str, y_dict in state["sight"].items():
            x = int(x_str)
            for y_str, value in y_dict.items():
                y = int(y_str)
                if value in self.ignored_objects:
                    continue # TODO: change the ignore_object
                self.observed_objects[value].append([x, y])

    def nothing_new_observed(self, perfect_effects):
        if perfect_effects:
            return all(
                self.last_observed_objects[obj_type] == self.observed_objects[obj_type] 
                for obj_type in self.observed_objects
                if obj_type != Tiles.SUPER
            )
            
        return all(
            self.last_observed_objects[obj_type] == self.observed_objects[obj_type] 
            for obj_type in self.observed_objects
        )
        

    def observed(self, obj_type):
        return obj_type in self.observed_objects
        
    def closest_object(self, obj_type):
        # TODO: implement
        # for now, random choice
        return random.choice(self.observed_objects[obj_type])
        
            
        
