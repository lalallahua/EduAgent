from fastapi import FastAPI

# Register shared Course tables for FK metadata.
import services.course_service.app.models  # noqa: F401
import services.knowledge_service.app.models  # noqa: F401

from services.knowledge_service.app.api.routes.materials import (
    router as materials_router,
)
from services.knowledge_service.app.api.routes.search import (
    router as search_router,
)


app = FastAPI(
    title="EduAgent Knowledge Service",
    version="0.2.0",
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "knowledge-service",
    }


app.include_router(
    materials_router,
    tags=["materials"],
)

app.include_router(
    search_router,
    tags=["knowledge"],
)
