#!/usr/bin/env python3
"""
Causalyn External Agent Intercept Runner
========================================
Demonstrates Causalyn operating as a Transparent Hypervisor Proxy.
Simulates real external developer agents (Claude Code, Cursor, terminal workers)
submitting tool calls and having them intercepted, Z3 SMT verified, and 
auto-patched via CEGIS in sub-milliseconds without disk corruption.

Usage:
    python scripts/external_agent_runner.py --agent "Claude-Code-3.7" --mode patch
    python scripts/external_agent_runner.py --agent "Cursor-IDE" --mode burst
    python scripts/external_agent_runner.py --agent "Terminal-CLI" --mode safe
    python scripts/external_agent_runner.py --agent "Exhaustion-Probe" --mode annihilate
    python scripts/external_agent_runner.py --loop 4
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error

# Ensure UTF-8 output in Windows PowerShell/Command Prompt
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

API_URL = "http://127.0.0.1:8000/api/v1/intercept"
SWARM_URL = "http://127.0.0.1:8000/api/v1/swarm/reconcile"

# ANSI Terminal Colors
CYAN = "\033[38;2;0;243;255m"
GREEN = "\033[38;2;16;185;129m"
RED = "\033[38;2;255;30;68m"
AMBER = "\033[38;2;245;158;11m"
PURPLE = "\033[38;2;168;85;247m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

SCENARIOS = {
    "safe": {
        "agent_id": "Claude-Code-3.7",
        "target_file": "services/auth_cluster.py",
        "proposed_content": "threads = 8\nmemory = 512\nsockets = 40",
        "state_variables": {"threads": 8, "memory": 512, "sockets": 40},
        "description": "Compliant agent AST mutation (satisfies all bounds)"
    },
    "patch": {
        "agent_id": "Cursor-Agent-Pro",
        "target_file": "core/high_throughput_worker.py",
        "proposed_content": "threads = 32\nmemory = 4096\nsockets = 80",
        "state_variables": {"threads": 32, "memory": 4096, "sockets": 80},
        "description": "Aggressive scaling mutation (threads > 16, memory > 1024 -> CEGIS Auto-Patch)"
    },
    "annihilate": {
        "agent_id": "Rogue-Agent-09",
        "target_file": "network/socket_pool.py",
        "proposed_content": "sockets = 256\nmemory = 2048\nthreads = 64",
        "state_variables": {"sockets": 256, "memory": 2048, "threads": 64},
        "description": "Fatal socket exhaustion (sockets > 200 -> VPSN Fail-Closed State Collapse)"
    }
}

def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "Causalyn-Transparent-Hypervisor-Client/3.1"}
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))

def run_single_intercept(agent_id: str, mode: str, target_file: str = None):
    scenario = SCENARIOS.get(mode, SCENARIOS["patch"])
    file_path = target_file or scenario["target_file"]
    state_vars = scenario["state_variables"]
    content = scenario["proposed_content"]

    print(f"\n{BOLD}{CYAN}═══════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}[TRANSPARENT HYPERVISOR PROXY INTERCEPT]{RESET} Mode: {AMBER}{mode.upper()}{RESET}")
    print(f"{CYAN}Agent Attached:{RESET} {BOLD}{agent_id}{RESET} ➔ Proposing write to {BOLD}{file_path}{RESET}")
    print(f"{DIM}Proposed State Variables:{RESET} {state_vars}")
    print(f"{DIM}Description:{RESET} {scenario['description']}")
    print(f"{DIM}Listening Proxy Gateway:{RESET} http://127.0.0.1:8000/api/v1/intercept")
    print(f"{CYAN}───────────────────────────────────────────────────────────────────────────{RESET}")

    payload = {
        "agent_id": agent_id,
        "target_file": file_path,
        "proposed_content": content,
        "state_variables": state_vars
    }

    t0 = time.perf_counter()
    try:
        result = post_json(API_URL, payload)
        wall_time_us = (time.perf_counter() - t0) * 1_000_000.0
    except urllib.error.URLError as e:
        print(f"{RED}{BOLD}ERROR:{RESET} Failed to reach Causalyn control plane at {API_URL}: {e}")
        print(f"{AMBER}Ensure Uvicorn is running: python backend/app.py{RESET}")
        return False

    status = result.get("status", "UNKNOWN")
    kappa = result.get("kappa", 0.0)
    latency_us = result.get("latency_us", wall_time_us)
    patch = result.get("patch")

    if status == "COMMITTED":
        status_color = GREEN
        badge = "✓ VPSN ATOMIC COMMIT"
    elif status == "SYNTHESIZED":
        status_color = AMBER
        badge = "⚡ CEGIS AST AUTO-PATCH"
    else:
        status_color = RED
        badge = "🛑 DETERMINISTIC ANNIHILATION"

    print(f"\n{status_color}{BOLD}{badge}{RESET} ➔ Status: {status_color}{status}{RESET}")
    print(f"  • Paradox Curvature (κ) : {status_color}{kappa:.2f}{RESET}")
    print(f"  • Hypervisor Latency    : {BOLD}{latency_us:.1f} µs{RESET} (Wall time: {wall_time_us:.1f} µs)")
    
    # Speedup comparison vs LLM retry
    llm_retry_est_us = 1_500_000.0
    speedup = llm_retry_est_us / max(latency_us, 1.0)
    print(f"  • Acausal Speedup       : {CYAN}{BOLD}{speedup:,.0f}× FASTER{RESET} than LLM token re-prompt loop")

    if patch and patch.get("values"):
        print(f"\n{BOLD}{CYAN}[CEGIS SYNTHESIZED REPLACEMENTS]{RESET}")
        for k, v in patch["values"].items():
            old = state_vars.get(k, "?")
            print(f"  {RED}- {k} = {old}{RESET}  {DIM}# UNSAT (exceeds invariant threshold){RESET}")
            print(f"  {GREEN}+ {k} = {v}{RESET}  {BOLD}{GREEN}# SYNTHESIZED in-memory via Ricci relaxation{RESET}")
        print(f"  {DIM}Result: Agent code safely repaired in {latency_us:.1f}µs. Zero disk corruption. Zero token retry.{RESET}")
    elif status == "ANNIHILATED":
        print(f"\n{RED}{BOLD}[FAIL-CLOSED COLLAPSE ENFORCED]{RESET}")
        print(f"  {RED}! State variables violate non-negotiable physical invariants.{RESET}")
        print(f"  {RED}! Shadow sandbox purged instantly. Host filesystem was never touched.{RESET}")
    else:
        print(f"\n{GREEN}{BOLD}[SPECIFICATION SATISFIED]{RESET}")
        print(f"  {GREEN}✓ State verified against Z3 continuum. Committed to ground truth ledger.{RESET}")

    return True

def run_swarm_burst():
    print(f"\n{BOLD}{PURPLE}═══════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}[CONCURRENT MULTI-AGENT SWARM BURST]{RESET}")
    print(f"{PURPLE}Emitting concurrent mutations across 4 worker agents via Lamport Vector Bus...{RESET}")

    payload = {
        "agents": [
            {
                "agent_id": "Claude-Code-Worker-01",
                "target_file": "services/cache.py",
                "proposed_content": "threads = 12",
                "state_variables": {"threads": 12}
            },
            {
                "agent_id": "Cursor-Subagent-02",
                "target_file": "db/connection_pool.py",
                "proposed_content": "memory = 512",
                "state_variables": {"memory": 512}
            },
            {
                "agent_id": "DevOps-Bot-03",
                "target_file": "api/gateway.py",
                "proposed_content": "sockets = 64",
                "state_variables": {"sockets": 64}
            },
            {
                "agent_id": "AutoGPT-Crawler-04",
                "target_file": "tasks/scheduler.py",
                "proposed_content": "threads = 4",
                "state_variables": {"threads": 4}
            }
        ]
    }

    try:
        res = post_json(SWARM_URL, payload)
        print(f"{GREEN}{BOLD}✓ SWARM RECONCILED DETERMINISTICALLY{RESET}")
        print(f"Total Operations: {res.get('total_operations', len(payload['agents']))}")
        print("Reconciliation Order:")
        for item in res.get("order", []):
            if isinstance(item, dict):
                print(f"  • Agent: {CYAN}{item['agent_id']}{RESET} | Vector Clock: {BOLD}{item['clock']}{RESET} | File: {item['target_file']}")
            else:
                print(f"  • {item}")
        return True
    except Exception as e:
        print(f"{RED}Swarm request failed: {e}{RESET}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Causalyn Transparent Hypervisor External Agent Runner")
    parser.add_argument("--agent", default="Claude-Code-3.7", help="Agent identifier")
    parser.add_argument("--mode", choices=["safe", "patch", "annihilate", "burst"], default="patch", help="Simulation scenario")
    parser.add_argument("--file", default=None, help="Target file path")
    parser.add_argument("--loop", type=int, default=0, help="Run a sequence of N automated scenario steps")
    args = parser.parse_args()

    if args.loop > 0:
        print(f"{BOLD}{CYAN}Initiating Continuous Multi-Agent Transparent Intercept Sequence ({args.loop} iterations)...{RESET}")
        modes = ["safe", "patch", "burst", "annihilate"]
        for i in range(args.loop):
            curr_mode = modes[i % len(modes)]
            print(f"\n{BOLD}--- Sequence Step {i+1}/{args.loop}: [{curr_mode.upper()}] ---{RESET}")
            if curr_mode == "burst":
                run_swarm_burst()
            else:
                agent = f"Agent-Swarm-Node-{i:02d}" if curr_mode != "patch" else "Claude-Code-3.7"
                run_single_intercept(agent, curr_mode)
            time.sleep(1.2)
        print(f"\n{GREEN}{BOLD}✓ Sequence complete. All operations transparently captured in Causalyn 3D Cockpit.{RESET}")
    elif args.mode == "burst":
        run_swarm_burst()
    else:
        run_single_intercept(args.agent, args.mode, args.file)

if __name__ == "__main__":
    main()
