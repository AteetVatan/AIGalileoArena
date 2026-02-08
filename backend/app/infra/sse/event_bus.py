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
    """Per-run subscriber queues + SSE streaming."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._seq_counters: dict[str, int] = defaultdict(int)

    def next_seq(self, run_id: str) -> int:
        self._seq_counters[run_id] += 1
        return self._seq_counters[run_id]

    async def emit(self, run_id: str, event_type: str, payload: dict[str, Any]) -> int:
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
        queue: asyncio.Queue = asyncio.Queue(maxsize=500)
        self._subscribers[run_id].append(queue)
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue) -> None:
        subs = self._subscribers.get(run_id, [])
        if queue in subs:
            subs.remove(queue)

    async def stream(
        self, run_id: str, *, heartbeat_seconds: int = 15,
    ) -> AsyncGenerator[str, None]:
        queue = self.subscribe(run_id)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=heartbeat_seconds)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            self.unsubscribe(run_id, queue)


# module-level singleton
event_bus = EventBus()


# emit + persist in one shot (used by usecases)
async def emit_and_persist(
    bus: EventBus, repo: "Repository",
    run_id: str, event_type: str, payload: dict[str, Any],
) -> int:
    seq = await bus.emit(run_id, event_type, payload)
    await repo.add_event(run_id=run_id, seq=seq, event_type=event_type, payload_json=payload)
    await repo.commit()
    return seq
