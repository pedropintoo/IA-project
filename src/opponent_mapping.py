import random

from src.goal import Goal

UP = [0, -1]
DOWN = [0, 1]
LEFT = [-1, 0]
RIGHT = [1, 0]

class OpponentMapping:
    def __init__(self, logger, width, height):
        self.logger = logger

        # Own Information
        self.own_body = [] # e.g: [[15, 14], [14, 14], [13, 14]]
        self.our_snake_length = 0
        self.own_traverse = False
        self.sight_state = [] # points [[int(x), int(y), value]] in the sight without the player's own snake
        self.previous_sight_state = []

        # Opponent Information
        self.opponent_name = ''
        self.opponent_direction = 'up' # TODO...
        self.opponent_head_position = 0 # TODO...
        self.opponent_target_food = 0 # TODO...
        self.previous_opponent_body = [] # TODO...
        self.predicted_head_position = 0 # TODO...
        self.opponent_traverse = True 

        # Number of times the agent survived to the simpleTrap
        self.simple_trap_survival = 0

        # Points to pass through to set a trap
        self.first_point = 0
        self.second_point = 0

        # Grid dimensions
        self.width = width
        self.height = height

    def update(self, state):
        if len(state['players']) == 1:
            return
        
        self.opponent_name = state['players'][1]

        # Update the own information
        self.own_body = state['body']
        self.our_snake_length = len(self.own_body)
        self.own_traverse = state['traverse']

        our_sight_state = state['sight']
        
        # Check if the opponent or foods are visible
        opponent_body = []
        targets_food = []
        for x_coordinate in our_sight_state:
            set_y_coordinates = our_sight_state[x_coordinate]
            for y_coordinate in set_y_coordinates:
                if [int(x_coordinate), int(y_coordinate)] in self.own_body:
                    continue
                
                value = set_y_coordinates[y_coordinate]
                self.sight_state.append([int(x_coordinate), int(y_coordinate), value]) 
                if value == 4:
                    opponent_body.append([int(x_coordinate), int(y_coordinate)])
                if value == 2:
                    targets_food.append([int(x_coordinate), int(y_coordinate)])

        # If the opponent is not visible, return
        if len(opponent_body) == 0:
            self.logger.critical('OPPONENT NOT VISIBLE')
            self.opponent_head_position = 0
            self.previous_sight_state = self.sight_state
            return

        self.logger.info(f'OPPONENT BODY: {opponent_body}')
        self.logger.info('OPPONENT VISIBLE')

        # Update the opponent head position
        self.opponent_head_position = self.determinate_current_head_position()
        self.previous_sight_state = self.sight_state
        
        # Update the opponent mapping only if we are sure about the opponent head position
        if self.opponent_head_position == 0:
            return 
        
        if len(targets_food) == 0:
            self.logger.info('NO TARGETS FOOD')
            self.opponent_target_food = 0
            return
        
        # Update the target food position
        self.logger.info(f'TARGETS FOOD: {targets_food}')
        previous_distance = self.width + self.height

        # Find the closest food to the opponent head position considering self.own_traverse
        for food in targets_food:
            opponent_dx_no_crossing_walls = abs(food[0] - self.opponent_head_position[0])
            opponent_dx = min(opponent_dx_no_crossing_walls, self.width - opponent_dx_no_crossing_walls) if self.opponent_traverse else opponent_dx_no_crossing_walls
            opponent_dy_no_crossing_walls = abs(food[1] - self.opponent_head_position[1])
            opponent_dy = min(opponent_dy_no_crossing_walls, self.height - opponent_dy_no_crossing_walls) if self.opponent_traverse else opponent_dy_no_crossing_walls
            food_distance = opponent_dx + opponent_dy

            # food_distance = abs(food[0] - self.opponent_head_position[0]) + abs(food[1] - self.opponent_head_position[1])
            if food_distance < previous_distance:
                self.opponent_target_food = food
                previous_distance = food_distance

        self.logger.critical(f'TARGET FOOD: {self.opponent_target_food}')
    
        # Update the predicted head position
        self.predicted_head_position = self.determine_predicted_head_position(self.opponent_head_position, self.opponent_direction, self.opponent_target_food)

        # Update the opponent direction: can be inferred from the head position and the predicted head position
        if self.predicted_head_position[0] > self.opponent_head_position[0]:
            self.opponent_direction = 'right'
        elif self.predicted_head_position[0] < self.opponent_head_position[0]:
            self.opponent_direction = 'left'
        elif self.predicted_head_position[1] > self.opponent_head_position[1]:
            self.opponent_direction = 'down'
        elif self.predicted_head_position[1] < self.opponent_head_position[1]:
            self.opponent_direction = 'up'
        
        self.opponent_head_position = self.predicted_head_position

    def is_to_attack_opponent(self):
        # return self.opponent_head_position if it is not 0 
        self.logger.critical(f'IS TO ATTACK OPPONENT?')
        if self.opponent_head_position != 0:
            return True
        else:
            self.logger.critical('NO OPPONENT HEAD POSITION')
            return False
        
    def is_to_attack_food(self):
        # Check if the opponent is not moving towards the food 
        if self.opponent_target_food == 0:
            return False
        
        # If some of the points are not empty or do not have a food, do not attack unless the agent is in traverse mode and the point is a wall (STONE = 1)
        # Check self.sight_state to see if the points are empty
        self.first_point = self.opponent_target_food + LEFT
        self.second_point = self.opponent_target_food + RIGHT
        
        for [x, y, value] in self.sight_state:
            if [x, y] == self.first_point or [x, y] == self.second_point:
                if (value == 0 or value == 2) or (self.own_traverse and value == 1):    
                    continue
                else:
                    return False
        
        # Distance from the agent to the food
        own_head_position = self.own_body[-1]
        own_dx_no_crossing_walls = abs(own_head_position[0] - self.opponent_target_food[0])
        own_dx = min(own_dx_no_crossing_walls, self.width - own_dx_no_crossing_walls) if self.own_traverse else own_dx_no_crossing_walls

        own_dy_no_crossing_walls = abs(own_head_position[1] - self.opponent_target_food[1])
        own_dy = min(own_dy_no_crossing_walls, self.height - own_dy_no_crossing_walls) if self.own_traverse else own_dy_no_crossing_walls

        own_distance_to_food = own_dx + own_dy  

        # Distance from the opponent to the food
        opponent_dx_no_crossing_walls = abs(self.opponent_head_position[0] - self.opponent_target_food[0])
        opponent_dx = min(opponent_dx_no_crossing_walls, self.width - opponent_dx_no_crossing_walls) if self.opponent_traverse else opponent_dx_no_crossing_walls

        opponent_dy_no_crossing_walls = abs(self.opponent_head_position[1] - self.opponent_target_food[1])
        opponent_dy = min(opponent_dy_no_crossing_walls, self.height - opponent_dy_no_crossing_walls) if self.opponent_traverse else opponent_dy_no_crossing_walls
        
        opponent_distance_to_food = opponent_dx + opponent_dy

        # Check if the food is closer to the agent than to the opponent
        if own_distance_to_food < opponent_distance_to_food:
            return True
        else:
            return False
        
    def attack_opponent(self):
        goal = Goal(goal_type='opponent', max_time=0.07, visited_range=0, priority=10, position=self.opponent_head_position, num_required_goals=1)
        self.logger.critical(f'ATTACKING OPPONENT: {self.opponent_head_position}')
        return [goal]

    def attack_food(self):
        # This function returns the points that the agent must pass through to set a trap for the opponent.
        # If the agent survived three times to the simpleTrap we conclude that he has algorithms to deal with dead ends and we try to do a more advanced trap, advancedTrap.
        if self.simple_trap_survival < 3:
            self.logger.critical('ATTACKING WITH SIMPLE TRAP')
            goals_positions = self.simpleTrap()
        else:
            self.logger.critical('ATTACKING WITH ADVANCED TRAP')
            goals_positions = self.advancedTrap()

        goals = []
        i = len(goals_positions)
        for goal_position in goals_positions:
            goal = Goal(goal_type='trap', max_time=0, visited_range=0, priority=0, position=goal_position, num_required_goals=i)
            goals.append(goal)
            i -= 1
        
        return goals, self.opponent_target_food

    # Auxiliar functions
    def determinate_current_head_position(self):     
        # Part of the snake that moves into previously unoccupied spaces (PASSAGE = 0).
        # Compare the self.sight_state with the previous_sight_state to determine the head position
        # If in the same position (x,y) the value is different than the previous value and is 4, then the head is in that position

        for [x, y, value] in self.sight_state:
            for [x_previous, y_previous, value_previous] in self.previous_sight_state:
                if x == x_previous and y == y_previous:
                    if value == 4 and value_previous != 4:
                        self.logger.info(f'Head position: [{x}, {y}]')
                        return [x, y]
        return 0

    def determine_predicted_head_position(self, opponent_head_position, direction, target_food):
        # If no food is nearby, assume the opponent will move straight unless forced to turn.
        if self.opponent_target_food == 0:
            # will move straight
            if direction == 'up':
                return self.go_up(opponent_head_position)
            elif direction == 'down':
                return self.go_down(opponent_head_position)
            elif direction == 'left':
                return self.go_left(opponent_head_position)
            elif direction == 'right':
                return self.go_right(opponent_head_position)
        
        # If food is nearby, assume the opponent will move towards the food.
        else:
            if opponent_head_position[0] < target_food[0]:
                return self.go_right(opponent_head_position)
            elif opponent_head_position[0] > target_food[0]:
                return self.go_left(opponent_head_position)
            elif opponent_head_position[1] < target_food[1]:
                return self.go_down(opponent_head_position)
            elif opponent_head_position[1] > target_food[1]:
                return self.go_up(opponent_head_position)

    def go_up(self, position):
        return [position[0] + UP[0], position[1] + UP[1]]

    def go_down(self, position):
        return [position[0] + DOWN[0], position[1] + DOWN[1]]
    
    def go_left(self, position):
        return [position[0] + LEFT[0], position[1] + LEFT[1]]
    
    def go_right(self, position):
        return [position[0] + RIGHT[0], position[1] + RIGHT[1]]

    # Traps
    def simpleTrap(self):
        # Return the two points that the agent must pass through to set a trap 
        self.simple_trap_survival += 1
        return [self.first_point, self.second_point] 

    def advancedTrap(self):
        # Return the three points that the agent must pass through to set a trap
        # Note: Now the points depend on the current length of our snake
        first_point = self.opponent_target_food + LEFT
        
        second_point_variation_in_x_coordinate = self.our_snake_length//3 # The variation depends on the length of our snake
        second_point = self.opponent_target_food + RIGHT + [second_point_variation_in_x_coordinate, 0]

        third_point_variation_in_x_coordinate = second_point_variation_in_x_coordinate//2 # TODO... add this in _consts.py
        third_point_variation_in_y_coordinate = second_point_variation_in_x_coordinate//3
        third_point = self.opponent_target_food + RIGHT + [third_point_variation_in_x_coordinate, third_point_variation_in_y_coordinate]
        
        return [first_point, second_point, third_point]
    

