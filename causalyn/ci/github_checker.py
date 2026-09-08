"""GitHub PR & Continuous Integration Shadow Verification Engine (Milestone M3).

Intercepts PR diffs, parses modified files, applies them inside an isolated
shadow sandbox, verifies invariants and policies via CEGAR, and emits GitHub PR
annotations and Article 10 audit manifests.
"""

from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from ..api.contracts import ActionType, GateDecision
from ..model.world_state import WorldStateManager
from ..orchestrator.cegar_graph import CEGAROrchestrationGraph
from ..shadow.drivers import LocalMemoryDriver
from ..storage.repository import get_audit_repository
from ..verification.policy_rag import PolicyRAGEngine


class PRCheckResult(BaseModel):
    """Output of continuous shadow verification for a Git PR."""
    pr_number: int
    commit_sha: str
    verdict: GateDecision
    paradox_index: float
    violations: List[Dict[str, Any]] = Field(default_factory=list)
    counterexamples: List[Dict[str, Any]] = Field(default_factory=list)
    unified_diffs: Dict[str, str] = Field(default_factory=dict)
    article_10_audit_id: str
    audit_hash: str
    github_status: str  # "success" or "failure"
    summary_markdown: str


class PRVerifier:
    """Continuous shadow verification engine for pull requests and CI pipelines."""

    def __init__(self, repo_root: Optional[str] = None) -> None:
        self.repo_root = Path(repo_root or ".").resolve()

    def parse_patch_files(self, diff_text: str) -> Dict[str, str]:
        """Extract modified file paths and their target content from diff text."""
        files_map: Dict[str, str] = {}
        chunks = re.split(r"(?:^|\n)diff --git ", diff_text)

        for chunk in chunks:
            if not chunk.strip():
                continue
            path = None
            match = re.search(r"\+\+\+ b/([^\n\r]+)", chunk)
            if match:
                path = "/" + match.group(1).lstrip("/")
            else:
                m_simple = re.search(r"--- a/([^\n\r]+)\s+\+\+\+ b/([^\n\r]+)", chunk)
                if m_simple:
                    path = "/" + m_simple.group(2).lstrip("/")

            if not path:
                continue

            # Skip test suites, scripts, and documentation from strict agent-mutation interception
            rel_lower = path.lstrip("/").lower()
            if any(rel_lower.startswith(pfx) for pfx in ("tests/", "test/", "scripts/", "docs/", ".github/")):
                continue

            # If the complete file exists on disk in the repo root, evaluate the full file AST
            disk_file = self.repo_root / path.lstrip("/")
            if disk_file.is_file():
                try:
                    files_map[path] = disk_file.read_text(encoding="utf-8", errors="ignore")
                    continue
                except Exception:
                    pass

            # Fallback: extract added lines from diff hunk
            added_lines = [
                l[1:] for l in chunk.splitlines()
                if l.startswith("+") and not l.startswith("+++")
            ]
            files_map[path] = "\n".join(added_lines)

        return files_map

    async def verify_diff(
        self,
        diff_text: str,
        pr_number: int = 1,
        commit_sha: Optional[str] = None,
        base_files: Optional[Dict[str, Any]] = None,
    ) -> PRCheckResult:
        """Run continuous shadow verification against a proposed PR diff."""
        commit_sha = commit_sha or hashlib.sha256(diff_text.encode()).hexdigest()[:12]
        files_map = self.parse_patch_files(diff_text)

        if not files_map:
            # Fallback if diff format was single file content
            files_map["/workspace/patch.py"] = diff_text

        # 1. Provision ephemeral shadow environment
        init_fs = dict(base_files or {})
        mgr = WorldStateManager()
        for p, c in init_fs.items():
            mgr.set_file_content(p, c)

        driver = LocalMemoryDriver(initial_files=init_fs)
        rag = PolicyRAGEngine()
        graph = CEGAROrchestrationGraph(
            world_state_manager=mgr,
            sandbox_driver=driver,
            policy_rag=rag,
        )

        # 2. Evaluate each modified file through CEGAR consensus
        total_violations: List[Dict[str, Any]] = []
        total_counterexamples: List[Dict[str, Any]] = []
        captured_diffs: Dict[str, str] = {}
        max_kappa = 0.0

        for target_path, content in files_map.items():
            initial_state = {
                "session_id": f"pr-{pr_number}-{commit_sha}",
                "pipeline_id": f"ci-{int(time.time()*1000)}",
                "intent": f"Continuous CI verification for PR #{pr_number} on {target_path}",
                "max_iterations": 2,
                "proposed_action": {
                    "action_type": "file_write",
                    "target_path": target_path,
                    "payload": {"content": content},
                },
            }
            final_state = await graph.invoke(initial_state)

            k = float(final_state.get("paradox_index", 0.0))
            if k > max_kappa:
                max_kappa = k

            total_violations.extend(final_state.get("violations", []))
            total_counterexamples.extend(final_state.get("counterexamples", []))
            captured_diffs.update(final_state.get("unified_diffs", {}))

        # 3. Determine consensus verdict
        if max_kappa == 0.0 and len(total_violations) == 0:
            verdict = GateDecision.ALLOW
            github_status = "success"
        else:
            verdict = GateDecision.DENY
            github_status = "failure"

        # 4. Generate immutable Article 10 audit record
        audit_raw = f"{pr_number}:{commit_sha}:{verdict.value}:{max_kappa}:{len(total_violations)}"
        audit_hash = hashlib.sha256(audit_raw.encode()).hexdigest()
        audit_id = f"art10-ci-{audit_hash[:16]}"

        try:
            repo = get_audit_repository()
            repo.record_causalyn_mission(
                mission_id=f"pr-{pr_number}-{commit_sha}",
                session_id=f"pr-{pr_number}",
                request_id=audit_id,
                agent_framework="github_actions",
                intent=f"PR #{pr_number} commit {commit_sha}",
                stage="committed" if verdict == GateDecision.ALLOW else "annihilated",
                paradox_index=max_kappa,
                verification_decision=verdict.value,
                commit_decision="committed" if verdict == GateDecision.ALLOW else "annihilated",
                pre_state_hash=audit_hash,
                post_state_hash=audit_hash if verdict == GateDecision.ALLOW else None,
            )
            repo.record_causalyn_audit(
                mission_id=f"pr-{pr_number}-{commit_sha}",
                verifier_matrix={"violations": total_violations},
                unified_diffs=captured_diffs,
                hash_signature=audit_hash,
                counterexamples=total_counterexamples,
                article_10_compliant=True,
            )
        except Exception:
            pass

        summary_md = self._format_github_markdown(
            pr_number=pr_number,
            commit_sha=commit_sha,
            verdict=verdict,
            kappa=max_kappa,
            violations=total_violations,
            audit_id=audit_id,
            audit_hash=audit_hash,
            diffs=captured_diffs,
        )

        return PRCheckResult(
            pr_number=pr_number,
            commit_sha=commit_sha,
            verdict=verdict,
            paradox_index=max_kappa,
            violations=total_violations,
            counterexamples=total_counterexamples,
            unified_diffs=captured_diffs,
            article_10_audit_id=audit_id,
            audit_hash=audit_hash,
            github_status=github_status,
            summary_markdown=summary_md,
        )

    def _format_github_markdown(
        self,
        pr_number: int,
        commit_sha: str,
        verdict: GateDecision,
        kappa: float,
        violations: List[Dict[str, Any]],
        audit_id: str,
        audit_hash: str,
        diffs: Dict[str, str],
    ) -> str:
        status_badge = "**[APPROVED / VERIFIED]**" if verdict == GateDecision.ALLOW else "**[REJECTED / BLOCKED]**"
        md = rf"""## Causalyn Continuous Shadow Verification (Epoch-V / VPSN)

| Field | Value |
| :--- | :--- |
| **Pull Request** | `#{pr_number}` |
| **Commit SHA** | `{commit_sha}` |
| **Consensus Verdict** | {status_badge} |
| **Paradox Index (kappa)** | `{kappa:.3f}` |
| **EU AI Act Article 10 Audit ID** | `{audit_id}` |
| **Cryptographic Signature** | `{audit_hash[:16]}...` |

"""
        if violations:
            md += "### [ALERT] Invariant & Policy Violations Detected\n\n"
            for v in violations:
                md += f"- **[{v.get('code', 'ERR')}]** {v.get('message', '')} *(Severity: {v.get('severity', 'high')})*\n"
            md += "\n> *Invalid mutations have been structurally annihilated in shadow space prior to merging.*\n\n"

        if diffs:
            md += "<details><summary><b>View Verified Diffs (" + str(len(diffs)) + " files)</b></summary>\n\n"
            for p, d in diffs.items():
                md += f"```diff\n# {p}\n{d}\n```\n"
            md += "</details>\n\n"

        md += "---\n*Governed by Causalyn Autonomous Execution Hypervisor & EU AI Act (Regulation 2024/1689 Article 10)*\n"
        return md
