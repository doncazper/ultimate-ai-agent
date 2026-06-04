from datetime import timedelta

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.time import utc_now


def _refs(**overrides):
    from ultimate_ai_agent.core.approvals.v2 import (
        ActionKind,
        ActionRef,
        ActionRiskLevel,
        ActionSideEffectClass,
        ActorRef,
        ActorTrustLevel,
        ApprovalScope,
        ApprovalScopeKind,
        ResourceRef,
        ResourceRefKind,
    )

    data = {
        "actor": ActorRef(actor_ref="actor:user:m28", trust_level=ActorTrustLevel.user),
        "action": ActionRef(
            action_ref="action:read-metadata:m28",
            action_kind=ActionKind.read_metadata,
            risk_level=ActionRiskLevel.low,
            side_effect_class=ActionSideEffectClass.read_only_metadata,
            safe_summary="Read metadata only.",
        ),
        "resource": ResourceRef(
            resource_ref="file_ref:m28-readme",
            resource_kind=ResourceRefKind.file_ref,
            safe_label="README metadata ref.",
        ),
    }
    data["scope"] = ApprovalScope(
        scope_ref="scope:m28-single",
        scope_kind=ApprovalScopeKind.single_action,
        actor_ref=data["actor"].actor_ref,
        action_ref=data["action"].action_ref,
        resource_ref=data["resource"].resource_ref,
        expires_at=utc_now() + timedelta(minutes=15),
        replay_nonce="nonce:m28-safe",
    )
    data.update(overrides)
    return data


def _intent(**overrides):
    from ultimate_ai_agent.core.approvals.v2 import ActionIntent

    refs = _refs()
    data = {
        "intent_id": "action-intent:m28-safe",
        "actor": refs["actor"],
        "action": refs["action"],
        "resource": refs["resource"],
        "safe_summary": "Evaluate a safe read-metadata action.",
        "approval_ref": None,
        "consent_ref": None,
        "input_refs": ["file_ref:m28-readme"],
    }
    data.update(overrides)
    return ActionIntent(**data)


def _grant(**overrides):
    from ultimate_ai_agent.core.approvals.v2 import ApprovalGrant, ApprovalGrantStatus

    refs = _refs()
    data = {
        "grant_ref": "approval:m28-grant",
        "actor_ref": refs["actor"].actor_ref,
        "action_ref": refs["action"].action_ref,
        "resource_ref": refs["resource"].resource_ref,
        "scope": refs["scope"],
        "status": ApprovalGrantStatus.active_for_policy_only,
        "issued_at": utc_now(),
        "expires_at": utc_now() + timedelta(minutes=15),
        "replay_nonce": "nonce:m28-safe",
    }
    data.update(overrides)
    return ApprovalGrant(**data)


def test_default_manifest_is_contract_only_and_disables_execution_authority():
    from ultimate_ai_agent.core.approvals.v2 import build_approval_authority_v2_manifest

    manifest = build_approval_authority_v2_manifest(baseline_version="0.32.0")

    assert manifest.action_execution_enabled is False
    assert manifest.execution_authorized is False
    assert manifest.execution_performed is False
    assert manifest.tool_execution_enabled is False
    assert manifest.filesystem_mutation_enabled is False
    assert manifest.memory_write_enabled is False
    assert manifest.network_action_enabled is False
    assert manifest.browser_action_enabled is False
    assert manifest.mobile_action_enabled is False
    assert manifest.remote_execution_enabled is False
    assert manifest.plugin_enable_enabled is False
    assert manifest.model_action_enabled is False
    assert manifest.wildcard_approval_enabled is False
    assert manifest.approval_test_refs_enabled is False


def test_safe_read_metadata_policy_decision_allows_policy_only_without_execution():
    from ultimate_ai_agent.core.approvals.v2 import ApprovalDecisionStatus, evaluate_action_policy

    decision = evaluate_action_policy(_intent(), grant=_grant(), replay_nonce="nonce:m28-safe")

    assert decision.status == ApprovalDecisionStatus.allowed_for_policy
    assert decision.allowed_for_policy is True
    assert decision.execution_authorized is False
    assert decision.execution_performed is False
    assert decision.receipt_plan is not None
    assert decision.receipt_plan.execution_performed is False
    assert "ACTION_POLICY_ALLOWED_FOR_POLICY_ONLY" in decision.reason_codes


