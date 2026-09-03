import unittest
from types import SimpleNamespace

from source.commit.boundary import CommitStatus
from source.services.mission_lifecycle import Decision, MissionLifecycleService, MissionState
from source.verification.invariant_checker import Decision as VerificationDecision


class FakeOrchestrator:
    def __init__(self, verification=VerificationDecision.ALLOW, commit=CommitStatus.COMMITTED,
                 authorized=True):
        self.context = SimpleNamespace(
            verification_decision=verification,
            commit_record=SimpleNamespace(
                decision=commit, authorization_given=authorized, escalation_reason=None
            ),
        )
        self.calls = []

    def process_intent(self, intent):
        self.calls.append(intent)
        return self.context


class TestMissionLifecycle(unittest.TestCase):
    def test_analysis_is_deterministic_and_provider_neutral(self):
        orchestrator = FakeOrchestrator()
        service = MissionLifecycleService(orchestrator)
        first = service.analyze("  Update   public settings ")
        second = service.analyze("Update public settings")
        self.assertEqual(first, second)
        self.assertEqual(first.operation, "mutate")
        self.assertEqual(first.risk, "medium")

    def test_allowed_mission_exposes_ordered_lifecycle(self):
        orchestrator = FakeOrchestrator()
        result = MissionLifecycleService(orchestrator).run("Update public settings")
        self.assertEqual(result.decision, Decision.ALLOW)
        self.assertEqual(result.state, MissionState.COMMIT)
        self.assertEqual(result.states, tuple(MissionState))
        self.assertEqual(orchestrator.calls, ["Update public settings"])

    def test_denied_verification_never_allows(self):
        orchestrator = FakeOrchestrator(verification=VerificationDecision.DENY)
        result = MissionLifecycleService(orchestrator).run("Delete protected file")
        self.assertEqual(result.decision, Decision.DENY)

    def test_orchestrator_failure_escalates(self):
        class Broken:
            def process_intent(self, intent):
                raise RuntimeError("offline failure")

        result = MissionLifecycleService(Broken()).run("Inspect state")
        self.assertEqual(result.decision, Decision.ESCALATE)
        self.assertIn("orchestrator failure", result.reason)

    def test_empty_intent_is_rejected_before_orchestrator(self):
        with self.assertRaises(ValueError):
            MissionLifecycleService(FakeOrchestrator()).run("  ")


if __name__ == "__main__":
    unittest.main()
