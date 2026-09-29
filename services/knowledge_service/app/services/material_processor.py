import hashlib
import json
from pathlib import Path
from uuid import UUID, uuid4

from services.course_service.app.tracing.recorder import (
    trace_recorder,
)
from services.knowledge_service.app.core.config import (
    settings,
)
from services.knowledge_service.app.db.session import (
    AsyncSessionLocal,
)
from services.knowledge_service.app.models.knowledge import (
    EvidenceRef,
    MaterialChunk,
    MaterialEmbedding,
    MaterialExtraction,
)
from services.knowledge_service.app.repositories.knowledge_repository import (
    KnowledgeRepository,
)
from services.knowledge_service.app.services.chunker import (
    chunk_units,
)
from services.knowledge_service.app.services.embeddings import (
    get_embedding_provider,
)
from services.knowledge_service.app.services.parsers import (
    parse_material,
)
from services.knowledge_service.app.services.storage import (
    object_storage,
)


repository = KnowledgeRepository()


class MaterialProcessor:
    async def process(
        self,
        *,
        material_id: UUID,
        owner_id: UUID,
        trace_id: UUID | None = None,
    ) -> dict:
        trace_id = await trace_recorder.start(
            trace_id=trace_id,
            trace_type="knowledge_pipeline",
            source_service="knowledge-service",
            operation="material.process",
            actor_type="teacher",
            actor_id=owner_id,
            input_json={
                "material_id":
                    str(material_id)
            },
        )

        await trace_recorder.event(
            trace_id=trace_id,
            seq=1,
            event_type="material.process.started",
            node="material_processor",
            payload_json={
                "material_id":
                    str(material_id)
            },
        )

        try:
            async with (
                AsyncSessionLocal()
                as db
            ):
                row = await repository.get_material(
                    db,
                    material_id=material_id,
                    owner_id=owner_id,
                )

                if row is None:
                    raise LookupError(
                        "Material not found"
                    )

                material, asset = row

                material.status = (
                    "processing"
                )

                await db.commit()

                data = (
                    await object_storage.get_bytes(
                        key=asset.storage_key
                    )
                )

                parser_name, units = (
                    parse_material(
                        filename=(
                            material.original_filename
                        ),
                        data=data,
                    )
                )

                if not units:
                    raise ValueError(
                        "Parser produced "
                        "no text content"
                    )

                await trace_recorder.event(
                    trace_id=trace_id,
                    seq=2,
                    event_type="material.parsed",
                    node="parser",
                    payload_json={
                        "parser": parser_name,
                        "unit_count":
                            len(units),
                    },
                )

                extraction_key = (
                    "extractions/"
                    f"{material.id}/"
                    f"{uuid4()}.json"
                )

                extraction_payload = {
                    "parser": parser_name,
                    "units": [
                        unit.to_dict()
                        for unit in units
                    ],
                }

                await object_storage.put_bytes(
                    key=extraction_key,
                    data=json.dumps(
                        extraction_payload,
                        ensure_ascii=False,
                    ).encode("utf-8"),
                    content_type=(
                        "application/json"
                    ),
                )

                chunks = chunk_units(
                    units,
                    max_chars=(
                        settings.chunk_max_chars
                    ),
                    overlap_chars=(
                        settings
                        .chunk_overlap_chars
                    ),
                )

                if not chunks:
                    raise ValueError(
                        "Chunker produced "
                        "no chunks"
                    )

                await repository.clear_derivatives(
                    db,
                    material_id=material.id,
                )

                extraction = (
                    MaterialExtraction(
                        material_id=material.id,
                        parser=parser_name,
                        parser_version="1",
                        text_ref=extraction_key,
                        media_manifest={
                            "unit_count":
                                len(units),
                            "chunk_count":
                                len(chunks),
                        },
                    )
                )

                db.add(extraction)

                await db.flush()

                chunk_models = []

                for chunk in chunks:
                    model = MaterialChunk(
                        material_id=(
                            material.id
                        ),
                        extraction_id=(
                            extraction.id
                        ),
                        chunk_index=(
                            chunk.chunk_index
                        ),
                        page_no=chunk.page_no,
                        section=chunk.section,
                        text=chunk.text,
                        token_count=(
                            chunk.token_count
                        ),
                        checksum_sha256=(
                            chunk
                            .checksum_sha256
                        ),
                    )

                    db.add(model)
                    chunk_models.append(model)

                await db.flush()

                await trace_recorder.event(
                    trace_id=trace_id,
                    seq=3,
                    event_type="material.chunked",
                    node="chunker",
                    payload_json={
                        "chunk_count":
                            len(
                                chunk_models
                            )
                    },
                )

                provider = (
                    get_embedding_provider()
                )

                vectors = await provider.embed(
                    [
                        chunk.text
                        for chunk
                        in chunk_models
                    ]
                )

                if (
                    len(vectors)
                    != len(chunk_models)
                ):
                    raise ValueError(
                        "Embedding provider "
                        "returned wrong count"
                    )

                for chunk, vector in zip(
                    chunk_models,
                    vectors,
                    strict=True,
                ):
                    db.add(
                        MaterialEmbedding(
                            chunk_id=chunk.id,
                            provider=(
                                provider.name
                            ),
                            model=(
                                provider.model
                            ),
                            dimension=(
                                len(vector)
                            ),
                            embedding=vector,
                        )
                    )

                    db.add(
                        EvidenceRef(
                            source_type=(
                                "material_chunk"
                            ),
                            material_id=(
                                material.id
                            ),
                            chunk_id=chunk.id,
                            locator={
                                "page":
                                    chunk.page_no,
                                "section":
                                    chunk.section,
                                "chunk_index":
                                    chunk.chunk_index,
                            },
                            quote_hash=(
                                hashlib.sha256(
                                    chunk.text.encode(
                                        "utf-8"
                                    )
                                ).hexdigest()
                            ),
                        )
                    )

                material.status = "ready"

                await db.commit()

                await trace_recorder.event(
                    trace_id=trace_id,
                    seq=4,
                    event_type="material.embedded",
                    node="embedding",
                    payload_json={
                        "provider":
                            provider.name,
                        "model":
                            provider.model,
                        "count":
                            len(vectors),
                        "dimension":
                            len(
                                vectors[0]
                            )
                            if vectors
                            else 0,
                    },
                )

                output = {
                    "material_id":
                        str(material.id),
                    "status": "ready",
                    "parser":
                        parser_name,
                    "chunks":
                        len(chunk_models),
                    "embedding_provider":
                        provider.name,
                    "embedding_model":
                        provider.model,
                }

                await trace_recorder.success(
                    trace_id=trace_id,
                    output_json=output,
                )

                return output

        except Exception as exc:
            async with (
                AsyncSessionLocal()
                as db
            ):
                row = (
                    await repository.get_material(
                        db,
                        material_id=(
                            material_id
                        ),
                        owner_id=owner_id,
                    )
                )

                if row is not None:
                    material, _ = row

                    material.status = "failed"

                    await db.commit()

            await trace_recorder.failure(
                trace_id=trace_id,
                error=exc,
            )

            raise


material_processor = MaterialProcessor()
