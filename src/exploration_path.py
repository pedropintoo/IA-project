import math

class ExplorationPath:
    
    def __init__(self, internal_walls, height, width, dead_ends=None):
        self.internal_walls = internal_walls
        self.height = height
        self.width = width
        self.dead_ends = dead_ends
        
        self.exploration_path = []
        self.exploration_generations_cache = {}
    
    def generate_exploration_path(self, body, sight_range, exploration_map, exploration_path=None):
        head = body[0]

        if exploration_path is None:
            exploration_path = self.exploration_path
     
        if self.exploration_generations_cache.get(sight_range) is None:
            new_exploration_path = GilbertCurve.get_curve(self.width, self.height, sight_range)
            self.exploration_generations_cache[sight_range] = new_exploration_path
        else:
            new_exploration_path = self.exploration_generations_cache[sight_range]
        
        if len(exploration_path) == 0:
            target = self.find_best_target(head, new_exploration_path, exploration_map)
        else:
            target = exploration_path.pop(-1)
        
        exploration_path += GilbertCurve.adjust_path_to_target(new_exploration_path, target)
        
    def next_exploration_point(self, body, sight_range, traverse, exploration_map):
        exploration_length_threshold = 20 // sight_range
        
        if len(self.exploration_path) < exploration_length_threshold:
            self.generate_exploration_path(body, sight_range, exploration_map)

        self.print_exploration_path()
        exploration_point_seen_threshold = sight_range * 1.5
        while self.exploration_path:
            point = list(self.exploration_path.pop(0))

            average_seen_density = self.calcule_average_seen_density(point, sight_range, exploration_map)

            if (traverse or point not in self.internal_walls) and point not in body and average_seen_density < exploration_point_seen_threshold:
                return point
            

    def peek_exploration_point(self, body, sight_range, traverse, exploration_map, n_points):
        points_to_return = []
        exploration_path_to_peek = self.exploration_path.copy()

        while len(points_to_return) < n_points:
            if len(exploration_path_to_peek) < n_points:
                self.generate_exploration_path(body, sight_range, exploration_map, exploration_path_to_peek)

            exploration_point_seen_threshold = sight_range * 1.5
            point = list(exploration_path_to_peek.pop(0))
            average_seen_density = self.calcule_average_seen_density(point, sight_range, exploration_map)
            if (traverse or point not in self.internal_walls) and point not in body and average_seen_density < exploration_point_seen_threshold:
                points_to_return.append(point)
            else:
                self.exploration_path.pop(0)
        
        return points_to_return
    
    def calcule_average_seen_density(self, point, sight_range, exploration_map):
        count = 0
        n_points = 0
        for dx in range(-sight_range, sight_range + 1):
            for dy in range(-sight_range, sight_range + 1):
                if abs(dx) + abs(dy) <= sight_range:
                    if (point[0] + dx, point[1] + dy) in exploration_map:
                        count += exploration_map[(point[0] + dx, point[1] + dy)][0]
                        n_points += 1
        return count / n_points


    def find_best_target(self, head, exploration_path, exploration_map):
        best_distance = float('inf')
        best_target = None
        for (x, y) in exploration_path:
            distance = math.dist((x, y), head)
            if distance < best_distance:
                if exploration_map[(x, y)][0] == 0:
                    best_distance = distance
                    best_target = (x, y)
        
        return best_target


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
    def get_curve(width, height, sight_range=1):
        path = list(GilbertCurve.gilbert2d(width, height, sight_range*2))
        adjusted_path = [(x * sight_range*2, y * sight_range*2) for x, y in path]
        return adjusted_path
    
    @staticmethod
    def gilbert2d(width, height, sight_range):
        virtual_width = (width + sight_range-1) // sight_range
        virtual_height = (height + sight_range-1) // sight_range

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
    jorge = GilbertCurve.get_curve(70,53, 4)
    for jorginho in jorge:
        print(tuple(jorginho))
    print(len(jorge))
