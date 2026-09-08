"""Comprehensive verification of Layer 1 Interception Hook (API proxy & CLI wrapper).

Tests:
1. POST /v1/proxy/action and POST /api/proxy/action endpoints.
2. Interception of safe file mutations and dangerous shell executions.
3. Generation and persistence of EU AI Act Article 10 audit records.
4. CLI standalone fallback and evaluation for 'intercept' and 'wrap' commands.
"""

import os
import unittest
from fastapi.testclient import TestClient

from app import api
from causalyn.cli import main as cli_main, _run_standalone_eval


class TestProxyAndCLISuite(unittest.TestCase):
    """Test suite covering Causalyn Gateway API proxy and CLI interception."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(api)

    def test_v1_proxy_action_safe_file_write(self):
        """Verify that benign file creation is verified, committed, and logged."""
        payload = {
            "action_type": "file_write",
            "target_path": "/app/service/worker.py",
            "payload": {"content": "def run():\n    return 'healthy'\n"},
            "agent_framework": "claude-code-test",
            "session_id": "test-sess-001",
        }
        resp = self.client.post("/v1/proxy/action", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["decision"], "allow")
        self.assertIn("article_10_audit_id", data)
        self.assertTrue(data["article_10_audit_id"].startswith("art10-"))
        self.assertEqual(len(data["violations"]), 0)
        self.assertIn("/app/service/worker.py", data["unified_diffs"])

    def test_api_proxy_action_mirrored_route(self):
        """Verify that /api/proxy/action and /v1/proxy/action provide identical contracts."""
        payload = {
            "action_type": "file_write",
            "target_path": "/public/docs.txt",
            "payload": {"content": "Documentation text."},
            "agent_framework": "cursor-agent",
        }
        resp = self.client.post("/api/proxy/action", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["decision"], "allow")
        self.assertIn("article_10_audit_id", data)

    def test_v1_proxy_action_blocks_protected_path(self):
        """Verify that attempts to mutate /protected/config.json are fail-closed rejected."""
        payload = {
            "action_type": "file_write",
            "target_path": "/protected/config.json",
            "payload": {"content": '{"pwned": true}'},
            "agent_framework": "rogue-agent",
        }
        resp = self.client.post("/v1/proxy/action", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["decision"], "deny")
        codes = [v["code"] for v in data["violations"]]
        self.assertIn("POL-001-PROTECTED-RESOURCE", codes)
        self.assertIn("article_10_audit_id", data)

    def test_v1_proxy_action_blocks_malicious_shell_exec(self):
        """Verify that destructive shell commands like 'rm -rf /' trigger SEC-002 rejection."""
        payload = {
            "action_type": "shell_exec",
            "target_path": "/",
            "payload": {"command": "rm -rf /"},
            "agent_framework": "compromised-agent",
        }
        resp = self.client.post("/v1/proxy/action", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["decision"], "deny")
        codes = [v["code"] for v in data["violations"]]
        self.assertIn("SEC-002-SHELL-INJECTION", codes)

    def test_cli_standalone_eval_safe_action(self):
        """Test direct CLI standalone evaluation of a safe action."""
        eval_result = _run_standalone_eval(
            action_type="file_write",
            target_path="/tmp/output.json",
            payload={"content": '{"status": "ok"}'},
        )
        self.assertEqual(eval_result["decision"], "allow")
        self.assertEqual(len(eval_result["violations"]), 0)

    def test_cli_standalone_eval_blocked_action(self):
        """Test direct CLI standalone evaluation of a dangerous action."""
        eval_result = _run_standalone_eval(
            action_type="shell_exec",
            target_path="/",
            payload={"command": "mkfs.ext4 /dev/sda"},
        )
        self.assertEqual(eval_result["decision"], "deny")
        self.assertTrue(len(eval_result["violations"]) > 0)

    def test_cli_main_wrap_blocks_destructive_command(self):
        """Verify CLI 'wrap' subcommand returns exit code 1 on destructive command."""
        exit_code = cli_main(["wrap", "rm -rf /", "--standalone", "--no-execute"])
        self.assertEqual(exit_code, 1)

    def test_cli_main_wrap_allows_safe_command(self):
        """Verify CLI 'wrap' subcommand returns exit code 0 on safe command."""
        exit_code = cli_main(["wrap", "echo 'Causalyn Safe'", "--standalone", "--no-execute"])
        self.assertEqual(exit_code, 0)

    def test_cli_main_intercept_subcommand(self):
        """Verify CLI 'intercept' subcommand output."""
        exit_code = cli_main([
            "intercept",
            "--type", "file_write",
            "--target", "/app/feature.py",
            "--payload", '{"content": "print(1)"}',
            "--standalone",
            "--json",
        ])
        self.assertEqual(exit_code, 0)


    def test_cli_main_verify_clean_file(self):
        """Verify CLI 'verify' subcommand succeeds on clean python files."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            clean_file = os.path.join(td, "clean.py")
            with open(clean_file, "w") as f:
                f.write("def add(a: int, b: int) -> int:\n    return a + b\n")
            exit_code = cli_main(["verify", clean_file])
            self.assertEqual(exit_code, 0)

    def test_cli_main_verify_hazardous_rce(self):
        """Verify CLI 'verify' subcommand flags dangerous eval/exec calls."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            rce_file = os.path.join(td, "rce.py")
            with open(rce_file, "w") as f:
                f.write("def run_untrusted(cmd):\n    eval(cmd)\n")
            exit_code = cli_main(["verify", rce_file])
            self.assertEqual(exit_code, 1)

    def test_cli_main_verify_syntax_error(self):
        """Verify CLI 'verify' subcommand flags invalid Python syntax."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            bad_syntax_file = os.path.join(td, "syntax.py")
            with open(bad_syntax_file, "w") as f:
                f.write("def broken() : return {unclosed\n")
            exit_code = cli_main(["verify", bad_syntax_file])
            self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()

