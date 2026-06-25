from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.planning.action_envelopes import (
    PLANS_ACTION_ENVELOPE_CONTRACT_REF,
    PLANS_ACTION_ENVELOPE_REQUIRED_BLOCKED_REFS,
    PLANS_ACTION_ENVELOPE_REQUIRED_REF_FIELDS,
    PlanActionEnvelope,
    build_plan_action_envelope,
    plans_action_envelope_authority_posture,
    plans_action_envelope_review_posture_rows,
    plans_action_envelope_surface_bindings,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


def test_reviewable_plan_action_envelope_requires_exact_scope_and_safe_refs() -> None:
    envelope = build_plan_action_envelope(
        source_plan_ref="plan-summary:test",
        title="Reviewable action envelope",
        safe_summary="Safe envelope summary for review.",
        evidence_refs=["evidence-ref:plans-action-envelope:test"],
    )

    payload = envelope.model_dump(mode="json")
    assert payload["contract_ref"] == PLANS_ACTION_ENVELOPE_CONTRACT_REF
    assert payload["action_envelope_ref"] == "action-envelope:plans:plan-summary-test"
    assert payload["scope_ref"] == "scope-ref:plans-action-envelope:plan-summary-test"
    assert payload["review_actions"] == ["approve", "edit", "reject", "defer"]
    assert payload["expected_receipt_refs"] == [
        "receipt-plan:plans-action-envelope:plan-summary-test"
    ]
    assert set(PLANS_ACTION_ENVELOPE_REQUIRED_BLOCKED_REFS) <= set(
        payload["blocked_state_refs"]
    )
    assert payload["exact_scope_required"] is True
    assert payload["approval_ref_authority"] is False
    assert payload["approval_grant_capture_enabled"] is False
    assert payload["action_execution_enabled"] is False
    assert payload["tool_execution_enabled"] is False
    assert payload["workflow_execution_enabled"] is False
    assert payload["browser_execution_enabled"] is False
    assert payload["connector_runtime_enabled"] is False
    assert payload["connector_write_enabled"] is False
    assert payload["shell_subprocess_execution_enabled"] is False
    assert payload["model_provider_authority_allowed"] is False
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_included"] is False


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("approval_ref_authority", True),
        ("approval_grant_capture_enabled", True),
        ("action_execution_enabled", True),
        ("tool_execution_enabled", True),
        ("workflow_execution_enabled", True),
        ("browser_execution_enabled", True),
        ("connector_runtime_enabled", True),
        ("connector_write_enabled", True),
        ("shell_subprocess_execution_enabled", True),
        ("model_provider_authority_allowed", True),
        ("safe_refs_only", False),
        ("raw_content_included", True),
    ],
)
def test_reviewable_envelope_rejects_authority_flags(
    field_name: str, value: bool
) -> None:
    envelope = build_plan_action_envelope(
        source_plan_ref="plan-summary:test",
        title="Reviewable action envelope",
        safe_summary="Safe envelope summary for review.",
        evidence_refs=["evidence-ref:plans-action-envelope:test"],
    )
    payload = envelope.model_dump(mode="json")
    payload[field_name] = value

    with pytest.raises(ValidationError):
        PlanActionEnvelope(**payload)


def test_reviewable_envelope_rejects_missing_required_blockers_and_refs() -> None:
    envelope = build_plan_action_envelope(
        source_plan_ref="plan-summary:test",
        title="Reviewable action envelope",
        safe_summary="Safe envelope summary for review.",
        evidence_refs=["evidence-ref:plans-action-envelope:test"],
    )
    payload = envelope.model_dump(mode="json")
    payload["blocked_state_refs"] = ["blocked-state:no-action-execution"]

    with pytest.raises(ValidationError, match="denied authority posture"):
        PlanActionEnvelope(**payload)

    payload = envelope.model_dump(mode="json")
    payload["evidence_refs"] = []

    with pytest.raises(ValidationError):
        PlanActionEnvelope(**payload)


@pytest.mark.parametrize(
    "unsafe_summary",
    [
        "Contains raw prompt body.",
        "Contains provider payload body.",
        "Contains raw response body.",
        "Contains account identifier details.",
    ],
)
def test_reviewable_envelope_rejects_raw_content_language(
    unsafe_summary: str,
) -> None:
    with pytest.raises(ValidationError, match="denied raw-content language"):
        build_plan_action_envelope(
            source_plan_ref="plan-summary:test",
            title="Reviewable action envelope",
            safe_summary=unsafe_summary,
            evidence_refs=["evidence-ref:plans-action-envelope:test"],
        )


