from uuid import UUID, uuid4

import httpx
from fastapi import (
    APIRouter,
    Header,
    Request,
    Response,
)


router = APIRouter()

KNOWLEDGE_SERVICE_URL = (
    "http://127.0.0.1:8002"
)


async def proxy(
    request: Request,
    *,
    x_user_id: UUID,
    x_trace_id: UUID | None,
) -> Response:
    trace_id = (
        x_trace_id
        or uuid4()
    )

    target = (
        KNOWLEDGE_SERVICE_URL
        + request.url.path
    )

    if request.url.query:
        target += (
            "?"
            + request.url.query
        )

    headers = {
        "X-User-Id":
            str(x_user_id),
        "X-Trace-Id":
            str(trace_id),
    }

    content_type = (
        request.headers.get(
            "content-type"
        )
    )

    if content_type:
        headers[
            "Content-Type"
        ] = content_type

    body = await request.body()

    async with httpx.AsyncClient(
        timeout=120.0
    ) as client:
        response = await client.request(
            request.method,
            target,
            headers=headers,
            content=body,
        )

    return Response(
        content=response.content,
        status_code=(
            response.status_code
        ),
        media_type=(
            response.headers.get(
                "content-type"
            )
        ),
        headers={
            "X-Trace-Id":
                str(trace_id)
        },
    )


@router.api_route(
    "/materials",
    methods=["GET", "POST"],
)
async def materials_root(
    request: Request,
    x_user_id: UUID = Header(
        alias="X-User-Id"
    ),
    x_trace_id: UUID | None = Header(
        default=None,
        alias="X-Trace-Id",
    ),
):
    return await proxy(
        request,
        x_user_id=x_user_id,
        x_trace_id=x_trace_id,
    )


@router.api_route(
    "/materials/{path:path}",
    methods=["GET", "POST"],
)
async def materials_proxy(
    request: Request,
    path: str,
    x_user_id: UUID = Header(
        alias="X-User-Id"
    ),
    x_trace_id: UUID | None = Header(
        default=None,
        alias="X-Trace-Id",
    ),
):
    return await proxy(
        request,
        x_user_id=x_user_id,
        x_trace_id=x_trace_id,
    )

@router.get(
    "/knowledge/jobs/{job_id}",
)
async def knowledge_job(
    request: Request,
    job_id: UUID,
    x_user_id: UUID = Header(
        alias="X-User-Id"
    ),
    x_trace_id: UUID | None = Header(
        default=None,
        alias="X-Trace-Id",
    ),
):
    return await proxy(
        request,
        x_user_id=x_user_id,
        x_trace_id=x_trace_id,
    )

@router.post(
    "/knowledge/search",
)
async def knowledge_search(
    request: Request,
    x_user_id: UUID = Header(
        alias="X-User-Id"
    ),
    x_trace_id: UUID | None = Header(
        default=None,
        alias="X-Trace-Id",
    ),
):
    return await proxy(
        request,
        x_user_id=x_user_id,
        x_trace_id=x_trace_id,
    )
