from typing import Any

from pydantic import ValidationError

from eduagent_course_dsl.models import (
    CourseDocument,
)


def validate_course_document(
    data: dict[str, Any],
) -> dict:
    try:
        document = CourseDocument.model_validate(
            data
        )

        return {
            "valid": True,
            "document": document,
            "errors": [],
        }

    except ValidationError as exc:
        return {
            "valid": False,
            "document": None,
            "errors": exc.errors(),
        }
