from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.course_service.app.models.course import (
    Chapter,
    Course,
    CourseVersion,
    Scene,
    ScenePayload,
)


class CourseRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        owner_id: UUID,
        title: str,
        description: str | None,
    ) -> tuple[Course, CourseVersion]:

        course = Course(
            owner_id=owner_id,
            title=title,
            description=description,
        )

        db.add(course)
        await db.flush()

        version = CourseVersion(
            course_id=course.id,
            version_no=1,
            state="draft",
            dsl_version="0.1",
        )

        db.add(version)
        await db.flush()

        course.current_version_id = version.id

        await db.commit()
        await db.refresh(course)
        await db.refresh(version)

        return course, version

    async def list_by_owner(
        self,
        db: AsyncSession,
        *,
        owner_id: UUID,
    ) -> list[tuple[Course, CourseVersion | None]]:

        stmt = (
            select(Course, CourseVersion)
            .outerjoin(
                CourseVersion,
                Course.current_version_id == CourseVersion.id,
            )
            .where(Course.owner_id == owner_id)
            .order_by(Course.created_at.desc())
        )

        result = await db.execute(stmt)

        return list(result.all())
    
    async def get_version_for_owner(
        self,
        db,
        *,
        course_id,
        version_id,
        owner_id,
    ):
        stmt = (
            select(CourseVersion)
            .join(
                Course,
                CourseVersion.course_id == Course.id,
            )
            .where(
                Course.id == course_id,
                Course.owner_id == owner_id,
                CourseVersion.id == version_id,
            )
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()


    async def create_chapter(
        self,
        db,
        *,
        version_id,
        title,
        order_no,
    ):
        chapter = Chapter(
            version_id=version_id,
            title=title,
            order_no=order_no,
        )

        db.add(chapter)

        await db.commit()
        await db.refresh(chapter)

        return chapter


    async def list_chapters(
        self,
        db,
        *,
        version_id,
    ):
        stmt = (
            select(Chapter)
            .where(
                Chapter.version_id == version_id
            )
            .order_by(Chapter.order_no)
        )

        result = await db.execute(stmt)

        return list(result.scalars().all())


    async def get_chapter_for_owner(
        self,
        db,
        *,
        chapter_id,
        owner_id,
    ):
        stmt = (
            select(Chapter)
            .join(
                CourseVersion,
                Chapter.version_id == CourseVersion.id,
            )
            .join(
                Course,
                CourseVersion.course_id == Course.id,
            )
            .where(
                Chapter.id == chapter_id,
                Course.owner_id == owner_id,
            )
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()


    async def create_scene(
        self,
        db,
        *,
        chapter,
        scene_type,
        title,
        order_no,
        payload,
    ):
        scene = Scene(
            version_id=chapter.version_id,
            chapter_id=chapter.id,
            scene_type=scene_type,
            title=title,
            order_no=order_no,
            revision=1,
        )

        db.add(scene)
        await db.flush()

        scene_payload = ScenePayload(
            scene_id=scene.id,
            schema_version="0.1",
            payload_json=payload,
        )

        db.add(scene_payload)

        await db.commit()
        await db.refresh(scene)

        return scene, scene_payload


    async def list_scenes(
        self,
        db,
        *,
        chapter_id,
    ):
        stmt = (
            select(Scene, ScenePayload)
            .join(
                ScenePayload,
                ScenePayload.scene_id == Scene.id,
            )
            .where(
                Scene.chapter_id == chapter_id
            )
            .order_by(Scene.order_no)
        )

        result = await db.execute(stmt)

        return list(result.all())


    async def get_scene_for_owner(
        self,
        db,
        *,
        scene_id,
        owner_id,
    ):
        stmt = (
            select(Scene, ScenePayload)
            .join(
                ScenePayload,
                ScenePayload.scene_id == Scene.id,
            )
            .join(
                CourseVersion,
                Scene.version_id == CourseVersion.id,
            )
            .join(
                Course,
                CourseVersion.course_id == Course.id,
            )
            .where(
                Scene.id == scene_id,
                Course.owner_id == owner_id,
            )
        )

        result = await db.execute(stmt)

        return result.one_or_none()
