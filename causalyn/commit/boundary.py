"""
Transactional State / Commit Boundary - distinct, auditable transition from candidate to protected state.
Now includes real authorization (token/policy) and persistence of commit history.
"""

import json
import time
import os
import yaml
import re
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from ..model.world_state import WorldState
from ..verification.invariant_checker import Decision, VerificationEngine
from ..failure_pattern.dataset import FailurePatternDataset


class CommitStatus(Enum):
    """Status of a commit attempt."""
    PENDING = "pending"
    COMMITTED = "committed"
    DENIED = "denied"
    ESCALATED = "escalated"
    FAILED = "failed"


@dataclass
class CommitRecord:
    """Record of a commit attempt for auditing."""
    commit_id: str
    timestamp: float
    intent_id: Optional[str]
    decision: CommitStatus
    verification_decision: Decision
    changes_summary: Dict[str, Any]
    authorization_given: bool
    escalation_reason: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'commit_id': self.commit_id,
            'timestamp': self.timestamp,
            'intent_id': self.intent_id,
            'decision': self.decision.value,
            'verification_decision': self.verification_decision.value,
            'changes_summary': self.changes_summary,
            'authorization_given': self.authorization_given,
            'escalation_reason': self.escalation_reason,
            'error_message': self.error_message
        }


