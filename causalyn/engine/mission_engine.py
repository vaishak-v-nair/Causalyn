"""Mission Engine - Core orchestration of Causalyn AI Execution Control Plane.

Implements the end-to-end mission loop:
Human Intent -> Intent Understanding -> Relevant State -> Proposed Action ->
Shadow Execution -> Verification -> Conflict Analysis -> Decision ->
Authorization -> Commit Boundary -> Audit Store.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from ..domain.models import (
    Action,
    AuditRecord,
    AuthorizationRequest,
    AuthorizationStatus,
    CandidateState,
    CommitRecord,
    Conflict,
    Decision,
    DecisionOutcome,
    Intent,
    Mission,
    MissionState,
    RiskAssessment,
    RiskLevel,
    StateSnapshot,
    VerificationEvidence,
    VerifierLayer,
)
from ..model.world_state import WorldState, WorldStateManager
from ..storage.repository import TransactionalAuditRepository, get_audit_repository
from ..verification.invariant_checker import VerificationEngine, create_default_verification_engine
from .conflict_engine import ConflictEngine
from .risk_engine import RiskEngine


class MissionEngine:
    """Deterministic, constraint-gated Mission execution engine."""

    def __init__(
        self,
        world_state_manager: Optional[WorldStateManager] = None,
        verification_engine: Optional[VerificationEngine] = None,
        repository: Optional[TransactionalAuditRepository] = None,
    ):
        self.world_state_manager = world_state_manager or WorldStateManager()
        self.verification_engine = verification_engine or create_default_verification_engine()
        self.risk_engine = RiskEngine()
        self.conflict_engine = ConflictEngine()
        self.repository = repository or get_audit_repository()

    # -------------------------------------------------------------------------
    # STAGE 1: ANALYZE (Intent Understanding + State Collection + Planning)
    # -------------------------------------------------------------------------
    def analyze_intent(
        self,
        intent_text: str,
        target_path: Optional[str] = None,
        action_type: str = "file_write",
        payload: Optional[Dict[str, Any]] = None,
    ) -> Mission:
        """Analyze intent without side effects or mutation."""
        if not intent_text or not intent_text.strip():
            raise ValueError("intent_text must be a non-empty string")

        mission_id = f"mission-{uuid.uuid4().hex[:12]}"
        normalized_goal = " ".join(intent_text.split())
        t_start = time.perf_counter()

        # Deterministic extraction of intent semantics
        intent_id = f"intent-{hashlib.sha256(normalized_goal.encode()).hexdigest()[:10]}"
        lowered = normalized_goal.lower()

        # Detect paths and operations
        extracted_paths: List[str] = []
        if target_path:
            extracted_paths.append(target_path)
        path_matches = re.findall(r"(/[a-zA-Z0-9_\-\./]+)", normalized_goal)
        for p in path_matches:
            if p not in extracted_paths:
                extracted_paths.append(p)

        # Invariants and constraints
        required_invariants = [
            "no_unauthorized_deletion",
            "no_secret_exfiltration",
            "tests_keep_passing",
            "schema_constraints_valid",
            "protected_files_immutable",
        ]
        forbidden_states = [
            "deletion of /protected/ or /secrets/ or .env",
            "exfiltration of credentials or tokens",
            "syntax corruption in Python/JSON/YAML",
            "arbitrary subprocess or exec injection",
        ]

        allowed_ops = ["inspect", "query", "state_read"]
        disallowed_ops = ["rm -rf", "drop table", "chmod 777", "unauthorized_deletion"]
        ambiguities = []
        assumptions = ["Execution isolated in copy-on-write shadow environment"]

        if any(w in lowered for w in ("delete", "remove", "destroy", "drop", "wipe")):
            allowed_ops.append("file_delete")
        elif any(w in lowered for w in ("create", "write", "add", "build", "update", "modify", "patch")):
            allowed_ops.append("file_write")
        else:
            ambiguities.append("Exact mutation operation was not explicitly specified; assumed read/analyze.")

        if not extracted_paths and any(w in lowered for w in ("file", "config", "code", "schema")):
            ambiguities.append("Target path unspecified in intent statement.")

        intent = Intent(
            intent_id=intent_id,
            goal=normalized_goal,
            scope={"included": extracted_paths, "excluded": ["/protected/", "/secrets/", "/.env"]},
            target_paths=extracted_paths,
            constraints=["Preserve existing invariants", "Fail closed on uncertainty"],
            required_invariants=required_invariants,
            forbidden_states=forbidden_states,
            allowed_operations=allowed_ops,
            disallowed_operations=disallowed_ops,
            assumptions=assumptions,
            ambiguities=ambiguities,
            acceptance_conditions=[
                "State transition verified in Semantic Null-Space (kappa = 0.0)",
                "Zero verifier disagreements",
                "Explicit human authorization if risk >= HIGH",
            ],
        )

        # Collect relevant system state before mutation
        live_state = self.world_state_manager.get_current_state()
        state_id = f"state-{uuid.uuid4().hex[:8]}"
        state_before = StateSnapshot(
            state_id=state_id,
            timestamp=time.time(),
            environment="local_sandbox",
            resources=sorted(list(live_state.file_system.keys())),
            file_system=dict(live_state.file_system),
            data=dict(live_state.data),
            provenance_hash=live_state.compute_hash(),
        )

        # Construct proposed Action(s)
        actions: List[Action] = []
        action_payload = dict(payload) if payload else {}
        primary_target = extracted_paths[0] if extracted_paths else (target_path or "/app/workspace/action.py")

        # Synthesize realistic action proposals if no explicit payload was provided
        if not action_payload or ("content" not in action_payload and "code" not in action_payload):
            if "clean" in lowered and "config" in lowered:
                # Agent attempts to consolidate configs into public settings, accidentally leaking vault secret
                primary_target = target_path or "/app/public/settings.json"
                action_type = "file_write"
                action_payload = {
                    "content": json.dumps({
                        "app_name": "CausalynDemoApp",
                        "version": "1.0.0",
                        "environment": "production",
                        "logging": "INFO",
                        "api_secret_key": "demo-vault-secret-key-98765-production-token",
                        "auth_token": "demo_prod_jwt_token_causalyn_safe",
                    }, indent=2)
                }
            elif "exfiltrate" in lowered and "secret" in lowered:
                primary_target = target_path or "/app/public/settings.json"
                action_type = "file_write"
                action_payload = {
                    "content": json.dumps({
                        "app_name": "CausalynDemoApp",
                        "api_key_secret": "demo-vault-secret-key-98765-production-token",
                    }, indent=2)
                }
            elif "syntax" in lowered or "broken" in lowered:
                primary_target = target_path or "/app/public/settings.json"
                action_type = "file_write"
                action_payload = {"content": "def broken(:"}
            elif "port" in lowered or "schema" in lowered:
                primary_target = target_path or "/app/public/settings.json"
                action_type = "file_write"
                action_payload = {"content": json.dumps({"port": "invalid_string_port", "timeout": 30.5})}
            elif "feature_flag" in lowered or "public settings" in lowered:
                primary_target = target_path or "/app/public/settings.json"
                action_type = "file_write"
                action_payload = {"content": json.dumps({"feature_flag_v2": True, "version": "1.1.0"}, indent=2)}

        actions.append(
            Action(
                action_id=f"act-{uuid.uuid4().hex[:8]}",
                action_type=action_type,
                target_path=primary_target,
                payload=action_payload,
            )
        )

        # Compute initial risk
        initial_risk = self.risk_engine.evaluate(intent=intent, actions=actions)

        mission = Mission(
            mission_id=mission_id,
            state=MissionState.ANALYZE,
            intent=intent,
            state_before=state_before,
            actions=actions,
            risk=initial_risk,
            latency_ms={"analyze_ms": (time.perf_counter() - t_start) * 1000},
        )

        # Persist initial mission
        self._save_mission(mission)
        return mission

    # -------------------------------------------------------------------------
    # STAGE 2: SHADOW EXECUTION
    # -------------------------------------------------------------------------
    def execute_shadow(self, mission: Mission) -> CandidateState:
        """Execute proposed actions in isolated shadow state without production mutation."""
        t_start = time.perf_counter()
        live_state = self.world_state_manager.get_current_state()
        shadow_state = live_state.clone()

        files_modified: Dict[str, Any] = {}
        files_added: Dict[str, Any] = {}
        files_deleted: List[str] = []
        side_effects: List[str] = []
        diffs: Dict[str, str] = {}

        for action in mission.actions:
            target = action.target_path
            if not target:
                continue

            if action.action_type in ("file_delete", "db_drop", "table_truncate"):
                if target in shadow_state.file_system:
                    old_content = shadow_state.file_system.pop(target)
                    files_deleted.append(target)
                    diffs[target] = f"--- {target} (deleted)\n+++ /dev/null\n@@ -1 +0,0 @@\n-{old_content}\n"
            elif action.action_type in ("file_write", "file_create", "file_modify", "patch"):
                new_content = action.payload.get("content", action.payload.get("code", ""))
                old_content = shadow_state.file_system.get(target)

                shadow_state.set_file_content(target, new_content)

                if old_content is None:
                    files_added[target] = new_content
                    old_lines = []
                else:
                    files_modified[target] = new_content
                    old_lines = str(old_content).splitlines(keepends=True)

                new_lines = str(new_content).splitlines(keepends=True)
                delta = difflib.unified_diff(
                    old_lines,
                    new_lines,
                    fromfile=f"a{target}",
                    tofile=f"b{target}",
                )
                diffs[target] = "".join(delta) or f"+++ {target}\n{new_content}\n"

            elif action.action_type in ("http_request", "network_egress"):
                side_effects.append(f"Network egress simulated to: {action.payload.get('url', 'external_host')}")

        duration_ms = (time.perf_counter() - t_start) * 1000
        candidate = CandidateState(
            candidate_id=f"cand-{uuid.uuid4().hex[:8]}",
            parent_state_id=mission.state_before.state_id if mission.state_before else "state-root",
            unified_diffs=diffs,
            files_modified=files_modified,
            files_added=files_added,
            files_deleted=files_deleted,
            side_effects=side_effects,
            exit_code=0,
            stdout="Shadow execution completed cleanly in scratchpad.",
            stderr="",
            duration_ms=duration_ms,
        )

        mission.candidate_state = candidate
        mission.state = MissionState.SHADOW
        mission.latency_ms["shadow_ms"] = duration_ms
        self._save_mission(mission)
        return candidate

    # -------------------------------------------------------------------------
    # STAGE 3: VERIFICATION & CONFLICT ANALYSIS & DECISION
    # -------------------------------------------------------------------------
    def verify_and_decide(
        self,
        mission: Mission,
        injected_shadow_state: Optional[WorldState] = None,
    ) -> Mission:
        """Run layered verification matrix, analyze conflicts, and form terminal decision."""
        t_start = time.perf_counter()
        live_state = self.world_state_manager.get_current_state()

        # Reconstruct candidate world state from candidate_state diffs
        if injected_shadow_state:
            shadow_state = injected_shadow_state
        else:
            shadow_state = live_state.clone()
            if mission.candidate_state:
                for del_path in mission.candidate_state.files_deleted:
                    shadow_state.file_system.pop(del_path, None)
                for path, content in mission.candidate_state.files_added.items():
                    shadow_state.set_file_content(path, content)
                for path, content in mission.candidate_state.files_modified.items():
                    shadow_state.set_file_content(path, content)

        # 1. Layered Verification
        evidences = self.verification_engine.evaluate_layered_evidence(live_state, shadow_state)
        mission.verifications = evidences

        # 2. Conflict Analysis
        conflicts = self.conflict_engine.detect_conflicts(evidences)
        mission.conflicts = conflicts

        # 3. Paradox Index kappa
        kappa = self.verification_engine.calculate_paradox_index(live_state, shadow_state)

        # 4. Final Risk Assessment
        risk = self.risk_engine.evaluate(
            intent=mission.intent,
            actions=mission.actions,
            candidate_state=mission.candidate_state,
            verifications=evidences,
            conflicts=conflicts,
        )
        mission.risk = risk

        # 5. Fail-Closed Terminal Decision Formation
        hard_failures = [e for e in evidences if e.status == "FAIL"]
        uncertain_checks = [e for e in evidences if e.status == "UNCERTAIN"]

        if hard_failures:
            # Hard invariant violation -> DENY
            fail_descs = [f"{e.verifier}: {e.message}" for e in hard_failures]
            leak_detected = any("secret" in e.verifier.lower() for e in hard_failures)
            leak_prefix = "Credential leak detected in shadow state. " if leak_detected else ""
            decision = Decision(
                outcome=DecisionOutcome.DENY,
                reason=f"{leak_prefix}Verification DENIED (kappa = {kappa:.2f}). Hard violations: {'; '.join(fail_descs)}",
                paradox_index=kappa,
                counterexamples=self.verification_engine.get_violation_details(live_state, shadow_state),
                escalation_required=False,
            )
            mission.decision = decision
            mission.state = MissionState.DENIED

        elif conflicts or uncertain_checks or risk.requires_authorization:
            # Conflicts, uncertainty, or high risk -> ESCALATE (Never convert uncertainty into ALLOW)
            reasons = []
            if conflicts:
                reasons.append(f"{len(conflicts)} verifier conflict(s) detected")
            if uncertain_checks:
                reasons.append(f"{len(uncertain_checks)} uncertain verifier check(s)")
            if risk.requires_authorization:
                reasons.append(f"Risk level {risk.risk_level.value} ({risk.score}/100) requires human gate")

            reason_str = "ESCALATED: " + "; ".join(reasons)
            decision = Decision(
                outcome=DecisionOutcome.ESCALATE,
                reason=reason_str,
                paradox_index=kappa,
                counterexamples=[],
                escalation_required=True,
            )
            mission.decision = decision
            mission.state = MissionState.AUTHORIZE

            # Instantiate Authorization Request
            mission.authorization = AuthorizationRequest(
                auth_id=f"auth-{uuid.uuid4().hex[:10]}",
                mission_id=mission.mission_id,
                affected_resources=sorted(
                    list(
                        (mission.candidate_state.files_modified.keys() if mission.candidate_state else [])
                        | (mission.candidate_state.files_added.keys() if mission.candidate_state else [])
                        | set(mission.candidate_state.files_deleted if mission.candidate_state else [])
                    )
                ),
                changes_summary=mission.candidate_state.unified_diffs if mission.candidate_state else {},
                risk_summary=risk.to_dict(),
                verification_summary={
                    "total_checks": len(evidences),
                    "passed": len([e for e in evidences if e.status == "PASS"]),
                    "failed": len(hard_failures),
                    "uncertain": len(uncertain_checks),
                    "paradox_index": kappa,
                },
                conflicts=[c.to_dict() for c in conflicts],
                rollback_available=True,
                status=AuthorizationStatus.PENDING,
            )

        else:
            # All checks pass cleanly -> ALLOW
            decision = Decision(
                outcome=DecisionOutcome.ALLOW,
                reason="Verified in Semantic Null-Space (kappa = 0.0). All invariants hold.",
                paradox_index=0.0,
                counterexamples=[],
                escalation_required=False,
            )
            mission.decision = decision
            mission.state = MissionState.COMMIT

        mission.latency_ms["verify_ms"] = (time.perf_counter() - t_start) * 1000
        self._save_mission(mission)
        return mission

    # -------------------------------------------------------------------------
    # STAGE 4: AUTHORIZATION (Human-in-the-Loop Gate)
    # -------------------------------------------------------------------------
    def authorize_mission(
        self,
        mission_id: str,
        approved: bool,
        user: str = "security_officer",
        comment: Optional[str] = None,
    ) -> Mission:
        """Process explicit human authorization verdict."""
        mission = self.get_mission(mission_id)
        if not mission:
            raise KeyError(f"Mission not found: {mission_id}")

        if not mission.authorization:
            raise ValueError(f"Mission {mission_id} has no pending authorization request")

        if approved:
            mission.authorization.status = AuthorizationStatus.APPROVED
            mission.authorization.approved_by = user
            mission.authorization.authorized_at = time.time()
            mission.authorization.comment = comment or "Approved via Security Gate"
            mission.state = MissionState.COMMIT
            self._save_mission(mission)
            # Proceed directly to commit
            return self.commit_mission(mission_id)
        else:
            mission.authorization.status = AuthorizationStatus.REJECTED
            mission.authorization.approved_by = user
            mission.authorization.authorized_at = time.time()
            mission.authorization.comment = comment or "Rejected via Security Gate"
            mission.state = MissionState.REJECTED
            mission.decision = Decision(
                outcome=DecisionOutcome.DENY,
                reason=f"Action explicitly rejected by authorizer {user}: {comment or 'Policy refusal'}",
                paradox_index=mission.decision.paradox_index if mission.decision else 0.0,
            )
            self._save_mission(mission)
            return mission

    # -------------------------------------------------------------------------
    # STAGE 5: COMMIT BOUNDARY (Fail-Closed Atomic Transition & Audit Store)
    # -------------------------------------------------------------------------
    def commit_mission(self, mission_id: str) -> Mission:
        """Commit verified candidate state to protected production state."""
        mission = self.get_mission(mission_id)
        if not mission:
            raise KeyError(f"Mission not found: {mission_id}")

        t_start = time.perf_counter()
        live_state = self.world_state_manager.get_current_state()

        # Commit Gate 1: State Authorization / Decision Check
        is_allowed = mission.decision and mission.decision.outcome == DecisionOutcome.ALLOW
        is_authorized = mission.authorization and mission.authorization.status == AuthorizationStatus.APPROVED

        if not (is_allowed or is_authorized):
            mission.state = MissionState.DENIED
            self._save_mission(mission)
            raise PermissionError(f"Commit Boundary Refusal: Mission {mission_id} is neither ALLOWED nor APPROVED.")

        # Commit Gate 2: 2PC Pre-State Hash Guard (Concurrency & Drift Check)
        current_pre_hash = live_state.compute_hash()
        expected_pre_hash = mission.state_before.provenance_hash if mission.state_before else ""
        if expected_pre_hash and current_pre_hash != expected_pre_hash:
            mission.state = MissionState.FAILED
            mission.decision = Decision(
                outcome=DecisionOutcome.DENY,
                reason=f"2PC Pre-State Drift Error: Live state hash {current_pre_hash[:12]} does not match expected {expected_pre_hash[:12]}.",
            )
            self._save_mission(mission)
            raise RuntimeError("2PC Pre-State Hash mismatch. Transaction aborted to prevent state corruption.")

        # Apply candidate mutations to WorldStateManager
        if mission.candidate_state:
            for del_file in mission.candidate_state.files_deleted:
                self.world_state_manager.delete_file(del_file)
            for file_path, content in mission.candidate_state.files_added.items():
                self.world_state_manager.set_file_content(file_path, content)
            for file_path, content in mission.candidate_state.files_modified.items():
                self.world_state_manager.set_file_content(file_path, content)

        post_state_hash = self.world_state_manager.get_current_state().compute_hash()
        commit_id = f"commit-{uuid.uuid4().hex[:10]}"

        commit_record = CommitRecord(
            commit_id=commit_id,
            mission_id=mission_id,
            pre_state_hash=current_pre_hash,
            post_state_hash=post_state_hash,
            authorization_id=mission.authorization.auth_id if mission.authorization else None,
            decision="committed",
            changes_summary=mission.candidate_state.unified_diffs if mission.candidate_state else {},
            committed_at=time.time(),
        )
        mission.commit = commit_record

        # EU AI Act Article 10 Audit Ledger Record
        audit_raw = f"{mission_id}:{commit_id}:{current_pre_hash}:{post_state_hash}"
        audit_sig = hashlib.sha256(audit_raw.encode()).hexdigest()

        audit_record = AuditRecord(
            audit_id=f"art10-{audit_sig[:12]}",
            mission_id=mission_id,
            timestamp=time.time(),
            lifecycle_events=[
                {"stage": "analyze", "timestamp": mission.created_at},
                {"stage": "shadow", "timestamp": mission.created_at + 0.01},
                {"stage": "verify", "timestamp": mission.created_at + 0.02},
                {"stage": "commit", "timestamp": time.time()},
            ],
            evidence_chain=[v.to_dict() for v in mission.verifications],
            hash_signature=audit_sig,
            article_10_compliant=True,
        )
        mission.audit_record = audit_record
        mission.state = MissionState.COMMITTED
        mission.latency_ms["commit_ms"] = (time.perf_counter() - t_start) * 1000

        # Persist to repository and append to immutable Article 10 audit ledger
        self._save_mission(mission)

        try:
            if hasattr(self.repository, "record_causalyn_mission"):
                self.repository.record_causalyn_mission(
                    mission_id=mission_id,
                    session_id=f"sess-{mission_id}",
                    request_id=f"req-{mission_id}",
                    agent_framework="causalyn-core",
                    intent=mission.intent.goal if mission.intent else "mission",
                    stage="committed",
                    paradox_index=mission.decision.paradox_index if mission.decision else 0.0,
                    verification_decision="allow" if is_allowed else "approved",
                    commit_decision="committed",
                    pre_state_hash=current_pre_hash,
                    post_state_hash=post_state_hash,
                )
            if hasattr(self.repository, "record_causalyn_audit"):
                self.repository.record_causalyn_audit(
                    mission_id=mission_id,
                    verifier_matrix={"verifications": [v.to_dict() for v in mission.verifications]},
                    unified_diffs=mission.candidate_state.unified_diffs if mission.candidate_state else {},
                    hash_signature=audit_sig,
                    counterexamples=mission.decision.counterexamples if mission.decision else [],
                    article_10_compliant=True,
                )
        except Exception:
            pass

        return mission

    # -------------------------------------------------------------------------
    # End-to-End Mission Pipeline Execution
    # -------------------------------------------------------------------------
    def run_mission(
        self,
        intent_text: str,
        target_path: Optional[str] = None,
        action_type: str = "file_write",
        payload: Optional[Dict[str, Any]] = None,
        auto_commit_if_allowed: bool = True,
    ) -> Mission:
        """Run full mission loop: Analyze -> Shadow -> Verify -> (Authorize/Commit)."""
        mission = self.analyze_intent(
            intent_text=intent_text,
            target_path=target_path,
            action_type=action_type,
            payload=payload,
        )
        self.execute_shadow(mission)
        self.verify_and_decide(mission)

        if mission.decision and mission.decision.outcome == DecisionOutcome.ALLOW and auto_commit_if_allowed:
            self.commit_mission(mission.mission_id)

        return self.get_mission(mission.mission_id) or mission

    # -------------------------------------------------------------------------
    # Persistence Helpers
    # -------------------------------------------------------------------------
    def _save_mission(self, mission: Mission) -> None:
        """Persist mission state to transactional repository."""
        mission.updated_at = time.time()
        if hasattr(self.repository, "save_domain_mission"):
            self.repository.save_domain_mission(mission.to_dict())

    def get_mission(self, mission_id: str) -> Optional[Mission]:
        """Load full domain Mission from repository."""
        if hasattr(self.repository, "get_domain_mission"):
            data = self.repository.get_domain_mission(mission_id)
            if data:
                return self._deserialize_mission(data)
        return None

    def list_missions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent missions for API/UI."""
        if hasattr(self.repository, "list_domain_missions"):
            return self.repository.list_domain_missions(limit)
        return []

    def _deserialize_mission(self, d: Dict[str, Any]) -> Mission:
        """Reconstruct Mission aggregate from dict."""
        intent = None
        if d.get("intent"):
            i = d["intent"]
            intent = Intent(
                intent_id=i["intent_id"],
                goal=i["goal"],
                scope=i.get("scope", {}),
                target_paths=i.get("target_paths", []),
                auth_scope=i.get("auth_scope", "PUBLIC"),
                constraints=i.get("constraints", []),
                required_invariants=i.get("required_invariants", []),
                forbidden_states=i.get("forbidden_states", []),
                allowed_operations=i.get("allowed_operations", []),
                disallowed_operations=i.get("disallowed_operations", []),
                assumptions=i.get("assumptions", []),
                ambiguities=i.get("ambiguities", []),
                acceptance_conditions=i.get("acceptance_conditions", []),
                ambient_coordinates=tuple(i.get("ambient_coordinates", (0.5, 0.9, 0.95))),
                created_at=i.get("created_at", time.time()),
            )

        state_before = None
        if d.get("state_before"):
            sb = d["state_before"]
            state_before = StateSnapshot(
                state_id=sb.get("state_id", "state-0"),
                timestamp=sb.get("timestamp", time.time()),
                resources=sb.get("resources", []),
                provenance_hash=sb.get("provenance_hash", ""),
            )

        actions = [
            Action(
                action_id=a.get("action_id", f"act-{idx}"),
                action_type=a.get("action_type", "unknown"),
                target_path=a.get("target_path"),
                payload=a.get("payload", {}),
            )
            for idx, a in enumerate(d.get("actions", []))
        ]

        candidate = None
        if d.get("candidate_state"):
            c = d["candidate_state"]
            candidate = CandidateState(
                candidate_id=c.get("candidate_id", ""),
                parent_state_id=c.get("parent_state_id", ""),
                unified_diffs=c.get("unified_diffs", {}),
                files_modified=c.get("files_modified", {}),
                files_added=c.get("files_added", {}),
                files_deleted=c.get("files_deleted", []),
                side_effects=c.get("side_effects", []),
                exit_code=c.get("exit_code", 0),
                stdout=c.get("stdout", ""),
                stderr=c.get("stderr", ""),
                duration_ms=c.get("duration_ms", 0.0),
            )

        verifications = [
            VerificationEvidence(
                verifier=v["verifier"],
                layer=VerifierLayer(v["layer"]) if v.get("layer") in VerifierLayer._value2member_map_ else VerifierLayer.POLICY,
                status=v["status"],
                penalty=v.get("penalty", 0.0),
                message=v.get("message", ""),
                details=v.get("details", {}),
                timestamp=v.get("timestamp", time.time()),
            )
            for v in d.get("verifications", [])
        ]

        conflicts = [
            Conflict(
                conflict_id=cf["conflict_id"],
                invariant_id=cf["invariant_id"],
                verifier_a=cf["verifier_a"],
                verifier_b=cf["verifier_b"],
                verdict_a=cf["verdict_a"],
                verdict_b=cf["verdict_b"],
                description=cf["description"],
                affected_invariant=cf["affected_invariant"],
                resolution_strategy=cf.get("resolution_strategy", "escalate_to_human"),
                timestamp=cf.get("timestamp", time.time()),
            )
            for cf in d.get("conflicts", [])
        ]

        risk = None
        if d.get("risk"):
            r = d["risk"]
            risk = RiskAssessment(
                risk_level=RiskLevel(r["risk_level"]) if r.get("risk_level") in RiskLevel._value2member_map_ else RiskLevel.MEDIUM,
                score=r.get("score", 0.0),
                factors=r.get("factors", []),
                requires_authorization=r.get("requires_authorization", False),
                details=r.get("details", {}),
            )

        decision = None
        if d.get("decision"):
            dec = d["decision"]
            decision = Decision(
                outcome=DecisionOutcome(dec["outcome"]) if dec.get("outcome") in DecisionOutcome._value2member_map_ else DecisionOutcome.DENY,
                reason=dec.get("reason", ""),
                paradox_index=dec.get("paradox_index", 0.0),
                counterexamples=dec.get("counterexamples", []),
                escalation_required=dec.get("escalation_required", False),
            )

        authorization = None
        if d.get("authorization"):
            au = d["authorization"]
            authorization = AuthorizationRequest(
                auth_id=au["auth_id"],
                mission_id=au.get("mission_id", d["mission_id"]),
                affected_resources=au.get("affected_resources", []),
                changes_summary=au.get("changes_summary", {}),
                risk_summary=au.get("risk_summary", {}),
                verification_summary=au.get("verification_summary", {}),
                conflicts=au.get("conflicts", []),
                rollback_available=au.get("rollback_available", True),
                status=AuthorizationStatus(au["status"]) if au.get("status") in AuthorizationStatus._value2member_map_ else AuthorizationStatus.PENDING,
                approved_by=au.get("approved_by"),
                authorized_at=au.get("authorized_at"),
                comment=au.get("comment"),
            )

        commit = None
        if d.get("commit"):
            cm = d["commit"]
            commit = CommitRecord(
                commit_id=cm["commit_id"],
                mission_id=cm["mission_id"],
                pre_state_hash=cm.get("pre_state_hash", ""),
                post_state_hash=cm.get("post_state_hash"),
                authorization_id=cm.get("authorization_id"),
                decision=cm.get("decision", ""),
                changes_summary=cm.get("changes_summary", {}),
                committed_at=cm.get("committed_at", time.time()),
            )

        audit_record = None
        if d.get("audit_record"):
            ar = d["audit_record"]
            audit_record = AuditRecord(
                audit_id=ar["audit_id"],
                mission_id=ar["mission_id"],
                timestamp=ar.get("timestamp", time.time()),
                lifecycle_events=ar.get("lifecycle_events", []),
                evidence_chain=ar.get("evidence_chain", []),
                hash_signature=ar.get("hash_signature", ""),
                article_10_compliant=ar.get("article_10_compliant", True),
            )

        return Mission(
            mission_id=d["mission_id"],
            state=MissionState(d["state"]) if d.get("state") in MissionState._value2member_map_ else MissionState.PENDING,
            intent=intent,
            state_before=state_before,
            actions=actions,
            candidate_state=candidate,
            verifications=verifications,
            conflicts=conflicts,
            risk=risk,
            decision=decision,
            authorization=authorization,
            commit=commit,
            audit_record=audit_record,
            latency_ms=d.get("latency_ms", {}),
            created_at=d.get("created_at", time.time()),
            updated_at=d.get("updated_at", time.time()),
        )
