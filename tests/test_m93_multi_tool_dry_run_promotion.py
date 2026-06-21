from typing import Any
import pytest

from tests.test_m92_low_risk_tool_autonomy_single_session import _request as _m92_request
from ultimate_ai_agent.core.autonomy import (
    MultiToolDryRunPromotionPolicy,
    MultiToolDryRunPromotionRequest,
    MultiToolDryRunPromotionStatus,
    build_low_risk_tool_autonomy_single_session_decision,
    build_multi_tool_dry_run_promotion_decision,
    validate_multi_tool_dry_run_promotion_decision,
    validate_multi_tool_dry_run_promotion_policy,
    validate_multi_tool_dry_run_promotion_request,
)


def _m92_decision() -> Any:
    return build_low_risk_tool_autonomy_single_session_decision(_m92_request())


def _request(**overrides: Any) -> Any:
    m92_decision = overrides.pop("m92_single_session_decision", _m92_decision())
    data = {
        "request_ref": "multi-tool-dry-run-promotion-request:m93",
        "promotion_ref": "multi-tool-dry-run-promotion:m93-review-only",
        "m92_single_session_decision_ref": m92_decision.decision_ref,
        "m92_single_session_decision": m92_decision,
        "actor_ref": m92_decision.actor_ref,
        "promotion_approval_ref": "approval:promotion-m93-exact-plan",
        "dry_run_plan_ref": "dry-run-plan:m93-redacted-review",
        "dry_run_plan_hash_ref": "plan-hash:m93-dry-run",
        "dry_run_plan_hash": "sha256:m93-equivalent-plan-0001",
        "real_run_plan_ref": "real-run-plan:m93-redacted-review",
        "real_run_plan_hash_ref": "plan-hash:m93-real-run",
        "real_run_plan_hash": "sha256:m93-equivalent-plan-0001",
        "safe_execution_scope_ref": m92_decision.safe_execution_scope_ref,
        "audit_ref": m92_decision.audit_ref,
        "replay_ref": m92_decision.replay_ref,
        "safe_tool_refs": [
            m92_decision.safe_tool_ref,
            "tool:m93-low-risk-review-only-second-tool",
        ],
        "prior_milestone_refs": ["milestone:M69", "milestone:M91", "milestone:M92"],
        "safe_promotion_summary": (
            "Compare a dry-run plan and proposed real-run plan for review without execution."
        ),
    }
    data.update(overrides)
    return MultiToolDryRunPromotionRequest(**data)