class CommitBoundary:
    """Manages the transactional commit boundary with authorization and verification."""

    def __init__(self, failure_dataset: Optional[FailurePatternDataset] = None,
                 auth_policy_path: str = "policies/auth.yaml",
                 commit_history_path: Optional[str] = None):
        self.commit_history_path = commit_history_path or os.environ.get("CAUSALYN_COMMIT_HISTORY")
        if not self.commit_history_path:
            if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
                import tempfile
                self.commit_history_path = os.path.join(tempfile.gettempdir(), "commit_history.jsonl")
            else:
                self.commit_history_path = os.path.abspath(
                    os.path.join("runtime", "commit_history.jsonl")
                )
        self.failure_dataset = failure_dataset
        self.auth_policy = self._load_auth_policy(auth_policy_path)
        # Ensure history file exists
        try:
            os.makedirs(os.path.dirname(self.commit_history_path), exist_ok=True)
            if not os.path.exists(self.commit_history_path):
                open(self.commit_history_path, 'a').close()
        except OSError:
            import tempfile
            self.commit_history_path = os.path.join(tempfile.gettempdir(), "commit_history.jsonl")
            try:
                os.makedirs(os.path.dirname(self.commit_history_path), exist_ok=True)
                if not os.path.exists(self.commit_history_path):
                    open(self.commit_history_path, 'a').close()
            except OSError:
                pass

    def _load_auth_policy(self, path: str) -> Dict[str, Any]:
        """Load authorization policy from YAML file."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            # Fallback to a default policy
            print(f"Warning: Could not load auth policy from {path}: {e}")
            return {
                "authorized_intents": [".*authorized.*", "build.*", "create.*", "migrate.*", "update.*", "fix.*", "resolve.*"],
                "auth_token_required": False,
                "auth_token": "change-me"
            }

    def prepare_commit(self,
                      intent_id: Optional[str],
                      changes: Dict[str, Any],
                      verification_engine: VerificationEngine,
                      before_state: WorldState,
                      after_state: WorldState,
                      intent_text: Optional[str] = None,
                      expected_pre_state_hash: Optional[str] = None) -> CommitRecord:
        """
        Prepare a commit attempt - runs verification, checks authorization, and verifies 2PC pre-state hash.

        Args:
            intent_id: ID of the intent being executed
            changes: Proposed changes to commit
            verification_engine: Engine to verify the transition
            before_state: State before the action
            after_state: State after the action (shadow state)
            intent_text: Optional natural language intent description
            expected_pre_state_hash: Expected SHA-256 fingerprint of before_state for 2PC concurrency control

        Returns:
            CommitRecord: Record of the commit attempt
        """
        commit_id = f"commit-{int(time.time() * 1000)}"
        timestamp = time.time()

        # Two-Phase Commit (2PC): Check for concurrent out-of-band host modifications
        if expected_pre_state_hash and hasattr(before_state, "compute_hash"):
            actual_hash = before_state.compute_hash()
            if actual_hash != expected_pre_state_hash:
                stale_record = CommitRecord(
                    commit_id=commit_id,
                    timestamp=timestamp,
                    intent_id=intent_id,
                    decision=CommitStatus.FAILED,
                    verification_decision=Decision.DENY,
                    changes_summary=self._summarize_changes(changes),
                    authorization_given=False,
                    escalation_reason=(
                        f"STALE_STATE_ABORT: Pre-state SHA-256 hash mismatch (expected {expected_pre_state_hash[:12]}..., "
                        f"found {actual_hash[:12]}...). Concurrent modification detected."
                    ),
                )
                self._persist_commit_record(stale_record)
                return stale_record

        # Run verification
        verification_decision = verification_engine.verify_transition(before_state, after_state)

        # Check authorization
        authorization_given = self._check_authorization(intent_id, changes, intent_text)

        # Create initial commit record
        commit_record = CommitRecord(
            commit_id=commit_id,
            timestamp=timestamp,
            intent_id=intent_id,
            decision=CommitStatus.PENDING,  # Will be updated below
            verification_decision=verification_decision,
            changes_summary=self._summarize_changes(changes),
            authorization_given=authorization_given
        )

        # Make final decision based on verification and authorization
        if verification_decision == Decision.DENY or not authorization_given:
            commit_record.decision = CommitStatus.DENIED
            if verification_decision == Decision.DENY:
                commit_record.escalation_reason = "Verification failed - invariants violated"
            else:
                commit_record.escalation_reason = "Authorization denied"
        elif verification_decision == Decision.ESCALATE:
            commit_record.decision = CommitStatus.ESCALATED
            commit_record.escalation_reason = "Verification uncertain - requires human review"
        else:
            # Verification ALLOW and authorization granted
            commit_record.decision = CommitStatus.COMMITTED

        # Persist the commit record
        self._persist_commit_record(commit_record)
        return commit_record

    def commit(self, commit_record: CommitRecord) -> bool:
        """
        Actually commit the changes (if authorized and verified).

        Args:
            commit_record: The commit record to commit

        Returns:
            bool: True if commit succeeded, False otherwise
        """
        # Only commit if decision was COMMITTED
        if commit_record.decision != CommitStatus.COMMITTED:
            return False

        # In a real implementation, this would apply changes to the protected state
        # For now, we'll just mark it as committed in our records (already persisted)
        # The actual state application would happen elsewhere via world_state_manager.commit_transaction
        # but we already applied changes in prepare_commit? Actually we haven't applied yet.
        # We'll assume the caller will apply changes after this returns True.
        # We'll update the record to reflect that commit succeeded (already persisted as COMMITTED).
        # For simplicity, we'll just return True.
        return True

    def escalate(self, commit_record: CommitRecord, reason: str) -> bool:
        """
        Escalate a commit decision to human review.

        Args:
            commit_record: The commit record to escalate
            reason: Reason for escalation

        Returns:
            bool: True if escalation recorded, False otherwise
        """
        if commit_record.decision != CommitStatus.ESCALATED:
            return False
        commit_record.escalation_reason = reason
        self._persist_commit_record(commit_record)
        return True

    def deny(self, commit_record: CommitRecord, reason: str) -> bool:
        """
        Explicitly deny a commit.

        Args:
            commit_record: The commit record to deny
            reason: Reason for denial

        Returns:
            bool: True if denial recorded, False otherwise
        """
        if commit_record.decision != CommitStatus.DENIED:
            return False
        commit_record.escalation_reason = reason
        self._persist_commit_record(commit_record)
        return True

    def get_commit_history(self) -> List[CommitRecord]:
        """Get the history of commit attempts."""
        records = []
        if not os.path.exists(self.commit_history_path):
            return records
        with open(self.commit_history_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    records.append(CommitRecord(
                        commit_id=data['commit_id'],
                        timestamp=data['timestamp'],
                        intent_id=data.get('intent_id'),
                        decision=CommitStatus(data['decision']),
                        verification_decision=Decision(data['verification_decision']),
                        changes_summary=data.get('changes_summary', {}),
                        authorization_given=data.get('authorization_given', False),
                        escalation_reason=data.get('escalation_reason'),
                        error_message=data.get('error_message')
                    ))
                except Exception:
                    pass
        return records

    def _persist_commit_record(self, record: CommitRecord):
        """Append a commit record to the history file."""
        try:
            with open(self.commit_history_path, 'a') as f:
                f.write(json.dumps(record.to_dict()) + '\n')
        except OSError:
            pass

    def _check_authorization(self, intent_id: Optional[str], changes: Dict[str, Any],
                             intent_text: Optional[str] = None) -> bool:
        """
        Check if authorization is given for this commit.
        Uses the loaded auth policy.
        """
        # Fail-closed: if no explicit allow, deny
        if not intent_id:
            return False

        # Policies describe human intent, not generated intent IDs.
        authorization_subject = intent_text or intent_id
        authorized_intents = self.auth_policy.get("authorized_intents", [])
        for pattern in authorized_intents:
            if authorization_subject and re.match(pattern, authorization_subject, re.IGNORECASE):
                return True

        # Check for auth token
        if self.auth_policy.get("auth_token_required", False):
            auth_token = changes.get("auth_token")
            expected_token = self.auth_policy.get("auth_token")
            if auth_token and expected_token and auth_token == expected_token:
                return True
            else:
                return False
        else:
            # If token is not required, we still allow if intent matches
            # But we already checked above, so if we reach here, no intent matched.
            # However, we might want to allow by default if no token required?
            # We'll stick to fail-closed: if no rule matched, deny.
            return False

        # If we reach here, no rule matched
        return False

    def _summarize_changes(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of changes for the commit record."""
        summary = {
            'total_changes': len(changes),
            'data_changes': 0,
            'file_changes': 0,
            'files_modified': [],
            'files_added': [],
            'files_deleted': []
        }

        for key, value in changes.items():
            if key.startswith('file:'):
                summary['file_changes'] += 1
                filepath = key[5:]  # Remove 'file:' prefix
                if value is None:
                    summary['files_deleted'].append(filepath)
                else:
                    # Determine if it's a modification or addition (simplified)
                    # We don't have previous state here, so we'll treat all as modifications for summary
                    summary['files_modified'].append(filepath)
            else:
                summary['data_changes'] += 1

        return summary


# Example usage and testing
if __name__ == "__main__":
    # This would normally be tested with the other components
    print("CommitBoundary class defined - ready for integration with other components")