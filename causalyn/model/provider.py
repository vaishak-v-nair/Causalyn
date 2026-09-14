"""Provider-neutral model boundary.

No network client is imported here.  The default implementation is deliberately
disabled so importing the backend cannot cause external calls or spend money.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModelRequest:
    prompt: str
    system: str | None = None


@dataclass(frozen=True)
class ModelResponse:
    text: str
    provider: str
    model: str | None = None


class ModelProvider(Protocol):
    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response without exposing provider-specific semantics."""


class ModelProviderDisabled(RuntimeError):
    """Raised when model execution has not been explicitly enabled."""


class DisabledModelProvider:
    name = "disabled"

    def generate(self, request: ModelRequest) -> ModelResponse:
        raise ModelProviderDisabled(
            "model provider is disabled; set CAUSALYN_MODEL_ENABLED=true "
            "and configure a provider explicitly"
        )


def create_model_provider(enabled: bool = False) -> ModelProvider:
    """Create the configured boundary; provider integrations are opt-in."""

    if not enabled:
        return DisabledModelProvider()
    raise ValueError("no model provider adapter is registered")
