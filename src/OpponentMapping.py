

import random


class OpponentMapping:
    def __init__(self, data):

        # Own Information
        self.our_snake_length = 0

        # Opponent Information
        self.opponent_name = data['players'][1] if data['players'][0] == 'joao' else data['players'][0]
        
        self.opponent_direction = random.choice(['up', 'down', 'left', 'right']) # TODO...
        self.opponent_head_position = (0, 0) # TODO...
        self.opponent_target_food = (0, 0) # TODO...
        
        # Previous Opponent Information
        self.previous_opponent_body = [] # TODO...

        # Predicted Opponent Information
        self.predicted_head_position = (0, 0) # TODO...

        # Number of times the agent survived to the simpleTrap
        self.simple_trap_survival = 0

    def determinate_current_head_position(self, opponent_body):     
        # Part of the snake that moves into previously unoccupied spaces (PASSAGE = 0).
        for [x, y] in opponent_body:
            if [x,y] not in self.previous_opponent_body:
                # Update the previous opponent body
                self.previous_opponent_body = opponent_body
                return [x, y]

    def determine_predicted_head_position(self, opponent_head_position, direction, target_food):
        # If no food is nearby, assume the opponent will move straight unless forced to turn.
        
        if self.opponent_target_food == (0, 0):
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

    def update(self, data):
        
        # Update the own information
        own_body = data['body'] # e.g: [[15, 14], [14, 14], [13, 14]]
        self.our_snake_length = len(own_body)

        # Process the data to update the opponent mapping
        our_sight_data = data['sight']
        
        # Check if the opponent or foods are visible
        opponent_body = []
        targets_food = []
        for x_coordinate in our_sight_data:
            set_y_coordinates = our_sight_data[x_coordinate]
            for y_coordinate in set_y_coordinates:
                # Discard the player's own snake
                if [x_coordinate, y_coordinate] not in own_body:
                    value = set_y_coordinates[y_coordinate]
                    if value == 4:
                        opponent_body.append([x_coordinate, y_coordinate])
                    if value == 2:
                        targets_food.append([x_coordinate, y_coordinate])
        
        # Update the opponent head position
        self.opponent_head_position = self.determinate_current_head_position(opponent_body)
        
        # Update the target food position
        if len(targets_food) == 0:
            self.opponent_target_food = (0, 0)
        else:    
            first_food = targets_food[0]
            previous_distance = abs(first_food[0] - self.opponent_head_position[0]) + abs(first_food[1] - self.currenhead_positiont_position[1])
            for food in targets_food:
                food_distance = abs(food[0] - self.opponent_head_position[0]) + abs(food[1] - self.opponent_head_position[1])
                if food_distance < previous_distance:
                    self.opponent_target_food = food
                    previous_distance = food_distance
        
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
    
    def isToAttack(self, own_head_position):
        # Check if the opponent is in a position to be attacked.
        # The opponent can be attacked if it is moving towards the food and the food is closer to the agent than to the opponent.

        # Check if the opponent is moving towards the food
        if self.opponent_target_food == (0, 0):
            return False
        
        # Check if the food is closer to the agent than to the opponent
        own_distance_to_food = abs(own_head_position[0] - self.opponent_target_food[0]) + abs(own_head_position[1] - self.opponent_target_food[1])
        opponent_distance_to_food = abs(self.opponent_head_position[0] - self.opponent_target_food[0]) + abs(self.opponent_head_position[1] - self.opponent_target_food[1])

        if own_distance_to_food < opponent_distance_to_food:
            return True
        else:
            return False
        
    def attack(self):
        # This function returns the points that the agent must pass through to set a trap for the opponent.
        # If the agent survived three times to the simpleTrap we conclude that he has algorithms to deal with dead ends and we try to do a more advanced trap, advancedTrap.
        if self.simple_trap_survival < 3:
            return self.simpleTrap()
        
        return self.advancedTrap()
        
    def simpleTrap(self):
        # Return the two points that the agent must pass through to set a trap
        first_point = [self.opponent_target_food[0]-1, self.opponent_target_food[1]]
        second_point = [self.opponent_target_food[0]+1, self.opponent_target_food[1]]
        return [first_point, second_point] 

    def advancedTrap(self):
        # Return the three points that the agent must pass through to set a trap
        # Note: Now the points depend on the current length of our snake
        first_point = [self.opponent_target_food[0]-1, self.opponent_target_food[1]]
        
        second_point_variation_in_x_coordinate = self.our_snake_length//3 # The variation depends on the length of our snake
        second_point =  [self.opponent_target_food[0]+1 + second_point_variation_in_x_coordinate, self.opponent_target_food[1]]

        third_point_variation_in_x_coordinate = second_point_variation_in_x_coordinate//2
        third_point_variation_in_y_coordinate = second_point_variation_in_x_coordinate//3
        third_point = [ self.opponent_target_food[0]+1 + third_point_variation_in_x_coordinate, self.opponent_target_food[1] - third_point_variation_in_y_coordinate ]
        
        return [first_point, second_point, third_point]
    