@pytest.mark.parametrize(
    ("approval_ref", "reason"),
    [
        ("approval:m28-arbitrary", "APPROVAL_REF_NOT_AUTHORITY"),
        ("approval_test_m28", "APPROVAL_TEST_REF_DENIED"),
    ],
)
def test_approval_ref_alone_and_test_refs_are_denied(approval_ref, reason):
    from ultimate_ai_agent.core.approvals.v2 import ApprovalDecisionStatus, evaluate_action_policy

    decision = evaluate_action_policy(_intent(approval_ref=approval_ref))

    assert decision.status == ApprovalDecisionStatus.denied
    assert decision.allowed_for_policy is False
    assert decision.execution_authorized is False
    assert reason in decision.reason_codes


def test_consent_ref_alone_is_not_authority():
    from ultimate_ai_agent.core.approvals.v2 import evaluate_action_policy

    decision = evaluate_action_policy(_intent(consent_ref="consent:m28"))

    assert decision.allowed_for_policy is False
    assert "CONSENT_REF_NOT_AUTHORITY" in decision.reason_codes


def test_wildcard_scope_is_denied():
    from ultimate_ai_agent.core.approvals.v2 import ApprovalScope, ApprovalScopeKind, evaluate_action_policy

    refs = _refs()
    wildcard_scope = ApprovalScope(
        scope_ref="scope:m28-wildcard",
        scope_kind=ApprovalScopeKind.blocked_wildcard,
        actor_ref=refs["actor"].actor_ref,
        action_ref="*",
        resource_ref=refs["resource"].resource_ref,
        expires_at=utc_now() + timedelta(minutes=15),
        replay_nonce="nonce:m28-wildcard",
    )
    grant = _grant(scope=wildcard_scope, action_ref="*")

    decision = evaluate_action_policy(_intent(), grant=grant, replay_nonce="nonce:m28-wildcard")

    assert decision.allowed_for_policy is False
    assert "WILDCARD_SCOPE_DENIED" in decision.reason_codes


@pytest.mark.parametrize(
    ("grant_update", "reason"),
    [
        ({"expires_at": utc_now() - timedelta(minutes=1)}, "APPROVAL_GRANT_EXPIRED"),
        ({"status": "revoked"}, "APPROVAL_GRANT_REVOKED"),
        ({"used_replay_nonces": ["nonce:m28-safe"]}, "APPROVAL_REPLAY_DETECTED"),
        ({"actor_ref": "actor:user:other"}, "APPROVAL_ACTOR_MISMATCH"),
        ({"action_ref": "action:other"}, "APPROVAL_ACTION_MISMATCH"),
        ({"resource_ref": "file_ref:other"}, "APPROVAL_RESOURCE_MISMATCH"),
    ],
)
def test_grant_expiry_revocation_replay_and_binding_mismatches_are_denied(grant_update, reason):
    from ultimate_ai_agent.core.approvals.v2 import evaluate_action_policy

    grant = _grant(**grant_update)
    decision = evaluate_action_policy(_intent(), grant=grant, replay_nonce="nonce:m28-safe")

    assert decision.allowed_for_policy is False
    assert decision.execution_authorized is False
    assert reason in decision.reason_codes


@pytest.mark.parametrize(
    ("resource_ref", "resource_kind", "reason"),
    [
        ("model:m28", "model_output_ref", "MODEL_OUTPUT_NOT_AUTHORITY"),
        ("memory:m28", "memory_ref", "MEMORY_REF_NOT_AUTHORITY"),
        ("context-pack:m28", "context_pack_ref", "CONTEXT_PACK_NOT_AUTHORITY"),
        ("tool-intent:m27", "tool_intent_ref", "TOOL_INTENT_NOT_AUTHORITY"),
    ],
)
def test_model_memory_context_and_tool_intent_refs_cannot_authorize(resource_ref, resource_kind, reason):
    from ultimate_ai_agent.core.approvals.v2 import ResourceRef, ResourceRefKind, evaluate_action_policy

    resource = ResourceRef(
        resource_ref=resource_ref,
        resource_kind=ResourceRefKind(resource_kind),
        safe_label="Non-authoritative source ref.",
    )

    decision = evaluate_action_policy(_intent(resource=resource), grant=_grant(), replay_nonce="nonce:m28-safe")

    assert decision.allowed_for_policy is False
    assert reason in decision.reason_codes


