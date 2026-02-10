"""Provider-specific preflight validation functions for API keys."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import anthropic
from google import genai
from mistralai import Mistral
from openai import APIError, AsyncOpenAI, RateLimitError

from .key_validation import (
    KeyValidationResult,
    KeyValidationStatus,
    classify_error,
)

logger = logging.getLogger(__name__)

# Timeout for individual preflight calls (8 seconds)
PREFLIGHT_TIMEOUT = 8


async def preflight_openai(api_key: str) -> KeyValidationResult:
    """Preflight validation for OpenAI API key.

    Uses models.list() which is lightweight and free.
    Falls back to minimal chat completion if models.list() is unavailable.
    """
    provider = "openai"
    api_key_env = "OPENAI_API_KEY"

    try:
        client = AsyncOpenAI(api_key=api_key, base_url="https://api.openai.com/v1")

        # Primary: Try models.list() - lightweight, no cost
        try:
            await asyncio.wait_for(
                client.models.list(),
                timeout=PREFLIGHT_TIMEOUT,
            )
            return KeyValidationResult(
                status=KeyValidationStatus.VALID,
                provider=provider,
                api_key_env=api_key_env,
                http_status=200,
            )
        except AttributeError:
            # Fallback: models.list() not available, use minimal chat completion
            logger.debug("OpenAI models.list() not available, using chat completion fallback")
            await asyncio.wait_for(
                client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1,
                ),
                timeout=PREFLIGHT_TIMEOUT,
            )
            return KeyValidationResult(
                status=KeyValidationStatus.VALID,
                provider=provider,
                api_key_env=api_key_env,
                http_status=200,
            )
    except asyncio.TimeoutError:
        return KeyValidationResult(
            status=KeyValidationStatus.TIMEOUT,
            provider=provider,
            api_key_env=api_key_env,
            error_message="Preflight request timed out",
        )
    except APIError as exc:
        status = getattr(exc, "status_code", None)
        message = getattr(exc, "message", str(exc))
        request_id = getattr(exc, "request_id", None)
        return KeyValidationResult(
            status=classify_error(status, message),
            provider=provider,
            api_key_env=api_key_env,
            error_message=message,
            request_id=request_id,
            http_status=status,
        )
    except RateLimitError as exc:
        # RateLimitError is a subclass of APIError but check separately
        status = getattr(exc, "status_code", 429)
        message = getattr(exc, "message", str(exc))
        request_id = getattr(exc, "request_id", None)
        return KeyValidationResult(
            status=classify_error(status, message),
            provider=provider,
            api_key_env=api_key_env,
            error_message=message,
            request_id=request_id,
            http_status=status,
        )
    except Exception as exc:
        # Catch-all for unexpected errors
        logger.warning("Unexpected error in OpenAI preflight: %s", exc, exc_info=True)
        return KeyValidationResult(
            status=classify_error(None, str(exc)),
            provider=provider,
            api_key_env=api_key_env,
            error_message=str(exc),
        )


async def preflight_anthropic(api_key: str) -> KeyValidationResult:
    """Preflight validation for Anthropic API key.

    Uses minimal messages.create() call (costs ~$0.00001).
    Anthropic doesn't have a free models.list endpoint.
    """
    provider = "anthropic"
    api_key_env = "ANTHROPIC_API_KEY"

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)

        await asyncio.wait_for(
            client.messages.create(
                model="claude-3-haiku-20240307",  # Cheapest model
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}],
            ),
            timeout=PREFLIGHT_TIMEOUT,
        )
        return KeyValidationResult(
            status=KeyValidationStatus.VALID,
            provider=provider,
            api_key_env=api_key_env,
            http_status=200,
        )
    except asyncio.TimeoutError:
        return KeyValidationResult(
            status=KeyValidationStatus.TIMEOUT,
            provider=provider,
            api_key_env=api_key_env,
            error_message="Preflight request timed out",
        )
    except anthropic.APIError as exc:
        status = getattr(exc, "status_code", None)
        message = getattr(exc, "message", str(exc))
        error_type = getattr(exc, "type", None)  # e.g., "authentication_error"
        request_id = None
        if hasattr(exc, "response") and exc.response:
            request_id = exc.response.headers.get("anthropic-request-id")
        return KeyValidationResult(
            status=classify_error(status, message, error_type),
            provider=provider,
            api_key_env=api_key_env,
            error_message=message,
            request_id=request_id,
            http_status=status,
        )
    except Exception as exc:
        logger.warning("Unexpected error in Anthropic preflight: %s", exc, exc_info=True)
        return KeyValidationResult(
            status=classify_error(None, str(exc)),
            provider=provider,
            api_key_env=api_key_env,
            error_message=str(exc),
        )


async def preflight_gemini(api_key: str) -> KeyValidationResult:
    """Preflight validation for Gemini API key.

    Tries models.list() if available, falls back to minimal generate_content.
    """
    provider = "gemini"
    api_key_env = "GEMINI_API_KEY"

    try:
        client = genai.Client(api_key=api_key)

        # Try models.list() first if available
        try:
            models = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.models.list(),
                ),
                timeout=PREFLIGHT_TIMEOUT,
            )
            # If we get here, the call succeeded
            return KeyValidationResult(
                status=KeyValidationStatus.VALID,
                provider=provider,
                api_key_env=api_key_env,
                http_status=200,
            )
        except AttributeError:
            # Fallback to minimal generate_content
            logger.debug("Gemini models.list() not available, using generate_content fallback")
            await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents="test",
                        config={"max_output_tokens": 1},
                    ),
                ),
                timeout=PREFLIGHT_TIMEOUT,
            )
            return KeyValidationResult(
                status=KeyValidationStatus.VALID,
                provider=provider,
                api_key_env=api_key_env,
                http_status=200,
            )
    except asyncio.TimeoutError:
        return KeyValidationResult(
            status=KeyValidationStatus.TIMEOUT,
            provider=provider,
            api_key_env=api_key_env,
            error_message="Preflight request timed out",
        )
    except Exception as exc:
        # Gemini errors vary - check common attributes
        status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
        message = str(exc)
        logger.warning("Error in Gemini preflight: %s", exc, exc_info=True)
        return KeyValidationResult(
            status=classify_error(status, message),
            provider=provider,
            api_key_env=api_key_env,
            error_message=message,
            http_status=status,
        )


async def preflight_mistral(api_key: str) -> KeyValidationResult:
    """Preflight validation for Mistral API key.

    Tries models.list() if available, falls back to minimal chat completion.
    """
    provider = "mistral"
    api_key_env = "MISTRAL_API_KEY"

    try:
        client = Mistral(api_key=api_key)

        # Mistral SDK may have models.list() - check first
        if hasattr(client, "models") and hasattr(client.models, "list"):
            await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.models.list(),
                ),
                timeout=PREFLIGHT_TIMEOUT,
            )
            return KeyValidationResult(
                status=KeyValidationStatus.VALID,
                provider=provider,
                api_key_env=api_key_env,
                http_status=200,
            )
        else:
            # Fallback to minimal chat
            await asyncio.wait_for(
                client.chat.complete_async(
                    model="mistral-small-latest",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1,
                ),
                timeout=PREFLIGHT_TIMEOUT,
            )
            return KeyValidationResult(
                status=KeyValidationStatus.VALID,
                provider=provider,
                api_key_env=api_key_env,
                http_status=200,
            )
    except asyncio.TimeoutError:
        return KeyValidationResult(
            status=KeyValidationStatus.TIMEOUT,
            provider=provider,
            api_key_env=api_key_env,
            error_message="Preflight request timed out",
        )
    except Exception as exc:
        # Mistral errors similar to OpenAI
        status = getattr(exc, "status_code", None)
        message = getattr(exc, "message", str(exc))
        logger.warning("Error in Mistral preflight: %s", exc, exc_info=True)
        return KeyValidationResult(
            status=classify_error(status, message),
            provider=provider,
            api_key_env=api_key_env,
            error_message=message,
            http_status=status,
        )


async def preflight_deepseek(api_key: str) -> KeyValidationResult:
    """Preflight validation for DeepSeek API key.

    Uses OpenAI-compatible API, same as OpenAI preflight.
    """
    provider = "deepseek"
    api_key_env = "DEEPSEEK_API_KEY"

    try:
        client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")

        # Primary: Try models.list() - lightweight, no cost
        try:
            await asyncio.wait_for(
                client.models.list(),
                timeout=PREFLIGHT_TIMEOUT,
            )
            return KeyValidationResult(
                status=KeyValidationStatus.VALID,
                provider=provider,
                api_key_env=api_key_env,
                http_status=200,
            )
        except AttributeError:
            # Fallback: models.list() not available, use minimal chat completion
            logger.debug("DeepSeek models.list() not available, using chat completion fallback")
            await asyncio.wait_for(
                client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1,
                ),
                timeout=PREFLIGHT_TIMEOUT,
            )
            return KeyValidationResult(
                status=KeyValidationStatus.VALID,
                provider=provider,
                api_key_env=api_key_env,
                http_status=200,
            )
    except asyncio.TimeoutError:
        return KeyValidationResult(
            status=KeyValidationStatus.TIMEOUT,
            provider=provider,
            api_key_env=api_key_env,
            error_message="Preflight request timed out",
        )
    except APIError as exc:
        status = getattr(exc, "status_code", None)
        message = getattr(exc, "message", str(exc))
        request_id = getattr(exc, "request_id", None)
        return KeyValidationResult(
            status=classify_error(status, message),
            provider=provider,
            api_key_env=api_key_env,
            error_message=message,
            request_id=request_id,
            http_status=status,
        )
    except RateLimitError as exc:
        status = getattr(exc, "status_code", 429)
        message = getattr(exc, "message", str(exc))
        request_id = getattr(exc, "request_id", None)
        return KeyValidationResult(
            status=classify_error(status, message),
            provider=provider,
            api_key_env=api_key_env,
            error_message=message,
            request_id=request_id,
            http_status=status,
        )
    except Exception as exc:
        logger.warning("Unexpected error in DeepSeek preflight: %s", exc, exc_info=True)
        return KeyValidationResult(
            status=classify_error(None, str(exc)),
            provider=provider,
            api_key_env=api_key_env,
            error_message=str(exc),
        )


async def preflight_grok(api_key: str) -> KeyValidationResult:
    """Preflight validation for Grok API key.

    Uses OpenAI-compatible API, same as OpenAI preflight.
    """
    provider = "grok"
    api_key_env = "GROK_API_KEY"

    try:
        client = AsyncOpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

        # Primary: Try models.list() - lightweight, no cost
        try:
            await asyncio.wait_for(
                client.models.list(),
                timeout=PREFLIGHT_TIMEOUT,
            )
            return KeyValidationResult(
                status=KeyValidationStatus.VALID,
                provider=provider,
                api_key_env=api_key_env,
                http_status=200,
            )
        except AttributeError:
            # Fallback: models.list() not available, use minimal chat completion
            logger.debug("Grok models.list() not available, using chat completion fallback")
            await asyncio.wait_for(
                client.chat.completions.create(
                    model="grok-2",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1,
                ),
                timeout=PREFLIGHT_TIMEOUT,
            )
            return KeyValidationResult(
                status=KeyValidationStatus.VALID,
                provider=provider,
                api_key_env=api_key_env,
                http_status=200,
            )
    except asyncio.TimeoutError:
        return KeyValidationResult(
            status=KeyValidationStatus.TIMEOUT,
            provider=provider,
            api_key_env=api_key_env,
            error_message="Preflight request timed out",
        )
    except APIError as exc:
        status = getattr(exc, "status_code", None)
        message = getattr(exc, "message", str(exc))
        request_id = getattr(exc, "request_id", None)
        return KeyValidationResult(
            status=classify_error(status, message),
            provider=provider,
            api_key_env=api_key_env,
            error_message=message,
            request_id=request_id,
            http_status=status,
        )
    except RateLimitError as exc:
        status = getattr(exc, "status_code", 429)
        message = getattr(exc, "message", str(exc))
        request_id = getattr(exc, "request_id", None)
        return KeyValidationResult(
            status=classify_error(status, message),
            provider=provider,
            api_key_env=api_key_env,
            error_message=message,
            request_id=request_id,
            http_status=status,
        )
    except Exception as exc:
        logger.warning("Unexpected error in Grok preflight: %s", exc, exc_info=True)
        return KeyValidationResult(
            status=classify_error(None, str(exc)),
            provider=provider,
            api_key_env=api_key_env,
            error_message=str(exc),
        )
