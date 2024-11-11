import math

class ExplorationPath:
    
    def __init__(self, internal_walls, dead_ends, height, width):
        self.internal_walls = internal_walls
        self.height = height
        self.width = width
        
        self.exploration_path = []
        
    def next_exploration_point(self, body, sight_range, traverse, super_foods, exploration_map):
        head = body[0]
        if len(self.exploration_path) == 0:
            unseen_cells = self.get_unseen_cells(exploration_map, traverse, body)
            if unseen_cells:
                target = self.find_best_target(head, sight_range, unseen_cells)
                self.exploration_path = HilbertCurve.get_curve(self.width, self.height, sight_range, target)
        
        #self.print_exploration_path()
        return list(self.exploration_path.pop(0))

    def get_unseen_cells(self, exploration_map, traverse, body):
        unseen_cells = set()
        for (x, y), value in exploration_map.items():
            if value[0] == 0 and (traverse or (x, y) not in self.internal_walls) and (x, y) not in body:
                unseen_cells.add((x, y))
        return unseen_cells

    def find_best_target(self, head, sight_range, unseen_cells):
        max_unseen = 0
        best_distance = float('inf')
        best_target = None
        unseen_counts_cache = {}
        for cell in unseen_cells:
            unseen_count = self.count_unseen_from_point(cell, sight_range, unseen_cells, unseen_counts_cache)
            distance = abs(cell[0] - head[0]) + abs(cell[1] - head[1])
            if unseen_count > max_unseen or (unseen_count == max_unseen and distance < best_distance):
                max_unseen = unseen_count
                best_distance = distance
                best_target = cell
        return best_target

    def count_unseen_from_point(self, point, sight_range, unseen_cells, cache):
        if point in cache:
            return cache[point]
        count = 0
        for dx in range(-sight_range, sight_range + 1):
            for dy in range(-sight_range, sight_range + 1):
                if (point[0] + dx, point[1] + dy) in unseen_cells:
                    count += 1
        cache[point] = count
        return count

    def print_exploration_path(self):
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                if [x, y] in self.exploration_path:
                    row += "X"
                else:
                    row += "."
            print(row)

class HilbertCurve:
    
    @staticmethod
    def get_curve(width, height, sight_range, target):
        order = HilbertCurve.minimum_hilbert_order(width, height, sight_range * 2)
        exploration_path = []
        HilbertCurve.hilbert_curve(0, 0, width, 0, 0, height, order, exploration_path)
        return HilbertCurve.adjust_path_to_target(exploration_path, target)
    
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

    @staticmethod
    def adjust_path_to_target(path, target):
        if target in path:
            target_index = path.index(target)
            return path[target_index:] + path[:target_index]
        else:
            path.insert(0, target)
            return path

# if __name__ == "__main__":
#     HilbertCurve.get_curve(, 10, 2)
