import heapq
import random
import time
from collections import defaultdict
from src.opponent_mapping import OpponentMapping
from src.exploration_path import ExplorationPath
from src.matrix_operations import MatrixOperations
from src.goal import Goal
from consts import Tiles
from src.utils._consts import get_exploration_point_seen_threshold, get_duration_of_expire_cells, get_food_seen_threshold

class Mapping:
    def __init__(self, logger, domain):
        self.state = None
        
        self.logger = logger
        self.domain = domain

        self.objects_updated = False
        self.observed_objects = None
        self.observation_duration = 90

        self.super_foods = []
        
        self.exploration_path = ExplorationPath(
            internal_walls=domain.internal_walls, 
            dead_ends=domain.dead_ends, 
            height=domain.height,
            width=domain.width
        )
        # TODO: change the ignore_objects
        self.ignored_objects = {Tiles.PASSAGE, Tiles.STONE, Tiles.SNAKE}

        # Cells mapping: 0 - unseen, 1 - seen
        self.cells_mapping = {
            (x, y): (0, None)
            for x in range(self.domain.width)
            for y in range(self.domain.height)
        }   
         
        self.ignored_duration = 5
        self.temp_ignored_goals = set() # ((x, y), observed_timestamp) 
        self.cumulated_ignored_goals = {(x, y): 0.5 for x in range(self.domain.width) for y in range(self.domain.height)}
        
        self.last_step = 0

        self.opponent = OpponentMapping(logger, domain.width, domain.height)

    @property
    def ignored_goals(self):
        for goal, timestamp in self.temp_ignored_goals.copy():
            if time.time() - timestamp > self.cumulated_ignored_goals[goal]:
                self.temp_ignored_goals.remove((goal, timestamp))
        return self.temp_ignored_goals

    def ignore_goal(self, obj_pos):
        self.temp_ignored_goals.add((tuple(obj_pos), time.time()))
        self.cumulated_ignored_goals[tuple(obj_pos)] *= 2 # double the time to ignore the goal
        
        # also remove from the observed objects
        if tuple(obj_pos) in self.observed_objects:
            del self.observed_objects[tuple(obj_pos)]
    
    def is_ignored_goal(self, obj_pos):
        return any(obj_pos[0] == x and obj_pos[1] == y for ((x, y), ts) in self.ignored_goals)
     
    def next_exploration(self) -> tuple:
        self.current_goal = self.exploration_path.next_exploration_point(
            self.state["body"], 
            self.state["range"],
            self.state["traverse"], 
            self.cells_mapping,
            self.is_ignored_goal
        )
        return self.current_goal
    
    def peek_next_exploration(self, n_points=1, force_traverse_disabled=False) -> list:
        return self.exploration_path.peek_exploration_point(
            self.state["body"], 
            self.state["traverse"] and not force_traverse_disabled, 
            self.cells_mapping,
            n_points,
            self.is_ignored_goal,
            self.current_goal
        )

    def update(self, state, perfect_state, goals):
        self.objects_updated = False if self.last_step + 1 != state["step"] else True

        self.opponent.update(state)

        head = state["body"][0]
        self.cumulated_ignored_goals[tuple(head)] = 0.5

        self.logger.debug(f"Old: {self.observed_objects}")
        ## Update the state
        if self.state and self.state["range"] != state["range"]:
            # Reset the exploration path if the range is changed
            self.exploration_path.exploration_path = []
        
        if self.state and self.state["traverse"] != state["traverse"]:
            # Reset the exploration path if the traverse is changed
            self.exploration_path.exploration_path = []

        self.state = {
            "body": state["body"] + [state["body"][-1]], # add the tail
            "range": state["range"],
            "traverse": state["traverse"],
            "observed_objects": self.state["observed_objects"] if self.state else dict(),
            "step": state["step"],
            "visited_goals": set()
        }
        self.update_cells_mapping(state["sight"]) 

        ## Copy for better readability
        self.observed_objects = self.state["observed_objects"] # as a reference

        ## Clear the expired observed objects
        for position, [obj_type, timestamp] in self.observed_objects.copy().items():
            if time.time() - timestamp > self.observation_duration:
                del self.observed_objects[position]

        currently_observed = defaultdict(list)

        for x_str, y_dict in state["sight"].items():
            x = int(x_str)
            for y_str, obj_type in y_dict.items():
                y = int(y_str)
                position = (x, y)
                timestamp = time.time()
                currently_observed[position] = [obj_type, timestamp]                 

        ## Update the observed objects
        for position, [obj_type, timestamp] in currently_observed.items():

            # This position has a object
            if position in self.observed_objects:
                
                # In case, the object is the same
                if obj_type == self.observed_objects[position][0]:
                    self.observed_objects[position][1] = timestamp # update the timestamp
                else:
                    if obj_type in self.ignored_objects:
                        del self.observed_objects[position] # ignore the empty space
                    else:
                        # Update the object type (and current ts)
                        self.observed_objects[position] = [obj_type, timestamp]
                        if not (obj_type == Tiles.SUPER and perfect_state):
                            self.objects_updated = True
            else:
                # This position is new
                if obj_type not in self.ignored_objects:
                    print("NEW - ", obj_type)
                    self.observed_objects[position] = [obj_type, timestamp]
                    if not (obj_type == Tiles.SUPER and perfect_state):
                        self.objects_updated = True
        
        if self.objects_updated:
            print("NEW OBJECTS OBSERVED")
        
        self.print_mapping([goal.position for goal in goals])
        self.logger.debug(f"New: {self.observed_objects}")

    def nothing_new_observed(self, goals):
        if self.objects_updated:
            return False
      
        # TODO: check if the goal has disappeared
        
        first_goal = goals[0]
        
        # TODO: check this!
        if first_goal.goal_type == "exploration":
            x, y = first_goal.position
            sight_range = self.state["range"]
            exploration_point_seen_threshold = get_exploration_point_seen_threshold(sight_range)
            average_seen_density = self.exploration_path.calcule_average_seen_density([x,y], sight_range, self.cells_mapping)
            if average_seen_density >= exploration_point_seen_threshold:
                return False
        elif first_goal.goal_type == "food" or first_goal.goal_type == "super":
            x, y = first_goal.position
            if (x, y) not in self.observed_objects:
                return False
            sight_range = self.state["range"]
            food_seen_threshold = get_food_seen_threshold(self.state["range"])
            average_seen_density = self.exploration_path.calcule_average_seen_density([x,y], sight_range, self.cells_mapping)
            if average_seen_density >= food_seen_threshold:
                self.ignore_goal([x, y])
                return False
            

        return True

    def observed(self, obj_type):
        return any(obj_type == object_type and not self.is_ignored_goal(position)
                     for position, [object_type, timestamp] in self.observed_objects.items())
        
    def closest_object(self, obj_type):
        """Find the closest object based on the heuristic"""
        closest = None
        min_heuristic = None

        default_goal = Goal(
            goal_type=obj_type,
            max_time=None,
            visited_range=0,
            priority=1,
            position=None
        )

        for position in self.observed_objects.keys():
            print(position, self.is_ignored_goal(position), self.ignored_goals)
            if self.is_ignored_goal(position):
                print("IGNORED")
                continue
            
            default_goal.position = position
            heuristic = self.domain.heuristic(self.state, [default_goal]) # change this!
            
            if min_heuristic is None or heuristic < min_heuristic:
                min_heuristic = heuristic
                closest = position
        
        self.logger.debug(f"Closest {obj_type}: {closest}")
        self.current_goal = closest
        return list(closest)                    
        
    def update_cells_mapping(self, sight):
        for x_str, y_dict in sight.items():
            x = int(x_str)
            for y_str, obj_type in y_dict.items():
                y = int(y_str)
                seen, timestamp = self.cells_mapping[(x, y)]
                self.cells_mapping[(x, y)] = (seen + 1, time.time())
        
        self.expire_cells_mapping()
    
    def expire_cells_mapping(self):
        duration = get_duration_of_expire_cells(self.state["range"])

        for position, (seen, timestamp) in self.cells_mapping.copy().items():
            if timestamp is not None and time.time() - timestamp > duration:
                self.cells_mapping[position] = (0, None)

    def print_mapping(self, goals):
        self.logger.mapping("\033[2J") # clear the screen
        self.logger.mapping("\033[H") # move cursor to the top
        
        for y in range(self.domain.height):
            row = ""
            for x in range(self.domain.width):
                if self.is_ignored_goal((x,y)):
                    row += f"\033[1;35m{' I':2}\033[0m "
                elif [x, y] in goals:
                    if (x, y) in self.observed_objects:
                        row += f"\033[1;35m{' F' if self.observed_objects[(x, y)][0] == Tiles.FOOD else ' S':2}\033[0m "
                    else:
                        row += f"\033[1;35m\033[1m{goals.index([x, y]):2}\033[0m "
                elif (x, y) in self.exploration_path.exploration_path:
                    row += f"\033[1;38;2;255;255;0m{' E':2}\033[0m "
                elif [x, y] in self.state["body"]:
                    row += f"\033[1;38;2;0;0;0m{self.state['body'].index([x, y]):2}\033[0m "
                elif [x, y] in self.domain.internal_walls:
                    row += f"\033[1;34m{' W':2}\033[0m "
                else:   
                    if (x, y) in self.observed_objects:
                        row += f"\033[1;34m{' F' if self.observed_objects[(x, y)][0] == Tiles.FOOD else ' S':2}\033[0m "
                    else:
                        seen = self.cells_mapping[(x, y)][0]
                        if seen == 0:
                            r = 255
                            g = 255
                            b = 255
                        else:
                            normalized_seen = min(seen / (10*self.state["range"]), 1.0)
                            if normalized_seen <= 0.5:
                                r = int(255 * (normalized_seen * 2))
                                g = int(255 * (1 - normalized_seen * 2))
                                b = 0
                            elif normalized_seen <= 0.85:
                                r = 255
                                g = 0
                                b = int(255 * ((normalized_seen - 0.5) * 4))
                            else:
                                r = int(255 * (1 - (normalized_seen - 0.85) * 4))
                                g = 0
                                b = 255
                                
                        row += f"\033[38;2;{r};{g};{b}m{seen:2}\033[0m "
            self.logger.mapping(row)
        
