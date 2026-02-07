"""BaseLLMClient Protocol – core contract for all LLM adapters."""

from __future__ import annotations

from typing import Any, Optional, Protocol


class LLMResponse:
    """Holds the result of an LLM call."""

    __slots__ = ("text", "latency_ms", "cost_estimate")

    def __init__(
        self, text: str, latency_ms: int = 0, cost_estimate: float = 0.0
    ) -> None:
        self.text = text
        self.latency_ms = latency_ms
        self.cost_estimate = cost_estimate


class BaseLLMClient(Protocol):
    """Every provider must implement this interface."""

    async def complete(
        self,
        prompt: str,
        *,
        json_schema: Optional[dict[str, Any]] = None,
        temperature: float = 0.0,
        timeout: int = 60,
        retries: int = 3,
    ) -> LLMResponse:
        """Return model completion; enforce JSON schema if given."""
        ...
