import re
from typing import Any

from ultimate_ai_agent.core.planning.enums import PlanInputTrustLevel, TaskRiskLevel, TaskStepKind


SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")
SECRET_LIKE_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer\s+|cookie|password|private\s+key|secret|token|client[_-]?secret)"
)
RAW_LOCAL_PATH_RE = re.compile(r"(^|[\s:=])(/Users/|/home/|/var/|/etc/|[A-Za-z]:\\)")

SAFE_STEP_KINDS = {
    TaskStepKind.no_effect,
    TaskStepKind.review_metadata,
    TaskStepKind.summarize_refs,
    TaskStepKind.compare_refs,
    TaskStepKind.prepare_checklist,
}
BLOCKED_EXECUTION_STEP_KINDS = set(TaskStepKind) - SAFE_STEP_KINDS
SAFE_INPUT_PREFIXES = {
    "canonical",
    "evidence",
    "receipt",
    "event",
    "user",
    "user_reviewed",
    "file_ref",
    "truth",
    "truth_claim",
}


def validate_safe_task_text(value: str, field_name: str = "text") -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")
    if SECRET_LIKE_RE.search(value) or "-----BEGIN" in value or RAW_LOCAL_PATH_RE.search(value):
        raise ValueError(f"{field_name} contains unsafe content")


def validate_safe_task_payload(value: Any, field_name: str = "payload") -> None:
    if isinstance(value, str):
        if value:
            validate_safe_task_text(value, field_name)
        return
    if isinstance(value, list):
        for item in value:
            validate_safe_task_payload(item, field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            validate_safe_task_payload(str(key), field_name)
            validate_safe_task_payload(item, field_name)


def validate_task_ref(value: str, field_name: str = "ref") -> None:
    validate_safe_task_text(value, field_name)
    if not SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name} must be a structured safe ref")


def infer_input_trust_level(source_ref: str) -> PlanInputTrustLevel:
    prefix = source_ref.split(":", 1)[0].lower()
    if prefix == "canonical":
        return PlanInputTrustLevel.canonical_ref
    if prefix == "evidence":
        return PlanInputTrustLevel.evidence_ref
    if prefix == "receipt":
        return PlanInputTrustLevel.receipt_ref
    if prefix == "event":
        return PlanInputTrustLevel.event_ref
    if prefix in {"user", "user_reviewed", "file_ref", "truth", "truth_claim"}:
        return PlanInputTrustLevel.user_reviewed_ref
    if prefix == "memory":
        return PlanInputTrustLevel.memory_ref
    if prefix == "context-pack":
        return PlanInputTrustLevel.context_pack_ref
    if prefix == "tool-intent":
        return PlanInputTrustLevel.tool_intent_ref
    if prefix == "approval":
        return PlanInputTrustLevel.approval_ref
    if prefix == "model":
        return PlanInputTrustLevel.model_output_blocked
    if prefix == "runtime":
        return PlanInputTrustLevel.runtime_output_blocked
    if prefix == "openwebui":
        return PlanInputTrustLevel.openwebui_output_blocked
    return PlanInputTrustLevel.unknown_blocked


def input_trust_reasons(source_ref: str, declared: PlanInputTrustLevel) -> list[str]:
    inferred = infer_input_trust_level(source_ref)
    reasons: list[str] = []
    if inferred == PlanInputTrustLevel.unknown_blocked:
        reasons.append("UNKNOWN_INPUT_REF_DENIED")
    if inferred == PlanInputTrustLevel.model_output_blocked:
        reasons.append("MODEL_OUTPUT_NOT_PLAN_AUTHORITY")
    if inferred == PlanInputTrustLevel.runtime_output_blocked:
        reasons.append("RUNTIME_OUTPUT_NOT_PLAN_AUTHORITY")
    if inferred == PlanInputTrustLevel.openwebui_output_blocked:
        reasons.append("OPENWEBUI_OUTPUT_NOT_PLAN_AUTHORITY")
    if inferred == PlanInputTrustLevel.memory_ref or declared == PlanInputTrustLevel.memory_ref:
        reasons.append("MEMORY_REF_NOT_PLAN_AUTHORITY")
    if inferred == PlanInputTrustLevel.context_pack_ref or declared == PlanInputTrustLevel.context_pack_ref:
        reasons.append("CONTEXT_PACK_NOT_PLAN_AUTHORITY")
    if inferred == PlanInputTrustLevel.tool_intent_ref or declared == PlanInputTrustLevel.tool_intent_ref:
        reasons.append("TOOL_INTENT_NOT_PLAN_AUTHORITY")
    if inferred == PlanInputTrustLevel.approval_ref or declared == PlanInputTrustLevel.approval_ref:
        reasons.append("APPROVAL_REF_NOT_TASK_AUTHORITY")
    if declared in {
        PlanInputTrustLevel.model_output_blocked,
        PlanInputTrustLevel.runtime_output_blocked,
        PlanInputTrustLevel.openwebui_output_blocked,
        PlanInputTrustLevel.unknown_blocked,
    }:
        reasons.append("INPUT_TRUST_LEVEL_DENIED")
    return list(dict.fromkeys(reasons))


def raw_input_reasons(boundary) -> list[str]:
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


def step_kind_reasons(step_kind: TaskStepKind, declared_risk_level: TaskRiskLevel) -> list[str]:
    reasons: list[str] = []
    if step_kind in BLOCKED_EXECUTION_STEP_KINDS:
        reasons.append("TASK_STEP_EXECUTION_DENIED")
        if declared_risk_level in {TaskRiskLevel.none, TaskRiskLevel.low}:
            reasons.append("TASK_RISK_DOWNGRADE_DENIED")
    return reasons
