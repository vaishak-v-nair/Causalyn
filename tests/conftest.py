"""Shared test fixtures for Causalyn tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository with an initial commit.

    Returns the path to the repo.
    """
    repo = tmp_path / "test_repo"
    repo.mkdir()

    # Initialize git repo
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@causalyn.dev")
    _git(repo, "config", "user.name", "Causalyn Test")

    # Create an initial file and commit
    hello = repo / "hello.py"
    hello.write_text('def greet():\n    return "Hello"\n', encoding="utf-8")

    test_file = repo / "test_hello.py"
    test_file.write_text(
        'from hello import greet\n\n'
        'def test_greet():\n'
        '    assert greet() == "Hello"\n',
        encoding="utf-8",
    )

    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "Initial commit")

    return repo


@pytest.fixture
def tmp_git_repo_with_steps(tmp_git_repo: Path) -> Path:
    """A git repo with several simulated agent steps already committed.

    Step sequence:
    - Initial: hello.py with greet() returning "Hello"
    - Step 0: Add math.py with add() function (good step)
    - Step 1: Add utils.py with helper (good step)
    - Step 2: Modify hello.py — break greet() to return wrong value (BAD STEP)
    - Step 3: Add config.py (unrelated, good step)
    - Step 4: Add more to utils.py (builds on broken state)
    """
    repo = tmp_git_repo

    # Step 0: Add math module
    (repo / "math_ops.py").write_text(
        'def add(a, b):\n    return a + b\n', encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "Step 0: add math_ops.py")

    # Step 1: Add utils
    (repo / "utils.py").write_text(
        'def format_name(name):\n    return name.strip().title()\n', encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "Step 1: add utils.py")

    # Step 2: BREAK hello.py — the root cause
    (repo / "hello.py").write_text(
        'def greet():\n    return "Goodbye"  # BUG: wrong return value\n', encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "Step 2: modify hello.py (introduces bug)")

    # Step 3: Unrelated change
    (repo / "config.py").write_text(
        'DEBUG = True\nVERSION = "1.0"\n', encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "Step 3: add config.py")

    # Step 4: More utils (builds on broken state)
    (repo / "utils.py").write_text(
        'def format_name(name):\n    return name.strip().title()\n\n'
        'def to_upper(s):\n    return s.upper()\n', encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "Step 4: extend utils.py")

    return repo


def _git(repo: Path, *args: str) -> str:
    """Run a git command in the given repo."""
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout
