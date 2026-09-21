from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


DSL_VERSION = "0.1"


class CourseMetadata(BaseModel):
    course_id: UUID
    version_id: UUID

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = None

    version_no: int = Field(
        ge=1,
    )

    state: str


class ChapterDocument(BaseModel):
    id: UUID

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    order_no: int = Field(
        ge=1,
    )


class Curriculum(BaseModel):
    chapters: list[ChapterDocument] = Field(
        default_factory=list
    )

    concepts: list[dict] = Field(
        default_factory=list
    )


class SlidePayload(BaseModel):
    elements: list[dict] = Field(
        default_factory=list
    )

    narration: str | None = None

    actions: list[dict] = Field(
        default_factory=list
    )


class QuizQuestion(BaseModel):
    id: str

    type: str

    stem: str = Field(
        min_length=1
    )

    options: list[str] = Field(
        default_factory=list
    )

    answer: str | list[str] | None = None

    rubric: dict | None = None


class QuizPayload(BaseModel):
    questions: list[QuizQuestion] = Field(
        min_length=1
    )

    rubric: dict | None = None

    feedback_policy: dict | None = None


class InteractivePayload(BaseModel):
    html: str = Field(
        min_length=1
    )

    initial_state: dict = Field(
        default_factory=dict
    )

    state_contract: dict = Field(
        default_factory=dict
    )


class PBLPayload(BaseModel):
    goal: str = Field(
        min_length=1
    )

    roles: list[dict] = Field(
        default_factory=list
    )

    milestones: list[dict] = Field(
        default_factory=list
    )

    tasks: list[dict] = Field(
        default_factory=list
    )

    rubric: dict | None = None


class DiscussionPayload(BaseModel):
    topic: str = Field(
        min_length=1
    )

    roles: list[dict] = Field(
        default_factory=list
    )

    turn_policy: dict = Field(
        default_factory=dict
    )


class BaseScene(BaseModel):
    id: UUID
    chapter_id: UUID

    order_no: int = Field(
        ge=1
    )

    title: str = Field(
        min_length=1,
        max_length=200,
    )


class SlideScene(BaseScene):
    type: Literal["slide"]

    payload: SlidePayload


class QuizScene(BaseScene):
    type: Literal["quiz"]

    payload: QuizPayload


class InteractiveScene(BaseScene):
    type: Literal["interactive"]

    payload: InteractivePayload


class PBLScene(BaseScene):
    type: Literal["pbl"]

    payload: PBLPayload


class DiscussionScene(BaseScene):
    type: Literal["discussion"]

    payload: DiscussionPayload


Scene = Annotated[
    SlideScene
    | QuizScene
    | InteractiveScene
    | PBLScene
    | DiscussionScene,
    Field(discriminator="type"),
]


class CourseDocument(BaseModel):
    dsl_version: Literal["0.1"] = DSL_VERSION

    course_metadata: CourseMetadata

    curriculum: Curriculum

    scenes: list[Scene] = Field(
        default_factory=list
    )

    agent_roster: list[dict] = Field(
        default_factory=list
    )

    evidence_manifest: list[dict] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def validate_domain_invariants(self):
        chapter_ids = {
            chapter.id
            for chapter in self.curriculum.chapters
        }

        chapter_orders = [
            chapter.order_no
            for chapter in self.curriculum.chapters
        ]

        if len(chapter_orders) != len(
            set(chapter_orders)
        ):
            raise ValueError(
                "chapter.order_no must be unique"
            )

        scene_orders: set[tuple[UUID, int]] = set()

        for scene in self.scenes:
            if scene.chapter_id not in chapter_ids:
                raise ValueError(
                    "scene.chapter_id does not exist"
                )

            key = (
                scene.chapter_id,
                scene.order_no,
            )

            if key in scene_orders:
                raise ValueError(
                    "scene.order_no must be unique "
                    "inside each chapter"
                )

            scene_orders.add(key)

        return self
