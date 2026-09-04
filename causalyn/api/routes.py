"""FastAPI route wiring for the backend service."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, HTTPException

from .contracts import IntentRequest, InterceptActionRequest, InterceptActionResponse
from .responses import HealthResponse, IntentResponse, PipelinesResponse, StateResponse
from .services import BackendService


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
    def missions() -> list[dict[str, Any]]:
        from ..storage.repository import get_audit_repository
        repo = get_audit_repository()
        if hasattr(repo, "get_causalyn_missions"):
            return repo.get_causalyn_missions(50)
        return []


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

    return router
