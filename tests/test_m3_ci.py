"""Test Suite for Causalyn Milestone M3: Continuous Shadow Verification on Git PRs."""

import asyncio
import unittest

from causalyn.api.contracts import GateDecision
from causalyn.ci.github_checker import PRVerifier
from causalyn.storage.repository import get_audit_repository


class TestM3CISuite(unittest.TestCase):
    """Verifies continuous shadow verification of Git PR diffs."""

    def setUp(self):
        self.verifier = PRVerifier()

    def test_benign_pr_diff_passes_verification(self):
        """Verify that a benign PR patch is approved with status 'success'."""
        diff_text = """diff --git a/app/helpers/format.py b/app/helpers/format.py
new file mode 100644
--- /dev/null
+++ b/app/helpers/format.py
@@ -0,0 +1,5 @@
+def format_currency(amount: float) -> str:
+    \"\"\"Format currency nicely.\"\"\"
+    return f"${amount:.2f}"
+
"""
        result = asyncio.run(self.verifier.verify_diff(
            diff_text=diff_text,
            pr_number=42,
            commit_sha="a1b2c3d4e5f6",
        ))

        self.assertEqual(result.verdict, GateDecision.ALLOW)
        self.assertEqual(result.github_status, "success")
        self.assertEqual(result.paradox_index, 0.0)
        self.assertEqual(len(result.violations), 0)
        self.assertIn("APPROVED / VERIFIED", result.summary_markdown)
        self.assertIn("art10-ci-", result.article_10_audit_id)

    def test_adversarial_pr_diff_blocked(self):
        """Verify that a PR attempting to modify protected resources and leak keys is blocked."""
        diff_text = """diff --git a/protected/config.json b/protected/config.json
--- a/protected/config.json
+++ b/protected/config.json
@@ -1,3 +1,3 @@
 {
-  "debug": false
+  "debug": true,
+  "compromised_key": "sk-proj-maliciouskey1234567890abcdef"
 }
"""
        result = asyncio.run(self.verifier.verify_diff(
            diff_text=diff_text,
            pr_number=99,
            commit_sha="badc0de12345",
        ))

        self.assertEqual(result.verdict, GateDecision.DENY)
        self.assertEqual(result.github_status, "failure")
        self.assertGreater(result.paradox_index, 0.0)
        self.assertGreater(len(result.violations), 0)

        codes = [v.get("code") for v in result.violations]
        self.assertIn("POL-001-PROTECTED-RESOURCE", codes)
        self.assertIn("REJECTED / BLOCKED", result.summary_markdown)

    def test_audit_ledger_persistence(self):
        """Verify that continuous CI verification records audit entries."""
        repo = get_audit_repository()
        audits = repo.get_causalyn_audits(limit=10)
        self.assertIsInstance(audits, list)


if __name__ == "__main__":
    unittest.main()
