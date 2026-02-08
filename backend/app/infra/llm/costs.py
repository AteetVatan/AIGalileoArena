"""Centralized LLM model pricing constants.

All pricing is in USD per 1 million tokens (input, output).
Format: (input_cost_per_1M_tokens, output_cost_per_1M_tokens)
"""

from typing import Final

# OpenAI models (GPT-4o)
OPENAI_GPT4O_PRICING: Final[tuple[float, float]] = (2.50, 10.00)

# Anthropic models (Claude 3.5 Sonnet)
ANTHROPIC_CLAUDE_35_SONNET_PRICING: Final[tuple[float, float]] = (3.00, 15.00)

# Mistral models (Mistral Large 2.1 / mistral-large-2411)
MISTRAL_LARGE_PRICING: Final[tuple[float, float]] = (2.00, 6.00)

# DeepSeek models (deepseek-chat) — using *input cache miss* as default input price
DEEPSEEK_CHAT_PRICING: Final[tuple[float, float]] = (0.27, 1.10)

# Google Gemini models (Gemini 2.0 Flash)
GEMINI_20_FLASH_PRICING: Final[tuple[float, float]] = (0.10, 0.40)

# Grok (xAI) models (Grok 2)
GROK_2_PRICING: Final[tuple[float, float]] = (2.00, 10.00)

# Default fallback pricing (used by openai_compatible base class)
DEFAULT_PRICING: Final[tuple[float, float]] = (1.00, 2.00)