@pytest.mark.parametrize(
    "action_kind",
    [
        "file_write_planned",
        "file_delete_planned",
        "memory_write_planned",
        "tool_execution_planned",
        "network_call_planned",
        "model_call_planned",
        "browser_action_planned",
        "mobile_device_action_planned",
        "remote_execution_planned",
        "plugin_enable_planned",
        "shell_execution_blocked",
        "destructive_blocked",
    ],
)
def test_effectful_or_executing_action_kinds_are_denied(action_kind):
    from ultimate_ai_agent.core.approvals.v2 import ActionKind, ActionRef, ActionRiskLevel, ActionSideEffectClass, evaluate_action_policy

    action = ActionRef(
        action_ref=f"action:{action_kind}:m28",
        action_kind=ActionKind(action_kind),
        risk_level=ActionRiskLevel.high,
        side_effect_class=ActionSideEffectClass.execution_blocked,
        safe_summary="Blocked action plan.",
    )
    decision = evaluate_action_policy(_intent(action=action), grant=_grant(action_ref=action.action_ref), replay_nonce="nonce:m28-safe")

    assert decision.allowed_for_policy is False
    assert decision.execution_authorized is False
    assert "ACTION_KIND_DENIED" in decision.reason_codes


@pytest.mark.parametrize(
    "field_update",
    [
        {"contains_raw_prompt": True},
        {"contains_raw_model_output": True},
        {"contains_raw_file_content": True},
        {"contains_raw_transcript": True},
        {"safe_summary": "contains api_key=abc123"},
        {"metadata": {"token": "abc123"}},
    ],
)
def test_raw_or_secret_like_action_inputs_are_rejected(field_update):
    with pytest.raises(ValidationError):
        _intent(**field_update)


@pytest.mark.parametrize(
    ("field_update", "reason"),
    [
        ({"contains_raw_prompt": True}, "RAW_PROMPT_DENIED"),
        ({"contains_raw_model_output": True}, "RAW_MODEL_OUTPUT_DENIED"),
        ({"contains_raw_file_content": True}, "RAW_FILE_CONTENT_DENIED"),
        ({"contains_raw_transcript": True}, "RAW_TRANSCRIPT_DENIED"),
        ({"contains_secret_like_content": True}, "ACTION_INTENT_SECRET_CONTENT_DENIED"),
        ({"metadata": {"token": "abc123"}}, "SECRET_METADATA_DENIED"),
        ({"metadata": {"api_key": "safe-looking"}}, "SECRET_METADATA_DENIED"),
        ({"metadata_refs": ["secret:m28"]}, "SECRET_METADATA_DENIED"),
        ({"safe_summary": "contains api_key=abc123"}, "ACTION_INTENT_SECRET_CONTENT_DENIED"),
    ],
)
def test_action_policy_revalidates_model_copy_mutated_action_intents(field_update, reason):
    from ultimate_ai_agent.core.approvals.v2 import evaluate_action_policy

    decision = evaluate_action_policy(
        _intent().model_copy(update=field_update),
        grant=_grant(),
        replay_nonce="nonce:m28-safe",
    )

    assert decision.allowed_for_policy is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False
    assert reason in decision.reason_codes


@pytest.mark.parametrize(
    ("grant_update", "reason"),
    [
        ({"grant_ref": "approval_test_m28"}, "APPROVAL_TEST_REF_DENIED"),
        ({"expires_at": utc_now() - timedelta(minutes=1)}, "APPROVAL_GRANT_EXPIRED"),
        ({"status": "revoked"}, "APPROVAL_GRANT_REVOKED"),
        ({"metadata": {"token": "abc123"}}, "SECRET_METADATA_DENIED"),
        ({"metadata_refs": ["secret:m28"]}, "SECRET_METADATA_DENIED"),
    ],
)
def test_approval_grant_revalidation_blocks_model_copy_mutations(grant_update, reason):
    from ultimate_ai_agent.core.approvals.v2 import evaluate_action_policy

    decision = evaluate_action_policy(
        _intent(),
        grant=_grant().model_copy(update=grant_update),
        replay_nonce="nonce:m28-safe",
    )

    assert decision.allowed_for_policy is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False
    assert reason in decision.reason_codes


@pytest.mark.parametrize(
    ("policy_update", "reason"),
    [
        ({"safe_summary": "contains token=abc123"}, "ACTION_POLICY_SECRET_CONTENT_DENIED"),
        ({"policy_ref": "invalid-policy-ref"}, "ACTION_POLICY_REVALIDATION_FAILED"),
    ],
)
def test_action_policy_revalidation_blocks_model_copy_mutations(policy_update, reason):
    from ultimate_ai_agent.core.approvals.v2 import ActionPolicy, evaluate_action_policy

    decision = evaluate_action_policy(
        _intent(),
        grant=_grant(),
        policy=ActionPolicy().model_copy(update=policy_update),
        replay_nonce="nonce:m28-safe",
    )

    assert decision.allowed_for_policy is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False
    assert reason in decision.reason_codes
