from services.course_service.app.tracing.recorder import (
    sanitize,
)


def test_sensitive_fields_are_redacted():
    value = {
        "name": "test",
        "password": "secret123",
        "nested": {
            "api_key": "abc",
        },
    }

    result = sanitize(value)

    assert result["name"] == "test"

    assert (
        result["password"]
        == "***REDACTED***"
    )

    assert (
        result["nested"]["api_key"]
        == "***REDACTED***"
    )
