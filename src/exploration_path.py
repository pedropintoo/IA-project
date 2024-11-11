import math

class ExplorationPath:
    
    def __init__(self, internal_walls, height, width, dead_ends=None):
        self.internal_walls = internal_walls
        self.height = height
        self.width = width
        self.dead_ends = dead_ends
        
        self.exploration_path = []
        
    def next_exploration_point(self, body, sight_range, traverse, exploration_map):
        head = body[0]
        if len(self.exploration_path) == 0:
            unseen_cells = self.get_unseen_cells(exploration_map, traverse, body)
            if unseen_cells:
                target = self.find_best_target(head, sight_range, unseen_cells)
                self.exploration_path = GilbertCurve.get_curve(self.width, self.height, target, sight_range)
        
        #self.print_exploration_path()
        while self.exploration_path:
            point = list(self.exploration_path[0])
            if (traverse or point not in self.internal_walls) and point not in body:
                return list(self.exploration_path.pop(0))
            else:
                self.exploration_path.pop(0)
        return None

    def peek_exploration_point(self, body, sight_range, traverse, exploration_map):
        head = body[0]
        if len(self.exploration_path) == 0:
            unseen_cells = self.get_unseen_cells(exploration_map, traverse, body)
            if unseen_cells:
                target = self.find_best_target(head, sight_range, unseen_cells)
                self.exploration_path = GilbertCurve.get_curve(self.width, self.height, target, sight_range)
        
        while self.exploration_path:
            point = list(self.exploration_path[0])
            if (traverse or point not in self.internal_walls) and point not in body:
                return point
            else:
                self.exploration_path.pop(0)
        return None

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
                if (x, y) in self.exploration_path:
                    row += "X"
                else:
                    row += "."
            print(row)

class GilbertCurve:
    def get_curve(width, height, target, sight_range=1):
        path = list(GilbertCurve.gilbert2d(width, height, sight_range*2))
        adjusted_path = [(x * sight_range*2, y * sight_range*2) for x, y in path]
        adjusted_path = GilbertCurve.adjust_path_to_target(adjusted_path, target)
        return adjusted_path
    
    @staticmethod
    def gilbert2d(width, height, sight_range):
        virtual_width = (width + sight_range - 1) // sight_range
        virtual_height = (height + sight_range - 1) // sight_range

        if width >= height:
            yield from GilbertCurve.generate2d(0, 0, virtual_width, 0, 0, virtual_height)
        else:
            yield from GilbertCurve.generate2d(0, 0, 0, virtual_height, virtual_width, 0)
    
    @staticmethod
    def sgn(x):
        return -1 if x < 0 else (1 if x > 0 else 0)

    @staticmethod
    def generate2d(x, y, ax, ay, bx, by):

        w = abs(ax + ay)
        h = abs(bx + by)

        (dax, day) = (GilbertCurve.sgn(ax), GilbertCurve.sgn(ay)) # unit major direction
        (dbx, dby) = (GilbertCurve.sgn(bx), GilbertCurve.sgn(by)) # unit orthogonal direction

        if h == 1:
            # trivial row fill
            for i in range(0, w):
                yield(x, y)
                (x, y) = (x + dax, y + day)
            return

        if w == 1:
            # trivial column fill
            for i in range(0, h):
                yield(x, y)
                (x, y) = (x + dbx, y + dby)
            return

        (ax2, ay2) = (ax//2, ay//2)
        (bx2, by2) = (bx//2, by//2)

        w2 = abs(ax2 + ay2)
        h2 = abs(bx2 + by2)

        if 2*w > 3*h:
            if (w2 % 2) and (w > 2):
                # prefer even steps
                (ax2, ay2) = (ax2 + dax, ay2 + day)

            # long case: split in two parts only
            yield from GilbertCurve.generate2d(x, y, ax2, ay2, bx, by)
            yield from GilbertCurve.generate2d(x+ax2, y+ay2, ax-ax2, ay-ay2, bx, by)

        else:
            if (h2 % 2) and (h > 2):
                # prefer even steps
                (bx2, by2) = (bx2 + dbx, by2 + dby)

            # standard case: one step up, one long horizontal, one step down
            yield from GilbertCurve.generate2d(x, y, bx2, by2, ax2, ay2)
            yield from GilbertCurve.generate2d(x+bx2, y+by2, ax, ay, bx-bx2, by-by2)
            yield from GilbertCurve.generate2d(x+(ax-dax)+(bx2-dbx), y+(ay-day)+(by2-dby),
                                  -bx2, -by2, -(ax-ax2), -(ay-ay2))

    @staticmethod
    def adjust_path_to_target(path, target):
        if target in path:
            target_index = path.index(target)
            return path[target_index:] + path[:target_index]
        else:
            # Find the closest_point in the path to the target
            closest_point = min(path, key=lambda p: math.dist(p, target))
            closest_point_index = path.index(closest_point)
            return path[closest_point_index:] + path[:closest_point_index]

if __name__ == "__main__":
    jorge = GilbertCurve.get_curve(48,24,(10,10), 4)
    for jorginho in jorge:
        print(tuple(jorginho))
