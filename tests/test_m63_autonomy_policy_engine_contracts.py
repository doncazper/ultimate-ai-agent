from typing import Any
import pytest

from ultimate_ai_agent.core.autonomy import (
    AutonomyAuthorityMode,
    AutonomyPolicyEvaluationRequest,
    AutonomyPolicyEnginePolicy,
    AutonomyPolicyRule,
    AutonomyRiskClass,
    ScopedAutonomySessionRequest,
    ScopedAutonomySessionScope,
    build_autonomy_policy_decision,
    validate_autonomy_policy_evaluation_request,
    validate_autonomy_policy_rule,
)
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)


def _scope(**overrides: Any) -> Any:
    data = {
        "scope_ref": "autonomy-session-scope:m63-local-review",
        "actor_ref": "actor:local-reviewer",
        "resource_refs": ["resource:local-prototype"],
        "capability_refs": ["capability:observe-only-review"],
        "allowlist_refs": ["allowlist:m63-local-review"],
        "max_duration_seconds": 900,
        "risk_class": AutonomyRiskClass.low,
        "revocation_ref": "revocation:m63-local-review",
        "audit_ref": "audit:m63-local-review",
        "replay_ref": "replay:m63-local-review",
    }
    data.update(overrides)
    return ScopedAutonomySessionScope(**data)


def _session_request(**overrides: Any) -> Any:
    data = {
        "session_request_ref": "autonomy-session-request:m63-local-review",
        "requested_mode": AutonomyAuthorityMode.dry_run_plan,
        "scope": _scope(),
    }
    data.update(overrides)
    return ScopedAutonomySessionRequest(**data)


def _rule(**overrides: Any) -> Any:
    data = {
        "rule_ref": "autonomy-policy-rule:m63-local-review",
        "allowed_actor_refs": ["actor:local-reviewer"],
        "allowed_resource_refs": ["resource:local-prototype"],
        "allowed_capability_refs": ["capability:observe-only-review"],
        "required_allowlist_refs": ["allowlist:m63-local-review"],
        "max_mode": AutonomyAuthorityMode.dry_run_plan,
        "max_risk_class": AutonomyRiskClass.low,
        "max_duration_seconds": 900,
        "revocation_required": True,
        "audit_replay_required": True,
        "dry_run_only": True,
    }
    data.update(overrides)
    return AutonomyPolicyRule(**data)


def _policy(**overrides: Any) -> Any:
    data = {
        "policy_ref": "autonomy-policy:m63-local-review",
        "policy_version_ref": "autonomy-policy-version:m63-v1",
        "rules": [_rule()],
    }
    data.update(overrides)
    return AutonomyPolicyEnginePolicy(**data)


def _evaluation_request(**overrides: Any) -> Any:
    data = {
        "evaluation_request_ref": "autonomy-policy-evaluation:m63-local-review",
        "policy": _policy(),
        "session_request": _session_request(),
    }
    data.update(overrides)
    return AutonomyPolicyEvaluationRequest(**data)


