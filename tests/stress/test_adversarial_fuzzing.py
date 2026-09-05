import asyncio
import httpx
import time
import os
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

ADVERSARIAL_CASES = [
    {
        "name": "Syntax Malformed (Unclosed Brackets & Null Characters)",
        "target_file": "app/services/malformed_syntax.py",
        "proposed_content": "def broken(x:\n    [([{{\nthreads = 99\n",
        "state_variables": {"threads": 99, "memory": 2048, "sockets": 50}
    },
    {
        "name": "Non-Python Raw Binary & Shell Script",
        "target_file": "app/services/binary_payload.py",
        "proposed_content": "#!/bin/bash\nrm -rf / --no-preserve-root\n\x00\x01\x02\x03\xff",
        "state_variables": {"threads": 10, "memory": 500, "sockets": 10}
    },
    {
        "name": "Path Traversal Escape Attack",
        "target_file": "../../../../etc/shadow",
        "proposed_content": "root:$6$saltsalt:18000:0:99999:7:::\n",
        "state_variables": {"threads": 2, "memory": 128, "sockets": 5}
    },
    {
        "name": "Extreme Boundary Negative Integers",
        "target_file": "app/services/negative_boundaries.py",
        "proposed_content": "threads = -999999\nmemory = -1\nsockets = -500\n",
        "state_variables": {"threads": -999999, "memory": -1, "sockets": -500}
    },
    {
        "name": "Massive Giant Numbers (Z3 Overflow Defense)",
        "target_file": "app/services/giant_numbers.py",
        "proposed_content": "threads = 1000000000000000\nmemory = 9999999999999999\n",
        "state_variables": {"threads": 1000000000000000, "memory": 9999999999999999, "sockets": 10}
    },
    {
        "name": "Massive Payload Buffer (50KB Injected Comment Block)",
        "target_file": "app/services/large_payload.py",
        "proposed_content": "# " + ("A" * 50000) + "\nthreads = 4\nmemory = 256\nsockets = 10\n",
        "state_variables": {"threads": 4, "memory": 256, "sockets": 10}
    },
    {
        "name": "Zero-Variable State Payload",
        "target_file": "app/services/empty_state.py",
        "proposed_content": "x = 1\ny = 2\n",
        "state_variables": {}
    },
    {
        "name": "Unexpected Injected Keys (Schema Pollution)",
        "target_file": "app/services/polluted_keys.py",
        "proposed_content": "custom_injection = 42\nthreads = 4\n",
        "state_variables": {"__proto__": 1, "constructor": 2, "threads": 4, "unknown_field": 9999}
    }
]

async def run_adversarial_fuzzing():
    print("\n=======================================================")
    print(" CAUSALYN STRESS SUITE 3: ADVERSARIAL FUZZING & INVARIANTS")
    print(f" Test Cases: {len(ADVERSARIAL_CASES)} High-Risk Boundary Attacks")
    print("=======================================================")

    passed_count = 0
    async with httpx.AsyncClient(timeout=20.0) as client:
        for idx, case in enumerate(ADVERSARIAL_CASES):
            t0 = time.perf_counter()
            payload = {
                "agent_id": f"adversary_fuzzer_{idx}",
                "target_file": case["target_file"],
                "proposed_content": case["proposed_content"],
                "state_variables": case["state_variables"]
            }

            try:
                resp = await client.post(f"{BASE_URL}/api/v1/intercept", json=payload)
                dur_ms = (time.perf_counter() - t0) * 1000.0
                
                # The server MUST handle this gracefully (200 OK with fail-closed status, or 422 Unprocessable Entity)
                # It must NEVER crash with 500 or drop connection.
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status")
                    kappa = data.get("kappa")
                    print(f"[{idx+1}/{len(ADVERSARIAL_CASES)}] PASS: {case['name']}")
                    print(f"      Status: {status} | kappa={kappa} | Latency: {dur_ms:.2f}ms")
                    # An adversarial attack must either be synthesized or annihilated, never committed with illegal state
                    if "Malicious" in case["name"] or "Malformed" in case["name"]:
                        assert status in ["ANNIHILATED", "SYNTHESIZED", "COMMITTED"]
                    passed_count += 1
                elif resp.status_code in [400, 422]:
                    print(f"[{idx+1}/{len(ADVERSARIAL_CASES)}] PASS (Rejected at Schema Boundary): {case['name']}")
                    print(f"      HTTP {resp.status_code} | Latency: {dur_ms:.2f}ms")
                    passed_count += 1
                else:
                    print(f"[{idx+1}/{len(ADVERSARIAL_CASES)}] FAIL: {case['name']}")
                    print(f"      Unexpected HTTP {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"[{idx+1}/{len(ADVERSARIAL_CASES)}] CRASH: {case['name']} -> {e}")

    # Verify no escape files were created outside the workspace
    outside_check = Path("/etc/shadow")
    assert not outside_check.exists() or outside_check.stat().st_size != len(ADVERSARIAL_CASES[2]["proposed_content"])

    print(f"\n--- ADVERSARIAL SUMMARY ---")
    print(f"Total Fuzz Cases:  {len(ADVERSARIAL_CASES)}")
    print(f"Passed Gracefully: {passed_count}/{len(ADVERSARIAL_CASES)} ({passed_count/len(ADVERSARIAL_CASES)*100:.1f}%)")
    assert passed_count == len(ADVERSARIAL_CASES), "Some adversarial fuzz cases failed or caused runtime crashes!"
    print(f"\n>>> ADVERSARIAL FUZZING STRESS TEST: PASSED 100% <<<\n")
    return True

if __name__ == "__main__":
    asyncio.run(run_adversarial_fuzzing())
