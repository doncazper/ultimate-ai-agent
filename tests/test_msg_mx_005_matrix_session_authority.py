from __future__ import annotations

from datetime import timedelta

import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    AuthorityLeaseScope,
    AuthorityLeaseStatus,
    TrustMode,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.communications.matrix_session import (
    MATRIX_SESSION_LANES,
    MatrixSessionCommand,
    MatrixSessionOperation,
    build_exact_matrix_session_lease,
    build_matrix_session_approval_request,
    build_matrix_session_authority_action,
    build_matrix_session_lease_issue_request,
    capture_exact_matrix_session_approval,
    issue_exact_matrix_session_lease,
    matrix_session_exact_resource_refs,
    matrix_session_lane,
    matrix_session_request_fingerprint_ref,
    matrix_session_rollback_ref,
    matrix_session_start_deadline_ref,
)
from ultimate_ai_agent.core.time import utc_now


def _command(operation: MatrixSessionOperation) -> MatrixSessionCommand:
    suffix = operation.value.replace("_", "-")
    deadline = utc_now() + timedelta(minutes=2)
    values: dict[str, object] = {
        "operation": operation,
        "request_ref": f"request-ref:matrix-session:{suffix}",
        "task_ref": f"task-ref:matrix-session:{suffix}",
        "mission_ref": "mission-ref:matrix-session:exact",
        "run_ref": f"run-ref:matrix-session:{suffix}",
        "dispatch_ref": f"dispatch-ref:matrix-session:{suffix}",
        "idempotency_ref": f"idempotency-ref:matrix-session:{suffix}",
        "lease_ref": f"authority-lease-ref:matrix-session:{suffix}",
        "homeserver_ref": "homeserver-ref:matrix:bound-target",
        "endpoint_class_ref": f"endpoint-class-ref:matrix:{suffix}",
        "discovery_observation_ref": (
            "observation-ref:matrix-discovery:pending"
            if operation == MatrixSessionOperation.discovery_read
            else "observation-ref:matrix-discovery:current"
        ),
        "discovery_freshness_ref": (
            "freshness-ref:matrix-discovery:pending"
            if operation == MatrixSessionOperation.discovery_read
            else "freshness-ref:matrix-discovery:current"
        ),
        "target_ref": "target-ref:communications:matrix-exact-homeserver",
        "credential_backend_ref": "credential-backend-ref:matrix:macos-keychain-v1",
        "budget_ref": "budget-ref:communications:matrix-session-zero-cost",
        "kill_switch_ref": "kill-switch-ref:authority-lease-local",
        "safe_disable_ref": "safe-disable-ref:communications:matrix-session",
        "readiness_ref": "readiness-ref:matrix-session:current",
        "target_refs": (),
        "request_created_at": deadline - timedelta(minutes=2),
        "start_deadline": deadline,
    }
    if operation in {
        MatrixSessionOperation.credential_auth_create,
        MatrixSessionOperation.sso_callback_consume,
        MatrixSessionOperation.refresh,
        MatrixSessionOperation.logout,
        MatrixSessionOperation.revoke_all,
        MatrixSessionOperation.credential_store_rotate,
        MatrixSessionOperation.credential_delete,
    }:
        values.update(
            {
                "account_ref": "account-ref:matrix:primary",
                "device_ref": "device-ref:matrix:stable",
                "session_ref": "session-ref:matrix:primary",
                "session_generation_ref": "session-generation-ref:matrix:one",
            }
        )
    if operation in {
        MatrixSessionOperation.credential_auth_create,
        MatrixSessionOperation.sso_callback_consume,
        MatrixSessionOperation.refresh,
        MatrixSessionOperation.logout,
        MatrixSessionOperation.revoke_all,
        MatrixSessionOperation.credential_store_rotate,
        MatrixSessionOperation.credential_delete,
    }:
        values.update(
            {
                "credential_item_ref": "credential-item-ref:matrix:primary",
                "credential_version_ref": "credential-version-ref:matrix:one",
            }
        )
    if operation == MatrixSessionOperation.credential_auth_create:
        values["crypto_store_ref"] = "crypto-store-ref:matrix:primary"
    if operation in {
        MatrixSessionOperation.refresh,
        MatrixSessionOperation.credential_store_rotate,
    }:
        values["next_credential_version_ref"] = "credential-version-ref:matrix:two"
    if operation in {
        MatrixSessionOperation.sso_launch,
        MatrixSessionOperation.sso_callback_consume,
    }:
        values["redirect_target_ref"] = "redirect-target-ref:matrix:loopback"
    if operation in {
        MatrixSessionOperation.sso_launch,
        MatrixSessionOperation.sso_callback_consume,
    }:
        values["callback_attempt_ref"] = "callback-attempt-ref:matrix:one"
    if operation == MatrixSessionOperation.revoke_all:
        values["target_refs"] = (
            "device-ref:matrix:stable",
            "device-set-fingerprint-ref:matrix:current",
        )
    values["request_fingerprint_ref"] = matrix_session_request_fingerprint_ref(**values)
    return MatrixSessionCommand(**values)


