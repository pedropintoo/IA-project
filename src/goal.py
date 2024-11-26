class Goal:
    
    def __init__(self, goal_type, max_time, visited_range, priority, position):
        self.goal_type = goal_type
        self.max_time = max_time
        self.visited_range = visited_range
        self.priority = priority
        self.position = position
