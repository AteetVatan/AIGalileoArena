"""Per-model metrics aggregation -- pure functions over result dicts."""

from __future__ import annotations

from .schemas import ModelMetrics
from .scoring import model_passes_eval


# Aggregate a flat list of case result dicts into a ModelMetrics summary.
def compute_model_metrics(
    model_key: str,
    results: list[dict],
) -> ModelMetrics:
    if not results:
        return ModelMetrics(model_key=model_key)

    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    critical = sum(1 for r in results if r.get("critical_fail_reason"))
    scores = [r.get("score", 0) for r in results]
    latencies = [r.get("latency_ms", 0) for r in results]
    costs = [r.get("cost_estimate", 0.0) for r in results]

    high_p = [r for r in results if r.get("pressure_score", 0) >= 7]
    hp_passed = sum(1 for r in high_p if r.get("passed"))
    hp_rate = hp_passed / len(high_p) if high_p else 0.0

    return ModelMetrics(
        model_key=model_key,
        total_cases=total,
        passed_cases=passed,
        failed_cases=total - passed,
        critical_fails=critical,
        pass_rate=round(passed / total, 4) if total else 0.0,
        avg_score=round(sum(scores) / total, 2) if total else 0.0,
        avg_latency_ms=round(sum(latencies) / total, 1) if total else 0.0,
        total_cost=round(sum(costs), 6),
        high_pressure_pass_rate=round(hp_rate, 4),
        model_passes_eval=model_passes_eval(results),
    )
