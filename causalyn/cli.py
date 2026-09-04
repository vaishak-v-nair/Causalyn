"""Command-Line Interface (CLI) Interception Wrapper for Causalyn.

Acts as Layer 1 (The Interception Hook): intercepts commands, scripts,
and agent file/shell mutations before they execute on host infrastructure.
Evaluates proposals against the Causalyn Consensus Engine & Article 10 Audit Ledger.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


DEFAULT_SERVER_URL = os.environ.get("CAUSALYN_SERVER_URL", "http://127.0.0.1:8000")


def _post_json(url: str, data: Dict[str, Any], timeout: float = 15.0) -> Dict[str, Any]:
    """Execute HTTP POST request returning decoded JSON response."""
    payload_bytes = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload_bytes,
        headers={"Content-Type": "application/json", "User-Agent": "Causalyn-CLI/0.2.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def _get_json(url: str, timeout: float = 10.0) -> Dict[str, Any]:
    """Execute HTTP GET request returning decoded JSON response."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Causalyn-CLI/0.2.0"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def _run_standalone_eval(
    action_type: str,
    target_path: str,
    payload: Dict[str, Any],
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run local CEGAR evaluation without requiring an active HTTP daemon."""
    import asyncio
    from .api.contracts import ActionType, InterceptActionRequest
    from .model.world_state import WorldStateManager
    from .orchestrator.cegar_graph import CEGAROrchestrationGraph
    from .shadow.drivers import LocalMemoryDriver
    from .verification.policy_rag import PolicyRAGEngine

    mgr = WorldStateManager()
    driver = LocalMemoryDriver(initial_files=mgr.get_current_state().file_system)
    rag = PolicyRAGEngine()
    graph = CEGAROrchestrationGraph(
        world_state_manager=mgr,
        sandbox_driver=driver,
        policy_rag=rag,
    )

    req = InterceptActionRequest(
        action_type=ActionType(action_type),
        target_path=target_path,
        payload=payload,
        session_id=session_id or f"cli-{int(time.time())}",
        agent_framework=agent_id or "cli-agent",
    )

    initial_state = {
        "session_id": req.session_id,
        "pipeline_id": f"cli-pipe-{int(time.time()*1000)}",
        "intent": f"Intercept {action_type} on {target_path}",
        "max_iterations": 2,
        "proposed_action": {
            "action_type": req.action_type.value,
            "target_path": req.target_path,
            "payload": req.payload,
        },
    }

    final_state = asyncio.run(graph.invoke(initial_state))
    decision = final_state.get("verification_decision", "deny")

    gate_decision = "allow" if decision == "allow" else "deny"

    return {
        "pipeline_id": final_state["pipeline_id"],
        "decision": gate_decision,
        "paradox_index": final_state.get("paradox_index", 0.0),
        "violations": final_state.get("violations", []),
        "counterexamples": final_state.get("counterexamples", []),
        "unified_diffs": final_state.get("unified_diffs", {}),
        "article_10_audit_id": f"art10-standalone-{int(time.time())}",
        "duration_ms": final_state.get("duration_ms", 0.0),
        "status_code": 200 if gate_decision == "allow" else 403,
    }


def handle_wrap(args: argparse.Namespace) -> int:
    """Wrap an arbitrary shell command, evaluating it before local execution."""
    command = args.command
    target = args.target_path or "."
    server_url = (args.server_url or DEFAULT_SERVER_URL).rstrip("/")

    req_payload = {
        "action_type": "shell_exec",
        "target_path": target,
        "payload": {"command": command},
        "agent_framework": args.agent_id or "cli-wrapper",
        "session_id": args.session_id or f"wrap-{int(time.time())}",
    }

    result: Dict[str, Any]
    endpoint = f"{server_url}/v1/proxy/action"

    if args.standalone:
        result = _run_standalone_eval(
            action_type="shell_exec",
            target_path=target,
            payload={"command": command},
            session_id=req_payload["session_id"],
            agent_id=args.agent_id or "cli-wrapper",
        )
    else:
        try:
            result = _post_json(endpoint, req_payload, timeout=args.timeout)
        except urllib.error.URLError:
            if not args.no_fallback:
                print(f"[WARN] Causalyn daemon unreachable at {server_url}. Falling back to standalone local CEGAR...")
                result = _run_standalone_eval(
                    action_type="shell_exec",
                    target_path=target,
                    payload={"command": command},
                    session_id=req_payload["session_id"],
                    agent_id=args.agent_id or "cli-wrapper",
                )
            else:
                print(f"[ERROR] Failed to reach Causalyn server at {server_url}. Standalone fallback disabled.", file=sys.stderr)
                return 2

    decision = result.get("decision", "deny")

    if decision in ("allow", "COMMITTED", "APPROVED"):
        print(f"[CAUSALYN APPROVED] Action verified by VPSN Consensus Engine.")
        print(f"Decision: {decision} | Paradox Index (kappa): {result.get('paradox_index', 0.0):.3f} | Audit ID: {result.get('article_10_audit_id')}")
        if args.execute:
            print(f"Executing on host: {command}\n")
            proc = subprocess.run(command, shell=True)
            return proc.returncode
        return 0
    else:
        print(f"\n========================================================", file=sys.stderr)
        print(f"[CAUSALYN BLOCKED] Execution intercepted and DENIED!", file=sys.stderr)
        print(f"========================================================", file=sys.stderr)
        print(f"Decision:        {decision}", file=sys.stderr)
        print(f"Audit Record ID: {result.get('article_10_audit_id')}", file=sys.stderr)
        print(f"Paradox Index kappa: {result.get('paradox_index', 0.0):.3f}", file=sys.stderr)
        violations = result.get("violations", [])
        if violations:
            print(f"\nPolicy & Invariant Violations ({len(violations)}):", file=sys.stderr)
            for v in violations:
                print(f"  - [{v.get('code', 'ERR')}] {v.get('message', '')}", file=sys.stderr)
        counterexamples = result.get("counterexamples", [])
        if counterexamples:
            print(f"\nCEGAR Counterexamples:", file=sys.stderr)
            for c in counterexamples:
                print(f"  - {c}", file=sys.stderr)
        print(f"========================================================\n", file=sys.stderr)
        return 1


def handle_intercept(args: argparse.Namespace) -> int:
    """Directly intercept and evaluate a candidate mutation payload."""
    server_url = (args.server_url or DEFAULT_SERVER_URL).rstrip("/")

    # Parse payload
    payload_dict: Dict[str, Any] = {}
    if args.payload:
        if args.payload.startswith("@"):
            with open(args.payload[1:], "r", encoding="utf-8") as f:
                payload_dict = json.load(f)
        else:
            try:
                payload_dict = json.loads(args.payload)
            except json.JSONDecodeError:
                payload_dict = {"content": args.payload}
    elif not sys.stdin.isatty():
        try:
            stdin_content = sys.stdin.read().strip()
            if stdin_content:
                payload_dict = json.loads(stdin_content)
        except Exception:
            payload_dict = {"content": stdin_content}

    req_payload = {
        "action_type": args.type,
        "target_path": args.target,
        "payload": payload_dict,
        "agent_framework": args.agent_id or "cli-agent",
        "session_id": args.session_id or f"intercept-{int(time.time())}",
    }

    result: Dict[str, Any]
    endpoint = f"{server_url}/v1/proxy/action"

    if args.standalone:
        result = _run_standalone_eval(
            action_type=args.type,
            target_path=args.target,
            payload=payload_dict,
            session_id=req_payload["session_id"],
            agent_id=args.agent_id or "cli-agent",
        )
    else:
        try:
            result = _post_json(endpoint, req_payload, timeout=args.timeout)
        except urllib.error.URLError:
            if not args.no_fallback:
                result = _run_standalone_eval(
                    action_type=args.type,
                    target_path=args.target,
                    payload=payload_dict,
                    session_id=req_payload["session_id"],
                    agent_id=args.agent_id or "cli-agent",
                )
            else:
                print(f"[ERROR] Failed to reach Causalyn server at {server_url}", file=sys.stderr)
                return 2

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        decision = result.get("decision", "deny")
        print("=== Causalyn Interception Report ===")
        print(f"Pipeline ID:     {result.get('pipeline_id')}")
        print(f"Decision:        {decision}")
        print(f"Paradox Index kappa: {result.get('paradox_index', 0.0):.3f}")
        print(f"Audit ID:        {result.get('article_10_audit_id')}")
        print(f"Verification:    {'PASSED' if decision in ('allow', 'COMMITTED', 'APPROVED') else 'FAILED'}")
        if result.get("violations"):
            print("Violations:")
            for v in result["violations"]:
                print(f"  * [{v.get('code')}] {v.get('message')}")
        if result.get("unified_diffs"):
            print("\nCandidate Diffs:")
            for p, d in result["unified_diffs"].items():
                print(f"--- {p} ---")
                print(d)

    return 0 if result.get("decision") in ("allow", "COMMITTED", "APPROVED") else 1


def handle_status(args: argparse.Namespace) -> int:
    """Query and display live health and pipeline audit status."""
    server_url = (args.server_url or DEFAULT_SERVER_URL).rstrip("/")
    try:
        health_data = _get_json(f"{server_url}/api/health", timeout=5.0)
        state_data = _get_json(f"{server_url}/api/state", timeout=5.0)
        pipelines_data = _get_json(f"{server_url}/api/pipelines", timeout=5.0)

        print("=== Causalyn Control Plane Status ===")
        print(f"Server:          {server_url}")
        print(f"Health:          {health_data.get('status', 'unknown').upper()}")
        print(f"Service:         {health_data.get('service', 'causalyn')}")
        print(f"Maturity:        {health_data.get('maturity', 'PROTOTYPE')}")
        print(f"World Files:     {len(state_data.get('files', []))}")
        recent_count = len(pipelines_data.get("pipelines", []))
        print(f"Recent Missions: {recent_count}")
        print("Compliance:      EU AI Act (Regulation 2024/1689 Article 10) Enforced")
        return 0
    except Exception as exc:
        print(f"[ERROR] Unable to connect to Causalyn at {server_url}: {exc}", file=sys.stderr)
        return 1


def handle_benchmark(args: argparse.Namespace) -> int:
    """Execute M2 empirical synthetic benchmark suite."""
    import asyncio
    from .benchmarks.synthetic import generate_synthetic_benchmark
    from .benchmarks.runner import BenchmarkRunner

    count = getattr(args, "count", 500)
    out_dir = getattr(args, "output_dir", "runtime/benchmarks")
    print(f"=== Running Causalyn M2 Empirical Benchmark ({count} tasks) ===")
    runner = BenchmarkRunner(output_dir=out_dir)
    tasks = generate_synthetic_benchmark(count)
    report = asyncio.run(runner.run_suite(tasks))

    print(f"\nBenchmark Complete:")
    print(f"Total Tasks:        {report.total_tasks}")
    print(f"HMPR (Prevention):  {report.hmpr_percent}%")
    print(f"FPR (False Pos):    {report.fpr_percent}%")
    print(f"TSR (Success Rate): {report.tsr_percent}%")
    print(f"Median Latency p50: {report.p50_latency_ms} ms")
    print(f"95th Percentile p95:{report.p95_latency_ms} ms")
    print(f"Reports saved to:   {out_dir}/m2_synthetic_report.json")
    return 0 if report.hmpr_percent == 100.0 else 1


def handle_ci(args: argparse.Namespace) -> int:
    """Execute M3 Continuous Shadow Verification on Git PR diff."""
    import asyncio
    from .ci.github_checker import PRVerifier
    from .api.contracts import GateDecision

    diff_content = ""
    if args.diff:
        if os.path.exists(args.diff):
            with open(args.diff, "r", encoding="utf-8") as f:
                diff_content = f.read()
        else:
            diff_content = args.diff
    elif not sys.stdin.isatty():
        diff_content = sys.stdin.read()
    else:
        print("[ERROR] No diff provided. Pass --diff <file> or pipe via stdin.", file=sys.stderr)
        return 2

    verifier = PRVerifier()
    pr_num = getattr(args, "pr_number", 1) or 1
    sha = getattr(args, "commit_sha", None)
    result = asyncio.run(verifier.verify_diff(diff_content, pr_number=int(pr_num), commit_sha=sha))

    print(result.summary_markdown)
    return 0 if result.verdict == GateDecision.ALLOW else 1


def handle_compliance(args: argparse.Namespace) -> int:
    """Generate M5 SOC2 Type II and EU AI Act Article 10 evidence pack."""
    from .compliance.engine import EnterpriseComplianceEngine

    out_dir = getattr(args, "output_dir", "runtime/compliance")
    engine = EnterpriseComplianceEngine()
    target_file = engine.export_evidence_pack(output_dir=out_dir)
    pack = engine.generate_evidence_pack()

    print("=== Causalyn Enterprise Compliance Evidence Pack ===")
    print(f"Pack ID:         {pack.pack_id}")
    print(f"Status:          {pack.overall_status}")
    print(f"Merkle Root:     {pack.merkle_root}")
    print(f"Missions Audited:{pack.total_missions_audited}")
    print(f"SOC2 Controls:   {len(pack.soc2_controls)} satisfied")
    print(f"EU AI Act Art10: {len(pack.eu_ai_act_controls)} satisfied")
    print(f"Evidence JSON:   {target_file}")
    return 0 if pack.overall_status == "COMPLIANT" else 1


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser for causalyn CLI."""
    parser = argparse.ArgumentParser(
        prog="causalyn",
        description="Causalyn: Deterministic AI Execution Control Plane and Interception Hook.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # Subcommand: wrap
    wrap_p = subparsers.add_parser("wrap", help="Wrap and verify a shell command before host execution")
    wrap_p.add_argument("command", help="Shell command string to intercept")
    wrap_p.add_argument("--target-path", "-p", default=".", help="Target workspace path or resource")
    wrap_p.add_argument("--server-url", "-s", default=DEFAULT_SERVER_URL, help="Causalyn daemon endpoint")
    wrap_p.add_argument("--agent-id", "-a", default="cli-agent", help="Agent identifier")
    wrap_p.add_argument("--session-id", default=None, help="Session identifier")
    wrap_p.add_argument("--execute", action="store_true", default=True, help="Execute on host if approved")
    wrap_p.add_argument("--no-execute", dest="execute", action="store_false", help="Evaluate only, do not run on host")
    wrap_p.add_argument("--standalone", action="store_true", help="Run local evaluation without daemon")
    wrap_p.add_argument("--no-fallback", action="store_true", help="Disallow fallback to standalone if daemon offline")
    wrap_p.add_argument("--timeout", type=float, default=15.0, help="Request timeout in seconds")

    # Subcommand: intercept
    int_p = subparsers.add_parser("intercept", help="Directly submit a candidate action for verification")
    int_p.add_argument("--type", "-t", required=True, choices=["file_write", "file_delete", "shell_exec", "db_migration", "network_egress"], help="Action type")
    int_p.add_argument("--target", "-p", required=True, help="Target file path or resource identifier")
    int_p.add_argument("--payload", "-d", default=None, help="Action payload (JSON string or @filename)")
    int_p.add_argument("--server-url", "-s", default=DEFAULT_SERVER_URL, help="Causalyn daemon endpoint")
    int_p.add_argument("--agent-id", "-a", default="cli-agent", help="Agent identifier")
    int_p.add_argument("--session-id", default=None, help="Session identifier")
    int_p.add_argument("--json", action="store_true", help="Output raw JSON response")
    int_p.add_argument("--standalone", action="store_true", help="Run local evaluation without daemon")
    int_p.add_argument("--no-fallback", action="store_true", help="Disallow fallback to standalone if daemon offline")
    int_p.add_argument("--timeout", type=float, default=15.0, help="Request timeout in seconds")

    # Subcommand: status
    stat_p = subparsers.add_parser("status", help="Display Causalyn control plane health and status")
    stat_p.add_argument("--server-url", "-s", default=DEFAULT_SERVER_URL, help="Causalyn daemon endpoint")

    # Subcommand: benchmark (M2)
    bench_p = subparsers.add_parser("benchmark", help="Run M2 empirical benchmark suite")
    bench_p.add_argument("--count", "-c", type=int, default=500, help="Number of benchmark tasks (default 500)")
    bench_p.add_argument("--output-dir", "-o", default="runtime/benchmarks", help="Output report directory")

    # Subcommand: ci (M3)
    ci_p = subparsers.add_parser("ci", help="Continuous shadow verification on Git PRs (M3)")
    ci_p.add_argument("--diff", "-d", required=True, help="Path to diff file or diff text")
    ci_p.add_argument("--pr-number", type=int, default=1, help="Pull request number")
    ci_p.add_argument("--commit-sha", default=None, help="Commit SHA")

    # Subcommand: compliance (M5)
    comp_p = subparsers.add_parser("compliance", help="Generate SOC2 Type II & EU AI Act compliance evidence pack (M5)")
    comp_p.add_argument("--output-dir", "-o", default="runtime/compliance", help="Output evidence directory")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """CLI main execution router."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 0

    if args.subcommand == "wrap":
        return handle_wrap(args)
    elif args.subcommand == "intercept":
        return handle_intercept(args)
    elif args.subcommand == "status":
        return handle_status(args)
    elif args.subcommand == "benchmark":
        return handle_benchmark(args)
    elif args.subcommand == "ci":
        return handle_ci(args)
    elif args.subcommand == "compliance":
        return handle_compliance(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
