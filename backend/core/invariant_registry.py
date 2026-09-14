"""
Causalyn Dynamic Invariant Registry
===================================
Maintains active mathematical and semantic invariants governing state space.
Supports both Z3 first-order logic constraints (numerical thresholds) and
semantic AST boundaries (forbidden operations, SQL safety, path isolation).

Thread-safe and dynamically authorable via the web cockpit and CLI.
"""

import threading
import re
from typing import List, Dict, Any, Tuple, Optional
from z3 import Int, ArithRef

class InvariantRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        self._invariants: Dict[str, Dict[str, Any]] = {
            "inv_threads": {
                "id": "inv_threads",
                "name": "MAX_THREADS",
                "kind": "numerical",
                "target_var": "threads",
                "operator": "<=",
                "threshold": 16,
                "description": "Worker concurrency bound: threads <= 16",
                "enabled": True,
                "builtin": True
            },
            "inv_memory": {
                "id": "inv_memory",
                "name": "MAX_MEMORY_MB",
                "kind": "numerical",
                "target_var": "memory",
                "operator": "<=",
                "threshold": 1024,
                "description": "Ephemeral heap allocation: memory <= 1024 MB",
                "enabled": True,
                "builtin": True
            },
            "inv_sockets": {
                "id": "inv_sockets",
                "name": "MAX_SOCKETS",
                "kind": "numerical",
                "target_var": "sockets",
                "operator": "<=",
                "threshold": 100,
                "description": "Network descriptor ceiling: sockets <= 100",
                "enabled": True,
                "builtin": True
            },
            "inv_forbid_db_drop": {
                "id": "inv_forbid_db_drop",
                "name": "FORBID_DB_DROP",
                "kind": "semantic",
                "pattern": r"(?i)(drop\s+table|truncate\s+table|delete\s+from\s+[a-z0-9_]+\s*;?$)",
                "description": "Disallow destructive DDL/DML table drops or truncate commands",
                "enabled": True,
                "builtin": True
            },
            "inv_forbid_secrets": {
                "id": "inv_forbid_secrets",
                "name": "FORBID_SECRET_LEAK",
                "kind": "semantic",
                "pattern": r"(?i)(api[_-]?key\s*=|secret[_-]?key\s*=|credentials\s*=|BEGIN\s+PRIVATE\s+KEY)",
                "description": "Prevent hardcoded API secrets or private cryptographic keys",
                "enabled": True,
                "builtin": True
            },
            "inv_allowed_paths": {
                "id": "inv_allowed_paths",
                "name": "WORKSPACE_SANDBOX_ISOLATION",
                "kind": "path",
                "allowed_prefixes": ["src", "config", "core", "services", "db", "api", "tasks", "network"],
                "description": "Prevent file mutations outside authorized application directory tree",
                "enabled": True,
                "builtin": True
            }
        }

    def get_all(self) -> List[Dict[str, Any]]:
        """Returns all invariants as a list of dictionaries."""
        with self._lock:
            return [dict(inv) for inv in self._invariants.values()]

    def get(self, inv_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single invariant by ID."""
        with self._lock:
            inv = self._invariants.get(inv_id)
            return dict(inv) if inv else None

    def toggle(self, inv_id: str, enabled: Optional[bool] = None) -> bool:
        """Toggles or sets the enabled status of an invariant."""
        with self._lock:
            if inv_id not in self._invariants:
                return False
            if enabled is None:
                self._invariants[inv_id]["enabled"] = not self._invariants[inv_id]["enabled"]
            else:
                self._invariants[inv_id]["enabled"] = bool(enabled)
            return True

    def add_invariant(self, inv: Dict[str, Any]) -> Dict[str, Any]:
        """Registers a new custom invariant."""
        with self._lock:
            inv_id = inv.get("id") or f"custom_{len(self._invariants) + 1}_{inv.get('name', 'rule').lower()}"
            record = {
                "id": inv_id,
                "name": inv.get("name", "CUSTOM_RULE"),
                "kind": inv.get("kind", "numerical"),
                "description": inv.get("description", "User-defined custom invariant"),
                "enabled": True,
                "builtin": False
            }
            kind = inv.get("kind") or inv.get("type") or "numerical"
            record["kind"] = kind
            record["type"] = kind
            if kind == "numerical":
                record["target_var"] = inv.get("target_var") or "threads"
                record["operator"] = inv.get("operator") or "<="
                thresh_val = inv.get("threshold")
                if thresh_val is None:
                    expr = inv.get("expression") or ""
                    import re
                    match = re.search(r"(\d+)", expr)
                    thresh_val = int(match.group(1)) if match else 16
                record["threshold"] = int(thresh_val)
                record["expression"] = inv.get("expression") or f"{record['target_var']} {record['operator']} {record['threshold']}"
            elif kind == "semantic":
                record["pattern"] = inv.get("pattern") or inv.get("expression") or r""
                record["expression"] = record["pattern"]
            elif kind == "path":
                record["allowed_prefixes"] = inv.get("allowed_prefixes", ["src"])
                record["expression"] = f"prefixes: {record['allowed_prefixes']}"

            self._invariants[inv_id] = record
            return dict(record)

    def delete_invariant(self, inv_id: str) -> bool:
        """Deletes a custom invariant (builtins cannot be deleted, only toggled)."""
        with self._lock:
            if inv_id in self._invariants and not self._invariants[inv_id].get("builtin", False):
                del self._invariants[inv_id]
                return True
            return False

    def compile_z3_constraints(self) -> List[Any]:
        """
        Compiles all active numerical invariants into Z3 lambda constraint functions.
        """
        constraints = []
        with self._lock:
            for inv in self._invariants.values():
                if not inv["enabled"] or inv["kind"] != "numerical":
                    continue
                var_name = inv["target_var"]
                threshold = inv["threshold"]
                op = inv.get("operator", "<=")

                if op == "<=":
                    constraints.append(
                        (lambda v, vn=var_name, th=threshold: v.get(vn, Int(vn)) <= th)
                    )
                elif op == "<":
                    constraints.append(
                        (lambda v, vn=var_name, th=threshold: v.get(vn, Int(vn)) < th)
                    )
                elif op == "==":
                    constraints.append(
                        (lambda v, vn=var_name, th=threshold: v.get(vn, Int(vn)) == th)
                    )
        return constraints

    def evaluate_semantic_and_path(
        self,
        target_file: str,
        content: str,
        state_vars: Dict[str, int]
    ) -> Tuple[bool, List[str]]:
        """
        Evaluates active semantic and path invariants against proposed state and code.
        Returns: (is_valid, list_of_violation_names)
        """
        violations = []
        with self._lock:
            for inv in self._invariants.values():
                if not inv["enabled"]:
                    continue

                if inv["kind"] == "semantic":
                    pattern = inv.get("pattern")
                    if pattern and re.search(pattern, content):
                        violations.append(f"{inv['name']} ({inv['description']})")

                elif inv["kind"] == "path":
                    prefixes = inv.get("allowed_prefixes", [])
                    clean_target = target_file.replace("\\", "/").lstrip("/")
                    
                    # Check for path traversal attempts
                    if ".." in clean_target or clean_target.startswith("/"):
                        violations.append(f"{inv['name']} (Path traversal detected)")
                        continue

                    if prefixes:
                        matched = any(clean_target.startswith(p) for p in prefixes)
                        # If file is directly in root like config.py or test.py, allow if root recognized
                        if not matched and "/" in clean_target:
                            violations.append(f"{inv['name']} (File outside authorized prefixes: {prefixes})")

        return (len(violations) == 0, violations)

# Global singleton
registry = InvariantRegistry()
