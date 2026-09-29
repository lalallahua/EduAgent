from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class KnowledgeJobRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    material_id: UUID
    owner_id: UUID

    job_type: str

    status: str
    stage: str
    progress: int

    attempt: int
    max_attempts: int

    trace_id: UUID | None

    error_json: dict | None
    result_json: dict | None

    created_at: datetime
    updated_at: datetime

    started_at: datetime | None
    finished_at: datetime | None
