from typing import Any


SECRET_MARKERS = (
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "private key",
    "authorization",
    "cookie",
    "bearer ",
    "sk-",
)

RAW_CONTENT_MARKERS = (
    "raw_",
    "raw ",
    "raw prompt",
    "raw transcript",
    "raw model output",
    "raw file content",
    "full prompt",
    "verbatim transcript",
)


def validate_safe_recall_text(value: str, field_name: str) -> str:
    lowered = value.lower()
    if any(marker in lowered for marker in RAW_CONTENT_MARKERS):
        raise ValueError(f"{field_name} must not include raw content")
    if any(marker in lowered for marker in SECRET_MARKERS):
        raise ValueError(f"{field_name} must not include secret-like content")
    if "/users/" in lowered or "\\users\\" in lowered:
        raise ValueError(f"{field_name} must not include private local paths")
    return value


def validate_safe_recall_payload(value: Any, field_name: str = "metadata") -> Any:
    if isinstance(value, str):
        return validate_safe_recall_text(value, field_name)
    if isinstance(value, dict):
        for key, item in value.items():
            validate_safe_recall_payload(str(key), f"{field_name} key")
            validate_safe_recall_payload(item, field_name)
    if isinstance(value, list):
        for item in value:
            validate_safe_recall_payload(item, field_name)
    return value


def validate_recall_ref(value: str, field_name: str) -> str:
    validate_safe_recall_text(value, field_name)
    if ":" not in value:
        raise ValueError(f"{field_name} must be a structured ref")
    return value
