from ultimate_ai_agent.core.mobile_companion.contracts import MobileReceiptPlan


def build_mobile_receipt_plan(receipt_ref: str, safe_summary: str) -> MobileReceiptPlan:
    return MobileReceiptPlan(receipt_ref=receipt_ref, safe_summary=safe_summary)
