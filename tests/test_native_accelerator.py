"""Tests for causalyn.engine.native_accelerator (Rust native kernel + Python fallback)."""

import hashlib
import unittest
from causalyn.engine.native_accelerator import NativeKernelBridge, get_native_accelerator


class TestNativeAccelerator(unittest.TestCase):
    def setUp(self):
        self.kernel = get_native_accelerator()

    def test_native_loaded(self):
        """Verify that native kernel is compiled and loaded in the environment."""
        self.assertTrue(self.kernel.is_native, "Rust causalyn_core.dll should be loaded natively.")

    def test_shannon_entropy(self):
        """Verify Shannon entropy calculation."""
        # Repetitive string should have 0 entropy
        self.assertAlmostEqual(self.kernel.compute_shannon_entropy("aaaaaaaaaaaa"), 0.0, places=4)

        # High-entropy random-like token
        high_entropy_tok = "sK-93jD71!aL#001zq_P8$kLz0"
        entropy = self.kernel.compute_shannon_entropy(high_entropy_tok)
        self.assertGreater(entropy, 3.8)

        # Empty string
        self.assertEqual(self.kernel.compute_shannon_entropy(""), 0.0)

    def test_scan_high_entropy_tokens(self):
        """Verify scanning of high-entropy credentials within source text."""
        code = """
        def connect():
            api_key = "sk-live-938481029384756201948573"
            simple_text = "this_is_a_normal_function_name_with_words"
            return api_key
        """
        findings = self.kernel.scan_high_entropy_tokens(code, threshold=3.5, min_token_len=16)
        self.assertTrue(len(findings) >= 1)
        self.assertTrue(any("sk-liv" in f["token"] for f in findings))

    def test_merkle_root_calculation(self):
        """Verify pairwise SHA-256 Merkle root computation."""
        # Empty tree
        empty_root = self.kernel.compute_merkle_root([])
        self.assertEqual(empty_root, hashlib.sha256(b"").hexdigest())

        # Single leaf
        leaf1 = hashlib.sha256(b"file1_content").hexdigest()
        root1 = self.kernel.compute_merkle_root([leaf1])
        self.assertEqual(root1, leaf1)

        # Pair of leaves
        leaf2 = hashlib.sha256(b"file2_content").hexdigest()
        root_pair = self.kernel.compute_merkle_root([leaf1, leaf2])
        expected_pair = hashlib.sha256(bytes.fromhex(leaf1) + bytes.fromhex(leaf2)).hexdigest()
        self.assertEqual(root_pair, expected_pair)

        # Three leaves (odd branch)
        leaf3 = hashlib.sha256(b"file3_content").hexdigest()
        root_three = self.kernel.compute_merkle_root([leaf1, leaf2, leaf3])
        self.assertEqual(len(root_three), 64)

    def test_symplectic_curvature_metric(self):
        """Verify Vaishak Continuum continuous curvature computation."""
        # Perfectly admissible state (cs=1.0, cc=1.0) with zero gradient -> curvature = 0.0
        c_zero = self.kernel.compute_symplectic_curvature(0.0, 1.0, 1.0, (0.0, 0.0, 0.0))
        self.assertAlmostEqual(c_zero, 0.0, places=4)

        # Non-admissible state with gradient spike -> curvature > 0
        c_spike = self.kernel.compute_symplectic_curvature(0.0, 0.0, 0.0, (1.0, 1.0, 1.0))
        self.assertGreater(c_spike, 1.0)

        # Time decay decreases curvature over evolution parameter t
        c_t0 = self.kernel.compute_symplectic_curvature(0.0, 0.2, 0.2, (2.0, 2.0, 2.0))
        c_t10 = self.kernel.compute_symplectic_curvature(10.0, 0.2, 0.2, (2.0, 2.0, 2.0))
        self.assertLess(c_t10, c_t0)

    def test_pure_python_fallback(self):
        """Verify fallback behavior when native kernel is bypassed."""
        fallback_kernel = NativeKernelBridge()
        fallback_kernel._is_native = False
        fallback_kernel._lib = None

        self.assertFalse(fallback_kernel.is_native)
        ent = fallback_kernel.compute_shannon_entropy("sK-93jD71!aL#001zq_P8$kLz0")
        self.assertGreater(ent, 3.8)

        leaf1 = hashlib.sha256(b"alpha").hexdigest()
        leaf2 = hashlib.sha256(b"beta").hexdigest()
        root = fallback_kernel.compute_merkle_root([leaf1, leaf2])
        expected = hashlib.sha256(bytes.fromhex(leaf1) + bytes.fromhex(leaf2)).hexdigest()
        self.assertEqual(root, expected)


if __name__ == "__main__":
    unittest.main()
