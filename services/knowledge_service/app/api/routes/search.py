from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
)

from services.course_service.app.tracing.recorder import (
    trace_recorder,
)
from services.knowledge_service.app.schemas.material import (
    SearchRequest,
    SearchResult,
)
from services.knowledge_service.app.services.search_service import (
    search_course,
)


router = APIRouter()


def current_user_id(
    x_user_id: UUID = Header(
        alias="X-User-Id"
    ),
) -> UUID:
    return x_user_id


def incoming_trace_id(
    x_trace_id: UUID | None = Header(
        default=None,
        alias="X-Trace-Id",
    ),
) -> UUID | None:
    return x_trace_id


@router.post(
    "/knowledge/search",
    response_model=list[SearchResult],
)
async def search(
    payload: SearchRequest,
    owner_id: UUID = Depends(
        current_user_id
    ),
    trace_id: UUID | None = Depends(
        incoming_trace_id
    ),
):
    trace_id = await trace_recorder.start(
        trace_id=trace_id,
        trace_type="knowledge_retrieval",
        source_service="knowledge-service",
        operation="knowledge.search",
        actor_type="teacher",
        actor_id=owner_id,
        course_id=payload.course_id,
        input_json={
            "query": payload.query,
            "top_k": payload.top_k,
        },
    )

    try:
        results = await search_course(
            course_id=payload.course_id,
            owner_id=owner_id,
            query=payload.query,
            top_k=payload.top_k,
        )

        await trace_recorder.event(
            trace_id=trace_id,
            seq=1,
            event_type="retrieval.result",
            node="pgvector",
            payload_json={
                "result_count":
                    len(results),
                "evidence_ids": [
                    str(
                        result[
                            "evidence_id"
                        ]
                    )
                    for result
                    in results
                ],
            },
        )

        await trace_recorder.success(
            trace_id=trace_id,
            output_json={
                "result_count":
                    len(results)
            },
        )

        return results

    except Exception as exc:
        await trace_recorder.failure(
            trace_id=trace_id,
            error=exc,
        )

        raise
