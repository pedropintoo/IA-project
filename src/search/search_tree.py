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
        self.best_solution = {"total_cost": root.heuristic, "node": root} 
        self.non_terminals = 0

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
            if self.problem.satisfies_first_goal(n.state):
                solution = n
            else:
                if solution:
                    break # condition is no longer satisfied
            n = n.parent         
        return self.inverse_plan(solution)

    # Search solution
    def search(self, time_limit=None):
        while self.open_nodes is not None and len(self.open_nodes) > 0:          
            node = heapq.heappop(self.open_nodes)

            ## Goals test: all goals are satisfied
            if self.problem.goal_test(node.state):
                self.best_solution = {"total_cost": node.heuristic, #+ node.cost,
                                      "node": node}
                # print(node.state["visited_goals"])
                return self.inverse_plan_to_solution(node)

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

                # ## Ignore nodes with heuristic much greater than the best solution
                # if self.best_solution["total_cost"]*5 < new_total_cost:
                #     continue
                
                new_lower_nodes.append(new_node)
                
                new_total_cost = new_node.heuristic #+ new_node.cost
                ## Store the best solution
                if self.best_solution["total_cost"] > new_total_cost:
                    self.best_solution = {"total_cost": new_total_cost, "node": new_node}

            self.add_to_open(new_lower_nodes)
        return []
    
    # add new nodes to the list of open nodes according to the strategy
    def add_to_open(self, new_lower_nodes):
        for node in new_lower_nodes:
            heapq.heappush(self.open_nodes, node)
    
    def remove_goal(self):
        goal = self.problem.goals.pop(0)
        
        ## Remove affected nodes
        new_open_nodes = []
        for node in self.open_nodes:
            if not self.problem.domain.satisfies(node.state, goal):
                new_open_nodes.append(node)
        self.open_nodes = new_open_nodes
        heapq.heapify(self.open_nodes)
        
        
    def __str__(self):
        return f"SearchTree: {self.problem} {self.best_solution} {self.non_terminals} {self.open_nodes}"
    