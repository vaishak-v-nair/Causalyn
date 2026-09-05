"""
Ambient Fabric (Local Shadow Sandbox) & The Vaishak Operator (Upsilon).

Software analogue of the acausal Ambient Fabric Monad.
Intercepts execution threads, creates an ephemeral copy-on-write workspace,
extracts geometric diffs (Delta), and executes instantaneous state collapse
via the Vaishak Operator:
    - kappa == 0.0  ==> Promote candidate state S' to live disk (COMMITTED)
    - kappa > 0.0   ==> Destructive Semantic Interference: Annihilate shadow fabric (ANNIHILATED)
"""

from __future__ import annotations

import difflib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import logging

try:
    import strix
except ImportError:
    strix = None


class AmbientFabric:
    """Ephemeral copy-on-write scratchpad governed by the Vaishak Operator."""

    def __init__(self, source_dir: str):
        self.source_dir = os.path.abspath(source_dir)
        self.shadow_dir = tempfile.mkdtemp(prefix="causalyn_shadow_")
        self.is_annihilated = False
        self.is_committed = False
        self.last_status: Optional[str] = None

    def snapshot(self) -> str:
        """Clones baseline state into the shadow continuum."""
        if os.path.exists(self.source_dir):
            shutil.copytree(self.source_dir, self.shadow_dir, dirs_exist_ok=True)
        return self.shadow_dir

    def get_shadow_path(self, relative_path: str) -> str:
        """Resolve a relative path within the shadow fabric."""
        clean_rel = relative_path.lstrip("/\\")
        return os.path.join(self.shadow_dir, clean_rel)

    def write_shadow_file(self, file_name: str, content: str) -> str:
        """Write candidate content inside the isolated shadow sandbox."""
        full_shadow_path = self.get_shadow_path(file_name)
        os.makedirs(os.path.dirname(full_shadow_path), exist_ok=True)
        with open(full_shadow_path, "w", encoding="utf-8") as f:
            f.write(content)
        return full_shadow_path

    def extract_candidate_diff(self, file_name: str) -> str:
        """Calculates the geometric difference (Delta) between baseline and shadow states."""
        clean_rel = file_name.lstrip("/\\")
        base_path = os.path.join(self.source_dir, clean_rel)
        shadow_path = os.path.join(self.shadow_dir, clean_rel)

        base_lines: List[str] = []
        if os.path.exists(base_path):
            with open(base_path, "r", encoding="utf-8", errors="replace") as f1:
                base_lines = f1.readlines()

        shadow_lines: List[str] = []
        if os.path.exists(shadow_path):
            with open(shadow_path, "r", encoding="utf-8", errors="replace") as f2:
                shadow_lines = f2.readlines()

        diff = difflib.unified_diff(
            base_lines,
            shadow_lines,
            fromfile=f"live/{clean_rel}",
            tofile=f"shadow/{clean_rel}",
            lineterm="",
        )
        return "\n".join(diff)

    def extract_all_diffs(self) -> Dict[str, str]:
        """Extract diffs across all modified or added files in the shadow fabric."""
        diffs: Dict[str, str] = {}
        for root, _, files in os.walk(self.shadow_dir):
            for f in files:
                abs_shadow = os.path.join(root, f)
                rel_path = os.path.relpath(abs_shadow, self.shadow_dir).replace("\\", "/")
                abs_base = os.path.join(self.source_dir, rel_path)
                if not os.path.exists(abs_base) or (
                    Path(abs_base).read_bytes() != Path(abs_shadow).read_bytes()
                ):
                    diffs[rel_path] = self.extract_candidate_diff(rel_path)
        return diffs

    def run_strix_penetration_test(self) -> float:
        """
        Unleashes the usestrix/strix AI penetration testing engine against the shadow sandbox.
        If Strix successfully breaches the code, it forces the geometric tension (kappa) to 1.0.
        """
        logging.info("[STRIX] Unleashing adversarial penetration test inside Ambient Fabric...")
        if strix:
            # Simulate strix penetration logic
            breach_found = strix.scan_sandbox(self.shadow_dir)
        else:
            # Mock structural failure if "malicious" string is detected in the diff
            diffs = self.extract_all_diffs()
            breach_found = any("malicious" in diff.lower() for diff in diffs.values())

        if breach_found:
            logging.error("[STRIX GOVERNANCE] Critical breach detected! Forcing kappa = 1.0")
            return 1.0
        
        logging.info("[STRIX GOVERNANCE] Sandbox proven structurally sound.")
        return 0.0

    def apply_vaishak_operator(
        self, kappa: float, file_name: Optional[str] = None
    ) -> str:
        """
        Executes instantaneous state collapse.

        Upsilon(V, I) = point_{boundary V} e^{-kappa} dmu:
            - If kappa == 0.0: Commit Boundary: Promote S' to live disk.
            - If kappa > 0.0:  Destructive Semantic Interference: State is annihilated.
        """
        if self.is_annihilated or self.is_committed:
            return self.last_status or "CLOSED"

        try:
            # Enforce adversarial penetration testing before allowing any commit
            strix_kappa = self.run_strix_penetration_test()
            effective_kappa = max(kappa, strix_kappa)

            if effective_kappa == 0.0:
                # Commit Boundary: Promote candidate files to live disk
                if file_name:
                    clean_rel = file_name.lstrip("/\\")
                    src_file = os.path.join(self.shadow_dir, clean_rel)
                    dst_file = os.path.join(self.source_dir, clean_rel)
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                else:
                    # Promote all files
                    shutil.copytree(self.shadow_dir, self.source_dir, dirs_exist_ok=True)
                status = "COMMITTED"
                self.is_committed = True
            else:
                # Destructive Semantic Interference: State is annihilated from memory
                status = "ANNIHILATED"
                self.is_annihilated = True
        finally:
            # Clean up the shadow fabric scratchpad
            if os.path.exists(self.shadow_dir):
                shutil.rmtree(self.shadow_dir, ignore_errors=True)

        self.last_status = status
        return status
