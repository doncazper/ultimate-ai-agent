import re
from typing import Any

from ultimate_ai_agent.core.planning.enums import PlanInputTrustLevel, TaskRiskLevel, TaskStepKind


SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")
SECRET_LIKE_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer\s+|cookie|password|private\s+key|secret|token|client[_-]?secret)"
)
RAW_LOCAL_PATH_RE = re.compile(r"(^|[\s:=])(/Users/|/home/|/var/|/etc/|[A-Za-z]:\\)")
HIDDEN_SIDE_EFFECT_RE = re.compile(
    r"(?i)(action|browser|daemon|delete|execute|execution|file[_ -]?(write|delete|mutation)|"
    r"memory[_ -]?write|model[_ -]?call|network|plugin|remote|scheduler|shell|sub" r"process|"
    r"tool[_ -]?execution|write)"
)

SAFE_STEP_KINDS = {
    TaskStepKind.no_effect,
    TaskStepKind.review_metadata,
    TaskStepKind.summarize_refs,
    TaskStepKind.compare_refs,
    TaskStepKind.prepare_checklist,
}
BLOCKED_EXECUTION_STEP_KINDS = set(TaskStepKind) - SAFE_STEP_KINDS
RISK_ORDER = {
    TaskRiskLevel.none: 0,
    TaskRiskLevel.low: 1,
    TaskRiskLevel.medium: 2,
    TaskRiskLevel.high: 3,
    TaskRiskLevel.critical: 4,
    TaskRiskLevel.blocked: 5,
    TaskRiskLevel.unknown_blocked: 5,
}
STEP_KIND_DERIVED_RISK = {
    TaskStepKind.no_effect: TaskRiskLevel.none,
    TaskStepKind.review_metadata: TaskRiskLevel.low,
    TaskStepKind.summarize_refs: TaskRiskLevel.low,
    TaskStepKind.compare_refs: TaskRiskLevel.low,
    TaskStepKind.prepare_checklist: TaskRiskLevel.low,
    TaskStepKind.tool_execution_planned: TaskRiskLevel.high,
    TaskStepKind.action_execution_planned: TaskRiskLevel.high,
    TaskStepKind.file_mutation_planned: TaskRiskLevel.high,
    TaskStepKind.memory_write_planned: TaskRiskLevel.high,
    TaskStepKind.network_call_planned: TaskRiskLevel.high,
    TaskStepKind.model_call_planned: TaskRiskLevel.high,
    TaskStepKind.browser_action_planned: TaskRiskLevel.high,
    TaskStepKind.mobile_device_action_planned: TaskRiskLevel.high,
    TaskStepKind.remote_execution_planned: TaskRiskLevel.high,
    TaskStepKind.plugin_enablement_planned: TaskRiskLevel.high,
    TaskStepKind.shell_execution_blocked: TaskRiskLevel.critical,
    TaskStepKind.destructive_blocked: TaskRiskLevel.critical,
    TaskStepKind.unknown_blocked: TaskRiskLevel.unknown_blocked,
}
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


def _payload_contains_hidden_side_effect(value: Any) -> bool:
    if isinstance(value, str):
        return bool(HIDDEN_SIDE_EFFECT_RE.search(value))
    if isinstance(value, list):
        return any(_payload_contains_hidden_side_effect(item) for item in value)
    if isinstance(value, dict):
        return any(
            _payload_contains_hidden_side_effect(str(key)) or _payload_contains_hidden_side_effect(item)
            for key, item in value.items()
        )
    return False


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


def step_kind_reasons(step_kind: TaskStepKind, declared_risk_level: TaskRiskLevel) -> list[str]:
    reasons: list[str] = []
    if step_kind in BLOCKED_EXECUTION_STEP_KINDS:
        reasons.append("TASK_STEP_EXECUTION_DENIED")
    if RISK_ORDER.get(declared_risk_level, 0) < RISK_ORDER.get(derived_step_risk_level(step_kind), 5):
        reasons.append("TASK_RISK_DOWNGRADE_DENIED")
    return reasons


def derived_step_risk_level(step_kind: TaskStepKind, declared_risk_level: TaskRiskLevel | None = None) -> TaskRiskLevel:
    derived = STEP_KIND_DERIVED_RISK.get(step_kind, TaskRiskLevel.unknown_blocked)
    if declared_risk_level is not None and step_kind in SAFE_STEP_KINDS:
        return max([derived, declared_risk_level], key=lambda risk: RISK_ORDER.get(risk, 5))
    return derived


def hidden_side_effect_reasons(step: Any) -> list[str]:
    reasons: list[str] = []
    if _payload_contains_hidden_side_effect(getattr(step, "metadata", {})):
        reasons.append("TASK_HIDDEN_SIDE_EFFECT_DENIED")
        if RISK_ORDER.get(getattr(step, "declared_risk_level", TaskRiskLevel.none), 0) < RISK_ORDER[TaskRiskLevel.high]:
            reasons.append("TASK_RISK_DOWNGRADE_DENIED")
    return reasons


def plan_derived_risk_level(steps: list) -> TaskRiskLevel:
    risks: list[TaskRiskLevel] = []
    for step in steps:
        derived = derived_step_risk_level(
            getattr(step, "step_kind", TaskStepKind.unknown_blocked),
            getattr(step, "declared_risk_level", None),
        )
        if hidden_side_effect_reasons(step):
            derived = max([derived, TaskRiskLevel.high], key=lambda risk: RISK_ORDER.get(risk, 5))
        risks.append(derived)
    if not risks:
        return TaskRiskLevel.unknown_blocked
    return max(risks, key=lambda risk: RISK_ORDER.get(risk, 5))
