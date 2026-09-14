"""
Mathematical Kernel (kappa Engine) for the Vaishak Principle of Semantic Nullification (VPSN).

Physical realization of the Paradox Index:
    S in N_semantic <==> kappa(S) = 0.0

Computes topological curvature tension penalties across candidate states using
AST NodeVisitor analysis, regex secret exfiltration scanners, and syntactic invariant checks.
"""

from __future__ import annotations

import ast
import re
from typing import Any, Dict, List, Optional, Tuple


class ParadoxVisitor(ast.NodeVisitor):
    """AST NodeVisitor that measures structural invariant breaches and computes kappa."""

    def __init__(self, intent_vector: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.kappa: float = 0.0
        self.violations: List[str] = []
        self.intent_vector: Dict[str, Any] = intent_vector or {"block_os": True}

    def visit_Import(self, node: ast.Import) -> None:
        """Flag unauthorized direct module imports."""
        for alias in node.names:
            name = alias.name.split(".")[0]
            if self.intent_vector.get("block_os", True) and name in {
                "os",
                "subprocess",
                "sys",
                "socket",
                "pty",
                "shutil",
            }:
                self.kappa += 50.0  # High curvature tension spike
                self.violations.append(f"Paradox: Unauthorized import of {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Flag unauthorized from-imports (e.g. from subprocess import Popen)."""
        if node.module:
            root_mod = node.module.split(".")[0]
            if self.intent_vector.get("block_os", True) and root_mod in {
                "os",
                "subprocess",
                "sys",
                "socket",
                "pty",
                "shutil",
            }:
                self.kappa += 50.0
                self.violations.append(f"Paradox: Unauthorized from-import from {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Detect hazardous dynamic execution functions (eval, exec, __import__)."""
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name in {"eval", "exec", "__import__", "compile"}:
            self.kappa += 75.0
            self.violations.append(f"Paradox: Hazardous dynamic execution call '{func_name}'")

        if func_name in {"system", "popen", "spawn", "call"} and isinstance(node.func, ast.Attribute):
            self.kappa += 100.0
            self.violations.append(f"Paradox: Unauthorized system call '{func_name}' detected")

        self.generic_visit(node)

    def visit_Delete(self, node: ast.Delete) -> None:
        """Flag deletion of protected nodes."""
        if self.intent_vector.get("block_deletion", True):
            self.kappa += 30.0
            self.violations.append("Paradox: Explicit AST deletion operation detected")
        self.generic_visit(node)


# Precompiled regular expressions for credential and secret pattern detection
SECRET_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9_-]{20,}", re.IGNORECASE), "OpenAI / Claude API key"),
    (re.compile(r"gh[pousr]_[a-zA-Z0-9]{20,}", re.IGNORECASE), "GitHub Personal Access Token"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
    (re.compile(r"nvapi-[a-zA-Z0-9_-]{20,}", re.IGNORECASE), "NVIDIA API Key"),
    (re.compile(r"-----BEGIN (?:[A-Z0-9_-]+ )*PRIVATE KEY-----"), "PEM Encrypted Private Key"),
    (re.compile(r"api[_-]?secret[_-]?key", re.IGNORECASE), "API Secret Key Token"),
    (re.compile(r"demo-vault-secret-key-98765-production-token", re.IGNORECASE), "Demo Vault Secret Token"),
    (re.compile(r"demo_prod_jwt_token_causalyn_safe", re.IGNORECASE), "Demo JWT Token"),
]


def compute_paradox_index(
    candidate_code: str, intent_vector: Optional[Dict[str, Any]] = None
) -> Tuple[float, List[str]]:
    """
    Compute the Paradox Index kappa(S) for candidate code against an Intent Vector.

    Mathematical Invariant:
        S in N_semantic <==> kappa(S) == 0.0

    Returns:
        Tuple[float, List[str]]: (kappa, violations)
    """
    if not isinstance(candidate_code, str):
        return 0.0, []

    # 1. Check for valid AST syntax
    try:
        tree = ast.parse(candidate_code)
    except SyntaxError:
        # Invalid syntax represents infinite topological rupture / paradox
        return float("inf"), ["Paradox: AST Syntax Corruption"]

    # 2. Traverse AST with ParadoxVisitor
    visitor = ParadoxVisitor(intent_vector)
    visitor.visit(tree)

    # 3. Scan code content for plaintext secret exfiltration
    if not intent_vector or intent_vector.get("block_secrets", True):
        for pattern, label in SECRET_PATTERNS:
            if pattern.search(candidate_code):
                visitor.kappa += 100.0
                visitor.violations.append(f"Paradox: Plaintext API secret detected ({label})")

    return visitor.kappa, visitor.violations

