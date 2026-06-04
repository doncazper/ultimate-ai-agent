from typing import Iterable

from ultimate_ai_agent.core.tools.runtime.contracts import (
    ToolInvocationDecision,
    ToolInvocationRequest,
    ToolInvocationResult,
    ToolRuntimePolicy,
)
from ultimate_ai_agent.core.tools.runtime.enums import ToolInvocationStatus, ToolRuntimeAuthorityLevel
from ultimate_ai_agent.core.tools.runtime.noop import invoke_noop_tool
from ultimate_ai_agent.core.tools.runtime.policy import validate_runtime_policy, validate_tool_invocation_request
from ultimate_ai_agent.core.tools.runtime.receipts import build_tool_invocation_receipt_plan
from ultimate_ai_agent.core.tools.runtime.validation import NOOP_TOOL_REF, validate_tool_runtime_ref


def _safe_invocation_id(value: str) -> str:
    try:
        validate_tool_runtime_ref(value, "invocation_id")
    except ValueError:
        return "tool-runtime-invocation:denied"
    return value


def _denied_decision(request: ToolInvocationRequest, reasons: list[str]) -> ToolInvocationDecision:
    status = ToolInvocationStatus.replay_detected if "TOOL_RUNTIME_REPLAY_DETECTED" in reasons else ToolInvocationStatus.denied
    invocation_id = _safe_invocation_id(request.invocation_id)
    return ToolInvocationDecision(
        decision_id=f"tool-runtime-decision:{invocation_id.split(':', 1)[-1]}",
        invocation_id=invocation_id,
        tool_ref=NOOP_TOOL_REF,
        status=status,
        invocation_allowed=False,
        execution_performed=False,
        reason_codes=list(dict.fromkeys(reasons)),
        safe_message="Tool runtime invocation denied by M31 no-op-only policy.",
    )


def evaluate_tool_invocation(
    request: ToolInvocationRequest,
    policy: ToolRuntimePolicy | None = None,
    replay_keys_seen: Iterable[str] | None = None,
) -> ToolInvocationDecision:
    active_policy = policy or ToolRuntimePolicy()
    reasons = validate_runtime_policy(active_policy)
    reasons.extend(validate_tool_invocation_request(request))
    if active_policy.replay_protection_required and request.replay_key in set(replay_keys_seen or []):
        reasons.append("TOOL_RUNTIME_REPLAY_DETECTED")
    reasons = list(dict.fromkeys(reasons))
    if reasons:
        return _denied_decision(request, reasons)

    output = invoke_noop_tool(request)
    receipt = build_tool_invocation_receipt_plan(request)
    result = ToolInvocationResult(
        result_id=f"tool-runtime-result:{request.invocation_id.split(':', 1)[-1]}",
        invocation_id=request.invocation_id,
        output=output,
        receipt_plan=receipt,
    )
    return ToolInvocationDecision(
        decision_id=f"tool-runtime-decision:{request.invocation_id.split(':', 1)[-1]}",
        invocation_id=request.invocation_id,
        tool_ref=NOOP_TOOL_REF,
        status=ToolInvocationStatus.noop_completed,
        invocation_allowed=True,
        execution_performed=True,
        authority_level=ToolRuntimeAuthorityLevel.noop_runtime_only,
        reason_codes=["NOOP_TOOL_COMPLETED"],
        safe_message="Deterministic no-op tool invocation completed without side effects.",
        result=result,
        receipt_plan=receipt,
    )
