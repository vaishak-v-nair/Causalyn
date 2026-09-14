"""Git-based checkpoint engine.

Creates lightweight git commits on a dedicated branch to snapshot the working
tree at each agent step.  No file copies — just git commits.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Optional

from .models import Checkpoint, StepKind


class CheckpointError(Exception):
    """Raised when a git checkpoint operation fails."""


class CheckpointEngine:
    """Manages git-based checkpoints for an agent run.

    Each checkpoint is a commit on a dedicated orphan branch.  Metadata
    (step_id, description, files_changed) is stored in the commit message
    as a JSON payload after a separator line.
    """

    METADATA_SEPARATOR = "\n---causalyn-meta---\n"

    def __init__(self, repo_dir: Path | str, branch: str = "causalyn/checkpoints"):
        self.repo_dir = Path(repo_dir).resolve()
        self.branch = branch
        self._original_branch: str | None = None
        self._checkpoints: list[Checkpoint] = []
        self._step_counter = 0
        self._load_existing_checkpoints()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def begin_session(self) -> None:
        """Record the current branch and prepare the checkpoint branch."""
        self._original_branch = self._git("rev-parse", "--abbrev-ref", "HEAD").strip()
        # Create orphan branch if it doesn't exist; if it does, reset it
        try:
            self._git("rev-parse", "--verify", self.branch)
            # Branch exists — delete and recreate so each session starts clean
            self._git("branch", "-D", self.branch)
        except CheckpointError:
            pass  # branch doesn't exist yet, that's fine

    def create(
        self,
        description: str = "",
        kind: StepKind = StepKind.UNKNOWN,
        step_id: str | None = None,
    ) -> Checkpoint:
        """Snapshot the current working tree as a checkpoint.

        Works on whatever branch is currently checked out.  We stage
        everything, commit to the checkpoint branch (using git's
        commit-tree plumbing so we never switch branches), then record
        the result.
        """
        if step_id is None:
            step_id = f"step_{self._step_counter:04d}"

        # Stage all changes (including untracked files)
        self._git("add", "-A")

        # Write the tree object
        tree_sha = self._git("write-tree").strip()

        # Build commit message with embedded metadata
        files_changed = self._get_changed_files()
        meta = {
            "step_id": step_id,
            "step_index": self._step_counter,
            "kind": kind.value,
            "files_changed": files_changed,
        }
        message = (
            f"[causalyn] {step_id}: {description}"
            f"{self.METADATA_SEPARATOR}"
            f"{json.dumps(meta)}"
        )

        # Create the commit.  If we already have checkpoints, chain from
        # the previous one; otherwise create the first commit parentless.
        parent_args: list[str] = []
        if self._checkpoints:
            parent_args = ["-p", self._checkpoints[-1].git_sha]

        commit_sha = self._git(
            "commit-tree", tree_sha, *parent_args, "-m", message
        ).strip()

        # Point the checkpoint branch at this new commit
        self._git("update-ref", f"refs/heads/{self.branch}", commit_sha)

        checkpoint = Checkpoint(
            step_id=step_id,
            step_index=self._step_counter,
            git_sha=commit_sha,
            description=description,
            kind=kind,
            files_changed=files_changed,
        )
        self._checkpoints.append(checkpoint)
        self._step_counter += 1

        # Unstage so we don't leave the index dirty for the agent
        self._git("reset", "HEAD")

        return checkpoint

    def restore(self, step_id: str) -> Checkpoint:
        """Hard-reset the working tree to a checkpoint's state.

        WARNING: this destructively modifies the working tree.  The
        bisection engine calls this during binary search.
        """
        cp = self.get(step_id)
        self._git("checkout", cp.git_sha, "--", ".")
        self._git("clean", "-fd")
        return cp

    def get(self, step_id: str) -> Checkpoint:
        """Look up a checkpoint by step_id."""
        for cp in self._checkpoints:
            if cp.step_id == step_id:
                return cp
        raise CheckpointError(f"No checkpoint found with step_id '{step_id}'")

    def diff(self, step_a: str, step_b: str) -> str:
        """Return the unified diff between two checkpoints."""
        cp_a = self.get(step_a)
        cp_b = self.get(step_b)
        try:
            return self._git("diff", cp_a.git_sha, cp_b.git_sha)
        except CheckpointError:
            return ""

    def list_all(self) -> list[Checkpoint]:
        """Return all checkpoints in creation order."""
        return list(self._checkpoints)

    def restore_original(self) -> None:
        """Restore the working tree to the state before bisection."""
        if self._original_branch:
            self._git("checkout", self._original_branch, "--", ".")

    def end_session(self) -> None:
        """Clean up: restore original branch, optionally delete checkpoint branch."""
        if self._original_branch:
            try:
                self._git("checkout", self._original_branch, "--", ".")
            except CheckpointError:
                pass

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _git(self, *args: str) -> str:
        """Run a git command and return stdout.  Raises CheckpointError on failure."""
        cmd = ["git", *args]
        result = subprocess.run(
            cmd,
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise CheckpointError(
                f"git {' '.join(args)} failed (rc={result.returncode}): {result.stderr.strip()}"
            )
        return result.stdout

    def _get_changed_files(self) -> list[str]:
        """Return list of files with staged changes."""
        try:
            output = self._git("diff", "--cached", "--name-only")
            return [f for f in output.strip().splitlines() if f]
        except CheckpointError:
            return []

    def _load_existing_checkpoints(self) -> None:
        """Load checkpoints from the git branch history."""
        try:
            # Check if the branch exists
            self._git("rev-parse", "--verify", f"refs/heads/{self.branch}")
        except CheckpointError:
            return  # Branch does not exist yet

        try:
            # Get all commits on the branch in reverse chronological (oldest first)
            output = self._git("log", "--reverse", "--format=%H%x00%B%x00---end-commit---", f"refs/heads/{self.branch}")
            commits = output.split("---end-commit---")
            for commit in commits:
                commit = commit.strip()
                if not commit:
                    continue
                parts = commit.split("\x00")
                if len(parts) >= 2:
                    git_sha = parts[0].strip()
                    message = parts[1].strip()
                    if self.METADATA_SEPARATOR in message:
                        desc_part, meta_part = message.split(self.METADATA_SEPARATOR, 1)
                        try:
                            meta = json.loads(meta_part)
                            # Handle description: strip the "[causalyn] step_X: " prefix if present
                            desc = desc_part
                            if desc.startswith("[causalyn] "):
                                desc = desc.split(": ", 1)[1] if ": " in desc else desc

                            cp = Checkpoint(
                                step_id=meta.get("step_id", ""),
                                step_index=meta.get("step_index", 0),
                                git_sha=git_sha,
                                description=desc,
                                kind=StepKind(meta.get("kind", StepKind.UNKNOWN.value)),
                                files_changed=meta.get("files_changed", []),
                            )
                            self._checkpoints.append(cp)
                            self._step_counter = max(self._step_counter, cp.step_index + 1)
                        except json.JSONDecodeError:
                            pass
        except CheckpointError:
            pass
