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
    
    def __init__(self, domain: SearchDomain, initial, goal):
        self.domain = domain
        self.initial = initial
        self.goals = goals
        self.ongoing_goals = goals.copy()
    
    def final_goal_test(self, state):
        return all(self.domain.satisfies(state, goal) for goal in self.goals)
    
    def goal_test(self, state):
        return self.domain.satisfies(state, self.ongoing_goals[0])