from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings

from services.knowledge_service.app.core.config import (
    settings,
)


def get_redis_settings() -> RedisSettings:
    return RedisSettings(
        host=settings.redis_host,
        port=settings.redis_port,
        database=settings.redis_db,
    )


async def enqueue_material_process(
    *,
    job_id: UUID,
    material_id: UUID,
    owner_id: UUID,
) -> None:
    redis = await create_pool(
        get_redis_settings(),
        default_queue_name=(
            settings.knowledge_queue_name
        ),
    )

    try:
        queued = await redis.enqueue_job(
            "process_material_job",
            str(job_id),
            str(material_id),
            str(owner_id),
            _job_id=str(job_id),
            _queue_name=(
                settings.knowledge_queue_name
            ),
        )

        if queued is None:
            raise RuntimeError(
                "ARQ refused to enqueue "
                "material processing job"
            )

    finally:
        await redis.aclose()
