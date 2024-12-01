import math
from src.utils._consts import get_exploration_length_threshold, get_last_exploration_distance_threshold, get_exploration_point_seen_threshold

class ExplorationPath:
    
    def __init__(self, internal_walls, height, width, dead_ends=None):
        self.internal_walls = internal_walls
        self.height = height
        self.width = width
        self.dead_ends = dead_ends
        
        self.exploration_path = []
        self.exploration_generations_cache = {}
        self.last_given_point = None

    def generate_exploration_path(self, head, sight_range, exploration_map, traverse, peek):
        
        if not peek:
            exploration_path = self.exploration_path
        else:
            exploration_path = []
     
        if self.exploration_generations_cache.get(sight_range) is None:
            new_exploration_path = GilbertCurve.get_curve(self.width, self.height, sight_range, traverse)
            self.exploration_generations_cache[sight_range] = new_exploration_path
        else:
            new_exploration_path = self.exploration_generations_cache[sight_range]
        
        if len(exploration_path) == 0:
            target = self.find_best_target(head, new_exploration_path, exploration_map, traverse, peek, sight_range)
        else:
            target = exploration_path.pop(-1)
        
        if not peek:
            self.exploration_path += GilbertCurve.adjust_path_to_target(new_exploration_path, target)
        else:
            return GilbertCurve.adjust_path_to_target(new_exploration_path, target)
    
    def generate_exploration_path_v2(self, body, sight_range, exploration_map, traverse):
        density_threshold = get_exploration_point_seen_threshold(sight_range)
        
        cluster_centers = self.cluster_unseen_cells(sight_range, density_threshold, exploration_map, traverse, body)

        ordered_points = self.order_cluster_centers(cluster_centers, body[0], traverse)
        
        self.exploration_path = ordered_points

    def next_exploration_point(self, body, sight_range, traverse, exploration_map, is_ignored_goal):
        exploration_length_threshold = get_exploration_length_threshold(sight_range)
        last_exploration_distance_threshold = get_last_exploration_distance_threshold(sight_range, body[0], self.width)

        if self.calcule_distance(traverse, body[0], self.last_given_point) > last_exploration_distance_threshold:
            self.exploration_path = []
        
        if len(self.exploration_path) < exploration_length_threshold:
            # self.generate_exploration_path(body[0], sight_range, exploration_map, traverse, False)
            self.generate_exploration_path_v2(body, sight_range, exploration_map, traverse)

        # self.print_exploration_path()
        exploration_point_seen_threshold = get_exploration_point_seen_threshold(sight_range)
        limit_iterations = 10
        while self.exploration_path:
            
            if len(self.exploration_path) < exploration_length_threshold or limit_iterations <= 0:
                # self.generate_exploration_path(body[0], sight_range, exploration_map, traverse, False)
                self.generate_exploration_path_v2(body, sight_range, exploration_map, traverse)
            
            point = list(self.exploration_path.pop(0))

            average_seen_density = self.calcule_average_seen_density(point, sight_range, exploration_map)

            if self.is_valid_point(point, body, traverse, is_ignored_goal, average_seen_density, exploration_point_seen_threshold) or limit_iterations <= 0:
                self.last_given_point = point
                return point          

            limit_iterations -= 1 # Avoid infinite loop 

    def peek_exploration_point(self, body, traverse, exploration_map, n_points, is_ignored_goal, goal_position):
        points_to_return = []
        sight_range = 2
        exploration_path_to_peek = self.generate_exploration_path(goal_position, sight_range, exploration_map, traverse, True)

        limit_iterations = 10
        while len(points_to_return) < n_points:
            
            if len(exploration_path_to_peek) < n_points or limit_iterations <= 0:
                self.generate_exploration_path(body, sight_range, exploration_map, traverse, exploration_path_to_peek)

            point = list(exploration_path_to_peek.pop(0))
            #if (traverse or point not in self.internal_walls) and point not in body and (not is_ignored_goal(point) or limit_iterations <= 0):
            if (not is_ignored_goal(point) or limit_iterations <= 0):
                points_to_return.append(point)
            
            limit_iterations -= 1 # Avoid infinite loop
        
        return points_to_return
    
    def is_valid_point(self, point, body, traverse, is_ignored_goal, average_seen_density=None, exploration_point_seen_threshold=None):
        if average_seen_density is None or exploration_point_seen_threshold is None:
            return (traverse or point not in self.internal_walls) and point not in body and not is_ignored_goal(tuple(point))
        else:
            return (traverse or point not in self.internal_walls) and point not in body and average_seen_density < exploration_point_seen_threshold and not is_ignored_goal(tuple(point))
            
    
    def calcule_average_seen_density(self, point, sight_range, exploration_map):
        count = 0
        n_points = 0
        for dx in range(-sight_range, sight_range + 1):
            for dy in range(-sight_range, sight_range + 1):
                if abs(dx) + abs(dy) <= sight_range:
                    if (point[0] + dx, point[1] + dy) in exploration_map:
                        count += exploration_map[(point[0] + dx, point[1] + dy)][0]
                        n_points += 1
        return count / n_points if n_points > 0 else 0
    
    def calcule_distance(self, traverse, a, b):
        dx = 0
        dy = 0
        if a is not None and b is not None:
            dx_no_crossing_walls = abs(a[0] - b[0])
            dx = min(dx_no_crossing_walls, self.width - dx_no_crossing_walls) if traverse else dx_no_crossing_walls
            dy_no_crossing_walls = abs(a[1] - b[1])
            dy = min(dy_no_crossing_walls, self.height - dy_no_crossing_walls) if traverse else dy_no_crossing_walls

        return dx + dy
            
    def find_best_target(self, head, exploration_path, exploration_map, traverse, peek, sight_range):
        if peek:
            best_distance = float('inf')
            best_target = None
            for (x, y) in exploration_path[::-1]:
                distance = self.calcule_distance(traverse, head, (x, y))
                if distance < best_distance and distance >= 4 * sight_range:
                    best_distance = distance
                    best_target = (x, y)
            return best_target
        else:
            max_unseen_cells = -1
            best_distance = float('inf')
            best_target = None
            for (x, y) in exploration_path[::-1]:
                if exploration_map.get((x, y), [0])[0] == 0:
                    unseen_cells_count = self.count_unseen_cells((x, y), sight_range, exploration_map)
                    distance = self.calcule_distance(traverse, head, (x, y))
                    if unseen_cells_count > max_unseen_cells or (unseen_cells_count == max_unseen_cells and distance < best_distance):
                        max_unseen_cells = unseen_cells_count
                        best_distance = distance
                        best_target = (x, y)
            return best_target

    def count_unseen_cells(self, point, sight_range, exploration_map):
        count = 0
        x, y = point
        for dx in range(-sight_range, sight_range + 1):
            for dy in range(-sight_range, sight_range + 1):
                if abs(dx) + abs(dy) <= sight_range:
                    cell = (x + dx, y + dy)
                    if exploration_map.get(cell, [0])[0] == 0:
                        count += 1
        return count

    def get_low_density_unseen_cells(self, exploration_map, density_threshold, sight_range, traverse, body):
        unseen_cells = []
        for (x,y), (seen_value, _) in exploration_map.items():
            if (traverse or [x, y] not in self.internal_walls) and seen_value == 0 and [x, y] not in body:
                density = self.calcule_average_seen_density((x, y), sight_range, exploration_map)
                if density < density_threshold:
                    unseen_cells.append((x, y))
        
        sorted_cells = sorted(
            unseen_cells,
            key=lambda cell: self.calcule_average_seen_density(cell, sight_range, exploration_map)
        )

        return sorted_cells
    
    def cluster_unseen_cells(self, sight_range, density_threshold, exploration_map, traverse, body):
        low_density_cells = self.get_low_density_unseen_cells(exploration_map, density_threshold, sight_range, traverse, body)

        cluster_centers = []
        min_distance = 2 * sight_range 

        for cell in low_density_cells:
            if all(self.calcule_distance(traverse, cell, center) > min_distance for center in cluster_centers):
                cluster_centers.append(cell)

        return cluster_centers
    
    def order_cluster_centers(self, cluster_centers, start_position, traverse):
        ordered_points = []
        unvisited = set(cluster_centers)
        current_position = start_position

        while unvisited:
            #TODO: Implement with traverse variable
            next_point = min(unvisited, key=lambda p: self.calcule_distance(traverse, current_position, p))
            ordered_points.append(next_point)
            unvisited.remove(next_point)
            current_position = next_point
        
        return ordered_points

    def print_exploration_path(self):
        print("EXPLORATION PATH")
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                if (x, y) in self.exploration_path:
                    row += "X"
                else:
                    row += "."
            print(row)

