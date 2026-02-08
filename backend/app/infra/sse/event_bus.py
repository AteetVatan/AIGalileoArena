"""In-memory SSE event bus with DB persistence for replay."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING, Any, AsyncGenerator

if TYPE_CHECKING:
    from app.infra.db.repository import Repository

logger = logging.getLogger(__name__)


class EventBus:
    """Singleton-ish event bus for SSE streaming.

    Subscribers get an asyncio.Queue per run_id.
    Events are also persisted to run_events via the repo.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._seq_counters: dict[str, int] = defaultdict(int)

    def next_seq(self, run_id: str) -> int:
        self._seq_counters[run_id] += 1
        return self._seq_counters[run_id]

    async def emit(
        self,
        run_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> int:
        """Publish event to all subscribers. Returns seq number."""
        seq = self.next_seq(run_id)
        event = {
            "seq": seq,
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }

        for queue in self._subscribers.get(run_id, []):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("SSE queue full for run %s, dropping event", run_id)

        return seq

    def subscribe(self, run_id: str) -> asyncio.Queue:
        """Create a new subscriber queue for a run."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=500)
        self._subscribers[run_id].append(queue)
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue) -> None:
        subs = self._subscribers.get(run_id, [])
        if queue in subs:
            subs.remove(queue)

    async def stream(
        self,
        run_id: str,
        *,
        heartbeat_seconds: int = 15,
    ) -> AsyncGenerator[str, None]:
        """Yield SSE-formatted strings for a subscriber."""
        queue = self.subscribe(run_id)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(
                        queue.get(), timeout=heartbeat_seconds
                    )
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            self.unsubscribe(run_id, queue)


# module-level singleton
event_bus = EventBus()


async def emit_and_persist(
    bus: EventBus,
    repo: Repository,
    run_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> int:
    """Emit an SSE event and persist it to run_events in one step.

    Used by both RunEvalUsecase and ReplayCachedUsecase to avoid
    duplicating the emit+store+commit pattern.
    """
    seq = await bus.emit(run_id, event_type, payload)
    await repo.add_event(
        run_id=run_id,
        seq=seq,
        event_type=event_type,
        payload_json=payload,
    )
    await repo.commit()
    return seq
