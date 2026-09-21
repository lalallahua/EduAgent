from fastapi import FastAPI

from services.course_service.app.api.routes.content import (
    router as content_router,
)
from services.course_service.app.api.routes.courses import (
    router as courses_router,
)


app = FastAPI(
    title="EduAgent Course Service",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "course-service",
    }


app.include_router(
    courses_router,
    prefix="/courses",
    tags=["courses"],
)

app.include_router(
    content_router,
    tags=["course-content"],
)
