from fastapi import FastAPI

app = FastAPI(
    title="EduAgent API",
    version="0.1.0",
    description="Backend API for EduAgent adaptive AI classroom platform",
)


@app.get("/")
async def root():
    return {
        "name": "EduAgent",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "api-gateway",
    }
