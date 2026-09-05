import threading
import time
import asyncio
from typing import Dict, Any, Tuple
from causalyn.verification.cegar_loop import AcausalSynthesizer

class HyperDimensionalStateBus:
    """
    The Hyper-Dimensional State Bus (GAP 2).
    Maps concurrent agent intents into the Vaishak Continuum and dynamically calculates 
    geometric conflicts (Paradox Index kappa) using the Z3 Mathematical Kernel.
    Blocks destructive interference atomically.
    """
    
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(HyperDimensionalStateBus, cls).__new__(cls)
                cls._instance.active_intents = {}
                cls._instance.state_lock = threading.Lock()
                cls._instance.synthesizer = AcausalSynthesizer()
                cls._instance.synthesizer.apply_intent_vector()
        return cls._instance

    def register_intent(self, agent_id: str, proposed_state: Dict[str, Any]) -> Tuple[bool, float, str]:
        """
        Maps an agent's intent to the Continuum.
        Calculates kappa against all other active intents geometrically.
        
        Returns:
            (is_allowed, kappa, message)
        """
        with self.state_lock:
            # Clean up stale intents (older than 10 seconds for prototype)
            current_time = time.time()
            stale_agents = [aid for aid, intent in self.active_intents.items() 
                            if current_time - intent['timestamp'] > 10.0]
            for aid in stale_agents:
                del self.active_intents[aid]
            
            # 1. Project to Vaishak Continuum (Aggregate State)
            combined_state = {}
            # Base combined state from currently active intents
            for active_agent_id, active_intent in self.active_intents.items():
                if active_agent_id == agent_id:
                    continue
                for k, v in active_intent['proposed_state'].items():
                    combined_state[k] = max(combined_state.get(k, 0), v)
                    
            # Add the new proposed state
            for k, v in proposed_state.items():
                # Simple collision logic for exact key matches if they differ geometrically
                if k in combined_state and combined_state[k] != v:
                    return False, 100.0, f"Destructive Interference: Agent swarm conflict on invariant '{k}'."
                combined_state[k] = max(combined_state.get(k, 0), v)
            
            # 2. Evaluate against Z3 Math Kernel (Paradox Index > 0)
            kappa, feedback = self._instance.synthesizer.evaluate_candidate_state(combined_state)
            
            if kappa > 0:
                # Paradox Detected. Rollback.
                return False, kappa, f"Geometric State Collision: {feedback[0] if feedback else 'Unknown mathematical conflict.'}"
            
            # If admissible, lock the vector
            self.active_intents[agent_id] = {
                'proposed_state': proposed_state,
                'timestamp': current_time
            }
            
            return True, 0.0, "Intent mapped to the Vaishak Continuum successfully."

    def release_intent(self, agent_id: str):
        """Releases the state lock after atomic commit."""
        with self.state_lock:
            if agent_id in self.active_intents:
                del self.active_intents[agent_id]
