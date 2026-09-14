import asyncio
import json
import time
import httpx
import websockets

WS_URL = "ws://127.0.0.1:8000/ws/continuum"
HTTP_URL = "http://127.0.0.1:8000"

async def ws_listener(client_id: int, stop_event: asyncio.Event, received_events: list, ready_event: asyncio.Event):
    try:
        async with websockets.connect(WS_URL) as ws:
            # Receive handshake ack
            greeting = await ws.recv()
            data = json.loads(greeting)
            assert data.get("type") == "connection_ack"
            ready_event.set()

            while not stop_event.is_set():
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=0.2)
                    parsed = json.loads(msg)
                    received_events.append({"client_id": client_id, "data": parsed})
                except asyncio.TimeoutError:
                    continue
    except Exception as e:
        print(f"[WS Client {client_id}] Connection error: {e}")

async def run_websocket_stress(num_clients: int = 25, broadcast_duration: float = 3.0):
    print("\n=======================================================")
    print(" CAUSALYN STRESS SUITE 4: WEBSOCKET STREAM MULTIPLEXING")
    print(f" Concurrent WS Clients: {num_clients}")
    print("=======================================================")

    received_events = []
    ready_events = [asyncio.Event() for _ in range(num_clients)]
    stop_event = asyncio.Event()

    # Start WS listener tasks
    ws_tasks = [
        asyncio.create_task(ws_listener(i, stop_event, received_events, ready_events[i]))
        for i in range(num_clients)
    ]

    # Wait for all clients to connect and receive handshake
    await asyncio.gather(*[re.wait() for re in ready_events])
    print(f"[+] All {num_clients} WebSocket clients connected and acknowledged.")

    # Concurrently emit bursts of HTTP mutations to generate telemetry broadcast traffic
    async with httpx.AsyncClient(timeout=10.0) as http_client:
        for i in range(10):
            payload = {
                "agent_id": f"ws_burst_agent_{i}",
                "target_file": "app/public/settings.json",
                "proposed_content": f"threads = {4 + (i % 8)}\nmemory = {256 + (i * 32)}\nsockets = 10\n",
                "state_variables": {"threads": 4 + (i % 8), "memory": 256 + (i * 32), "sockets": 10}
            }
            await http_client.post(f"{HTTP_URL}/api/v1/intercept", json=payload)
            await asyncio.sleep(0.04)

    # Allow brief window for all broadcast packets to reach all clients
    await asyncio.sleep(0.8)
    stop_event.set()
    await asyncio.gather(*ws_tasks)

    paradox_events = [e for e in received_events if e["data"].get("type") == "paradox_spike"]
    manifold_events = [e for e in received_events if e["data"].get("type") == "manifold_update"]

    print(f"\n--- WEBSOCKET STREAM SUMMARY ---")
    print(f"Total Telemetry Packets Received: {len(received_events)}")
    print(f"Paradox Spike Events Streamed:    {len(paradox_events)}")
    print(f"Manifold Update Events Streamed:   {len(manifold_events)}")
    print(f"Average Events Per Client:        {len(received_events) / num_clients:.1f}")

    assert len(received_events) > 0, "No telemetry events were received by WebSocket clients!"
    assert len(paradox_events) >= 10 * num_clients, "Some clients missed broadcast telemetry packets!"
    print(f"\n>>> WEBSOCKET STREAM STRESS TEST: PASSED 100% <<<\n")
    return True

if __name__ == "__main__":
    asyncio.run(run_websocket_stress(num_clients=25, broadcast_duration=2.5))
