"""Causalyn Acausal Workspace Template Engine.

Manages the .causalyn/ directory lifecycle, defining:
- invariants.z3: Absolute mathematical rules and SMT-LIB constraints.
- seed_state.json: Baseline architectural ground truth.
- manifest.toml: Target files, permissions, and security boundaries.
"""

from __future__ import annotations

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
