"""App settings -- all config from env vars via pydantic-settings."""

import logging
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).parent.parent
_ENV_FILE = _BACKEND_ROOT / ".env"


# Debate-mode defaults (prod)
DEFAULT_DEBATE_ENABLED_MODELS = "mistral/mistral-large-latest,deepseek/deepseek-chat"
DEFAULT_DEBATE_DAILY_CAP = 3
DEFAULT_EVAL_SCHEDULER_CRON_DAY = 1
DEFAULT_EVAL_SCHEDULER_CRON_HOUR = 2
DEFAULT_EVAL_SCHEDULER_DATASETS = 6
DEFAULT_EVAL_SCHEDULER_CASES = 1
DEFAULT_TIMEZONE = "Europe/Berlin"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = Field(
        default="postgresql+asyncpg://galileo:galileo_pass@localhost:5432/galileo_arena",
    )
    database_url_migrations: str = Field(
        default="",
        description="Separate connection string for Alembic migrations (postgres role). Falls back to database_url if empty.",
    )
    database_require_ssl: bool = Field(
        default=False,
        description="Require SSL for database connections (enable for Supabase / cloud-hosted Postgres)",
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

    _LOG_LEVEL_MAP: dict[str, int] = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    @property
    def log_level_int(self) -> int:
        return self._LOG_LEVEL_MAP.get(self.log_level.upper(), logging.INFO)

    # --- environment mode ---
    debug: bool = Field(
        default=True,
        description="Debug mode: all models enabled, no daily caps, no scheduler restrictions",
    )

    @property
    def debug_mode(self) -> bool:
        return self.debug

    # --- debate mode (prod) ---
    debate_daily_cap: int = Field(
        default=DEFAULT_DEBATE_DAILY_CAP,
        ge=1,
        description="Max debate calls per model per calendar day (prod only)",
    )
    debate_enabled_models: str = Field(
        default=DEFAULT_DEBATE_ENABLED_MODELS,
        description="Comma-separated provider/model_name pairs allowed in debate mode (prod only)",
    )
    app_timezone: str = Field(
        default=DEFAULT_TIMEZONE,
        description="Timezone for daily cap resets and scheduler triggers",
    )

    @property
    def debate_enabled_model_keys(self) -> list[str]:
        return [m.strip() for m in self.debate_enabled_models.split(",") if m.strip()]

    # --- monthly eval scheduler (prod) ---
    eval_scheduler_enabled: bool = Field(
        default=False,
        description="Enable monthly evaluation scheduler (prod only, ignored in debug)",
    )
    eval_scheduler_cron_day: int = Field(
        default=DEFAULT_EVAL_SCHEDULER_CRON_DAY,
        ge=1, le=28,
        description="Day of month for scheduled eval (1-28)",
    )
    eval_scheduler_cron_hour: int = Field(
        default=DEFAULT_EVAL_SCHEDULER_CRON_HOUR,
        ge=0, le=23,
        description="Hour (in app_timezone) for scheduled eval",
    )
    eval_scheduler_datasets: int = Field(
        default=DEFAULT_EVAL_SCHEDULER_DATASETS,
        ge=1,
        description="Number of datasets to evaluate per scheduled run",
    )
    eval_scheduler_cases: int = Field(
        default=DEFAULT_EVAL_SCHEDULER_CASES,
        ge=1,
        description="Random cases per dataset per scheduled run",
    )

    def get_api_key(self, provider: str) -> str | None:
        """Explicit provider → key mapping. No getattr."""
        key_map: dict[str, str | None] = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "mistral": self.mistral_api_key,
            "deepseek": self.deepseek_api_key,
            "gemini": self.gemini_api_key,
            "grok": self.grok_api_key,
        }
        return key_map.get(provider.lower())

    # --- galileo sweep ---
    sweep_enabled: bool = False
    sweep_cron_hour: int = 3
    sweep_cases_count: int = 5
    sweep_include_baseline: bool = True
    sweep_max_evals_per_run: int = 50
    sweep_max_parallel: int = 3
    sweep_max_cost_usd: float = 5.0

    # --- analytics query timeouts (seconds) ---
    analytics_timeout_summary_s: int = 5
    analytics_timeout_trend_s: int = 5
    analytics_timeout_heatmap_s: int = 15
    analytics_timeout_distribution_s: int = 10
    analytics_timeout_default_s: int = 10
    analytics_cache_ttl_s: int = 60


settings = Settings()
