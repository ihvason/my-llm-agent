"""
Single source of truth for the model endpoint.

Every model client in the app reads its endpoint from here, so switching between
the hosted DeepSeek API and a self-hosted OpenAI-compatible server needs only
environment variables:

- LLM_BASE_URL: endpoint base, e.g. http://127.0.0.1:8000/v1
- LLM_MODEL: model id served by the endpoint
- LLM_API_KEY: optional; a placeholder is used for keyless local servers
- LLM_CONTEXT_WINDOW: context size, so compaction triggers at the right point
- LLM_JSON_MODE / LLM_MAX_COMPLETION_TOKENS / LLM_STRICT_TOOLS: capability flags
"""

import json
import os
from dataclasses import dataclass

from openai import AsyncOpenAI

# Defaults preserve the original hosted behavior: leaving LLM_BASE_URL unset keeps
# the agent on the DeepSeek API.
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"
DEFAULT_CONTEXT_WINDOW = 131_072


def _flag(name: str, default: bool) -> bool:
    """Read a boolean environment flag; an unset variable keeps the default."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class LLMSettings:
    """Resolved endpoint configuration shared by the agent and the sidecar clients."""

    base_url: str
    api_key: str
    model: str
    context_window: int
    json_mode: bool
    max_completion_tokens: bool
    strict_tools: bool


def _load() -> LLMSettings:
    base_url = os.environ.get("LLM_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("API_KEY")

    if not api_key:
        # The hosted API cannot work without a key, so fail at startup with a clear
        # message. A self-hosted server usually ignores the key, but the OpenAI
        # client still requires a non-empty value.
        if base_url == DEFAULT_BASE_URL:
            raise RuntimeError(
                "API_KEY is not set. Set API_KEY for the hosted API, or set "
                "LLM_BASE_URL to a self-hosted OpenAI-compatible endpoint."
            )
        api_key = "local"

    return LLMSettings(
        base_url=base_url,
        api_key=api_key,
        model=os.environ.get("LLM_MODEL", DEFAULT_MODEL),
        context_window=int(os.environ.get("LLM_CONTEXT_WINDOW", str(DEFAULT_CONTEXT_WINDOW))),
        json_mode=_flag("LLM_JSON_MODE", True),
        max_completion_tokens=_flag("LLM_MAX_COMPLETION_TOKENS", True),
        strict_tools=_flag("LLM_STRICT_TOOLS", True),
    )


settings = _load()


def async_client() -> AsyncOpenAI:
    """Build a client for the requests that bypass the agent framework."""
    return AsyncOpenAI(api_key=settings.api_key, base_url=settings.base_url)


def extract_json_object(text: str) -> dict:
    """
    Parse the first JSON object in a reply, tolerating prose or code fences around it.

    Used when the endpoint does not implement `response_format={"type": "json_object"}`
    and the model wraps the payload in an explanation.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found in the reply")
    return json.loads(text[start : end + 1])
