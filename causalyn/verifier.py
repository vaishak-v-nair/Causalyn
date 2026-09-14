"""Cross-vendor fix verification.

Sends the proposed fix, causal report, and original task description to a
model from a *different vendor* than the one that wrote the bug.  The
independent model's job is narrow: does this fix address the actual root
cause, or does it just suppress the symptom?
"""

from __future__ import annotations

import json
import os
import time
from typing import Optional

from .config import CausalynConfig
from .models import CausalReport, VerificationVerdict


class VerificationError(Exception):
    """Raised when verification cannot proceed."""


# ------------------------------------------------------------------
# Prompt template — this is the entire prompt.  Kept simple and fixed
# to prevent prompt injection via user-controlled fields.
# ------------------------------------------------------------------

_VERIFICATION_PROMPT = """\
You are an independent code reviewer.  A coding agent made a mistake that \
was traced to a specific root cause by a causal bisection tool.  The agent \
has now proposed a fix.  Your job is to evaluate whether the fix addresses \
the *actual root cause*, or whether it merely suppresses the symptom in a \
way that could regress.

## Causal Report
{causal_report}

## Diff at Root-Cause Step
```diff
{root_cause_diff}
```

## Agent's Proposed Fix
```diff
{proposed_fix}
```

## Original Task Description
{task_description}

---

Respond with a JSON object (no markdown fences) containing:
- "agrees": true/false — does the fix address the root cause?
- "concerns": [] — list of specific concerns (empty if agrees is true)
- "recommendation": "" — what you'd recommend instead (empty if agrees is true)
- "confidence": 0.0–1.0 — your confidence in this assessment
"""


def verify_fix(
    proposed_fix: str,
    report: CausalReport,
    task_description: str = "",
    config: CausalynConfig | None = None,
) -> VerificationVerdict:
    """Send the fix to an independent model for verification.

    Raises VerificationError if the API call fails after retries.
    """
    config = config or CausalynConfig.from_env()
    provider = config.verification_provider
    model = config.verification_model
    prompt = _VERIFICATION_PROMPT.format(
        causal_report=report.summary,
        root_cause_diff=report.diff_at_root_cause or "(not available)",
        proposed_fix=proposed_fix,
        task_description=task_description or "(not provided)",
    )

    def _attempt_verification(p: str, m: str) -> VerificationVerdict | None:
        api_key = config.get_api_key(p)
        if p != "mock" and not api_key:
            raise VerificationError(
                f"No API key configured for provider '{p}'. "
                f"Set the appropriate environment variable."
            )
        
        for attempt in range(3):  # 1 initial + 2 retries
            try:
                raw_response = _call_model(
                    provider=p,
                    model=m,
                    prompt=prompt,
                    api_key=api_key,
                    timeout=config.verification_timeout_s,
                )
                return _parse_verdict(raw_response, model_name=f"{p}/{m}")
            except Exception as e:
                print(f"[Verifier] Attempt {attempt + 1} failed for {p}/{m}: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    return None
        return None

    # Try primary provider
    result = _attempt_verification(provider, model)
    if result is not None:
        return result

    # If primary was NIM and it failed, fallback to Groq
    if provider == "nim":
        print("[Verifier] NIM failed after retries, falling back to Groq...")
        fallback_model = "openai/gpt-oss-120b"
        result = _attempt_verification("groq", fallback_model)
        if result is not None:
            return result

    raise VerificationError(f"Verification failed after retries for provider {provider}")


def _call_model(
    *,
    provider: str,
    model: str,
    prompt: str,
    api_key: str,
    timeout: int,
) -> str:
    """Dispatch to the appropriate provider SDK.

    We use the OpenAI-compatible chat completions API for OpenAI and Groq
    (Groq is OpenAI-compatible).  For Anthropic and Gemini, we use their
    native SDKs.
    """
    if provider == "mock":
        return (
            '{"agrees": false, '
            '"concerns": ["The fix merely suppresses the symptom by replacing `None` with `object()`. This will prevent the AttributeError but the auth middleware logic is still broken.", "It does not restore the authentication logic."], '
            '"recommendation": "Restore the AuthMiddleware instance: `auth = AuthMiddleware()`", '
            '"confidence": 0.99}'
        )
    elif provider in ("openai", "groq", "nim"):
        base_url = None
        if provider == "groq":
            base_url = "https://api.groq.com/openai/v1"
        elif provider == "nim":
            base_url = "https://integrate.api.nvidia.com/v1"
        return _call_openai_compatible(
            prompt=prompt,
            model=model,
            api_key=api_key,
            timeout=timeout,
            base_url=base_url,
        )
    elif provider == "anthropic":
        return _call_anthropic(prompt=prompt, model=model, api_key=api_key, timeout=timeout)
    elif provider == "gemini":
        return _call_gemini(prompt=prompt, model=model, api_key=api_key, timeout=timeout)
    else:
        raise VerificationError(f"Unsupported provider: {provider}")


def _call_openai_compatible(
    *,
    prompt: str,
    model: str,
    api_key: str,
    timeout: int,
    base_url: str | None = None,
) -> str:
    """Call an OpenAI-compatible chat completions endpoint."""
    try:
        from openai import OpenAI
    except ImportError:
        raise VerificationError(
            "The 'openai' package is required for OpenAI/Groq verification. "
            "Install it with: pip install openai"
        )

    client = OpenAI(api_key=api_key, timeout=timeout, **({"base_url": base_url} if base_url else {}))
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,  # Low temp for consistent evaluations
        max_tokens=1024,
    )
    return response.choices[0].message.content or ""


def _call_anthropic(*, prompt: str, model: str, api_key: str, timeout: int) -> str:
    """Call the Anthropic Messages API."""
    try:
        from anthropic import Anthropic
    except ImportError:
        raise VerificationError(
            "The 'anthropic' package is required for Anthropic verification. "
            "Install it with: pip install anthropic"
        )

    client = Anthropic(api_key=api_key, timeout=timeout)
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return response.content[0].text if response.content else ""


def _call_gemini(*, prompt: str, model: str, api_key: str, timeout: int) -> str:
    """Call the Google Gemini API via the google-genai SDK."""
    try:
        from google import genai
    except ImportError:
        raise VerificationError(
            "The 'google-genai' package is required for Gemini verification. "
            "Install it with: pip install google-genai"
        )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    return response.text or ""


def _parse_verdict(raw_response: str, model_name: str) -> VerificationVerdict:
    """Parse the model's JSON response into a VerificationVerdict.

    Tolerant of models that wrap JSON in markdown fences.
    """
    text = raw_response.strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first and last lines (the fences)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Model didn't return valid JSON — treat the whole response as a
        # concern and mark as disagreement to be safe.
        return VerificationVerdict(
            agrees=False,
            concerns=[f"Verification model returned non-JSON response: {raw_response[:200]}"],
            recommendation="Manual review required — the verification model's response could not be parsed.",
            confidence=0.0,
            model_used=model_name,
            raw_response=raw_response,
        )

    return VerificationVerdict(
        agrees=bool(data.get("agrees", False)),
        concerns=data.get("concerns", []),
        recommendation=data.get("recommendation", ""),
        confidence=float(data.get("confidence", 0.5)),
        model_used=model_name,
        raw_response=raw_response,
    )
