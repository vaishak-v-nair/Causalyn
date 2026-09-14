import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import ast
from backend.core.z3_engine import verify_invariants

def test_safe_mutation():
    code = "threads = 8\nmemory = 512"
    tree = ast.parse(code)
    rules = ["MAX_THREADS=16", "MAX_MEMORY=1024", "LEAK_CHECK"]
    assert verify_invariants(tree, rules) == True
    print("test_safe_mutation passed")

def test_unsafe_mutation():
    code = "threads = 32\nmemory = 4096"
    tree = ast.parse(code)
    rules = ["MAX_THREADS=16", "MAX_MEMORY=1024", "LEAK_CHECK"]
    assert verify_invariants(tree, rules) == False
    print("test_unsafe_mutation passed")

if __name__ == "__main__":
    test_safe_mutation()
    test_unsafe_mutation()
    print("All Z3 engine tests passed!")
