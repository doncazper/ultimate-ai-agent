from ultimate_ai_agent.core.openwebui_bridge.contracts import OpenWebUIBridgeReceiptPlan
from ultimate_ai_agent.core.openwebui_bridge.validation import (
    validate_openwebui_bridge_receipt_plan,
)


def build_openwebui_bridge_receipt_plan(
    session_ref: str,
    receipt_plan_id: str = "openwebui_bridge_receipt_plan_m21",
) -> OpenWebUIBridgeReceiptPlan:
    plan = OpenWebUIBridgeReceiptPlan(
        receipt_plan_id=receipt_plan_id,
        session_ref=session_ref,
        safe_summary="OpenWebUI bridge receipts require redacted summary-only metadata.",
    )
    validate_openwebui_bridge_receipt_plan(plan)
    return plan
