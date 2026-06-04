import re
from typing import Any

from pydantic import ValidationError


NOOP_TOOL_REF = "tool:no_op.v1"
NOOP_TOOL_NAME = "noop"
SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")
SECRET_LIKE_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer\s+|cookie|password|private\s+key|secret|token\b|client[_-]?secret)"
)
RAW_LOCAL_PATH_RE = re.compile(r"(^|[\s:=])(/Users/|/home/|/var/|/etc/|[A-Za-z]:\\)")
EFFECTFUL_TOOL_RE = re.compile(
    r"(?i)(file|memory|network|model|browser|mobile|remote|plugin|shell|tool[_\s-]?execute|dynamic|callable|module)"
)


def validate_safe_tool_runtime_text(value: str, field_name: str = "text") -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")
    if SECRET_LIKE_RE.search(value) or "-----BEGIN" in value or RAW_LOCAL_PATH_RE.search(value):
        raise ValueError(f"{field_name} contains unsafe content")


def validate_safe_tool_runtime_payload(value: Any, field_name: str = "payload") -> None:
    if isinstance(value, str):
        if value and (SECRET_LIKE_RE.search(value) or "-----BEGIN" in value or RAW_LOCAL_PATH_RE.search(value)):
            raise ValueError(f"{field_name} contains unsafe content")
        return
    if isinstance(value, list):
        for item in value:
            validate_safe_tool_runtime_payload(item, field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            validate_safe_tool_runtime_payload(str(key), field_name)
            validate_safe_tool_runtime_payload(item, field_name)
        return


def validate_tool_runtime_ref(value: str, field_name: str = "ref") -> None:
    validate_safe_tool_runtime_text(value, field_name)
    if not SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name} must be a structured safe ref")


def raw_input_reason_codes(value: Any) -> list[str]:
    reasons: list[str] = []
    for field_name, reason in [
        ("contains_raw_prompt", "RAW_PROMPT_DENIED"),
        ("contains_raw_model_output", "RAW_MODEL_OUTPUT_DENIED"),
        ("contains_raw_file_content", "RAW_FILE_CONTENT_DENIED"),
        ("contains_raw_transcript", "RAW_TRANSCRIPT_DENIED"),
        ("contains_secret_like_content", "SECRET_CONTENT_DENIED"),
    ]:
        if bool(value.__dict__.get(field_name, False)):
            reasons.append(reason)
    return reasons


def safe_validation_reasons(exc: Exception, fallback: str = "TOOL_RUNTIME_VALIDATION_FAILED") -> list[str]:
    text = str(exc).lower()
    if isinstance(exc, ValidationError):
        text = " ".join(str(error.get("msg", "")).lower() for error in exc.errors())
    reasons: list[str] = []
    if "raw prompt" in text:
        reasons.append("RAW_PROMPT_DENIED")
    if "raw model" in text or "model output" in text:
        reasons.append("RAW_MODEL_OUTPUT_DENIED")
    if "raw file" in text:
        reasons.append("RAW_FILE_CONTENT_DENIED")
    if "raw transcript" in text:
        reasons.append("RAW_TRANSCRIPT_DENIED")
    if "secret" in text or "unsafe content" in text:
        reasons.append("SECRET_CONTENT_DENIED")
    if "approval_test" in text:
        reasons.append("APPROVAL_TEST_REF_DENIED")
    if not reasons:
        reasons.append(fallback)
    return list(dict.fromkeys(reasons))


def tool_allowlist_reason_codes(tool_ref: str, tool_name: str) -> list[str]:
    reasons: list[str] = []
    if tool_ref != NOOP_TOOL_REF:
        reasons.append("TOOL_NOT_ALLOWLISTED_DENIED")
    if tool_name != NOOP_TOOL_NAME:
        reasons.append("TOOL_NAME_MISMATCH_DENIED")
    if EFFECTFUL_TOOL_RE.search(tool_ref) and tool_ref != NOOP_TOOL_REF:
        reasons.append("EFFECTFUL_TOOL_BLOCKED")
    if EFFECTFUL_TOOL_RE.search(tool_name) and tool_name != NOOP_TOOL_NAME:
        reasons.append("DYNAMIC_DISPATCH_DENIED")
    return list(dict.fromkeys(reasons))


def authority_reason_codes(approval_ref: str | None, authority_refs: list[str]) -> list[str]:
    reasons: list[str] = []
    if approval_ref:
        reasons.append("APPROVAL_REF_NOT_AUTHORITY")
        if approval_ref.startswith("approval_test_"):
            reasons.append("APPROVAL_TEST_REF_DENIED")
    for ref in authority_refs:
        prefix = ref.split(":", 1)[0]
        if prefix == "approval_test_":
            reasons.append("APPROVAL_TEST_REF_DENIED")
        if ref.startswith("approval_test_"):
            reasons.append("APPROVAL_TEST_REF_DENIED")
        if prefix in {"task-plan", "plan", "context-pack", "memory", "tool-intent", "approval", "model", "runtime", "openwebui"}:
            reasons.append("AUTHORITY_REF_NOT_TOOL_RUNTIME_AUTHORITY")
    return list(dict.fromkeys(reasons))
