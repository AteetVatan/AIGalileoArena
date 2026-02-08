"""Grok (xAI) client – OpenAI-compatible, different base URL."""

from .costs import GROK_2_PRICING
from .openai_compatible import OpenAICompatibleClient


class GrokClient(OpenAICompatibleClient):
    BASE_URL = "https://api.x.ai/v1"
    PRICING = GROK_2_PRICING
