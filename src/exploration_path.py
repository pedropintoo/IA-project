import math

class ExplorationPath:
    
    def __init__(self, walls, dead_ends, height, width):
        self.walls = walls
        self.dead_ends = dead_ends
        self.height = height
        self.width = width
        
        self.exploration_path = []
        
    def next_exploration_point(self, body, range, traverse, super_foods, exploration_map):
        # TODO: fix the Hilbert curves
        if len(self.exploration_path) == 0:
            self.exploration_path = HilbertCurve.get_curve(self.width, self.height, range)
        
        return self.exploration_path.pop(0)

class HilbertCurve:
    
    @staticmethod
    def get_curve(width, height, sight_range):
        print("....--",width, height, sight_range)
        order = HilbertCurve.minimum_hilbert_order(width, height, sight_range * 2)  # sight_range * 2 for distance between points
        exploration_path = []  # Initialize the exploration path list
        HilbertCurve.hilbert_curve(0, 0, width, 0, 0, height, order, exploration_path)
        return exploration_path
    
    @staticmethod
    def hilbert_curve(x0, y0, xi, xj, yi, yj, order, exploration_path):
        """ Generate a Hilbert curve of a given order """
        if order <= 0:
            X = x0 + (xi + yi) // 2
            Y = y0 + (xj + yj) // 2
            exploration_path.append([X, Y])
        else:
            # Recursively generate the four segments of the Hilbert curve
            HilbertCurve.hilbert_curve(x0, y0, yi // 2, yj // 2, xi // 2, xj // 2, order - 1, exploration_path)
            HilbertCurve.hilbert_curve(x0 + xi // 2, y0 + xj // 2, xi // 2, xj // 2, yi // 2, yj // 2, order - 1, exploration_path)
            HilbertCurve.hilbert_curve(x0 + xi // 2 + yi // 2, y0 + xj // 2 + yj // 2, xi // 2, xj // 2, yi // 2, yj // 2, order - 1, exploration_path)
            HilbertCurve.hilbert_curve(x0 + xi // 2 + yi, y0 + xj // 2 + yj, -yi // 2, -yj // 2, -xi // 2, -xj // 2, order - 1, exploration_path)

    @staticmethod
    def minimum_hilbert_order(grid_width, grid_height, sight_range):
        """Calculate the minimum Hilbert curve order to ensure no two points are farther apart than sight_range."""
        num_cells_width = math.ceil(grid_width / sight_range)
        num_cells_height = math.ceil(grid_height / sight_range)
        max_dimension = max(num_cells_width, num_cells_height)
        
        # The Hilbert curve of order 'n' can cover a 2^n x 2^n grid
        order = math.ceil(math.log2(max_dimension))
        return order

# if __name__ == "__main__":
#     HilbertCurve.get_curve(, 10, 2)
