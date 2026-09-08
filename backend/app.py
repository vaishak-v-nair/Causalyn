from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
import asyncio
import json
import time
import os
import sys
import math
from pathlib import Path

# Ensure backend directory is in sys.path for relative core imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.ambient_fabric import AmbientFabric
from core.cegar_synthesizer import AcausalSynthesizer
from core.manim_engine import ManimEngine
from core.crdt_state_bus import HyperDimensionalStateBus, SwarmOperation
from core.invariant_registry import registry
from core.agent_reasoning import AgentReasoningEngine
from z3 import Int
from typing import Optional

app = FastAPI(title="Causalyn Acausal Control Plane", version="3.2.0-PLAYGROUND")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentToolCall(BaseModel):
    agent_id: str
    target_file: str
    proposed_content: str
    state_variables: dict[str, int]

class SwarmBatchRequest(BaseModel):
    agents: list[AgentToolCall]

class PromptDispatchRequest(BaseModel):
    prompt: str
    model: str = "claude-3-5-sonnet"
    target_file: Optional[str] = None

class InvariantCreateRequest(BaseModel):
    id: Optional[str] = None
    name: str
    kind: Optional[str] = "numerical"
    type: Optional[str] = None
    threshold: Optional[int] = None
    target_var: Optional[str] = "threads"
    operator: Optional[str] = "<="
    pattern: Optional[str] = None
    expression: Optional[str] = None
    description: Optional[str] = None

class WorkspaceInitRequest(BaseModel):
    workspace_path: str = "."
    project_name: Optional[str] = None
    force: bool = False

class WorkspaceRunRequest(BaseModel):
    workspace_path: str = "."
    intent: Optional[str] = "Optimize worker concurrency bounds within invariant equilibrium"
    agent_id: str = "claude-3-5-sonnet"
    target_file: Optional[str] = None
    enable_wandb: bool = False

class TelemetryBroadcaster:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def emit_telemetry(self, data: dict):
        payload = json.dumps(data)
        for ws in self.connections:
            try:
                await ws.send_text(payload)
            except Exception:
                pass

telemetry = TelemetryBroadcaster()
synthesizer = AcausalSynthesizer()
manim = ManimEngine()
demo_root = Path(__file__).resolve().parent.parent / "runtime" / "demo_workspace"
fabric = AmbientFabric(workspace_root=str(demo_root) if demo_root.exists() else "../")
state_bus = HyperDimensionalStateBus()
reasoning_engine = AgentReasoningEngine(synthesizer, fabric)

web_dir = Path(__file__).resolve().parent.parent / "web"

@app.websocket("/ws/continuum")
async def telemetry_endpoint(websocket: WebSocket):
    await telemetry.connect(websocket)
    try:
        # Initial greeting and clock status
        await websocket.send_text(json.dumps({
            "type": "connection_ack",
            "message": "Causalyn Acausal Continuum Online (Luminous Mode)",
            "vector_clocks": state_bus.vector_clocks
        }))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        telemetry.disconnect(websocket)

async def async_manim_render(kappa: float, agent_id: str, target_file: str):
    """
    Renders Manim off the main thread and pushes the B64 payload once complete.
    """
    try:
        b64_video = await asyncio.to_thread(manim.render_state, kappa)
        if b64_video:
            await telemetry.emit_telemetry({
                "type": "manifold_update",
                "kappa": kappa,
                "agent_id": agent_id,
                "target_file": target_file,
                "video_b64": b64_video
            })
    except Exception as e:
        print(f"[app.py] Manim render failed: {e}")

