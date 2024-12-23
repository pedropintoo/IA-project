import math
from src.utils._consts import get_exploration_length_threshold, get_last_exploration_distance_threshold, get_exploration_point_seen_threshold

class ExplorationPath:
    
    def __init__(self, internal_walls, height, width):
        self.internal_walls = internal_walls
        self.height = height
        self.width = width
        
        self.exploration_path = []
        self.exploration_generations_cache = {}
        self.last_given_point = None

    def generate_exploration_path(self, head, sight_range, exploration_map, traverse):
        
        exploration_path = self.exploration_path

        if self.exploration_generations_cache.get((sight_range, traverse)) is None:
            new_exploration_path = GilbertCurve.get_curve(self.width, self.height, sight_range, traverse)
            self.exploration_generations_cache[(sight_range, traverse)] = new_exploration_path
        else:
            new_exploration_path = self.exploration_generations_cache[(sight_range, traverse)]
        
        if len(exploration_path) == 0:
            target = self.find_best_target(head, new_exploration_path, exploration_map, traverse, sight_range)
        else:
            target = exploration_path.pop(-1)
        
        self.exploration_path += GilbertCurve.adjust_path_to_target(new_exploration_path, target)

    def next_exploration_point(self, body, sight_range, traverse, exploration_map, is_ignored_goal):

        exploration_length_threshold = get_exploration_length_threshold(sight_range)
        if len(self.exploration_path) < exploration_length_threshold:
            self.generate_exploration_path(body[0], sight_range, exploration_map, traverse)

        exploration_point_seen_threshold = get_exploration_point_seen_threshold(sight_range, traverse)
        while self.exploration_path:
            
            if len(self.exploration_path) < exploration_length_threshold:
                self.generate_exploration_path(body[0], sight_range, exploration_map, traverse)
            
            point = list(self.exploration_path.pop(0))

            average_seen_density = self.calcule_average_seen_density(point, sight_range, exploration_map)

            if not is_ignored_goal(point) and self.is_valid_point(point, body, traverse, average_seen_density, exploration_point_seen_threshold):
                self.last_given_point = point
                return point    

    def peek_exploration_point(self, body, traverse, exploration_map, n_points, is_ignored_goal, goal_position):
        density = []
        quadrant_height = self.height // 2
        quadrant_width = self.width // 2

        x0, y0 = self.get_quadrant(body[0], traverse, quadrant_width, quadrant_height) 
        area_to_check = max(self.width, self.height) // 32
        best_points = []

        ranges_x = [(x0, x0+quadrant_width//2), (x0+quadrant_width//2, x0 + quadrant_width)]
        ranges_y = [(y0, y0+quadrant_height//2), (y0+quadrant_height//2, y0 + quadrant_height)]
        
        for range_x in ranges_x:
            for range_y in ranges_y:
                x_range = range(range_x[0], range_x[1])
                y_range = range(range_y[0], range_y[1])

                best_point_in_quadrant, quadrant_density = self.search_best_point_in_quadrant(x_range, y_range, body, traverse, is_ignored_goal, area_to_check)
                #print(best_point_in_quadrant)
                if best_point_in_quadrant:
                    best_points.append(best_point_in_quadrant)
                    density.append(quadrant_density)

        ## Sort by quadrant (density)
        return [point for _, point in sorted(zip(density, best_points), key=lambda x: x[0])]
    
    def search_best_point_in_quadrant(self, x_range, y_range, body, traverse, is_ignored_goal, area_to_check):
        best_point = None
        quadrant_density = 0
        min_obstacles = None
        
        for x in x_range:
            for y in y_range:
                point = [x % self.width, y % self.height]
                
                quadrant_density += self.obstacle_value(point, traverse, body, is_ignored_goal)
                
                if best_point:
                    continue # already found a point
                
                if not self.is_valid_point(point, body, traverse) or is_ignored_goal(point, debug=True):
                    continue
                                
                obstacles = self.count_obstacles_around_point(point, body, traverse, area_to_check, is_ignored_goal)
                if obstacles == 0:
                    best_point = point
                
        
        return best_point, quadrant_density

    def is_valid_point(self, point, body, traverse, average_seen_density=None, exploration_point_seen_threshold=None):
        if average_seen_density is None or exploration_point_seen_threshold is None:
            return (traverse or point not in self.internal_walls) and point not in body
        else:
            return (traverse or point not in self.internal_walls) and point not in body and (average_seen_density < exploration_point_seen_threshold or point[1] == 0)
    
    def obstacle_value(self, point, traverse, body, is_ignored_goal):
        x = point[0]
        y = point[1]
        count = 0
        
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return 1
        if (not traverse and point in self.internal_walls) or point in body:
            count += 1
        if is_ignored_goal(point):
            count += 2
        
        return count
    
    def count_obstacles_around_point(self, point, body, traverse, area_to_check, is_ignored_goal):
        x0, y0 = point
        count = 0

        for dx in range(-area_to_check, area_to_check + 1):
            for dy in range(-area_to_check, area_to_check + 1):
                x = (x0 + dx) % self.width if traverse else x0 + dx
                y = (y0 + dy) % self.height if traverse else y0 + dy
                count += self.obstacle_value([x, y], traverse, body, is_ignored_goal)
                
        return count
    
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
            
    def find_best_target(self, head, exploration_path, exploration_map, traverse, sight_range):
        exploration_seen_density_threshold = get_exploration_point_seen_threshold(sight_range, traverse)
        best_distance = float('inf')
        best_target = None
        for (x, y) in exploration_path[::-1]:
            average_seen_density = self.calcule_average_seen_density((x, y), sight_range, exploration_map)
            distance = self.calcule_distance(traverse, head, (x, y))
            if average_seen_density < exploration_seen_density_threshold and distance < best_distance:
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

    def get_quadrant(self, point, traverse, quadrant_width, quadrant_height):
        x, y = point
        width_half = quadrant_width // 2
        height_half = quadrant_height // 2

        x_start = (x - width_half) % self.width if traverse else x - width_half
        x_end = (x + width_half) % self.width if traverse else x + width_half
        
        y_start = (y - height_half) % self.height if traverse else y - height_half
        y_end = (y + height_half) % self.height if traverse  else y + height_half


        if x_start < 0:
            x_end += abs(x_start)
            x_start = 0
        
        if x_end >= self.width:
            x_start -= (x_end - self.width + 1)
            x_end = self.width - 1

        if y_start < 0:
            y_end += abs(y_start)
            y_start = 0
        
        if y_end >= self.height:
            y_start -= (y_end - self.height + 1)
            y_end = self.height - 1
        

        return x_start, y_start

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

        if sight_range in [5, 6]:
            num_divisions = max(1, sight_range // 2)

            full_path = []

            for i in range(len(adjusted_path)- 1):
                start = adjusted_path[i]
                end = adjusted_path[i + 1]
                full_path.append(start)

                intermediate_points = GilbertCurve.generate_intermediate_points(start, end, num_divisions)
                full_path.extend(intermediate_points)
            
            full_path.append(adjusted_path[-1])
            adjusted_path = full_path

        return adjusted_path
    
    def generate_intermediate_points(start, end, num_divisions):
        x0, y0 = start
        x1, y1 = end
        points = []

        for i in range(1, num_divisions):
            t = i / num_divisions
            x = x0 + t * (x1 - x0)
            y = y0 + t * (y1 - y0)
            points.append((int(round(x)), int(round(y))))
        
        return points


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

