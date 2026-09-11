"""Database Shadow Branching Engine for Causalyn Milestone M4.

Provides ephemeral copy-on-write database branching for SQLite and PostgreSQL.
Intercepts schema migrations, executes candidate DDL in an isolated branch,
validates schema invariants, detects destructive statements (DROP TABLE,
TRUNCATE, unconstrained DELETE), and synthesizes rollback plans.
"""

from __future__ import annotations

import os
import re
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from ..api.contracts import GateDecision


class MigrationSafetyViolation(BaseModel):
    code: str
    message: str
    severity: str  # "critical", "high", "medium"
    penalty: float


class DBMigrationResult(BaseModel):
    branch_id: str
    decision: GateDecision
    paradox_index: float
    violations: List[MigrationSafetyViolation] = Field(default_factory=list)
    rollback_sql: Optional[str] = None
    applied_statements: int = 0
    duration_ms: float = 0.0


class DatabaseShadowBranchManager:
    """Manages ephemeral database branches and verifies schema migrations."""

    def __init__(self, base_db_path: Optional[str] = None) -> None:
        default_base = str(Path(__file__).resolve().parent.parent.parent / "runtime" / "causalyn.sqlite3")
        self.base_db_path = base_db_path or os.getenv("CAUSALYN_DB") or default_base
        if self.base_db_path != ":memory:":
            Path(self.base_db_path).resolve().parent.mkdir(parents=True, exist_ok=True)
        self.active_branches: Dict[str, str] = {}  # branch_id -> branch_file_path

    def analyze_sql_safety(self, sql_script: str) -> List[MigrationSafetyViolation]:
        """Scan SQL text for destructive DDL and unconstrained DML."""
        violations: List[MigrationSafetyViolation] = []
        clean_script = re.sub(r"--[^\n]*", "", sql_script)  # strip comments

        # 1. DROP TABLE / DROP SCHEMA / DROP DATABASE
        drop_pat = re.compile(r"\bDROP\s+(TABLE|SCHEMA|DATABASE)\b", re.IGNORECASE)
        if drop_pat.search(clean_script):
            violations.append(MigrationSafetyViolation(
                code="DB-001-DROP-RESOURCE",
                message="Destructive DROP TABLE/SCHEMA/DATABASE statement detected",
                severity="critical",
                penalty=1.0,
            ))

        # 2. TRUNCATE TABLE
        truncate_pat = re.compile(r"\bTRUNCATE\b", re.IGNORECASE)
        if truncate_pat.search(clean_script):
            violations.append(MigrationSafetyViolation(
                code="DB-002-TRUNCATE-DATA",
                message="Data loss hazard: TRUNCATE TABLE detected",
                severity="critical",
                penalty=1.0,
            ))

        # 3. DELETE without WHERE clause
        statements = [s.strip() for s in clean_script.split(";") if s.strip()]
        for stmt in statements:
            if re.search(r"^\s*DELETE\s+FROM\b", stmt, re.IGNORECASE):
                if not re.search(r"\bWHERE\b", stmt, re.IGNORECASE):
                    violations.append(MigrationSafetyViolation(
                        code="DB-003-UNCONSTRAINED-DELETE",
                        message=f"Catastrophic data deletion without WHERE clause: '{stmt[:60]}...'",
                        severity="critical",
                        penalty=1.0,
                    ))

            # 4. UPDATE without WHERE clause
            if re.search(r"^\s*UPDATE\s+\w+\s+SET\b", stmt, re.IGNORECASE):
                if not re.search(r"\bWHERE\b", stmt, re.IGNORECASE):
                    violations.append(MigrationSafetyViolation(
                        code="DB-004-UNCONSTRAINED-UPDATE",
                        message=f"Mass data overwrite without WHERE clause: '{stmt[:60]}...'",
                        severity="high",
                        penalty=0.8,
                    ))

        return violations

    def create_shadow_branch(self, branch_id: Optional[str] = None) -> Tuple[str, str]:
        """Create an isolated copy-on-write branch of the target database."""
        branch_id = branch_id or f"db-branch-{int(time.time()*1000)}"
        temp_dir = tempfile.mkdtemp(prefix="causalyn_db_")
        branch_file = os.path.join(temp_dir, f"{branch_id}.sqlite3")

        if os.path.exists(self.base_db_path):
            shutil.copy2(self.base_db_path, branch_file)
        else:
            # Initialize empty schema
            conn = sqlite3.connect(branch_file)
            conn.execute("CREATE TABLE IF NOT EXISTS _schema_version (version INTEGER PRIMARY KEY);")
            conn.commit()
            conn.close()

        self.active_branches[branch_id] = branch_file
        return branch_id, branch_file

    def execute_and_verify_migration(
        self, sql_script: str, branch_id: Optional[str] = None
    ) -> DBMigrationResult:
        """Execute migration candidate in shadow branch and verify invariants."""
        start_t = time.perf_counter()

        # Step 1: Static SQL Safety Analysis
        violations = self.analyze_sql_safety(sql_script)

        # Step 2: Provision Branch
        branch_id, branch_file = self.create_shadow_branch(branch_id)

        # If static analysis failed catastrophically, annihilate and reject
        if any(v.penalty >= 1.0 for v in violations):
            self.annihilate_branch(branch_id)
            duration_ms = (time.perf_counter() - start_t) * 1000
            return DBMigrationResult(
                branch_id=branch_id,
                decision=GateDecision.DENY,
                paradox_index=sum(v.penalty for v in violations),
                violations=violations,
                duration_ms=duration_ms,
            )

        applied_count = 0
        rollback_statements: List[str] = []

        try:
            conn = sqlite3.connect(branch_file)
            cursor = conn.cursor()

            statements = [s.strip() for s in sql_script.split(";") if s.strip()]
            for stmt in statements:
                # Synthesize naive rollback if CREATE TABLE
                create_match = re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)", stmt, re.IGNORECASE)
                if create_match:
                    tbl = create_match.group(1)
                    rollback_statements.append(f"DROP TABLE IF EXISTS {tbl};")

                cursor.execute(stmt)
                applied_count += 1

            conn.commit()

            # Step 3: Verify Post-Migration Invariants (PRAGMA integrity_check)
            cursor.execute("PRAGMA integrity_check;")
            integrity = cursor.fetchall()
            if integrity != [("ok",)]:
                violations.append(MigrationSafetyViolation(
                    code="DB-005-INTEGRITY-FAILED",
                    message=f"Database corruption detected: {integrity}",
                    severity="critical",
                    penalty=1.0,
                ))

            conn.close()

        except sqlite3.Error as e:
            violations.append(MigrationSafetyViolation(
                code="DB-006-SQL-SYNTAX-ERROR",
                message=f"SQL execution failure: {e}",
                severity="critical",
                penalty=1.0,
            ))

        duration_ms = (time.perf_counter() - start_t) * 1000
        kappa = sum(v.penalty for v in violations)

        if kappa == 0.0:
            decision = GateDecision.ALLOW
            rollback_sql = "\n".join(reversed(rollback_statements)) if rollback_statements else "-- No rollback needed"
        else:
            decision = GateDecision.DENY
            rollback_sql = None
            self.annihilate_branch(branch_id)

        return DBMigrationResult(
            branch_id=branch_id,
            decision=decision,
            paradox_index=kappa,
            violations=violations,
            rollback_sql=rollback_sql,
            applied_statements=applied_count,
            duration_ms=duration_ms,
        )

    def annihilate_branch(self, branch_id: str) -> None:
        """Purge shadow database branch completely."""
        if branch_id in self.active_branches:
            branch_file = self.active_branches.pop(branch_id)
            if os.path.exists(branch_file):
                os.unlink(branch_file)
            parent_dir = os.path.dirname(branch_file)
            if os.path.exists(parent_dir):
                shutil.rmtree(parent_dir, ignore_errors=True)
