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
    
    def next_point_v2(self, body, sight_range, exploration_map, traverse, is_ignored_goal):
        head = body[0]
        exploration_point_seen_threshold = get_exploration_point_seen_threshold(sight_range, traverse)

        min_density = None
        closest_point = None
        min_distance = None

        # Define a reasonable search radius around the snake's head to limit computation
        search_radius = 5 * sight_range  # Adjust based on performance needs

        # Generate positions within the search radius
        positions_to_evaluate = []
        for dx in range(-search_radius, search_radius + 1):
            for dy in range(-search_radius, search_radius + 1):
                if abs(dx) + abs(dy) > search_radius:
                    continue  # Skip points outside the search radius
                x = head[0] + dx
                y = head[1] + dy
                if traverse:
                    x %= self.width
                    y %= self.height
                else:
                    if x < 0 or x >= self.width or y < 0 or y >= self.height:
                        continue  # Skip out-of-bounds positions
                positions_to_evaluate.append((x, y))

        for point in positions_to_evaluate:
            if point in body:
                continue  # Skip snake's body
            if is_ignored_goal(point):
                continue  # Skip ignored goals

            # Calculate density
            density = self.calcule_average_seen_density(point, sight_range, exploration_map)
            if density > exploration_point_seen_threshold:
                continue  # Skip points exceeding density threshold

            # Calculate distance to head
            distance = self.calcule_distance(traverse, head, point)

            # Select point with acceptable density and minimal distance
            if closest_point is None or distance < min_distance:
                closest_point = point
                min_distance = distance

        return closest_point  # Returns None if no suitable point is found


    def next_exploration_point(self, body, sight_range, traverse, exploration_map, is_ignored_goal):
        # if not traverse or sight_range in [5, 6]:
        #     return self.next_point_v2(body, sight_range, exploration_map, traverse, is_ignored_goal)

        exploration_length_threshold = get_exploration_length_threshold(sight_range)
        # last_exploration_distance_threshold = get_last_exploration_distance_threshold(sight_range, body[0], self.width)

        # if self.calcule_distance(traverse, body[0], self.last_given_point) > last_exploration_distance_threshold:
        #     self.exploration_path = []
        
        if len(self.exploration_path) < exploration_length_threshold:
            print("REGENERATING PATH BECAUSE OF LENGTH AFTER NEXT REQUEST")
            self.generate_exploration_path(body[0], sight_range, exploration_map, traverse, False)

        # self.print_exploration_path()
        exploration_point_seen_threshold = get_exploration_point_seen_threshold(sight_range, traverse)
        # limit_iterations = 45 / sight_range
        while self.exploration_path:
            
            if len(self.exploration_path) < exploration_length_threshold: #or limit_iterations <= 0:
                print("REGENERATING PATH BECAUSE OF LENGTH INSIDE THE LOOP")
                self.generate_exploration_path(body[0], sight_range, exploration_map, traverse, False)
            
            point = list(self.exploration_path.pop(0))

            average_seen_density = self.calcule_average_seen_density(point, sight_range, exploration_map)

            #if self.is_valid_point(point, body, traverse, average_seen_density, exploration_point_seen_threshold) and (not is_ignored_goal(tuple(point)) or limit_iterations <= 0):
            if not is_ignored_goal(point) and self.is_valid_point(point, body, traverse, average_seen_density, exploration_point_seen_threshold):# or limit_iterations <= 0:
                self.last_given_point = point
                return point    

            print(f"---------->POINT SKIPPED {point}")

            if is_ignored_goal(point):
                print(f"Reason: IS AN IGNORED GOAL!")
                is_ignored_goal(point, debug=True)
            
            if not self.is_valid_point(point, body, traverse, average_seen_density, exploration_point_seen_threshold):
                print(f"Reason: NOT A VALID POINT!")
 

            # limit_iterations -= 1 # Avoid infinite loop 

    def peek_exploration_point(self, body, traverse, exploration_map, n_points, is_ignored_goal, goal_position):
        x_range, y_range = self.get_quadrant(goal_position)
        area_to_check = max(self.width, self.height) // 8
    
        min_obstacles = float('inf')
        best_point = None

        for x in x_range:
            for y in y_range:
                point = (x, y)
                if not self.is_valid_point(point, body, traverse):
                    continue
                    
                obstacles = self.count_obstacles_around_point(point, body, traverse, area_to_check)
                if obstacles < min_obstacles:
                    min_obstacles = obstacles
                    best_point = point

                    if obstacles == 0:
                        return best_point
        return best_point

    def is_valid_point(self, point, body, traverse, average_seen_density=None, exploration_point_seen_threshold=None):
        if average_seen_density is None or exploration_point_seen_threshold is None:
            # VALIDATION OF PEEK
            return (traverse or point not in self.internal_walls) and point not in body
        else:
            # VALIDATION OF NEXT POINT
            print("BODY IN VALIDATION POINT:", body)

            if (not traverse and point in self.internal_walls):
                print("POINT IN WALLS")
            
            if point in body:
                print("POINT IN BODY")
                
            if average_seen_density >= exploration_point_seen_threshold:
                print("POINT ABOVE SEEN THRESHOLD")
                print(f"AVERAGE = {average_seen_density} THRESHOLD = {exploration_point_seen_threshold}")

            return (traverse or point not in self.internal_walls) and point not in body and (average_seen_density < exploration_point_seen_threshold or point[1] == 0)
            
    def count_obstacles_around_point(self, point, body, traverse, area_to_check):
        x0, y0 = point
        count = 0
        obstacles = set(map(tuple, body)) if traverse else set(map(tuple, body)) | set(map(tuple, self.internal_walls))

        for dx in range(-area_to_check, area_to_check + 1):
            for dy in range(-area_to_check, area_to_check + 1):
                x = (x0 + dx) % self.width if traverse else x0 + dx
                y = (y0 + dy) % self.height if traverse else y0 + dy

                if x < 0 or x >= self.width or y < 0 or y >= self.height:
                    # If the point is out of bounds, it is considered an obstacle
                    count += 1
                    continue

                if (x, y) in obstacles:
                    count += 1
                
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
            
    def find_best_target(self, head, exploration_path, exploration_map, traverse, peek, sight_range):
        if peek:
            best_distance = float('inf')
            best_target = None
            for (x, y) in exploration_path[::-1]:
                distance = self.calcule_distance(traverse, head, (x, y))
                if distance < best_distance and self.last_given_point != [x, y]: #and distance >= 4 * sight_range:
                    best_distance = distance
                    best_target = (x, y)
            return best_target
        else:
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

    def get_quadrant(self, point):
        x, y = point
        width_mid = self.width // 2
        height_mid = self.height // 2

        if x < width_mid:
            x_range = range(0, width_mid)
        else:
            x_range = range(width_mid, self.width)
        
        if y < height_mid:
            y_range = range(0, height_mid)
        else:
            y_range = range(height_mid, self.height)
        
        return x_range, y_range
    
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

if __name__ == "__main__":
    jorge = GilbertCurve.get_curve(48,24, 2, True)
    for jorginho in jorge:
        print(tuple(jorginho))
    print(len(jorge))
