"""API routes for model configuration and availability."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.infra.llm.key_validator import validate_all_keys
from app.infra.llm.key_validation import KeyValidationResult, KeyValidationStatus

router = APIRouter(prefix="/models", tags=["models"])

# Simple rate limiting: track last request time per IP
# Format: {ip: last_request_timestamp}
_rate_limit_cache: dict[str, float] = {}
RATE_LIMIT_SECONDS = 5  # Reduced from 10 to 5 seconds for better UX


def _check_rate_limit(request: Request) -> None:
    """Check if request is within rate limit.

    Raises:
        HTTPException: If rate limit exceeded
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    if client_ip in _rate_limit_cache:
        last_request = _rate_limit_cache[client_ip]
        elapsed = now - last_request
        if elapsed < RATE_LIMIT_SECONDS:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Please wait {RATE_LIMIT_SECONDS - int(elapsed)} seconds.",
            )

    _rate_limit_cache[client_ip] = now


def _serialize_validation_result(result: KeyValidationResult) -> dict:
    """Serialize KeyValidationResult to dict for JSON response."""
    return {
        "status": result.status.value,
        "provider": result.provider,
        "api_key_env": result.api_key_env,
        "error_message": result.error_message,
        "request_id": result.request_id,
        "http_status": result.http_status,
        "validated_at": result.validated_at.isoformat() if result.validated_at else None,
    }


@router.get("/available-keys")
async def get_available_keys(
    request: Request,  # FastAPI will inject this automatically
    validate: bool = False,
    force: bool = False,
):
    """Return a set of API key environment variable names that are configured.

    Args:
        validate: If True, also validate keys and return validation results
        force: If True, bypass cache and force re-validation (only used if validate=True)
        request: FastAPI request object (injected automatically, used for rate limiting)

    Returns:
        Dict with available_keys list, and optionally validation dict
    """
    available = set()

    # Map of env var names to settings attributes
    key_map = {
        "OPENAI_API_KEY": "openai_api_key",
        "ANTHROPIC_API_KEY": "anthropic_api_key",
        "MISTRAL_API_KEY": "mistral_api_key",
        "DEEPSEEK_API_KEY": "deepseek_api_key",
        "GEMINI_API_KEY": "gemini_api_key",
        "GROK_API_KEY": "grok_api_key",
    }

    for env_name, attr_name in key_map.items():
        key_value = getattr(settings, attr_name, None)
        # Check if key is actually set and not empty/None/"No"
        if key_value and isinstance(key_value, str):
            key_value = key_value.strip().lower()
            # Exclude empty strings, "No", "no", "false", "False", "none", etc.
            # Also check if it looks like a real API key (starts with common prefixes)
            invalid_values = ("no", "false", "none", "", "n/a", "na", "not set", "unset")
            is_valid = (
                key_value not in invalid_values
                and len(key_value) > 10  # Real API keys are usually longer
            )
            if is_valid:
                available.add(env_name)

    response = {"available_keys": list(available)}

    # If validation requested, add validation results
    if validate:
        # Check rate limit for validation requests
        _check_rate_limit(request)

        try:
            validation_results = await validate_all_keys(force=force)
            # Serialize validation results
            response["validation"] = {
                api_key_env: _serialize_validation_result(result)
                for api_key_env, result in validation_results.items()
            }
        except HTTPException:
            # Re-raise rate limit exceptions
            raise
        except Exception as exc:
            # Log error but don't fail the request
            # Return empty validation dict on error
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error during key validation: {exc}", exc_info=True)
            response["validation"] = {}
            response["validation_error"] = "Failed to validate keys. Please try again."

    return response