def test_all_exact_lanes_bind_authority_domain_scope_and_governance() -> None:
    assert set(MATRIX_SESSION_LANES) == set(MatrixSessionOperation)
    for operation, lane in MATRIX_SESSION_LANES.items():
        command = _command(operation)
        request = build_matrix_session_lease_issue_request(command)
        assert request.scope == AuthorityLeaseScope.session.value
        assert request.mode == lane.required_mode.value
        assert request.requested_domains == {
            lane.authority_domain.value: [lane.authority_capability.value]
        }
        assert request.constraints == {
            "exact_lane_ref": lane.lane_ref,
            "exact_capability_ref": lane.capability_ref,
            "exact_adapter_ref": lane.adapter_ref,
            "exact_tool_ref": lane.tool_ref,
            "exact_request_fingerprint_ref": command.request_fingerprint_ref,
            "exact_start_deadline_ref": matrix_session_start_deadline_ref(
                command.start_deadline
            ),
            "exact_readiness_ref": command.readiness_ref,
            "exact_budget_ref": command.budget_ref,
            "exact_safe_disable_ref": command.safe_disable_ref,
            "exact_rollback_ref": matrix_session_rollback_ref(operation),
        }
        assert set(request.authority_constraints[0].allowed_refs) == set(
            matrix_session_exact_resource_refs(command)
        )


@pytest.mark.parametrize(
    "field",
    (
        "target_ref",
        "credential_backend_ref",
        "budget_ref",
        "kill_switch_ref",
        "safe_disable_ref",
    ),
)
def test_governance_ref_substitution_fails_at_command_validation(field: str) -> None:
    payload = _command(MatrixSessionOperation.discovery_read).model_dump(mode="python")
    payload[field] = f"{field.replace('_', '-')}:substituted"
    fingerprint_values = {
        key: value
        for key, value in payload.items()
        if key not in {"schema_version", "request_fingerprint_ref"}
    }
    payload["request_fingerprint_ref"] = matrix_session_request_fingerprint_ref(
        **fingerprint_values
    )
    with pytest.raises(ValueError, match="SUBSTITUTION_DENIED"):
        MatrixSessionCommand.model_validate(payload)


def test_read_lane_issues_exact_session_lease_and_coarse_messages_stays_denied(
    tmp_path,
) -> None:
    command = _command(MatrixSessionOperation.discovery_read)
    store = AuthorityLeaseStore(tmp_path)
    lease, receipt = issue_exact_matrix_session_lease(
        command,
        store=store,
        confirmed=False,
    )
    assert receipt.status == "issued"
    assert lease.scope == AuthorityLeaseScope.session.value
    assert (
        evaluate_authority_request(
            build_matrix_session_authority_action(command), [lease]
        ).outcome
        == "allow"
    )

    coarse = AuthorityLease(
        lease_ref="authority-lease-ref:matrix-session:coarse",
        mode=TrustMode.read_only,
        scope=AuthorityLeaseScope.session,
        status=AuthorityLeaseStatus.active,
        domains={AuthorityDomain.messages: [AuthorityCapability.read]},
        safe_summary="Coarse messages read lease must not authorize exact Matrix lanes.",
    )
    assert (
        evaluate_authority_request(
            build_matrix_session_authority_action(command), [coarse]
        ).outcome
        == "deny"
    )


def test_mutation_lease_requires_exact_operator_approval(tmp_path) -> None:
    command = _command(MatrixSessionOperation.credential_auth_create)
    with pytest.raises(ValueError, match="MATRIX_SESSION_LEASE_CONFIRMATION_REQUIRED"):
        issue_exact_matrix_session_lease(
            command,
            store=AuthorityLeaseStore(tmp_path / "denied"),
            confirmed=False,
        )
    lease, receipt = issue_exact_matrix_session_lease(
        command,
        store=AuthorityLeaseStore(tmp_path / "approved"),
        confirmed=True,
    )
    assert receipt.status == "issued"
    assert lease.domains == {AuthorityDomain.messages.value: ["mutate"]}


