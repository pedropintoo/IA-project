

class OpponentMapping:
    def __init__(self, data):
        self.our_snake_length = 0

        # Opponent Information
        self.name = data['players'][1] if data['players'][0] == 'joao' else data['players'][0]
        
        self.direction = 'up' # TODO...
        self.head_position = (0, 0) # TODO...
        self.target_food = (0, 0) # TODO...
        
        self.predicted_direction = 'up' # TODO...
        self.predicted_head_position = (0, 0) # TODO...
        

    def update(self, data):
        # TODO... We can probably use the body() function in game.py to get our snake's body because this only gives the head and tail        
        own_body = data['body'] # e.g: [[15, 14], [14, 14]]

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
        self.head_position = opponent_body[-1]
        
        # Update the target food
        previous_distance = abs(targets_food[0][0] - self.head_position[0]) + abs(targets_food[0][1] - self.currenhead_positiont_position[1])
        for food in targets_food:
            food_distance = abs(food[0] - self.head_position[0]) + abs(food[1] - self.head_position[1])
            if food_distance < self.previous_distance:
                self.target_food = food
            previous_distance = food_distance
        
        # Update the predicted head position
        self.predicted_head_position = self.head_position + 1 # TODO... Implement the prediction algorithm

        # Update the predicted direction: can be inferred from the head position and the predicted head position
        if self.predicted_head_position[0] > self.head_position[0]:
            self.predicted_direction = 'right'
        elif self.predicted_head_position[0] < self.head_position[0]:
            self.predicted_direction = 'left'
        elif self.predicted_head_position[1] > self.head_position[1]:
            self.predicted_direction = 'down'
        elif self.predicted_head_position[1] < self.head_position[1]:
            self.predicted_direction = 'up'
        
        # Update the current direction
        self.direction = self.predicted_direction

        return
    
    def simpleTrap(self):
        # Return the two points that the agent must pass through to set a trap
        first_point = (self.target_food[0]-1, self.target_food[1])
        second_point = (self.target_food[0]+1, self.target_food[1])
        return [first_point, second_point] 

    def advancedTrap(self):
        # Return the three points that the agent must pass through to set a trap
        # Note: Now the points depend on the current length of our snake
        first_point = (self.target_food[0]-1, self.target_food[1])
        
        second_point_variation_in_x_coordinate = + self.our_snake_length//3
        second_point = ( self.target_food[0]+1 + second_point_variation_in_x_coordinate, self.target_food[1])

        third_point_variation_in_x_coordinate = second_point_variation_in_x_coordinate//2
        third_point_variation_in_y_coordinate = second_point_variation_in_x_coordinate//3
        third_point = (self.target_food[0]+1 + third_point_variation_in_x_coordinate, self.target_food[1] - third_point_variation_in_y_coordinate)
        
        return [first_point, second_point, third_point]
    
