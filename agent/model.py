"""
Model configuration shared by the main agent wiring (core.py) and the sub agent module
(subagents.py), so neither has to import the other.

The endpoint comes from core.llm, which defaults to the hosted DeepSeek API and can be
pointed at any OpenAI-compatible server through LLM_BASE_URL.
"""

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.openai import OpenAIProvider

from core.llm import settings

# Model id currently in use, needed by the /status command and session metadata
MODEL_NAME = settings.model

# The endpoint is OpenAI-compatible rather than OpenAI itself, so the capability flags
# are declared explicitly instead of inherited from a model-name guess: a self-hosted
# server often rejects strict tool schemas and the max_completion_tokens field.
model = OpenAIChatModel(
    MODEL_NAME,
    provider=OpenAIProvider(base_url=settings.base_url, api_key=settings.api_key),
    profile=OpenAIModelProfile(
        supports_json_schema_output=False,
        supports_json_object_output=settings.json_mode,
        openai_supports_strict_tool_definition=settings.strict_tools,
        openai_chat_supports_max_completion_tokens=settings.max_completion_tokens,
    ),
)
