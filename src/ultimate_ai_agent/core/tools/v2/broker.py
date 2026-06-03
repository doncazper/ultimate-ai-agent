from typing import Mapping, Optional

from ultimate_ai_agent.core.tools.v2.catalog import build_default_tool_catalog
from ultimate_ai_agent.core.tools.v2.contracts import ToolCatalogEntry, ToolIntent, ToolIntentDecision, ToolReceiptPlan
from ultimate_ai_agent.core.tools.v2.enums import (
    ToolAuthorityLevel,
    ToolExecutionMode,
    ToolIntentDecisionStatus,
)
from ultimate_ai_agent.core.tools.v2.validation import (
    has_side_effects,
    risk_rank,
    tool_target_reason_codes,
)


def evaluate_tool_intent(
    intent: ToolIntent,
    catalog: Optional[Mapping[str, ToolCatalogEntry]] = None,
) -> ToolIntentDecision:
    catalog = catalog or build_default_tool_catalog()
    entry = catalog.get(intent.tool_id)
    reasons: list[str] = []

    if entry is None:
        reasons.append("UNKNOWN_TOOL_DENIED")
    else:
        reasons.extend(tool_target_reason_codes(intent.target.target_ref, intent.target.target_kind))
        if entry.target_kind != intent.target.target_kind:
            reasons.append("TOOL_TARGET_KIND_MISMATCH_DENIED")
        if intent.requested_execution_mode != ToolExecutionMode.preview_only:
            reasons.append("TOOL_EXECUTION_MODE_DENIED")
        if intent.requested_execution_mode not in entry.allowed_execution_modes:
            reasons.append("TOOL_EXECUTION_MODE_DENIED")
        if risk_rank(intent.declared_risk_class) < risk_rank(entry.risk_class):
            reasons.append("TOOL_RISK_DOWNGRADE_DENIED")
        catalog_effects = set(entry.side_effects)
        declared_effects = set(intent.declared_side_effects)
        if catalog_effects - declared_effects:
            reasons.append("TOOL_SIDE_EFFECTS_HIDDEN_DENIED")
        if has_side_effects(list(catalog_effects | declared_effects)):
            reasons.append("TOOL_SIDE_EFFECTS_DENIED")

    if intent.approval_ref:
        reasons.append("APPROVAL_REF_NOT_AUTHORITY")
    if intent.context_pack_refs:
        reasons.append("CONTEXT_PACK_NOT_AUTHORITY")
    if intent.authority_level not in {ToolAuthorityLevel.validation_only, ToolAuthorityLevel.preview_only}:
        reasons.append("TOOL_AUTHORITY_LEVEL_DENIED")

    reasons = list(dict.fromkeys(reasons))
    if reasons:
        return ToolIntentDecision(
            decision_id=f"tool-decision:{intent.intent_id}",
            intent_id=intent.intent_id,
            tool_id=intent.tool_id,
            status=ToolIntentDecisionStatus.denied,
            preview_allowed=False,
            execution_allowed=False,
            approval_required=bool(entry and entry.approval_requirement.value.endswith("required")),
            reason_codes=reasons,
            safe_message="Tool intent was denied by M27 validation-only policy.",
        )

    return ToolIntentDecision(
        decision_id=f"tool-decision:{intent.intent_id}",
        intent_id=intent.intent_id,
        tool_id=intent.tool_id,
        status=ToolIntentDecisionStatus.preview_allowed,
        preview_allowed=True,
        execution_allowed=False,
        reason_codes=["SAFE_PREVIEW_INTENT_ACCEPTED"],
        safe_message="Tool intent is safe for metadata-only preview. No execution was performed.",
        receipt_plan=ToolReceiptPlan(
            receipt_plan_ref=f"tool-receipt-plan:{intent.intent_id}",
            intent_id=intent.intent_id,
            tool_id=intent.tool_id,
            execution_performed=False,
            side_effects_performed=[],
            safe_summary="Receipt plan for validation-only tool intent preview.",
        ),
    )
