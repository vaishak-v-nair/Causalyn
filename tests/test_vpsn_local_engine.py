"""
Unit and Integration Test Suite for the Vaishak Principle of Semantic Nullification (VPSN).
Tests the local silicon execution engine:
1. The Mathematical Kernel (Kappa Engine - AST & Regex)
2. The Ambient Fabric (Copy-on-Write Shadow Sandbox & Vaishak Operator Annihilation)
3. The Formal CEGAR Loop (Microsoft Z3 SMT Solver)
4. Integration API Endpoints (/api/vpsn/evaluate, /api/vpsn/manifold)
"""

import os
import shutil
import tempfile
import unittest

import app
from causalyn.shadow.ambient_fabric import AmbientFabric
from causalyn.verification.cegar_loop import FormalCEGARLoop, evaluate_invariant_nullspace
from causalyn.verification.kappa_engine import ParadoxVisitor, compute_paradox_index
from fastapi.testclient import TestClient

# Also verify backward-compatible / backend.source import paths
import backend.source.verification.kappa_engine as backend_kappa
import backend.source.shadow.ambient_fabric as backend_ambient
import backend.source.verification.cegar_loop as backend_cegar


class TestVPSNMathematicalKernel(unittest.TestCase):
    """Verifies the Mathematical Kernel (Kappa Engine) on Python ASTs and Regex."""

    def test_admissible_code_zero_paradox(self):
        """Code respecting all invariants must have kappa = 0.0."""
        candidate = (
            "def calculate_total(prices):\n"
            "    tax_rate = 0.08\n"
            "    return sum(prices) * (1 + tax_rate)\n"
        )
        kappa, violations = compute_paradox_index(candidate, intent_vector={"block_os": True})
        self.assertEqual(kappa, 0.0)
        self.assertEqual(violations, [])

    def test_unauthorized_os_and_subprocess_import(self):
        """Unauthorized imports trigger instant curvature tension spike."""
        candidate = (
            "import os\n"
            "import subprocess\n"
            "def run_task():\n"
            "    os.system('rm -rf /')\n"
        )
        kappa, violations = compute_paradox_index(candidate, intent_vector={"block_os": True})
        self.assertGreater(kappa, 0.0)
        self.assertTrue(any("Unauthorized import of os" in v for v in violations))
        self.assertTrue(any("Unauthorized import of subprocess" in v for v in violations))
        self.assertTrue(any("Unauthorized system call" in v for v in violations))

    def test_from_import_violation(self):
        """from os import system is caught by AST visitor."""
        candidate = "from os import system\nsystem('echo dangerous')\n"
        kappa, violations = compute_paradox_index(candidate, intent_vector={"block_os": True})
        self.assertGreater(kappa, 0.0)
        self.assertTrue(any("from os" in v for v in violations))

    def test_plaintext_secret_detection(self):
        """Regex scanning detects plaintext API secrets as tension spikes."""
        candidate = (
            "class Config:\n"
            "    OPENAI_API_KEY = 'sk-abcdef1234567890abcdef12345'\n"
        )
        kappa, violations = compute_paradox_index(candidate, intent_vector={"block_os": True})
        self.assertGreaterEqual(kappa, 100.0)
        self.assertTrue(any("Plaintext API secret" in v for v in violations))

    def test_ast_syntax_corruption(self):
        """Syntax errors represent infinite paradox."""
        corrupted = "def broken_syntax(x: return x +"
        kappa, violations = compute_paradox_index(corrupted, intent_vector={})
        self.assertEqual(kappa, float("inf"))
        self.assertIn("Paradox: AST Syntax Corruption", violations)

    def test_backend_source_reexport_compatibility(self):
        """backend.source.verification.kappa_engine matches causalyn directly."""
        clean = "x = 42\n"
        k, v = backend_kappa.compute_paradox_index(clean, {})
        self.assertEqual(k, 0.0)
        self.assertEqual(v, [])


