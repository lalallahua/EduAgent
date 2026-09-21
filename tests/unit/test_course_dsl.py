from uuid import uuid4

from eduagent_course_dsl import (
    ChapterDocument,
    CourseDocument,
    CourseMetadata,
    Curriculum,
    SlidePayload,
    SlideScene,
)


def test_valid_course_document():
    course_id = uuid4()
    version_id = uuid4()
    chapter_id = uuid4()

    document = CourseDocument(
        course_metadata=CourseMetadata(
            course_id=course_id,
            version_id=version_id,
            title="Computer Vision Fundamentals",
            version_no=1,
            state="draft",
        ),
        curriculum=Curriculum(
            chapters=[
                ChapterDocument(
                    id=chapter_id,
                    title="Introduction",
                    order_no=1,
                )
            ]
        ),
        scenes=[
            SlideScene(
                id=uuid4(),
                chapter_id=chapter_id,
                order_no=1,
                title="What is Computer Vision?",
                type="slide",
                payload=SlidePayload(
                    narration="Introduction"
                ),
            )
        ],
    )

    assert document.dsl_version == "0.1"


def test_invalid_scene_chapter():
    valid_chapter_id = uuid4()

    try:
        CourseDocument(
            course_metadata=CourseMetadata(
                course_id=uuid4(),
                version_id=uuid4(),
                title="Test",
                version_no=1,
                state="draft",
            ),
            curriculum=Curriculum(
                chapters=[
                    ChapterDocument(
                        id=valid_chapter_id,
                        title="Chapter",
                        order_no=1,
                    )
                ]
            ),
            scenes=[
                SlideScene(
                    id=uuid4(),
                    chapter_id=uuid4(),
                    order_no=1,
                    title="Invalid Scene",
                    type="slide",
                    payload=SlidePayload(),
                )
            ],
        )

        assert False

    except ValueError:
        assert True
