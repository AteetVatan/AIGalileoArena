"""
Single-round LLM eval → leaderboard report for social media posting.

Runs 6 models × 2 random datasets × 2 random cases (≈24 evals),
generates a formatted leaderboard, prints to stdout and saves to disk.

Designed to be called by OpenClaw's cron system.

Usage:
    python scripts/run_eval_report.py
    python scripts/run_eval_report.py --base http://localhost:8000
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Reuse core logic from the 24h eval runner
from run_24h_evals import MODELS, list_datasets, run_one_round, log


def build_leaderboard(results: list[dict]) -> str:
    """Build a text leaderboard from one round of eval results."""
    today = datetime.now(tz=timezone.utc).strftime("%b %d, %Y")

    # Aggregate per model
    model_stats: dict[str, dict] = defaultdict(
        lambda: {"scores": [], "ok": 0, "err": 0, "cost": 0.0}
    )
    for r in results:
        m = r["model"]
        if r["status"] == "COMPLETED":
            model_stats[m]["ok"] += 1
            if r.get("score") is not None:
                model_stats[m]["scores"].append(float(r["score"]))
        else:
            model_stats[m]["err"] += 1
        model_stats[m]["cost"] += float(r.get("cost") or 0)

    # Sort by avg score descending
    ranked = sorted(
        model_stats.items(),
        key=lambda kv: (
            sum(kv[1]["scores"]) / len(kv[1]["scores"]) if kv[1]["scores"] else 0
        ),
        reverse=True,
    )

    # ── Build report ──
    lines: list[str] = []
    lines.append(f"🏆 AI Galileo Arena — Daily LLM Eval ({today})")
    lines.append("")
    lines.append(f"{'#':<3} {'Model':<35} {'Avg':>6} {'Win%':>6} {'Cost':>8}")
    lines.append("─" * 62)

    for i, (model, stats) in enumerate(ranked, 1):
        total = stats["ok"] + stats["err"]
        avg = (
            f"{sum(stats['scores']) / len(stats['scores']):.1f}"
            if stats["scores"]
            else "  -"
        )
        win_pct = f"{stats['ok'] / total * 100:.0f}%" if total else "-"
        cost = f"${stats['cost']:.4f}"
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "  ")
        lines.append(f"{medal:<3} {model:<35} {avg:>6} {win_pct:>6} {cost:>8}")

    lines.append("")
    total_cost = sum(s["cost"] for s in model_stats.values())
    total_evals = sum(s["ok"] + s["err"] for s in model_stats.values())
    total_ok = sum(s["ok"] for s in model_stats.values())
    lines.append(
        f"Evals: {total_evals} | Passed: {total_ok} | "
        f"Total cost: ${total_cost:.4f}"
    )
    lines.append("")
    lines.append("#AI #LLM #Benchmark #AIGalileoArena")

    return "\n".join(lines)


def build_linkedin_post(results: list[dict]) -> str:
    """Build a LinkedIn-friendly version of the report (more professional tone)."""
    today = datetime.now(tz=timezone.utc).strftime("%B %d, %Y")

    model_stats: dict[str, dict] = defaultdict(
        lambda: {"scores": [], "ok": 0, "err": 0, "cost": 0.0}
    )
    for r in results:
        m = r["model"]
        if r["status"] == "COMPLETED":
            model_stats[m]["ok"] += 1
            if r.get("score") is not None:
                model_stats[m]["scores"].append(float(r["score"]))
        else:
            model_stats[m]["err"] += 1
        model_stats[m]["cost"] += float(r.get("cost") or 0)

    ranked = sorted(
        model_stats.items(),
        key=lambda kv: (
            sum(kv[1]["scores"]) / len(kv[1]["scores"]) if kv[1]["scores"] else 0
        ),
        reverse=True,
    )

    lines: list[str] = []
    lines.append(f"🏆 Daily LLM Performance Report — {today}")
    lines.append("")
    lines.append(
        "We run daily head-to-head evaluations of leading LLMs "
        "across randomized datasets in our AI Galileo Arena. "
        "Here are today's results:"
    )
    lines.append("")

    for i, (model, stats) in enumerate(ranked, 1):
        avg = (
            f"{sum(stats['scores']) / len(stats['scores']):.1f}"
            if stats["scores"]
            else "N/A"
        )
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        lines.append(f"{medal} {model} — Score: {avg}")

    lines.append("")
    lines.append(
        "Models tested: GPT-4o, Claude Sonnet 4, Mistral Large, "
        "DeepSeek, Gemini 2.0 Flash, Grok-3"
    )
    lines.append("")
    lines.append("#ArtificialIntelligence #LLM #Benchmark #MachineLearning #AI")

    return "\n".join(lines)


def save_report(report: str, reports_dir: Path, suffix: str = "") -> Path:
    """Save report to disk, return the file path."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    filename = f"eval_{date_str}{suffix}.txt"
    path = reports_dir / filename
    path.write_text(report, encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one eval round and generate a leaderboard report.",
    )
    parser.add_argument(
        "--base", default="http://localhost:8000", help="Backend API base URL"
    )
    parser.add_argument(
        "--timeout", type=int, default=300, help="Timeout per run (seconds)"
    )
    args = parser.parse_args()

    base = args.base.rstrip("/")

    # Discover datasets
    all_datasets = list_datasets(base)
    if not all_datasets:
        log.error("No datasets found at %s/datasets", base)
        sys.exit(1)
    log.info("Found %d datasets", len(all_datasets))

    # Run one round
    log.info("Running eval round: %d models × 2 datasets × 2 cases", len(MODELS))
    results, ok, err = run_one_round(base, all_datasets, round_num=1, timeout_s=args.timeout)

    if not results:
        log.error("No results produced")
        sys.exit(1)

    # Generate reports
    twitter_report = build_leaderboard(results)
    linkedin_report = build_linkedin_post(results)

    # Save to disk
    reports_dir = Path(__file__).resolve().parent.parent / "reports"
    twitter_path = save_report(twitter_report, reports_dir, "_twitter")
    linkedin_path = save_report(linkedin_report, reports_dir, "_linkedin")
    log.info("Twitter report saved: %s", twitter_path)
    log.info("LinkedIn report saved: %s", linkedin_path)

    # Print both reports to stdout (OpenClaw captures this)
    print("=== TWITTER REPORT ===")
    print(twitter_report)
    print()
    print("=== LINKEDIN REPORT ===")
    print(linkedin_report)

    log.info("Done — %d ok, %d errors", ok, err)
    sys.exit(0 if err == 0 else 1)


if __name__ == "__main__":
    main()
