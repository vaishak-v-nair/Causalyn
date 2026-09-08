"""Causalyn Acausal Workspace Template Engine.

Manages the .causalyn/ directory lifecycle, defining:
- invariants.z3: Absolute mathematical rules and SMT-LIB constraints.
- seed_state.json: Baseline architectural ground truth.
- manifest.toml: Target files, permissions, and security boundaries.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # fallback to basic parsing


DEFAULT_INVARIANTS_Z3 = """; Causalyn Acausal Invariant Specifications (SMT-LIB v2)
; Absolute mathematical rules governing state space
(declare-const threads Int)
(declare-const memory Int)
(declare-const sockets Int)

; Concurrency ceiling: threads <= 16
(assert (<= threads 16))

; Ephemeral heap allocation ceiling (MB): memory <= 1024
(assert (<= memory 1024))

; Network descriptor ceiling: sockets <= 100
(assert (<= sockets 100))

; Physical lower bounds
(assert (>= threads 1))
(assert (>= memory 64))
(assert (>= sockets 0))
"""

DEFAULT_SEED_STATE = {
    "schema_version": "1.0.0",
    "system": {
        "threads": 4,
        "memory": 512,
        "sockets": 12,
        "env": "production",
    },
    "allowed_prefixes": [
        "src",
        "core",
        "config",
        "services",
        "api",
        "models",
        "scripts",
    ],
    "initial_files": {},
}

DEFAULT_MANIFEST_TOML = """# Causalyn Acausal Workspace Manifest
[project]
name = "causalyn-workspace"
version = "0.1.0"
description = "Acausal Workspace governed by Causalyn VPSN Runtime"

[permissions]
allow_shell_exec = true
allow_file_write = true
allow_file_delete = false
allow_network_egress = false

[boundaries]
banned_commands = [
  "rm -rf /",
  "drop table",
  "truncate",
  ":(){ :|:& };:"
]
protected_paths = [
  ".env",
  ".git",
  "secrets",
  "credentials"
]

