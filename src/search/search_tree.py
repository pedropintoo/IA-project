'''
 # @ Authors: 
 #  - Pedro Pinto (pmap@ua.pt)
 #  - Joao Pinto (jpapinto@ua.pt)
 #  - Guilherme Santos (gui.santos91@ua.pt)
 # @ Create Time: 2024-10-13
 '''
import heapq
import datetime

from src.search.search_node import SearchNode
from src.search.search_problem import SearchProblem
from src.utils.exceptions import TimeLimitExceeded

class SearchTree:
    """Search Tree"""
    
    def __init__(self, problem: SearchProblem):
        self.problem = problem
        root = SearchNode(problem.initial, None, heuristic=problem.domain.heuristic(problem.initial, problem.goals))
        self.open_nodes = [root]
        heapq.heapify(self.open_nodes)
        self._best_solution = (root.heuristic, root)
        self.non_terminals = 0

    @property
    def best_solution(self):
        return self._best_solution[1]

    # Path from root to node
    def inverse_plan(self, node):
        n = node
        _plan = []
        while n is not None:
            if n.action:
                _plan.append(n.action)
            n = n.parent
        return _plan

    # Search solution
    def search(self, time_limit=None):
        while self.open_nodes is not None and len(self.open_nodes) > 0:          
            node = heapq.heappop(self.open_nodes)

            ## Goals test: all goals are satisfied
            if self.problem.goal_test(node.state):
                self._best_solution = node
                return self.inverse_plan(node)            
            
            self.non_terminals += 1
            new_lower_nodes = []
            visited_goal = None
            ## Iterate over possible actions to generate new nodes
            for act in self.problem.domain.actions(node.state):
                
                if time_limit is not None and datetime.datetime.now() >= time_limit: 
                    ## Time limit exceeded
                    raise TimeLimitExceeded(f"Time limit exceeded: {(datetime.datetime.now() - time_limit).total_seconds()}s")

                new_state = self.problem.domain.result(node.state, act, self.problem.goals)

                if node.in_parent(new_state):
                    continue

                cost = node.cost + self.problem.domain.cost(node.state, act)
                new_node = SearchNode(
                    new_state, 
                    node, 
                    cost,
                    heuristic=self.problem.domain.heuristic(new_state, self.problem.goals), # aqui ele considera os que ja foram visitados, com base no estado
                    action=act,
                    )
                new_lower_nodes.append(new_node)
                
                ## Store the best solution
                if self._best_solution[0] > new_node.heuristic:
                    self._best_solution = (new_node.heuristic, new_node)

            self.add_to_open(new_lower_nodes)
        return None
    
    # add new nodes to the list of open nodes according to the strategy
    def add_to_open(self, new_lower_nodes):
        for node in new_lower_nodes:
            heapq.heappush(self.open_nodes, node)
    