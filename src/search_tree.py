'''
 # @ Authors: 
 #  - Pedro Pinto (pmap@ua.pt)
 #  - Joao Pinto (jpapinto@ua.pt)
 #  - Guilherme Santos (gui.santos91@ua.pt)
 # @ Create Time: 2024-10-13
 '''
from src.search_node import SearchNode
from src.search_problem import SearchProblem

class SearchTree:
    """Search Tree"""
    
    def __init__(self, problem: SearchProblem, strategy='A*'):
        self.problem = problem
        root = SearchNode(problem.initial, None, heuristic=problem.domain.heuristic(problem.initial, problem.goal))
        self.open_nodes = [root]
        self.strategy = strategy
        self.solution = None
        self.non_terminals = 0
        
    @property 
    def avg_branching(self):
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
    def search(self, limit=None):
        while self.open_nodes != []:
            node = self.open_nodes.pop(0) # don't forgot this pop! in self.terminals
            if self.problem.goal_test(node.state):
                self.solution = node
                return self.get_path(node)

            self.non_terminals += 1
            if limit != None and node.depth >= limit:
                continue
            
            lnewnodes = [] # lower nodes!
            for act in self.problem.domain.actions(node.state): # get the next possible actions!
                newstate = self.problem.domain.result(node.state,act)
                if node.in_parent(newstate):
                    continue
                cost = node.cost + self.problem.domain.cost(node.state, act)
                newnode = SearchNode(
                    newstate, 
                    node, 
                    cost,
                    heuristic=self.problem.domain.heuristic(newstate, self.problem.goal),
                    action=act
                    )
                lnewnodes.append(newnode)
                            
            self.add_to_open(lnewnodes)
        return None
    
    # add new nodes to the list of open nodes according to the strategy
    def add_to_open(self, lnewnodes):
        if self.strategy == 'breadth':
            self.open_nodes.extend(lnewnodes)
        elif self.strategy == 'depth':
            self.open_nodes[:0] = lnewnodes
        elif self.strategy == 'uniform':
            self.open_nodes.extend(lnewnodes)
            self.open_nodes.sort(key=lambda node: node.cost)
        elif self.strategy == 'greedy':
            self.open_nodes.extend(lnewnodes)
            self.open_nodes.sort(key=lambda node: node.heuristic)
        elif self.strategy == 'A*':
            self.open_nodes.extend(lnewnodes)
            self.open_nodes.sort(key=lambda node: node.cost + node.heuristic)