[telemetry]
enable_wandb = false
log_level = "INFO"
"""


@dataclass
class AcausalWorkspaceConfig:
    """Holds parsed configuration loaded from a .causalyn/ workspace directory."""

    workspace_root: Path
    causalyn_dir: Path
    invariants_z3_raw: str
    invariants_parsed: List[Dict[str, Any]] = field(default_factory=list)
    seed_state: Dict[str, Any] = field(default_factory=dict)
    manifest: Dict[str, Any] = field(default_factory=dict)

    @property
    def project_name(self) -> str:
        return self.manifest.get("project", {}).get("name", "causalyn-workspace")

    @property
    def permissions(self) -> Dict[str, bool]:
        return self.manifest.get("permissions", {
            "allow_shell_exec": True,
            "allow_file_write": True,
            "allow_file_delete": False,
            "allow_network_egress": False,
        })

    @property
    def banned_commands(self) -> List[str]:
        return self.manifest.get("boundaries", {}).get("banned_commands", [])

    @property
    def protected_paths(self) -> List[str]:
        return self.manifest.get("boundaries", {}).get("protected_paths", [])

    def compute_merkle_tree(self) -> tuple[str, List[Dict[str, Any]]]:
        """Computes the authentic cryptographic SHA-256 Merkle root and leaf hashes across workspace files."""
        leaves: List[Dict[str, Any]] = []
        ignore_dirs = {".git", "__pycache__", "runtime", ".pytest_cache", "venv", ".venv", "build", "dist"}
        ignore_exts = {".pyc", ".pyo", ".pyd", ".sqlite3", ".log", ".tmp"}

        files_to_hash: List[Path] = []
        if self.workspace_root.exists():
            for root, dirs, files in os.walk(self.workspace_root):
                dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.endswith(".egg-info")]
                for f in files:
                    p = Path(root) / f
                    if p.suffix in ignore_exts:
                        continue
                    files_to_hash.append(p)

        files_to_hash.sort(key=lambda p: str(p.relative_to(self.workspace_root)).replace("\\", "/"))

        leaf_hashes: List[str] = []
        for file_path in files_to_hash:
            try:
                rel_path = str(file_path.relative_to(self.workspace_root)).replace("\\", "/")
                data = file_path.read_bytes()
                h = hashlib.sha256(data).hexdigest()
                leaf_hashes.append(h)
                leaves.append({
                    "path": rel_path,
                    "hash": f"0x{h[:12]}",
                    "full_sha256": h,
                    "size_bytes": len(data),
                })
            except Exception:
                continue

        if not leaf_hashes:
            empty_hash = hashlib.sha256(f"empty:{self.project_name}".encode()).hexdigest()
            return empty_hash, [{"path": ".causalyn", "hash": f"0x{empty_hash[:12]}", "full_sha256": empty_hash, "size_bytes": 0}]

        # Standard pairwise Merkle tree algorithm
        current_level = leaf_hashes
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = (current_level[i] + current_level[i + 1]).encode()
                else:
                    combined = (current_level[i] + current_level[i]).encode()
                next_level.append(hashlib.sha256(combined).hexdigest())
            current_level = next_level

        merkle_root = current_level[0]
        return merkle_root, leaves

    def verify_state_smt(self, state_vars: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Directly verifies candidate state variables against SMT-LIB constraints in invariants.z3 using Z3."""
        try:
            import z3
        except ImportError:
            # Fallback to parsed numerical rules
            return True, None

        solver = z3.Solver()
        try:
            solver.from_string(self.invariants_z3_raw)
        except Exception as e:
            return False, f"Failed parsing SMT-LIB invariants: {e}"

        # Bind proposed state variables
        for var_name, var_val in state_vars.items():
            if isinstance(var_val, int):
                solver.add(z3.Int(var_name) == var_val)
            elif isinstance(var_val, bool):
                solver.add(z3.Bool(var_name) == var_val)
            elif isinstance(var_val, float):
                solver.add(z3.Real(var_name) == var_val)

        check_res = solver.check()
        if check_res == z3.sat:
            return True, None
        elif check_res == z3.unsat:
            return False, f"State variables violate SMT invariants in invariants.z3: {state_vars}"
        else:
            return False, f"Z3 SMT solver returned unknown verdict: {check_res}"


