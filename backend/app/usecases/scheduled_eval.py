"""Monthly scheduled evaluation: 5 models × N datasets × M random cases."""

from __future__ import annotations

import logging
import random
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infra.db.repository import Repository
from app.infra.db.session import async_session_factory
from app.infra.sse.event_bus import event_bus
from app.usecases.run_eval import RunEvalUsecase

logger = logging.getLogger(__name__)

_SCHEDULER_MODELS = [
    {"provider": "openai", "model_name": "gpt-4o", "api_key_env": "OPENAI_API_KEY"},
    {"provider": "anthropic", "model_name": "claude-sonnet-4-20250514", "api_key_env": "ANTHROPIC_API_KEY"},
    {"provider": "mistral", "model_name": "mistral-large-latest", "api_key_env": "MISTRAL_API_KEY"},
    {"provider": "deepseek", "model_name": "deepseek-chat", "api_key_env": "DEEPSEEK_API_KEY"},
    {"provider": "grok", "model_name": "grok-3", "api_key_env": "GROK_API_KEY"},
]

_STATUS_COMPLETED = "completed"
_STATUS_SKIPPED = "skipped"


async def _run_single_eval(
    *, dataset_id: str, case_id: str, model: dict[str, str],
) -> None:
    """Run one eval with its own session for isolation."""
    run_id = str(uuid.uuid4())
    async with async_session_factory() as session:
        repo = Repository(session)
        await repo.create_run(
            run_id=run_id,
            dataset_id=dataset_id,
            case_id=case_id,
            models_json=[{"provider": model["provider"], "model_name": model["model_name"]}],
        )
        await repo.commit()

        uc = RunEvalUsecase(session, event_bus)
        await uc.execute(
            dataset_id=dataset_id,
            case_id=case_id,
            models=[model],
            run_id=run_id,
        )
    logger.info(
        "Scheduled eval done: run_id=%s dataset=%s case=%s model=%s/%s",
        run_id, dataset_id, case_id,
        model["provider"], model["model_name"],
    )


async def run_scheduled_eval(
    session: AsyncSession,
) -> dict[str, object]:
    """Execute the monthly eval batch.

    Picks N random datasets, M random cases per dataset, runs all 5 models.
    Each eval gets its own session for isolation.
    """
    repo = Repository(session)
    datasets = await repo.list_datasets()
    if not datasets:
        logger.warning("No datasets found for scheduled eval")
        return {"status": _STATUS_SKIPPED, "reason": "no datasets"}

    n_datasets = min(settings.eval_scheduler_datasets, len(datasets))
    n_cases = settings.eval_scheduler_cases
    selected_ds = random.sample(datasets, n_datasets)

    total_runs = 0
    errors = 0

    for ds in selected_ds:
        cases = await repo.get_dataset_cases(ds.id)
        if not cases:
            continue
        chosen_cases = random.sample(cases, min(n_cases, len(cases)))

        for case_row in chosen_cases:
            for model in _SCHEDULER_MODELS:
                try:
                    await _run_single_eval(
                        dataset_id=ds.id,
                        case_id=case_row.case_id,
                        model=model,
                    )
                    total_runs += 1
                except (OSError, ConnectionError) as exc:
                    errors += 1
                    logger.exception(
                        "Scheduled eval network error: dataset=%s case=%s model=%s/%s",
                        ds.id, case_row.case_id,
                        model["provider"], model["model_name"],
                    )
                except Exception as exc:
                    errors += 1
                    logger.exception(
                        "Scheduled eval failed: dataset=%s case=%s model=%s/%s",
                        ds.id, case_row.case_id,
                        model["provider"], model["model_name"],
                    )

    return {
        "status": _STATUS_COMPLETED,
        "total_runs": total_runs,
        "errors": errors,
        "datasets_used": n_datasets,
        "cases_per_dataset": n_cases,
    }
