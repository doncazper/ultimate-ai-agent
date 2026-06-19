from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel

from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


TASK_DECOMPOSITION_API_ENV = "UAA_TASK_DECOMPOSITION_API_ENABLED"
TASK_DECOMPOSITION_API_BEARER_ENV = "UAA_TASK_DECOMPOSITION_API_BEARER"

_REDACTED_TASK_REQUEST_REF = "task_request_ref:raw_request_omitted"
_REDACTED_REGISTRY_REF = "task_decomposition_registry_ref:local"
_REDACTED_APPROVAL_REF = "approval_ref:omitted"
_TASK_REQUEST_DERIVED_TEXT_KEYS = {
    "goal",
    "objective",
    "raw_request",
}
_TASK_REQUEST_BINDING_KEYS = {
    "request",
    "raw_request",
}
_LOCAL_PATH_KEYS = {
    "registry_path",
}
_READ_APPROVAL_REF_KEYS = {
    "approval_ref",
    "approval_request_id",
}


def task_decomposition_authority_error(
    authorization: str | None,
    env: Mapping[str, str] | None = None,
) -> tuple[int, str] | None:
    values = os.environ if env is None else env
    if values.get(TASK_DECOMPOSITION_API_ENV) != "1":
        return 403, "Task decomposition local API authority is disabled by default."
    expected_bearer = values.get(TASK_DECOMPOSITION_API_BEARER_ENV)
    if not expected_bearer or authorization != f"Bearer {expected_bearer}":
        return 401, "Task decomposition local API authority requires an explicit local bearer."
    return None


def sanitize_task_decomposition_api_payload(
    payload: Any,
    *,
    redact_read_refs: bool = False,
) -> Any:
    if isinstance(payload, BaseModel):
        payload = payload.model_dump(mode="json")
    if isinstance(payload, dict):
        safe: dict[str, Any] = {}
        for key, value in payload.items():
            if key in _LOCAL_PATH_KEYS:
                safe["registry_ref"] = _REDACTED_REGISTRY_REF
                safe["registry_path_omitted"] = True
                continue
            if redact_read_refs and key in _READ_APPROVAL_REF_KEYS:
                safe[f"{key}_omitted"] = True
                safe[f"{key}_safe_ref"] = _REDACTED_APPROVAL_REF
                continue
            if key == "input_bindings" and isinstance(value, dict):
                safe[key] = _sanitize_input_bindings(value, redact_read_refs=redact_read_refs)
                continue
            if key in _TASK_REQUEST_DERIVED_TEXT_KEYS:
                safe[f"{key}_ref"] = _REDACTED_TASK_REQUEST_REF
                safe[f"{key}_omitted"] = True
                continue
            safe[key] = sanitize_task_decomposition_api_payload(value, redact_read_refs=redact_read_refs)
        return safe
    if isinstance(payload, list):
        return [
            sanitize_task_decomposition_api_payload(item, redact_read_refs=redact_read_refs)
            for item in payload
        ]
    if isinstance(payload, tuple):
        return [
            sanitize_task_decomposition_api_payload(item, redact_read_refs=redact_read_refs)
            for item in payload
        ]
    if isinstance(payload, str) and contains_obvious_secret({"value": payload}):
        return "[redacted]"
    return payload


def _sanitize_input_bindings(bindings: dict[str, Any], *, redact_read_refs: bool) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in bindings.items():
        if key in _TASK_REQUEST_BINDING_KEYS:
            safe[f"{key}_ref"] = _REDACTED_TASK_REQUEST_REF
            safe[f"{key}_omitted"] = True
            continue
        safe[key] = sanitize_task_decomposition_api_payload(value, redact_read_refs=redact_read_refs)
    return safe
