import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from services.course_service.app.db.session import AsyncSessionLocal
from services.course_service.app.models.trace import Trace, TraceEvent


SENSITIVE_KEYS = {
    "password",
    "authorization",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "secret",
    "cookie",
}


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}

        for key, item in value.items():
            if key.lower() in SENSITIVE_KEYS:
                result[key] = "***REDACTED***"
            else:
                result[key] = sanitize(item)

        return result

    if isinstance(value, list):
        return [sanitize(item) for item in value]

    return value


class TraceRecorder:
    def __init__(self) -> None:
        self.started_monotonic: dict[UUID, float] = {}

    async def start(
        self,
        *,
        trace_id: UUID | None = None,
        parent_trace_id: UUID | None = None,
        trace_type: str,
        source_service: str,
        operation: str,
        actor_type: str | None = None,
        actor_id: UUID | None = None,
        course_id: UUID | None = None,
        course_version_id: UUID | None = None,
        chapter_id: UUID | None = None,
        scene_id: UUID | None = None,
        input_json: dict | None = None,
        metadata_json: dict | None = None,
    ) -> UUID:
        trace_id = trace_id or uuid4()

        trace = Trace(
            id=trace_id,
            parent_trace_id=parent_trace_id,
            trace_type=trace_type,
            source_service=source_service,
            operation=operation,
            status="running",
            actor_type=actor_type,
            actor_id=actor_id,
            course_id=course_id,
            course_version_id=course_version_id,
            chapter_id=chapter_id,
            scene_id=scene_id,
            input_json=sanitize(input_json),
            metadata_json=sanitize(metadata_json),
        )

        async with AsyncSessionLocal() as db:
            db.add(trace)
            await db.commit()

        self.started_monotonic[trace_id] = time.monotonic()

        return trace_id

    async def event(
        self,
        *,
        trace_id: UUID,
        seq: int,
        event_type: str,
        node: str | None = None,
        payload_json: dict | None = None,
    ) -> None:
        event = TraceEvent(
            trace_id=trace_id,
            seq=seq,
            event_type=event_type,
            node=node,
            payload_json=sanitize(payload_json),
        )

        async with AsyncSessionLocal() as db:
            db.add(event)
            await db.commit()

    async def success(
        self,
        *,
        trace_id: UUID,
        output_json: dict | None = None,
    ) -> None:
        async with AsyncSessionLocal() as db:
            trace = await db.get(Trace, trace_id)

            if trace is None:
                return

            started = self.started_monotonic.pop(
                trace_id,
                None,
            )

            trace.status = "success"
            trace.output_json = sanitize(output_json)
            trace.ended_at = datetime.now(timezone.utc)

            if started is not None:
                trace.latency_ms = int(
                    (time.monotonic() - started) * 1000
                )

            await db.commit()

    async def failure(
        self,
        *,
        trace_id: UUID,
        error: Exception,
    ) -> None:
        async with AsyncSessionLocal() as db:
            trace = await db.get(Trace, trace_id)

            if trace is None:
                return

            started = self.started_monotonic.pop(
                trace_id,
                None,
            )

            trace.status = "failed"
            trace.error_json = {
                "type": type(error).__name__,
                "message": str(error),
            }
            trace.ended_at = datetime.now(timezone.utc)

            if started is not None:
                trace.latency_ms = int(
                    (time.monotonic() - started) * 1000
                )

            await db.commit()


trace_recorder = TraceRecorder()
