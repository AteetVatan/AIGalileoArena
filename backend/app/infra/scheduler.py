"""APScheduler wrapper for the freshness sweep cron job.

Only starts when settings.sweep_enabled is True.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None

_JOB_ID = "galileo_freshness_sweep"


async def _sweep_job() -> None:
    from app.infra.db.session import async_session_factory
    from app.usecases.freshness_sweep import run_freshness_sweep

    try:
        async with async_session_factory() as session:
            result = await run_freshness_sweep(session)
            logger.info("Scheduled sweep result: %s", result.get("message", "done"))
    except Exception:
        logger.exception("Scheduled sweep failed")


def start_scheduler() -> None:
    global _scheduler
    if not settings.sweep_enabled:
        logger.info("Sweep scheduler disabled (SWEEP_ENABLED=false)")
        return
    if _scheduler is not None:
        return

    _scheduler = AsyncIOScheduler()
    trigger = CronTrigger(hour=settings.sweep_cron_hour, minute=0)
    _scheduler.add_job(
        _sweep_job,
        trigger=trigger,
        id=_JOB_ID,
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info(
        "Sweep scheduler started (daily at %02d:00 UTC)",
        settings.sweep_cron_hour,
    )


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Sweep scheduler stopped")