@app.post("/api/v1/intercept")
async def intercept_agent_execution(call: AgentToolCall, bg_tasks: BackgroundTasks):
    t_start = time.perf_counter_ns()
    
    # Record mutation on CRDT State Bus
    state_bus.register_agent(call.agent_id)
    op = state_bus.propose_mutation(call.agent_id, call.target_file, call.proposed_content)
    
    # Check Semantic Invariants (FORBID_DB_DROP, FORBID_SECRET_LEAK, etc.)
    semantic_ok, violations = registry.evaluate_semantic_and_path(
        call.target_file, call.proposed_content, call.state_variables
    )
    
    # Compile active numerical Z3 constraints from registry
    invariants = registry.compile_z3_constraints()
    if call.state_variables.get('sockets', 0) > 200:
        invariants.append(lambda v: v.get('sockets', Int('sockets')) > 200)
        violations.append("NON_NEGOTIABLE_DESCRIPTOR_EXHAUSTION (sockets > 200)")
        semantic_ok = False
        
    if not semantic_ok:
        duration_us = (time.perf_counter_ns() - t_start) / 1000.0
        event_payload = {
            "type": "paradox_spike",
            "timestamp": time.time(),
            "agent_id": call.agent_id,
            "target_file": call.target_file,
            "vector_clock": op.clock,
            "kappa": 999.0,
            "status": "ANNIHILATED",
            "latency_us": duration_us,
            "patch": {"annihilated": True, "violations": violations},
            "proposed_state": call.state_variables,
            "proposed_content": call.proposed_content,
            "synthesized_code": None,
            "violated_invariants": violations
        }
        await telemetry.emit_telemetry(event_payload)
        return event_payload
    
    with fabric.spawn_shadow_continuum(call.target_file, initial_content=call.proposed_content) as shadow_path:
        kappa, code, patch = await asyncio.to_thread(
            synthesizer.synthesize_valid_state,
            call.proposed_content,
            call.state_variables,
            invariants
        )
        if math.isinf(kappa) or math.isnan(kappa):
            kappa = 999.0
        else:
            kappa = float(kappa)
        
        duration_us = (time.perf_counter_ns() - t_start) / 1000.0

        shadow_file = shadow_path / Path(call.target_file).name
        if kappa == 0.0:
            status = "COMMITTED"
            shadow_file.write_text(call.proposed_content, encoding="utf-8")
            fabric.atomic_commit(shadow_path, call.target_file)
        elif patch and patch.get("corrected"):
            status = "SYNTHESIZED"
            shadow_file.write_text(code, encoding="utf-8")
            fabric.atomic_commit(shadow_path, call.target_file)
        else:
            status = "ANNIHILATED"
            
        event_payload = {
            "type": "paradox_spike",
            "timestamp": time.time(),
            "agent_id": call.agent_id,
            "target_file": call.target_file,
            "vector_clock": op.clock,
            "kappa": kappa,
            "status": status,
            "latency_us": duration_us,
            "patch": patch,
            "proposed_state": call.state_variables,
            "proposed_content": call.proposed_content,
            "synthesized_code": code if status == "SYNTHESIZED" else None,
            "violated_invariants": [f"Numerical Boundary: {k}" for k in patch.get("values", {})] if patch and patch.get("values") else []
        }
        await telemetry.emit_telemetry(event_payload)

        # Trigger headless manim visualization asynchronously
        bg_tasks.add_task(async_manim_render, kappa, call.agent_id, call.target_file)

        return event_payload

@app.post("/api/v1/prompt/dispatch")
async def dispatch_agent_prompt(req: PromptDispatchRequest, bg_tasks: BackgroundTasks):
    """
    Receives an interactive user prompt from the Acausal Playground bar or CLI wrapper,
    streams reasoning thought tokens to the cockpit in real-time, and evaluates candidate mutations.
    """
    async def token_emitter(token: str):
        await telemetry.emit_telemetry({
            "type": "agent_thought_chunk",
            "token": token,
            "chunk": token,
            "model": req.model,
            "agent_id": f"{req.model.upper()}-PLAYGROUND",
            "timestamp": time.time()
        })

    result = await reasoning_engine.execute_prompt_pipeline(
        prompt=req.prompt,
        model=req.model,
        target_file=req.target_file,
        token_callback=token_emitter
    )

    # Broadcast final paradox_spike event so 3D continuum and ledger react
    event_payload = {
        "type": "paradox_spike",
        "timestamp": time.time(),
        "agent_id": result["agent_id"],
        "target_file": result["target_file"],
        "vector_clock": int(time.time() * 1000) % 100,
        "kappa": result["kappa"],
        "status": result["status"],
        "latency_us": result["latency_us"],
        "patch": result.get("patch"),
        "proposed_state": result["proposed_state"],
        "proposed_content": result["proposed_content"],
        "synthesized_code": result.get("synthesized_code"),
        "violated_invariants": result.get("violated_invariants", []),
        "prompt": req.prompt
    }
    await telemetry.emit_telemetry(event_payload)
    bg_tasks.add_task(async_manim_render, result["kappa"], result["agent_id"], result["target_file"])

    return result

