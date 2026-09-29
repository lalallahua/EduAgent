import uuid
from datetime import datetime

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text as sql_text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from services.course_service.app.db.base import (
    Base,
    TimestampMixin,
)


class Asset(Base, TimestampMixin):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    storage_key: Mapped[str] = mapped_column(
        String(1024),
        unique=True,
        nullable=False,
    )

    original_filename: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    checksum_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )


class Material(Base, TimestampMixin):
    __tablename__ = "materials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )

    source_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    original_filename: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="uploaded",
        nullable=False,
        index=True,
    )


class MaterialExtraction(Base, TimestampMixin):
    __tablename__ = "material_extractions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    parser: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    parser_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    text_ref: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )

    media_manifest: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )


class MaterialChunk(Base, TimestampMixin):
    __tablename__ = "material_chunks"

    __table_args__ = (
        UniqueConstraint(
            "material_id",
            "chunk_index",
            name="uq_material_chunk_index",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    extraction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "material_extractions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    page_no: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    section: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    checksum_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )


class MaterialEmbedding(Base, TimestampMixin):
    __tablename__ = "material_embeddings"

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "material_chunks.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    provider: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    model: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    dimension: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    embedding: Mapped[list[float]] = mapped_column(
        VECTOR(),
        nullable=False,
    )


class EvidenceRef(Base, TimestampMixin):
    __tablename__ = "evidence_refs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    source_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "material_chunks.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    locator: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    quote_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )


class KnowledgeJob(Base, TimestampMixin):
    __tablename__ = "knowledge_jobs"

    __table_args__ = (
        Index(
            "uq_knowledge_jobs_active_material",
            "material_id",
            unique=True,
            postgresql_where=sql_text(
                "status IN ('queued', 'processing')"
            ),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "materials.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    job_type: Mapped[str] = mapped_column(
        String(64),
        default="material_process",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="queued",
        nullable=False,
        index=True,
    )

    stage: Mapped[str] = mapped_column(
        String(64),
        default="queued",
        nullable=False,
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    attempt: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    max_attempts: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )

    trace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    error_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    result_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

