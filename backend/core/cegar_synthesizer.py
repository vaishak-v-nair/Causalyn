import ast
import threading
from typing import Tuple, Dict, Any, Optional
from z3 import Solver, Int, sat, unsat

_z3_lock = threading.Lock()

class ASTConstraintInjector(ast.NodeTransformer):
    """Dynamically mutates an AST based on Z3 counterexample solutions."""
    def __init__(self, replacements: Dict[str, int]):
        self.replacements = replacements

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in self.replacements:
                new_value = self.replacements[target.id]
                return ast.copy_location(
                    ast.Assign(
                        targets=node.targets,
                        value=ast.Constant(value=new_value)
                    ),
                    node
                )
        return node

class AcausalSynthesizer:
    def __init__(self):
        self.rules = []

    def compile_intent_manifold(self, rules: list):
        """Compiles architectural invariants into first-order logic."""
        self.rules.extend(rules)

    def synthesize_valid_state(
        self, 
        source_code: str, 
        state_vars: Dict[str, int], 
        constraints: list
    ) -> Tuple[float, str, Optional[Dict[str, Any]]]:
        """
        Evaluates candidate state via CEGIS (Counterexample-Guided Inductive Synthesis).
        Thread-safe: Protected by global _z3_lock to prevent Z3 C++ AST context contention.
        Returns: (kappa, final_code, patch_metadata)
        """
        # Sanitize and coerce state variables
        clean_vars: Dict[str, int] = {}
        for k, v in state_vars.items():
            try:
                clean_vars[str(k)] = int(v)
            except (ValueError, TypeError):
                clean_vars[str(k)] = 0

        with _z3_lock:
            try:
                solver = Solver()
                for rule in self.rules:
                    solver.add(rule)

                z3_vars = {name: Int(name) for name in clean_vars}
                
                # Apply current state mutations
                for name, val in clean_vars.items():
                    solver.add(z3_vars[name] == val)

                for c in constraints:
                    solver.add(c(z3_vars))

                result = solver.check()

                if result == sat:
                    return 0.0, source_code, None

                # PARADOX DETECTED: Solve for minimal correction (Ricci Flow Relaxation)
                relax_solver = Solver()
                for rule in self.rules:
                    relax_solver.add(rule)

                # Add constraints without the illegal candidate values
                for c in constraints:
                    relax_solver.add(c(z3_vars))

                if relax_solver.check() == sat:
                    model = relax_solver.model()
                    corrections = {
                        name: model[z3_vars[name]].as_long()
                        for name in clean_vars
                        if model[z3_vars[name]] is not None
                    }
                else:
                    return 999.0, "", {"annihilated": True}
            except Exception as e:
                return 999.0, "", {"annihilated": True, "error": str(e)}

        # Synthesize corrected AST or fallback to regex substitution outside the Z3 lock
        corrected_code = source_code
        try:
            parsed_ast = ast.parse(source_code)
            transformer = ASTConstraintInjector(corrections)
            mutated_ast = transformer.visit(parsed_ast)
            ast.fix_missing_locations(mutated_ast)
            corrected_code = ast.unparse(mutated_ast)
        except Exception:
            import re
            for k, v in corrections.items():
                corrected_code = re.sub(rf'\b{re.escape(k)}\s*[:=]\s*\d+', f"{k} = {v}", corrected_code)

        return 1.0, corrected_code, {"corrected": True, "values": corrections}
