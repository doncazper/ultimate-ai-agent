import re
from typing import Any

from ultimate_ai_agent.core.execution.enums import (
    ExecutionBlockReason,
    ExecutionInputTrustLevel,
    ExecutionStepMode,
)


SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")
SECRET_LIKE_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer\s+|cookie|password|private\s+key|secret|token|client[_-]?secret)"
)
ABSOLUTE_LOCAL_PATH_PATTERNS = (
    re.compile(r"(?:^|[^A-Za-z0-9])[A-Za-z]:[\\/][^\s\"')>\],;]*"),
    re.compile(r"(?:^|[^A-Za-z0-9])\\\\[^\\\s]+\\[^\s\"')>\],;]+"),
    re.compile(r"\b(?i:file):(?://|%2f)"),
)
_POSIX_ABSOLUTE_PATH_CANDIDATE_RE = re.compile(r"/(?:/)?[^\s\"')>\],;]+")
_SAFE_REF_TOKEN_RE = re.compile(
    r"[A-Za-z][A-Za-z0-9_.-]*:[A-Za-z0-9][A-Za-z0-9_.:/@-]*"
)
_NETWORK_URI_TOKEN_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://[^\s\"')>\],;]+")
RAW_LOCAL_PATH_RE = re.compile(r"(^|[\s:=])(/Users/|/home/|/var/|/etc/|[A-Za-z]:\\)")
EFFECTFUL_HINT_RE = re.compile(
    r"(?i)("
    r"file[_\s-]?(write|delete|mutat)|"
    r"memory[_\s-]?write|"
    r"tool[_\s-]?(execute|execution)|"
    r"action[_\s-]?(execute|execution)|"
    r"task[_\s-]?(execute|execution)|"
    r"network[_\s-]?(call|send|post)|"
    r"model[_\s-]?(call|provider)|"
    r"browser|mobile|remote|plugin|shell|" + "sub" + "process|"
    r"scheduler|background[_\s-]?worker|side[_\s-]?effect"
    r")"
)

SAFE_STEP_MODES = {
    ExecutionStepMode.no_effect,
    ExecutionStepMode.validation_only,
    ExecutionStepMode.receipt_plan_only,
}

STEP_MODE_REASONS = {
    ExecutionStepMode.task_execution_blocked: ExecutionBlockReason.task_execution_denied.value,
    ExecutionStepMode.action_execution_blocked: ExecutionBlockReason.action_execution_denied.value,
    ExecutionStepMode.tool_execution_blocked: ExecutionBlockReason.tool_execution_denied.value,
    ExecutionStepMode.file_mutation_blocked: ExecutionBlockReason.file_mutation_denied.value,
    ExecutionStepMode.memory_write_blocked: ExecutionBlockReason.memory_write_denied.value,
    ExecutionStepMode.event_ledger_mutation_blocked: ExecutionBlockReason.event_ledger_mutation_denied.value,
    ExecutionStepMode.network_call_blocked: ExecutionBlockReason.network_call_denied.value,
    ExecutionStepMode.model_call_blocked: ExecutionBlockReason.model_call_denied.value,
    ExecutionStepMode.browser_action_blocked: ExecutionBlockReason.browser_action_denied.value,
    ExecutionStepMode.mobile_device_action_blocked: ExecutionBlockReason.mobile_device_action_denied.value,
    ExecutionStepMode.remote_execution_blocked: ExecutionBlockReason.remote_execution_denied.value,
    ExecutionStepMode.plugin_enablement_blocked: ExecutionBlockReason.plugin_enablement_denied.value,
    ExecutionStepMode.shell_execution_blocked: ExecutionBlockReason.shell_execution_denied.value,
    ExecutionStepMode.scheduler_blocked: ExecutionBlockReason.scheduler_denied.value,
    ExecutionStepMode.background_worker_blocked: ExecutionBlockReason.background_worker_denied.value,
    ExecutionStepMode.unknown_blocked: ExecutionBlockReason.unknown_step_mode_denied.value,
}


def dedupe_reasons(reasons: list[str]) -> list[str]:
    return list(dict.fromkeys(reason for reason in reasons if reason))


