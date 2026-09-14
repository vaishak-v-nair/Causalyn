"""
Shadow Execution - isolated runtime for candidate actions.
Intercepts actions and runs them in a safe environment before allowing commit.
Now uses a temporary directory as a real filesystem shadow.
"""

import copy
import difflib
import json
import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from ..model.world_state import WorldState, WorldStateManager
from ..harness.context import HarnessContext


class ExecutionMode(Enum):
    """Modes of execution."""
    SHADOW = "shadow"      # Run in isolated environment (default for untrusted actions)
    DIRECT = "direct"      # Run directly (for trusted/system actions)
    SIMULATE = "simulate"  # Simulate without actual execution


class ShadowExecutor:
    """Executes actions in a shadow environment for safety evaluation."""

    def __init__(self, world_state_manager: WorldStateManager, harness_context: Optional[HarnessContext] = None):
        self.world_state_manager = world_state_manager
        self.harness_context = harness_context
        self.shadow_dir: Optional[str] = None
        self.original_state_snapshot: Optional[Dict[str, Any]] = None
        self.execution_log: List[Dict[str, Any]] = []
        self.is_shadow_active = False
        self.shadow_data: Dict[str, Any] = {}
        self.shadow_overrides: Dict[str, Any] = {}

    def enter_shadow_mode(self) -> WorldState:
        """Enter shadow execution mode - creates isolated copy of current state using a temp dir."""
        if self.is_shadow_active:
            raise RuntimeError("Already in shadow mode")

        # Notify harness context that we are entering shadow mode
        if self.harness_context:
            self.harness_context.set_shadow_mode(True)

        # Create a temporary directory for shadow filesystem
        self.shadow_dir = tempfile.mkdtemp(prefix="shadow_")
        # Tell the harness context about the shadow directory
        if self.harness_context:
            self.harness_context._set_shadow_dir(self.shadow_dir)

        # Snapshot current world state (data and file system)
        current_state = self.world_state_manager.get_current_state()
        # Deep copy data
        data_snapshot = copy.deepcopy(current_state.data)
        # Replicate file system into shadow dir
        for rel_path, content in current_state.file_system.items():
            abs_path = os.path.join(self.shadow_dir, rel_path.lstrip('/'))
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            if isinstance(content, str):
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(abs_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f)
        self.original_state_snapshot = {
            'data': data_snapshot,
            'file_system': copy.deepcopy(current_state.file_system)
        }
        self.shadow_data = copy.deepcopy(data_snapshot)
        self.shadow_overrides = {}
        self.is_shadow_active = True
        self.execution_log = []

        # Return a WorldState that points to shadow dir? We'll just return the original state snapshot
        # but the executor will operate on the shadow dir.
        # For compatibility, we return a WorldState with data snapshot and empty file_system
        # (the executor will use its own shadow_dir for file ops).
        ws = WorldState()
        ws.data = copy.deepcopy(data_snapshot)
        ws.file_system = {}  # we will not use this; we rely on shadow_dir
        return ws

    def reset_shadow_sandbox(self) -> None:
        """Reset shadow sandbox to initial snapshot (Destructive Semantic Interference)."""
        if not self.is_shadow_active or not self.shadow_dir or not self.original_state_snapshot:
            return
        for item in os.listdir(self.shadow_dir):
            p = os.path.join(self.shadow_dir, item)
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            else:
                try:
                    os.unlink(p)
                except OSError:
                    pass
        for rel_path, content in self.original_state_snapshot['file_system'].items():
            abs_path = os.path.join(self.shadow_dir, rel_path.lstrip('/'))
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            if isinstance(content, (dict, list)):
                with open(abs_path, 'w') as f:
                    json.dump(content, f)
            else:
                with open(abs_path, 'w') as f:
                    f.write(str(content))
        self.shadow_data = copy.deepcopy(self.original_state_snapshot['data'])
        self.shadow_overrides = {}
        self.execution_log.append({
            "action": "destructive_semantic_interference_reset",
            "timestamp": time.time(),
        })

    def exit_shadow_mode(self, commit: bool = False) -> Optional[WorldState]:
        """Exit shadow execution mode.

        Args:
            commit: If True, commit changes to real state; if False, discard changes

        Returns:
            The shadow state if commit=True, None otherwise
        """
        if not self.is_shadow_active:
            raise RuntimeError("Not in shadow mode")

        result_state = None
        if commit and self.shadow_dir:
            # Compute changes by comparing shadow dir to original snapshot
            changes = self._compute_changes()
            self.world_state_manager.commit_transaction(changes)
            # Build a WorldState reflecting the new state (optional)
            result_state = WorldState()
            result_state.data = copy.deepcopy(self.original_state_snapshot['data'])
            # Apply changes to data
            for key, val in changes.items():
                if not key.startswith('file:'):
                    if val is None:
                        result_state.data.pop(key, None)
                    else:
                        result_state.data[key] = val
            # For file changes, we could update file_system but not needed now.
            result_state.file_system = copy.deepcopy(self.original_state_snapshot['file_system'])
            # Apply file changes
            for key, val in changes.items():
                if key.startswith('file:'):
                    rel_path = key[5:]  # remove 'file:'
                    if val is None:
                        result_state.file_system.pop(rel_path, None)
                    else:
                        result_state.file_system[rel_path] = val

        # Clean up shadow directory
        if self.shadow_dir and os.path.exists(self.shadow_dir):
            shutil.rmtree(self.shadow_dir, ignore_errors=True)
        self.shadow_dir = None
        self.original_state_snapshot = None
        self.shadow_data = {}
        self.shadow_overrides = {}
        # Notify harness context that we are leaving shadow mode
        if self.harness_context:
            self.harness_context.set_shadow_mode(False)
            self.harness_context._set_shadow_dir(None)
        self.is_shadow_active = False
        self.execution_log = []

        return result_state

    def execute_action(self, action: Callable, *args, **kwargs) -> Any:
        """Execute an action in the current mode (shadow or direct).

        Args:
            action: Function to execute
            *args, **kwargs: Arguments to pass to the action

        Returns:
            Result of the action execution
        """
        if self.is_shadow_active:
            return self._execute_in_shadow(action, *args, **kwargs)
        else:
            return self._execute_direct(action, *args, **kwargs)

    def _execute_in_shadow(self, action: Callable, *args, **kwargs) -> Any:
        """Execute action in shadow environment using the shadow directory."""
        if not self.shadow_dir:
            raise RuntimeError("Shadow directory not initialized")

        # Record the action attempt
        action_record = {
            'action': action.__name__ if hasattr(action, '__name__') else str(action),
            'args': str(args),
            'kwargs': str(kwargs),
            'timestamp': None  # Could add actual timestamp
        }

        try:
            # Execute the action. The action should use the harness context's tools,
            # which will route to the shadow directory because the harness context
            # knows we are in shadow mode (via set_shadow_mode) and has the shadow directory set.
            result = action(*args, **kwargs)

            action_record['status'] = 'success'
            action_record['result'] = str(result)[:200]  # Limit length
            self.execution_log.append(action_record)

            return result
        except Exception as e:
            action_record['status'] = 'error'
            action_record['error'] = str(e)
            self.execution_log.append(action_record)
            raise

    def _execute_direct(self, action: Callable, *args, **kwargs) -> Any:
        """Execute action directly (bypass shadow)."""
        action_record = {
            'action': action.__name__ if hasattr(action, '__name__') else str(action),
            'args': str(args),
            'kwargs': str(kwargs),
            'mode': 'direct'
        }

        try:
            result = action(*args, **kwargs)
            action_record['status'] = 'success'
            self.execution_log.append(action_record)
            return result
        except Exception as e:
            action_record['status'] = 'error'
            action_record['error'] = str(e)
            self.execution_log.append(action_record)
            raise

    def _compute_changes(self) -> Dict[str, Any]:
        """Compute changes made during shadow execution by comparing shadow dir to snapshot."""
        if not self.shadow_dir or not self.original_state_snapshot:
            return {}

        changes = {}
        snap_data = self.original_state_snapshot['data']
        snap_fs = self.original_state_snapshot['file_system']

        # Data changes are maintained explicitly by update_data so they are
        # included in the same transactional diff as filesystem changes.
        for key, value in self.shadow_data.items():
            if snap_data.get(key) != value or key not in snap_data:
                changes[f'data:{key}'] = copy.deepcopy(value)
        for key in snap_data:
            if key not in self.shadow_data:
                changes[f'data:{key}'] = None

        # File changes: walk shadow dir and compare to snapshot
        for root, dirs, files in os.walk(self.shadow_dir):
            for f in files:
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, self.shadow_dir)
                # Normalize to start with /
                rel_path = '/' + rel_path.replace(os.sep, '/')
                # Read content
                try:
                    with open(abs_path, 'r', encoding='utf-8') as fh:
                        raw_content = fh.read()
                    original = snap_fs.get(rel_path)
                    if original is not None and not isinstance(original, str):
                        try:
                            content = json.loads(raw_content)
                        except json.JSONDecodeError:
                            content = raw_content
                    else:
                        content = raw_content
                except Exception:
                    content = None
                # Compare to snapshot
                if rel_path in snap_fs:
                    if snap_fs[rel_path] != content:
                        changes[f'file:{rel_path}'] = content
                else:
                    # New file
                    changes[f'file:{rel_path}'] = content
        # Check for deletions
        for rel_path, snap_content in snap_fs.items():
            abs_path = os.path.join(self.shadow_dir, rel_path.lstrip('/'))
            if not os.path.exists(abs_path):
                changes[f'file:{rel_path}'] = None  # deleted

        for rel_path, content in self.shadow_overrides.items():
            if content is None:
                changes[f'file:{rel_path}'] = None
            elif snap_fs.get(rel_path) != content:
                changes[f'file:{rel_path}'] = copy.deepcopy(content)

        return changes
    
    def compute_unified_diffs(self) -> Dict[str, str]:
        """Compute human-readable unified diffs for all modified/added/deleted files."""
        if not self.shadow_dir or not self.original_state_snapshot:
            return {}
        diffs = {}
        snap_fs = self.original_state_snapshot.get('file_system', {})
        changes = self._compute_changes()
        for key, val in changes.items():
            if key.startswith('file:'):
                filepath = key[5:]
                orig_raw = snap_fs.get(filepath, "")
                if isinstance(orig_raw, (dict, list)):
                    orig_lines = json.dumps(orig_raw, indent=2).splitlines(keepends=True)
                else:
                    orig_lines = str(orig_raw or "").splitlines(keepends=True)
                
                if val is None:
                    new_lines = []
                elif isinstance(val, (dict, list)):
                    new_lines = json.dumps(val, indent=2).splitlines(keepends=True)
                else:
                    new_lines = str(val).splitlines(keepends=True)
                
                diff_lines = list(difflib.unified_diff(
                    orig_lines,
                    new_lines,
                    fromfile=f"a{filepath}",
                    tofile=f"b{filepath}"
                ))
                if diff_lines:
                    diffs[filepath] = "".join(diff_lines)
                elif val is not None and not orig_lines:
                    diffs[filepath] = "".join([f"+{l}" for l in new_lines])
        return diffs

    def record_file_write(self, path: str, content: Any) -> None:
        """Preserve the logical type of content written through the harness."""
        if not self.is_shadow_active:
            raise RuntimeError("File updates require active shadow mode")
        self.shadow_overrides[WorldState._normalize_path(path)] = copy.deepcopy(content)

    def record_file_delete(self, path: str) -> None:
        """Record a logical deletion made through the harness."""
        if not self.is_shadow_active:
            raise RuntimeError("File updates require active shadow mode")
        self.shadow_overrides[WorldState._normalize_path(path)] = None

    def update_data(self, key: str, value: Any) -> None:
        """Update candidate data without touching the real world."""
        if not self.is_shadow_active:
            raise RuntimeError("Data updates require active shadow mode")
        self.shadow_data[key] = copy.deepcopy(value)

    def get_shadow_state(self) -> WorldState:
        """Materialize the current candidate state for verification."""
        if not self.is_shadow_active or not self.original_state_snapshot:
            raise RuntimeError("Shadow mode is not active")

        file_system: Dict[str, str] = {}
        assert self.shadow_dir is not None
        for root, _, files in os.walk(self.shadow_dir):
            for filename in files:
                path = os.path.join(root, filename)
                rel_path = "/" + os.path.relpath(path, self.shadow_dir).replace(os.sep, "/")
                try:
                    with open(path, encoding="utf-8") as handle:
                        raw_content = handle.read()
                    original = self.original_state_snapshot["file_system"].get(rel_path)
                    if original is not None and not isinstance(original, str):
                        try:
                            file_system[rel_path] = json.loads(raw_content)
                        except json.JSONDecodeError:
                            file_system[rel_path] = raw_content
                    else:
                        file_system[rel_path] = raw_content
                except (OSError, UnicodeDecodeError):
                    continue

        for rel_path, content in self.shadow_overrides.items():
            if content is None:
                file_system.pop(rel_path, None)
            else:
                file_system[rel_path] = copy.deepcopy(content)

        return WorldState(
            data=copy.deepcopy(self.shadow_data),
            file_system=file_system,
        )

    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get the log of actions executed in shadow mode."""
        return self.execution_log.copy()

    def is_in_shadow_mode(self) -> bool:
        """Check if currently in shadow execution mode."""
        return self.is_shadow_active