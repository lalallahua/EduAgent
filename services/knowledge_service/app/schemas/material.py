from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MaterialRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    owner_id: UUID
    course_id: UUID
    asset_id: UUID
    source_type: str
    original_filename: str
    status: str
    created_at: datetime
    updated_at: datetime


class ChunkRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    material_id: UUID
    chunk_index: int
    page_no: int | None
    section: str | None
    text: str
    token_count: int


class SearchRequest(BaseModel):
    course_id: UUID

    query: str = Field(
        min_length=1,
        max_length=4000,
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )


class SearchResult(BaseModel):
    chunk_id: UUID
    material_id: UUID
    evidence_id: UUID

    text: str

    page_no: int | None
    section: str | None

    distance: float
    similarity: float

    locator: dict
