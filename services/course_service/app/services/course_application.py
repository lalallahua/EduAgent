from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from services.course_service.app.repositories.course_repository import (
    CourseRepository,
)
from services.course_service.app.schemas.course import (
    CourseCreate,
    CourseSummary,
)


class CourseApplicationService:
    def __init__(self) -> None:
        self.repository = CourseRepository()

    async def create_course(
        self,
        db: AsyncSession,
        *,
        owner_id: UUID,
        payload: CourseCreate,
    ) -> CourseSummary:

        course, version = await self.repository.create(
            db,
            owner_id=owner_id,
            title=payload.title,
            description=payload.description,
        )

        return CourseSummary(
            id=course.id,
            title=course.title,
            description=course.description,
            status=course.status,
            current_version_id=course.current_version_id,
            version_no=version.version_no,
            version_state=version.state,
            created_at=course.created_at,
            updated_at=course.updated_at,
        )

    async def list_courses(
        self,
        db: AsyncSession,
        *,
        owner_id: UUID,
    ) -> list[CourseSummary]:

        rows = await self.repository.list_by_owner(
            db,
            owner_id=owner_id,
        )

        return [
            CourseSummary(
                id=course.id,
                title=course.title,
                description=course.description,
                status=course.status,
                current_version_id=course.current_version_id,
                version_no=version.version_no if version else None,
                version_state=version.state if version else None,
                created_at=course.created_at,
                updated_at=course.updated_at,
            )
            for course, version in rows
        ]
