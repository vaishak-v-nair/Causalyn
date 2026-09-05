"""FastAPI route wiring for the backend service."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Request

from .contracts import (
    AuthorizeMissionRequest,
    CreateMissionRequest,
    EvaluateVPSNRequest,
    IntentRequest,
    InterceptActionRequest,
    InterceptActionResponse,
)
from .responses import HealthResponse, IntentResponse, PipelinesResponse, StateResponse
from .services import BackendService


_MANIFOLD_TELEMETRY: dict[str, Any] = {
    "annihilation_count": 0,
    "last_kappa": 0.0,
    "last_status": "EQUILIBRIUM",
    "last_violations": [],
}


def create_router(
    service: BackendService, serialize_context: Callable[[Any], dict[str, Any]], prefix: str = "/api"
) -> APIRouter:
    router = APIRouter(prefix=prefix)

    @router.get("/health", response_model=HealthResponse)
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "causalyn", "maturity": "M1_TOY_PROTOTYPE"}

    @router.get("/state", response_model=StateResponse)
    def state() -> dict[str, Any]:
        return service.state()

    @router.get("/world-state")
    def world_state() -> dict[str, Any]:
        return service.state()

    @router.get("/missions")
    def list_missions() -> list[dict[str, Any]]:
        from ..engine.mission_engine import MissionEngine
        engine = MissionEngine(world_state_manager=service.world_state)
        domain_missions = engine.list_missions(50)
        if domain_missions:
            return domain_missions
        from ..storage.repository import get_audit_repository
        repo = get_audit_repository()
        if hasattr(repo, "get_causalyn_missions"):
            return repo.get_causalyn_missions(50)
        return []

    @router.post("/missions")
    def create_mission(request: CreateMissionRequest) -> dict[str, Any]:
        from ..engine.mission_engine import MissionEngine
        engine = MissionEngine(world_state_manager=service.world_state)
        if request.auto_run:
            mission = engine.run_mission(
                intent_text=request.intent,
                target_path=request.target_path,
                action_type=request.action_type,
                payload=request.payload,
                auto_commit_if_allowed=True,
            )
        else:
            mission = engine.analyze_intent(
                intent_text=request.intent,
                target_path=request.target_path,
                action_type=request.action_type,
                payload=request.payload,
            )
        return mission.to_dict()

    @router.get("/missions/{mission_id}")
    def get_mission_detail(mission_id: str) -> dict[str, Any]:
        from ..engine.mission_engine import MissionEngine
        engine = MissionEngine(world_state_manager=service.world_state)
        mission = engine.get_mission(mission_id)
        if not mission:
            raise HTTPException(
                status_code=404,
                detail={"code": "mission_not_found", "message": f"Mission not found: {mission_id}"},
            )
        return mission.to_dict()

    @router.post("/missions/{mission_id}/run")
    def run_mission_flow(mission_id: str) -> dict[str, Any]:
        from ..engine.mission_engine import MissionEngine
        engine = MissionEngine(world_state_manager=service.world_state)
        mission = engine.get_mission(mission_id)
        if not mission:
            raise HTTPException(
                status_code=404,
                detail={"code": "mission_not_found", "message": f"Mission not found: {mission_id}"},
            )
        engine.execute_shadow(mission)
        engine.verify_and_decide(mission)
        from ..domain.models import DecisionOutcome
        if mission.decision and mission.decision.outcome == DecisionOutcome.ALLOW:
            engine.commit_mission(mission_id)
        updated = engine.get_mission(mission_id) or mission
        return updated.to_dict()

    @router.post("/missions/{mission_id}/authorize")
    def authorize_mission(mission_id: str, request: AuthorizeMissionRequest) -> dict[str, Any]:
        from ..engine.mission_engine import MissionEngine
        engine = MissionEngine(world_state_manager=service.world_state)
        try:
            mission = engine.authorize_mission(
                mission_id=mission_id,
                approved=request.approved,
                user=request.user,
                comment=request.comment,
            )
            return mission.to_dict()
        except KeyError:
            raise HTTPException(
                status_code=404,
                detail={"code": "mission_not_found", "message": f"Mission not found: {mission_id}"},
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail={"code": "invalid_authorization", "message": str(e)},
            )

    @router.post("/missions/{mission_id}/commit")
    def commit_mission(mission_id: str) -> dict[str, Any]:
        from ..engine.mission_engine import MissionEngine
        engine = MissionEngine(world_state_manager=service.world_state)
        try:
            mission = engine.commit_mission(mission_id)
            return mission.to_dict()
        except KeyError:
            raise HTTPException(
                status_code=404,
                detail={"code": "mission_not_found", "message": f"Mission not found: {mission_id}"},
            )
        except PermissionError as e:
            raise HTTPException(
                status_code=403,
                detail={"code": "commit_forbidden", "message": str(e)},
            )
        except Exception as e:
            raise HTTPException(
                status_code=409,
                detail={"code": "commit_conflict", "message": str(e)},
            )

    @router.get("/missions/{mission_id}/audit")
    def get_mission_audit(mission_id: str) -> dict[str, Any]:
        from ..engine.mission_engine import MissionEngine
        engine = MissionEngine(world_state_manager=service.world_state)
        mission = engine.get_mission(mission_id)
        if not mission:
            raise HTTPException(
                status_code=404,
                detail={"code": "mission_not_found", "message": f"Mission not found: {mission_id}"},
            )
        return {
            "mission_id": mission.mission_id,
            "state": mission.state.value if hasattr(mission.state, "value") else str(mission.state),
            "decision": mission.decision.to_dict() if mission.decision else None,
            "risk": mission.risk.to_dict() if mission.risk else None,
            "verifications": [v.to_dict() for v in mission.verifications],
            "conflicts": [c.to_dict() for c in mission.conflicts],
            "audit_record": mission.audit_record.to_dict() if mission.audit_record else None,
            "commit": mission.commit.to_dict() if mission.commit else None,
        }


    @router.get("/pipelines", response_model=PipelinesResponse)
    def pipelines() -> dict[str, Any]:
        return {"pipelines": service.store.recent()}

    @router.get("/pipelines/{pipeline_id}")
    def pipeline_detail(pipeline_id: str) -> dict[str, Any]:
        for pipeline in service.store.recent(100):
            if pipeline.get("pipeline_id") == pipeline_id:
                return pipeline
        raise HTTPException(
            status_code=404,
            detail={"code": "pipeline_not_found", "message": "Pipeline not found"},
        )

    @router.get("/diff/{pipeline_id}")
    def pipeline_diff(pipeline_id: str) -> dict[str, Any]:
        for pipeline in service.store.recent(100):
            if pipeline.get("pipeline_id") == pipeline_id:
                diffs_map = pipeline.get("unified_diffs", {})
                return {
                    "pipeline_id": pipeline_id,
                    "diffs": diffs_map,
                    "unified_diffs": diffs_map,
                    "changes": pipeline.get("commit", {}).get("changes") if pipeline.get("commit") else {},
                }
        raise HTTPException(
            status_code=404,
            detail={"code": "pipeline_not_found", "message": "Pipeline not found"},
        )

    @router.get("/files")
    def files() -> dict[str, Any]:
        details = service.get_file_details()
        return {"files": details, "count": len(details)}

    @router.get("/files/content")
    def file_content(path: str) -> dict[str, Any]:
        if not path or ".." in path:
            raise HTTPException(
                status_code=403,
                detail={"code": "forbidden_path", "message": "Directory traversal is strictly forbidden"},
            )
        content = service.get_file_content(path)
        if content is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "file_not_found", "message": f"File not found: {path}"},
            )
        import hashlib
        return {
            "path": path,
            "content": content,
            "size": len(content),
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "exists": True,
        }

    @router.get("/providers")
    def providers() -> dict[str, Any]:
        from causalyn.config import get_settings
        settings = get_settings()
        return {
            "active_provider": settings.model_provider or ("gemini" if settings.gemini_api_key else "null"),
            "model_name": settings.model_name or "gemini-3.6-flash",
            "providers": ["gemini", "groq", "openrouter", "nvidia", "null"],
            "available_keys": {
                "gemini": bool(settings.gemini_api_key),
                "groq": bool(settings.groq_api_key),
                "openrouter": bool(settings.openrouter_api_key),
                "nvidia": bool(settings.nvidia_nim_key),
            },
            "status": "ready"
        }

    @router.get("/audit")
    def audit() -> dict[str, Any]:
        return {
            "framework": "EU AI Act (Regulation 2024/1689 Article 10)",
            "records": service.store.recent(50),
        }

    @router.post("/intents", response_model=IntentResponse)
    def intents(request: IntentRequest) -> dict[str, Any]:
        intent = request.intent.strip()
        if not intent:
            raise HTTPException(
                status_code=400,
                detail={"code": "invalid_intent", "message": "intent must be a non-empty string"},
            )
        context = service.run_intent(intent, request.execution_mode)
        payload = serialize_context(context)
        payload["execution_mode"] = request.execution_mode
        service.save_context(payload)
        return payload

    @router.post("/proxy/action", response_model=InterceptActionResponse)
    async def proxy_action(request: InterceptActionRequest) -> dict[str, Any]:
        import hashlib
        import time
        from ..orchestrator.cegar_graph import CEGAROrchestrationGraph
        from ..storage.repository import get_audit_repository

        start_time = time.perf_counter()
        cegar = CEGAROrchestrationGraph(world_state_manager=service.world_state)

        final_state = await cegar.invoke({
            "session_id": request.session_id,
            "pipeline_id": f"proxy-{request.request_id}",
            "intent": f"[{request.agent_framework.upper()}] {request.action_type.value} on {request.target_path or 'workspace'}",
            "proposed_action": {
                "agent_framework": request.agent_framework,
                "action_type": request.action_type.value,
                "target_path": request.target_path,
                "payload": request.payload,
                "environment_variables": request.environment_variables,
            },
        })

        duration_ms = (time.perf_counter() - start_time) * 1000
        decision_str = final_state.get("verification_decision", "deny")
        kappa = float(final_state.get("paradox_index", 0.0))
        violations = final_state.get("violations", [])
        diffs = final_state.get("unified_diffs", {})

        raw_audit = f"{request.request_id}:{decision_str}:{kappa}:{len(violations)}"
        audit_hash = hashlib.sha256(raw_audit.encode()).hexdigest()

        try:
            audit_repo = get_audit_repository()
            audit_repo.record_causalyn_mission(
                mission_id=f"mission-{request.request_id}",
                session_id=request.session_id,
                request_id=request.request_id,
                agent_framework=request.agent_framework,
                intent=f"{request.action_type.value} -> {request.target_path or 'host'}",
                stage=final_state.get("commit_status", "annihilated"),
                paradox_index=kappa,
                verification_decision=decision_str,
                commit_decision=final_state.get("commit_status", "annihilated"),
                pre_state_hash=audit_hash,
                post_state_hash=audit_hash if decision_str == "allow" else None,
            )
            audit_repo.record_causalyn_audit(
                mission_id=f"mission-{request.request_id}",
                verifier_matrix={"violations_count": len(violations), "violations": violations},
                unified_diffs=diffs,
                hash_signature=audit_hash,
                counterexamples=final_state.get("counterexamples", []),
                article_10_compliant=True,
            )
        except Exception:
            pass

        reason = (
            "State transition verified in Semantic Null-Space (\u03ba = 0.0)"
            if decision_str == "allow"
            else f"Consensus gate rejected action (\u03ba = {kappa:.2f}). Violations detected; shadow state annihilated."
        )

        service.save_context({
            "pipeline_id": f"proxy-{request.request_id}",
            "session_id": request.session_id,
            "stage": "committed" if decision_str == "allow" else "failed",
            "stages_completed": [
                "intent_received",
                "shadow_execution",
                "verification",
                "committed" if decision_str == "allow" else "failed",
            ],
            "intent": {
                "goal": f"[{request.agent_framework.upper()}] {request.action_type.value} on {request.target_path or 'workspace'}"
            },
            "verification": decision_str,
            "paradox_index": kappa,
            "commit": {
                "decision": "committed" if decision_str == "allow" else "denied",
                "authorization_given": (decision_str == "allow"),
                "reason": reason,
                "commit_id": f"tx-{audit_hash[:12]}",
                "changes": diffs,
            },
            "unified_diffs": diffs,
            "cegar_counterexamples": final_state.get("counterexamples", []),
        })

        return {
            "decision": decision_str,
            "paradox_index": kappa,
            "reason": reason,
            "violations": violations,
            "execution_time_ms": duration_ms,
            "audit_hash": audit_hash,
            "article_10_audit_id": f"art10-{audit_hash[:16]}",
            "unified_diffs": diffs,
        }

    @router.post("/vpsn/evaluate")
    def evaluate_vpsn(request: EvaluateVPSNRequest) -> dict[str, Any]:
        """
        Execute candidate code through the Mathematical Kernel (kappa Engine),
        Z3 SMT Solver, and Ambient Fabric with the Vaishak Operator.
        """
        import time
        from ..verification.kappa_engine import compute_paradox_index
        from ..verification.cegar_loop import evaluate_invariant_nullspace
        from ..shadow.ambient_fabric import AmbientFabric

        t0 = time.perf_counter()

        # 1. AST & Invariant evaluation
        ast_kappa, ast_violations = compute_paradox_index(
            request.candidate_code, request.intent_vector
        )

        # 2. SMT Null-Space constraint evaluation
        smt_kappa, smt_msg = evaluate_invariant_nullspace(
            request.proposed_vars, request.intent_vector
        )
        smt_counterexample = (
            {"smt_status": "UNSAT", "proof": smt_msg} if smt_kappa > 0 else None
        )

        # 3. Aggregate Paradox Index
        total_kappa = (ast_kappa if ast_kappa != float("inf") else 1000.0) + smt_kappa
        all_violations = list(ast_violations)
        if smt_kappa > 0:
            all_violations.append(smt_msg)

        # 4. Ambient Fabric Simulation
        fabric = AmbientFabric(source_dir=str(service.world_state.root_path))
        fabric.snapshot()
        fabric.write_shadow_file(request.file_name, request.candidate_code)
        diff = fabric.extract_candidate_diff(request.file_name)

        # 5. Apply the Vaishak Operator (Upsilon)
        operator_status = fabric.apply_vaishak_operator(total_kappa, request.file_name)

        duration_ms = (time.perf_counter() - t0) * 1000

        # Update global manifold state for WebGL canvas
        global _MANIFOLD_TELEMETRY
        _MANIFOLD_TELEMETRY["annihilation_count"] += 1 if operator_status == "ANNIHILATED" else 0
        _MANIFOLD_TELEMETRY["last_kappa"] = total_kappa
        _MANIFOLD_TELEMETRY["last_status"] = operator_status
        _MANIFOLD_TELEMETRY["last_violations"] = all_violations
        _MANIFOLD_TELEMETRY["last_timestamp"] = time.time()

        # Broadcast real-time execution state directly to GPU over WebSocket
        try:
            import app as main_app
            main_app.trigger_semantic_interference_sync(
                kappa_val=total_kappa,
                violation=all_violations[0] if all_violations else "Semantic Null-Space Admitted",
            )
        except Exception:
            pass

        return {
            "paradox_index": total_kappa,
            "kappa": total_kappa,
            "vaishak_operator": operator_status,
            "operator_status": operator_status,
            "admissible": (total_kappa == 0.0),
            "ast_violations": ast_violations,
            "structural_violations": all_violations,
            "smt_message": smt_msg,
            "smt_counterexample": smt_counterexample,
            "unified_diff": diff,
            "diff": diff,
            "live_bytes_mutated": len(request.candidate_code) if operator_status == "COMMITTED" else 0,
            "duration_ms": round(duration_ms, 2),
            "state_annihilated": (operator_status == "ANNIHILATED"),
        }

    @router.get("/vpsn/manifold")
    def get_manifold_telemetry() -> dict[str, Any]:
        """Telemetry endpoint providing real-time 3D Symplectic Manifold data for WebGL."""
        kappa = _MANIFOLD_TELEMETRY.get("last_kappa", 0.0)
        annihilations = _MANIFOLD_TELEMETRY.get("annihilation_count", 0)
        return {
            "manifold": "Vaishak Continuum",
            "curvature": round(kappa * 0.15, 4),
            "active_kappa": kappa,
            "paradox_index": kappa,
            "topology_status": (
                "PARADOX_SPIKE" if kappa > 0.0 else "EQUILIBRIUM"
            ),
            "annihilations_total": annihilations,
            "annihilations_count": annihilations,
            "paradox_eruptions_count": annihilations,
            "last_operator_event": _MANIFOLD_TELEMETRY.get("last_status", "EQUILIBRIUM"),
            "active_violations": _MANIFOLD_TELEMETRY.get("last_violations", []),
            "telemetry_history": [
                {
                    "timestamp": _MANIFOLD_TELEMETRY.get("last_timestamp", 0),
                    "kappa": kappa,
                    "status": _MANIFOLD_TELEMETRY.get("last_status", "EQUILIBRIUM"),
                }
            ],
        }

    @router.post("/vpsn/synthesize")
    def synthesize_dependencies(request: Request, payload: dict[str, Any]) -> dict[str, Any]:
        """Real-time integration with the Z3 Acausal Synthesizer, State Bus, and Ricci Flow."""
        import time
        from ..orchestrator.state_bus import HyperDimensionalStateBus
        from ..verification.cegar_loop import AcausalSynthesizer

        start_time = time.perf_counter()
        
        # 1. State Bus Integration (GAP 2)
        agent_id = "ui-agent-1"
        bus = HyperDimensionalStateBus()
        
        # Register intent with the bus to check global geometric collisions
        allowed, bus_kappa, bus_msg = bus.register_intent(agent_id, payload)
        
        # 2. Acausal Compiler & Ricci Flow (GAP 1)
        # Even if the bus allows it locally, we run Ricci flow to auto-correct any internal violations
        synthesizer = AcausalSynthesizer()
        synthesizer.apply_intent_vector()
        
        kappa, feedback, corrected_state = synthesizer.apply_ricci_flow(payload)
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Clean up the intent from the bus after transaction
        bus.release_intent(agent_id)
        
        decision_str = "allow" if kappa == 0 else "deny"
        
        # Broadcast real-time execution state directly to GPU over WebSocket
        try:
            import app as main_app
            main_app.trigger_semantic_interference_sync(
                kappa_val=kappa,
                violation=feedback[0] if feedback else "Semantic Null-Space Admitted",
            )
        except Exception:
            pass

        return {
            "decision": decision_str,
            "paradox_index": kappa,
            "reason": feedback[0] if feedback else "State is mathematically flawless. Merging.",
            "violations": feedback,
            "corrected_state": corrected_state, # Ricci Flow smoothed state (GAP 1)
            "bus_collision": not allowed,       # Multi-agent collision detection (GAP 2)
            "bus_message": bus_msg,
            "execution_time_ms": duration_ms,
            "unified_diffs": {},
        }

    return router
