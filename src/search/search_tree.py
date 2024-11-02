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
    
    def __init__(self, problem: SearchProblem, strategy='A*'):
        self.problem = problem
        root = SearchNode(problem.initial, None, heuristic=problem.domain.heuristic(problem.initial, problem.goal))
        self.open_nodes = [root]
        heapq.heapify(self.open_nodes)
        self.strategy = strategy
        self.solution = None
        self.non_terminals = 0
        self.max_total_cost = root.heuristic
        
    @property 
    def avg_branching(self):
        if self.non_terminals == 0:
            return 0
        return (self.terminals + self.non_terminals - 1) / self.non_terminals
     
    @property
    def terminals(self):
        return len(self.open_nodes) + 1
    
    @property
    def length(self):
        return self.solution.depth

    @property
    def cost(self):
        return self.solution.cost

    # Path (sequence of states) from root to node
    def get_path(self,node):
        path = []
        while node is not None:
            path[:0] = [node.state]
            node = node.parent
        return path

    @property
    def plan(self):
        n = self.solution
        _plan = []
        while n is not None:
            if n.action:
                _plan[:0] = [n.action]
            n = n.parent
        return _plan
    
    @property
    def inverse_plan(self):
        n = self.solution
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

            # Goal test
            if self.problem.goal_test(node.state):
                self.solution = node
                return self.get_path(node)

            self.non_terminals += 1
            
            # if node.cost + node.heuristic > self.max_total_cost:
            #     print("\33[33mPruning node with cost {} and heuristic {}\33[0m".format(node.cost, node.heuristic))
            #     continue

            new_lower_nodes = []
            # Iterate over possible actions to generate new nodes
            for act in self.problem.domain.actions(node.state):
                
                if time_limit is not None and datetime.datetime.now() >= time_limit: 
                    print(f"Time limit: {time_limit}")
                    raise TimeLimitExceeded(f"Time limit exceeded: {(datetime.datetime.now() - time_limit).total_seconds()}s")

                new_state = self.problem.domain.result(node.state,act)

                if node.in_parent(new_state):
                    continue
                
                cost = node.cost + self.problem.domain.cost(node.state, act)
                new_node = SearchNode(
                    new_state, 
                    node, 
                    cost,
                    heuristic=self.problem.domain.heuristic(new_state, self.problem.goal),
                    action=act
                    )
                new_lower_nodes.append(new_node)

            

            self.add_to_open(new_lower_nodes)
        return None
    
    # add new nodes to the list of open nodes according to the strategy
    def add_to_open(self, new_lower_nodes):
        for node in new_lower_nodes:
            if self.strategy == 'greedy':
                heapq.heappush(self.open_nodes, node)
            elif self.strategy == 'A*':
                heapq.heappush(self.open_nodes, node)
    