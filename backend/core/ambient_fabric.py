import os
import shutil
import tempfile
import uuid
import time
from pathlib import Path
from typing import Generator
from contextlib import contextmanager

class AmbientFabricException(Exception):
    """Raised when the Ambient Fabric boundary is violated."""
    pass

class AmbientFabric:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()
        if not self.workspace_root.exists():
            raise FileNotFoundError(f"Root path {workspace_root} does not exist.")

    @contextmanager
    def spawn_shadow_continuum(self, target_file: str, initial_content: str = None) -> Generator[Path, None, None]:
        """
        Provisions an isolated, ephemeral CoW sandbox for a SPECIFIC file.
        This avoids the O(N) I/O bottleneck of copying the entire workspace.
        """
        shadow_dir = Path(tempfile.mkdtemp(prefix="causalyn_fabric_"))
        source_file = self.workspace_root / target_file
        shadow_file = shadow_dir / Path(target_file).name

        try:
            shadow_file.parent.mkdir(parents=True, exist_ok=True)
            if initial_content is not None:
                shadow_file.write_text(initial_content, encoding="utf-8")
            elif source_file.exists():
                shutil.copy2(source_file, shadow_file)
            else:
                shadow_file.write_text("", encoding="utf-8")
            
            yield shadow_dir
        finally:
            # Instantaneous Nullification: Annihilate shadow continuum
            shutil.rmtree(shadow_dir, ignore_errors=True)

    def atomic_commit(self, shadow_dir: Path, target_file: str) -> None:
        """
        Commits verified state (S ∈ N_semantic) to physical host disk.
        Thread-safe across high-concurrency swarm mutations with Windows retry safety.
        """
        source_path = shadow_dir / Path(target_file).name
        target_path = self.workspace_root / target_file

        if not source_path.exists():
            raise FileNotFoundError(f"Source file {source_path} missing in shadow.")

        # Ensure parent directories exist
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Unique temp destination per atomic commit to avoid collision under concurrent writes
        unique_id = uuid.uuid4().hex[:12]
        temp_dest = target_path.with_name(f"{target_path.name}.tmp_{unique_id}")
        shutil.copy2(source_path, temp_dest)

        # Retry loop for Windows filesystem locks
        max_retries = 5
        for attempt in range(max_retries):
            try:
                os.replace(temp_dest, target_path)
                break
            except PermissionError:
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.01 * (2 ** attempt))
            finally:
                if temp_dest.exists():
                    try:
                        temp_dest.unlink(missing_ok=True)
                    except Exception:
                        pass