def test_m93_multi_tool_dry_run_promotion_is_review_only() -> None:
    decision = build_multi_tool_dry_run_promotion_decision(_request())

    assert decision.status == MultiToolDryRunPromotionStatus.promotion_ready_for_review
    assert decision.review_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.safe_refs_only is True
    assert decision.m92_single_session_revalidated is True
    assert decision.dry_run_plan_bound is True
    assert decision.real_run_plan_bound is True
    assert decision.dry_run_real_run_equivalent is True
    assert decision.exact_promotion_approval_bound is True
    assert decision.wildcard_approval_denied is True
    assert decision.promotion_allowed_for_review is True
    assert decision.execution_authorized is False
    assert decision.real_run_execution_authorized is False
    assert decision.tool_execution_authorized is False
    assert decision.session_start_authorized is False
    assert decision.execution_performed is False
    assert decision.real_run_execution_performed is False
    assert decision.tool_execution_performed is False
    assert decision.session_start_performed is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.store_safe_summary_only is True
    assert decision.receipt_plan.store_plan_hash_refs_only is True
    assert decision.receipt_plan.execution_performed is False
    assert decision.reason_codes == [
        "M93_MULTI_TOOL_DRY_RUN_REAL_RUN_PROMOTION_REVIEW_ONLY",
        "M93_DRY_RUN_REAL_RUN_EQUIVALENCE_REQUIRED",
        "M93_EXACT_PROMOTION_APPROVAL_REQUIRED",
        "M93_PLAN_HASH_BINDING_REQUIRED",
        "M93_NO_UNAPPROVED_REAL_EXECUTION",
        "M94_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("execution_requested", "EXECUTION_DENIED"),
        ("real_run_execution_requested", "M93_REAL_RUN_EXECUTION_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("autonomous_execution_requested", "AUTONOMOUS_EXECUTION_DENIED"),
        ("session_start_requested", "SESSION_START_DENIED"),
        ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
        ("command_execution_requested", "COMMAND_EXECUTION_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("subprocess_execution_requested", "SUBPROCESS_EXECUTION_DENIED"),
        ("filesystem_mutation_requested", "FILESYSTEM_MUTATION_DENIED"),
        ("network_access_requested", "NETWORK_ACCESS_DENIED"),
        ("browser_click_requested", "BROWSER_CLICK_DENIED"),
        ("browser_form_requested", "BROWSER_FORM_DENIED"),
        ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
        ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
        ("model_call_requested", "MODEL_CALL_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
        ("contains_raw_tool_payload", "M93_RAW_TOOL_PAYLOAD_DENIED"),
        ("contains_raw_provider_payload", "M93_RAW_PROVIDER_PAYLOAD_DENIED"),
        ("contains_raw_prompt", "RAW_PROMPT_DENIED"),
        ("contains_secret", "SECRET_LIKE_DRY_RUN_PROMOTION_CONTENT_DENIED"),
    ],
)
def test_m93_denies_execution_authority_and_raw_fields(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_multi_tool_dry_run_promotion_request(_request(**{field: True}))


def test_m93_requires_exact_plan_equivalence_and_bindings() -> None:
    for update, reason in [
        ({"real_run_plan_hash": "sha256:m93-different-plan-0002"}, "M93_DRY_RUN_REAL_RUN_PLAN_HASH_MISMATCH"),
        ({"m92_single_session_decision_ref": "low-risk-tool-autonomy-single-session-decision:other"}, "M93_M92_SINGLE_SESSION_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M93_ACTOR_BINDING_MISMATCH"),
        ({"safe_execution_scope_ref": "scope:other"}, "M93_SAFE_EXECUTION_SCOPE_BINDING_MISMATCH"),
        ({"safe_tool_refs": ["tool:m93-one"]}, "M93_MULTI_TOOL_PLAN_REQUIRED"),
        ({"safe_tool_refs": ["tool:m93-one", "tool:m93-two"]}, "M93_SAFE_TOOL_BINDING_MISMATCH"),
        ({"promotion_approval_ref": "approval_test_:m93"}, "APPROVAL_TEST_REF_DENIED"),
        ({"promotion_approval_ref": "approval:promotion-wildcard-all"}, "M93_WILDCARD_APPROVAL_DENIED"),
        ({"promotion_approval_ref": "approval:scope-only"}, "M93_EXACT_PROMOTION_APPROVAL_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            build_multi_tool_dry_run_promotion_decision(_request(**update))


def test_m93_revalidates_model_copy_mutated_m92_decision() -> None:
    with pytest.raises(ValueError, match="TOOL_EXECUTION_DENIED"):
        build_multi_tool_dry_run_promotion_decision(
            _request(
                m92_single_session_decision=_m92_decision().model_copy(
                    update={"tool_execution_authorized": True}
                )
            )
        )


def test_m93_revalidates_decision_and_receipt_flags() -> None:
    decision = build_multi_tool_dry_run_promotion_decision(_request())
    for update, reason in [
        ({"execution_authorized": True}, "EXECUTION_DENIED"),
        ({"real_run_execution_authorized": True}, "M93_REAL_RUN_EXECUTION_DENIED"),
        ({"tool_execution_authorized": True}, "TOOL_EXECUTION_DENIED"),
        ({"session_start_authorized": True}, "SESSION_START_DENIED"),
        ({"background_worker_started": True}, "BACKGROUND_WORKER_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_multi_tool_dry_run_promotion_decision(decision.model_copy(update=update))

    with pytest.raises(ValueError, match="M93_RAW_TOOL_PAYLOAD_DENIED"):
        validate_multi_tool_dry_run_promotion_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_raw_tool_payload": True}
                    )
                }
            )
        )


def test_m93_policy_denies_promotion_enablement_and_execution_flags() -> None:
    for field, reason in [
        ("real_run_promotion_enabled", "M93_REAL_RUN_PROMOTION_ENABLEMENT_DENIED"),
        ("real_run_execution_enabled", "M93_REAL_RUN_EXECUTION_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
        ("session_start_enabled", "SESSION_START_DENIED"),
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("browser_click_enabled", "BROWSER_CLICK_DENIED"),
        ("browser_form_enabled", "BROWSER_FORM_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_multi_tool_dry_run_promotion_policy(
                MultiToolDryRunPromotionPolicy(**{field: True})
            )
