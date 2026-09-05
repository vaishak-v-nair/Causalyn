import pytest
from causalyn.orchestrator.state_bus import HyperDimensionalStateBus

def test_destructive_interference_blocked():
    bus = HyperDimensionalStateBus()
    
    # Reset singleton state for tests
    bus.active_intents = {}
    
    # Agent 1 targets the database
    allowed1, kappa1, msg1 = bus.register_intent("Agent_1", "/app/db.py", "hash1")
    assert allowed1 is True
    assert kappa1 == 0.0
    
    # Agent 2 targets a different file
    allowed2, kappa2, msg2 = bus.register_intent("Agent_2", "/app/ui.js", "hash2")
    assert allowed2 is True
    assert kappa2 == 0.0
    
    # Agent 3 tries to target the database while Agent 1 is mutating it (Destructive Interference)
    allowed3, kappa3, msg3 = bus.register_intent("Agent_3", "/app/db.py", "hash3")
    assert allowed3 is False
    assert kappa3 > 0.0
    assert "Destructive Interference" in msg3

def test_release_intent():
    bus = HyperDimensionalStateBus()
    bus.active_intents = {}
    
    bus.register_intent("Agent_1", "/app/db.py", "hash1")
    bus.release_intent("Agent_1")
    
    # Agent 3 should now be allowed
    allowed, kappa, msg = bus.register_intent("Agent_3", "/app/db.py", "hash3")
    assert allowed is True
    assert kappa == 0.0
