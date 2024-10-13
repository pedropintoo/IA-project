'''
 # @ Authors: 
 #  - Pedro Pinto (pmap@ua.pt)
 #  - Joao Pinto (jpapinto@ua.pt)
 #  - Guilherme Santos (gui.santos91@ua.pt)
 # @ Create Time: 2024-10-13
 '''
from search_domain import SearchDomain

class SearchProblem:
    """Search Problem"""
    
    def __init__(self, domain: SearchDomain, initial, goal):
        self.domain = domain
        self.initial = initial
        self.goal = goal
    
    def goal_test(self, state):
        return self.domain.satisfies(state,self.goal)
