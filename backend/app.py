"""
Re-export module for backend.app compatibility.
Bridges root app.py for imports matching backend.app.
"""

import sys
from pathlib import Path

# Ensure root directory is in sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app import (
    ContinuumGateway,
    app,
    api,
    gateway,
    trigger_semantic_interference,
    trigger_semantic_interference_sync,
)

__all__ = [
    "ContinuumGateway",
    "app",
    "api",
    "gateway",
    "trigger_semantic_interference",
    "trigger_semantic_interference_sync",
]
