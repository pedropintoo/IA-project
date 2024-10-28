import heapq
from src.exploration_path import ExplorationPath
from src.matrix_operations import MatrixOperations

class Mapping:
    def __init__(self, matrix):
        self.last_observed_objects = {}
        self.observed_objects = {}
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
        
    def next_exploration(self, body, sight_range, traverse) -> tuple:
        return self.exploration_path.next_exploration_point(body, sight_range, traverse, self.super_foods, self.exploration_map)



