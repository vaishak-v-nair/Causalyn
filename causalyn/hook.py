"""Claude Code hook implementation.

This module is invoked by the Claude Code hooks system.  It intercepts
tool-use events, creates git checkpoints, and on failure triggers the
full bisection → verification pipeline.

Usage as a Claude Code hook:
    The hooks/causalyn.json file registers this as a subcommand hook.
    Claude Code calls it with JSON on stdin describing the event.
"""

from __future__ import annotations

import json
import sys
import os
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .checkpoint import CheckpointEngine, CheckpointError
from .bisect import bisect, BisectionError
from .config import CausalynConfig
from .models import StepKind
from .verifier import verify_fix, VerificationError

console = Console(stderr=True)

# Module-level engine — initialized once per hook process lifetime.
_engine: CheckpointEngine | None = None


def get_engine(config: CausalynConfig | None = None) -> CheckpointEngine:
    """Get or create the singleton CheckpointEngine."""
    global _engine
    if _engine is None:
        config = config or CausalynConfig.from_env()
        _engine = CheckpointEngine(
            repo_dir=config.project_dir,
            branch=config.checkpoint_branch,
        )
        _engine.begin_session()
    return _engine


def handle_hook_event(event: dict[str, Any]) -> dict[str, Any]:
    """Process a single hook event from Claude Code.

    Claude Code hook events have this shape:
    {
        "hook_type": "PreToolUse" | "PostToolUse" | "OnError",
        "tool_name": "write_file" | "run_command" | ...,
        "tool_input": { ... },
        "tool_output": { ... },   // only for PostToolUse
        "error": "...",           // only for OnError
        "session_id": "...",
    }

    Returns a response dict.  For PreToolUse, returning
    {"decision": "block", "reason": "..."} blocks the tool call.
    Returning {"decision": "allow"} lets it proceed.
    """
    hook_type = event.get("hook_type", "")
    tool_name = event.get("tool_name", "")

    if hook_type == "PreToolUse":
        return _handle_pre_tool_use(event)
    elif hook_type == "PostToolUse":
        return _handle_post_tool_use(event)
    elif hook_type == "OnError":
        return _handle_on_error(event)
    else:
        return {"decision": "allow"}


def _handle_pre_tool_use(event: dict[str, Any]) -> dict[str, Any]:
    """Before a tool call — create a checkpoint of the current state."""
    tool_name = event.get("tool_name", "unknown")
    tool_input = event.get("tool_input", {})

    engine = get_engine()
    kind = _classify_tool(tool_name)
    description = _describe_tool_use(tool_name, tool_input)

    try:
        cp = engine.create(description=description, kind=kind)
        console.print(
            f"[dim]📸 Checkpoint {cp.step_id}: {description}[/dim]"
        )
    except CheckpointError as e:
        console.print(f"[yellow]⚠ Checkpoint failed: {e}[/yellow]")

    return {"decision": "allow"}


def _handle_post_tool_use(event: dict[str, Any]) -> dict[str, Any]:
    """After a tool call — record the result.  If it's a test failure,
    trigger bisection."""
    tool_name = event.get("tool_name", "")
    tool_output = event.get("tool_output", {})

    # Check if this was a test run that failed
    if tool_name in ("run_command", "bash") and _looks_like_test_failure(tool_output):
        test_command = _extract_test_command(event)
        if test_command:
            console.print(
                Panel(
                    "[bold red]Test failure detected — starting causal bisection...[/bold red]",
                    title="🔍 Causalyn",
                    border_style="red",
                )
            )
            return _run_bisection_and_verification(test_command, event)

    return {"decision": "allow"}


def _handle_on_error(event: dict[str, Any]) -> dict[str, Any]:
    """On error — log it.  If we can identify a test command, bisect."""
    error_msg = event.get("error", "Unknown error")
    console.print(f"[red]❌ Error intercepted: {error_msg}[/red]")
    return {"decision": "allow"}


