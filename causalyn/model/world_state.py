"""
World / State Model - represents the state of the world (isolated test environment).
Now includes pathlib-based filesystem tracking and dirty-set for efficient commits.
"""

import copy
import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class StateStatus(Enum):
    """Status of the world state."""
    CLEAN = "clean"
    DIRTY = "dirty"
    CORRUPTED = "corrupted"


@dataclass
class WorldState:
    """Represents the state of the world/environment."""
    # Core state data
    data: Dict[str, Any] = field(default_factory=dict)

    # File system representation (mapping of relative POSIX path to content string)
    # This is a snapshot of the filesystem at the time the WorldState was created.
    file_system: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    status: StateStatus = StateStatus.CLEAN
    version: int = 0
    description: str = ""

    # Tracking for verification (sets of relative paths)
    modified_files: List[str] = field(default_factory=list)
    accessed_files: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize with empty state if none provided."""
        if not self.data:
            self.data = {}
        if not self.file_system:
            self.file_system = {}

    def clone(self) -> 'WorldState':
        """Create a deep copy of the world state for shadow execution."""
        return copy.deepcopy(self)

    def compute_hash(self) -> str:
        """Compute SHA-256 fingerprint over data and filesystem (2PC Integrity)."""
        import hashlib
        raw_repr = {
            "data": self.data,
            "file_system": {
                k: (v if isinstance(v, str) else json.dumps(v, sort_keys=True))
                for k, v in sorted(self.file_system.items())
            }
        }
        serialized = json.dumps(raw_repr, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def update_data(self, key: str, value: Any):
        """Update a piece of data in the world state."""
        self.data[key] = value
        self.status = StateStatus.DIRTY
        self.version += 1

    def get_data(self, key: str, default: Any = None) -> Any:
        """Get a piece of data from the world state."""
        return self.data.get(key, default)

    def set_file_content(self, path: str, content: Any):
        """Set content of a file in the virtual file system.
        Normalizes path to POSIX style and ensures parent directories exist in the snapshot.
        """
        # Normalize path
        norm_path = self._normalize_path(path)
        # Ensure we have entries for parent directories? Not needed for file content.
        self.file_system[norm_path] = content
        if norm_path not in self.modified_files:
            self.modified_files.append(norm_path)
        self.status = StateStatus.DIRTY
        self.version += 1

    def get_file_content(self, path: str) -> Optional[str]:
        """Get content of a file from the virtual file system.
        Returns None if file does not exist.
        """
        norm_path = self._normalize_path(path)
        if norm_path in self.accessed_files:
            # Already accessed, don't duplicate
            pass
        else:
            self.accessed_files.append(norm_path)
        return self.file_system.get(norm_path)

    def delete_file(self, path: str) -> bool:
        """Delete a file from the virtual file system."""
        norm_path = self._normalize_path(path)
        if norm_path in self.file_system:
            del self.file_system[norm_path]
            if norm_path not in self.modified_files:
                self.modified_files.append(norm_path)
            self.status = StateStatus.DIRTY
            self.version += 1
            return True
        return False

    def file_exists(self, path: str) -> bool:
        """Check if a file exists in the virtual file system."""
        norm_path = self._normalize_path(path)
        return norm_path in self.file_system

    def list_files(self, directory: str = "") -> List[str]:
        """List files in a directory (simple implementation).
        Returns list of relative POSIX paths.
        """
        if not directory:
            # Return all files (simplified)
            return list(self.file_system.keys())

        # Normalize directory path
        norm_dir = self._normalize_path(directory)
        if not norm_dir.endswith('/'):
            norm_dir += '/'
        # Return paths that start with norm_dir
        return [p for p in self.file_system.keys() if p.startswith(norm_dir)]

    def apply_changes(self, changes: Dict[str, Any]):
        """Apply a set of changes to the world state.
        changes dict can have keys:
          - 'data:<key>' for data updates
          - 'file:<path>' for file content (string) or None for deletion
        """
        for key, value in changes.items():
            if key.startswith('data:'):
                data_key = key[5:]  # remove 'data:'
                if value is None:
                    self.data.pop(data_key, None)
                else:
                    self.data[data_key] = value
            elif key.startswith('file:'):
                file_path = key[5:]  # remove 'file:'
                if value is None:
                    # deletion
                    self.delete_file(file_path)
                else:
                    # set content
                    self.set_file_content(file_path, value)
            else:
                # unknown key type, ignore
                pass
        self.status = StateStatus.DIRTY
        self.version += 1

    def reset(self):
        """Reset the world state to clean state."""
        self.data = {}
        self.file_system = {}
        self.status = StateStatus.CLEAN
        self.version = 0
        self.modified_files = []
        self.accessed_files = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert world state to dictionary for serialization."""
        return {
            "data": self.data,
            "file_system": self.file_system,
            "status": self.status.value,
            "version": self.version,
            "description": self.description,
            "modified_files": self.modified_files.copy(),
            "accessed_files": self.accessed_files.copy()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorldState':
        """Create world state from dictionary."""
        state = cls()
        state.data = data.get("data", {})
        state.file_system = data.get("file_system", {})
        state.status = StateStatus(data.get("status", "clean"))
        state.version = data.get("version", 0)
        state.description = data.get("description", "")
        state.modified_files = data.get("modified_files", [])
        state.accessed_files = data.get("accessed_files", [])
        return state

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize a path to POSIX relative path (with leading slash)."""
        # Remove leading slash if we want to store without? We'll store with leading slash for ease.
        # We'll just replace backslashes and ensure it starts with /
        path = path.replace('\\', '/')
        if not path.startswith('/'):
            path = '/' + path
        # Remove double slashes
        while '//' in path:
            path = path.replace('//', '/')
        return path


class WorldStateManager:
    """Manages world state operations including snapshots and restoration.
    Also handles persistence to an actual directory on disk.
    """

    def __init__(self, root_path: Optional[str] = None):
        """
        Args:
            root_path: Path to a directory on disk that represents the real filesystem.
                       If None, uses a temporary directory (for testing).
        """
        if root_path is None:
            # Create a temporary directory for isolation
            self.root_path = Path(tempfile.mkdtemp(prefix="worldstate_"))
            self._owns_root = True
        else:
            self.root_path = Path(root_path)
            self._owns_root = False
        # Ensure root exists
        self.root_path.mkdir(parents=True, exist_ok=True)
        # Load existing files into file_system cache
        self._file_system: Dict[str, str] = {}
        self._load_filesystem()
        self.data: Dict[str, Any] = {}
        self.state_history: List[Dict[str, Any]] = []  # store snapshots of (data, file_system)
        self.snapshots: Dict[str, Dict[str, Any]] = {}  # named snapshots

    def _load_filesystem(self):
        """Load all files under root_path into the file_system cache."""
        self._file_system.clear()
        for root, dirs, files in os.walk(self.root_path):
            for f in files:
                abs_path = Path(root) / f
                rel_path = abs_path.relative_to(self.root_path)
                # Convert to POSIX path with leading slash
                rel_path_str = '/' + str(rel_path).replace('\\', '/')
                try:
                    raw_content = abs_path.read_text(encoding='utf-8')
                    try:
                        content = json.loads(raw_content)
                    except json.JSONDecodeError:
                        content = raw_content
                except Exception:
                    # Skip binary files for simplicity
                    continue
                self._file_system[rel_path_str] = content

    def _save_filesystem(self, file_system: Dict[str, str]):
        """Write the given file_system dict to disk under root_path.
        This will create, update, and delete files to match the dict exactly.
        """
        # First, delete any files that are not in the new file_system
        existing_files = set()
        for root, dirs, files in os.walk(self.root_path):
            for f in files:
                abs_path = Path(root) / f
                rel_path = abs_path.relative_to(self.root_path)
                rel_path_str = '/' + str(rel_path).replace('\\', '/')
                existing_files.add(rel_path_str)
        # Determine files to delete
        to_delete = existing_files - set(self._file_system.keys())
        for rel_path in to_delete:
            abs_path = self.root_path / rel_path.lstrip('/')
            try:
                abs_path.unlink()
            except Exception:
                pass
        # Remove empty directories (optional)
        # For simplicity, we skip directory cleanup.

        # Now write/update files
        for rel_path, content in self._file_system.items():
            abs_path = self.root_path / rel_path.lstrip('/')
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, str):
                serialized = content
            else:
                serialized = json.dumps(content)
            abs_path.write_text(serialized, encoding='utf-8')

    # --- Modification methods ---
    def set_file_content(self, path: str, content: str):
        """Set content of a file in the managed world state."""
        norm_path = WorldState._normalize_path(path)
        self._file_system[norm_path] = content
        # No need to track modifications here; we can compute on snapshot if needed.

    def get_file_content(self, path: str) -> Optional[str]:
        """Get content of a file from the managed world state."""
        norm_path = WorldState._normalize_path(path)
        return self._file_system.get(norm_path)

    def delete_file(self, path: str) -> bool:
        """Delete a file from the managed world state."""
        norm_path = WorldState._normalize_path(path)
        if norm_path in self._file_system:
            del self._file_system[norm_path]
            return True
        return False

    def file_exists(self, path: str) -> bool:
        """Check if a file exists in the managed world state."""
        norm_path = WorldState._normalize_path(path)
        return norm_path in self._file_system

    def list_files(self, directory: str = "") -> List[str]:
        """List files in a directory (relative POSIX paths)."""
        if not directory:
            return list(self._file_system.keys())
        norm_dir = WorldState._normalize_path(directory)
        if not norm_dir.endswith('/'):
            norm_dir += '/'
        return [p for p in self._file_system.keys() if p.startswith(norm_dir)]

    def update_data(self, key: str, value: Any):
        """Update a piece of data in the managed world state."""
        self.data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """Get a piece of data from the managed world state."""
        return self.data.get(key, default)

    def apply_changes(self, changes: Dict[str, Any]):
        """Apply a set of changes to the managed world state."""
        for key, value in changes.items():
            if key.startswith('data:'):
                data_key = key[5:]  # remove 'data:'
                if value is None:
                    self.data.pop(data_key, None)
                else:
                    self.data[data_key] = value
            elif key.startswith('file:'):
                file_path = key[5:]  # remove 'file:'
                if value is None:
                    # deletion
                    self.delete_file(file_path)
                else:
                    # set content
                    self.set_file_content(file_path, value)
            else:
                # unknown key type, ignore
                pass

    def get_current_state(self) -> WorldState:
        """Get a WorldState snapshot of the current world state."""
        ws = WorldState()
        ws.data = copy.deepcopy(self.data)
        ws.file_system = copy.deepcopy(self._file_system)
        ws.status = StateStatus.DIRTY if self._has_changes() else StateStatus.CLEAN
        ws.version = len(self.state_history)  # simple version
        ws.description = ""
        ws.modified_files = []  # snapshot doesn't track modifications
        ws.accessed_files = []
        return ws

    def _has_changes(self) -> bool:
        """Check if there are uncommitted changes in data or file_system."""
        # We don't track changes in data vs snapshot; we'll just assume dirty if state_history not empty?
        # For simplicity, we'll consider the manager always dirty unless we have a clean snapshot.
        # We'll implement a proper dirty flag later if needed.
        return len(self.state_history) > 0

    def create_snapshot(self, name: str) -> WorldState:
        """Create a named snapshot of the current state."""
        snapshot = self.get_current_state()
        self.snapshots[name] = {
            'data': copy.deepcopy(snapshot.data),
            'file_system': copy.deepcopy(snapshot.file_system)
        }
        return snapshot

    def restore_snapshot(self, name: str) -> bool:
        """Restore a named snapshot as current state."""
        if name in self.snapshots:
            snap = self.snapshots[name]
            self.data = copy.deepcopy(snap['data'])
            self._file_system = copy.deepcopy(snap['file_system'])
            self._save_filesystem(self._file_system)
            return True
        return False

    def add_to_history(self, state: WorldState):
        """Add a state to the history."""
        self.state_history.append({
            'data': copy.deepcopy(state.data),
            'file_system': copy.deepcopy(state.file_system)
        })

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the state history."""
        return [{'data': copy.deepcopy(h['data']),
                 'file_system': copy.deepcopy(h['file_system'])}
                for h in self.state_history]

    def clear_history(self):
        """Clear the state history."""
        self.state_history = []

    def apply_transaction(self, changes: Dict[str, Any]) -> WorldState:
        """Apply changes as a transaction, returning new state."""
        new_state = self.get_current_state()
        new_state.apply_changes(changes)
        return new_state

    def commit_transaction(self, changes: Dict[str, Any]):
        """Commit changes to the current state."""
        # Apply changes to the current state's data and file_system
        self.apply_changes(changes)
        # Persist to disk
        self._save_filesystem(self._file_system)
        # Add to history
        self.add_to_history(WorldState.from_dict({
            'data': self.data,
            'file_system': self._file_system,
            'status': 'clean',
            'version': len(self.state_history),
            'description': ''
        }))


# Example usage and testing
if __name__ == "__main__":
    # Create a world state manager with a temporary root
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WorldStateManager(tmpdir)
        # Create a file
        manager.set_file_content("hello.txt", "Hello World")
        # Get current state
        state = manager.get_current_state()
        print("Initial file system:", state.file_system)
        # Modify via manager
        manager.set_file_content("/hello.txt", "Hello Updated")
        # Commit changes
        manager.commit_transaction({})
        # Verify on disk
        print("Disk content:", (manager.root_path / "hello.txt").read_text())