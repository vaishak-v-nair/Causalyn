"""Tests for C-VPSN Categorical Nullification, CEGAR-CEGIS loop, and Paradox Index calculation."""

import tempfile
import unittest
from pathlib import Path

from causalyn.commit.boundary import CommitBoundary, CommitStatus
from causalyn.failure_pattern.dataset import FailurePatternDataset
from causalyn.model.world_state import WorldState, WorldStateManager
from causalyn.orchestrator.orchestrator import AIOrchestrator, OrchestrationStage
from causalyn.shadow.executor import ShadowExecutor
from causalyn.verification.invariant_checker import Decision, create_default_verification_engine
from causalyn.llm.provider import LLMMessage, NullProvider, create_llm_provider
from causalyn.config import RuntimeSettings


class TestCVPSNCEGAR(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.TemporaryDirectory()
        self.history = tempfile.NamedTemporaryFile(delete=False)
        self.history.close()

        self.manager = WorldStateManager(self.root.name)
        self.manager.set_file_content("/protected/config.json", {"secret_key": "enterprise-secret"})
        self.manager.set_file_content("/app/public/settings.json", {"feature_flag": False})

        self.dataset = FailurePatternDataset()
        self.executor = ShadowExecutor(self.manager)
        self.engine = create_default_verification_engine()
        self.boundary = CommitBoundary(
            self.dataset, commit_history_path=self.history.name
        )
        self.orchestrator = AIOrchestrator()
        self.orchestrator.set_dependencies(
            self.manager,
            self.executor,
            self.engine,
            self.boundary,
            self.dataset,
            llm_provider=NullProvider(),
        )

    def tearDown(self):
        self.root.cleanup()
        Path(self.history.name).unlink(missing_ok=True)

    def test_paradox_index_zero_for_valid_transition(self):
        """Clean transitions must reside in the Semantic Null-Space (kappa == 0)."""
        before = WorldState()
        before.set_file_content("/app/public/settings.json", {"feature_flag": False})

        after = WorldState()
        after.set_file_content("/app/public/settings.json", {"feature_flag": True})

        decision = self.engine.verify_transition(before, after)
        kappa = self.engine.calculate_paradox_index(before, after)

        self.assertEqual(decision, Decision.ALLOW)
        self.assertEqual(kappa, 0.0)

    def test_paradox_index_positive_and_counterexample_extracted_on_violation(self):
        """Violations must trigger positive kappa penalty and extract structured counterexamples."""
        before = WorldState()
        before.set_file_content("/protected/config.json", {"secret_key": "top-secret"})

        after = WorldState()
        # Unauthorized mutation of protected configuration
        after.set_file_content("/protected/config.json", {"secret_key": "mutated"})

        decision = self.engine.verify_transition(before, after)
        kappa = self.engine.calculate_paradox_index(before, after)
        counterexample = self.engine.get_counterexample(before, after)

        self.assertEqual(decision, Decision.DENY)
        self.assertGreater(kappa, 0.0)
        self.assertTrue(len(counterexample["violations"]) > 0)
        self.assertTrue(len(counterexample["remediation_guidance"]) > 0)

    def test_ast_syntax_verifier_detects_malformed_code(self):
        """Modified Python source with syntax error must fail verification and add to kappa."""
        before = WorldState()
        before.set_file_content("/app/service.py", "def valid(): pass\n")

        after = WorldState()
        after.set_file_content("/app/service.py", "def broken_syntax(:\n")

        self.assertFalse(self.engine._verify_tests_keep_passing(before, after))

    def test_schema_verifier_detects_malformed_json(self):
        """Modified JSON configuration with malformed syntax must fail schema verification."""
        before = WorldState()
        before.set_file_content("/app/config.json", '{"status": "ok"}')

        after = WorldState()
        after.set_file_content("/app/config.json", '{"status": "broken", invalid json')

        self.assertFalse(self.engine._verify_schema_constraints_valid(before, after))

    def test_cegar_refinement_metadata_recorded_in_orchestration(self):
        """Orchestration context must capture Paradox Index and CEGAR iteration telemetry."""
        context = self.orchestrator.process_intent(
            "Update the public settings to enable the new feature"
        )
        self.assertEqual(context.verification_decision, Decision.ALLOW)
        self.assertEqual(context.commit_record.decision, CommitStatus.COMMITTED)
        self.assertIn("paradox_index", context.metadata)
        self.assertEqual(context.metadata["paradox_index"], 0.0)
        self.assertIn("refinement_iterations", context.metadata)

    def test_multi_provider_llm_factory(self):
        """Null provider should complete safely without network I/O."""
        settings = RuntimeSettings(model_enabled=False)
        provider = create_llm_provider(settings)
        resp = provider.complete([LLMMessage(role="user", content="ping")])
        self.assertEqual(resp.provider, "null")
