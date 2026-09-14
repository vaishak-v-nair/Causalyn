"""Staging Infrastructure Gate & Container Hypervisor (Milestone M4).

Evaluates container manifests, Kubernetes specs, and microservice definitions
in shadow isolation before deployment to staging infrastructure.
"""

from __future__ import annotations

import difflib
import re
import time
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field

from ..api.contracts import GateDecision


class ProxyPromptInterceptor:
    """
    Self-Reflective Invariant Injection.
    Flips RAG on its head: Injects absolute mathematical boundaries (Intent Vector I)
    directly into the agent's prompt to guide generation along valid semantic manifolds.
    """
    
    def __init__(self, intent_vector: Optional[Dict[str, Any]] = None):
        self.intent_vector = intent_vector or {}

    def inject_invariants(self, original_prompt: str) -> str:
        """Injects system boundaries into the prompt."""
        if not self.intent_vector:
            return original_prompt
            
        invariants_text = "\n".join([f"- {k}: {v}" for k, v in self.intent_vector.items()])
        
        system_block = (
            "\n\n[CAUSALYN SYSTEM OVERRIDE]\n"
            "The following invariants define the absolute geometric boundaries of the system.\n"
            "You MUST conform to these constraints, or your state will be annihilated:\n"
            f"{invariants_text}\n"
            "[/CAUSALYN SYSTEM OVERRIDE]\n\n"
        )
        
        return system_block + original_prompt


class StagingViolation(BaseModel):
    code: str
    message: str
    severity: str  # "critical", "high", "medium"
    penalty: float


class StagingGatingResult(BaseModel):
    decision: GateDecision
    paradox_index: float
    violations: List[StagingViolation] = Field(default_factory=list)
    unified_diff: str = ""
    duration_ms: float = 0.0


class StagingInfrastructureGate:
    """Hypervisor evaluating staging infrastructure mutations."""

    def __init__(self) -> None:
        self.dangerous_volume_mounts = [
            "/",
            "/etc",
            "/var/run/docker.sock",
            "/proc",
            "/sys",
            "/root",
        ]

    def verify_manifest(
        self, candidate_yaml: str, baseline_yaml: Optional[str] = None
    ) -> StagingGatingResult:
        """Verify candidate container/K8s manifest against zero-trust staging policies."""
        start_t = time.perf_counter()
        violations: List[StagingViolation] = []

        # 1. YAML Syntax Check
        parsed_doc: Any = None
        try:
            parsed_doc = yaml.safe_load(candidate_yaml)
        except Exception as exc:
            violations.append(StagingViolation(
                code="INFRA-000-YAML-SYNTAX",
                message=f"Invalid manifest YAML syntax: {exc}",
                severity="critical",
                penalty=1.0,
            ))
            duration_ms = (time.perf_counter() - start_t) * 1000
            return StagingGatingResult(
                decision=GateDecision.DENY,
                paradox_index=1.0,
                violations=violations,
                duration_ms=duration_ms,
            )

        # 2. Text-level checks
        # Check privileged mode
        if re.search(r"\bprivileged:\s*true\b", candidate_yaml, re.IGNORECASE):
            violations.append(StagingViolation(
                code="INFRA-001-PRIVILEGED-CONTAINER",
                message="Disallowed privileged container mode requested (CAP_SYS_ADMIN hazard)",
                severity="critical",
                penalty=1.0,
            ))

        # Check host network
        if re.search(r"\b(hostNetwork|network_mode):\s*(true|['\"]?host['\"]?)\b", candidate_yaml, re.IGNORECASE):
            violations.append(StagingViolation(
                code="INFRA-004-HOST-NETWORKING",
                message="Host network namespace sharing requested",
                severity="high",
                penalty=0.8,
            ))

        # Check dangerous host mounts
        for mount in self.dangerous_volume_mounts:
            pat = rf"(:|\s|-)(['\"]?{re.escape(mount)}['\"]?)(\s|$|,|:)"
            if re.search(pat, candidate_yaml):
                violations.append(StagingViolation(
                    code="INFRA-002-HOST-MOUNT",
                    message=f"Forbidden host filesystem volume mount detected: '{mount}'",
                    severity="critical",
                    penalty=1.0,
                ))
                break

        # 3. Object-level structural checks if K8s Deployment or Container
        if isinstance(parsed_doc, dict):
            # Check resource limits
            containers = []
            if "spec" in parsed_doc and isinstance(parsed_doc["spec"], dict):
                template_spec = parsed_doc["spec"].get("template", {}).get("spec", {})
                containers = template_spec.get("containers", [])
            elif "services" in parsed_doc and isinstance(parsed_doc["services"], dict):
                containers = list(parsed_doc["services"].values())

            for c in containers:
                if isinstance(c, dict):
                    # Check missing resources/limits
                    if "resources" not in c and "deploy" not in c:
                        violations.append(StagingViolation(
                            code="INFRA-003-UNBOUNDED-RESOURCES",
                            message=f"Container '{c.get('name', 'service')}' missing CPU/Memory limits (DoS risk)",
                            severity="medium",
                            penalty=0.4,
                        ))

        # Compute diff if baseline provided
        diff_str = ""
        if baseline_yaml:
            base_lines = baseline_yaml.splitlines(keepends=True)
            cand_lines = candidate_yaml.splitlines(keepends=True)
            diff_str = "".join(difflib.unified_diff(base_lines, cand_lines, fromfile="baseline.yaml", tofile="candidate.yaml"))

        duration_ms = (time.perf_counter() - start_t) * 1000
        kappa = sum(v.penalty for v in violations)

        decision = GateDecision.ALLOW if kappa == 0.0 else GateDecision.DENY

        return StagingGatingResult(
            decision=decision,
            paradox_index=kappa,
            violations=violations,
            unified_diff=diff_str,
            duration_ms=duration_ms,
        )
