import tempfile
import unittest
from pathlib import Path

from causalyn.commit.boundary import CommitBoundary, CommitStatus
from causalyn.failure_pattern.dataset import FailurePatternDataset
from causalyn.orchestrator.orchestrator import AIOrchestrator, OrchestrationStage
from causalyn.shadow.executor import ShadowExecutor
from causalyn.verification.invariant_checker import Decision, create_default_verification_engine
from causalyn.model.world_state import WorldStateManager


class TestPrototypePipeline(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.TemporaryDirectory()
        self.history = tempfile.NamedTemporaryFile(delete=False)
        self.history.close()
        self.manager = WorldStateManager(self.root.name)
        self.manager.set_file_content("/protected/config.json", {"secret_key": "hidden"})
        self.manager.set_file_content("/app/public/settings.json", {"feature_flag": False})
        self.dataset = FailurePatternDataset()
        self.executor = ShadowExecutor(self.manager)
        self.engine = create_default_verification_engine()
        self.boundary = CommitBoundary(
            self.dataset, commit_history_path=self.history.name
        )
        self.orchestrator = AIOrchestrator()
        self.orchestrator.set_dependencies(
            self.manager, self.executor, self.engine, self.boundary, self.dataset
        )

    def tearDown(self):
        self.root.cleanup()
        Path(self.history.name).unlink(missing_ok=True)

    def test_authorized_safe_intent_commits_data(self):
        context = self.orchestrator.process_intent(
            "Update the public settings to enable the new feature"
        )
        self.assertEqual(context.verification_decision, Decision.ALLOW)
        self.assertEqual(context.commit_record.decision, CommitStatus.COMMITTED)
        self.assertEqual(context.current_stage, OrchestrationStage.COMMITTED)
        self.assertEqual(self.manager.get_data("migration_status"), "in_progress")

    def test_protected_deletion_is_denied(self):
        self.executor.harness_context = self.orchestrator.harness_context

        def delete_protected():
            self.orchestrator.harness_context.delete_file("/protected/config.json")

        original = self.orchestrator._execute_intent_actions
        self.orchestrator._execute_intent_actions = lambda context: delete_protected()
        try:
            context = self.orchestrator.process_intent("Update the public settings")
        finally:
            self.orchestrator._execute_intent_actions = original
        self.assertEqual(context.verification_decision, Decision.DENY)
        self.assertTrue(self.manager.file_exists("/protected/config.json"))

    def test_public_file_change_commits(self):
        original = self.orchestrator._execute_intent_actions
        self.orchestrator._execute_intent_actions = lambda context: (
            self.orchestrator.harness_context.write_file(
                "/app/public/settings.json", '{"feature_flag": true}'
            )
        )
        try:
            context = self.orchestrator.process_intent("Update public settings")
        finally:
            self.orchestrator._execute_intent_actions = original
        self.assertEqual(context.current_stage, OrchestrationStage.COMMITTED)
        self.assertEqual(
            self.manager.get_file_content("/app/public/settings.json"),
            '{"feature_flag": true}',
        )

    def test_secret_exfiltration_is_denied(self):
        original = self.orchestrator._execute_intent_actions
        self.orchestrator._execute_intent_actions = lambda context: (
            self.orchestrator.harness_context.write_file(
                "/logs/app.log", "secret_key=hidden"
            )
        )
        try:
            context = self.orchestrator.process_intent("Update public settings")
        finally:
            self.orchestrator._execute_intent_actions = original
        self.assertEqual(context.verification_decision, Decision.DENY)
        self.assertIsNone(self.manager.get_file_content("/logs/app.log"))
