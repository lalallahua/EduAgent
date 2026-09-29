from uuid import UUID, uuid4

from arq import Retry

from services.knowledge_service.app.core.config import (
    settings,
)
from services.knowledge_service.app.db.session import (
    AsyncSessionLocal,
)
from services.knowledge_service.app.jobs.queue import (
    get_redis_settings,
)
from services.knowledge_service.app.repositories.job_repository import (
    job_repository,
)
from services.knowledge_service.app.services.material_processor import (
    material_processor,
)


async def process_material_job(
    ctx,
    job_id: str,
    material_id: str,
    owner_id: str,
):
    job_uuid = UUID(job_id)
    material_uuid = UUID(material_id)
    owner_uuid = UUID(owner_id)

    attempt = int(
        ctx.get("job_try", 1)
    )

    # A retry needs a new Trace UUID because
    # TraceRecorder.start() inserts a new trace row.
    trace_id = uuid4()

    async with AsyncSessionLocal() as db:
        await job_repository.mark_processing(
            db,
            job_id=job_uuid,
            attempt=attempt,
            trace_id=trace_id,
        )

    try:
        result = await material_processor.process(
            material_id=material_uuid,
            owner_id=owner_uuid,
            trace_id=trace_id,
        )

    except (LookupError, ValueError) as exc:
        # Deterministic failures:
        # missing material, parser/chunk/input errors.
        async with AsyncSessionLocal() as db:
            await job_repository.mark_failed(
                db,
                job_id=job_uuid,
                attempt=attempt,
                error=exc,
            )

        raise

    except Exception as exc:
        if (
            attempt
            < settings.knowledge_job_max_tries
        ):
            async with AsyncSessionLocal() as db:
                await job_repository.mark_retrying(
                    db,
                    job_id=job_uuid,
                    attempt=attempt,
                    error=exc,
                )

            raise Retry(
                defer=min(
                    5 * attempt,
                    30,
                )
            )

        async with AsyncSessionLocal() as db:
            await job_repository.mark_failed(
                db,
                job_id=job_uuid,
                attempt=attempt,
                error=exc,
            )

        raise

    async with AsyncSessionLocal() as db:
        await job_repository.mark_succeeded(
            db,
            job_id=job_uuid,
            result_json=result,
        )

    return result


class WorkerSettings:
    functions = [
        process_material_job
    ]

    redis_settings = (
        get_redis_settings()
    )

    queue_name = (
        settings.knowledge_queue_name
    )

    max_jobs = (
        settings
        .knowledge_worker_max_jobs
    )

    job_timeout = (
        settings
        .knowledge_job_timeout_seconds
    )

    max_tries = (
        settings
        .knowledge_job_max_tries
    )

    keep_result = 3600
