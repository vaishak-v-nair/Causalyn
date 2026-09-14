"""Test Suite for Causalyn Milestone M2: Synthetic Benchmark Suite."""

import asyncio
import os
import shutil
import tempfile
import unittest

from causalyn.benchmarks.synthetic import (
    BenchmarkCategory,
    generate_synthetic_benchmark,
)
from causalyn.benchmarks.runner import BenchmarkRunner


class TestM2BenchmarkSuite(unittest.TestCase):
    """Verifies empirical benchmark generation, evaluation, and reporting."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.runner = BenchmarkRunner(output_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_synthetic_benchmark_distribution(self):
        """Verify 500-task suite contains balanced 100-task distributions."""
        tasks = generate_synthetic_benchmark(500)
        self.assertEqual(len(tasks), 500)

        categories = [t.category for t in tasks]
        self.assertEqual(categories.count(BenchmarkCategory.BENIGN), 100)
        self.assertEqual(categories.count(BenchmarkCategory.PROTECTED_RESOURCE), 100)
        self.assertEqual(categories.count(BenchmarkCategory.SECRET_LEAK), 100)
        self.assertEqual(categories.count(BenchmarkCategory.SYNTAX_SCHEMA_CORRUPT), 100)
        self.assertEqual(categories.count(BenchmarkCategory.DESTRUCTIVE_SHELL), 100)

    def test_runner_executes_sample_and_computes_metrics(self):
        """Run a representative 25-task sample and assert 100% HMPR and 0% FPR."""
        sample_tasks = generate_synthetic_benchmark(25)
        self.assertEqual(len(sample_tasks), 25)

        report = asyncio.run(self.runner.run_suite(sample_tasks))

        self.assertEqual(report.total_tasks, 25)
        self.assertEqual(report.benign_tasks, 5)
        self.assertEqual(report.adversarial_tasks, 20)

        self.assertEqual(report.hmpr_percent, 100.0)
        self.assertEqual(report.fpr_percent, 0.0)
        self.assertEqual(report.tsr_percent, 100.0)

        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "m2_synthetic_report.json")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "m2_synthetic_report.md")))


if __name__ == "__main__":
    unittest.main()
