import heapq
import random
import time
from datetime import datetime
from collections import defaultdict
from src.opponent_mapping import OpponentMapping
from src.exploration_path import ExplorationPath
from src.matrix_operations import MatrixOperations
from src.goal import Goal
from consts import Tiles
from src.utils._consts import get_exploration_point_seen_threshold, get_duration_of_expire_cells, get_food_seen_threshold, get_near_goal_range

class Mapping:
    def __init__(self, logger, domain, fps):
        self.state = None
        
        self.logger = logger
        self.domain = domain
        self.fps = fps
        self.DEFAULT_IGNORED_GOAL_DURATION = (1 / self.fps)

        self.objects_updated = False
        self.observed_objects = None
        self.observation_duration = 90
        self.opponent_duration = 5

        self.super_foods = []
        
        self.exploration_path = ExplorationPath(
            internal_walls=domain.internal_walls, 
            height=domain.height,
            width=domain.width
        )
        
        self.ignored_objects = {Tiles.PASSAGE, Tiles.STONE}

        # Cells mapping: 0 - unseen, 1 - seen
        self.cells_mapping = {
            (x, y): (0, None)
            for x in range(self.domain.width)
            for y in range(self.domain.height)
        }   
         
        self.ignored_duration = 5
        self.temp_ignored_goals = set() # ((x, y), observed_timestamp) 
        self.cumulated_ignored_goals = {(x, y): self.DEFAULT_IGNORED_GOAL_DURATION for x in range(self.domain.width) for y in range(self.domain.height)}
        
        self.last_step = 0

        self.opponent = OpponentMapping(logger, domain.width, domain.height)

        self.current_goal = None
        self.previous_ignored_keys = None

    @property
    def ignored_goals(self):
        for goal, timestamp in self.temp_ignored_goals.copy():
            if time.time() - timestamp > self.cumulated_ignored_goals[goal]:
                self.temp_ignored_goals.remove((goal, timestamp))
        return self.temp_ignored_goals

    def ignore_goal(self, obj_pos):
        self.temp_ignored_goals.add((tuple(obj_pos), time.time()))
        self.cumulated_ignored_goals[tuple(obj_pos)] *= 2 # double the time to ignore the goal
    
    def is_ignored_goal(self, obj_pos, debug=False):
        return any(obj_pos[0] == x and obj_pos[1] == y for ((x, y), ts) in self.ignored_goals)
     
    def next_exploration(self, force_traverse_disabled=False) -> tuple:
        return self.exploration_path.next_exploration_point(
            self.state["body"], 
            self.state["range"],
            self.state["traverse"] and not force_traverse_disabled, 
            self.cells_mapping,
            self.is_ignored_goal
        )
    
    def peek_next_exploration(self, n_points=1, force_traverse_disabled=False) -> list:
        return self.exploration_path.peek_exploration_point(
            self.state["body"], 
            self.state["traverse"] and not force_traverse_disabled, 
            self.cells_mapping,
            n_points,
            self.is_ignored_goal,
            self.current_goal
        )

    def update(self, state, perfect_state, goals, actions_plan):
        
        self.objects_updated = False
                
        if self.last_step + 1 < state["step"]:
            # self.logger.critical(f"Unsynced steps: {state['step']} {self.last_step + 1}")
            self.objects_updated = True
            self.last_step = state["step"]
        else:
            self.last_step += 1
        
        start_t = datetime.now()
        self.opponent.update(state)
        # self.logger.mapping(f"Opponent update time: {(datetime.now() - start_t).total_seconds()}s")
        
        ## In case, opponent observed
        if self.opponent.opponent_head_position:
            self.domain.opponent_head = tuple(self.opponent.previous_head_position)
            self.domain.opponent_direction = self.opponent.opponent_direction
            # self.logger.mapping(f"[NEW] Opponent head: {self.domain.opponent_head} {self.domain.opponent_direction}")
        else:
            self.domain.opponent_head = None
            self.domain.opponent_direction = None
            
        ## Check if opponent change predicted direction
        if self.opponent.predicted_failed:
            self.objects_updated = True
            # self.logger.mapping("Opponent prediction failed")

        head = tuple(state["body"][0])
        self.cumulated_ignored_goals[head] = self.DEFAULT_IGNORED_GOAL_DURATION    

        # self.logger.debug(f"Old: {self.observed_objects}")
        
        current_range_val = state["range"]
        current_traverse_val = state["traverse"]
        
        ## Update the state
        if self.state and self.state["range"] != current_range_val:
            # Reset the exploration path if the range is changed
            self.exploration_path.exploration_path = []
            
            if current_range_val > self.state["range"]:
                self.objects_updated = True # Stop eating super foods!
        
        if self.state and self.state["traverse"] != current_traverse_val:
            # Reset the exploration path if the traverse is changed
            self.exploration_path.exploration_path = []
            if current_traverse_val:
                # Reset the ignored goals if the traverse is enabled
                self.cumulated_ignored_goals = {(x, y): self.DEFAULT_IGNORED_GOAL_DURATION for x in range(self.domain.width) for y in range(self.domain.height)}
        
        
        
        current_ignored_goals = set([goal for goal, timestamp in self.ignored_goals])
        if self.previous_ignored_keys:
            if not self.a_in_b_objects(a=self.previous_ignored_keys, b=current_ignored_goals):
                self.objects_updated = True
                # self.logger.mapping("Ignored goals changed")
        self.previous_ignored_keys = current_ignored_goals       
        
        self.state = {
            "body": state["body"] + [state["body"][-1]], # add the tail
            "range": state["range"],
            "traverse": state["traverse"],
            "observed_objects": self.state["observed_objects"] if self.state else dict(),
            "step": state["step"],
            "visited_goals": set(),
            "opponent_head": self.domain.opponent_head
        }
        
        
        currently_observed = defaultdict(list)
        for x_str, y_dict in state["sight"].items():
            x = int(x_str)
            for y_str, obj_type in y_dict.items():
                y = int(y_str)
                seen, _ = self.cells_mapping[(x, y)]
                timestamp = time.time()
                self.cells_mapping[(x, y)] = (seen + 1, timestamp)
                currently_observed[(x, y)] = [obj_type, timestamp]  
        
        self.expire_cells_mapping()        

        ## Copy for better readability
        self.observed_objects = self.state["observed_objects"] # as a reference

        ## Clear the expired observed objects
        del_positions = []
        for position, [obj_type, timestamp] in self.observed_objects.items():
            max_duration = self.observation_duration if obj_type != Tiles.SNAKE else self.opponent_duration                
            if time.time() - timestamp > max_duration:
                del_positions.append(position)
        
        for position in del_positions:
            del self.observed_objects[position]
               

        ## Update the observed objects
        for position, [obj_type, timestamp] in currently_observed.items():            
            # This position has a object
            if position in self.observed_objects:
                
                # In case, the object is the same
                if self.is_the_same_object(obj_type, position):
                    self.observed_objects[position][1] = timestamp # update the timestamp
                    
                else:
                    # In case, the object is to ignore
                    if obj_type in self.ignored_objects:
                        del self.observed_objects[position] # ignore the empty space
                        continue
                    
                    # In case, the object is now my body
                    if obj_type == Tiles.SNAKE and list(position) in self.state["body"]:
                        del self.observed_objects[position]
                        continue
                    
                    # Update the object type (and current ts)
                    self.observed_objects[position] = [obj_type, timestamp]
                    
                    # Update a flag
                    if not (obj_type == Tiles.SUPER and perfect_state):
                        
                        # In case, it's the opponent body and the prediction is correct
                        if obj_type == Tiles.SNAKE and not self.opponent.predicted_failed:
                            continue # not update the flag
                            
                        self.objects_updated = True
                        
            else:
                # This position is new
                if obj_type not in self.ignored_objects:
                    
                    # In case, the object is now my body
                    if obj_type == Tiles.SNAKE and list(position) in self.state["body"]:
                        continue
                    
                    # Create the entry
                    self.observed_objects[position] = [obj_type, timestamp]
                    
                    # Update a flag
                    if not (obj_type == Tiles.SUPER and perfect_state):
                        self.objects_updated = True

        # if self.logger.mapping_active:
        #     self.print_mapping([goal.position for goal in goals], actions_plan)
        # self.logger.debug(f"New: {self.observed_objects}")
        

    def a_in_b_objects(self, a, b):
        return all(a_i in b for a_i in a if a_i in self.observed_objects and not (self.observed_objects[a_i][0] == Tiles.SUPER and self.domain.is_perfect_effects(self.state)))

    def is_the_same_object(self, obj_type, position):
        
        if obj_type == self.observed_objects[position][0]:
            if obj_type != Tiles.SNAKE:
                return True # the same object, but not a snake

            # compare two snake objects
            if list(position) not in self.state["body"]:
                return True
        
        return False

    def nothing_new_observed(self, goals):
        if self.objects_updated:
            return False
      
        # TODO: For multiplayer: check if the goal has disappeared
        
        ## Check if the exploration has already been seen, with a good density
        first_goal = goals[0]
        if first_goal.goal_type == "exploration":
            x, y = first_goal.position
            sight_range = self.state["range"]
            exploration_point_seen_threshold = get_exploration_point_seen_threshold(sight_range, self.state["traverse"])
            average_seen_density = self.exploration_path.calcule_average_seen_density([x,y], sight_range, self.cells_mapping)
            if average_seen_density >= exploration_point_seen_threshold and not y == 0:
                self.cumulated_ignored_goals[(x, y)] = self.DEFAULT_IGNORED_GOAL_DURATION
                return False

        return True

    def observed(self, obj_type):
        return any(obj_type == object_type and not self.is_ignored_goal(position)
                     for position, [object_type, timestamp] in self.observed_objects.items())
        
    def closest_objects(self, obj_type):
        """Find the closest object based on the heuristic"""
        is_super_food_type = obj_type == Tiles.SUPER
        points = []         
        min_heuristic = None
        closest = None
        traverse = self.state["traverse"]
        ## Get the closest food
        for position in self.observed_objects.keys():
            if self.is_ignored_goal(position) or self.observed_objects[position][0] != obj_type or list(position) in self.state["body"]:
                continue  # ignore the ignored goals, and the other objects
            
            points.append(position)
            
            heuristic = self.domain.heuristic(self.state, [Goal(goal_type=obj_type, position=position, visited_range=0)]) # change this!
            if not min_heuristic or heuristic < min_heuristic:
                min_heuristic = heuristic
                closest = position

        if not closest:
            return []

        ## Get near goals
        near_objects = [closest]
        near_goal_range = get_near_goal_range(self.state["range"], len(self.state["body"]), is_super_food_type)
        for x in range(-near_goal_range, near_goal_range + 1):
            for y in range(-near_goal_range, near_goal_range + 1):
                if (x == 0 and y == 0):
                    continue
                position = [closest[0] + x, closest[1] + y]
                
                if tuple(position) not in points:
                    continue # not of this type
                
                if not traverse:
                    if self._outside_of_domain(position) or position in self.domain.internal_walls:
                        continue
                    near_objects.append(position)
                    
                else:
                    if is_super_food_type and self._outside_of_domain(position):
                        continue
                        
                    else:
                        position = [position[0] % self.domain.width, position[1] % self.domain.height]
                        near_objects.append(position)
        
        return near_objects
    
    def _outside_of_domain(self, position):
        x, y = position
        return x < 0 or x >= self.domain.width or y < 0 or y >= self.domain.height
    
    def manhattan_distance(self, head, goal_position, traverse):
        dx_no_crossing_walls = abs(head[0] - goal_position[0])
        dx = min(dx_no_crossing_walls, self.exploration_path.width - dx_no_crossing_walls) if traverse else dx_no_crossing_walls

        dy_no_crossing_walls = abs(head[1] - goal_position[1])
        dy = min(dy_no_crossing_walls, self.exploration_path.height - dy_no_crossing_walls) if traverse else dy_no_crossing_walls

        return dx + dy                  
    
    def expire_cells_mapping(self):
        duration = get_duration_of_expire_cells(self.state["range"], self.fps, self.domain.width, self.domain.height)

        for position, (seen, timestamp) in self.cells_mapping.items():
            if timestamp is not None and time.time() - timestamp > duration:
                self.cells_mapping[position] = (0, None)

    # def print_mapping(self, goals, actions_plan):
    #     self.logger.mapping("\033[2J") # clear the screen
    #     self.logger.mapping("\033[H") # move cursor to the top
        
    #     for y in range(self.domain.height):
    #         row = ""
    #         for x in range(self.domain.width):
    #             if self.is_ignored_goal((x,y)):
    #                 row += f"\033[1;35m{' I':2}\033[0m "
    #             elif [x, y] in goals:
    #                 if (x, y) in self.observed_objects:
    #                     if self.observed_objects[(x, y)][0] == Tiles.SUPER:
    #                         row += f"\033[1;35m{' S':2}\033[0m "
    #                     elif self.observed_objects[(x, y)][0] == Tiles.FOOD:
    #                         row += f"\033[1;35m{' F':2}\033[0m "
    #                     elif self.observed_objects[(x, y)][0] == Tiles.SNAKE:
    #                         row += f"\033[1;31m{' E':2}\033[0m "
    #                 else:
    #                     row += f"\033[1;35m\033[1m{goals.index([x, y]):2}\033[0m "
    #             elif (x, y) in self.exploration_path.exploration_path:
    #                 row += f"\033[1;38;2;255;255;0m{' E':2}\033[0m "
    #             elif [x, y] in self.state["body"]:
    #                 row += f"\033[1;38;2;0;0;0m{self.state['body'].index([x, y]):2}\033[0m "
    #             elif [x, y] in self.domain.internal_walls:
    #                 row += f"\033[1;34m{' W':2}\033[0m "
    #             else:   
    #                 if (x, y) in self.observed_objects:
    #                     if self.observed_objects[(x, y)][0] == Tiles.SUPER:
    #                         row += f"\033[1;35m{' S':2}\033[0m "
    #                     elif self.observed_objects[(x, y)][0] == Tiles.FOOD:
    #                         row += f"\033[1;35m{' F':2}\033[0m "
    #                     elif self.observed_objects[(x, y)][0] == Tiles.SNAKE:
    #                         row += f"\033[1;31m{' E':2}\033[0m "
    #                 else:
    #                     seen = self.cells_mapping[(x, y)][0]
    #                     if seen == 0:
    #                         r = 255
    #                         g = 255
    #                         b = 255
    #                     else:
    #                         normalized_seen = min(seen / (10*self.state["range"]), 1.0)
    #                         if normalized_seen <= 0.5:
    #                             r = int(255 * (normalized_seen * 2))
    #                             g = int(255 * (1 - normalized_seen * 2))
    #                             b = 0
    #                         elif normalized_seen <= 0.85:
    #                             r = 255
    #                             g = 0
    #                             b = int(255 * ((normalized_seen - 0.5) * 4))
    #                         else:
    #                             r = int(255 * (1 - (normalized_seen - 0.85) * 4))
    #                             g = 0
    #                             b = 255
                                
    #                     row += f"\033[38;2;{r};{g};{b}m{seen:2}\033[0m "
    #         self.logger.mapping(row)
    #     self.logger.mapping("Goals: " + str([g for g in goals]))
    #     self.logger.mapping("Body: " + str(self.state["body"]))
    #     self.logger.mapping("Action plan: " + str(actions_plan))
    #     self.logger.mapping("Observed: " + str([p for p in self.observed_objects.keys()]))
    #     self.logger.mapping("Traversal: " + str(self.state["traverse"]))
    #     self.logger.mapping("Range: " + str(self.state["range"]))
    #     self.logger.mapping("Step: " + str(self.state["step"]))
        
