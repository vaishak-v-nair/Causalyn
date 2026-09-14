"""Test Suite for Causalyn Milestone M4: Staging Infrastructure Control & Database Shadow Branching."""

import os
import shutil
import tempfile
import unittest

from causalyn.api.contracts import GateDecision
from causalyn.shadow.db_branching import DatabaseShadowBranchManager
from causalyn.staging.proxy_interceptor import StagingInfrastructureGate


class TestM4StagingAndDBSuite(unittest.TestCase):
    """Verifies database shadow branching and staging infrastructure gating."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.base_db = os.path.join(self.temp_dir, "test_base.sqlite3")
        self.db_manager = DatabaseShadowBranchManager(base_db_path=self.base_db)
        self.staging_gate = StagingInfrastructureGate()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_benign_migration_executes_and_generates_rollback(self):
        """Verify benign CREATE TABLE generates rollback and commits."""
        sql = """
        CREATE TABLE IF NOT EXISTS service_metrics (
            metric_id INTEGER PRIMARY KEY,
            service_name TEXT NOT NULL,
            value REAL NOT NULL
        );
        """
        result = self.db_manager.execute_and_verify_migration(sql)
        self.assertEqual(result.decision, GateDecision.ALLOW)
        self.assertEqual(result.paradox_index, 0.0)
        self.assertEqual(result.applied_statements, 1)
        self.assertIsNotNone(result.rollback_sql)
        self.assertIn("DROP TABLE IF EXISTS service_metrics", result.rollback_sql)

    def test_destructive_drop_table_annihilated(self):
        """Verify that DROP TABLE is intercepted and rejected with DB-001."""
        sql = "DROP TABLE production_users;"
        result = self.db_manager.execute_and_verify_migration(sql)
        self.assertEqual(result.decision, GateDecision.DENY)
        self.assertGreater(result.paradox_index, 0.0)
        codes = [v.code for v in result.violations]
        self.assertIn("DB-001-DROP-RESOURCE", codes)

    def test_catastrophic_delete_without_where_blocked(self):
        """Verify DELETE without WHERE clause is intercepted with DB-003."""
        sql = "DELETE FROM financial_transactions;"
        result = self.db_manager.execute_and_verify_migration(sql)
        self.assertEqual(result.decision, GateDecision.DENY)
        codes = [v.code for v in result.violations]
        self.assertIn("DB-003-UNCONSTRAINED-DELETE", codes)

    def test_truncate_table_blocked(self):
        """Verify TRUNCATE is caught and blocked with DB-002."""
        sql = "TRUNCATE TABLE billing_records;"
        result = self.db_manager.execute_and_verify_migration(sql)
        self.assertEqual(result.decision, GateDecision.DENY)
        codes = [v.code for v in result.violations]
        self.assertIn("DB-002-TRUNCATE-DATA", codes)

    def test_staging_gate_allows_compliant_manifest(self):
        """Verify compliant microservice manifest is approved."""
        manifest = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: app
          image: myregistry/api:1.0.0
          resources:
            limits:
              cpu: "500m"
              memory: "512Mi"
"""
        res = self.staging_gate.verify_manifest(manifest)
        self.assertEqual(res.decision, GateDecision.ALLOW)
        self.assertEqual(res.paradox_index, 0.0)
        self.assertEqual(len(res.violations), 0)

    def test_staging_gate_blocks_host_mount_and_privileged_container(self):
        """Verify privileged container with host docker socket mount is blocked."""
        bad_manifest = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: malicious-daemon
spec:
  template:
    spec:
      containers:
        - name: pwn
          image: attacker/rootkit:latest
          privileged: true
          volumeMounts:
            - mountPath: /var/run/docker.sock
              name: dockersock
"""
        res = self.staging_gate.verify_manifest(bad_manifest)
        self.assertEqual(res.decision, GateDecision.DENY)
        self.assertGreater(res.paradox_index, 0.0)
        codes = [v.code for v in res.violations]
        self.assertIn("INFRA-001-PRIVILEGED-CONTAINER", codes)
        self.assertIn("INFRA-002-HOST-MOUNT", codes)


if __name__ == "__main__":
    unittest.main()
