from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.knowledge_service.app.models.knowledge import (
    KnowledgeJob,
)


ACTIVE_STATUSES = (
    "queued",
    "processing",
)


class KnowledgeJobRepository:
    async def get_active_for_material(
        self,
        db: AsyncSession,
        *,
        material_id: UUID,
        owner_id: UUID,
    ) -> KnowledgeJob | None:
        result = await db.execute(
            select(KnowledgeJob)
            .where(
                KnowledgeJob.material_id
                == material_id,
                KnowledgeJob.owner_id
                == owner_id,
                KnowledgeJob.status.in_(
                    ACTIVE_STATUSES
                ),
            )
            .order_by(
                KnowledgeJob.created_at.desc()
            )
        )

        return result.scalars().first()

    async def create(
        self,
        db: AsyncSession,
        *,
        material_id: UUID,
        owner_id: UUID,
        max_attempts: int,
    ) -> KnowledgeJob:
        job = KnowledgeJob(
            material_id=material_id,
            owner_id=owner_id,
            job_type="material_process",
            status="queued",
            stage="queued",
            progress=0,
            attempt=0,
            max_attempts=max_attempts,
        )

        db.add(job)

        await db.commit()
        await db.refresh(job)

        return job

    async def get_owned(
        self,
        db: AsyncSession,
        *,
        job_id: UUID,
        owner_id: UUID,
    ) -> KnowledgeJob | None:
        result = await db.execute(
            select(KnowledgeJob).where(
                KnowledgeJob.id == job_id,
                KnowledgeJob.owner_id
                == owner_id,
            )
        )

        return result.scalar_one_or_none()

    async def mark_processing(
        self,
        db: AsyncSession,
        *,
        job_id: UUID,
        attempt: int,
        trace_id: UUID,
    ) -> None:
        job = await db.get(
            KnowledgeJob,
            job_id,
        )

        if job is None:
            raise LookupError(
                "Knowledge job not found"
            )

        job.status = "processing"
        job.stage = "processing"
        job.progress = 5
        job.attempt = attempt
        job.trace_id = trace_id
        job.error_json = None

        if job.started_at is None:
            job.started_at = (
                datetime.now(timezone.utc)
            )

        await db.commit()

    async def mark_retrying(
        self,
        db: AsyncSession,
        *,
        job_id: UUID,
        attempt: int,
        error: Exception,
    ) -> None:
        job = await db.get(
            KnowledgeJob,
            job_id,
        )

        if job is None:
            return

        job.status = "queued"
        job.stage = "retrying"
        job.progress = 5
        job.attempt = attempt

        job.error_json = {
            "type":
                type(error).__name__,
            "message":
                str(error),
        }

        await db.commit()

    async def mark_succeeded(
        self,
        db: AsyncSession,
        *,
        job_id: UUID,
        result_json: dict,
    ) -> None:
        job = await db.get(
            KnowledgeJob,
            job_id,
        )

        if job is None:
            return

        job.status = "succeeded"
        job.stage = "completed"
        job.progress = 100

        job.result_json = result_json
        job.error_json = None

        job.finished_at = (
            datetime.now(timezone.utc)
        )

        await db.commit()

    async def mark_failed(
        self,
        db: AsyncSession,
        *,
        job_id: UUID,
        attempt: int,
        error: Exception,
    ) -> None:
        job = await db.get(
            KnowledgeJob,
            job_id,
        )

        if job is None:
            return

        job.status = "failed"
        job.stage = "failed"
        job.attempt = attempt

        job.error_json = {
            "type":
                type(error).__name__,
            "message":
                str(error),
        }

        job.finished_at = (
            datetime.now(timezone.utc)
        )

        await db.commit()


job_repository = KnowledgeJobRepository()
