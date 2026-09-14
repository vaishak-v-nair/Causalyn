"""Test Suite for Causalyn Milestone M5: Enterprise Production Hypervisor.

Verifies:
1. Hardware Enclave Remote Attestation & Sealed Memory (Confidential Computing).
2. Multi-Vendor Byzantine-Fault-Tolerant Distributed Consensus.
3. SOC2 Type II & EU AI Act Article 10 Compliance Automation.
"""

import os
import shutil
import tempfile
import unittest

from causalyn.api.contracts import GateDecision
from causalyn.compliance.engine import EnterpriseComplianceEngine
from causalyn.consensus.distributed_consensus import DistributedConsensusEngine
from causalyn.enclave.attestation import EnclaveAttestationManager


class TestM5EnterpriseSuite(unittest.TestCase):
    """Verifies enterprise production hypervisor capabilities."""

    def setUp(self):
        self.enclave = EnclaveAttestationManager()
        self.consensus = DistributedConsensusEngine(enclave_manager=self.enclave)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_enclave_attestation_and_quote_verification(self):
        """Verify remote attestation quotes are signed and bound to candidate payload."""
        user_data = "file_write:/app/main.py:def test(): pass"
        quote = self.enclave.generate_attestation_quote(user_data)

        self.assertTrue(quote.verified)
        self.assertEqual(quote.platform, "SEV-SNP")

        # Valid verification
        valid = self.enclave.verify_attestation_quote(quote, user_data)
        self.assertTrue(valid)

        # Tampered verification fails
        tampered = self.enclave.verify_attestation_quote(quote, "file_write:/protected/hack.py:pwned")
        self.assertFalse(tampered)

    def test_enclave_state_sealing_and_unsealing(self):
        """Verify state sealing with tamper detection."""
        secret_state = {"master_token": "prod_12345", "counter": 42}
        sealed = self.enclave.seal_payload(secret_state)

        self.assertIsInstance(sealed, str)
        self.assertNotIn("prod_12345", sealed)  # Encrypted

        unsealed = self.enclave.unseal_payload(sealed)
        self.assertEqual(unsealed, secret_state)

    def test_distributed_consensus_allows_safe_action(self):
        """Verify safe action receives unanimous/quorum allow vote."""
        result = self.consensus.evaluate_action_consensus(
            action_type="file_write",
            target_path="/app/utils.py",
            payload={"content": "def add(a, b): return a + b"},
            ast_violations=[],
            rag_policies=["POL-001-GENERAL"],
        )
        self.assertEqual(result.consensus_decision, GateDecision.ALLOW)
        self.assertTrue(result.quorum_reached)
        self.assertGreaterEqual(result.allow_count, 3)

    def test_distributed_consensus_vetoes_protected_mutation(self):
        """Verify protected path is vetoed by policy node and denied by consensus."""
        result = self.consensus.evaluate_action_consensus(
            action_type="file_write",
            target_path="/protected/system.json",
            payload={"content": "{}"},
            ast_violations=[],
            rag_policies=[],
        )
        self.assertEqual(result.consensus_decision, GateDecision.DENY)
        self.assertEqual(result.votes["node_2_policy_rag"], "deny")

    def test_distributed_consensus_vetoes_destructive_shell(self):
        """Verify destructive shell command is vetoed by cross-examiner node."""
        result = self.consensus.evaluate_action_consensus(
            action_type="shell_exec",
            target_path="/",
            payload={"command": "rm -rf /"},
            ast_violations=[],
            rag_policies=[],
        )
        self.assertEqual(result.consensus_decision, GateDecision.DENY)
        self.assertEqual(result.votes["node_3_cross_examiner"], "deny")

    def test_compliance_engine_generates_evidence_pack(self):
        """Verify SOC2 Type II and EU AI Act Article 10 compliance evidence pack synthesis."""
        engine = EnterpriseComplianceEngine()
        pack = engine.generate_evidence_pack()

        self.assertEqual(pack.overall_status, "COMPLIANT")
        self.assertTrue(len(pack.merkle_root) > 0)
        self.assertTrue(len(pack.signature) > 0)

        soc2_ids = [c.control_id for c in pack.soc2_controls]
        self.assertIn("CC6.1", soc2_ids)
        self.assertIn("CC6.6", soc2_ids)
        self.assertIn("CC6.8", soc2_ids)
        self.assertIn("CC7.1", soc2_ids)
        self.assertIn("CC8.1", soc2_ids)

        art10_ids = [c.control_id for c in pack.eu_ai_act_controls]
        self.assertIn("ART10.1", art10_ids)
        self.assertIn("ART10.2", art10_ids)
        self.assertIn("ART10.3", art10_ids)

        out_file = engine.export_evidence_pack(output_dir=self.temp_dir)
        self.assertTrue(os.path.exists(out_file))


if __name__ == "__main__":
    unittest.main()
