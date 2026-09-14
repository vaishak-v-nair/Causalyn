"""Tests for the Claude Code hook implementation."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from causalyn.hook import handle_hook_event, _classify_tool, _describe_tool_use, _looks_like_test_failure
from causalyn.models import StepKind


class TestClassifyTool:
    """Test mapping Claude Code tool names to StepKind."""

    def test_write_file(self):
        assert _classify_tool("write_file") == StepKind.FILE_WRITE

    def test_edit_file(self):
        assert _classify_tool("edit_file") == StepKind.FILE_WRITE

    def test_delete_file(self):
        assert _classify_tool("delete_file") == StepKind.FILE_DELETE

    def test_run_command(self):
        assert _classify_tool("run_command") == StepKind.COMMAND_RUN

    def test_bash(self):
        assert _classify_tool("bash") == StepKind.COMMAND_RUN

    def test_unknown(self):
        assert _classify_tool("some_other_tool") == StepKind.UNKNOWN


class TestDescribeToolUse:
    """Test human-readable descriptions of tool use events."""

    def test_write_file_description(self):
        desc = _describe_tool_use("write_file", {"path": "src/app.py"})
        assert "write_file" in desc
        assert "src/app.py" in desc

    def test_run_command_description(self):
        desc = _describe_tool_use("run_command", {"command": "pytest tests/"})
        assert "run" in desc
        assert "pytest" in desc

    def test_long_command_is_truncated(self):
        long_cmd = "python -c 'print(\"a\" * 500)' " + "x" * 200
        desc = _describe_tool_use("run_command", {"command": long_cmd})
        assert len(desc) < 120

    def test_unknown_tool(self):
        desc = _describe_tool_use("mystery_tool", {})
        assert "mystery_tool" in desc


class TestLooksLikeTestFailure:
    """Test heuristic detection of test failures."""

    def test_pytest_failure(self):
        assert _looks_like_test_failure("FAILED test_app.py::test_login")

    def test_traceback(self):
        assert _looks_like_test_failure("Traceback (most recent call last)")

    def test_exit_code_1(self):
        assert _looks_like_test_failure("Process finished with exit code 1")

    def test_clean_output(self):
        assert not _looks_like_test_failure("All tests passed successfully.")

    def test_dict_output(self):
        assert _looks_like_test_failure({"content": "FAILED test_x.py"})

    def test_empty_string(self):
        assert not _looks_like_test_failure("")


class TestHandleHookEvent:
    """Test the hook event dispatcher."""

    @patch("causalyn.hook.get_engine")
    def test_pre_tool_use_allows(self, mock_engine):
        mock_engine.return_value = MagicMock()
        mock_engine.return_value.create.return_value = MagicMock(step_id="step_0")

        event = {
            "hook_type": "PreToolUse",
            "tool_name": "write_file",
            "tool_input": {"path": "app.py"},
        }
        result = handle_hook_event(event)

        assert result["decision"] == "allow"

    def test_unknown_hook_type_allows(self):
        event = {"hook_type": "SomeFutureHook"}
        result = handle_hook_event(event)
        assert result["decision"] == "allow"

    @patch("causalyn.hook.get_engine")
    def test_post_tool_use_no_failure_allows(self, mock_engine):
        mock_engine.return_value = MagicMock()

        event = {
            "hook_type": "PostToolUse",
            "tool_name": "write_file",
            "tool_input": {"path": "app.py"},
            "tool_output": {"content": "File written successfully"},
        }
        result = handle_hook_event(event)

        assert result["decision"] == "allow"
