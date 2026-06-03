import re
from typing import Any

from ultimate_ai_agent.core.tools.v2.enums import (
    ToolInputTrustLevel,
    ToolRiskClass,
    ToolSideEffectKind,
    ToolTargetKind,
)


SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")
SECRET_LIKE_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer\s+|cookie|password|private\s+key|secret|token=|client[_-]?secret)"
)
RAW_LOCAL_PATH_RE = re.compile(r"(^|[\s:=])(/Users/|/home/|/var/|/etc/|[A-Za-z]:\\)")


TARGET_REF_PREFIXES: dict[str, ToolTargetKind] = {
    "none": ToolTargetKind.none,
    "file": ToolTargetKind.file_ref,
    "file_ref": ToolTargetKind.file_ref,
    "memory": ToolTargetKind.memory_ref,
    "memory_ref": ToolTargetKind.memory_ref,
    "message": ToolTargetKind.message_draft_ref,
    "message_draft": ToolTargetKind.message_draft_ref,
    "draft": ToolTargetKind.message_draft_ref,
    "api": ToolTargetKind.api_route_ref,
    "api-route": ToolTargetKind.api_route_ref,
    "api_route": ToolTargetKind.api_route_ref,
    "route": ToolTargetKind.api_route_ref,
    "runtime": ToolTargetKind.local_runtime_ref,
    "local-runtime": ToolTargetKind.local_runtime_ref,
    "local_runtime": ToolTargetKind.local_runtime_ref,
    "browser": ToolTargetKind.browser_ref,
    "plugin": ToolTargetKind.plugin_ref,
    "remote": ToolTargetKind.remote_node_ref,
    "remote_node": ToolTargetKind.remote_node_ref,
    "node": ToolTargetKind.remote_node_ref,
    "mobile": ToolTargetKind.mobile_device_ref,
    "device": ToolTargetKind.mobile_device_ref,
    "context-pack": ToolTargetKind.context_pack_ref,
    "context_pack": ToolTargetKind.context_pack_ref,
}

RISK_RANK: dict[ToolRiskClass, int] = {
    ToolRiskClass.safe: 0,
    ToolRiskClass.low: 1,
    ToolRiskClass.medium: 2,
    ToolRiskClass.high: 3,
    ToolRiskClass.critical: 4,
    ToolRiskClass.forbidden: 5,
}

BLOCKED_INPUT_TRUST_LEVELS = {
    ToolInputTrustLevel.model_output,
    ToolInputTrustLevel.runtime_output,
    ToolInputTrustLevel.openwebui_output,
    ToolInputTrustLevel.unknown,
}


def validate_safe_tool_text(value: str, field_name: str = "text") -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")
    if SECRET_LIKE_RE.search(value):
        raise ValueError(f"{field_name} contains unsafe content")
    if "-----BEGIN" in value or RAW_LOCAL_PATH_RE.search(value):
        raise ValueError(f"{field_name} contains unsafe content")


def validate_safe_tool_payload(value: Any, field_name: str = "payload") -> None:
    if isinstance(value, str):
        if value and (SECRET_LIKE_RE.search(value) or "-----BEGIN" in value or RAW_LOCAL_PATH_RE.search(value)):
            raise ValueError(f"{field_name} contains unsafe content")
        return
    if isinstance(value, list):
        for item in value:
            validate_safe_tool_payload(item, field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            validate_safe_tool_payload(str(key), field_name)
            validate_safe_tool_payload(item, field_name)
        return


def validate_tool_ref(value: str, field_name: str = "ref") -> None:
    validate_safe_tool_text(value, field_name)
    if value != "none" and not SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name} must be a structured safe ref")


def infer_tool_target_kind(target_ref: str) -> ToolTargetKind:
    if target_ref == "none":
        return ToolTargetKind.none
    prefix = target_ref.split(":", 1)[0]
    return TARGET_REF_PREFIXES.get(prefix, ToolTargetKind.unknown)


def tool_target_reason_codes(target_ref: str, target_kind: ToolTargetKind) -> list[str]:
    inferred = infer_tool_target_kind(target_ref)
    reasons: list[str] = []
    if target_kind == ToolTargetKind.unknown or inferred == ToolTargetKind.unknown:
        reasons.append("UNKNOWN_TOOL_TARGET_DENIED")
    if inferred != ToolTargetKind.unknown and target_kind != inferred:
        reasons.append("TOOL_TARGET_KIND_MISMATCH_DENIED")
    return list(dict.fromkeys(reasons))


def risk_rank(risk_class: ToolRiskClass) -> int:
    return RISK_RANK[risk_class]


def has_side_effects(side_effects: list[ToolSideEffectKind]) -> bool:
    return any(effect != ToolSideEffectKind.none for effect in side_effects)


def assert_no_tool_execution(execution_allowed: bool) -> None:
    if execution_allowed:
        raise ValueError("M27 Tool Broker v2 decisions must not allow execution")


def assert_no_tool_side_effects(side_effects_performed: bool) -> None:
    if side_effects_performed:
        raise ValueError("M27 Tool Broker v2 decisions must not perform side effects")


def assert_approval_ref_not_authority(approval_ref: str | None) -> None:
    if approval_ref:
        raise ValueError("approval_ref is an identifier, not runtime authority")


def assert_context_pack_not_authority(context_pack_refs: list[str]) -> None:
    if context_pack_refs:
        raise ValueError("context pack refs are not tool execution authority")


def assert_model_output_not_tool_input(input_trust_level: ToolInputTrustLevel) -> None:
    if input_trust_level in BLOCKED_INPUT_TRUST_LEVELS:
        raise ValueError("model/runtime/OpenWebUI output is not trusted tool input")


def assert_tool_target_kind_consistency(target_ref: str, target_kind: ToolTargetKind) -> None:
    if tool_target_reason_codes(target_ref, target_kind):
        raise ValueError("tool target ref/kind consistency is required")


def assert_tool_risk_not_downgraded(declared_risk: ToolRiskClass, catalog_risk: ToolRiskClass) -> None:
    if risk_rank(declared_risk) < risk_rank(catalog_risk):
        raise ValueError("caller-declared risk cannot downgrade catalog risk")
