"""LLM client factory – resolve provider string to concrete client."""

from __future__ import annotations

from app.config import settings

from .anthropic_client import AnthropicClient
from .base import BaseLLMClient
from .deepseek_client import DeepSeekClient
from .gemini_client import GeminiClient
from .grok_client import GrokClient
from .mistral_client import MistralClient
from .openai_client import OpenAIClient

_PROVIDERS: dict[str, type] = {
    "openai": OpenAIClient,
    "anthropic": AnthropicClient,
    "mistral": MistralClient,
    "deepseek": DeepSeekClient,
    "gemini": GeminiClient,
    "grok": GrokClient,
}

_KEY_MAP: dict[str, str] = {
    "openai": "openai_api_key",
    "anthropic": "anthropic_api_key",
    "mistral": "mistral_api_key",
    "deepseek": "deepseek_api_key",
    "gemini": "gemini_api_key",
    "grok": "grok_api_key",
}


def get_llm_client(
    *,
    provider: str,
    model_name: str,
    api_key_env: str | None = None,
) -> BaseLLMClient:
    """Instantiate the right LLM client for *provider*."""
    provider_lower = provider.lower()
    cls = _PROVIDERS.get(provider_lower)
    if cls is None:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Supported: {', '.join(_PROVIDERS)}"
        )

    # resolve API key: explicit env-var name override or default from _KEY_MAP
    attr = (
        api_key_env.lower() if api_key_env else _KEY_MAP.get(provider_lower, "")
    )
    api_key = getattr(settings, attr, "") or ""

    if not api_key:
        raise ValueError(
            f"No API key found for provider '{provider}'. "
            f"Set {attr.upper()} in your .env file."
        )

    return cls(api_key=api_key, model_name=model_name)  # type: ignore[call-arg]
