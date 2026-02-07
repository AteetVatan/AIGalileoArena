"""Application settings via pydantic-settings. All config from env vars."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env file path relative to backend directory (2 levels up from this file)
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
        description="Database connection URL",
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


settings = Settings()
