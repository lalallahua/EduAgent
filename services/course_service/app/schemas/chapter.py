from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChapterCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )

    order_no: int = Field(
        ge=1
    )


class ChapterRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    version_id: UUID
    title: str
    order_no: int
    created_at: datetime
    updated_at: datetime
