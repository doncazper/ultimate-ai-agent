from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ultimate_ai_agent.core.hygiene.envelopes import (
    ErrorCategory,
    ErrorEnvelope,
    ResultEnvelope,
    Severity,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like


def _sanitize_validation_location(part: object) -> str:
    text = str(part)
    sensitive_keys = {
        "api_key",
        "auth_token",
        "client_secret",
        "credential_value",
        "password",
        "private_key",
        "raw_secret",
        "secret",
        "secret_value",
        "token",
    }
    normalized = text.lower().replace("-", "_")
    if normalized in sensitive_keys or contains_secret_like(text):
        return "[redacted]"
    return text


def sanitize_validation_errors(errors: list[dict]) -> list[dict]:
    sanitized = []
    for error in errors:
        sanitized_error = {
            "type": error.get("type", "validation_error"),
            "loc": [
                _sanitize_validation_location(part)
                for part in error.get("loc", [])
            ],
            "msg": error.get("msg", "Validation failed."),
        }
        if contains_secret_like(sanitized_error["msg"]):
            sanitized_error["msg"] = "Validation failed."
        sanitized.append(sanitized_error)
    return sanitized


def safe_validation_error_response(
    *,
    path: str,
    errors: list[dict],
) -> JSONResponse:
    envelope = ResultEnvelope(
        success=False,
        operation="request_validation",
        service="API",
        trace_id="system",
        error=ErrorEnvelope(
            code="REQUEST_VALIDATION_FAILED",
            category=ErrorCategory.validation_error,
            safe_message="Request validation failed.",
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="FastAPI",
            caused_by=["RequestValidationError"],
            metadata={
                "path": path,
                "error_count": len(errors),
                "validation_errors": sanitize_validation_errors(errors),
            },
        ),
        redactions_applied=["validation_input"],
    )
    return JSONResponse(status_code=422, content=envelope.model_dump(mode="json"))


def safe_request_validation_error_response(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return safe_validation_error_response(path=request.url.path, errors=exc.errors())


__all__ = [
    "safe_request_validation_error_response",
    "safe_validation_error_response",
    "sanitize_validation_errors",
]
