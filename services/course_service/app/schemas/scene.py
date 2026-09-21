from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from eduagent_course_dsl import (
    DiscussionPayload,
    InteractivePayload,
    PBLPayload,
    QuizPayload,
    SlidePayload,
)


class BaseSceneCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )

    order_no: int = Field(
        ge=1
    )


class SlideSceneCreate(BaseSceneCreate):
    type: Literal["slide"]
    payload: SlidePayload


class QuizSceneCreate(BaseSceneCreate):
    type: Literal["quiz"]
    payload: QuizPayload


class InteractiveSceneCreate(BaseSceneCreate):
    type: Literal["interactive"]
    payload: InteractivePayload


class PBLSceneCreate(BaseSceneCreate):
    type: Literal["pbl"]
    payload: PBLPayload


class DiscussionSceneCreate(BaseSceneCreate):
    type: Literal["discussion"]
    payload: DiscussionPayload


SceneCreate = Annotated[
    SlideSceneCreate
    | QuizSceneCreate
    | InteractiveSceneCreate
    | PBLSceneCreate
    | DiscussionSceneCreate,
    Field(discriminator="type"),
]


class SceneRead(BaseModel):
    id: UUID
    version_id: UUID
    chapter_id: UUID
    type: str
    order_no: int
    title: str
    revision: int
    payload: dict
