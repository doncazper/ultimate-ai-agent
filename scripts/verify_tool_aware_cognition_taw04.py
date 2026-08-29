from __future__ import annotations

from ultimate_ai_agent.core.capabilities import (
    AwarenessEvidenceStatus,
    ChatShadowEvidence,
    ShadowChatAction,
    build_catalog_injection_cases,
    build_chat_shadow_inspection,
    evaluate_chat_shadow,
)
from ultimate_ai_agent.core.capabilities.chat_shadow import (
    TAW04_CATALOG_INJECTION_FIELD_PATHS,
)


def verify() -> None:
    decision = evaluate_chat_shadow(
        ChatShadowEvidence(
            awareness_status=AwarenessEvidenceStatus.over_budget,
        )
    )
    if (
        decision.action != ShadowChatAction.preserve_direct_chat
        or not decision.safe_disable_engaged
        or decision.operator_visible_route_ref != decision.legacy_route_ref
        or not decision.ordinary_no_tool_chat_preserved
    ):
        raise RuntimeError("TAW-04 verifier did not preserve safe direct chat")
    if (
        any(
            (
                decision.operator_visible_routing_changed,
                decision.model_context_changed,
                decision.prompt_assembly_performed,
                decision.skill_activation_performed,
                decision.proposal_constructed,
                decision.approval_requested,
                decision.execution_performed,
                decision.provider_call_performed,
                decision.network_access_performed,
                decision.web_fetch_performed,
                decision.authority_granted,
            )
        )
        or decision.extra_model_call_count != 0
    ):
        raise RuntimeError("TAW-04 verifier detected authority or routing expansion")
    projection = build_chat_shadow_inspection(decision)
    if projection.decision_fingerprint_ref != decision.decision_fingerprint_ref:
        raise RuntimeError("TAW-04 verifier detected inspection parity drift")
    cases = build_catalog_injection_cases()
    if tuple(item.field_path for item in cases) != (
        TAW04_CATALOG_INJECTION_FIELD_PATHS
    ) or any(item.model_visible_in_shadow for item in cases):
        raise RuntimeError("TAW-04 verifier detected injection census drift")


def main() -> int:
    verify()
    print("Tool-aware cognition TAW-04 chat shadow verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