class GilbertCurve:
    def get_curve(width, height, sight_range=1, traverse=True):
        path = list(GilbertCurve.gilbert2d(width, height, sight_range*2))
        adjusted_path = [(x * sight_range*2 + 1, y * sight_range*2 + 1) for x, y in path]
        
        if not traverse:
            start_point = adjusted_path[0]
            end_point = adjusted_path[-1]
            
            return_path = GilbertCurve.linear_path(end_point, start_point, sight_range * 2)
            
            for point in return_path:
                if point not in adjusted_path:
                    adjusted_path.append(point)
        
        return adjusted_path
    
    def linear_path(start, end, step_size):
        x0, y0 = start
        x1, y1 = end
        points = []
        
        x0 -=1
        y0 -=1
        x1 -=1
        y1 -=1

        dx = x1 - x0
        dy = y1 - y0
        distance = (dx ** 2 + dy ** 2) ** 0.5
        steps = max(1, int(distance // step_size))
        
        for i in range(1, steps + 1):
            x = int(x0 + dx * i / steps)
            y = int(y0 + dy * i / steps)
            points.append((x, y))
        
        return points
    
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
    jorge = GilbertCurve.get_curve(48,24, 3, True)
    for jorginho in jorge:
        print(tuple(jorginho))
    print(len(jorge))
