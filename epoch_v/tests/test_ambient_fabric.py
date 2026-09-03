import unittest
from epoch_v.ambient_fabric import AuthenticationManifold
from epoch_v.geometry import MetricTensor

class AmbientFabricTests(unittest.TestCase):
    def test_dimensions_and_metric(self):
        fabric = AuthenticationManifold()
        self.assertEqual(len(fabric.snapshot()), 3)
        metric = fabric.metric.detach().tolist() if hasattr(fabric.metric, "detach") else fabric.metric
        self.assertEqual((len(metric), len(metric[0])), (3, 3))
        self.assertTrue(MetricTensor(metric).is_positive_definite())

if __name__ == "__main__":
    unittest.main()
