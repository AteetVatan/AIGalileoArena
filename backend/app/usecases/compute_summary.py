"""Compute run summary from stored results."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.metrics import compute_model_metrics
from app.core.domain.schemas import ModelMetrics, RunSummary
from app.infra.db.repository import Repository


async def compute_run_summary(
    session: AsyncSession,
    run_id: str,
) -> RunSummary:
    """Build a RunSummary from the run_results table."""
    repo = Repository(session)
    run = await repo.get_run(run_id)
    results = await repo.get_run_results(run_id)

    # group by model_key
    by_model: dict[str, list[dict]] = {}
    for r in results:
        key = r.model_key
        if key not in by_model:
            by_model[key] = []
        by_model[key].append({
            "score": r.score,
            "passed": r.passed,
            "critical_fail_reason": r.critical_fail_reason,
            "latency_ms": r.latency_ms,
            "cost_estimate": float(r.cost_estimate),
            "pressure_score": 5,  # we'll enrich below
        })

    # enrich with pressure_score from dataset_cases
    dataset_id = run.dataset_id if run else ""
    cases = await repo.get_dataset_cases(dataset_id)
    pressure_map = {c.case_id: c.pressure_score for c in cases}

    for r in results:
        for entry in by_model.get(r.model_key, []):
            if entry.get("score") == r.score:
                entry["pressure_score"] = pressure_map.get(r.case_id, 5)
                break

    models: list[ModelMetrics] = []
    for model_key, entries in by_model.items():
        metrics = compute_model_metrics(model_key, entries)
        models.append(metrics)

    return RunSummary(
        run_id=run_id,
        status=run.status if run else "UNKNOWN",
        total_cases=len(results),
        models=models,
    )
