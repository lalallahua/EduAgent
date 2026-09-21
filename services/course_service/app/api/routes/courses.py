from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from services.course_service.app.db.session import get_db
from services.course_service.app.schemas.course import (
    CourseCreate,
    CourseSummary,
)
from services.course_service.app.services.course_application import (
    CourseApplicationService,
)


router = APIRouter()

service = CourseApplicationService()


def current_user_id(
    x_user_id: UUID = Header(alias="X-User-Id"),
) -> UUID:
    return x_user_id


@router.post(
    "",
    response_model=CourseSummary,
    status_code=201,
)
async def create_course(
    payload: CourseCreate,
    owner_id: UUID = Depends(current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await service.create_course(
        db,
        owner_id=owner_id,
        payload=payload,
    )


@router.get(
    "",
    response_model=list[CourseSummary],
)
async def list_courses(
    owner_id: UUID = Depends(current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_courses(
        db,
        owner_id=owner_id,
    )
