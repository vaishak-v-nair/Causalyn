import ast
import threading
from typing import List, Dict, Any
from z3 import Solver, Int, sat, unsat

_z3_lock = threading.Lock()

class ASTVariableExtractor(ast.NodeVisitor):
    def __init__(self):
        self.variables: Dict[str, Any] = {}

    def visit_Assign(self, node: ast.Assign):
        if isinstance(node.value, ast.Constant):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.variables[target.id] = node.value.value
        self.generic_visit(node)

def verify_invariants(ast_tree: ast.AST, active_rules: List[str]) -> bool:
    """
    Formal verification engine using Z3.
    Evaluates whether the provided AST adheres to the active structural and numerical rules.
    """
    extractor = ASTVariableExtractor()
    extractor.visit(ast_tree)
    variables = extractor.variables

    if not active_rules:
        return True

    with _z3_lock:
        solver = Solver()
        
        # Inject extracted state variables into Z3 as constants
        z3_vars = {}
        for var_name, var_value in variables.items():
            if isinstance(var_value, (int, float)):
                z3_var = Int(var_name)
                z3_vars[var_name] = z3_var
                solver.add(z3_var == int(var_value))
                
        # Parse active rules and add as constraints
        for rule in active_rules:
            if rule == "MAX_THREADS=16":
                # Ensure threads <= 16 if 'threads' is defined
                if "threads" in z3_vars:
                    solver.add(z3_vars["threads"] <= 16)
                else:
                    t = Int("threads")
                    solver.add(t <= 16)
            elif rule == "MAX_MEMORY=1024":
                if "memory" in z3_vars:
                    solver.add(z3_vars["memory"] <= 1024)
            elif rule == "LEAK_CHECK":
                if "sockets" in z3_vars:
                    solver.add(z3_vars["sockets"] <= 100)
            elif rule == "FORBID_SUBPROCESS":
                # Check for subprocess AST nodes
                for node in ast.walk(ast_tree):
                    if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            if "subprocess" in alias.name:
                                return False
                
        # Check satisfiability
        result = solver.check()
        if result == sat:
            return True
        else:
            return False
