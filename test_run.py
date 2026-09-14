#!/usr/bin/env python
"""Test script to run the AI tool pipeline."""

import time
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'source'))

from harness.context import HarnessContext
from translator.intent_translator import IntentTranslator
from model.world_state import WorldStateManager
from shadow.executor import ShadowExecutor
from verification.invariant_checker import create_default_verification_engine
from commit.boundary import CommitBoundary
from orchestrator.orchestrator import AIOrchestrator
from failure_pattern.dataset import FailurePatternDataset

def test_pipeline():
    print("Testing AI Tool Pipeline...")
    # Initialize
    world_state_manager = WorldStateManager()
    shadow_executor = ShadowExecutor(world_state_manager)
    harness_context = HarnessContext(world_state_manager, shadow_executor)
    shadow_executor.harness_context = harness_context
    intent_translator = IntentTranslator()
    verification_engine = create_default_verification_engine()
    failure_dataset = FailurePatternDataset()
    commit_boundary = CommitBoundary(failure_dataset=failure_dataset)
    orchestrator = AIOrchestrator()
    orchestrator.set_dependencies(
        world_state_manager=world_state_manager,
        shadow_executor=shadow_executor,
        verification_engine=verification_engine,
        commit_boundary=commit_boundary,
        failure_dataset=failure_dataset
    )

    # Set up initial state
    world_state_manager.current_state.set_file_content("/protected/config.json", {"debug": True, "secret": "hidden"})
    world_state_manager.current_state.set_file_content("/app/public/settings.json", {"feature": False})
    world_state_manager.current_state.set_data("version", "1.0")

    # Test intent
    intent = "Update the public settings to enable the new feature"
    print(f"Processing intent: {intent}")
    start = time.time()
    context = orchestrator.process_intent(intent)
    elapsed = time.time() - start
    print(f"Pipeline ID: {context.pipeline_id}")
    print(f"Final Stage: {context.current_stage.value}")
    print(f"Intent ID: {context.intent_spec.intent_id if context.intent_spec else 'None'}")
    print(f"Goal: {context.intent_spec.goal if context.intent_spec else 'None'}")
    if context.verification_decision:
        print(f"Verification Decision: {context.verification_decision.value}")
    if context.commit_record:
        print(f"Commit Decision: {context.commit_record.decision.value}")
        if context.commit_record.escalation_reason:
            print(f"Escalation/Denial Reason: {context.commit_record.escalation_reason}")
    if context.error:
        print(f"Error: {context.error}")
    print(f"Execution Time: {elapsed*1000:.2f} ms")
    # Show resulting state
    print(f"Files after: {len(world_state_manager.current_state.file_system)}")
    if world_state_manager.current_state.file_exists('/app/public/settings.json'):
        content = world_state_manager.current_state.get_file_content('/app/public/settings.json')
        print(f"/app/public/settings.json: {content}")
    print("Test completed successfully.")

if __name__ == "__main__":
    test_pipeline()