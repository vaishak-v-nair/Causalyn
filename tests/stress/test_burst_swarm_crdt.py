import asyncio
import httpx
import time
import statistics

BASE_URL = "http://127.0.0.1:8000"

async def send_swarm_batch(client: httpx.AsyncClient, batch_id: int, agent_count: int = 15) -> dict:
    t0 = time.perf_counter()
    agents = []
    for a in range(agent_count):
        agent_id = f"swarm_agent_{batch_id}_{a}"
        agents.append({
            "agent_id": agent_id,
            "target_file": f"app/services/worker_{a % 4}.py",
            "proposed_content": f"# Swarm mutation from {agent_id} in batch {batch_id}\ndef work(): return {batch_id * 100 + a}\n",
            "state_variables": {"threads": 4, "memory": 512, "sockets": 20}
        })
    
    payload = {"agents": agents}
    try:
        resp = await client.post(f"{BASE_URL}/api/v1/swarm/reconcile", json=payload, timeout=15.0)
        dur_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "batch_id": batch_id,
            "status_code": resp.status_code,
            "duration_ms": dur_ms,
            "body": resp.json() if resp.status_code == 200 else resp.text,
            "error": None
        }
    except Exception as e:
        dur_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "batch_id": batch_id,
            "status_code": 0,
            "duration_ms": dur_ms,
            "body": None,
            "error": str(e)
        }

async def run_swarm_crdt_stress(total_batches: int = 60, concurrency: int = 20, agents_per_batch: int = 15):
    print("\n=======================================================")
    print(" CAUSALYN STRESS SUITE 2: SWARM CRDT VECTOR CLOCK BURST")
    print(f" Batches: {total_batches} | Concurrency: {concurrency} | Agents/Batch: {agents_per_batch}")
    print(f" Total Concurrent Swarm Operations: {total_batches * agents_per_batch}")
    print("=======================================================")

    limits = httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency * 2)
    async with httpx.AsyncClient(limits=limits, timeout=25.0) as client:
        start_time = time.perf_counter()
        semaphore = asyncio.Semaphore(concurrency)

        async def sem_task(idx: int):
            async with semaphore:
                return await send_swarm_batch(client, idx, agents_per_batch)

        tasks = [sem_task(i) for i in range(total_batches)]
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time

    successes = [r for r in results if r["status_code"] == 200]
    failures = [r for r in results if r["status_code"] != 200]
    latencies = [r["duration_ms"] for r in successes]

    total_ops_reconciled = 0
    ordering_valid = True

    for r in successes:
        body = r["body"]
        if isinstance(body, dict) and "order" in body:
            order = body["order"]
            total_ops_reconciled += len(order)
            # Verify deterministic ordering: clocks must be non-decreasing
            clocks = [op["clock"] for op in order]
            if clocks != sorted(clocks):
                ordering_valid = False

    print(f"\n--- EXECUTION SUMMARY ---")
    print(f"Total Batches Sent:       {len(results)}")
    print(f"Successful (HTTP 200):    {len(successes)} ({len(successes)/len(results)*100:.1f}%)")
    print(f"Failed / Error:           {len(failures)} ({len(failures)/len(results)*100:.1f}%)")
    print(f"Total Operations Merged:  {total_ops_reconciled}")
    print(f"Total Wallclock Time:     {total_time:.3f} s")
    print(f"Swarm Ops Throughput:     {total_ops_reconciled/total_time:.2f} ops/s")
    print(f"Vector Clock Monotonic:   {'VERIFIED (100% Deterministic)' if ordering_valid else 'VIOLATION DETECTED'}")

    if latencies:
        latencies.sort()
        print(f"\n--- LATENCY METRICS (ms) ---")
        print(f"Min:    {min(latencies):.2f} ms")
        print(f"Mean:   {statistics.mean(latencies):.2f} ms")
        print(f"Median: {statistics.median(latencies):.2f} ms")
        print(f"P90:    {latencies[int(len(latencies) * 0.90)]:.2f} ms")
        print(f"P95:    {latencies[int(len(latencies) * 0.95)]:.2f} ms")
        print(f"P99:    {latencies[int(len(latencies) * 0.99)]:.2f} ms")
        print(f"Max:    {max(latencies):.2f} ms")

    assert len(failures) == 0, f"Encountered {len(failures)} failed batches!"
    assert ordering_valid, "Vector clock ordering was not monotonic!"
    print(f"\n>>> SWARM CRDT BURST STRESS TEST: PASSED 100% <<<\n")
    return True

if __name__ == "__main__":
    asyncio.run(run_swarm_crdt_stress(total_batches=60, concurrency=20, agents_per_batch=15))
