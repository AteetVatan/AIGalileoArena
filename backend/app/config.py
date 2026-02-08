"""App settings -- all config from env vars via pydantic-settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).parent.parent
_ENV_FILE = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = Field(
        default="postgresql+asyncpg://galileo:galileo_pass@localhost:5432/galileo_arena",
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key from OPENAI_API_KEY env var",
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key from ANTHROPIC_API_KEY env var",
    )
    mistral_api_key: Optional[str] = Field(
        default=None,
        description="Mistral API key from MISTRAL_API_KEY env var",
    )
    deepseek_api_key: Optional[str] = Field(
        default=None,
        description="DeepSeek API key from DEEPSEEK_API_KEY env var",
    )
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Gemini API key from GEMINI_API_KEY env var",
    )
    grok_api_key: Optional[str] = Field(
        default=None,
        description="Grok API key from GROK_API_KEY env var",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level from LOG_LEVEL env var",
    )

    # prompt versioning
    prompt_version: str = Field(
        default="v1",
        description="Prompt template version directory to use (e.g. v1, v2)",
    )

    # cache / replay
    store_result: bool = Field(
        default=False,
        description="Persist LLM results as cache slots and serve from cache when available",
    )
    cache_results: int = Field(
        default=4,
        ge=1,
        description="Number of cache slots per (dataset, model, case) triple",
    )

    @property
    def debug_mode(self) -> bool:
        return self.log_level.upper() == "DEBUG"


settings = Settings()
