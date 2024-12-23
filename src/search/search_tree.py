'''
 # @ Authors: 
 #  - Pedro Pinto (pmap@ua.pt)
 #  - Joao Pinto (jpapinto@ua.pt)
 #  - Guilherme Santos (gui.santos91@ua.pt)
 # @ Create Time: 2024-10-13
 '''
import datetime
import sys
from operator import attrgetter

from src.search.search_node import SearchNode
from src.search.search_problem import SearchProblem
from src.utils.exceptions import TimeLimitExceeded

class SearchTree:
    """Search Tree"""
    
    def __init__(self, problem: SearchProblem, strategy="A*"):
        self.problem = problem
        root = SearchNode(problem.initial, None, heuristic=problem.domain.heuristic(problem.initial, problem.goals))
        self.open_nodes = [root]
        self.best_solution = None
        self.non_terminals = 0
        self.strategy = strategy

    # Get the root two actions to a given node
    def first_two_actions_to(self, node):
        n = node
        previous = n.parent
        while previous is not None and previous.parent is not None:
            if previous.parent.parent is None:
                return [n.action, n.parent.action]
            n = previous
            previous = n.parent
        return None
        

    # Path from root to node
    def inverse_plan(self, node):
        n = node
        _plan = []
        while n is not None:
            if n.action:
                _plan.append(n.action)
            n = n.parent
        return _plan
    
    # Path from root to solution on a given condition (first node **in the tree** to satisfy the condition)
    def inverse_plan_to_solution(self, node):
        solution = None
        n = node
        while n is not None:
            if self.problem.satisfies_present_goals(n.state):
                solution = n
            else:
                if solution:
                    break # condition is no longer satisfied
            n = n.parent         
        return self.inverse_plan(solution)

    # Search solution
    def search(self, time_limit=None, first_two_actions=False):
        while self.open_nodes is not None and len(self.open_nodes) > 0:          
            node = self.open_nodes.pop(0)

            if time_limit is not None and datetime.datetime.now() >= time_limit: 
                ## Time limit exceeded
                #print("time limit exceeded")
                return -1

            ## Goals test: all goals are satisfied
            if self.problem.goal_test(node.state):
                # print("__________________")
                ## In case only the first two directions are needed
                if first_two_actions:
                    return self.first_two_actions_to(node)
                
                return self.inverse_plan_to_solution(node)

            self.non_terminals += 1
            new_lower_nodes = []
            visited_goal = None
            ## Iterate over possible actions to generate new nodes
            for act in self.problem.domain.actions(node.state):
                
                if time_limit is not None and datetime.datetime.now() >= time_limit: 
                    ## Time limit exceeded
                    return -1

                new_state = self.problem.domain.result(node.state, act, self.problem.goals)

                if node.in_parent(new_state):
                    continue

                cost = node.cost + self.problem.domain.cost(node.state, act)
                heuristic = self.problem.domain.heuristic(new_state, self.problem.goals)
                # print("heuristic: ", heuristic)
                new_node = SearchNode(
                    new_state, 
                    node, 
                    cost,
                    heuristic=heuristic,
                    action=act,
                    )
                
                new_lower_nodes.append(new_node)
                
            self.add_to_open(new_lower_nodes)
        return []
    
    # add new nodes to the list of open nodes according to the strategy
    def add_to_open(self, new_lower_nodes):
        self.open_nodes.extend(new_lower_nodes)
        
        if self.strategy == "A*":
            self.open_nodes.sort(key=lambda node: node.cost + node.heuristic)
            #print(self.open_nodes)
        elif self.strategy == "greedy":
            self.open_nodes.sort(key=lambda node: node.heuristic)
        else:
            sys.exit(f"Unknown strategy: {self.strategy}")        
        
    def __str__(self):
        return f"SearchTree: {self.problem} {self.best_solution} {self.non_terminals} {self.open_nodes}"
    