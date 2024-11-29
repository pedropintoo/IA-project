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
    return sight_range

def get_duration_of_expire_cells(sight_range):
    """
    This is the duration of the cells in the exploration map.
    Goal: So the snake clears the exploration map of old cells so it has always some new cells to explore.
    """
    return 30 / sight_range

