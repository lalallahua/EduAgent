from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession

from services.course_service.app.db.session import get_db
from services.course_service.app.repositories.course_repository import (
    CourseRepository,
)
from services.course_service.app.schemas.chapter import (
    ChapterCreate,
    ChapterRead,
)
from services.course_service.app.schemas.scene import (
    SceneCreate,
    SceneRead,
)
from services.course_service.app.tracing.recorder import (
    trace_recorder,
)

from services.course_service.app.services.course_document import (
    assemble_course_document,
)

router = APIRouter()
repository = CourseRepository()


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


@router.post(
    "/courses/{course_id}/versions/{version_id}/chapters",
    response_model=ChapterRead,
    status_code=201,
)
async def create_chapter(
    course_id: UUID,
    version_id: UUID,
    payload: ChapterCreate,
    owner_id: UUID = Depends(current_user_id),
    trace_id: UUID | None = Depends(
        incoming_trace_id
    ),
    db: AsyncSession = Depends(get_db),
):
    version = await repository.get_version_for_owner(
        db,
        course_id=course_id,
        version_id=version_id,
        owner_id=owner_id,
    )

    if version is None:
        raise HTTPException(
            status_code=404,
            detail="Course version not found",
        )

    trace_id = await trace_recorder.start(
        trace_id=trace_id,
        trace_type="course_mutation",
        source_service="course-service",
        operation="chapter.create",
        actor_type="teacher",
        actor_id=owner_id,
        course_id=course_id,
        course_version_id=version_id,
        input_json=payload.model_dump(
            mode="json"
        ),
    )

    try:
        chapter = await repository.create_chapter(
            db,
            version_id=version_id,
            title=payload.title,
            order_no=payload.order_no,
        )

        await trace_recorder.success(
            trace_id=trace_id,
            output_json={
                "chapter_id": str(chapter.id)
            },
        )

        return chapter

    except Exception as exc:
        await trace_recorder.failure(
            trace_id=trace_id,
            error=exc,
        )
        raise


@router.get(
    "/courses/{course_id}/versions/{version_id}/chapters",
    response_model=list[ChapterRead],
)
async def list_chapters(
    course_id: UUID,
    version_id: UUID,
    owner_id: UUID = Depends(current_user_id),
    db: AsyncSession = Depends(get_db),
):
    version = await repository.get_version_for_owner(
        db,
        course_id=course_id,
        version_id=version_id,
        owner_id=owner_id,
    )

    if version is None:
        raise HTTPException(
            status_code=404,
            detail="Course version not found",
        )

    return await repository.list_chapters(
        db,
        version_id=version_id,
    )


@router.post(
    "/chapters/{chapter_id}/scenes",
    response_model=SceneRead,
    status_code=201,
)
async def create_scene(
    chapter_id: UUID,
    payload: SceneCreate,
    owner_id: UUID = Depends(current_user_id),
    trace_id: UUID | None = Depends(
        incoming_trace_id
    ),
    db: AsyncSession = Depends(get_db),
):
    chapter = await repository.get_chapter_for_owner(
        db,
        chapter_id=chapter_id,
        owner_id=owner_id,
    )

    if chapter is None:
        raise HTTPException(
            status_code=404,
            detail="Chapter not found",
        )

    trace_id = await trace_recorder.start(
        trace_id=trace_id,
        trace_type="course_mutation",
        source_service="course-service",
        operation="scene.create",
        actor_type="teacher",
        actor_id=owner_id,
        course_version_id=chapter.version_id,
        chapter_id=chapter.id,
        input_json=payload.model_dump(
            mode="json"
        ),
    )

    try:
        scene, scene_payload = (
            await repository.create_scene(
                db,
                chapter=chapter,
                scene_type=payload.type,
                title=payload.title,
                order_no=payload.order_no,
                payload=payload.payload.model_dump(
                    mode="json"
                ),
            )
        )

        await trace_recorder.success(
            trace_id=trace_id,
            output_json={
                "scene_id": str(scene.id)
            },
        )

        return SceneRead(
            id=scene.id,
            version_id=scene.version_id,
            chapter_id=scene.chapter_id,
            type=scene.scene_type,
            order_no=scene.order_no,
            title=scene.title,
            revision=scene.revision,
            payload=scene_payload.payload_json,
        )

    except Exception as exc:
        await trace_recorder.failure(
            trace_id=trace_id,
            error=exc,
        )
        raise


@router.get(
    "/chapters/{chapter_id}/scenes",
    response_model=list[SceneRead],
)
async def list_scenes(
    chapter_id: UUID,
    owner_id: UUID = Depends(current_user_id),
    db: AsyncSession = Depends(get_db),
):
    chapter = await repository.get_chapter_for_owner(
        db,
        chapter_id=chapter_id,
        owner_id=owner_id,
    )

    if chapter is None:
        raise HTTPException(
            status_code=404,
            detail="Chapter not found",
        )

    rows = await repository.list_scenes(
        db,
        chapter_id=chapter_id,
    )

    return [
        SceneRead(
            id=scene.id,
            version_id=scene.version_id,
            chapter_id=scene.chapter_id,
            type=scene.scene_type,
            order_no=scene.order_no,
            title=scene.title,
            revision=scene.revision,
            payload=payload.payload_json,
        )
        for scene, payload in rows
    ]


@router.get(
    "/scenes/{scene_id}",
    response_model=SceneRead,
)
async def get_scene(
    scene_id: UUID,
    owner_id: UUID = Depends(current_user_id),
    db: AsyncSession = Depends(get_db),
):
    row = await repository.get_scene_for_owner(
        db,
        scene_id=scene_id,
        owner_id=owner_id,
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Scene not found",
        )

    scene, payload = row

    return SceneRead(
        id=scene.id,
        version_id=scene.version_id,
        chapter_id=scene.chapter_id,
        type=scene.scene_type,
        order_no=scene.order_no,
        title=scene.title,
        revision=scene.revision,
        payload=payload.payload_json,
    )

@router.get(
    "/courses/{course_id}/versions/{version_id}/document",
)
async def get_course_document(
    course_id: UUID,
    version_id: UUID,
    owner_id: UUID = Depends(current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        document = await assemble_course_document(
            db,
            course_id=course_id,
            version_id=version_id,
            owner_id=owner_id,
        )

    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Course version not found",
        )

    return document.model_dump(
        mode="json"
    )
