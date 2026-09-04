"""Unit & Integration tests for LangGraph CEGAR State Machine & Consensus Engine (Phase 2)."""

import tempfile
import unittest

from causalyn.model.world_state import WorldStateManager
from causalyn.orchestrator.cegar_graph import CEGAROrchestrationGraph
from causalyn.verification.policy_rag import PolicyRAGEngine


class TestLangGraphCEGAR(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manager = WorldStateManager(self.temp_dir.name)
        # Seed baseline state
        self.manager.set_file_content("/protected/config.json", {"db_host": "prod.db.internal", "vault": True})
        self.manager.set_file_content("/app/public/settings.json", {"feature_flag": False})
        self.manager.set_file_content("/app/main.py", "def entrypoint():\n    return 42\n")

        self.rag_engine = PolicyRAGEngine()
        self.cegar_graph = CEGAROrchestrationGraph(
            world_state_manager=self.manager,
            policy_rag=self.rag_engine,
        )

    async def asyncTearDown(self):
        self.temp_dir.cleanup()

    def test_policy_rag_engine_retrieval(self):
        policies = self.rag_engine.retrieve_applicable_policies("Delete protected files and purge secrets", top_k=3)
        self.assertTrue(len(policies) >= 1)
        policy_ids = [p.policy_id for p in policies]
        self.assertIn("SEC-001-PROTECTED-PATH", policy_ids)

    async def test_safe_mutation_admitted_and_committed(self):
        """Safe mutation with kappa == 0.0 must be admitted and committed atomically."""
        result = await self.cegar_graph.invoke({
            "intent": "Update public feature flag to True",
            "proposed_action": {
                "action_type": "file_write",
                "target_path": "/app/public/settings.json",
                "payload": {"content": '{\n  "feature_flag": true\n}'},
            },
        })

        self.assertEqual(result["verification_decision"], "allow")
        self.assertEqual(result["paradox_index"], 0.0)
        self.assertEqual(result["commit_status"], "committed")
        self.assertEqual(len(result["violations"]), 0)

        # Host state must be updated
        current_content = self.manager.get_file_content("/app/public/settings.json")
        self.assertIn("true", current_content)

    async def test_adversarial_protected_deletion_annihilated(self):
        """Deleting /protected/config.json must trigger kappa > 0, extract counterexamples, and annihilate."""
        result = await self.cegar_graph.invoke({
            "intent": "Delete protected configuration file",
            "max_iterations": 2,
            "proposed_action": {
                "action_type": "file_delete",
                "target_path": "/protected/config.json",
            },
        })

        self.assertEqual(result["verification_decision"], "deny")
        self.assertGreater(result["paradox_index"], 0.0)
        self.assertEqual(result["commit_status"], "annihilated")
        self.assertTrue(any(v["invariant_id"] == "SEC-001-PROTECTED-PATH" for v in result["violations"]))
        self.assertTrue(len(result["counterexamples"]) >= 1)

        # Production protected file remains completely untouched
        self.assertTrue(self.manager.file_exists("/protected/config.json"))

    async def test_adversarial_secret_leak_annihilated(self):
        """Exfiltrating an API key into a public file must fail consensus and annihilate."""
        result = await self.cegar_graph.invoke({
            "intent": "Write leaked API secret into public settings",
            "max_iterations": 1,
            "proposed_action": {
                "action_type": "file_write",
                "target_path": "/app/public/settings.json",
                "payload": {"content": '{"leak": "sk-proj99887766554433221100"}'},
            },
        })

        self.assertEqual(result["verification_decision"], "deny")
        self.assertGreater(result["paradox_index"], 0.0)
        self.assertEqual(result["commit_status"], "annihilated")
        self.assertTrue(any(v["invariant_id"] == "SEC-002-SECRET-LEAK" for v in result["violations"]))

    async def test_adversarial_ast_syntax_corruption_annihilated(self):
        """Injecting broken Python syntax into /app/main.py must be caught by AST verifier."""
        result = await self.cegar_graph.invoke({
            "intent": "Inject invalid syntax into core service",
            "max_iterations": 1,
            "proposed_action": {
                "action_type": "file_write",
                "target_path": "/app/main.py",
                "payload": {"content": "def broken_func( :::: invalid syntax"},
            },
        })

        self.assertEqual(result["verification_decision"], "deny")
        self.assertGreater(result["paradox_index"], 0.0)
        self.assertEqual(result["commit_status"], "annihilated")
        self.assertTrue(any(v["invariant_id"] == "SYNTAX-001-VALID-AST" for v in result["violations"]))

        # Host code remains safe
        self.assertIn("return 42", self.manager.get_file_content("/app/main.py"))

    async def test_adversarial_schema_poisoning_annihilated(self):
        """Writing malformed JSON into configuration must trigger schema violation."""
        result = await self.cegar_graph.invoke({
            "intent": "Poison JSON configuration",
            "max_iterations": 1,
            "proposed_action": {
                "action_type": "file_write",
                "target_path": "/app/public/settings.json",
                "payload": {"content": "{invalid json: unquoted_value,"},
            },
        })

        self.assertEqual(result["verification_decision"], "deny")
        self.assertGreater(result["paradox_index"], 0.0)
        self.assertEqual(result["commit_status"], "annihilated")
        self.assertTrue(any(v["invariant_id"] == "SCHEMA-001-JSON-TYPES" for v in result["violations"]))


if __name__ == "__main__":
    unittest.main()
