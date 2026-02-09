"""Parallel validation service for LLM API keys with caching."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from app.config import settings

from .key_validation import KeyValidationResult, KeyValidationStatus
from .preflight import (
    preflight_anthropic,
    preflight_deepseek,
    preflight_gemini,
    preflight_grok,
    preflight_mistral,
    preflight_openai,
)

logger = logging.getLogger(__name__)

# Cache TTL: 2 hours (increased to reduce API costs)
# Note: Validation is opt-in (manual refresh only) to avoid automatic costs
# Cost per validation:
#   - OpenAI/DeepSeek/Grok: FREE (uses models.list())
#   - Anthropic: ~$0.00001 per call (minimal messages.create with max_tokens=1)
#   - Gemini/Mistral: Varies (tries free endpoints first)
CACHE_TTL_SECONDS = 7200  # 2 hours

# In-memory cache: key -> (result, timestamp)
_validation_cache: Dict[str, tuple[KeyValidationResult, datetime]] = {}


def _get_available_keys() -> Dict[str, str]:
    """Get all configured API keys.

    Returns:
        Dict mapping api_key_env -> api_key value
    """
    key_map = {
        "OPENAI_API_KEY": "openai_api_key",
        "ANTHROPIC_API_KEY": "anthropic_api_key",
        "MISTRAL_API_KEY": "mistral_api_key",
        "DEEPSEEK_API_KEY": "deepseek_api_key",
        "GEMINI_API_KEY": "gemini_api_key",
        "GROK_API_KEY": "grok_api_key",
    }

    available = {}
    for env_name, attr_name in key_map.items():
        key_value = getattr(settings, attr_name, None)
        # Check if key is actually set and not empty/None/"No"
        if key_value and isinstance(key_value, str):
            key_value_stripped = key_value.strip().lower()
            # Exclude empty strings, "No", "no", "false", "False", "none", etc.
            invalid_values = ("no", "false", "none", "", "n/a", "na", "not set", "unset")
            is_valid = (
                key_value_stripped not in invalid_values
                and len(key_value_stripped) > 10  # Real API keys are usually longer
            )
            if is_valid:
                available[env_name] = key_value  # Store original (not lowercased)

    return available


def _get_cache_key(api_key_env: str) -> str:
    """Get cache key for an API key env var."""
    return f"key_validation:{api_key_env}"


def _get_cached_result(api_key_env: str) -> Optional[KeyValidationResult]:
    """Get cached validation result if still valid.

    Returns:
        KeyValidationResult if cached and not expired, None otherwise
    """
    cache_key = _get_cache_key(api_key_env)
    if cache_key not in _validation_cache:
        return None

    result, cached_at = _validation_cache[cache_key]
    age = (datetime.utcnow() - cached_at).total_seconds()

    if age < CACHE_TTL_SECONDS:
        logger.debug(f"Cache hit for {api_key_env} (age: {age:.1f}s)")
        return result
    else:
        # Expired, remove from cache
        del _validation_cache[cache_key]
        logger.debug(f"Cache expired for {api_key_env} (age: {age:.1f}s)")
        return None


def _set_cached_result(api_key_env: str, result: KeyValidationResult) -> None:
    """Store validation result in cache."""
    cache_key = _get_cache_key(api_key_env)
    _validation_cache[cache_key] = (result, datetime.utcnow())
    logger.debug(f"Cached validation result for {api_key_env}: {result.status}")


async def _validate_single_key(
    api_key_env: str, api_key: str, force: bool = False
) -> KeyValidationResult:
    """Validate a single API key.

    Args:
        api_key_env: Environment variable name (e.g., "OPENAI_API_KEY")
        api_key: The actual API key value
        force: If True, bypass cache

    Returns:
        KeyValidationResult
    """
    # Check cache first (unless force refresh)
    if not force:
        cached = _get_cached_result(api_key_env)
        if cached is not None:
            return cached

    # Map api_key_env to preflight function
    preflight_functions = {
        "OPENAI_API_KEY": preflight_openai,
        "ANTHROPIC_API_KEY": preflight_anthropic,
        "MISTRAL_API_KEY": preflight_mistral,
        "DEEPSEEK_API_KEY": preflight_deepseek,
        "GEMINI_API_KEY": preflight_gemini,
        "GROK_API_KEY": preflight_grok,
    }

    preflight_func = preflight_functions.get(api_key_env)
    if preflight_func is None:
        logger.warning(f"No preflight function for {api_key_env}")
        return KeyValidationResult(
            status=KeyValidationStatus.UNKNOWN_ERROR,
            provider="unknown",
            api_key_env=api_key_env,
            error_message=f"No preflight function for {api_key_env}",
        )

    try:
        # Run preflight (already has timeout built in)
        result = await preflight_func(api_key)
        # Cache the result
        _set_cached_result(api_key_env, result)
        return result
    except Exception as exc:
        # Unexpected error in preflight wrapper
        logger.error(f"Unexpected error validating {api_key_env}: {exc}", exc_info=True)
        result = KeyValidationResult(
            status=KeyValidationStatus.UNKNOWN_ERROR,
            provider="unknown",
            api_key_env=api_key_env,
            error_message=str(exc),
        )
        # Cache even errors (with shorter TTL would be better, but keep it simple)
        _set_cached_result(api_key_env, result)
        return result


async def validate_all_keys(force: bool = False) -> Dict[str, KeyValidationResult]:
    """Validate all configured API keys in parallel.

    Args:
        force: If True, bypass cache and force re-validation

    Returns:
        Dict mapping api_key_env -> KeyValidationResult
    """
    available_keys = _get_available_keys()

    if not available_keys:
        logger.debug("No API keys configured")
        return {}

    # Create validation tasks for all keys
    tasks = []
    key_envs = []
    for api_key_env, api_key in available_keys.items():
        key_envs.append(api_key_env)
        tasks.append(_validate_single_key(api_key_env, api_key, force=force))

    # Run all validations in parallel
    logger.info(f"Validating {len(tasks)} API keys in parallel (force={force})")
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results: convert exceptions to KeyValidationResult
    validation_results = {}
    for api_key_env, result in zip(key_envs, results):
        if isinstance(result, Exception):
            logger.error(
                f"Exception during validation of {api_key_env}: {result}",
                exc_info=result,
            )
            validation_results[api_key_env] = KeyValidationResult(
                status=KeyValidationStatus.UNKNOWN_ERROR,
                provider="unknown",
                api_key_env=api_key_env,
                error_message=str(result),
            )
        else:
            validation_results[api_key_env] = result

    logger.info(
        f"Validation complete: {sum(1 for r in validation_results.values() if r.status == KeyValidationStatus.VALID)}/{len(validation_results)} valid"
    )
    return validation_results
