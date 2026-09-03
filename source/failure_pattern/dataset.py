"""
Agentic Failure-Pattern Dataset - append-only records of failed gates, attacks, and disagreements.
"""

import json
import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path


class FailureType(Enum):
    """Types of failures that can be recorded."""
    GATE_DENIED = "gate_denied"          # Verification gate denied the action
    GATE_ESCALATED = "gate_escalated"    # Verification gate escalated to human
    AUTHORIZATION_FAILED = "authorization_failed"  # Authorization check failed
    EXECUTION_ERROR = "execution_error"  # Error during action execution
    TIMEOUT = "timeout"                  # Operation timed out
    INVARIANT_VIOLATION = "invariant_violation"  # Specific invariant violation
    SYSTEM_ERROR = "system_error"        # Internal system error
    DISAGREEMENT = "disagreement"        # Agent/model disagreement
    ATTACK_DETECTED = "attack_detected"  # Potential security attack detected


class FailureSeverity(Enum):
    """Severity levels for failures."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FailureRecord:
    """Record of a failure or disagreement."""
    failure_id: str
    timestamp: float
    failure_type: FailureType
    severity: FailureSeverity
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    related_intent: Optional[str] = None
    pipeline_id: Optional[str] = None
    stage: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'failure_id': self.failure_id,
            'timestamp': self.timestamp,
            'failure_type': self.failure_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'context': self.context,
            'stack_trace': self.stack_trace,
            'related_intent': self.related_intent,
            'pipeline_id': self.pipeline_id,
            'stage': self.stage,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FailureRecord':
        """Create failure record from dictionary."""
        return cls(
            failure_id=data['failure_id'],
            timestamp=data['timestamp'],
            failure_type=FailureType(data['failure_type']),
            severity=FailureSeverity(data['severity']),
            description=data['description'],
            context=data.get('context', {}),
            stack_trace=data.get('stack_trace'),
            related_intent=data.get('related_intent'),
            pipeline_id=data.get('pipeline_id'),
            stage=data.get('stage'),
            metadata=data.get('metadata', {})
        )


class FailurePatternDataset:
    """Append-only dataset for recording failure patterns."""

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the failure pattern dataset.

        Args:
            storage_path: Path to store failure records. If None, uses in-memory storage.
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self.failures: List[FailureRecord] = []

        # If storage path provided, load existing failures
        if self.storage_path and self.storage_path.exists():
            self._load_failures()

    def record_failure(self,
                      failure_type: FailureType,
                      description: str,
                      severity: FailureSeverity = FailureSeverity.MEDIUM,
                      context: Optional[Dict[str, Any]] = None,
                      stack_trace: Optional[str] = None,
                      related_intent: Optional[str] = None,
                      pipeline_id: Optional[str] = None,
                      stage: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> FailureRecord:
        """
        Record a failure or disagreement.

        Args:
            failure_type: Type of failure
            description: Human-readable description
            severity: Severity level
            context: Additional context information
            stack_trace: Stack trace if applicable
            related_intent: Related intent ID if applicable
            pipeline_id: Pipeline ID if applicable
            stage: Stage of pipeline where failure occurred
            metadata: Additional metadata

        Returns:
            FailureRecord: The recorded failure
        """
        failure_id = str(uuid.uuid4())
        timestamp = time.time()

        failure_record = FailureRecord(
            failure_id=failure_id,
            timestamp=timestamp,
            failure_type=failure_type,
            severity=severity,
            description=description,
            context=context or {},
            stack_trace=stack_trace,
            related_intent=related_intent,
            pipeline_id=pipeline_id,
            stage=stage,
            metadata=metadata or {}
        )

        self.failures.append(failure_record)

        # Persist to storage if configured
        if self.storage_path:
            self._save_failures()

        return failure_record

    def record_gate_denial(self,
                          description: str,
                          intent_id: Optional[str] = None,
                          pipeline_id: Optional[str] = None,
                          stage: Optional[str] = None,
                          invariant_violations: Optional[List[str]] = None) -> FailureRecord:
        """Record a verification gate denial."""
        context = {}
        if invariant_violations:
            context['invariant_violations'] = invariant_violations

        return self.record_failure(
            failure_type=FailureType.GATE_DENIED,
            description=description,
            severity=FailureSeverity.HIGH,
            context=context,
            related_intent=intent_id,
            pipeline_id=pipeline_id,
            stage=stage
        )

    def record_gate_escalation(self,
                              description: str,
                              intent_id: Optional[str] = None,
                              pipeline_id: Optional[str] = None,
                              stage: Optional[str] = None,
                              uncertainties: Optional[List[str]] = None) -> FailureRecord:
        """Record a verification gate escalation."""
        context = {}
        if uncertainties:
            context['uncertainties'] = uncertainties

        return self.record_failure(
            failure_type=FailureType.GATE_ESCALATED,
            description=description,
            severity=FailureSeverity.MEDIUM,
            context=context,
            related_intent=intent_id,
            pipeline_id=pipeline_id,
            stage=stage
        )

    def record_execution_error(self,
                              error: str,
                              stack_trace: Optional[str] = None,
                              intent_id: Optional[str] = None,
                              pipeline_id: Optional[str] = None,
                              stage: Optional[str] = None) -> FailureRecord:
        """Record an execution error."""
        return self.record_failure(
            failure_type=FailureType.EXECUTION_ERROR,
            description=error,
            severity=FailureSeverity.HIGH,
            stack_trace=stack_trace,
            related_intent=intent_id,
            pipeline_id=pipeline_id,
            stage=stage
        )

    def record_disagreement(self,
                           description: str,
                           agent1: str,
                           agent2: str,
                           topic: str,
                           pipeline_id: Optional[str] = None,
                           stage: Optional[str] = None) -> FailureRecord:
        """Record a disagreement between agents or models."""
        context = {
            'agent1': agent1,
            'agent2': agent2,
            'topic': topic
        }

        return self.record_failure(
            failure_type=FailureType.DISAGREEMENT,
            description=description,
            severity=FailureSeverity.MEDIUM,
            context=context,
            pipeline_id=pipeline_id,
            stage=stage
        )

    def get_failures(self,
                    failure_type: Optional[FailureType] = None,
                    severity: Optional[FailureSeverity] = None,
                    limit: Optional[int] = None,
                    since: Optional[float] = None) -> List[FailureRecord]:
        """
        Get failure records with optional filtering.

        Args:
            failure_type: Filter by failure type
            severity: Filter by severity
            limit: Maximum number of records to return
            since: Return failures after this timestamp

        Returns:
            List of failure records matching the criteria
        """
        filtered = self.failures

        if failure_type:
            filtered = [f for f in filtered if f.failure_type == failure_type]

        if severity:
            filtered = [f for f in filtered if f.severity == severity]

        if since:
            filtered = [f for f in filtered if f.timestamp >= since]

        # Sort by timestamp descending (newest first)
        filtered = sorted(filtered, key=lambda x: x.timestamp, reverse=True)

        if limit:
            filtered = filtered[:limit]

        return filtered

    def get_failure_stats(self) -> Dict[str, Any]:
        """Get statistics about recorded failures."""
        if not self.failures:
            return {
                'total_failures': 0,
                'by_type': {},
                'by_severity': {},
                'recent_count': 0
            }

        by_type = {}
        by_severity = {}

        for failure in self.failures:
            # Count by type
            ftype = failure.failure_type.value
            by_type[ftype] = by_type.get(ftype, 0) + 1

            # Count by severity
            severity = failure.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1

        # Count recent failures (last 24 hours)
        recent_threshold = time.time() - (24 * 60 * 60)
        recent_count = len([f for f in self.failures if f.timestamp >= recent_threshold])

        return {
            'total_failures': len(self.failures),
            'by_type': by_type,
            'by_severity': by_severity,
            'recent_count': recent_count
        }

    def clear_failures(self):
        """Clear all failure records (use with caution)."""
        self.failures = []
        if self.storage_path:
            self._save_failures()

    def _save_failures(self):
        """Save failures to storage."""
        if not self.storage_path:
            return

        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert failures to dictionaries
        data = [failure.to_dict() for failure in self.failures]

        # Write to file
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_failures(self):
        """Load failures from storage."""
        if not self.storage_path or not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)

            self.failures = [FailureRecord.from_dict(item) for item in data]
        except Exception as e:
            # If loading fails, start with empty list
            print(f"Warning: Could not load failure dataset: {e}")
            self.failures = []


# Example usage and testing
if __name__ == "__main__":
    # Create failure dataset (in-memory for demo)
    dataset = FailurePatternDataset()

    # Record some failures
    dataset.record_gate_denial(
        description="Attempt to delete protected configuration file",
        intent_id="intent-001",
        pipeline_id="pipeline-001",
        stage="verification",
        invariant_violations=["protected_files_immutable"]
    )

    dataset.record_execution_error(
        error="File not found: /nonexistent/file.txt",
        stack_trace="FileNotFoundError: [Errno 2] No such file or directory: '/nonexistent/file.txt'",
        intent_id="intent-002",
        pipeline_id="pipeline-002",
        stage="shadow_execution"
    )

    dataset.record_disagreement(
        description="Disagreement on whether action requires authorization",
        agent1="Validator",
        agent2="Orchestrator",
        topic="Authorization requirement for config update",
        pipeline_id="pipeline-003",
        stage="commit_attempt"
    )

    # Print statistics
    stats = dataset.get_failure_stats()
    print("Failure Statistics:")
    print(json.dumps(stats, indent=2))

    # Print recent failures
    recent = dataset.get_failures(limit=5)
    print(f"\nRecent Failures ({len(recent)}):")
    for failure in recent:
        print(f"  [{failure.failure_type.value}] {failure.description}")