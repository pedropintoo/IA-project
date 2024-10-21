import math

class ExplorationHilbertCurve:
    
    def __init__(self, matrix, width, height):
        self.matrix = matrix
        self.width = width
        self.height = height

        self.exploration_path = []
    
    def get_exploration_path(self, sight_range: int):
        self.exploration_path = []
        order = self.minimum_hilbert_order(self.width, self.height, sight_range*2) # sight_range*2 due to distance between two points
        self.hilbert_curve(0, 0, self.width, 0, 0, self.height, order)
    
    def hilbert_curve(self, x0, y0, xi, xj, yi, yj, order):
        """ Generate a Hilbert curve of a given order """
        if order <= 0:
            X = x0 + (xi + yi) // 2
            Y = y0 + (xj + yj) // 2
            self.exploration_path.append([X, Y])
        else:
            # Recursively generate the four segments of the Hilbert curve
            self.hilbert_curve(x0, y0, yi//2, yj//2, xi//2, xj//2, order - 1)
            self.hilbert_curve(x0 + xi//2, y0 + xj//2, xi//2, xj//2, yi//2, yj//2, order - 1)
            self.hilbert_curve(x0 + xi//2 + yi//2, y0 + xj//2 + yj//2, xi//2, xj//2, yi//2, yj//2, order - 1)
            self.hilbert_curve(x0 + xi//2 + yi, y0 + xj//2 + yj, -yi//2,-yj//2,-xi//2,-xj//2, order - 1)

    def minimum_hilbert_order(self, grid_width, grid_height, sight_range):
        """Calculate the minimum Hilbert curve order to ensure no two points are farther apart than sight_range."""
        num_cells_width = math.ceil(grid_width / sight_range)
        num_cells_height = math.ceil(grid_height / sight_range)
        max_dimension = max(num_cells_width, num_cells_height)
        
        # The Hilbert curve of order 'n' can cover a 2^n x 2^n grid
        order = math.ceil(math.log2(max_dimension))
        return order
     

class Matrix:
    
    def __init__(self, matrix):
        self.matrix = matrix
        self.width = len(matrix)
        self.height = len(matrix[0])
        self.exploration = ExplorationHilbertCurve(matrix, self.width, self.height)
    
    def get_exploration_path(self, sight_range: int):
        self.exploration.get_exploration_path(sight_range)
        return self.exploration.exploration_path
        
    def find_ones(self):
        ones_coordinates = []
        for row_idx, row in enumerate(self.matrix):
            for col_idx, value in enumerate(row):
                if value == 1:
                    ones_coordinates.append([row_idx, col_idx])
        return ones_coordinates


        