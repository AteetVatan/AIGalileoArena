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

    # --- ML scoring (ONNX) ---
    ml_scoring_enabled: bool = Field(
        default=True,
        description="Enable ONNX ML-enhanced scoring (requires models in ml_models_dir)",
    )
    ml_models_dir: str = Field(
        default="models",
        description="Directory containing exported ONNX models (relative to backend root)",
    )
    onnx_intra_threads: int = Field(
        default=2, ge=1,
        description="ONNX Runtime intra-op thread count (leave cores for uvicorn)",
    )
    ml_max_workers: int = Field(
        default=2, ge=1,
        description="Max concurrent ML scoring threads in the bounded executor",
    )
    ml_nli_max_tokens: int = Field(
        default=384, ge=64, le=512,
        description="Max token length for NLI cross-encoder inputs (truncation limit)",
    )
    ml_falsifiable_threshold: float = Field(
        default=0.45, ge=0.0, le=1.0,
        description="Cosine-sim threshold for semantic falsifiability exemplar match",
    )
    ml_deference_threshold_low: float = Field(
        default=0.4,
        description="NLI entailment below this = no deference penalty",
    )
    ml_deference_threshold_mid: float = Field(
        default=0.6,
        description="NLI entailment below this = -5 deference penalty",
    )
    ml_deference_threshold_high: float = Field(
        default=0.8,
        description="NLI entailment below this = -10; above = -15 deference penalty",
    )
    ml_refusal_threshold: float = Field(
        default=0.6, ge=0.0, le=1.0,
        description="NLI entailment threshold above which refusal penalty is applied",
    )

    # --- AutoGen debate mode ---
    use_autogen_debate: bool = Field(
        default=False,
        description="Use AutoGen-powered debate orchestration instead of FSM controller",
    )
    autogen_max_cross_exam_messages: int = Field(
        default=2, ge=1, le=20,
        description="Max agent turns in AutoGen cross-examination phase",
    )
    autogen_enable_tools: bool = Field(
        default=False,
        description="Enable evidence retrieval tools for AutoGen debate agents",
    )

    @property
    def debug_mode(self) -> bool:
        return self.log_level.upper() == "DEBUG"


settings = Settings()
