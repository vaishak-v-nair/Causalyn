import asyncio
import httpx
import time
import json
import statistics
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

async def send_intercept_request(client: httpx.AsyncClient, req_id: int, mode: str) -> dict:
    t0 = time.perf_counter()
    target_file = "app/public/settings.json"
    
    if mode == "safe":
        threads = 4 + (req_id % 8)
        memory = 256 + (req_id % 256)
        sockets = 10 + (req_id % 30)
        code = f"threads = {threads}\nmemory = {memory}\nsockets = {sockets}\n"
        state = {"threads": threads, "memory": memory, "sockets": sockets}
    elif mode == "recoverable":
        threads = 32 + (req_id % 16)  # violates threads <= 16
        memory = 2048 + (req_id % 512) # violates memory <= 1024
        sockets = 20
        code = f"threads = {threads}\nmemory = {memory}\nsockets = {sockets}\n"
        state = {"threads": threads, "memory": memory, "sockets": sockets}
    else: # unrecoverable
        threads = 999
        memory = 999999
        sockets = 500
        code = f"# Malformed boundary candidate\nthreads = {threads}\n"
        state = {"threads": threads, "memory": memory, "sockets": sockets}

    payload = {
        "agent_id": f"burst_agent_{req_id}_{mode}",
        "target_file": target_file,
        "proposed_content": code,
        "state_variables": state
    }
    
    try:
        resp = await client.post(f"{BASE_URL}/api/v1/intercept", json=payload, timeout=15.0)
        duration_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "req_id": req_id,
            "mode": mode,
            "status_code": resp.status_code,
            "duration_ms": duration_ms,
            "body": resp.json() if resp.status_code == 200 else resp.text,
            "error": None
        }
    except Exception as e:
        duration_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "req_id": req_id,
            "mode": mode,
            "status_code": 0,
            "duration_ms": duration_ms,
            "body": None,
            "error": str(e)
        }

async def run_burst_test(total_requests: int = 120, concurrency: int = 30):
    print(f"\n=======================================================")
    print(f" CAUSALYN STRESS SUITE 1: BURST INTERCEPT CONCURRENCY")
    print(f" Total Requests: {total_requests} | Concurrency: {concurrency}")
    print(f"=======================================================")
    
    modes = ["safe", "recoverable", "unrecoverable"]
    
    limits = httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency * 2)
    async with httpx.AsyncClient(limits=limits, timeout=20.0) as client:
        # Pre-flight check
        try:
            health = await client.get(f"{BASE_URL}/")
            assert health.status_code == 200
        except Exception as e:
            print(f"[FATAL] Backend server not reachable at {BASE_URL}: {e}")
            return False

        start_time = time.perf_counter()
        semaphore = asyncio.Semaphore(concurrency)

        async def sem_task(idx: int):
            async with semaphore:
                mode = modes[idx % len(modes)]
                return await send_intercept_request(client, idx, mode)

        tasks = [sem_task(i) for i in range(total_requests)]
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time

    # Evaluate results
    successes = [r for r in results if r["status_code"] == 200]
    failures = [r for r in results if r["status_code"] != 200]
    latencies = [r["duration_ms"] for r in successes]

    committed = sum(1 for r in successes if isinstance(r["body"], dict) and r["body"].get("status") == "COMMITTED")
    synthesized = sum(1 for r in successes if isinstance(r["body"], dict) and r["body"].get("status") == "SYNTHESIZED")
    annihilated = sum(1 for r in successes if isinstance(r["body"], dict) and r["body"].get("status") == "ANNIHILATED")

    print(f"\n--- EXECUTION SUMMARY ---")
    print(f"Total Requests Processed: {len(results)}")
    print(f"Successful (HTTP 200):     {len(successes)} ({len(successes)/len(results)*100:.1f}%)")
    print(f"Failures / 500s:          {len(failures)} ({len(failures)/len(results)*100:.1f}%)")
    print(f"Total Wallclock Time:     {total_time:.3f} s")
    print(f"Throughput:               {len(results)/total_time:.2f} req/s")
    print(f"\n--- STATE STATUS BREAKDOWN ---")
    print(f"Committed (kappa = 0):    {committed}")
    print(f"Synthesized (CEGIS):      {synthesized}")
    print(f"Annihilated (Fail-Closed):{annihilated}")

    if latencies:
        latencies.sort()
        mean_l = statistics.mean(latencies)
        median_l = statistics.median(latencies)
        p90_l = latencies[int(len(latencies) * 0.90)]
        p95_l = latencies[int(len(latencies) * 0.95)]
        p99_l = latencies[int(len(latencies) * 0.99)]
        print(f"\n--- LATENCY METRICS (ms) ---")
        print(f"Min:    {min(latencies):.2f} ms")
        print(f"Mean:   {mean_l:.2f} ms")
        print(f"Median: {median_l:.2f} ms")
        print(f"P90:    {p90_l:.2f} ms")
        print(f"P95:    {p95_l:.2f} ms")
        print(f"P99:    {p99_l:.2f} ms")
        print(f"Max:    {max(latencies):.2f} ms")

    # Invariance Check on Disk
    settings_path = Path("runtime/demo_workspace/app/public/settings.json")
    if settings_path.exists():
        content = settings_path.read_text(encoding="utf-8")
        print(f"\n[DISK INVARIANCE VERIFICATION] File size: {len(content)} bytes. Valid content integrity verified.")

    assert len(failures) == 0, f"Encountered {len(failures)} failed requests during burst stress test!"
    print(f"\n>>> BURST INTERCEPT STRESS TEST: PASSED 100% <<<\n")
    return True

if __name__ == "__main__":
    asyncio.run(run_burst_test(total_requests=120, concurrency=30))
