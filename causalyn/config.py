"""Runtime configuration with conservative, local-only defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class RuntimeSettings:
    """Settings used by the HTTP process and its optional model adapter."""

    host: str = "127.0.0.1"
    port: int = 8000
    database_path: str = str(ROOT / "runtime" / "causalyn.sqlite3")
    model_enabled: bool = False
    model_provider: str | None = None
    model_name: str | None = None
    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    openrouter_api_key: str | None = None
    nvidia_nim_key: str | None = None

    @classmethod
    def from_env(cls) -> "RuntimeSettings":
        raw_port = os.getenv("CAUSALYN_PORT", "8000")
        try:
            port = int(raw_port)
        except ValueError:
            port = 8000
        if not 1 <= port <= 65535:
            port = 8000
        provider = os.getenv("CAUSALYN_MODEL_PROVIDER") or None
        return cls(
            host=os.getenv("CAUSALYN_HOST", "127.0.0.1"),
            port=port,
            database_path=os.getenv(
                "CAUSALYN_DB", str(ROOT / "runtime" / "causalyn.sqlite3")
            ),
            model_enabled=_env_bool("CAUSALYN_MODEL_ENABLED"),
            model_provider=provider,
            model_name=os.getenv("CAUSALYN_MODEL_NAME") or None,
            gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
            groq_api_key=os.getenv("GROQ_API_KEY") or None,
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY") or None,
            nvidia_nim_key=os.getenv("NVIDIA_NIM_KEY") or None,
        )


def get_settings() -> RuntimeSettings:
    """Return a fresh settings snapshot (environment changes are observable)."""

    return RuntimeSettings.from_env()