def validation_reason(
    exc: Exception, fallback: str = "EXECUTION_REVALIDATION_FAILED"
) -> list[str]:
    message = str(exc).lower()
    if "raw_prompt_denied" in message:
        return ["RAW_PROMPT_DENIED", fallback]
    if "raw_model_output_denied" in message:
        return ["RAW_MODEL_OUTPUT_DENIED", fallback]
    if "raw_file_content_denied" in message:
        return ["RAW_FILE_CONTENT_DENIED", fallback]
    if "raw_transcript_denied" in message:
        return ["RAW_TRANSCRIPT_DENIED", fallback]
    if "secret_like_input_denied" in message:
        return ["SECRET_LIKE_INPUT_DENIED", fallback]
    if "unsafe content" in message or "secret" in message:
        return ["SECRET_METADATA_DENIED", fallback]
    if "raw_" in message or "raw " in message:
        return ["RAW_INPUT_DENIED", fallback]
    return [fallback]


def validate_safe_execution_text(value: str, field_name: str = "text") -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")
    if (
        SECRET_LIKE_RE.search(value)
        or "-----BEGIN" in value
        or RAW_LOCAL_PATH_RE.search(value)
    ):
        raise ValueError(f"{field_name} contains unsafe content")


def contains_absolute_local_path(value: str) -> bool:
    """Return whether text contains an absolute local path in canonical grammar."""

    if any(pattern.search(value) for pattern in ABSOLUTE_LOCAL_PATH_PATTERNS):
        return True
    protected_spans = [
        match.span()
        for pattern in (_SAFE_REF_TOKEN_RE, _NETWORK_URI_TOKEN_RE)
        for match in pattern.finditer(value)
    ]
    for match in _POSIX_ABSOLUTE_PATH_CANDIDATE_RE.finditer(value):
        slash_index = match.start()
        predecessor = value[slash_index - 1] if slash_index > 0 else ""
        if predecessor.isascii() and predecessor.isalnum():
            continue
        if any(start <= slash_index < end for start, end in protected_spans):
            continue
        return True
    return False


