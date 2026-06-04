from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationReceiptPlan, ToolInvocationRequest
from ultimate_ai_agent.core.tools.runtime.validation import NOOP_TOOL_REF


def build_tool_invocation_receipt_plan(request: ToolInvocationRequest) -> ToolInvocationReceiptPlan:
    suffix = request.invocation_id.split(":", 1)[-1]
    return ToolInvocationReceiptPlan(
        receipt_plan_ref=f"tool-runtime-receipt:{suffix}",
        invocation_id=request.invocation_id,
        tool_ref=NOOP_TOOL_REF,
    )
