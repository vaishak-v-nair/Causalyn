"""
Test script to verify the Causalyn Tech Stack Governance and Infrastructure.
"""
from causalyn.shadow.ambient_fabric import AmbientFabric
from causalyn.infrastructure.turbovec_engine import TurbovecEngine
from causalyn.infrastructure.colibri_moe import ColibriAirGappedEngine
from causalyn.infrastructure.anydoc_parser import AnydocIngestionPipeline
from causalyn.governance.agent_reach_sandbox import AgentReachSandbox
from causalyn.governance.mempalace_scanner import MemPalaceScanner
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(message)s")

def test_governance_and_infrastructure():
    print("=========================================================")
    print("  CAUSALYN — INFRASTRUCTURE & GOVERNANCE TEST HARNESS")
    print("=========================================================\n")

    print("[1] Testing Infrastructure Keepers")
    TurbovecEngine()
    ColibriAirGappedEngine()
    AnydocIngestionPipeline.ingest_compliance_document("test_policy.pdf")
    
    print("\n[2] Testing Agent-Reach Structural Sanitization")
    AgentReachSandbox.scrape_and_sanitize("https://reddit.com/r/learnpython")
    
    print("\n[3] Testing MemPalace Secret Scanning")
    MemPalaceScanner.scan_memory_drawer("Normal state log. Safe.")
    MemPalaceScanner.scan_memory_drawer("Leaked sk-1234567890abcdefghij secret here.")

    print("\n[4] Testing Adversarial Strix Injection in Ambient Fabric")
    fabric = AmbientFabric("./config")
    
    # Mocking a malicious file in the shadow dir to trigger Strix failure
    os.makedirs(fabric.shadow_dir, exist_ok=True)
    fabric.write_shadow_file("malicious_config.py", "execute malicious code")
    
    print("-> Forcing a state collapse evaluation (which invokes Strix)...")
    status = fabric.apply_vaishak_operator(kappa=0.0)
    print(f"-> Collapse Result: {status}")

if __name__ == "__main__":
    test_governance_and_infrastructure()
