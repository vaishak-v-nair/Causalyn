import unittest
from epoch_v.ambient_fabric import AuthenticationManifold
from epoch_v.constraints import check_invariants, constraint_violation
from epoch_v.paradox_index import paradox_index

class ConstraintTests(unittest.TestCase):
    def test_valid_state_has_zero_paradox_index(self):
        state = AuthenticationManifold((1, 1, 1))
        self.assertEqual(constraint_violation(state), 0.0)
        self.assertTrue(all(check_invariants(state).values()))

    def test_causality_tear_is_nonzero(self):
        self.assertGreater(constraint_violation(AuthenticationManifold((0, 1, 1))), 0.0)
    def test_invalid_state_has_positive_kappa(self):
        state = AuthenticationManifold((0, 1, 1))
        self.assertGreater(paradox_index(state), 0)
        self.assertFalse(all(check_invariants(state).values()))

    def test_valid_state_has_zero_violation(self):
        state = AuthenticationManifold((1, 1, 1))
        self.assertEqual(constraint_violation(state), 0)
        self.assertTrue(all(check_invariants(state).values()))

if __name__ == "__main__":
    unittest.main()
