from consts import Tiles
from functools import partial

def get_exploration_length_threshold(sight_range):
    """
    This is the threshold used to determine when to regenerate a new exploration path.
    If the exploration path is shorter than this threshold, the path will be regenerated.
    Goal: So the exploration path is never empty.
    """
    return 25 // sight_range if sight_range < 5 else 25 // 4

def get_last_exploration_distance_threshold(sign_range, head, width):
    """
    This is the threshold used to reset and regenerate the exploration path.
    If the last given point in the exploration path is further than this threshold, the path will be reset and regenerated.
    Goal: So the snake always goes to the closest point in the exploration path.
    """
    if head[0] > width - sign_range * 10:
        return float("inf")
    return sign_range * 10

def get_exploration_point_seen_threshold(sight_range, traverse):
    """
    This is the threshold used to determine if a point in the exploration path is valid.
    If the average seen density of the point is higher than this threshold, the point is not valid.
    Goal: So the snake doesn't go to points in previously seen areas.
    """
    if sight_range == 2:
        return float("inf") if not traverse else 3
    elif sight_range == 3:
        return float("inf") if not traverse else 5
    elif sight_range == 4:
        return float("inf") if not traverse else 7
    elif sight_range == 5:
        return float("inf") if not traverse else 9
    else:
        return float("inf") if not traverse else 15

    # if traverse:
    #     return sight_range * 1.5
    # else:
    #     return sight_range * 2.5
    
def get_food_seen_threshold(sight_range):
    """
    This is the threshold used to determine if a food is valid.
    If the average seen density of the food is higher than this threshold, the food is not valid.
    Goal: So the snake doesn't go to points in previously seen areas.
    """
    if sight_range == 2:
        return 6
    elif sight_range == 3:
        return 12
    elif sight_range == 4:
        return 18
    elif sight_range == 5:
        return 27
    else:
        return 45
        
def get_duration_of_expire_cells(sight_range, fps, width, height):
    """
    This is the duration of the cells in the exploration map.
    Goal: So the snake clears the exploration map of old cells so it has always some new cells to explore.
    """
    # (48, 24)
    # return (30 / sight_range) * 10 / fps
    return ((30 / sight_range) * 10 / fps) * (width / 48) * (height / 24)


############################################################################################################
# 
# --  Agent
#
############################################################################################################

def is_snake_in_perfect_effects(state, max_steps):
    """
    This function is used to determine if the snake should go for the super food.
    Goal: So the snake goes for the super food if it's required.
    """
    traverse = state["traverse"]
    
    if state["step"] > (max_steps - 300):
        return False
    
    if state["range"] == 2:
        supers_required = 0
        
    elif state["range"] == 3:
        supers_required = 6 # TODO: or 8 
        
    elif state["range"] == 4:
        supers_required = 12 if traverse else 8
        
    elif state["range"] == 5:
        supers_required = 15 if traverse else 0
        
    elif state["range"] == 6:
        supers_required = 20 if traverse else 0
        
    return not len([p for p in state.get("observed_objects", []) if state["observed_objects"][p][0] == Tiles.SUPER]) >= supers_required
    
def get_num_future_goals(current_range):
    """
    This function is used to determine the number of future goals.
    Goal: So the snake goes for the future goals.
    """
    return 2

def get_num_max_present_goals():
    """
    This function is used to determine the maximum number of present goals.
    Goal: So the snake goes for the present goals.
    """
    # infinite -> the get_near_goal_range will determine the quantity of present goals
    return 5#3
    
def get_future_goals_priority(num_goals):
    """
    This function is used to determine the priority of the future goals.
    Goal: So the snake goes for the future goals.
    """
    inicial_range = 20
    base_decrement = 0.5
    return [inicial_range * base_decrement for i in range(num_goals)]
    
def get_future_goals_range(num_goals, current_range):
    """
    This function is used to determine the range of the future goals.
    Goal: So the snake goes for the future goals.
    """
    inicial_range = 3
    base_increment = current_range - 1 
    return [inicial_range + base_increment * i for i in range(num_goals)]
    
def get_near_goal_range(current_range, body_length, super_food=False):
    """
    This function is used to determine the range of the near goals.
    Goal: So the snake goes for the near goals.
    """
    if body_length <= 20:
        return 10
    elif body_length <= 40:
        return 3
    elif body_length <= 70:
        return 2
    else:
        return 1
