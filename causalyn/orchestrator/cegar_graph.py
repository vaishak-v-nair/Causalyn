"""LangGraph-driven CEGAR-CEGIS Consensus State Machine.

Orchestrates the macro-lifecycle:
Intercept -> Sandbox Provisioning -> Shadow Execution -> Policy RAG ->
Deterministic Verification Matrix -> Paradox Index (\u03ba) ->
CEGAR Refinement Loop -> Atomic Commit Boundary / Annihilation.
"""

from __future__ import annotations

import ast
import json
import os
import re
import time

from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from ..api.contracts import ActionType, InterceptActionRequest
from ..model.world_state import WorldStateManager
from ..shadow.drivers import (
    AbstractSandboxDriver,
    LocalMemoryDriver,
    ShadowExecutionResult,
)
from ..verification.policy_rag import PolicyRAGEngine


class CausalynGraphState(TypedDict):
    """Execution state carried across LangGraph nodes."""
    session_id: str
    pipeline_id: str
    intent: str
    iteration: int
    max_iterations: int
    sandbox_id: Optional[str]
    proposed_action: Dict[str, Any]
    shadow_result: Optional[Dict[str, Any]]
    violations: List[Dict[str, Any]]
    paradox_index: float
    verification_decision: str  # "allow", "deny", "retry"
    commit_status: Optional[str]  # "committed", "annihilated", "pending"
    error: Optional[str]
    unified_diffs: Dict[str, str]
    counterexamples: List[Dict[str, Any]]
    applicable_policies: List[str]
    duration_ms: float


