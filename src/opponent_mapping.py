import random

from goal import Goal


class OpponentMapping:
    def __init__(self, logger):
        self.logger = logger

        # Own Information
        self.own_body = [] # e.g: [[15, 14], [14, 14], [13, 14]]
        self.our_snake_length = 0
        self.own_traverse = False
        self.sight_data = [] # points [[int(x), int(y), value]] in the sight without the player's own snake
        self.previous_sight_data = []

        # Opponent Information
        self.opponent_name = ''
        self.opponent_direction = random.choice(['up', 'down', 'left', 'right']) # TODO...
        self.opponent_head_position = 0 # TODO...
        self.opponent_target_food = 0 # TODO...
        self.previous_opponent_body = [] # TODO...
        self.predicted_head_position = 0 # TODO...

        # Number of times the agent survived to the simpleTrap
        self.simple_trap_survival = 0

        # Points to pass through to set a trap
        self.first_point = 0
        self.second_point = 0

    def update(self, data):
        self.opponent_name = data['players'][1]
        
        # Update the own information
        self.own_body = data['body']
        self.our_snake_length = len(self.own_body)
        self.own_traverse = data['traverse']

        # Process the data to update the opponent mapping
        our_sight_data = data['sight']
        
        # Check if the opponent or foods are visible
        opponent_body = []
        targets_food = []
        for x_coordinate in our_sight_data:
            set_y_coordinates = our_sight_data[x_coordinate]
            for y_coordinate in set_y_coordinates:
                # Discard the player's own snake
                if [int(x_coordinate), int(y_coordinate)] not in self.own_body:
                    value = set_y_coordinates[y_coordinate]
                    self.sight_data.append([int(x_coordinate), int(y_coordinate), value]) 
                    if value == 4:
                        opponent_body.append([int(x_coordinate), int(y_coordinate)])
                    if value == 2:
                        targets_food.append([int(x_coordinate), int(y_coordinate)])

        # If the opponent is not visible, return
        if len(opponent_body) == 0:
            self.logger.critical('OPPONENT NOT VISIBLE')
            return

        self.logger.info(f'OPPONENT BODY: {opponent_body}')
        self.logger.info('OPPONENT VISIBLE')

        # Update the opponent head position
        self.opponent_head_position = self.determinate_current_head_position()
        self.previous_sight_data = self.sight_data
        
        # Update the opponent mapping only if we are sure about the opponent head position
        if self.opponent_head_position != 0: 
            # Update the target food position
            if len(targets_food) == 0:
                self.logger.info('NO TARGETS FOOD')
                self.opponent_target_food = 0
            else:
                self.logger.info(f'TARGETS FOOD: {targets_food}')
                first_food = targets_food[0]
                self.opponent_target_food = first_food
                previous_distance = abs(first_food[0] - self.opponent_head_position[0]) + abs(first_food[1] - self.opponent_head_position[1])

                # Find the closest food to the opponent head position
                for food in targets_food:
                    food_distance = abs(food[0] - self.opponent_head_position[0]) + abs(food[1] - self.opponent_head_position[1])
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

        return
    
    def is_to_attack(self):
        # Check if the opponent is not moving towards the food 
        if self.opponent_target_food == 0:
            return False
        
        # If some of the points are not empty or do not have a food, do not attack unless the agent is in traverse mode and the point is a wall (STONE = 1)
        # Check self.sight_data to see if the points are empty
        self.first_point = [self.opponent_target_food[0]-1, self.opponent_target_food[1]]
        self.second_point = [self.opponent_target_food[0]+1, self.opponent_target_food[1]]
        
        for [x, y, value] in self.sight_data:
            if [x, y] == self.first_point or [x, y] == self.second_point:
                if (value == 0 or value == 2) or (self.own_traverse and value == 1):    
                    continue
                else:
                    return False
        
    
        own_head_position = self.own_body[-1]
        # Check if the food is closer to the agent than to the opponent
        own_distance_to_food = abs(own_head_position[0] - self.opponent_target_food[0]) + abs(own_head_position[1] - self.opponent_target_food[1])
        opponent_distance_to_food = abs(self.opponent_head_position[0] - self.opponent_target_food[0]) + abs(self.opponent_head_position[1] - self.opponent_target_food[1])

        # TODO ..
        # dx_no_crossing_walls = abs(head[0] - goal_position[0])
        # dx = min(dx_no_crossing_walls, self.width - dx_no_crossing_walls) if traverse else dx_no_crossing_walls

        # dy_no_crossing_walls = abs(head[1] - goal_position[1])
        # dy = min(dy_no_crossing_walls, self.height - dy_no_crossing_walls) if traverse else dy_no_crossing_walls

        if own_distance_to_food < opponent_distance_to_food:
            return True
        else:
            return False
        
    def attack(self):
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
        # Compare the self.sigth_data with the previous_sight_data to determine the head position
        # If in the same position (x,y) the value is different than the previous value and is 4, then the head is in that position

        for [x, y, value] in self.sight_data:
            for [x_previous, y_previous, value_previous] in self.previous_sight_data:
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
                return [opponent_head_position[0], opponent_head_position[1] + 1]
            elif direction == 'down':
                return [opponent_head_position[0], opponent_head_position[1] - 1]
            elif direction == 'left':
                return [opponent_head_position[0] - 1, opponent_head_position[1]]
            elif direction == 'right':
                return [opponent_head_position[0] + 1, opponent_head_position[1]]
        
        # If food is nearby, assume the opponent will move towards the food.
        else:
            if opponent_head_position[0] < target_food[0]:
                return [opponent_head_position[0] + 1, opponent_head_position[1]]
            elif opponent_head_position[0] > target_food[0]:
                return [opponent_head_position[0] - 1, opponent_head_position[1]]
            elif opponent_head_position[1] < target_food[1]:
                return [opponent_head_position[0], opponent_head_position[1] + 1]
            elif opponent_head_position[1] > target_food[1]:
                return [opponent_head_position[0], opponent_head_position[1] - 1]

    # Traps
    def simpleTrap(self):
        # Return the two points that the agent must pass through to set a trap 
        self.simple_trap_survival += 1
        return [self.first_point, self.second_point] # TODO... delete the last point 

    def advancedTrap(self):
        # Return the three points that the agent must pass through to set a trap
        # Note: Now the points depend on the current length of our snake
        first_point = [self.opponent_target_food[0]-1, self.opponent_target_food[1]]
        
        second_point_variation_in_x_coordinate = self.our_snake_length//3 # The variation depends on the length of our snake
        second_point =  [self.opponent_target_food[0]+1 + second_point_variation_in_x_coordinate, self.opponent_target_food[1]]

        third_point_variation_in_x_coordinate = second_point_variation_in_x_coordinate//2 # TODO... add this in _consts.py
        third_point_variation_in_y_coordinate = second_point_variation_in_x_coordinate//3
        third_point = [ self.opponent_target_food[0]+1 + third_point_variation_in_x_coordinate, self.opponent_target_food[1] - third_point_variation_in_y_coordinate ]
        
        return [first_point, second_point, third_point]
    

