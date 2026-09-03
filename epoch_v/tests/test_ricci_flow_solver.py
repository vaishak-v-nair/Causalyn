import unittest
from epoch_v.ambient_fabric import AuthenticationManifold
from epoch_v.ricci_flow_solver import RicciFlowSolver, SolverStatus

class SolverTests(unittest.TestCase):
    def test_solver_reduces_causality_tear_and_schema(self):
        result = RicciFlowSolver().solve(AuthenticationManifold((0, 1, 1)))
        self.assertLessEqual(result.final_kappa, result.initial_kappa)
        self.assertEqual(len(result.final_state), 3)
        self.assertIn(result.status, (SolverStatus.CONVERGED, SolverStatus.MAX_STEPS))
        self.assertEqual(set(result.constraint_results), {
            "revoked_token_active_session", "unauthorized_authenticated_state", "out_of_bounds"})

    def test_max_steps_status_is_reported(self):
        from epoch_v.config import RuntimeConfig
        result = RicciFlowSolver(RuntimeConfig(max_steps=1, learning_rate=0.000001)).solve(
            AuthenticationManifold((0, 1, 1)))
        self.assertEqual(result.status, SolverStatus.MAX_STEPS)

if __name__ == "__main__":
    unittest.main()
