from __future__ import annotations

from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.metrics import compute_model_metrics
from app.core.domain.schemas import ModelMetrics, RunSummary
from app.infra.db.repository import Repository


async def compute_run_summary(session: AsyncSession, run_id: str) -> RunSummary:
    repo = Repository(session)
    run = await repo.get_run(run_id)
    results = await repo.get_run_results(run_id)

    # group by model, include case_id so we can match pressure later
    by_model: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_model[r.model_key].append({
            "case_id": r.case_id,
            "score": r.score,
            "passed": r.passed,
            "critical_fail_reason": r.critical_fail_reason,
            "latency_ms": r.latency_ms,
            "cost_estimate": float(r.cost_estimate),
            "pressure_score": 5,  # enriched below
        })

    # enrich pressure from dataset_cases
    dataset_id = run.dataset_id if run else ""
    cases = await repo.get_dataset_cases(dataset_id)
    pressure_map = {c.case_id: c.pressure_score for c in cases}

    for entries in by_model.values():
        for entry in entries:
            entry["pressure_score"] = pressure_map.get(entry["case_id"], 5)

    models: list[ModelMetrics] = [
        compute_model_metrics(mk, entries) for mk, entries in by_model.items()
    ]

    return RunSummary(
        run_id=run_id,
        status=run.status if run else "UNKNOWN",
        total_cases=len(results),
        models=models,
    )
