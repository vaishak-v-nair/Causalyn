"""Vercel Serverless Function entrypoint for Causalyn."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add repository root to sys.path for serverless imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Set VERCEL environment variable for runtime adaptation
os.environ.setdefault("VERCEL", "1")

# Export canonical top-level FastAPI instance
from app import app, api

__all__ = ["app", "api"]
