"""Strict model_key parser for LLM identity canonicalization.

Prevents identity fragmentation in find-or-create flows.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.domain.exceptions import GalileoError


class InvalidModelKeyError(GalileoError):
    def __init__(self, model_key: str) -> None:
        super().__init__(f"Cannot parse model_key: '{model_key}'")
        self.model_key = model_key


@dataclass(frozen=True)
class ModelIdentity:
    provider: str
    model_name: str
    version: str | None = None


def parse_model_key(model_key: str) -> ModelIdentity:
    """Parse 'provider/model_name' or 'provider/model_name@version'.

    Raises InvalidModelKeyError if format is unrecognised.
    """
    if "/" not in model_key:
        raise InvalidModelKeyError(model_key)

    provider, rest = model_key.split("/", maxsplit=1)
    if not provider or not rest:
        raise InvalidModelKeyError(model_key)

    if "@" in rest:
        model_name, version = rest.rsplit("@", maxsplit=1)
        return ModelIdentity(
            provider=provider.lower(),
            model_name=model_name,
            version=version or None,
        )

    return ModelIdentity(provider=provider.lower(), model_name=rest)


def build_model_key(identity: ModelIdentity) -> str:
    """Reconstruct canonical model_key from identity."""
    base = f"{identity.provider}/{identity.model_name}"
    if identity.version:
        return f"{base}@{identity.version}"
    return base
