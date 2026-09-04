"""Provider-agnostic LLM integration for Causalyn control plane.

Supports Gemini (Primary), Groq, OpenRouter, and NVIDIA NIM with fail-closed
semantics and strict JSON/reasoning extraction.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol

from causalyn.config import RuntimeSettings

logger = logging.getLogger("causalyn.llm")


@dataclass(frozen=True)
class LLMMessage:
    role: str  # "system", "user", "assistant"
    content: str


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    provider: str
    token_usage: dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0


class LLMProvider(Protocol):
    def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResponse: ...


class NullProvider:
    """Deterministic null provider for offline testing and air-gapped runs."""

    def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        return LLMResponse(
            content="{}",
            model="null",
            provider="null",
            token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            latency_ms=0.0,
        )


class GeminiProvider:
    """Native Google Gemini provider via REST API."""

    def __init__(self, api_key: str, model_name: str = "gemini-3.6-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={api_key}"
        )

    def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        start_time = time.perf_counter()

        system_instruction = None
        contents = []
        for msg in messages:
            if msg.role == "system":
                system_instruction = {"parts": [{"text": msg.content}]}
            elif msg.role == "user":
                contents.append({"role": "user", "parts": [{"text": msg.content}]})
            elif msg.role == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg.content}]})

        body: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instruction:
            body["systemInstruction"] = system_instruction

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            logger.error("Gemini API error %d: %s", exc.code, err_body)
            raise RuntimeError(f"Gemini API returned {exc.code}: {err_body}") from exc
        except Exception as exc:
            logger.error("Gemini connection error: %s", exc)
            raise RuntimeError(f"Gemini connection failed: {exc}") from exc

        candidates = result.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned empty candidate list.")

        text_parts = []
        for part in candidates[0].get("content", {}).get("parts", []):
            if "text" in part:
                text_parts.append(part["text"])
        content = "".join(text_parts).strip()

        usage = result.get("usageMetadata", {})
        latency = (time.perf_counter() - start_time) * 1000.0

        return LLMResponse(
            content=content,
            model=self.model_name,
            provider="gemini",
            token_usage={
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
                "total_tokens": usage.get("totalTokenCount", 0),
            },
            latency_ms=latency,
        )


class OpenAICompatibleProvider:
    """Generic provider for OpenAI-compatible completions (Groq, OpenRouter, NVIDIA NIM)."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        provider_name: str,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.provider_name = provider_name
        self.endpoint = f"{self.base_url}/chat/completions"

    def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        start_time = time.perf_counter()

        formatted_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        if self.provider_name == "openrouter":
            headers["HTTP-Referer"] = "https://causalyn.ai"
            headers["X-Title"] = "Causalyn Hypervisor"

        req = urllib.request.Request(
            self.endpoint,
            data=data,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            logger.error("%s API error %d: %s", self.provider_name, exc.code, err_body)
            raise RuntimeError(f"{self.provider_name} API error {exc.code}: {err_body}") from exc
        except Exception as exc:
            logger.error("%s connection error: %s", self.provider_name, exc)
            raise RuntimeError(f"{self.provider_name} connection failed: {exc}") from exc

        choices = result.get("choices", [])
        if not choices:
            raise RuntimeError(f"{self.provider_name} returned empty choices.")

        content = choices[0].get("message", {}).get("content", "").strip()
        usage = result.get("usage", {})
        latency = (time.perf_counter() - start_time) * 1000.0

        return LLMResponse(
            content=content,
            model=self.model_name,
            provider=self.provider_name,
            token_usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            latency_ms=latency,
        )


class GroqProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile"):
        super().__init__(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
            model_name=model_name,
            provider_name="groq",
        )


class OpenRouterProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str, model_name: str = "anthropic/claude-3.5-sonnet"):
        super().__init__(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            model_name=model_name,
            provider_name="openrouter",
        )


class NvidiaProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str, model_name: str = "meta/llama-3.1-70b-instruct"):
        super().__init__(
            api_key=api_key,
            base_url="https://integrate.api.nvidia.com/v1",
            model_name=model_name,
            provider_name="nvidia",
        )


def create_llm_provider(settings: RuntimeSettings) -> LLMProvider:
    """Create the active LLM provider based on priority and environment keys."""
    # Explicit provider override if requested
    if settings.model_provider:
        p = settings.model_provider.lower()
        if p == "gemini" and settings.gemini_api_key:
            return GeminiProvider(
                settings.gemini_api_key,
                settings.model_name or "gemini-3.6-flash",
            )
        if p == "groq" and settings.groq_api_key:
            return GroqProvider(
                settings.groq_api_key,
                settings.model_name or "llama-3.3-70b-versatile",
            )
        if p == "openrouter" and settings.openrouter_api_key:
            return OpenRouterProvider(
                settings.openrouter_api_key,
                settings.model_name or "anthropic/claude-3.5-sonnet",
            )
        if p in ("nvidia", "nim") and settings.nvidia_nim_key:
            return NvidiaProvider(
                settings.nvidia_nim_key,
                settings.model_name or "meta/llama-3.1-70b-instruct",
            )

    # Automatic priority selection: Gemini -> Groq -> OpenRouter -> NVIDIA
    if settings.gemini_api_key:
        return GeminiProvider(
            settings.gemini_api_key,
            settings.model_name or "gemini-3.6-flash",
        )
    if settings.groq_api_key:
        return GroqProvider(
            settings.groq_api_key,
            settings.model_name or "llama-3.3-70b-versatile",
        )
    if settings.openrouter_api_key:
        return OpenRouterProvider(
            settings.openrouter_api_key,
            settings.model_name or "anthropic/claude-3.5-sonnet",
        )
    if settings.nvidia_nim_key:
        return NvidiaProvider(
            settings.nvidia_nim_key,
            settings.model_name or "meta/llama-3.1-70b-instruct",
        )

    return NullProvider()
