import uuid

from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from services.course_service.app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        nullable=False,
    )

    display_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="active",
        nullable=False,
    )


class Course(Base, TimestampMixin):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="active",
        nullable=False,
    )

    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "course_versions.id",
            name="fk_courses_current_version_id",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
    )


class CourseVersion(Base, TimestampMixin):
    __tablename__ = "course_versions"

    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "version_no",
            name="uq_course_versions_course_version",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_versions.id", ondelete="SET NULL"),
        nullable=True,
    )

    state: Mapped[str] = mapped_column(
        String(32),
        default="draft",
        nullable=False,
    )

    dsl_version: Mapped[str] = mapped_column(
        String(16),
        default="0.1",
        nullable=False,
    )


class Chapter(Base, TimestampMixin):
    __tablename__ = "chapters"

    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "order_no",
            name="uq_chapters_version_order",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    order_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )


class Scene(Base, TimestampMixin):
    __tablename__ = "scenes"

    __table_args__ = (
        UniqueConstraint(
            "chapter_id",
            "order_no",
            name="uq_scenes_chapter_order",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    scene_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    order_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    revision: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )


class ScenePayload(Base, TimestampMixin):
    __tablename__ = "scene_payloads"

    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    schema_version: Mapped[str] = mapped_column(
        String(16),
        default="0.1",
        nullable=False,
    )

    payload_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )


class SceneRevision(Base, TimestampMixin):
    __tablename__ = "scene_revisions"

    __table_args__ = (
        UniqueConstraint(
            "scene_id",
            "revision",
            name="uq_scene_revision",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    revision: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    patch_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    actor_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
