"""WebSocket connection manager for real-time telemetry streaming."""
from typing import List, Dict, Any
from fastapi import WebSocket
import asyncio
import json
import logging

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info("[WEBSOCKET] Client connected to Manifold Telemetry.")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logging.info("[WEBSOCKET] Client disconnected.")

    async def broadcast_json(self, payload: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(payload)
            except Exception as e:
                logging.error(f"[WEBSOCKET] Error broadcasting: {e}")
                self.disconnect(connection)

# Global manager instance
ws_manager = ConnectionManager()

def trigger_semantic_interference_sync(kappa_val: float, violation: str):
    """
    Synchronous wrapper to trigger async broadcast.
    Instantly broadcasts the Paradox Spike to the WebGL frontend over WebSocket.
    """
    event = "PARADOX_DETECTED" if kappa_val > 0 else "NULL_SPACE_CONFIRMED"
    decision = "DENY" if kappa_val > 0 else "ALLOW"
    payload = {
        "type": "paradox_spike" if kappa_val > 0 else "equilibrium",
        "event": event,
        "decision": decision,
        "kappa": kappa_val,
        "violation": violation
    }
    logging.info(f"[WEBSOCKET BROADCAST] {payload}")
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(ws_manager.broadcast_json(payload))
        else:
            loop.run_until_complete(ws_manager.broadcast_json(payload))
    except Exception as e:
        logging.error(f"[WEBSOCKET ERROR] Failed to dispatch broadcast task: {e}")
