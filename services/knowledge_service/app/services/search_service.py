from uuid import UUID

from sqlalchemy import select

from services.knowledge_service.app.db.session import (
    AsyncSessionLocal,
)
from services.knowledge_service.app.models.knowledge import (
    EvidenceRef,
    Material,
    MaterialChunk,
    MaterialEmbedding,
)
from services.knowledge_service.app.services.embeddings import (
    get_embedding_provider,
)


async def search_course(
    *,
    course_id: UUID,
    owner_id: UUID,
    query: str,
    top_k: int,
) -> list[dict]:
    provider = get_embedding_provider()

    vectors = await provider.embed(
        [query]
    )

    query_vector = vectors[0]

    distance = (
        MaterialEmbedding.embedding
        .cosine_distance(
            query_vector
        )
        .label("distance")
    )

    stmt = (
        select(
            MaterialChunk,
            EvidenceRef,
            distance,
        )
        .join(
            Material,
            MaterialChunk.material_id
            == Material.id,
        )
        .join(
            MaterialEmbedding,
            MaterialEmbedding.chunk_id
            == MaterialChunk.id,
        )
        .join(
            EvidenceRef,
            EvidenceRef.chunk_id
            == MaterialChunk.id,
        )
        .where(
            Material.course_id
            == course_id,
            Material.owner_id
            == owner_id,
            Material.status
            == "ready",
            MaterialEmbedding.provider
            == provider.name,
            MaterialEmbedding.model
            == provider.model,
        )
        .order_by(distance)
        .limit(top_k)
    )

    async with AsyncSessionLocal() as db:
        result = await db.execute(stmt)

        rows = result.all()

    output = []

    for chunk, evidence, value in rows:
        distance_value = float(
            value
        )

        output.append(
            {
                "chunk_id":
                    chunk.id,
                "material_id":
                    chunk.material_id,
                "evidence_id":
                    evidence.id,
                "text":
                    chunk.text,
                "page_no":
                    chunk.page_no,
                "section":
                    chunk.section,
                "distance":
                    distance_value,
                "similarity":
                    1.0
                    - distance_value,
                "locator":
                    evidence.locator,
            }
        )

    return output
