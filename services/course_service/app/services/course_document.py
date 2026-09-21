from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eduagent_course_dsl import (
    ChapterDocument,
    CourseDocument,
    CourseMetadata,
    Curriculum,
    DiscussionScene,
    InteractiveScene,
    PBLScene,
    QuizScene,
    SlideScene,
)

from services.course_service.app.models.course import (
    Chapter,
    Course,
    CourseVersion,
    Scene,
    ScenePayload,
)


SCENE_MODEL_MAP = {
    "slide": SlideScene,
    "quiz": QuizScene,
    "interactive": InteractiveScene,
    "pbl": PBLScene,
    "discussion": DiscussionScene,
}


async def assemble_course_document(
    db: AsyncSession,
    *,
    course_id: UUID,
    version_id: UUID,
    owner_id: UUID,
) -> CourseDocument:
    stmt = (
        select(Course, CourseVersion)
        .join(
            CourseVersion,
            CourseVersion.course_id == Course.id,
        )
        .where(
            Course.id == course_id,
            Course.owner_id == owner_id,
            CourseVersion.id == version_id,
        )
    )

    result = await db.execute(stmt)
    row = result.one_or_none()

    if row is None:
        raise LookupError(
            "Course version not found"
        )

    course, version = row

    chapter_result = await db.execute(
        select(Chapter)
        .where(
            Chapter.version_id == version_id
        )
        .order_by(Chapter.order_no)
    )

    chapters = list(
        chapter_result.scalars().all()
    )

    scene_result = await db.execute(
        select(Scene, ScenePayload)
        .join(
            ScenePayload,
            ScenePayload.scene_id == Scene.id,
        )
        .where(
            Scene.version_id == version_id
        )
        .order_by(
            Scene.chapter_id,
            Scene.order_no,
        )
    )

    scenes = []

    for scene, payload in scene_result.all():
        model = SCENE_MODEL_MAP[
            scene.scene_type
        ]

        scenes.append(
            model(
                id=scene.id,
                chapter_id=scene.chapter_id,
                order_no=scene.order_no,
                title=scene.title,
                type=scene.scene_type,
                payload=payload.payload_json,
            )
        )

    return CourseDocument(
        dsl_version=version.dsl_version,
        course_metadata=CourseMetadata(
            course_id=course.id,
            version_id=version.id,
            title=course.title,
            description=course.description,
            version_no=version.version_no,
            state=version.state,
        ),
        curriculum=Curriculum(
            chapters=[
                ChapterDocument(
                    id=chapter.id,
                    title=chapter.title,
                    order_no=chapter.order_no,
                )
                for chapter in chapters
            ],
        ),
        scenes=scenes,
        agent_roster=[],
        evidence_manifest=[],
    )
