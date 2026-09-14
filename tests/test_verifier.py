"""Tests for cross-vendor fix verification.

All API calls are mocked — no real API calls in tests.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from causalyn.config import CausalynConfig
from causalyn.models import CausalReport, VerificationVerdict
from causalyn.verifier import VerificationError, verify_fix, _parse_verdict


class TestParseVerdict:
    """Test JSON response parsing."""

    def test_parse_valid_json(self):
        raw = json.dumps({
            "agrees": True,
            "concerns": [],
            "recommendation": "",
            "confidence": 0.95,
        })
        verdict = _parse_verdict(raw, "test/model")

        assert verdict.agrees is True
        assert verdict.concerns == []
        assert verdict.confidence == 0.95
        assert verdict.model_used == "test/model"

    def test_parse_json_with_markdown_fences(self):
        raw = '```json\n{"agrees": false, "concerns": ["Missing import"], "recommendation": "Add the import back", "confidence": 0.8}\n```'
        verdict = _parse_verdict(raw, "test/model")

        assert verdict.agrees is False
        assert "Missing import" in verdict.concerns
        assert verdict.confidence == 0.8

    def test_parse_invalid_json_returns_disagreement(self):
        raw = "I think the fix looks fine but I can't return JSON."
        verdict = _parse_verdict(raw, "test/model")

        assert verdict.agrees is False
        assert len(verdict.concerns) > 0
        assert verdict.confidence == 0.0

    def test_parse_partial_json(self):
        """Even if some fields are missing, parsing should be tolerant."""
        raw = json.dumps({"agrees": True})
        verdict = _parse_verdict(raw, "test/model")

        assert verdict.agrees is True
        assert verdict.concerns == []
        assert verdict.confidence == 0.5  # default

    def test_parse_preserves_raw_response(self):
        raw = json.dumps({"agrees": True, "confidence": 0.9})
        verdict = _parse_verdict(raw, "test/model")

        assert verdict.raw_response == raw


class TestVerifyFix:
    """Test the full verification flow with mocked API calls."""

    def _make_report(self) -> CausalReport:
        return CausalReport(
            root_cause_step="step_4",
            crash_step="step_14",
            summary="Step 4 removed the auth import. Step 14 crashed.",
            diff_at_root_cause="--- a/app.py\n+++ b/app.py\n-from auth import middleware",
            test_command="pytest tests/",
        )

    def _make_config(self, provider: str = "openai") -> CausalynConfig:
        return CausalynConfig(
            verification_provider=provider,
            verification_model="gpt-4o",
            openai_api_key="sk-test-key",
            anthropic_api_key="sk-ant-test",
        )

    @patch("causalyn.verifier._call_openai_compatible")
    def test_verify_fix_openai_agrees(self, mock_call):
        mock_call.return_value = json.dumps({
            "agrees": True,
            "concerns": [],
            "recommendation": "",
            "confidence": 0.92,
        })

        report = self._make_report()
        config = self._make_config("openai")

        verdict = verify_fix(
            proposed_fix="+ from auth import middleware",
            report=report,
            task_description="Add user authentication",
            config=config,
        )

        assert verdict.agrees is True
        assert verdict.confidence == 0.92
        mock_call.assert_called_once()

    @patch("causalyn.verifier._call_openai_compatible")
    def test_verify_fix_openai_disagrees(self, mock_call):
        mock_call.return_value = json.dumps({
            "agrees": False,
            "concerns": ["Fix only adds a try/except around the crash site, doesn't restore the import"],
            "recommendation": "Restore the auth import at the top of app.py",
            "confidence": 0.88,
        })

        report = self._make_report()
        config = self._make_config("openai")

        verdict = verify_fix(
            proposed_fix="+ try:\n+     middleware.check()\n+ except:\n+     pass",
            report=report,
            config=config,
        )

        assert verdict.agrees is False
        assert len(verdict.concerns) == 1
        assert "import" in verdict.concerns[0]

    def test_verify_fix_no_api_key_raises(self):
        report = self._make_report()
        config = CausalynConfig(
            verification_provider="openai",
            verification_model="gpt-4o",
            openai_api_key=None,
        )

        with pytest.raises(VerificationError, match="No API key"):
            verify_fix(
                proposed_fix="some fix",
                report=report,
                config=config,
            )

    def test_verify_fix_unsupported_provider_raises(self):
        report = self._make_report()
        config = CausalynConfig(
            verification_provider="nonexistent",
            verification_model="model",
            openai_api_key="key",
        )
        # get_api_key returns None for unknown provider
        # but we override by setting it manually via a different approach
        with pytest.raises(VerificationError):
            verify_fix(
                proposed_fix="some fix",
                report=report,
                config=config,
            )


class TestVerificationPrompt:
    """Test that the verification prompt is constructed correctly."""

    @patch("causalyn.verifier._call_openai_compatible")
    def test_prompt_contains_causal_report(self, mock_call):
        mock_call.return_value = json.dumps({"agrees": True, "confidence": 0.9})

        report = CausalReport(
            root_cause_step="step_4",
            crash_step="step_14",
            summary="Auth import was removed at step 4.",
            diff_at_root_cause="- from auth import check",
            test_command="pytest",
        )

        config = CausalynConfig(
            verification_provider="openai",
            verification_model="gpt-4o",
            openai_api_key="sk-test",
        )

        verify_fix(
            proposed_fix="+ from auth import check",
            report=report,
            task_description="Fix authentication",
            config=config,
        )

        # Check the prompt that was sent
        call_args = mock_call.call_args
        prompt = call_args.kwargs["prompt"]

        assert "Auth import was removed" in prompt
        assert "from auth import check" in prompt
        assert "Fix authentication" in prompt