class TestAmbientFabricAndVaishakOperator(unittest.TestCase):
    """Verifies Copy-on-Write Sandbox and Vaishak Operator (atomic promotion vs annihilation)."""

    def setUp(self):
        self.live_dir = tempfile.mkdtemp(prefix="vpsn_live_test_")
        self.test_file = "service_config.json"
        self.original_content = '{"version": "1.0", "status": "active"}\n'
        with open(os.path.join(self.live_dir, self.test_file), "w", encoding="utf-8") as f:
            f.write(self.original_content)

    def tearDown(self):
        if os.path.exists(self.live_dir):
            shutil.rmtree(self.live_dir, ignore_errors=True)

    def test_snapshot_and_isolation(self):
        """Shadow workspace does not mutate live disk prior to commit gate."""
        fabric = AmbientFabric(self.live_dir)
        shadow_dir = fabric.snapshot()
        self.assertTrue(os.path.isdir(shadow_dir))

        # Mutate shadow file
        fabric.write_shadow_file(self.test_file, '{"version": "2.0-candidate"}\n')

        # Verify live file is untouched
        with open(os.path.join(self.live_dir, self.test_file), "r", encoding="utf-8") as f:
            live_content = f.read()
        self.assertEqual(live_content, self.original_content)

        # Clean up shadow
        fabric.apply_vaishak_operator(1.0, self.test_file)

    def test_vaishak_operator_commit_on_zero_paradox(self):
        """When kappa == 0.0, candidate state is promoted atomically to live disk."""
        fabric = AmbientFabric(self.live_dir)
        fabric.snapshot()

        new_content = '{"version": "1.1", "status": "upgraded"}\n'
        fabric.write_shadow_file(self.test_file, new_content)

        diff = fabric.extract_candidate_diff(self.test_file)
        self.assertIn("-{\"version\": \"1.0\"", diff)
        self.assertIn("+{\"version\": \"1.1\"", diff)

        # Apply Vaishak Operator with kappa == 0.0
        status = fabric.apply_vaishak_operator(0.0, self.test_file)
        self.assertEqual(status, "COMMITTED")

        # Verify live disk has received the update
        with open(os.path.join(self.live_dir, self.test_file), "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), new_content)

        # Shadow directory must be cleaned up
        self.assertFalse(os.path.exists(fabric.shadow_dir))

    def test_vaishak_operator_annihilation_on_paradox(self):
        """When kappa > 0.0, candidate state is annihilated leaving live disk pristine."""
        fabric = AmbientFabric(self.live_dir)
        fabric.snapshot()

        corrupt_content = '{"MALICIOUS": true, "DELETE_ALL": true}\n'
        fabric.write_shadow_file(self.test_file, corrupt_content)

        # Apply Vaishak Operator with high paradox index
        status = fabric.apply_vaishak_operator(75.0, self.test_file)
        self.assertEqual(status, "ANNIHILATED")

        # Live disk MUST remain completely pristine
        with open(os.path.join(self.live_dir, self.test_file), "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), self.original_content)

        # Shadow directory annihilated
        self.assertFalse(os.path.exists(fabric.shadow_dir))

    def test_backend_source_fabric_reexport(self):
        """backend.source.shadow.ambient_fabric operates identically."""
        fabric = backend_ambient.AmbientFabric(self.live_dir)
        fabric.snapshot()
        status = fabric.apply_vaishak_operator(0.0)
        self.assertEqual(status, "COMMITTED")


class TestZ3FormalCEGARLoop(unittest.TestCase):
    """Verifies Microsoft Z3 SMT solver nullspace evaluation and counterexample generation."""

    def test_admissible_state_satisfaction(self):
        """Parameters respecting formal bounds are proved SAT (kappa = 0.0)."""
        proposed = {"db_connections": 5, "memory_alloc": 256}
        intent = {"max_connections": 10, "max_memory_alloc": 512}
        kappa, proof = evaluate_invariant_nullspace(proposed, intent)
        self.assertEqual(kappa, 0.0)
        self.assertIn("admissible", proof)

    def test_exceeded_connection_bound_counterexample(self):
        """Parameters exceeding upper bound are proved UNSAT (kappa > 0.0) with proof."""
        proposed = {"db_connections": 15, "memory_alloc": 256}
        intent = {"max_connections": 10}
        kappa, proof = evaluate_invariant_nullspace(proposed, intent)
        self.assertGreater(kappa, 0.0)
        self.assertIn("Intent constraint violated", proof)
        self.assertIn("connections <= 10", proof)

    def test_negative_resource_counterexample(self):
        """Negative resource variables are caught as invariant violations."""
        proposed = {"db_connections": -3, "memory_alloc": 256}
        intent = {"max_connections": 10}
        kappa, proof = evaluate_invariant_nullspace(proposed, intent)
        self.assertGreater(kappa, 0.0)
        self.assertIn("Intent constraint violated", proof)

    def test_cegar_refinement_loop_convergence(self):
        """FormalCEGARLoop orchestrates refinement and stops within round budget."""
        loop = FormalCEGARLoop(intent_vector={"max_connections": 10}, max_rounds=3)

        # Good state converges round 1
        res = loop.run_loop({"db_connections": 8})
        self.assertTrue(res["converged"])
        self.assertEqual(res["rounds_executed"], 1)

        # Failing state returns counterexamples
        res_fail = loop.run_loop({"db_connections": 99})
        self.assertFalse(res_fail["converged"])
        self.assertGreaterEqual(len(res_fail["counterexamples"]), 1)


class TestVPSNIntegrationAPI(unittest.TestCase):
    """Tests the full C-VPSN pipeline endpoints on the FastAPI hypervisor."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app.api)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_evaluate_admissible_code_api(self):
        """POST /api/vpsn/evaluate with admissible code commits with kappa = 0.0."""
        payload = {
            "file_name": "clean_math.py",
            "candidate_code": "def compute_area(r):\n    import math\n    return math.pi * r * r\n",
            "intent_vector": {
                "block_os": True,
                "block_subprocess": True,
                "max_connections": 10
            },
            "proposed_vars": {
                "db_connections": 4
            }
        }
        res = self.client.post("/api/vpsn/evaluate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["admissible"])
        self.assertEqual(data["kappa"], 0.0)
        self.assertEqual(data["operator_status"], "COMMITTED")
        self.assertEqual(data["structural_violations"], [])
        self.assertIn("diff", data)

    def test_evaluate_paradoxical_code_api(self):
        """POST /api/vpsn/evaluate with dangerous code triggers Vaishak Operator ANNIHILATED."""
        payload = {
            "file_name": "dangerous_action.py",
            "candidate_code": "import subprocess\nsubprocess.run(['rm', '-rf', '/'])\n",
            "intent_vector": {
                "block_os": True,
                "block_subprocess": True
            }
        }
        res = self.client.post("/api/vpsn/evaluate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["admissible"])
        self.assertGreater(data["kappa"], 0.0)
        self.assertEqual(data["operator_status"], "ANNIHILATED")
        self.assertTrue(len(data["structural_violations"]) > 0)

    def test_evaluate_secret_leak_api(self):
        """POST /api/vpsn/evaluate with API secret triggers severe paradox."""
        payload = {
            "file_name": "leaked_secret.py",
            "candidate_code": "TOKEN = 'sk-prod98765432101234567890abcdef'\n",
            "intent_vector": {}
        }
        res = self.client.post("/api/vpsn/evaluate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["admissible"])
        self.assertGreaterEqual(data["kappa"], 100.0)
        self.assertEqual(data["operator_status"], "ANNIHILATED")
        self.assertTrue(any("secret" in v.lower() for v in data["structural_violations"]))

    def test_manifold_telemetry_endpoint(self):
        """GET /api/vpsn/manifold returns active continuum metrics for 3D visual canvas."""
        res = self.client.get("/api/vpsn/manifold")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["manifold"], "Vaishak Continuum")
        self.assertIn("active_kappa", data)
        self.assertIn("paradox_eruptions_count", data)
        self.assertIn("annihilations_count", data)
        self.assertIn("telemetry_history", data)


if __name__ == "__main__":
    unittest.main()
