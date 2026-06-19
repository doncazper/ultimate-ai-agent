from pathlib import Path

from ultimate_ai_agent.api.app import safe_exception_message, sanitize_validation_errors


def test_api_handlers_do_not_return_raw_exception_messages():
    app_source = Path("src/ultimate_ai_agent/api/app.py").read_text(encoding="utf-8")

    assert "safe_message=str(e)" not in app_source
    assert "safe_message = str(e)" not in app_source
    assert "safe_message=str(exc)" not in app_source
    assert "safe_message = str(exc)" not in app_source
    assert "detail=str(e)" not in app_source
    assert "detail = str(e)" not in app_source
    assert "detail=str(exc)" not in app_source
    assert "detail = str(exc)" not in app_source


def test_api_safe_exception_message_is_redacted_and_non_diagnostic():
    message = safe_exception_message("REQUEST_PROCESSING_FAILED")

    assert message == "REQUEST_PROCESSING_FAILED failed safely; details are redacted."
    assert "traceback" not in message.lower()
    assert "exception" not in message.lower()


def test_validation_error_sanitizer_redacts_secret_like_location_and_message():
    sanitized = sanitize_validation_errors(
        [
            {
                "type": "value_error",
                "loc": ["body", "token"],
                "msg": "token='abcdefghijklmnop' is invalid",
            }
        ]
    )

    assert sanitized == [
        {
            "type": "value_error",
            "loc": ["body", "[redacted]"],
            "msg": "Validation failed.",
        }
    ]
    assert "abcdefghijklmnop" not in str(sanitized)


def test_validation_error_sanitizer_handles_multiple_sensitive_fields():
    sanitized = sanitize_validation_errors(
        [
            {
                "type": "value_error",
                "loc": ["body", "client_secret"],
                "msg": "client_secret='abcdefghijklmnop' is invalid",
            },
            {
                "type": "value_error",
                "loc": ["body", "raw_secret"],
                "msg": "raw_secret='qrstuvwxyz123456' is invalid",
            },
        ]
    )

    assert sanitized == [
        {
            "type": "value_error",
            "loc": ["body", "[redacted]"],
            "msg": "Validation failed.",
        },
        {
            "type": "value_error",
            "loc": ["body", "[redacted]"],
            "msg": "Validation failed.",
        },
    ]
    assert "abcdefghijklmnop" not in str(sanitized)
    assert "qrstuvwxyz123456" not in str(sanitized)