def test_review_posture_rows_and_authority_posture_are_review_only() -> None:
    rows = plans_action_envelope_review_posture_rows()
    assert [row["review_action"] for row in rows] == [
        "approve",
        "edit",
        "reject",
        "defer",
    ]
    for row in rows:
        assert row["exact_scope_required"] is True
        assert row["safe_refs_required"] is True
        assert row["receipt_refs_required"] is True
        assert row["grants_execution_authority"] is False
        assert row["captures_approval_grant"] is False

    posture = plans_action_envelope_authority_posture()
    assert posture["safe_refs_only"] is True
    assert posture["exact_scope_required"] is True
    assert posture["approval_required_before_mutation"] is True
    assert posture["approval_grant_capture_enabled"] is False
    assert posture["action_execution_enabled"] is False
    assert posture["state_change_enabled"] is False
    assert posture["tool_execution_enabled"] is False
    assert posture["workflow_execution_enabled"] is False
    assert posture["browser_execution_enabled"] is False
    assert posture["connector_runtime_enabled"] is False
    assert posture["connector_write_enabled"] is False
    assert posture["shell_subprocess_execution_enabled"] is False
    assert posture["model_provider_authority_allowed"] is False
    assert posture["production_authority_enabled"] is False

    bindings = plans_action_envelope_surface_bindings()
    assert {"Today", "Plans", "Actions", "Evidence", "Memory"} == {
        row["surface"] for row in bindings
    }


def test_founder_loop_today_and_actions_bind_plan_action_envelopes(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    today = repo.today_summary()
    inbox = repo.actions_inbox()

    assert today["plans_action_envelope_contract_ref"] == (
        PLANS_ACTION_ENVELOPE_CONTRACT_REF
    )
    assert today["plans_action_envelope_required_ref_fields"] == (
        PLANS_ACTION_ENVELOPE_REQUIRED_REF_FIELDS
    )
    assert today["plans_action_envelope_required_blocked_refs"] == (
        PLANS_ACTION_ENVELOPE_REQUIRED_BLOCKED_REFS
    )
    assert today["plan_action_state"]["action_envelope_contract_ref"] == (
        PLANS_ACTION_ENVELOPE_CONTRACT_REF
    )
    assert today["plan_action_state"]["review_actions"] == [
        "approve",
        "edit",
        "reject",
        "defer",
    ]
    assert today["plan_action_state"]["approval_grant_capture_enabled"] is False

    plan = today["plans"][0]
    assert plan["action_envelope_contract_ref"] == PLANS_ACTION_ENVELOPE_CONTRACT_REF
    assert plan["action_envelope_ref"].startswith("action-envelope:plans:")
    assert plan["scope_ref"].startswith("scope-ref:plans-action-envelope:")
    assert plan["approval_requirement_ref"].startswith(
        "approval-requirement:plans-action-envelope:"
    )
    assert plan["expected_receipt_refs"]
    assert plan["idempotency_key_ref"].startswith(
        "idempotency-ref:plans-action-envelope:"
    )
    assert "blocked-state:no-action-execution" in plan["blocked_state_refs"]
    assert plan["action_execution_enabled"] is False
    assert plan["approval_grant_capture_enabled"] is False
    assert plan["raw_content_included"] is False

    action = inbox["items"][0]
    assert action["action_envelope_contract_ref"] == (
        PLANS_ACTION_ENVELOPE_CONTRACT_REF
    )
    assert action["action_envelope_ref"].startswith("action-envelope:plans:")
    assert action["action_review_actions"] == ["approve", "edit", "reject", "defer"]
    assert action["action_expected_receipt_refs"]
    assert "blocked-state:no-action-execution" in action["action_blocked_state_refs"]
    assert action["action_envelope_execution_enabled"] is False
    assert action["action_envelope_grant_capture_enabled"] is False

    timeline_item = next(
        item
        for item in today["evidence_timeline"]
        if item["item_kind"] == "plan_action_envelope_ref"
    )
    assert PLANS_ACTION_ENVELOPE_CONTRACT_REF in timeline_item["status_refs"]
    assert timeline_item["receipt_refs"]
    assert timeline_item["rollback_refs"]
    assert "blocked-state:no-action-execution" in timeline_item["blocked_states"]
