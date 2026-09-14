import asyncio
import time
import sys
from test_burst_intercept import run_burst_test
from test_burst_swarm_crdt import run_swarm_crdt_stress
from test_adversarial_fuzzing import run_adversarial_fuzzing
from test_websocket_stream_stress import run_websocket_stress

async def main():
    t_start = time.perf_counter()
    print("\n" + "=" * 70)
    print("      CAUSALYN COMPLETE SYSTEM PRESSURE & STRESS BENCHMARK")
    print("=" * 70)

    # Suite 1: Burst Intercept
    s1_ok = await run_burst_test(total_requests=120, concurrency=30)
    assert s1_ok, "Suite 1 Failed!"

    # Suite 2: Swarm CRDT
    s2_ok = await run_swarm_crdt_stress(total_batches=60, concurrency=20, agents_per_batch=15)
    assert s2_ok, "Suite 2 Failed!"

    # Suite 3: Adversarial Fuzzing
    s3_ok = await run_adversarial_fuzzing()
    assert s3_ok, "Suite 3 Failed!"

    # Suite 4: WebSocket Multiplexing
    s4_ok = await run_websocket_stress(num_clients=25, broadcast_duration=2.0)
    assert s4_ok, "Suite 4 Failed!"

    total_duration = time.perf_counter() - t_start
    print("\n" + "=" * 70)
    print("  >>> ALL 4 BACKEND PRESSURE TEST SUITES PASSED FLAWLESSLY <<<")
    print(f"  Total Benchmark Execution Time: {total_duration:.2f} seconds")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
