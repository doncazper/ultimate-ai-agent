from pydantic import ValidationError

from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationRequest, ToolRuntimePolicy
from ultimate_ai_agent.core.tools.runtime.validation import (
    authority_reason_codes,
    raw_input_reason_codes,
    safe_validation_reasons,
    tool_allowlist_reason_codes,
    validate_safe_tool_runtime_payload,
)


def validate_tool_invocation_request(request: ToolInvocationRequest) -> list[str]:
    reasons: list[str] = []
    try:
        validate_safe_tool_runtime_payload(request.metadata, "metadata")
        ToolInvocationRequest.model_validate(request.model_dump())
    except (ValidationError, ValueError) as exc:
        reasons.extend(safe_validation_reasons(exc, fallback="TOOL_RUNTIME_REQUEST_REVALIDATION_FAILED"))
    reasons.extend(raw_input_reason_codes(request))
    reasons.extend(tool_allowlist_reason_codes(request.tool_ref, request.tool_name))
    reasons.extend(authority_reason_codes(request.approval_ref, request.authority_refs))
    if request.invocation_kind.value != "noop":
        reasons.append("EFFECTFUL_TOOL_BLOCKED")
    return list(dict.fromkeys(reasons))


def validate_runtime_policy(policy: ToolRuntimePolicy) -> list[str]:
    try:
        ToolRuntimePolicy.model_validate(policy.model_dump())
    except (ValidationError, ValueError) as exc:
        return safe_validation_reasons(exc, fallback="TOOL_RUNTIME_POLICY_INVALID")
    return []
