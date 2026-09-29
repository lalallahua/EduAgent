import hashlib
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    UploadFile,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from services.course_service.app.tracing.recorder import (
    trace_recorder,
)
from services.knowledge_service.app.core.config import (
    settings,
)
from services.knowledge_service.app.db.session import (
    get_db,
)
from services.knowledge_service.app.models.knowledge import (
    Asset,
)
from services.knowledge_service.app.repositories.knowledge_repository import (
    KnowledgeRepository,
)
from services.knowledge_service.app.jobs.queue import (
    enqueue_material_process,
)
from services.knowledge_service.app.repositories.job_repository import (
    job_repository,
)
from services.knowledge_service.app.schemas.job import (
    KnowledgeJobRead,
)
from services.knowledge_service.app.schemas.material import (
    ChunkRead,
    MaterialRead,
)
from services.knowledge_service.app.services.storage import (
    object_storage,
)


router = APIRouter()

repository = KnowledgeRepository()


def current_user_id(
    x_user_id: UUID = Header(
        alias="X-User-Id"
    ),
) -> UUID:
    return x_user_id


def incoming_trace_id(
    x_trace_id: UUID | None = Header(
        default=None,
        alias="X-Trace-Id",
    ),
) -> UUID | None:
    return x_trace_id


def source_type_for(
    filename: str,
) -> str:
    suffix = Path(
        filename
    ).suffix.lower()

    mapping = {
        ".pdf": "pdf",
        ".pptx": "pptx",
        ".docx": "docx",
        ".txt": "text",
        ".md": "markdown",
        ".markdown": "markdown",
    }

    return mapping.get(
        suffix,
        "binary",
    )


@router.post(
    "/materials",
    response_model=MaterialRead,
    status_code=201,
)
async def upload_material(
    course_id: UUID = Form(...),
    file: UploadFile = File(...),
    owner_id: UUID = Depends(
        current_user_id
    ),
    trace_id: UUID | None = Depends(
        incoming_trace_id
    ),
    db: AsyncSession = Depends(get_db),
):
    course = (
        await repository.get_owned_course(
            db,
            course_id=course_id,
            owner_id=owner_id,
        )
    )

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    filename = (
        file.filename
        or "material.bin"
    )

    data = await file.read()

    if not data:
        raise HTTPException(
            status_code=400,
            detail="Empty file",
        )

    if (
        len(data)
        > settings.material_max_bytes
    ):
        raise HTTPException(
            status_code=413,
            detail="Material too large",
        )

    mime_type = (
        file.content_type
        or "application/octet-stream"
    )

    checksum = hashlib.sha256(
        data
    ).hexdigest()

    trace_id = await trace_recorder.start(
        trace_id=trace_id,
        trace_type="knowledge_pipeline",
        source_service="knowledge-service",
        operation="material.upload",
        actor_type="teacher",
        actor_id=owner_id,
        course_id=course_id,
        input_json={
            "filename": filename,
            "mime_type": mime_type,
            "size_bytes":
                len(data),
            "checksum_sha256":
                checksum,
        },
    )

    storage_key = (
        f"materials/"
        f"{course_id}/"
        f"{uuid4()}/source"
    )

    try:
        await object_storage.put_bytes(
            key=storage_key,
            data=data,
            content_type=mime_type,
        )

        asset = Asset(
            owner_id=owner_id,
            storage_key=storage_key,
            original_filename=filename,
            mime_type=mime_type,
            size_bytes=len(data),
            checksum_sha256=checksum,
        )

        material = (
            await repository.create_material(
                db,
                owner_id=owner_id,
                course_id=course_id,
                asset=asset,
                source_type=(
                    source_type_for(
                        filename
                    )
                ),
                original_filename=(
                    filename
                ),
            )
        )

        await trace_recorder.event(
            trace_id=trace_id,
            seq=1,
            event_type=(
                "material.asset.stored"
            ),
            node="object_storage",
            payload_json={
                "material_id":
                    str(material.id),
                "asset_id":
                    str(asset.id),
                "storage_key":
                    storage_key,
            },
        )

        await trace_recorder.success(
            trace_id=trace_id,
            output_json={
                "material_id":
                    str(material.id),
                "status":
                    material.status,
            },
        )

        return material

    except Exception as exc:
        await trace_recorder.failure(
            trace_id=trace_id,
            error=exc,
        )

        raise


@router.get(
    "/materials",
    response_model=list[MaterialRead],
)
async def list_materials(
    course_id: UUID,
    owner_id: UUID = Depends(
        current_user_id
    ),
    db: AsyncSession = Depends(get_db),
):
    course = (
        await repository.get_owned_course(
            db,
            course_id=course_id,
            owner_id=owner_id,
        )
    )

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    return await repository.list_materials(
        db,
        owner_id=owner_id,
        course_id=course_id,
    )


@router.get(
    "/materials/{material_id}",
    response_model=MaterialRead,
)
async def get_material(
    material_id: UUID,
    owner_id: UUID = Depends(
        current_user_id
    ),
    db: AsyncSession = Depends(get_db),
):
    row = await repository.get_material(
        db,
        material_id=material_id,
        owner_id=owner_id,
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Material not found",
        )

    material, _ = row

    return material


@router.post(
    "/materials/{material_id}/process",
    response_model=KnowledgeJobRead,
    status_code=202,
)
async def process_material(
    material_id: UUID,
    owner_id: UUID = Depends(
        current_user_id
    ),
    db: AsyncSession = Depends(get_db),
):
    row = await repository.get_material(
        db,
        material_id=material_id,
        owner_id=owner_id,
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Material not found",
        )

    active = (
        await job_repository
        .get_active_for_material(
            db,
            material_id=material_id,
            owner_id=owner_id,
        )
    )

    if active is not None:
        return active

    try:
        job = await job_repository.create(
            db,
            material_id=material_id,
            owner_id=owner_id,
            max_attempts=(
                settings
                .knowledge_job_max_tries
            ),
        )

    except IntegrityError:
        await db.rollback()

        active = (
            await job_repository
            .get_active_for_material(
                db,
                material_id=material_id,
                owner_id=owner_id,
            )
        )

        if active is not None:
            return active

        raise

    try:
        await enqueue_material_process(
            job_id=job.id,
            material_id=material_id,
            owner_id=owner_id,
        )

    except Exception as exc:
        await job_repository.mark_failed(
            db,
            job_id=job.id,
            attempt=0,
            error=exc,
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Unable to enqueue "
                "material processing job"
            ),
        ) from exc

    await db.refresh(job)

    return job


@router.get(
    "/knowledge/jobs/{job_id}",
    response_model=KnowledgeJobRead,
)
async def get_knowledge_job(
    job_id: UUID,
    owner_id: UUID = Depends(
        current_user_id
    ),
    db: AsyncSession = Depends(get_db),
):
    job = await job_repository.get_owned(
        db,
        job_id=job_id,
        owner_id=owner_id,
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Knowledge job not found",
        )

    return job


@router.get(
    "/materials/{material_id}/chunks",
    response_model=list[ChunkRead],
)
async def list_chunks(
    material_id: UUID,
    owner_id: UUID = Depends(
        current_user_id
    ),
    db: AsyncSession = Depends(get_db),
):
    return await repository.list_chunks(
        db,
        material_id=material_id,
        owner_id=owner_id,
    )
