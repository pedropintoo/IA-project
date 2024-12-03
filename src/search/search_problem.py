'''
 # @ Authors: 
 #  - Pedro Pinto (pmap@ua.pt)
 #  - Joao Pinto (jpapinto@ua.pt)
 #  - Guilherme Santos (gui.santos91@ua.pt)
 # @ Create Time: 2024-10-13
 '''
from src.search.search_domain import SearchDomain

class SearchProblem:
    """Search Problem"""
    
    def __init__(self, domain: SearchDomain, initial, goals, num_present_goals=1):
        self.domain = domain
        self.initial = initial
        self.goals = goals
        self.num_present_goals = num_present_goals
    
    def goal_test(self, state):
        return all(self.domain.satisfies(state, goal) for goal in self.goals)
    
    def satisfies_present_goals(self, state):
        goal_idx = self.num_present_goals - 1
        return self.domain.is_goal_visited(head=state["body"][0], goal=self.goals[goal_idx], traverse=state["traverse"])