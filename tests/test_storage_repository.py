import tempfile
import unittest
from pathlib import Path

from causalyn.storage.repository import TransactionalAuditRepository


class TestTransactionalAuditRepository(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.repository = TransactionalAuditRepository(
            Path(self.directory.name) / "audit.sqlite3"
        )

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_mission_event_and_summaries_are_persisted(self) -> None:
        mission = self.repository.create_mission(
            "request-1", "deploy", {"intent": "safe change"}
        )
        event = self.repository.record_event(
            mission.mission_id, "verification", {"decision": "allow"}
        )
        evidence = self.repository.save_evidence_summary(
            mission.mission_id, {"checks": 2}
        )
        decision = self.repository.save_decision_summary(
            mission.mission_id, {"decision": "allow"}
        )

        self.assertEqual(self.repository.get_mission(mission.mission_id), mission)
        self.assertEqual(self.repository.list_events(mission.mission_id), [event])
        self.assertEqual(self.repository.get_evidence_summary(mission.mission_id), evidence)
        self.assertEqual(self.repository.get_decision_summary(mission.mission_id), decision)

    def test_request_id_replay_does_not_duplicate_and_conflicts_fail(self) -> None:
        first = self.repository.create_mission("same", "one")
        replay = self.repository.create_mission("same", "one")
        self.assertEqual(first, replay)
        self.assertEqual(len(self.repository.list_missions()), 1)
        with self.assertRaises(ValueError):
            self.repository.create_mission("same", "different")

        event = self.repository.record_event(
            first.mission_id, "started", request_id="event-request"
        )
        self.assertEqual(
            self.repository.record_event(
                first.mission_id, "started", request_id="event-request"
            ),
            event,
        )
        self.assertEqual(len(self.repository.list_events(first.mission_id)), 1)

    def test_queries_are_bounded(self) -> None:
        for index in range(120):
            self.repository.create_mission(f"request-{index}", str(index))
        self.assertEqual(len(self.repository.list_missions(1000)), 100)
        mission = self.repository.list_missions(1)[0]
        for index in range(120):
            self.repository.record_event(mission.mission_id, str(index))
        self.assertEqual(len(self.repository.list_events(mission.mission_id, 1000)), 100)


if __name__ == "__main__":
    unittest.main()
