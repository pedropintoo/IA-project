import random

from src.goal import Goal
from consts import Tiles

DIRECTIONS = {
    'NORTH': [0, -1],
    'SOUTH': [0, 1],
    'WEST': [-1, 0],
    'EAST': [1, 0]
}

class OpponentMapping:
    def __init__(self, logger, width, height):
        self.logger = logger

        # Own Information
        self.own_body = []
        self.own_snake_length = 0
        self.own_traverse = False
        self.sight_state = [] # points [[int(x), int(y), value]] in the sight without the player's own snake
        self.previous_sight_state = []

        # Opponent Information
        self.opponent_direction = None
        self.opponent_head_position = None
        self.opponent_target_food = None
        self.opponent_traverse = True 

        # Previous and Future Opponent Information
        self.previous_head_position = None
        self.previous_opponent_body = []
        self.predicted_head_position = None
        self.predicted_failed = False

        # Number of times the agent survived to the simpleTrap
        self.simple_trap_survival = 0

        # Points to pass through to set a trap
        self.first_point = 0
        self.second_point = 0

        # Grid dimensions
        self.width = width
        self.height = height

    def update(self, state):
        # TODO: make a function to determine if the agent is the only one in the game
        if len(state['players']) == 1: 
            return      # THIS IS WRONG!!!!
        
        # Update the own information
        self.update_own_information(state)
        
        opponent_body = []
        targets_food = []
        self.process_sight_state(state['sight'], opponent_body, targets_food)

        # If the opponent is not visible, return
        if len(opponent_body) == 0:
            self.reset_opponent_state()
            return

        # Determine the opponent head position
        self.opponent_head_position = self.determine_current_head_position()
        self.previous_sight_state = self.sight_state

        # Evaluate the prediction made in the previous step
        self.update_prediction_status()
        
        # The opponent is visible. However, we are not sure about the position of the opponent head
        if not self.opponent_head_position:
            self.reset_opponent_prediction()
            self.logger.critical('NO OPPONENT HEAD POSITION')
            return 
        
        if len(targets_food) == 0:
            self.opponent_target_food = None
        
        else:
            # Find the closest food to the opponent head position considering self.own_traverse
            self.update_opponent_target_food(targets_food)
            # self.logger.critical(f'TARGET FOOD: {self.opponent_target_food}')
    
        # Predict the future position of the opponent's head
        self.opponent_direction = self.determine_opponent_direction(self.previous_head_position, self.opponent_head_position)
        self.predicted_head_position = self.determine_predicted_head_position(self.opponent_head_position, self.opponent_direction, self.opponent_target_food)
        
        self.previous_head_position = self.opponent_head_position
        # self.logger.info(f'Current head position assigned to previous_head_position: {self.previous_head_position}')
        self.opponent_head_position = self.predicted_head_position
        # self.logger.info(f'Next (predicted) head position: {self.predicted_head_position}')

    def reset_opponent_state(self):
        self.opponent_head_position = None
        self.opponent_direction = None
        self.opponent_target_food = None
        self.opponent_traverse = True
        self.previous_sight_state = self.sight_state

    def update_own_information(self, state):
        self.own_body = state['body']
        self.own_snake_length = len(self.own_body)
        self.own_traverse = state['traverse']

    def process_sight_state(self, sight, opponent_body, targets_food):
        self.sight_state = []

        for x, y_info in sight.items():
            x = int(x)
            for y, value in y_info.items():
                y = int(y)
                position = (x, y)
                if list(position) in self.own_body:
                    continue
                self.sight_state.append([x, y, value])

                if value == Tiles.SNAKE:
                    opponent_body.append(position)
                if value in [Tiles.FOOD, Tiles.SUPER]:
                    targets_food.append(position)
        
    
    def reset_opponent_prediction(self):
        self.opponent_head_position = None
        self.previous_head_position = None
        self.predicted_head_position = None
        self.predicted_failed = False

    def update_prediction_status(self):
        if self.predicted_head_position and self.opponent_head_position != self.predicted_head_position:
            self.predicted_failed = True

    def update_opponent_target_food(self, targets_food):
        closest_food = min(
            targets_food,
            key=lambda food: self.calculate_distance(self.opponent_head_position, food, self.opponent_traverse),
            default=None
        )
        self.opponent_target_food = closest_food

    def calculate_distance(self, position1, position2, traverse):
        dx_no_crossing_walls = abs(position1[0] - position2[0])
        dx = min(dx_no_crossing_walls, self.width - dx_no_crossing_walls) if traverse else dx_no_crossing_walls
        dy_no_crossing_walls = abs(position1[1] - position2[1])
        dy = min(dy_no_crossing_walls, self.height - dy_no_crossing_walls) if traverse else dy_no_crossing_walls
        return dx + dy

    def is_to_attack_opponent(self):
        # return self.opponent_head_position if it is not 0 
        # self.logger.critical(f'IS TO ATTACK OPPONENT?')
        if self.opponent_head_position and self.opponent_direction:
            return True
        else:
            # self.logger.critical('NO OPPONENT HEAD POSITION')
            return False
        
    def is_to_attack_food(self):
        # Check if the opponent is not moving towards the food 
        if not self.opponent_target_food:
            return False
        
        # If some of the points are not empty or do not have a food, do not attack unless the agent is in traverse mode and the point is a wall (STONE = 1)
        # Check self.sight_state to see if the points are empty
        self.first_point = self.opponent_target_food + DIRECTIONS["WEST"]
        self.second_point = self.opponent_target_food + DIRECTIONS["EAST"]
        
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
        return own_distance_to_food < opponent_distance_to_food
        
    def attack_opponent(self):
        # Predict the future position of the opponent in five steps from the current position if the opponent is moving straight using self.opponent_direction

        i = 0
        opponent_future_position = self.opponent_head_position
        while i < 5:
            opponent_future_position = self.go_direction(opponent_future_position, self.opponent_direction)
            i += 1                                        

        # self.logger.info(f"Opponent Direction: {self.opponent_direction} ; Opponent Head Position: {self.opponent_head_position}")
        # self.logger.info(f'Colliding with opponent in position : {opponent_future_position}')
        goal = Goal(goal_type='opponent', max_time=0.07, visited_range=0, priority=10, position=opponent_future_position, num_required_goals=1)
        return [goal]

    def attack_food(self):
        # This function returns the points that the agent must pass through to set a trap for the opponent.
        # If the agent survived three times to the simpleTrap we conclude that he has algorithms to deal with dead ends and we try to do a more advanced trap, advancedTrap.
        if self.simple_trap_survival < 3:
            # self.logger.critical('ATTACKING WITH SIMPLE TRAP')
            goals_positions = self.simpleTrap()
        else:
            # self.logger.critical('ATTACKING WITH ADVANCED TRAP')
            goals_positions = self.advancedTrap()

        goals = []
        i = len(goals_positions)
        for goal_position in goals_positions:
            goal = Goal(goal_type='trap', max_time=0, visited_range=0, priority=0, position=goal_position, num_required_goals=i)
            goals.append(goal)
            i -= 1
        
        return goals, self.opponent_target_food

    # Auxiliar functions
    def determine_current_head_position(self):     
        # Part of the snake that moves into previously unoccupied spaces (PASSAGE = 0).
        # Compare the self.sight_state with the previous_sight_state to determine the head position
        # If in the same position (x,y) the value is different than the previous value and is 4, then the head is in that position
        if len(self.previous_sight_state) == 0:
            # self.logger.info('we dont have previous sight state')
            return None

        for [x, y, value] in self.sight_state:
            for [x_previous, y_previous, value_previous] in self.previous_sight_state:
                if x == x_previous and y == y_previous:
                    if value == Tiles.SNAKE and value_previous != Tiles.SNAKE:
                        return [x, y]
    
        return None

    def determine_predicted_head_position(self, opponent_head_position, direction, target_food):
        # If no food is nearby, assume the opponent will move straight unless forced to turn.
        # self.logger.info(f'Opponent Direction: {direction}')
        
        # If we could not determine the direction of the opponent, we cannot predict the future position
        if not direction:
            return None
        
        # Assume the opponent will move straight for simplicity
        return self.go_direction(opponent_head_position, direction)

    def determine_opponent_direction(self, previous_head_position, current_head_position):
        # self.logger.info(f'Previous head position: {previous_head_position} ; Current head position: {current_head_position}')
        if not previous_head_position:
            return None
        if current_head_position[0] > previous_head_position[0]:
            return 'EAST'
        elif current_head_position[0] < previous_head_position[0]:
            return 'WEST'
        elif current_head_position[1] > previous_head_position[1]:
            return 'SOUTH'
        elif current_head_position[1] < previous_head_position[1]:
            return 'NORTH'

    def go_direction(self, position, direction):
        if DIRECTIONS.get(direction) is None:
            return None
        return [(position[0] + DIRECTIONS[direction][0]) % self.width, (position[1] + DIRECTIONS[direction][1]) % self.height]


    # # Traps
    # def simpleTrap(self):
    #     # Return the two points that the agent must pass through to set a trap 
    #     self.simple_trap_survival += 1
    #     return [self.first_point, self.second_point] 

    # def advancedTrap(self):
    #     # Return the three points that the agent must pass through to set a trap
    #     # Note: Now the points depend on the current length of our snake
    #     first_point = self.opponent_target_food + LEFT
        
    #     second_point_variation_in_x_coordinate = self.own_snake_length//3 # The variation depends on the length of our snake
    #     second_point = self.opponent_target_food + RIGHT + [second_point_variation_in_x_coordinate, 0]

    #     third_point_variation_in_x_coordinate = second_point_variation_in_x_coordinate//2 # TODO... add this in _consts.py
    #     third_point_variation_in_y_coordinate = second_point_variation_in_x_coordinate//3
    #     third_point = self.opponent_target_food + RIGHT + [third_point_variation_in_x_coordinate, third_point_variation_in_y_coordinate]
        
    #     return [first_point, second_point, third_point]
    

