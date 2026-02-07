"""TOML serialization/deserialization utilities for LLM interaction.

Uses:
  - ``tomllib`` (stdlib 3.11+) for parsing TOML text → dict.
  - ``tomli_w`` for writing dict → TOML text.

All LLM prompts emit and expect TOML; internal storage stays JSON.
"""

from __future__ import annotations

import re
import tomllib
from typing import Any

import tomli_w

# ── Pre-processing helpers ───────────────────────────────────────────────────

_FENCE_RE = re.compile(
    r"```(?:toml)?\s*\n(.*?)```",
    re.DOTALL,
)


def _strip_none(data: Any) -> Any:
    """Recursively remove ``None`` values (TOML has no null)."""
    if isinstance(data, dict):
        return {k: _strip_none(v) for k, v in data.items() if v is not None}
    if isinstance(data, list):
        return [_strip_none(item) for item in data]
    return data


def _ensure_floats(data: Any, float_keys: frozenset[str] = frozenset({"confidence"})) -> Any:
    """Ensure known float fields stay ``float`` so TOML writes ``0.9`` not ``0``."""
    if isinstance(data, dict):
        out: dict[str, Any] = {}
        for k, v in data.items():
            if k in float_keys and isinstance(v, int):
                out[k] = float(v)
            else:
                out[k] = _ensure_floats(v, float_keys)
        return out
    if isinstance(data, list):
        return [_ensure_floats(item, float_keys) for item in data]
    return data


# ── Public API ───────────────────────────────────────────────────────────────


def dict_to_toml(data: dict[str, Any]) -> str:
    """Serialize a Python dict to a TOML string.

    Pre-processes the dict to:
      1. Strip ``None`` values (TOML has no null).
      2. Ensure known float fields keep ``float`` type.
    """
    cleaned = _strip_none(data)
    cleaned = _ensure_floats(cleaned)
    return tomli_w.dumps(cleaned)


def toml_to_dict(text: str) -> dict[str, Any]:
    """Parse a TOML string (potentially wrapped in markdown fences) to dict.

    Handles common LLM output quirks:
      1. Strips markdown ``` fences (with or without ``toml`` tag).
      2. Falls back to extracting the first TOML-like block from mixed text.

    Raises ``ValueError`` when no valid TOML can be extracted.
    """
    cleaned = _extract_toml_block(text)
    try:
        return tomllib.loads(cleaned)
    except tomllib.TOMLDecodeError:
        pass

    # Last resort: try the raw stripped text
    try:
        return tomllib.loads(text.strip())
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Could not parse TOML: {exc}") from exc


# ── Internal extraction ──────────────────────────────────────────────────────


def _extract_toml_block(text: str) -> str:
    """Extract TOML content from LLM output.

    Strategy (ordered):
      1. If text is wrapped in ```toml ... ```, extract inner content.
      2. If text starts with a valid TOML key line, use as-is.
      3. Find the first line that looks like a TOML key=value and take
         everything from there to the end (or a closing fence).
    """
    stripped = text.strip()

    # 1. Fenced block
    match = _FENCE_RE.search(stripped)
    if match:
        return match.group(1).strip()

    # 2. Generic ``` fences without toml tag
    if stripped.startswith("```"):
        first_nl = stripped.find("\n")
        last_fence = stripped.rfind("```", first_nl)
        if first_nl != -1 and last_fence > first_nl:
            return stripped[first_nl + 1:last_fence].strip()

    # 3. Already looks like TOML (starts with a key = value or [[)
    if _looks_like_toml(stripped):
        return stripped

    # 4. Find first TOML-like line in mixed output
    for idx, line in enumerate(stripped.splitlines()):
        if _looks_like_toml(line):
            return "\n".join(stripped.splitlines()[idx:]).strip()

    return stripped


def _looks_like_toml(text: str) -> bool:
    """Heuristic: does this text start with a TOML key-value or table header?"""
    first = text.lstrip()
    if not first:
        return False
    # Table header [[array]] or [section]
    if first.startswith("["):
        return True
    # key = value
    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*=', first):
        return True
    return False