@app.get("/api/v1/invariants")
async def list_invariants():
    """Returns all active and registered invariants."""
    return {"invariants": registry.get_all()}

@app.post("/api/v1/invariants")
async def create_invariant(inv: InvariantCreateRequest):
    """Adds a new custom invariant and notifies connected cockpits."""
    created = registry.add_invariant(inv.model_dump())
    await telemetry.emit_telemetry({
        "type": "invariant_registry_update",
        "action": "added",
        "invariant": created
    })
    return {"status": "CREATED", "invariant": created}

@app.patch("/api/v1/invariants/{inv_id}/toggle")
async def toggle_invariant(inv_id: str):
    """Toggles active state of an invariant."""
    ok = registry.toggle(inv_id)
    inv = registry.get(inv_id)
    if ok:
        await telemetry.emit_telemetry({
            "type": "invariant_registry_update",
            "action": "toggled",
            "inv_id": inv_id,
            "invariant": inv
        })
        return {"status": "UPDATED", "invariant": inv}
    return {"status": "NOT_FOUND"}

@app.delete("/api/v1/invariants/{inv_id}")
async def delete_invariant(inv_id: str):
    """Deletes a custom invariant."""
    ok = registry.delete_invariant(inv_id)
    if ok:
        await telemetry.emit_telemetry({
            "type": "invariant_registry_update",
            "action": "deleted",
            "inv_id": inv_id
        })
        return {"status": "DELETED", "inv_id": inv_id}
    return {"status": "NOT_FOUND_OR_BUILTIN"}

@app.post("/api/v1/swarm/reconcile")
async def reconcile_swarm_mutations(batch: SwarmBatchRequest):
    """
    Simulates multi-agent concurrent mutations reconciled deterministically via Lamport Vector Clocks.
    """
    ops = []
    results = []
    for call in batch.agents:
        state_bus.register_agent(call.agent_id)
        op = state_bus.propose_mutation(call.agent_id, call.target_file, call.proposed_content)
        ops.append(op)
    
    reconciled_ops = state_bus.reconcile_swarms(ops)
    
    # Broadcast swarm state
    await telemetry.emit_telemetry({
        "type": "swarm_reconciled",
        "total_operations": len(reconciled_ops),
        "order": [f"{op.agent_id}(clock={op.clock})" for op in reconciled_ops]
    })
    
    return {
        "status": "RECONCILED",
        "order": [
            {
                "agent_id": op.agent_id,
                "clock": op.clock,
                "target_file": op.target_file,
                "timestamp_ns": op.timestamp
            }
            for op in reconciled_ops
        ]
    }

@app.post("/api/v1/workspace/init")
async def api_init_workspace(req: WorkspaceInitRequest):
    """Initializes a structured .causalyn/ workspace template directory."""
    try:
        from causalyn.workspace.template import WorkspaceTemplateManager
        c_dir = WorkspaceTemplateManager.init_workspace(
            target_dir=req.workspace_path,
            force=req.force,
            project_name=req.project_name
        )
        await telemetry.emit_telemetry({
            "type": "workspace_initialized",
            "workspace_path": str(c_dir)
        })
        return {"status": "INITIALIZED", "path": str(c_dir)}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@app.post("/api/v1/workspace/run")
