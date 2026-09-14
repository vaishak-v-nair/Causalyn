"""MCP server exposing Causalyn tools to any MCP-compatible client.

Tools:
- create_checkpoint: Snapshot the current working tree
- list_checkpoints: List all checkpoints in the session
- bisect_failure: Run causal bisection for a test failure
- verify_fix: Send a proposed fix for cross-vendor verification
- get_report: Get the latest causal report
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .checkpoint import CheckpointEngine, CheckpointError
from .bisect import bisect, BisectionError
from .config import CausalynConfig
from .models import StepKind
from .verifier import verify_fix as _verify_fix, VerificationError

app = Server("causalyn-mcp")

# Session state — initialized on first tool call
_engine: CheckpointEngine | None = None
_latest_report: dict | None = None


def _get_engine() -> CheckpointEngine:
    global _engine
    if _engine is None:
        config = CausalynConfig.from_env()
        _engine = CheckpointEngine(
            repo_dir=config.project_dir,
            branch=config.checkpoint_branch,
        )
        _engine.begin_session()
    return _engine


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="create_checkpoint",
            description=(
                "Create a git-based checkpoint of the current working tree. "
                "Call this before each meaningful agent step."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Human-readable description of what this step does.",
                    },
                    "step_id": {
                        "type": "string",
                        "description": "Optional custom step ID. Auto-generated if omitted.",
                    },
                    "kind": {
                        "type": "string",
                        "enum": ["file_write", "file_delete", "command_run", "test_run", "unknown"],
                        "description": "What kind of action this step represents.",
                    },
                },
            },
        ),
        types.Tool(
            name="list_checkpoints",
            description="List all checkpoints in the current session.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="bisect_failure",
            description=(
                "Run causal bisection to find the first step that caused a test failure. "
                "Produces a plain-language causal report."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "test_command": {
                        "type": "string",
                        "description": "The test command to run (e.g. 'pytest tests/'). Must exit 0 on success, non-zero on failure.",
                    },
                },
                "required": ["test_command"],
            },
        ),
        types.Tool(
            name="verify_fix",
            description=(
                "Send a proposed fix to an independent model from a different vendor "
                "for verification. Requires a prior bisect_failure call."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "proposed_fix": {
                        "type": "string",
                        "description": "The diff or code of the proposed fix.",
                    },
                    "task_description": {
                        "type": "string",
                        "description": "What the agent was originally trying to accomplish.",
                    },
                },
                "required": ["proposed_fix"],
            },
        ),
        types.Tool(
            name="get_report",
            description="Retrieve the latest causal report from the most recent bisection.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    global _latest_report

    if name == "create_checkpoint":
        engine = _get_engine()
        kind_str = arguments.get("kind", "unknown")
        try:
            kind = StepKind(kind_str)
        except ValueError:
            kind = StepKind.UNKNOWN

        try:
            cp = engine.create(
                description=arguments.get("description", ""),
                kind=kind,
                step_id=arguments.get("step_id"),
            )
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "ok",
                    "step_id": cp.step_id,
                    "git_sha": cp.git_sha,
                    "files_changed": cp.files_changed,
                }),
            )]
        except CheckpointError as e:
            return [types.TextContent(type="text", text=json.dumps({"status": "error", "message": str(e)}))]

    elif name == "list_checkpoints":
        engine = _get_engine()
        checkpoints = engine.list_all()
        data = [
            {
                "step_id": cp.step_id,
                "step_index": cp.step_index,
                "git_sha": cp.git_sha[:8],
                "description": cp.description,
                "kind": cp.kind.value,
                "files_changed": cp.files_changed,
            }
            for cp in checkpoints
        ]
        return [types.TextContent(type="text", text=json.dumps({"checkpoints": data}))]

    elif name == "bisect_failure":
        test_command = arguments.get("test_command", "")
        if not test_command:
            return [types.TextContent(type="text", text=json.dumps({"status": "error", "message": "test_command is required"}))]

        engine = _get_engine()
        try:
            result = bisect(engine, test_command)
        except BisectionError as e:
            return [types.TextContent(type="text", text=json.dumps({"status": "error", "message": str(e)}))]

        report_data = result.report.model_dump(mode="json")
        _latest_report = report_data

        return [types.TextContent(type="text", text=json.dumps({
            "status": "ok",
            "first_breaking_step": result.first_breaking_step,
            "last_good_step": result.last_good_step,
            "steps_tested": result.steps_tested,
            "total_checkpoints": result.total_checkpoints,
            "report": report_data,
        }))]

    elif name == "verify_fix":
        proposed_fix = arguments.get("proposed_fix", "")
        task_description = arguments.get("task_description", "")

        if not proposed_fix:
            return [types.TextContent(type="text", text=json.dumps({"status": "error", "message": "proposed_fix is required"}))]

        if not _latest_report:
            return [types.TextContent(type="text", text=json.dumps({
                "status": "error",
                "message": "No causal report available. Run bisect_failure first.",
            }))]

        from .models import CausalReport
        report = CausalReport(**_latest_report)

        config = CausalynConfig.from_env()
        try:
            verdict = _verify_fix(
                proposed_fix=proposed_fix,
                report=report,
                task_description=task_description,
                config=config,
            )
            return [types.TextContent(type="text", text=json.dumps({
                "status": "ok",
                "agrees": verdict.agrees,
                "concerns": verdict.concerns,
                "recommendation": verdict.recommendation,
                "confidence": verdict.confidence,
                "model_used": verdict.model_used,
            }))]
        except VerificationError as e:
            return [types.TextContent(type="text", text=json.dumps({"status": "error", "message": str(e)}))]

    elif name == "get_report":
        if not _latest_report:
            return [types.TextContent(type="text", text=json.dumps({"status": "error", "message": "No report available yet."}))]
        return [types.TextContent(type="text", text=json.dumps({"status": "ok", "report": _latest_report}))]

    raise ValueError(f"Unknown tool: {name}")


def run_mcp_server() -> None:
    """Run the MCP server over stdin/stdout."""
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(run())


if __name__ == "__main__":
    run_mcp_server()
