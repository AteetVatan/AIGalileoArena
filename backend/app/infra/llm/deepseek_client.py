"""DeepSeek client – OpenAI-compatible, just a different base URL."""

from .costs import DEEPSEEK_CHAT_PRICING
from .openai_compatible import OpenAICompatibleClient


class DeepSeekClient(OpenAICompatibleClient):
    BASE_URL = "https://api.deepseek.com"
    PRICING = DEEPSEEK_CHAT_PRICING
