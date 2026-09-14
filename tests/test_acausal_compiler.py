import pytest
from causalyn.verification.acausal_compiler import AcausalCompiler

def test_syntax_auto_correction():
    compiler = AcausalCompiler()
    
    # Missing colon (Syntax Error)
    broken_code = "def validate_state()\n    return True\n"
    
    kappa, msg, corrected = compiler.verify_and_correct(broken_code)
    
    assert kappa == 0.0, "Kappa should be smoothed to 0.0"
    assert "Semantic Ricci Flow applied successfully" in msg
    assert "def validate_state():" in corrected

def test_destructive_interference():
    compiler = AcausalCompiler()
    
    # Contains a banned call (os.system)
    dangerous_code = "import os\ndef do_work():\n    os.system('rm -rf /')\n"
    
    kappa, msg, corrected = compiler.verify_and_correct(dangerous_code)
    
    assert kappa > 0.0, "Kappa should spike for destructive interference"
    assert "Destructive Interference Detected" in msg
    assert "os.system" not in corrected
    assert "pass # Auto-corrected by Causalyn" in corrected
