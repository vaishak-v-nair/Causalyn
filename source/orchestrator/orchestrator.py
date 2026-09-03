"""
AI Orchestration - routing, sequencing, specialist handoff, disagreement handling.
"""

from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
import time
from ..harness.context import HarnessContext
from ..translator.intent_translator import IntentTranslator, IntentSpecification
from ..shadow.executor import ShadowExecutor
from ..verification.invariant_checker import VerificationEngine, Decision
from ..commit.boundary import CommitBoundary, CommitStatus
from ..model.world_state import WorldState, WorldStateManager
from ..failure_pattern.dataset import FailurePatternDataset, FailureType, FailureSeverity


class OrchestrationStage(Enum):
    """Stages in the orchestration pipeline."""
    INTENT_RECEIVED = "intent_received"
    INTENT_TRANSLATED = "intent_translated"
    SHADOW_EXECUTION = "shadow_execution"
    VERIFICATION = "verification"
    COMMIT_ATTEMPT = "commit_attempt"
    COMMITTED = "committed"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass
class OrchestrationContext:
    """Context carried through the orchestration pipeline."""
    pipeline_id: str
    timestamp: float = field(default_factory=time.time)
    harness_context: Optional[HarnessContext] = None
    intent_spec: Optional[IntentSpecification] = None
    shadow_state: Optional[WorldState] = None
    verification_decision: Optional[Decision] = None
    commit_record: Optional[Any] = None
    current_stage: OrchestrationStage = OrchestrationStage.INTENT_RECEIVED
    stages_completed: List[OrchestrationStage] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIOrchestrator:
    """Orchestrates the flow from intent to committed state."""

    def __init__(self):
        # These will be set via set_dependencies
        self.harness_context: Optional[HarnessContext] = None
        self.intent_translator: Optional[IntentTranslator] = None
        self.world_state_manager: Optional[WorldStateManager] = None
        self.shadow_executor: Optional[ShadowExecutor] = None
        self.verification_engine: Optional[VerificationEngine] = None
        self.commit_boundary: Optional[CommitBoundary] = None
        self.failure_dataset: Optional[FailurePatternDataset] = None

        self.pipeline_history: List[OrchestrationContext] = []
        self.active_pipelines: Dict[str, OrchestrationContext] = {}

    def set_dependencies(self,
                       world_state_manager: WorldStateManager,
                       shadow_executor: ShadowExecutor,
                       verification_engine: VerificationEngine,
                       commit_boundary: CommitBoundary,
                       failure_dataset: FailurePatternDataset):
        """Set the component dependencies."""
        self.world_state_manager = world_state_manager
        self.shadow_executor = shadow_executor
        self.verification_engine = verification_engine
        self.commit_boundary = commit_boundary
        self.failure_dataset = failure_dataset
        # Create harness context with the world state manager
        self.harness_context = HarnessContext(world_state_manager, shadow_executor)
        self.intent_translator = IntentTranslator()

    def process_intent(self, natural_language_intent: str) -> OrchestrationContext:
        """
        Process a natural language intent through the full orchestration pipeline.

        Args:
            natural_language_intent: Human intent in natural language

        Returns:
            OrchestrationContext: Context of the completed pipeline
        """
        pipeline_id = f"pipeline-{int(time.time() * 1000)}"
        context = OrchestrationContext(
            pipeline_id=pipeline_id,
            harness_context=self.harness_context
        )

        self.active_pipelines[pipeline_id] = context

        try:
            # Stage 1: Intent Received
            context.current_stage = OrchestrationStage.INTENT_RECEIVED
            context.stages_completed.append(OrchestrationStage.INTENT_RECEIVED)
            self._record_stage_completion(context)

            # Stage 2: Intent Translation
            if not self.intent_translator:
                raise RuntimeError("Intent translator not configured")
            context.intent_spec = self.intent_translator.translate(natural_language_intent)
            context.harness_context.set_intent(context.intent_spec)
            context.current_stage = OrchestrationStage.INTENT_TRANSLATED
            context.stages_completed.append(OrchestrationStage.INTENT_TRANSLATED)
            self._record_stage_completion(context)

            # Stage 3: Shadow Execution Preparation
            if not self.world_state_manager:
                raise RuntimeError("World state manager not configured")

            # Enter shadow mode
            shadow_state = self.world_state_manager.create_snapshot(f"shadow_{pipeline_id}")
            context.shadow_state = shadow_state

            if not self.shadow_executor:
                raise RuntimeError("Shadow executor not configured")
            self.shadow_executor.enter_shadow_mode()

            context.current_stage = OrchestrationStage.SHADOW_EXECUTION
            context.stages_completed.append(OrchestrationStage.SHADOW_EXECUTION)
            self._record_stage_completion(context)

            # Execute intent-based actions through harness
            self._execute_intent_actions(context)

            # Stage 4: Verification
            if not self.verification_engine:
                raise RuntimeError("Verification engine not configured")

            before_state = self.world_state_manager.get_current_state()
            if not self.shadow_executor:
                raise RuntimeError("Shadow executor not configured")
            context.shadow_state = self.shadow_executor.get_shadow_state()
            after_state = context.shadow_state

            verification_decision = self.verification_engine.verify_transition(before_state, after_state)
            context.verification_decision = verification_decision
            context.current_stage = OrchestrationStage.VERIFICATION
            context.stages_completed.append(OrchestrationStage.VERIFICATION)
            self._record_stage_completion(context)

            # Stage 5: Commit Attempt
            if not self.commit_boundary:
                raise RuntimeError("Commit boundary not configured")

            # Prepare changes (compute from shadow state vs current state)
            changes = self._compute_changes(context.shadow_state, before_state)

            commit_record = self.commit_boundary.prepare_commit(
                intent_id=context.intent_spec.intent_id if context.intent_spec else None,
                changes=changes,
                verification_engine=self.verification_engine,
                before_state=before_state,
                after_state=context.shadow_state,
                intent_text=natural_language_intent
            )
            context.commit_record = commit_record
            context.current_stage = OrchestrationStage.COMMIT_ATTEMPT
            context.stages_completed.append(OrchestrationStage.COMMIT_ATTEMPT)
            self._record_stage_completion(context)

            # Actually commit if appropriate
            if commit_record.decision == CommitStatus.COMMITTED:
                success = self.commit_boundary.commit(commit_record)
                if success:
                    # Exit shadow mode with commit
                    if self.shadow_executor:
                        self.shadow_executor.exit_shadow_mode(commit=True)
                    context.current_stage = OrchestrationStage.COMMITTED
                else:
                    context.current_stage = OrchestrationStage.FAILED
                    context.error = "Commit failed"
            else:
                # Exit shadow mode without committing
                if self.shadow_executor:
                    self.shadow_executor.exit_shadow_mode(commit=False)

                if commit_record.decision == CommitStatus.DENIED:
                    context.current_stage = OrchestrationStage.FAILED
                    context.error = f"Commit denied: {commit_record.escalation_reason}"
                elif commit_record.decision == CommitStatus.ESCALATED:
                    context.current_stage = OrchestrationStage.ESCALATED
                    context.error = f"Commit escalated: {commit_record.escalation_reason}"
                else:
                    context.current_stage = OrchestrationStage.FAILED
                    context.error = f"Unknown commit decision: {commit_record.decision}"

            context.stages_completed.append(context.current_stage)
            self._record_stage_completion(context)

        except Exception as e:
            context.error = str(e)
            context.current_stage = OrchestrationStage.FAILED
            # Ensure we exit shadow mode if we entered it
            try:
                if self.shadow_executor and self.shadow_executor.is_in_shadow_mode():
                    self.shadow_executor.exit_shadow_mode(commit=False)
            except:
                pass  # Best effort to clean up
            self._record_stage_completion(context)

        finally:
            # Move to history and remove from active
            self.pipeline_history.append(context)
            if len(self.pipeline_history) > 100:
                del self.pipeline_history[:-100]
            if context.pipeline_id in self.active_pipelines:
                del self.active_pipelines[context.pipeline_id]

            # Record failure pattern if applicable
            if self.failure_dataset and context.error:
                self.failure_dataset.record_failure(
                    failure_type=FailureType.EXECUTION_ERROR,
                    description=context.error or "Unknown error",
                    severity=FailureSeverity.HIGH,
                    related_intent=natural_language_intent[:100],
                    pipeline_id=context.pipeline_id,
                    stage=context.current_stage.value
                )

        return context

    def _execute_intent_actions(self, context: OrchestrationContext):
        """Execute actions based on the translated intent via the harness context."""
        if not context.intent_spec or not context.harness_context:
            return

        # For now, we simulate some basic actions.
        # In a real implementation, we would parse the intent spec and execute
        # the corresponding actions through the harness context tools.
        # We'll just log that we would execute actions.
        intent_goal = context.intent_spec.goal.lower()

        # Simulate some common actions based on intent keywords
        if "migrate" in intent_goal or "update" in intent_goal:
            # Simulate a configuration change via harness tool
            # For now, we'll just update the world state data through harness
            context.harness_context.update_state("migration_status", "in_progress")
            # Also modify a file via a tool if we had one
            pass
        elif "build" in intent_goal or "create" in intent_goal:
            # Simulate creating a new file or component
            context.harness_context.update_state("build_status", "started")
            pass
        elif "fix" in intent_goal or "resolve" in intent_goal:
            # Simulate fixing an issue
            context.harness_context.update_state("fix_status", "applied")
            pass

    def _compute_changes(self, shadow_state: WorldState, before_state: WorldState) -> Dict[str, Any]:
        """Compute changes between shadow state and before state."""
        changes = {}

        # Compare data
        for key in shadow_state.data:
            if key not in before_state.data or shadow_state.data[key] != before_state.data.get(key):
                changes[f"data:{key}"] = shadow_state.data[key]
        # Check for deleted data keys
        for key in before_state.data:
            if key not in shadow_state.data:
                changes[f"data:{key}"] = None  # Mark for deletion

        # Compare file system
        for path in shadow_state.file_system:
            if path not in before_state.file_system or \
               shadow_state.file_system[path] != before_state.file_system.get(path):
                changes[f"file:{path}"] = shadow_state.file_system[path]
        # Check for deleted files
        for path in before_state.file_system:
            if path not in shadow_state.file_system:
                changes[f"file:{path}"] = None  # Mark for deletion

        return changes

    def _record_stage_completion(self, context: OrchestrationContext):
        """Record completion of a stage for debugging/monitoring."""
        # In a real implementation, this might log to a monitoring system
        pass

    def get_pipeline_status(self, pipeline_id: str) -> Optional[OrchestrationContext]:
        """Get the status of a pipeline by ID."""
        # Check active pipelines first
        if pipeline_id in self.active_pipelines:
            return self.active_pipelines[pipeline_id]

        # Check history
        for context in self.pipeline_history:
            if context.pipeline_id == pipeline_id:
                return context

        return None

    def get_recent_pipelines(self, limit: int = 10) -> List[OrchestrationContext]:
        """Get the most recent pipelines."""
        return sorted(self.pipeline_history,
                     key=lambda x: x.timestamp,
                     reverse=True)[:limit]


# Example usage and testing
if __name__ == "__main__":
    print("AIOrchestrator class defined - ready for integration with other components")
    # This would normally be tested with all components wired together