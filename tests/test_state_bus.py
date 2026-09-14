import pytest
from causalyn.orchestrator.state_bus import HyperDimensionalStateBus

def test_destructive_interference_blocked():
    bus = HyperDimensionalStateBus()
    
    # Reset singleton state for tests
    bus.active_intents = {}
    
    # Agent 1 targets the database with state
    allowed1, kappa1, msg1 = bus.register_intent("Agent_1", {"db_connections": 5})
    assert allowed1 is True
    assert kappa1 == 0.0
    
    # Agent 2 targets UI state with safe variables
    allowed2, kappa2, msg2 = bus.register_intent("Agent_2", {"ui_workers": 2})
    assert allowed2 is True
    assert kappa2 == 0.0
    
    # Agent 3 tries to set contradictory database connection value (Destructive Interference)
    allowed3, kappa3, msg3 = bus.register_intent("Agent_3", {"db_connections": 15})
    assert allowed3 is False
    assert kappa3 > 0.0
    assert "Destructive Interference" in msg3

def test_release_intent():
    bus = HyperDimensionalStateBus()
    bus.active_intents = {}
    
    bus.register_intent("Agent_1", {"db_connections": 5})
    bus.release_intent("Agent_1")
    
    # Agent 3 should now be allowed since Agent 1 released intent
    allowed, kappa, msg = bus.register_intent("Agent_3", {"db_connections": 5})
    assert allowed is True
    assert kappa == 0.0
