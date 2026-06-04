import re
from typing import Any

from pydantic import ValidationError


NOOP_TOOL_REF = "tool:no_op.v1"
NOOP_TOOL_NAME = "noop"
FILESYSTEM_METADATA_TOOL_REF = "tool:filesystem_metadata.v1"
FILESYSTEM_METADATA_TOOL_NAME = "filesystem_metadata"
ALLOWLISTED_TOOL_NAMES = {
    NOOP_TOOL_REF: NOOP_TOOL_NAME,
    FILESYSTEM_METADATA_TOOL_REF: FILESYSTEM_METADATA_TOOL_NAME,
}
SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")
SECRET_LIKE_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer\s+|cookie|password|private\s+key|secret|token\b|client[_-]?secret)"
)
RAW_LOCAL_PATH_RE = re.compile(r"(^|[\s:=])(/Users/|/home/|/var/|/etc/|[A-Za-z]:\\)")
EFFECTFUL_TOOL_RE = re.compile(
    r"(?i)(file|memory|network|model|browser|mobile|remote|plugin|shell|tool[_\s-]?execute|dynamic|callable|module)"
)
DYNAMIC_DISPATCH_FIELD_RE = re.compile(
    r"(?i)(module|module_path|callable|callable_name|function|function_name|handler|dispatch|registry|plugin_registry|tool_ref|tool_name)"
)
SIDE_EFFECT_FIELD_RE = re.compile(
    r"(?i)(side_effect|file_(read|write|delete)|memory_write|network_call|model_call|browser_action|mobile_action|remote_action|plugin_action|shell_command|environment_read|secret_lookup)"
)
SIDE_EFFECT_VALUE_RE = re.compile(
    r"(?i)(file[_:.-]?(read|write|delete)|memory[_:.-]?write|network[_:.-]?call|model[_:.-]?call|browser[_:.-]?action|mobile[_:.-]?action|remote[_:.-]?action|plugin[_:.-]?(action|enable)|shell[_:.-]?command|side[_:.-]?effect)"
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


def _payload_boundary_reason_codes(value: Any) -> list[str]:
    reasons: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if DYNAMIC_DISPATCH_FIELD_RE.search(key_text):
                reasons.append("DYNAMIC_DISPATCH_DENIED")
            if SIDE_EFFECT_FIELD_RE.search(key_text):
                reasons.append("SIDE_EFFECT_ATTEMPT_DENIED")
            reasons.extend(_payload_boundary_reason_codes(item))
        return reasons
    if isinstance(value, list):
        for item in value:
            reasons.extend(_payload_boundary_reason_codes(item))
        return reasons
    if isinstance(value, str):
        if DYNAMIC_DISPATCH_FIELD_RE.search(value):
            reasons.append("DYNAMIC_DISPATCH_DENIED")
        if SIDE_EFFECT_VALUE_RE.search(value):
            reasons.append("SIDE_EFFECT_ATTEMPT_DENIED")
    return reasons


def runtime_request_boundary_reason_codes(value: Any, allowed_fields: set[str]) -> list[str]:
    reasons: list[str] = []
    for field_name, field_value in value.__dict__.items():
        if field_name not in allowed_fields:
            if DYNAMIC_DISPATCH_FIELD_RE.search(field_name):
                reasons.append("DYNAMIC_DISPATCH_DENIED")
            if SIDE_EFFECT_FIELD_RE.search(field_name):
                reasons.append("SIDE_EFFECT_ATTEMPT_DENIED")
            reasons.extend(_payload_boundary_reason_codes(field_value))
    reasons.extend(_payload_boundary_reason_codes(value.__dict__.get("metadata", {})))
    return list(dict.fromkeys(reasons))


def tool_allowlist_reason_codes(tool_ref: str, tool_name: str) -> list[str]:
    reasons: list[str] = []
    expected_tool_name = ALLOWLISTED_TOOL_NAMES.get(tool_ref)
    if expected_tool_name is None:
        reasons.append("TOOL_NOT_ALLOWLISTED_DENIED")
    if expected_tool_name is None or tool_name != expected_tool_name:
        reasons.append("TOOL_NAME_MISMATCH_DENIED")
    if EFFECTFUL_TOOL_RE.search(tool_ref) and tool_ref not in ALLOWLISTED_TOOL_NAMES:
        reasons.append("EFFECTFUL_TOOL_BLOCKED")
    if EFFECTFUL_TOOL_RE.search(tool_name) and tool_name != expected_tool_name:
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
        if prefix in {
            "task-plan",
            "plan",
            "context-pack",
            "memory",
            "tool-intent",
            "approval",
            "model",
            "runtime",
            "openwebui",
            "control-center",
        }:
            reasons.append("AUTHORITY_REF_NOT_TOOL_RUNTIME_AUTHORITY")
    return list(dict.fromkeys(reasons))