class CEGAROrchestrationGraph:
    """Manages compilation and execution of the Causalyn CEGAR state graph."""

    def __init__(
        self,
        world_state_manager: Optional[WorldStateManager] = None,
        sandbox_driver: Optional[AbstractSandboxDriver] = None,
        policy_rag: Optional[PolicyRAGEngine] = None,
    ) -> None:
        self.world_state_manager = world_state_manager
        self.sandbox_driver = sandbox_driver or LocalMemoryDriver(
            initial_files=world_state_manager.get_current_state().file_system if world_state_manager else {}
        )
        self.policy_rag = policy_rag or PolicyRAGEngine()
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(CausalynGraphState)

        builder.add_node("provision_sandbox", self._provision_sandbox_node)
        builder.add_node("rag_policy_retrieval", self._rag_policy_retrieval_node)
        builder.add_node("execute_shadow", self._execute_shadow_node)
        builder.add_node("verify_consensus", self._verify_consensus_node)
        builder.add_node("cegar_refine", self._cegar_refine_node)
        builder.add_node("commit_boundary", self._commit_boundary_node)

        # Graph Edges
        builder.add_edge(START, "provision_sandbox")
        builder.add_edge("provision_sandbox", "rag_policy_retrieval")
        builder.add_edge("rag_policy_retrieval", "execute_shadow")
        builder.add_edge("execute_shadow", "verify_consensus")

        # Conditional branching after verification
        builder.add_conditional_edges(
            "verify_consensus",
            self._route_after_verification,
            {
                "allow": "commit_boundary",
                "retry": "cegar_refine",
                "deny": "commit_boundary",
            },
        )

        # CEGAR loop back
        builder.add_edge("cegar_refine", "execute_shadow")
        builder.add_edge("commit_boundary", END)

        return builder.compile()

    async def _provision_sandbox_node(self, state: CausalynGraphState) -> Dict[str, Any]:
        """Layer 2: Provision ephemeral sandbox workspace."""
        if state.get("sandbox_id"):
            return {}

        # If LocalMemoryDriver, sync latest world state files
        if isinstance(self.sandbox_driver, LocalMemoryDriver) and self.world_state_manager:
            self.sandbox_driver.seed_initial_files(self.world_state_manager.get_current_state().file_system)

        sandbox_id = await self.sandbox_driver.provision()
        return {"sandbox_id": sandbox_id, "iteration": 1}

    async def _rag_policy_retrieval_node(self, state: CausalynGraphState) -> Dict[str, Any]:
        """Layer 3: Query Milvus RAG engine for applicable invariant rules."""
        policies = self.policy_rag.retrieve_applicable_policies(state.get("intent", ""), top_k=5)
        policy_ids = [p.policy_id for p in policies]
        return {"applicable_policies": policy_ids}

    async def _execute_shadow_node(self, state: CausalynGraphState) -> Dict[str, Any]:
        """Layer 2: Execute proposed action in complete acausal isolation."""
        sandbox_id = state["sandbox_id"]
        assert sandbox_id is not None

        action_data = state["proposed_action"]
        action = InterceptActionRequest(
            session_id=state["session_id"],
            request_id=f"{state['pipeline_id']}-r{state['iteration']}",
            agent_framework=action_data.get("agent_framework", "custom"),
            action_type=ActionType(action_data.get("action_type", "file_write")),
            target_path=action_data.get("target_path"),
            payload=action_data.get("payload", {}),
            environment_variables=action_data.get("environment_variables", {}),
        )

        exec_res: ShadowExecutionResult = await self.sandbox_driver.execute_action(sandbox_id, action)

        return {
            "shadow_result": {
                "exit_code": exec_res.exit_code,
                "stdout": exec_res.stdout,
                "stderr": exec_res.stderr,
                "duration_ms": exec_res.duration_ms,
                "files_added": exec_res.files_added,
                "files_modified": exec_res.files_modified,
                "files_deleted": exec_res.files_deleted,
            },
            "unified_diffs": exec_res.unified_diffs,
        }

    async def _verify_consensus_node(self, state: CausalynGraphState) -> Dict[str, Any]:
        """Layer 3: Deterministic Invariant Suite & Paradox Index calculation."""
        shadow_res = state.get("shadow_result") or {}
        diffs = state.get("unified_diffs") or {}
        violations: List[Dict[str, Any]] = []

        files_modified = shadow_res.get("files_modified", {})
        files_added = shadow_res.get("files_added", {})
        files_deleted = shadow_res.get("files_deleted", [])

        # 1. Protected Path Guard & Path Traversal Guard
        protected_prefixes = ("/protected", "/secrets", "/.env", "/config")
        all_touched = set(files_modified.keys()) | set(files_added.keys()) | set(files_deleted)
        
        # Check target_path in proposed action as well
        prop_act = state.get("proposed_action") or {}
        target_path_str = prop_act.get("target_path") or ""
        if target_path_str:
            norm_target = os.path.normpath(target_path_str.replace("\\", "/"))
            is_traversal = (
                ".." in target_path_str.split("/")
                or ".." in target_path_str.split("\\")
                or norm_target.startswith("..")
                or any(norm_target.startswith(bad) for bad in ("/etc", "/var", "/usr", "/bin", "/root", "/boot", "/proc", "/sys", "\\etc", "\\windows"))
                or any(target_path_str.startswith(bad) for bad in ("/etc", "/var", "/usr", "/bin", "/root", "/boot", "/proc", "/sys"))
            )
            if is_traversal:
                desc = f"Path traversal attack detected: {target_path_str}"
                violations.append({
                    "invariant_id": "SEC-004-PATH-TRAVERSAL",
                    "code": "SEC-004-PATH-TRAVERSAL",
                    "description": desc,
                    "message": desc,
                    "severity": "critical",
                    "penalty": 1.0,
                })
            for pfx in protected_prefixes:
                if target_path_str.startswith(pfx):
                    all_touched.add(target_path_str)

        for path in all_touched:
            for pfx in protected_prefixes:
                if path.startswith(pfx):
                    is_del = (path in files_deleted)
                    desc = f"Unauthorized deletion of protected path {path}" if is_del else f"Unauthorized access or modification to protected path {path}"
                    violations.append({
                        "invariant_id": "SEC-001-PROTECTED-PATH",
                        "code": "POL-001-PROTECTED-RESOURCE",
                        "description": desc,
                        "message": desc,
                        "severity": "critical" if is_del else "high",
                        "penalty": 1.0 if is_del else 0.8,
                    })
                    break

        # 2. Secret Exfiltration Scanner
        secret_patterns = [
            re.compile(r"sk-[a-zA-Z0-9_-]{20,}", re.IGNORECASE),
            re.compile(r"gsk_[a-zA-Z0-9_-]{20,}", re.IGNORECASE),
            re.compile(r"nvapi-[a-zA-Z0-9_-]{20,}", re.IGNORECASE),
            re.compile(r"api[_-]?secret", re.IGNORECASE),
            re.compile(r"aws[_-]?secret", re.IGNORECASE),
            re.compile(r"AKIA[0-9A-Z]{16}"),
            re.compile(r"gh[pousr]_[a-zA-Z0-9]{20,}", re.IGNORECASE),
            re.compile(r"github[_-]?token", re.IGNORECASE),
            re.compile(r"-----BEGIN (?:[A-Z0-9_-]+ )*PRIVATE KEY-----"),
        ]

        candidate_contents = {**files_modified, **files_added}
        for path, content in candidate_contents.items():
            if not isinstance(content, str):
                continue
            for pat in secret_patterns:
                if pat.search(content):
                    desc = f"Detected plaintext credentials / private key in {path}"
                    violations.append({
                        "invariant_id": "SEC-002-SECRET-LEAK",
                        "code": "SEC-002-SECRET-LEAK",
                        "description": desc,
                        "message": desc,
                        "severity": "critical",
                        "penalty": 1.0,
                    })
                    break

        # 3. AST Syntax Parser & Dangerous Execution / RCE Guard on Python files
        for path, content in candidate_contents.items():
            if path.endswith(".py") and isinstance(content, str):
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec", "__import__"):
                                desc = f"Dangerous RCE function call detected: {node.func.id}() in {path}"
                                violations.append({
                                    "invariant_id": "SEC-003-RCE-INJECTION",
                                    "code": "SEC-003-RCE-INJECTION",
                                    "description": desc,
                                    "message": desc,
                                    "severity": "critical",
                                    "penalty": 1.0,
                                })
                                break
                            elif isinstance(node.func, ast.Attribute):
                                attr_name = node.func.attr
                                val_id = getattr(node.func.value, "id", None)
                                is_internal_cli = path.endswith(("cli.py", "runner.py", "drivers.py"))

                                if attr_name in ("system", "popen", "spawn", "spawnlp", "spawnv") and (val_id == "os" or not val_id):
                                    desc = f"Dangerous process execution detected: .{attr_name}() in {path}"
                                    violations.append({
                                        "invariant_id": "SEC-003-RCE-INJECTION",
                                        "code": "SEC-003-RCE-INJECTION",
                                        "description": desc,
                                        "message": desc,
                                        "severity": "critical",
                                        "penalty": 1.0,
                                    })
                                    break
                                elif attr_name in ("call", "check_call", "check_output", "Popen", "run") and val_id == "subprocess" and not is_internal_cli:
                                    desc = f"Dangerous subprocess execution detected: subprocess.{attr_name}() in {path}"
                                    violations.append({
                                        "invariant_id": "SEC-003-RCE-INJECTION",
                                        "code": "SEC-003-RCE-INJECTION",
                                        "description": desc,
                                        "message": desc,
                                        "severity": "critical",
                                        "penalty": 1.0,
                                    })
                                    break
                        elif isinstance(node, ast.Import):
                            is_internal_cli = path.endswith(("cli.py", "runner.py", "drivers.py"))
                            for alias in node.names:
                                if alias.name in ("subprocess",) and not is_internal_cli:
                                    desc = f"Disallowed module import: {alias.name} in {path}"
                                    violations.append({
                                        "invariant_id": "SEC-003-RCE-INJECTION",
                                        "code": "SEC-003-RCE-INJECTION",
                                        "description": desc,
                                        "message": desc,
                                        "severity": "critical",
                                        "penalty": 1.0,
                                    })
                                    break
                        elif isinstance(node, ast.ImportFrom):
                            is_internal_cli = path.endswith(("cli.py", "runner.py", "drivers.py"))
                            if node.module in ("subprocess",) and not is_internal_cli:
                                desc = f"Disallowed module import from: {node.module} in {path}"
                                violations.append({
                                    "invariant_id": "SEC-003-RCE-INJECTION",
                                    "code": "SEC-003-RCE-INJECTION",
                                    "description": desc,
                                    "message": desc,
                                    "severity": "critical",
                                    "penalty": 1.0,
                                    })
                                break
                except SyntaxError as e:
                    desc = f"Python AST syntax error in {path} at line {e.lineno}: {e.msg}"
                    violations.append({
                        "invariant_id": "SYNTAX-001-VALID-AST",
                        "code": "SYNTAX-001-VALID-AST",
                        "description": desc,
                        "message": desc,
                        "severity": "high",
                        "penalty": 0.8,
                    })

        # 4. Schema Integrity Verifier on JSON files
        for path, content in candidate_contents.items():
            if path.endswith(".json") and isinstance(content, str):
                try:
                    json.loads(content)
                except json.JSONDecodeError as e:
                    desc = f"JSON schema corruption in {path}: {e.msg}"
                    violations.append({
                        "invariant_id": "SCHEMA-001-JSON-TYPES",
                        "code": "SCHEMA-001-JSON-TYPES",
                        "description": desc,
                        "message": desc,
                        "severity": "high",
                        "penalty": 0.7,
                    })

        # 5. Shell Injection & Destructive Command Verifier
        action_type = prop_act.get("action_type") or ""
        cmd_str = (prop_act.get("payload") or {}).get("command") or ""
        if ("shell" in action_type or action_type in ("shell_command", "shell_exec")) and cmd_str:
            destructive_patterns = [
                re.compile(r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--force\s+-r|-r\s+--force)\s+([/~*]|\./)", re.IGNORECASE),
                re.compile(r"rm\s+-rf\s+.*", re.IGNORECASE),
                re.compile(r"mkfs", re.IGNORECASE),
                re.compile(r"dd\s+if=", re.IGNORECASE),
                re.compile(r":\(\)\s*\{\s*:\|:&\s*\};:", re.IGNORECASE),
                re.compile(r"chmod\s+-R\s+777\s+/", re.IGNORECASE),
                re.compile(r"(curl|wget|nc|netcat|ncat)\s+.*http", re.IGNORECASE),
                re.compile(r"\$\(cat\s+/etc/(?:passwd|shadow)\)", re.IGNORECASE),
                re.compile(r"/etc/passwd", re.IGNORECASE),
                re.compile(r"/etc/shadow", re.IGNORECASE),
            ]
            for pat in destructive_patterns:
                if pat.search(cmd_str):
                    desc = f"Destructive shell command / exfiltration pattern detected: {cmd_str}"
                    violations.append({
                        "invariant_id": "SEC-002-SHELL-INJECTION",
                        "code": "SEC-002-SHELL-INJECTION",
                        "description": desc,
                        "message": desc,
                        "severity": "critical",
                        "penalty": 1.0,
                    })
                    break


        # 6. Execution Watchdog check
        if shadow_res.get("exit_code") == 124:
            desc = "Candidate shell command timed out after 10.0s (Watchdog enforced)"
            violations.append({
                "invariant_id": "WATCHDOG-001-TIMEOUT",
                "code": "WATCHDOG-001-TIMEOUT",
                "description": desc,
                "message": desc,
                "severity": "critical",
                "penalty": 1.0,
            })

        # Compute Paradox Index \kappa
        paradox_index = sum(v.get("penalty", 0.5) for v in violations)

        # Decision routing
        current_iter = state.get("iteration", 1)
        max_iter = state.get("max_iterations", 3)

        if paradox_index == 0.0:
            decision = "allow"
        elif current_iter < max_iter:
            decision = "retry"
        else:
            decision = "deny"

        return {
            "violations": violations,
            "paradox_index": paradox_index,
            "verification_decision": decision,
        }

    def _route_after_verification(self, state: CausalynGraphState) -> str:
        """Route to commit, CEGAR refine, or deny based on verification decision."""
        return state.get("verification_decision", "deny")

    async def _cegar_refine_node(self, state: CausalynGraphState) -> Dict[str, Any]:
        """CEGAR Loop: Synthesize counterexample diagnostics and increment iteration."""
        counterexamples = list(state.get("counterexamples", []))
        counterexamples.append({
            "round": state.get("iteration", 1),
            "paradox_index": state.get("paradox_index", 0.0),
            "violations": state.get("violations", []),
        })

        new_iter = state.get("iteration", 1) + 1
        return {
            "iteration": new_iter,
            "counterexamples": counterexamples,
        }

    async def _commit_boundary_node(self, state: CausalynGraphState) -> Dict[str, Any]:
        """Layer 4: Atomic Commit or Instant Annihilation."""
        decision = state.get("verification_decision", "deny")
        sandbox_id = state.get("sandbox_id")

        if decision == "allow":
            # Apply candidate mutations atomically to real WorldStateManager
            if self.world_state_manager and state.get("shadow_result"):
                shadow_res = state["shadow_result"]
                for p, c in shadow_res.get("files_added", {}).items():
                    self.world_state_manager.set_file_content(p, c)
                for p, c in shadow_res.get("files_modified", {}).items():
                    self.world_state_manager.set_file_content(p, c)
                for p in shadow_res.get("files_deleted", []):
                    self.world_state_manager.delete_file(p)

            # Cleanup sandbox
            if sandbox_id:
                await self.sandbox_driver.annihilate(sandbox_id)
            return {"commit_status": "committed"}
        else:
            # Annihilate shadow sandbox instantly (Destructive Semantic Interference)
            if sandbox_id:
                await self.sandbox_driver.annihilate(sandbox_id)
            return {"commit_status": "annihilated"}

    async def invoke(self, initial_state: Dict[str, Any]) -> CausalynGraphState:
        """Execute the CEGAR graph from START to END."""
        start_t = time.perf_counter()
        full_initial: CausalynGraphState = {
            "session_id": initial_state.get("session_id", "session-default"),
            "pipeline_id": initial_state.get("pipeline_id", f"pipe-{int(time.time()*1000)}"),
            "intent": initial_state.get("intent", ""),
            "iteration": 1,
            "max_iterations": initial_state.get("max_iterations", 3),
            "sandbox_id": None,
            "proposed_action": initial_state.get("proposed_action", {}),
            "shadow_result": None,
            "violations": [],
            "paradox_index": 0.0,
            "verification_decision": "pending",
            "commit_status": "pending",
            "error": None,
            "unified_diffs": {},
            "counterexamples": [],
            "applicable_policies": [],
            "duration_ms": 0.0,
        }

        final_state = await self.graph.ainvoke(full_initial)
        final_state["duration_ms"] = (time.perf_counter() - start_t) * 1000
        return final_state