def validate_safe_execution_payload(value: Any, field_name: str = "payload") -> None:
    if isinstance(value, str):
        if value:
            validate_safe_execution_text(value, field_name)
        return
    if isinstance(value, list):
        for item in value:
            validate_safe_execution_payload(item, field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            validate_safe_execution_payload(str(key), field_name)
            validate_safe_execution_payload(item, field_name)


def hidden_side_effect_reasons(value: Any) -> list[str]:
    reasons: list[str] = []
    if isinstance(value, str):
        if EFFECTFUL_HINT_RE.search(value):
            reasons.append("HIDDEN_SIDE_EFFECT_DENIED")
        return reasons
    if isinstance(value, list):
        for item in value:
            reasons.extend(hidden_side_effect_reasons(item))
        return dedupe_reasons(reasons)
    if isinstance(value, dict):
        for key, item in value.items():
            reasons.extend(hidden_side_effect_reasons(str(key)))
            reasons.extend(hidden_side_effect_reasons(item))
    return dedupe_reasons(reasons)


def validate_execution_ref(value: str, field_name: str = "ref") -> None:
    validate_safe_execution_text(value, field_name)
    if SAFE_REF_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a structured safe ref")


def raw_input_reasons(boundary: Any) -> list[str]:
    reasons: list[str] = []
    if bool(getattr(boundary, "contains_raw_prompt", False)):
        reasons.append("RAW_PROMPT_DENIED")
    if bool(getattr(boundary, "contains_raw_model_output", False)):
        reasons.append("RAW_MODEL_OUTPUT_DENIED")
    if bool(getattr(boundary, "contains_raw_file_content", False)):
        reasons.append("RAW_FILE_CONTENT_DENIED")
    if bool(getattr(boundary, "contains_raw_transcript", False)):
        reasons.append("RAW_TRANSCRIPT_DENIED")
    if bool(getattr(boundary, "contains_secret_like_content", False)):
        reasons.append("SECRET_LIKE_INPUT_DENIED")
    return reasons


def infer_input_trust_level(source_ref: str) -> ExecutionInputTrustLevel:
    prefix = source_ref.split(":", 1)[0].lower()
    if prefix == "canonical":
        return ExecutionInputTrustLevel.canonical_ref
    if prefix == "evidence":
        return ExecutionInputTrustLevel.evidence_ref
    if prefix == "receipt":
        return ExecutionInputTrustLevel.receipt_ref
    if prefix == "event":
        return ExecutionInputTrustLevel.event_ref
    if prefix in {"user", "user_reviewed", "file_ref", "truth", "truth_claim"}:
        return ExecutionInputTrustLevel.user_reviewed_ref
    if prefix == "memory":
        return ExecutionInputTrustLevel.memory_ref
    if prefix == "context-pack":
        return ExecutionInputTrustLevel.context_pack_ref
    if prefix == "tool-intent":
        return ExecutionInputTrustLevel.tool_intent_ref
    if prefix == "approval":
        return ExecutionInputTrustLevel.approval_ref
    if prefix == "approval-decision":
        return ExecutionInputTrustLevel.approval_decision_ref
    if prefix == "model":
        return ExecutionInputTrustLevel.model_output_blocked
    if prefix == "runtime":
        return ExecutionInputTrustLevel.runtime_output_blocked
    if prefix == "openwebui":
        return ExecutionInputTrustLevel.openwebui_output_blocked
    if prefix == "control-center":
        return ExecutionInputTrustLevel.control_center_preview_blocked
    return ExecutionInputTrustLevel.unknown_blocked


def input_trust_reasons(
    source_ref: str, declared: ExecutionInputTrustLevel
) -> list[str]:
    inferred = infer_input_trust_level(source_ref)
    reasons: list[str] = []
    if inferred == ExecutionInputTrustLevel.unknown_blocked:
        reasons.append("UNKNOWN_INPUT_REF_DENIED")
    if inferred == ExecutionInputTrustLevel.model_output_blocked:
        reasons.append("MODEL_OUTPUT_NOT_EXECUTION_AUTHORITY")
    if inferred == ExecutionInputTrustLevel.runtime_output_blocked:
        reasons.append("RUNTIME_OUTPUT_NOT_EXECUTION_AUTHORITY")
    if inferred == ExecutionInputTrustLevel.openwebui_output_blocked:
        reasons.append("OPENWEBUI_OUTPUT_NOT_EXECUTION_AUTHORITY")
    if inferred == ExecutionInputTrustLevel.control_center_preview_blocked:
        reasons.append("CONTROL_CENTER_PREVIEW_NOT_EXECUTION_AUTHORITY")
    if (
        inferred == ExecutionInputTrustLevel.memory_ref
        or declared == ExecutionInputTrustLevel.memory_ref
    ):
        reasons.append("MEMORY_REF_NOT_EXECUTION_AUTHORITY")
    if (
        inferred == ExecutionInputTrustLevel.context_pack_ref
        or declared == ExecutionInputTrustLevel.context_pack_ref
    ):
        reasons.append("CONTEXT_PACK_NOT_EXECUTION_AUTHORITY")
    if (
        inferred == ExecutionInputTrustLevel.tool_intent_ref
        or declared == ExecutionInputTrustLevel.tool_intent_ref
    ):
        reasons.append("TOOL_INTENT_NOT_EXECUTION_AUTHORITY")
    if inferred in {
        ExecutionInputTrustLevel.approval_ref,
        ExecutionInputTrustLevel.approval_decision_ref,
    } or declared in {
        ExecutionInputTrustLevel.approval_ref,
        ExecutionInputTrustLevel.approval_decision_ref,
    }:
        reasons.append("APPROVAL_REF_NOT_EXECUTION_AUTHORITY")
    if declared in {
        ExecutionInputTrustLevel.model_output_blocked,
        ExecutionInputTrustLevel.runtime_output_blocked,
        ExecutionInputTrustLevel.openwebui_output_blocked,
        ExecutionInputTrustLevel.control_center_preview_blocked,
        ExecutionInputTrustLevel.unknown_blocked,
    }:
        reasons.append("INPUT_TRUST_LEVEL_DENIED")
    return dedupe_reasons(reasons)


def boundary_reason_codes(boundary: Any) -> list[str]:
    reasons = raw_input_reasons(boundary)
    for ref in [
        *getattr(boundary, "input_refs", []),
        *getattr(boundary, "metadata_refs", []),
    ]:
        reasons.extend(
            input_trust_reasons(
                ref,
                getattr(
                    boundary,
                    "input_trust_level",
                    ExecutionInputTrustLevel.safe_reference,
                ),
            )
        )
    return dedupe_reasons(reasons)


def step_mode_reason(mode: ExecutionStepMode) -> str | None:
    if mode in SAFE_STEP_MODES:
        return None
    return STEP_MODE_REASONS.get(
        mode, ExecutionBlockReason.unknown_step_mode_denied.value
    )
