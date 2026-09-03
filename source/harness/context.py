"""
AI Harness Context - carries intent and state through the system.
Provides tools for file operations that respect shadow mode.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from ..model.world_state import WorldState, WorldStateManager


class HarnessContext:
    def __init__(self, world_state_manager: WorldStateManager, shadow_executor: Optional[Any] = None):
        self.world_state_manager = world_state_manager
        self._in_shadow = False  # set by shadow_executor when entering shadow mode
        self._shadow_dir: Optional[str] = None
        self.intent = None
        self.state: Dict[str, Any] = {}
        self.tools: Dict[str, Callable] = {}
        self.memory: Dict[str, Any] = {}
        self.budgets: Dict[str, Any] = {}
        self.retries: Dict[str, Any] = {}
        self.checkpoints: list = []
        self.shadow_executor = shadow_executor
        if self.shadow_executor is not None:
            # Link back so shadow executor can set shadow mode and dir
            self.shadow_executor.harness_context = self

        # Register default tools
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default tools like file operations."""
        self.register_tool("read_file", self.read_file)
        self.register_tool("write_file", self.write_file)
        self.register_tool("delete_file", self.delete_file)
        self.register_tool("list_files", self.list_files)
        self.register_tool("update_state", self.update_state)
        self.register_tool("get_state", self.get_state)

    def register_tool(self, name: str, func: Callable):
        """Register a tool that can be used during execution."""
        self.tools[name] = func

    def execute_tool(self, name: str, *args, **kwargs) -> Any:
        """Execute a registered tool."""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not registered")
        return self.tools[name](*args, **kwargs)

    def set_shadow_mode(self, in_shadow: bool):
        """Called by shadow executor to indicate shadow mode."""
        self._in_shadow = in_shadow

    def _set_shadow_dir(self, shadow_dir: Optional[str]):
        """Set the shadow directory path for file resolution."""
        self._shadow_dir = shadow_dir

    def _resolve_path(self, path: str) -> Path:
        """Resolve a path to the appropriate location based on shadow mode.
        Returns a Path object.
        """
        if not isinstance(path, str):
            raise ValueError("path must be a string")
        norm_path = path.replace('\\', '/')
        parts = [part for part in norm_path.split('/') if part]
        if any(part in (".", "..") for part in parts):
            raise ValueError("path traversal is not allowed")
        if not norm_path.startswith('/'):
            norm_path = '/' + norm_path
        # Remove double slashes
        while '//' in norm_path:
            norm_path = norm_path.replace('//', '/')
        if self._in_shadow and self._shadow_dir:
            # Use shadow directory
            base = Path(self._shadow_dir)
        else:
            # Use real directory from world state manager
            base = Path(self.world_state_manager.root_path)
        candidate = (base / norm_path.lstrip('/')).resolve()
        if candidate != base.resolve() and base.resolve() not in candidate.parents:
            raise ValueError("path escapes managed state")
        return candidate

    def read_file(self, path: str) -> Optional[str]:
        """Read a file's content."""
        try:
            full_path = self._resolve_path(path)
            if full_path.is_file():
                return full_path.read_text(encoding='utf-8')
            return None
        except Exception:
            return None

    def write_file(self, path: str, content: str) -> bool:
        """Write content to a file, creating parent directories as needed."""
        try:
            full_path = self._resolve_path(path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            if self._in_shadow and self.shadow_executor is not None:
                self.shadow_executor.record_file_write(path, content)
            return True
        except Exception:
            return False

    def delete_file(self, path: str) -> bool:
        """Delete a file."""
        try:
            full_path = self._resolve_path(path)
            if full_path.is_file():
                full_path.unlink()
                if self._in_shadow and self.shadow_executor is not None:
                    self.shadow_executor.record_file_delete(path)
                return True
            return False
        except Exception:
            return False

    def list_files(self, directory: str = "") -> list:
        """List files in a directory (relative paths)."""
        try:
            if directory == "":
                base_path = self._resolve_path("")
            else:
                base_path = self._resolve_path(directory)
            if not base_path.is_dir():
                return []
            files = []
            for item in base_path.rglob("*"):
                if item.is_file():
                    # Compute relative path from base
                    rel = item.relative_to(base_path)
                    # Convert to POSIX with leading slash
                    rel_str = '/' + str(rel).replace('\\', '/')
                    files.append(rel_str)
            return files
        except Exception:
            return []

    def update_state(self, key: str, value: Any):
        """Update a piece of state."""
        self.state[key] = value
        if self._in_shadow and self.shadow_executor is not None:
            self.shadow_executor.update_data(key, value)

    def get_state(self, key=None):
        """Get state, either specific key or entire state."""
        if key is None:
            return self.state.copy()
        return self.state.get(key)

    # Intent and memory methods
    def set_intent(self, intent):
        """Set the human intent for this execution."""
        self.intent = intent

    def get_intent(self):
        """Get the current intent."""
        return self.intent

    def remember(self, key, value):
        """Store something in memory."""
        self.memory[key] = value

    def recall(self, key, default=None):
        """Recall something from memory."""
        return self.memory.get(key, default)

    def set_budget(self, resource, limit):
        """Set a budget limit for a resource."""
        self.budgets[resource] = limit

    def get_budget(self, resource):
        """Get the budget for a resource."""
        return self.budgets.get(resource)

    def increment_retry(self, action):
        """Increment retry count for an action."""
        self.retries[action] = self.retries.get(action, 0) + 1

    def get_retry_count(self, action):
        """Get retry count for an action."""
        return self.retries.get(action, 0)

    def add_checkpoint(self, description):
        """Add a checkpoint to the execution history."""
        self.checkpoints.append({
            'description': description,
            'timestamp': None  # Could be filled with actual timestamp
        })

    def get_checkpoints(self):
        """Get all checkpoints."""
        return self.checkpoints.copy()