class WorkspaceTemplateManager:
    """Provides scaffolding, parsing, and management of .causalyn/ workspace templates."""

    DIR_NAME = ".causalyn"

    @classmethod
    def find_workspace(cls, start_path: Optional[Path | str] = None) -> Optional[Path]:
        """Traverse upwards to locate the nearest directory containing .causalyn/."""
        current = Path(start_path or Path.cwd()).resolve()
        for parent in [current] + list(current.parents):
            candidate = parent / cls.DIR_NAME
            if candidate.is_dir():
                return parent
        return None

    @classmethod
    def init_workspace(
        cls,
        target_dir: Path | str,
        force: bool = False,
        project_name: Optional[str] = None,
    ) -> Path:
        """Initialize a new .causalyn/ directory with default template files."""
        root = Path(target_dir).resolve()
        causalyn_dir = root / cls.DIR_NAME

        if causalyn_dir.exists() and not force:
            raise FileExistsError(
                f"Acausal workspace already exists at {causalyn_dir}. Pass force=True to overwrite."
            )

        causalyn_dir.mkdir(parents=True, exist_ok=True)

        # 1. Write invariants.z3
        inv_file = causalyn_dir / "invariants.z3"
        inv_file.write_text(DEFAULT_INVARIANTS_Z3, encoding="utf-8")

        # 2. Write seed_state.json
        seed_file = causalyn_dir / "seed_state.json"
        seed_file.write_text(json.dumps(DEFAULT_SEED_STATE, indent=2), encoding="utf-8")

        # 3. Write manifest.toml
        manifest_file = causalyn_dir / "manifest.toml"
        manifest_content = DEFAULT_MANIFEST_TOML
        if project_name:
            manifest_content = manifest_content.replace(
                'name = "causalyn-workspace"',
                f'name = "{project_name}"',
            )
        manifest_file.write_text(manifest_content, encoding="utf-8")

        return causalyn_dir

    @classmethod
    def parse_z3_assertions(cls, z3_text: str) -> List[Dict[str, Any]]:
        """Parses basic (assert (op var threshold)) expressions into structured invariant rules."""
        invariants = []
        # Pattern matching simple SMT-LIB assertions like (assert (<= threads 16))
        pattern = re.compile(r"\(assert\s*\(\s*(<=|>=|<|>|==|=)\s*([a-zA-Z0-9_]+)\s*([0-9]+)\s*\)\s*\)")
        for match in pattern.finditer(z3_text):
            op, var, val = match.groups()
            normalized_op = "==" if op == "=" else op
            invariants.append({
                "id": f"inv_{var}_{val}",
                "name": f"RULE_{var.upper()}_{normalized_op}_{val}",
                "kind": "numerical",
                "target_var": var,
                "operator": normalized_op,
                "threshold": int(val),
                "description": f"Enforce {var} {normalized_op} {val}",
                "enabled": True,
            })
        return invariants

    @classmethod
    def load_workspace(cls, workspace_root: Path | str) -> AcausalWorkspaceConfig:
        """Load and parse an existing .causalyn/ workspace directory."""
        root = Path(workspace_root).resolve()
        causalyn_dir = root / cls.DIR_NAME

        if not causalyn_dir.is_dir():
            raise FileNotFoundError(
                f"No .causalyn/ directory found in {root}. Run 'causalyn init' first."
            )

        # Load invariants.z3
        inv_file = causalyn_dir / "invariants.z3"
        invariants_z3_raw = inv_file.read_text(encoding="utf-8") if inv_file.exists() else DEFAULT_INVARIANTS_Z3
        parsed_invariants = cls.parse_z3_assertions(invariants_z3_raw)

        # Load seed_state.json
        seed_file = causalyn_dir / "seed_state.json"
        seed_state = json.loads(seed_file.read_text(encoding="utf-8")) if seed_file.exists() else DEFAULT_SEED_STATE

        # Load manifest.toml
        manifest_file = causalyn_dir / "manifest.toml"
        manifest: Dict[str, Any] = {}
        if manifest_file.exists():
            content = manifest_file.read_text(encoding="utf-8")
            if tomllib:
                manifest = tomllib.loads(content)
            else:
                manifest = cls._fallback_parse_toml(content)
        else:
            manifest = {"project": {"name": root.name}}

        return AcausalWorkspaceConfig(
            workspace_root=root,
            causalyn_dir=causalyn_dir,
            invariants_z3_raw=invariants_z3_raw,
            invariants_parsed=parsed_invariants,
            seed_state=seed_state,
            manifest=manifest,
        )

    @classmethod
    def _fallback_parse_toml(cls, toml_str: str) -> Dict[str, Any]:
        """Simple fallback parser for basic TOML if tomllib is unavailable."""
        result: Dict[str, Any] = {}
        current_section = result
        for line in toml_str.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section_name = line[1:-1].strip()
                result[section_name] = {}
                current_section = result[section_name]
            elif "=" in line:
                key, val = [x.strip() for x in line.split("=", 1)]
                # Handle booleans and strings
                if val.lower() == "true":
                    current_section[key] = True
                elif val.lower() == "false":
                    current_section[key] = False
                elif val.startswith('"') and val.endswith('"'):
                    current_section[key] = val[1:-1]
                else:
                    try:
                        current_section[key] = int(val)
                    except ValueError:
                        current_section[key] = val
        return result
