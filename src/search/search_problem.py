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
    
    def __init__(self, domain: SearchDomain, initial, goals):
        self.domain = domain
        self.initial = initial
        self.goals = goals
    
    def goal_test(self, state):
        return all(self.domain.satisfies(state, goal) for goal in self.goals)
    
    def satisfies_first_goal(self, state):
        return self.domain.is_goal_visited(head=state["body"][0], goal=self.goals[0], traverse=state["traverse"])