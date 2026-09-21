import os
from uuid import UUID

import httpx
from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


COURSE_SERVICE_URL = os.getenv(
    "COURSE_SERVICE_URL",
    "http://127.0.0.1:8001",
)


app = FastAPI(
    title="EduAgent API",
    version="0.1.0",
    description="Backend API Gateway for EduAgent",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.post("/courses")
async def create_course(
    request: Request,
    x_user_id: UUID = Header(alias="X-User-Id"),
):
    payload = await request.json()

    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:
        try:
            response = await client.post(
                f"{COURSE_SERVICE_URL}/courses",
                json=payload,
                headers={
                    "X-User-Id": str(x_user_id),
                },
            )
        except httpx.RequestError as exc:
            return JSONResponse(
                status_code=502,
                content={
                    "detail": "Course service unavailable",
                    "error": str(exc),
                },
            )

    return JSONResponse(
        status_code=response.status_code,
        content=response.json(),
    )


@app.get("/courses")
async def list_courses(
    x_user_id: UUID = Header(alias="X-User-Id"),
):
    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:
        try:
            response = await client.get(
                f"{COURSE_SERVICE_URL}/courses",
                headers={
                    "X-User-Id": str(x_user_id),
                },
            )
        except httpx.RequestError as exc:
            return JSONResponse(
                status_code=502,
                content={
                    "detail": "Course service unavailable",
                    "error": str(exc),
                },
            )

    return JSONResponse(
        status_code=response.status_code,
        content=response.json(),
    )
