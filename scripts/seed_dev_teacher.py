import asyncio
from uuid import UUID

from services.course_service.app.db.session import AsyncSessionLocal
from services.course_service.app.models.course import User


DEV_TEACHER_ID = UUID(
    "00000000-0000-0000-0000-000000000001"
)

DEV_TEACHER_EMAIL = "dev-teacher@eduagent.local"
DEV_TEACHER_NAME = "EduAgent Dev Teacher"


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        teacher = await session.get(
            User,
            DEV_TEACHER_ID,
        )

        if teacher is None:
            teacher = User(
                id=DEV_TEACHER_ID,
                email=DEV_TEACHER_EMAIL,
                display_name=DEV_TEACHER_NAME,
                status="active",
            )

            session.add(teacher)

            print("Creating development teacher...")
        else:
            teacher.email = DEV_TEACHER_EMAIL
            teacher.display_name = DEV_TEACHER_NAME
            teacher.status = "active"

            print("Development teacher already exists; refreshing values...")

        await session.commit()

        print("Development teacher ready:")
        print(f"  id: {DEV_TEACHER_ID}")
        print(f"  email: {DEV_TEACHER_EMAIL}")


if __name__ == "__main__":
    asyncio.run(seed())
