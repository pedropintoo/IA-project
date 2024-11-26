'''
 # @ Authors: 
 #  - Pedro Pinto (pmap@ua.pt)
 #  - Joao Pinto (jpapinto@ua.pt)
 #  - Guilherme Santos (gui.santos91@ua.pt)
 # @ Create Time: 2024-10-13
 '''
from abc import ABC, abstractmethod

class SearchDomain(ABC):
    """Search Domain"""
    
    # construtor
    @abstractmethod
    def __init__(self):
        pass

    # List of possible actions in a state
    @abstractmethod
    def actions(self, state):
        pass

    # Result of an action in a state: next state. (since we are using multiple goals, we need to change state depending on progress)
    @abstractmethod
    def result(self, state, action, goals):
        pass

    # Cost of an action in a state
    @abstractmethod
    def cost(self, state, action):
        pass

    # Estimated cost: one state to another
    @abstractmethod
    def heuristic(self, state, goals):
        pass

    # Test if the given "goal" is satisfied in "state"
    @abstractmethod
    def satisfies(self, state, goal):
        pass
