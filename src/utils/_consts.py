from consts import Tiles
from functools import partial

def get_exploration_length_threshold(sight_range):
    """
    This is the threshold used to determine when to regenerate a new exploration path.
    If the exploration path is shorter than this threshold, the path will be regenerated.
    Goal: So the exploration path is never empty.
    """
    return 20 // sight_range

def get_last_exploration_distance_threshold(sign_range):
    """
    This is the threshold used to reset and regenerate the exploration path.
    If the last given point in the exploration path is further than this threshold, the path will be reset and regenerated.
    Goal: So the snake always goes to the closest point in the exploration path.
    """
    return sign_range * 3

def get_exploration_point_seen_threshold(sight_range):
    """
    This is the threshold used to determine if a point in the exploration path is valid.
    If the average seen density of the point is higher than this threshold, the point is not valid.
    Goal: So the snake doesn't go to points in previously seen areas.
    """
    if sight_range == 2:
        return 2
    elif sight_range == 3:
        return 4
    elif sight_range == 4:
        return 6
    elif sight_range == 5:
        return 9
    else:
        return 15

def get_duration_of_expire_cells(sight_range):
    """
    This is the duration of the cells in the exploration map.
    Goal: So the snake clears the exploration map of old cells so it has always some new cells to explore.
    """
    return 30 / sight_range




############################################################################################################
# 
# --  Agent
#
############################################################################################################

def is_snake_in_perfect_effects(state):
    """
    This function is used to determine if the snake should go for the super food.
    Goal: So the snake goes for the super food if it's required.
    """
    supers_required = 0 if not state["traverse"] else 2
    
    if state["step"] > 2900 or state["range"] < 3:
        return False
    
    if state["range"] == 3:
        supers_required = 8
        
    elif state["range"] == 4:
        supers_required = 6
        
    elif state["range"] == 5:
        supers_required = 4
        
    elif state["range"] == 6:
        supers_required = 3
        
    return not len([p for p in state.get("observed_objects", []) if state["observed_objects"][p][0] == Tiles.SUPER]) >= supers_required
    
def get_num_future_goals(goals, current_range):
    """
    This function is used to determine the number of future goals.
    Goal: So the snake goes for the future goals.
    """
    return len(goals) 
    
def get_future_goals_priority(goals):
    """
    This function is used to determine the priority of the future goals.
    Goal: So the snake goes for the future goals.
    """
    inicial_range = 1
    base_decrement = 0.2
    return [inicial_range - base_decrement * i for i in range(len(goals))]
    
def get_future_goals_range(goals, current_range):
    """
    This function is used to determine the range of the future goals.
    Goal: So the snake goes for the future goals.
    """
    inicial_range = 1
    base_increment = current_range - 1
    num_goals = len(goals)
    return [inicial_range + base_increment * i for i in range(num_goals)]
    