def test_autonomy_policy_rule_is_contract_only_and_bound() -> None:
    rule = validate_autonomy_policy_rule(_rule())

    assert rule.dry_run_only is True
    assert rule.revocation_required is True
    assert rule.audit_replay_required is True
    assert rule.allowed_actor_refs == ["actor:local-reviewer"]
    assert rule.required_allowlist_refs == ["allowlist:m63-local-review"]

    with pytest.raises(ValueError, match="POLICY_ACTOR_BINDING_REQUIRED"):
        validate_autonomy_policy_rule(_rule(allowed_actor_refs=[]))

    with pytest.raises(ValueError, match="POLICY_ALLOWLIST_REQUIRED"):
        validate_autonomy_policy_rule(_rule(required_allowlist_refs=[]))


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("dry_run_only", "DRY_RUN_FIRST_REQUIRED"),
        ("policy_activation_enabled", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
        ("session_start_enabled", "AUTONOMY_SESSION_START_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("network_tool_enabled", "NETWORK_TOOL_DENIED"),
        ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
        ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
        ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("model_provider_call_enabled", "MODEL_PROVIDER_CALL_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_autonomy_policy_rule_denies_runtime_flags(field: str, reason: str) -> None:
    value = False if field == "dry_run_only" else True

    with pytest.raises(ValueError, match=reason):
        validate_autonomy_policy_rule(_rule(**{field: value}))


def test_autonomy_policy_decision_is_review_only_and_non_authoritative() -> None:
    decision = build_autonomy_policy_decision(_evaluation_request())

    assert decision.contract_valid_for_review is True
    assert decision.policy_matched is True
    assert decision.policy_allows_review is True
    assert decision.authority_granted is False
    assert decision.session_started is False
    assert decision.execution_performed is False
    assert decision.side_effects_performed == []
    assert decision.reason_codes == ["M63_AUTONOMY_POLICY_MATCH_REVIEW_ONLY"]
    assert "private key" not in str(decision.model_dump()).lower()


@pytest.mark.parametrize(
    ("request_update", "reason"),
    [
        ({"requested_mode": AutonomyAuthorityMode.ask_before_every_action}, "POLICY_MODE_EXCEEDS_RULE"),
        ({"scope": _scope(actor_ref="actor:other")}, "POLICY_ACTOR_NOT_ALLOWED"),
        ({"scope": _scope(resource_refs=["resource:other"])}, "POLICY_RESOURCE_NOT_ALLOWED"),
        (
            {"scope": _scope(capability_refs=["capability:tool-execution"])},
            "POLICY_CAPABILITY_NOT_ALLOWED",
        ),
        ({"scope": _scope(allowlist_refs=["allowlist:other"])}, "POLICY_ALLOWLIST_NOT_SATISFIED"),
        ({"scope": _scope(max_duration_seconds=901)}, "POLICY_DURATION_EXCEEDED"),
        ({"scope": _scope(risk_class=AutonomyRiskClass.medium)}, "POLICY_RISK_EXCEEDED"),
    ],
)
def test_autonomy_policy_decision_denies_out_of_scope_requests(request_update: Any, reason: str) -> None:
    decision = build_autonomy_policy_decision(
        _evaluation_request(session_request=_session_request(**request_update))
    )

    assert decision.policy_matched is False
    assert decision.policy_allows_review is False
    assert decision.authority_granted is False
    assert reason in decision.reason_codes


def test_autonomy_policy_denies_approval_refs_as_authority() -> None:
    with pytest.raises(ValueError, match="APPROVAL_TEST_REF_DENIED"):
        validate_autonomy_policy_evaluation_request(
            _evaluation_request(approval_test_ref="approval_test_:m63")
        )

    request = _evaluation_request(approval_ref="approval:m63-review-only")
    decision = build_autonomy_policy_decision(request)

    assert decision.authority_granted is False
    assert "APPROVAL_REF_IDENTIFIER_ONLY" in decision.reason_codes


def test_autonomy_policy_revalidates_model_copy_mutated_objects() -> None:
    safe_request = _evaluation_request()
    mutated_rule = safe_request.policy.rules[0].model_copy(update={"execution_enabled": True})
    mutated_policy = safe_request.policy.model_copy(update={"rules": [mutated_rule]})
    mutated_request = safe_request.model_copy(
        update={
            "policy": mutated_policy,
            "policy_activation_requested": True,
            "metadata": {"token": "abcde12345678901234"},
        }
    )

    with pytest.raises(ValueError, match="SECRET_LIKE_AUTONOMY_POLICY_CONTENT_DENIED"):
        validate_autonomy_policy_evaluation_request(mutated_request)


def test_autonomy_policy_decision_records_matching_authority_lease_scope() -> None:
    lease = AuthorityLease(
        lease_ref="authority-lease-ref:m63-workspace-write",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        safe_summary="M63 test lease grants workspace write for review visibility.",
    )
    authority_action_request = AuthorityActionRequest(
        action_ref="authority-action-ref:m63-workspace-write",
        domain=AuthorityDomain.workspace,
        capability=AuthorityCapability.write,
        requested_mode=TrustMode.ask_before_changes,
        safe_summary="Evaluate M63 workspace write against an active AuthorityLease.",
        draft_fallback_available=True,
        rollback_ref="rollback-ref:m63-workspace-write",
        safe_disable_ref="safe-disable-ref:m63-workspace-write",
    )

    decision = build_autonomy_policy_decision(
        _evaluation_request(
            authority_action_request=authority_action_request,
            active_authority_leases=[lease],
        )
    )

    assert decision.policy_matched is True
    assert decision.policy_allows_review is True
    assert decision.authority_granted is False
    assert decision.session_started is False
    assert decision.execution_performed is False
    assert decision.authority_decision_outcome == AuthorityDecisionOutcome.ask.value
    assert decision.authority_lease_ref == lease.lease_ref
    assert decision.authority_known is True
    assert decision.authority_decision_allows_review is True
    assert decision.authority_receipt_ref is not None
    assert "AUTHORITY_LEASE_SCOPE_MATCHED_FOR_REVIEW" in decision.reason_codes


def test_autonomy_policy_decision_blocks_review_when_authority_scope_is_missing() -> None:
    authority_action_request = AuthorityActionRequest(
        action_ref="authority-action-ref:m63-workspace-write-missing-lease",
        domain=AuthorityDomain.workspace,
        capability=AuthorityCapability.write,
        requested_mode=TrustMode.ask_before_changes,
        safe_summary="Evaluate M63 workspace write without an active AuthorityLease.",
        draft_fallback_available=True,
        rollback_ref="rollback-ref:m63-workspace-write-missing-lease",
        safe_disable_ref="safe-disable-ref:m63-workspace-write-missing-lease",
    )

    decision = build_autonomy_policy_decision(
        _evaluation_request(authority_action_request=authority_action_request)
    )

    assert decision.policy_matched is True
    assert decision.policy_allows_review is False
    assert decision.authority_granted is False
    assert (
        decision.authority_decision_outcome
        == AuthorityDecisionOutcome.degrade_to_draft.value
    )
    assert decision.authority_lease_ref is None
    assert decision.authority_known is False
    assert decision.authority_decision_allows_review is False
    assert decision.authority_receipt_ref is None
    assert "reason-ref:authority:no-active-lease-for-domain-capability" in (
        decision.authority_reason_refs
    )
    assert "AUTHORITY_LEASE_SCOPE_NOT_GRANTED_FOR_REVIEW" in decision.reason_codes
