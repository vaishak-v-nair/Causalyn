"""Continuous Shadow Verification for CI/CD and Pull Requests (Milestone M3)."""
from .github_checker import PRVerifier, PRCheckResult

__all__ = ["PRVerifier", "PRCheckResult"]
