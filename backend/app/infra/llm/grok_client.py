"""Grok (xAI) client – OpenAI-compatible, different base URL."""

from .openai_compatible import OpenAICompatibleClient


class GrokClient(OpenAICompatibleClient):
    BASE_URL = "https://api.x.ai/v1"
    PRICING = (2.0, 10.0)  # grok-2 approximate pricing per 1M tokens