def test_exact_lease_cannot_authorize_another_lane_or_changed_request() -> None:
    now = utc_now()
    command = _command(MatrixSessionOperation.discovery_read)
    lease = build_exact_matrix_session_lease(
        command,
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    other = _command(MatrixSessionOperation.auth_methods_read)
    assert (
        evaluate_authority_request(
            build_matrix_session_authority_action(other), [lease]
        ).outcome
        == "deny"
    )

    action = build_matrix_session_authority_action(command)
    changed = action.model_copy(
        update={
            "constraints": {
                **action.constraints,
                "request_fingerprint_ref": "request-fingerprint-ref:matrix-session:changed",
            }
        }
    )
    assert evaluate_authority_request(changed, [lease]).outcome == "deny"

    omitted_resource = action.model_copy(
        update={"resource_refs": action.resource_refs[:-1]}
    )
    assert evaluate_authority_request(omitted_resource, [lease]).outcome == "deny"


def test_expired_or_wrong_scope_lease_fails_closed() -> None:
    now = utc_now()
    command = _command(MatrixSessionOperation.sso_launch)
    expired = build_exact_matrix_session_lease(
        command,
        issued_at=now - timedelta(minutes=10),
        expires_at=now - timedelta(minutes=1),
    )
    assert (
        evaluate_authority_request(
            build_matrix_session_authority_action(command), [expired], now=now
        ).outcome
        == "deny"
    )
    issue_payload = build_matrix_session_lease_issue_request(command).model_dump(
        mode="python"
    )
    issue_payload["scope"] = AuthorityLeaseScope.mission
    with pytest.raises(
        ValueError, match="AUTHORITY_LEASE_REQUESTED_REF_EXACT_BINDING_REQUIRED"
    ):
        type(build_matrix_session_lease_issue_request(command)).model_validate(
            issue_payload
        )


def test_approval_identifier_alone_cannot_authorize_and_scope_is_exact() -> None:
    command = _command(MatrixSessionOperation.logout)
    approval_request = build_matrix_session_approval_request(command)
    authority = LocalApprovalAuthority()
    unknown = authority.validate_for_request(
        approval_request,
        "approval-ref:matrix-session:identifier-only",
    )
    assert unknown.allowed is False
    assert unknown.reason_codes == ["APPROVAL_REF_UNKNOWN"]

    approval_ref = capture_exact_matrix_session_approval(
        command,
        approval_authority=authority,
        confirmed=True,
    )
    assert (
        authority.validate_for_request(approval_request, approval_ref).allowed is True
    )
    wrong = approval_request.model_copy(
        update={
            "resource_refs": [
                *approval_request.resource_refs[:-1],
                "target-ref:matrix-session:substituted",
            ]
        }
    )
    assert authority.validate_for_request(wrong, approval_ref).allowed is False


def test_unknown_or_unlisted_matrix_action_remains_denied() -> None:
    command = _command(MatrixSessionOperation.discovery_read)
    now = utc_now()
    lease = build_exact_matrix_session_lease(
        command,
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    unknown = AuthorityActionRequest(
        action_ref="authority-action-ref:matrix-session:unknown",
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.read,
        safe_summary="Unknown Matrix action must remain denied.",
        capability_ref="authority-capability-ref:matrix-unknown-v1",
        lane_ref="authority-lane-ref:matrix-unknown",
        adapter_ref="authority-adapter-ref:matrix-unknown-v1",
        constraints={
            "tool_ref": "tool-ref:matrix-unknown:v1",
            "request_fingerprint_ref": command.request_fingerprint_ref,
        },
    )
    assert evaluate_authority_request(unknown, [lease]).outcome == "deny"


def test_exact_binding_rejects_incomplete_constraints_and_target_substitution() -> None:
    command = _command(MatrixSessionOperation.discovery_read)
    valid = build_matrix_session_lease_issue_request(command).model_dump(mode="python")
    valid["authority_constraints"] = valid["authority_constraints"][1:]
    with pytest.raises(
        ValueError, match="AUTHORITY_LEASE_REQUESTED_REF_EXACT_BINDING_REQUIRED"
    ):
        AuthorityLeaseIssueRequest.model_validate(valid)

    substituted = build_matrix_session_lease_issue_request(command).model_dump(
        mode="python"
    )
    resource_constraint = substituted["authority_constraints"][0]
    resource_constraint["allowed_refs"].append(
        "target-ref:communications:unbound-external-host"
    )
    with pytest.raises(
        ValueError, match="AUTHORITY_LEASE_REQUESTED_REF_EXACT_BINDING_REQUIRED"
    ):
        AuthorityLeaseIssueRequest.model_validate(substituted)


def test_read_lane_rejects_unnecessary_action_approval() -> None:
    command = _command(MatrixSessionOperation.discovery_read)
    with pytest.raises(ValueError, match="MATRIX_SESSION_READ_APPROVAL_FORBIDDEN"):
        capture_exact_matrix_session_approval(
            command,
            approval_authority=LocalApprovalAuthority(),
            confirmed=True,
        )


def test_session_fingerprint_and_operation_scope_are_immutable() -> None:
    command = _command(MatrixSessionOperation.sso_callback_consume)
    changed_callback = command.model_dump(mode="python")
    changed_callback["callback_attempt_ref"] = "callback-attempt-ref:matrix:two"
    with pytest.raises(ValueError, match="MATRIX_SESSION_REQUEST_FINGERPRINT_MISMATCH"):
        MatrixSessionCommand.model_validate(changed_callback)
    missing_redirect = command.model_dump(mode="python")
    missing_redirect["redirect_target_ref"] = None
    with pytest.raises(
        ValueError, match="MATRIX_SESSION_EXACT_REDIRECT_SCOPE_REQUIRED"
    ):
        MatrixSessionCommand.model_validate(missing_redirect)


def test_lane_constants_match_accepted_exact_binding_names() -> None:
    assert matrix_session_lane(MatrixSessionOperation.discovery_read).lane_ref == (
        "authority-lane-ref:matrix-discovery-read"
    )
    assert matrix_session_lane(
        MatrixSessionOperation.sso_callback_consume
    ).tool_ref == ("tool-ref:matrix-session-sso-callback-consume:v1")
