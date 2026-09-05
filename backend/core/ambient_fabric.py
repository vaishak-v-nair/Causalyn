import os
import shutil
import tempfile
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
    def spawn_shadow_continuum(self, target_file: str) -> Generator[Path, None, None]:
        """
        Provisions an isolated, ephemeral CoW sandbox for a SPECIFIC file.
        This avoids the O(N) I/O bottleneck of copying the entire workspace.
        """
        shadow_dir = Path(tempfile.mkdtemp(prefix="causalyn_fabric_"))
        source_file = self.workspace_root / target_file
        shadow_file = shadow_dir / Path(target_file).name

        try:
            if source_file.exists():
                shutil.copy2(source_file, shadow_file)
            
            yield shadow_dir
        finally:
            # Instantaneous Nullification: Annihilate shadow continuum
            shutil.rmtree(shadow_dir, ignore_errors=True)

    def atomic_commit(self, shadow_dir: Path, target_file: str) -> None:
        """
        Commits verified state (S ∈ N_semantic) to physical host disk.
        """
        source_path = shadow_dir / Path(target_file).name
        target_path = self.workspace_root / target_file

        if not source_path.exists():
            raise FileNotFoundError(f"Source file {source_path} missing in shadow.")

        # Ensure parent directories exist
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic replacement via rename over same filesystem partition
        temp_dest = target_path.with_suffix(".tmp_causalyn")
        shutil.copy2(source_path, temp_dest)
        os.replace(temp_dest, target_path)
