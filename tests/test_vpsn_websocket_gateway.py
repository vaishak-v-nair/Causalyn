"""
Unit and Integration Test Suite for the VPSN WebSocket Gateway.
Verifies real-time bidirectional WebSocket streaming between the VPSN backend
and the Three.js GPU client:
1. WebSocket connection and lifecycle management (connect, disconnect).
2. Gateway state broadcasting (direct JSON stream to active sockets).
3. Semantic interference trigger functions (PARADOX_DETECTED vs NULL_SPACE_CONFIRMED).
4. End-to-end evaluation pipeline streaming via POST /api/vpsn/evaluate.
"""

import asyncio
import json
import unittest

import app
from fastapi.testclient import TestClient


class TestVPSNWebSocketGateway(unittest.TestCase):
    """Verifies the Continuum Gateway WebSocket stream."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app.api)

    def test_websocket_connect_and_disconnect(self):
        """WebSocket clients successfully connect, register in gateway, and cleanly disconnect."""
        initial_connections = len(app.gateway.active_connections)
        with self.client.websocket_connect("/ws/continuum") as websocket:
            self.assertEqual(len(app.gateway.active_connections), initial_connections + 1)
            # Send a ping message from client
            websocket.send_text("PING")
        # After exit block, connection must be removed
        self.assertEqual(len(app.gateway.active_connections), initial_connections)

    def test_gateway_broadcast_state(self):
        """Gateway broadcasts state payload directly to all connected sockets."""
        with self.client.websocket_connect("/ws/continuum") as websocket:
            payload = {
                "event": "TEST_BROADCAST",
                "kappa": 42.0,
                "violation": "Test Invariant Breach",
                "decision": "DENY"
            }
            # Run async broadcast in loop
            asyncio.run(app.gateway.broadcast_state(payload))
            
            # Receive broadcast on websocket
            data = websocket.receive_text()
            parsed = json.loads(data)
            self.assertEqual(parsed["event"], "TEST_BROADCAST")
            self.assertEqual(parsed["kappa"], 42.0)
            self.assertEqual(parsed["decision"], "DENY")

    def test_trigger_semantic_interference_paradox(self):
        """trigger_semantic_interference with kappa > 0 broadcasts PARADOX_DETECTED."""
        with self.client.websocket_connect("/ws/continuum") as websocket:
            asyncio.run(app.trigger_semantic_interference(
                kappa_val=75.0,
                violation="Paradox: Unauthorized os.system call"
            ))

            data = websocket.receive_text()
            parsed = json.loads(data)
            self.assertEqual(parsed["event"], "PARADOX_DETECTED")
            self.assertEqual(parsed["kappa"], 75.0)
            self.assertEqual(parsed["decision"], "DENY")
            self.assertIn("os.system", parsed["violation"])

    def test_trigger_semantic_interference_null_space(self):
        """trigger_semantic_interference with kappa == 0 broadcasts NULL_SPACE_CONFIRMED."""
        with self.client.websocket_connect("/ws/continuum") as websocket:
            asyncio.run(app.trigger_semantic_interference(
                kappa_val=0.0,
                violation=""
            ))

            data = websocket.receive_text()
            parsed = json.loads(data)
            self.assertEqual(parsed["event"], "NULL_SPACE_CONFIRMED")
            self.assertEqual(parsed["kappa"], 0.0)
            self.assertEqual(parsed["decision"], "ALLOW")

    def test_e2e_evaluate_vpsn_broadcasts_to_websocket(self):
        """Calling /api/vpsn/evaluate streams state update live to connected WebSockets."""
        with self.client.websocket_connect("/ws/continuum") as websocket:
            # Send evaluation request
            res = self.client.post("/api/vpsn/evaluate", json={
                "file_name": "malicious.py",
                "candidate_code": "import subprocess\nsubprocess.Popen(['rm', '-rf', '/'])\n",
                "intent_vector": {"block_os": True}
            })
            self.assertEqual(res.status_code, 200)

            # Receive WebSocket broadcast streamed during evaluation
            data = websocket.receive_text()
            parsed = json.loads(data)
            self.assertEqual(parsed["event"], "PARADOX_DETECTED")
            self.assertGreater(parsed["kappa"], 0.0)
            self.assertEqual(parsed["decision"], "DENY")


if __name__ == "__main__":
    unittest.main()
