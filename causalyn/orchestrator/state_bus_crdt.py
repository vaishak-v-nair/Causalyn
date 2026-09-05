"""
Hyper-Dimensional State Bus (CRDT Sync)

Uses pycrdt (Y.js port) to create a Conflict-Free Replicated Data Type (CRDT) for the system state.
Agents propose state deltas. The bus simulates the merge, passes the resulting topology to the 
Z3 Mathematical Kernel (the kappa-Engine), and mathematically rejects the merge if a geometric 
paradox (kappa > 0) is detected.
"""

import z3
import json
from typing import Dict, Any, Tuple
import pycrdt as crdt

class KappaEngine:
    def __init__(self):
        # Strict architectural intent vector for the global state
        self.global_constraints = {
            "urllib3": (100, 199),  # Example: >= v1.0.0, < v2.0.0 represented as ints
            "fastapi": (95, 200),
            "max_connections": (1, 100)
        }
        
    def evaluate_state(self, state_dict: Dict[str, Any]) -> Tuple[float, str]:
        """
        Evaluates the absolute geometric constraint of the provided state.
        Returns (kappa_index, violation_description). kappa == 0 means valid.
        """
        solver = z3.Solver()
        z3_vars = {k: z3.Int(k) for k in self.global_constraints.keys()}
        
        for k, (min_val, max_val) in self.global_constraints.items():
            solver.add(z3_vars[k] >= min_val, z3_vars[k] <= max_val)
            
        for k, v in state_dict.items():
            if k in z3_vars and isinstance(v, (int, float)):
                solver.add(z3_vars[k] == int(v))
                
        if solver.check() == z3.unsat:
            return 100.0, "Paradox Detected: The merged state violated architectural invariants."
        return 0.0, "Valid geometric state."

class CRDTStateBus:
    def __init__(self):
        # Master State Document
        self.master_doc = crdt.Doc()
        # The primary shared memory map
        self.global_state = crdt.Map()
        self.master_doc["global_state"] = self.global_state
        
        # Initialize default valid state directly via dictionary merge
        with self.master_doc.transaction():
            self.global_state.update({
                "urllib3": 190,
                "fastapi": 95,
                "max_connections": 10
            })
            
        self.kappa_engine = KappaEngine()

    def get_current_state(self) -> Dict[str, Any]:
        """Returns the current synchronized JSON representation of the CRDT map."""
        return self.global_state.to_py()

    def propose_delta(self, agent_id: str, delta_updates: Dict[str, Any]) -> Tuple[bool, float, str]:
        """
        An agent proposes a state update.
        We simulate the CRDT merge using a shadow document.
        If kappa == 0, we apply to master. Else, we mathematically reject.
        """
        # 1. Clone the master document to create a Shadow/Speculative space
        shadow_doc = crdt.Doc()
        shadow_state = crdt.Map()
        shadow_doc["global_state"] = shadow_state
        
        # Apply the current master state to the shadow doc
        update = self.master_doc.get_update()
        shadow_doc.apply_update(update)

        # 2. Speculatively apply the agent's delta to the shadow doc
        with shadow_doc.transaction():
            shadow_state.update(delta_updates)

        # 3. Extract the proposed resulting JSON topology
        proposed_topology = shadow_state.to_py()

        # 4. Route through the kappa-Engine
        kappa, message = self.kappa_engine.evaluate_state(proposed_topology)

        if kappa == 0.0:
            # 5. Admissible! Apply the delta strictly to the master document
            with self.master_doc.transaction():
                self.global_state.update(delta_updates)
            return True, kappa, f"Delta from {agent_id} merged. State remains geometrically valid."
        else:
            # 6. Destructive Interference. Reject the delta.
            return False, kappa, f"Delta from {agent_id} mathematically rejected: {message}"


def test_crdt_state_bus():
    print("=" * 72)
    print("  HYPER-DIMENSIONAL STATE BUS (CRDT SYNC)")
    print("=" * 72)
    
    bus = CRDTStateBus()
    print(f"[INIT] Master State: {bus.get_current_state()}")
    
    # Valid Delta from Agent 1
    agent1_delta = {"fastapi": 105}
    print(f"\n[AGENT 1] Proposes delta: {agent1_delta}")
    success1, k1, msg1 = bus.propose_delta("Agent-1", agent1_delta)
    print(f"[BUS] Merged: {success1} (kappa={k1}) | {msg1}")
    print(f"[CURRENT STATE] {bus.get_current_state()}")

    # Invalid Delta from Agent 2
    agent2_delta = {"urllib3": 500} # Violates max constraint 199
    print(f"\n[AGENT 2] Proposes conflicting delta: {agent2_delta}")
    success2, k2, msg2 = bus.propose_delta("Agent-2", agent2_delta)
    print(f"[BUS] Merged: {success2} (kappa={k2}) | {msg2}")
    print(f"[CURRENT STATE] {bus.get_current_state()} (Untouched)")

    # Concurrent complex merge attempt
    agent3_delta = {"max_connections": 50, "urllib3": 195}
    print(f"\n[AGENT 3] Proposes delta: {agent3_delta}")
    success3, k3, msg3 = bus.propose_delta("Agent-3", agent3_delta)
    print(f"[BUS] Merged: {success3} (kappa={k3}) | {msg3}")
    print(f"[FINAL STATE] {bus.get_current_state()}")


if __name__ == "__main__":
    test_crdt_state_bus()