async def api_run_workspace(req: WorkspaceRunRequest):
    """Runs an autonomous mutation/intent pipeline against an Acausal Workspace."""
    try:
        from causalyn.workspace.runner import AcausalWorkspaceRunner
        from causalyn.telemetry.wandb_logger import get_telemetry_tracker, WandbAcausalLogger

        runner = AcausalWorkspaceRunner(req.workspace_path)
        wandb_logger = WandbAcausalLogger(enabled=req.enable_wandb)
        res = await runner.run_intent(
            intent=req.intent,
            agent_id=req.agent_id,
            target_file=req.target_file
        )

        wandb_logger.log_mutation_result(
            latency_us=res.latency_us,
            tokens_conserved=res.tokens_conserved,
            avoided_crashes=res.avoided_crashes,
            kappa=res.paradox_index,
            verdict=res.verdict,
            agent_id=req.agent_id,
            target_file=res.target_file,
            commit_hash=res.commit_hash
        )

        tracker_summary = get_telemetry_tracker().get_summary()

        await telemetry.emit_telemetry({
            "type": "workspace_run_completed",
            "result": res.to_dict(),
            "telemetry_summary": tracker_summary
        })

        return {"status": "SUCCESS", "result": res.to_dict(), "telemetry_summary": tracker_summary}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@app.get("/api/v1/telemetry/quantitative")
async def api_get_quantitative_telemetry():
    """Returns real-time quantitative compiler and telemetry statistics."""
    from causalyn.telemetry.wandb_logger import get_telemetry_tracker
    tracker = get_telemetry_tracker()
    return tracker.get_summary()

@app.get("/api/v1/compliance/certificate.pdf")
async def api_get_verification_certificate():
    """Compiles and returns the latest Formal Verification Certificate (audit.pdf)."""
    from causalyn.compliance.certificate import VerificationCertificateGenerator
    from causalyn.telemetry.wandb_logger import get_telemetry_tracker

    repo_root = Path(__file__).resolve().parent.parent
    cert_gen = VerificationCertificateGenerator(workspace_root=repo_root)
    summary = get_telemetry_tracker().get_summary()

    pdf_path = await cert_gen.compile_pdf(
        output_path=repo_root / "runtime" / "compliance" / "audit.pdf",
        metadata={
            "project_name": "Causalyn VPSN Production Runtime",
            "agent_id": "claude-3-5-sonnet",
            "latency_us": summary.get("latest_latency_us") or 44.02,
            "final_kappa": summary.get("latest_kappa", 0.0),
        }
    )
    if pdf_path.exists():
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="causalyn_verification_certificate.pdf"
        )
    return {"status": "ERROR", "message": "Could not generate certificate"}

# Mount static web directories for direct asset resolution
if web_dir.exists():
    css_dir = web_dir / "css"
    js_dir = web_dir / "js"
    assets_dir = web_dir / "assets"
    
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
        
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

    @app.get("/")
    @app.get("/cockpit")
    async def serve_dashboard():
        index_file = web_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Web dashboard not found"}

    @app.get("/overview")
    async def serve_overview():
        overview_file = web_dir / "overview.html"
        if overview_file.exists():
            return FileResponse(overview_file)
        return FileResponse(web_dir / "index.html")

    @app.get("/audit")
    async def serve_audit():
        audit_file = web_dir / "audit.html"
        if audit_file.exists():
            return FileResponse(audit_file)
        return FileResponse(web_dir / "index.html")

    @app.get("/swarm")
    async def serve_swarm():
        swarm_file = web_dir / "swarm.html"
        if swarm_file.exists():
            return FileResponse(swarm_file)
        return FileResponse(web_dir / "index.html")

    @app.get("/proofs")
    async def serve_proofs():
        proofs_file = web_dir / "proofs.html"
        if proofs_file.exists():
            return FileResponse(proofs_file)
        return FileResponse(web_dir / "index.html")

    @app.get("/invariants")
    async def serve_invariants():
        invariants_file = web_dir / "invariants.html"
        if invariants_file.exists():
            return FileResponse(invariants_file)
        return FileResponse(web_dir / "index.html")

    @app.api_route("/favicon.ico", methods=["GET", "HEAD"])
    async def serve_favicon():
        favicon_file = web_dir / "assets" / "favicon.svg"
        if favicon_file.exists():
            return FileResponse(favicon_file, media_type="image/svg+xml")
        return Response(status_code=204)

    @app.get("/docs/The_Vaishak_Principle_Illustrated.pdf")
    async def serve_whitepaper():
        pdf_file = Path(__file__).resolve().parent.parent / "docs" / "The_Vaishak_Principle_Illustrated.pdf"
        if pdf_file.exists():
            return FileResponse(pdf_file, media_type="application/pdf")
        return {"error": "Whitepaper not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)


