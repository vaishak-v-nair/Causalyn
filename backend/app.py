from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import asyncio
import json
import time
import os

from core.ambient_fabric import AmbientFabric
from core.cegar_synthesizer import AcausalSynthesizer
from core.manim_engine import ManimEngine
from core.crdt_state_bus import HyperDimensionalStateBus, SwarmOperation
from z3 import Int

app = FastAPI(title="Causalyn Acausal Control Plane", version="3.1.0-BRIGHT")

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
fabric = AmbientFabric(workspace_root="../")
state_bus = HyperDimensionalStateBus()

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
    
    invariants = [
        lambda v: v.get('threads', Int('threads')) <= 16,
        lambda v: v.get('memory', Int('memory')) <= 1024,
        lambda v: v.get('sockets', Int('sockets')) <= 100
    ]
    
    with fabric.spawn_shadow_continuum(call.target_file) as shadow_path:
        kappa, code, patch = await asyncio.to_thread(
            synthesizer.synthesize_valid_state,
            call.proposed_content,
            call.state_variables,
            invariants
        )
        
        duration_us = (time.perf_counter_ns() - t_start) / 1000.0

        if kappa == 0.0:
            status = "COMMITTED"
            fabric.atomic_commit(shadow_path, call.target_file)
        elif patch and patch.get("corrected"):
            status = "SYNTHESIZED"
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
            "patch": patch
        }
        await telemetry.emit_telemetry(event_payload)

        # Trigger headless manim visualization asynchronously
        bg_tasks.add_task(async_manim_render, kappa, call.agent_id, call.target_file)

        return {
            "status": status,
            "kappa": kappa,
            "latency_us": duration_us,
            "vector_clock": op.clock,
            "synthesized_code": code if status == "SYNTHESIZED" else None
        }

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
    async def serve_dashboard():
        index_file = web_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Web dashboard not found"}

