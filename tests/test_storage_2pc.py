"""Unit tests for Dual Transaction Storage & Two-Phase Commit (2PC) Pre-State Validation (Phase 3)."""

import os
import tempfile
import unittest

from causalyn.commit.boundary import CommitBoundary, CommitStatus
from causalyn.model.world_state import WorldState, WorldStateManager
from causalyn.storage.repository import (
    PostgreSQLAuditRepository,
    TransactionalAuditRepository,
    get_audit_repository,
)
from causalyn.verification.invariant_checker import create_default_verification_engine


class TestStorage2PC(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_audit.sqlite3")
        self.repo = TransactionalAuditRepository(self.db_path)
        self.manager = WorldStateManager(self.temp_dir.name)
        self.boundary = CommitBoundary(commit_history_path=os.path.join(self.temp_dir.name, "history.jsonl"))
        self.engine = create_default_verification_engine()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_world_state_compute_hash_deterministic(self):
        ws1 = WorldState(data={"counter": 1}, file_system={"/app/conf.json": '{"a": 1}'})
        ws2 = WorldState(data={"counter": 1}, file_system={"/app/conf.json": '{"a": 1}'})
        h1 = ws1.compute_hash()
        h2 = ws2.compute_hash()
        self.assertEqual(len(h1), 64)
        self.assertEqual(h1, h2)

        # Modifying state changes hash
        ws2.set_file_content("/app/conf.json", '{"a": 2}')
        self.assertNotEqual(ws1.compute_hash(), ws2.compute_hash())

    def test_2pc_pre_state_hash_matching_allows_commit(self):
        before = WorldState(data={"v": 1}, file_system={"/app/public/test.txt": "ok"})
        after = WorldState(data={"v": 2}, file_system={"/app/public/test.txt": "ok2"})
        expected_hash = before.compute_hash()

        record = self.boundary.prepare_commit(
            intent_id="intent-safe",
            changes={"data:v": 2},
            verification_engine=self.engine,
            before_state=before,
            after_state=after,
            intent_text="update test data",
            expected_pre_state_hash=expected_hash,
        )
        self.assertEqual(record.decision, CommitStatus.COMMITTED)
        self.assertTrue(record.authorization_given)

    def test_2pc_pre_state_hash_mismatch_aborts_stale_state(self):
        before = WorldState(data={"v": 1}, file_system={"/app/public/test.txt": "human_edited"})
        after = WorldState(data={"v": 2}, file_system={"/app/public/test.txt": "agent_candidate"})
        stale_hash = "0000000000000000000000000000000000000000000000000000000000000000"

        record = self.boundary.prepare_commit(
            intent_id="intent-stale",
            changes={"data:v": 2},
            verification_engine=self.engine,
            before_state=before,
            after_state=after,
            intent_text="update test data",
            expected_pre_state_hash=stale_hash,
        )
        self.assertEqual(record.decision, CommitStatus.FAILED)
        self.assertFalse(record.authorization_given)
        self.assertIn("STALE_STATE_ABORT", record.escalation_reason)

    def test_article10_audit_and_mission_persistence(self):
        self.repo.record_causalyn_mission(
            mission_id="mission-001",
            session_id="sess-001",
            request_id="req-unique-01",
            agent_framework="claude_code",
            intent="Update staging feature flag",
            stage="committed",
            paradox_index=0.0,
            verification_decision="allow",
            commit_decision="committed",
            pre_state_hash="a" * 64,
            post_state_hash="b" * 64,
        )

        missions = self.repo.get_causalyn_missions(limit=10)
        self.assertEqual(len(missions), 1)
        self.assertEqual(missions[0]["mission_id"], "mission-001")
        self.assertEqual(missions[0]["paradox_index"], 0.0)

        # Audit ledger
        self.repo.record_causalyn_audit(
            mission_id="mission-001",
            verifier_matrix={"ast_syntax": True, "schema": True, "secrets": True},
            unified_diffs={"/app/config.json": "+ flag: true"},
            hash_signature="sig-hash-12345",
            counterexamples=[],
            article_10_compliant=True,
        )

        audits = self.repo.get_causalyn_audits(limit=10)
        self.assertEqual(len(audits), 1)
        self.assertEqual(audits[0]["mission_id"], "mission-001")
        self.assertTrue(audits[0]["verifier_matrix"]["ast_syntax"])

    def test_get_audit_repository_factory(self):
        sqlite_repo = get_audit_repository(self.db_path)
        self.assertIsInstance(sqlite_repo, TransactionalAuditRepository)

        # PostgreSQL selection
        try:
            pg_repo = get_audit_repository("postgresql://user:pass@localhost:5432/testdb")
            self.assertIsInstance(pg_repo, PostgreSQLAuditRepository)
        except RuntimeError as e:
            # Expected if psycopg2 is not installed
            self.assertIn("PostgreSQL driver", str(e))


if __name__ == "__main__":
    unittest.main()
