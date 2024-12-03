class Goal:
    
    def __init__(self, goal_type=None, max_time=None, visited_range=None, priority=None, position=None, num_required_goals=1):
        self.goal_type = goal_type
        self.max_time = max_time
        self.visited_range = visited_range
        self.priority = priority
        self.position = position
        self.num_required_goals = num_required_goals

    def __str__(self):
        return f"Goal({self.goal_type}, {self.position}, {self.visited_range} {self.priority})"