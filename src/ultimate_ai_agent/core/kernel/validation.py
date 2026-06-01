from pydantic import ValidationError

from ultimate_ai_agent.core.files.validation import file_content_contains_secret
from ultimate_ai_agent.core.kernel.requests import KernelTaskRequest


def validate_kernel_payload(payload: dict) -> KernelTaskRequest:
    if _payload_contains_secret(payload):
        raise ValueError("SECRET_CONTENT_BLOCKED")
    try:
        return KernelTaskRequest.model_validate(payload)
    except ValidationError:
        raise


def _payload_contains_secret(payload: object) -> bool:
    if isinstance(payload, str):
        return file_content_contains_secret(payload)
    if isinstance(payload, dict):
        return any(_payload_contains_secret(key) or _payload_contains_secret(value) for key, value in payload.items())
    if isinstance(payload, list):
        return any(_payload_contains_secret(item) for item in payload)
    return False
