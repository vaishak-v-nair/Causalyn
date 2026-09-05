"""
Self-Reflective Invariant Injection (GAP 3)

Injects absolute mathematical boundaries into the agent's context window.
Extracts the Intent Vector (I) from the Z3 Math Kernel and formats it as an LLM prompt.
"""

from typing import Dict, Any

class InvariantInjector:
    def __init__(self):
        # We can pull these directly from the intent configuration 
        # or evaluate them via the AcausalSynthesizer's active constraints.
        self.global_constraints = {
            "urllib3": "< 2.0.0",
            "fastapi": ">= 0.95.0",
            "db_connections": "<= 10",
            "memory_alloc_mb": "<= 2048",
            "port_number": "[1024, 65535]",
            "timeout_ms": "<= 30000",
            "worker_count": "<= 16"
        }

    def generate_system_prompt_prefix(self) -> str:
        """
        Translates the Z3 system constraints into a strict structured prompt prefix.
        Forces the AI to generate code perfectly aligned with the architecture from token 1.
        """
        prompt = (
            "<vpsn_intent_vector>\n"
            "CRITICAL ARCHITECTURAL INVARIANTS. DO NOT VIOLATE THESE MATHEMATICAL CONSTRAINTS.\n"
            "The Acausal Synthesizer will automatically annihilate any proposed state that violates these limits:\n\n"
        )
        
        for key, limit in self.global_constraints.items():
            prompt += f"- {key}: {limit}\n"
            
        prompt += (
            "</vpsn_intent_vector>\n"
            "Ensure all proposed architecture, configurations, and variables strictly adhere to the above manifold constraints."
        )
        return prompt

    def inject_into_agent(self, agent_id: str, original_prompt: str) -> str:
        """
        Middleware to inject the invariants directly into the agent's prompt pipeline.
        """
        return f"{self.generate_system_prompt_prefix()}\n\n{original_prompt}"