def _run_bisection_and_verification(
    test_command: str, event: dict[str, Any]
) -> dict[str, Any]:
    """The full pipeline: bisect → report → verify."""
    engine = get_engine()

    try:
        result = bisect(engine, test_command)
    except BisectionError as e:
        console.print(f"[yellow]⚠ Bisection failed: {e}[/yellow]")
        return {"decision": "allow"}

    report = result.report

    # Print the causal report
    console.print()
    console.print(Panel(
        report.summary,
        title="📋 Causal Report",
        border_style="cyan",
        padding=(1, 2),
    ))

    if report.diff_at_root_cause:
        console.print(Panel(
            report.diff_at_root_cause[:2000],  # Truncate very long diffs
            title=f"🔧 Diff at {report.root_cause_step}",
            border_style="yellow",
        ))

    # Attempt cross-vendor verification
    config = CausalynConfig.from_env()
    proposed_fix = event.get("tool_output", {}).get("content", "")
    task_description = event.get("session_context", {}).get("task", "")

    if proposed_fix and config.get_api_key():
        try:
            verdict = verify_fix(
                proposed_fix=proposed_fix,
                report=report,
                task_description=task_description,
                config=config,
            )

            if verdict.agrees:
                console.print(Panel(
                    f"[green]✅ Independent model agrees: the fix addresses the root cause.[/green]\n"
                    f"Confidence: {verdict.confidence:.0%}\n"
                    f"Model: {verdict.model_used}",
                    title="🛡️ Verification Verdict",
                    border_style="green",
                ))
            else:
                concerns_text = "\n".join(f"  • {c}" for c in verdict.concerns)
                console.print(Panel(
                    f"[red]⚠ Independent model disagrees:[/red]\n"
                    f"{concerns_text}\n\n"
                    f"[yellow]Recommendation:[/yellow] {verdict.recommendation}\n"
                    f"Confidence: {verdict.confidence:.0%}\n"
                    f"Model: {verdict.model_used}",
                    title="🛡️ Verification Verdict",
                    border_style="red",
                ))
        except VerificationError as e:
            console.print(f"[yellow]⚠ Verification skipped: {e}[/yellow]")
    else:
        console.print(
            "[dim]ℹ Verification skipped (no API key configured or no fix to verify)[/dim]"
        )

    return {"decision": "allow"}


def _classify_tool(tool_name: str) -> StepKind:
    """Map a Claude Code tool name to a StepKind."""
    if tool_name in ("write_file", "edit_file", "create_file"):
        return StepKind.FILE_WRITE
    elif tool_name in ("delete_file",):
        return StepKind.FILE_DELETE
    elif tool_name in ("run_command", "bash", "execute"):
        return StepKind.COMMAND_RUN
    elif tool_name in ("run_tests", "test"):
        return StepKind.TEST_RUN
    return StepKind.UNKNOWN


def _describe_tool_use(tool_name: str, tool_input: dict) -> str:
    """Create a human-readable description of a tool use event."""
    if tool_name in ("write_file", "edit_file", "create_file"):
        path = tool_input.get("path", tool_input.get("file_path", "unknown file"))
        return f"{tool_name}: {path}"
    elif tool_name in ("run_command", "bash"):
        cmd = tool_input.get("command", "unknown command")
        # Truncate long commands
        if len(cmd) > 80:
            cmd = cmd[:77] + "..."
        return f"run: {cmd}"
    return f"{tool_name}"


def _looks_like_test_failure(tool_output: dict | str) -> bool:
    """Heuristic: does this tool output look like a test failure?"""
    if isinstance(tool_output, str):
        text = tool_output
    elif isinstance(tool_output, dict):
        text = tool_output.get("content", "") or tool_output.get("stderr", "")
    else:
        return False

    failure_indicators = [
        "FAILED",
        "ERRORS",
        "AssertionError",
        "Error:",
        "Traceback (most recent call last)",
        "pytest",
        "FAIL:",
        "error:",
        "exit code 1",
        "exit status 1",
    ]
    return any(indicator in text for indicator in failure_indicators)


def _extract_test_command(event: dict[str, Any]) -> str:
    """Try to extract the test command from a tool-use event."""
    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "")
    if command and any(kw in command for kw in ["pytest", "test", "npm test", "cargo test"]):
        return command
    return ""


def run_hook_stdin() -> None:
    """Entry point for the Claude Code hook: read JSON from stdin, process, write response to stdout."""
    raw = sys.stdin.read()
    if not raw.strip():
        json.dump({"decision": "allow"}, sys.stdout)
        return

    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    response = handle_hook_event(event)
    json.dump(response, sys.stdout)
