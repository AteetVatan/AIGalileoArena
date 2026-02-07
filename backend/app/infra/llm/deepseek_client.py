"""DeepSeek client – OpenAI-compatible, just a different base URL."""

from .openai_compatible import OpenAICompatibleClient


class DeepSeekClient(OpenAICompatibleClient):
    BASE_URL = "https://api.deepseek.com"
    PRICING = (0.14, 0.28)  # deepseek-chat pricing per 1M tokens
