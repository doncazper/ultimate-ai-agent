from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.communications.matrix_crypto import (
    MATRIX_CRYPTO_LANES,
    MatrixCryptoCommand,
    MatrixCryptoOperation,
    MatrixCryptoPosture,
    MatrixCryptoRuntimeStatus,
    build_default_matrix_crypto_posture,
    build_matrix_crypto_approval_request,
    build_matrix_crypto_authority_action,
    build_matrix_crypto_availability,
    build_matrix_crypto_lease_issue_request,
    build_matrix_crypto_proposal,
    capture_exact_matrix_crypto_approval,
    capture_exact_matrix_crypto_lease_approval,
    issue_exact_matrix_crypto_lease,
    matrix_crypto_request_fingerprint_ref,
    matrix_crypto_rollback_ref,
)
from ultimate_ai_agent.core.time import utc_now


def _command(
    operation: MatrixCryptoOperation = MatrixCryptoOperation.backup_status_read,
    **overrides: object,
) -> MatrixCryptoCommand:
    now = utc_now()
    values: dict[str, object] = {
        "operation": operation,
        "request_ref": "request-ref:msg-mx-007:test",
        "task_ref": "task-ref:msg-mx-007:test",
        "mission_ref": "mission-ref:msg-mx-007:test",
        "run_ref": "run-ref:msg-mx-007:test",
        "dispatch_ref": f"dispatch-ref:msg-mx-007:{operation.value}",
        "idempotency_ref": f"idempotency-ref:msg-mx-007:{operation.value}",
        "lease_ref": f"authority-lease-ref:msg-mx-007:{operation.value}",
        "account_ref": "account-ref:matrix:test",
        "device_ref": "device-ref:matrix:test",
        "crypto_store_ref": "crypto-store-ref:matrix:test",
        "store_schema_ref": "store-schema-ref:matrix:test:v1",
        "store_generation_ref": "store-generation-ref:matrix:test:1",
        "crypto_key_item_ref": "crypto-key-item-ref:matrix:test",
        "crypto_key_version_ref": "crypto-key-version-ref:matrix:test:1",
        "cross_signing_generation_ref": "cross-signing-generation-ref:matrix:test:1",
        "backup_ref": "backup-ref:matrix:test",
        "backup_version_ref": "backup-version-ref:matrix:test:1",
        "backup_integrity_ref": "backup-integrity-ref:matrix:test:1",
        "backup_key_item_ref": "backup-key-item-ref:matrix:test",
        "backup_key_version_ref": "backup-key-version-ref:matrix:test:1",
        "recovery_target_ref": "recovery-target-ref:matrix:test",
        "recovery_attempt_ref": "recovery-attempt-ref:matrix:test:1",
        "readiness_ref": "readiness-ref:matrix-crypto:adapter-required",
        "rollback_ref": matrix_crypto_rollback_ref(operation),
        "request_created_at": now,
        "start_deadline": now + timedelta(minutes=2),
    }
    if operation in {
        MatrixCryptoOperation.verification_request,
        MatrixCryptoOperation.verification_cancel,
        MatrixCryptoOperation.verification_confirm,
    }:
        values.update(
            {
                "peer_device_ref": "device-ref:matrix:peer",
                "verification_transaction_ref": "verification-ref:matrix:test",
                "verification_method_ref": "verification-method-ref:matrix:sas",
                "verification_generation_ref": "verification-generation-ref:matrix:test:1",
            }
        )
    if operation == MatrixCryptoOperation.verification_confirm:
        values["transcript_hash_ref"] = "transcript-hash-ref:matrix:test"
    if operation == MatrixCryptoOperation.crypto_store_key_rotate:
        values["next_crypto_key_version_ref"] = "crypto-key-version-ref:matrix:test:2"
    if operation == MatrixCryptoOperation.backup_rotate:
        values["next_backup_version_ref"] = "backup-version-ref:matrix:test:2"
    if operation in {
        MatrixCryptoOperation.recovery_restore,
        MatrixCryptoOperation.local_backup_restore,
    }:
        values["staging_store_ref"] = "crypto-store-ref:matrix:staging"
    if operation == MatrixCryptoOperation.identity_reset:
        values["consequence_review_ref"] = "consequence-review-ref:matrix:test"
    values.update(overrides)
    values["request_fingerprint_ref"] = matrix_crypto_request_fingerprint_ref(**values)
    return MatrixCryptoCommand(**values)


def test_exact_crypto_authority_allowlist_has_no_global_callable_switch() -> None:
    assert set(MATRIX_CRYPTO_LANES) == set(MatrixCryptoOperation)
    assert len(MATRIX_CRYPTO_LANES) == 17
    assert len({lane.lane_ref for lane in MATRIX_CRYPTO_LANES.values()}) == 17
    assert len({lane.tool_ref for lane in MATRIX_CRYPTO_LANES.values()}) == 17
    assert all("broad" not in lane.lane_ref for lane in MATRIX_CRYPTO_LANES.values())


@pytest.mark.parametrize(
    "operation",
    (
        MatrixCryptoOperation.identity_reset,
        MatrixCryptoOperation.device_revoke,
        MatrixCryptoOperation.crypto_store_key_delete,
        MatrixCryptoOperation.local_backup_delete,
    ),
)
def test_destructive_crypto_operations_have_backend_owned_irreversibility(
    operation: MatrixCryptoOperation,
) -> None:
    command = _command(operation)
    assert command.rollback_ref.startswith("irreversibility-ref:matrix-crypto:")
    with pytest.raises(ValidationError, match="ROLLBACK_POSTURE_MISMATCH"):
        _command(operation, rollback_ref="rollback-readiness-ref:matrix-crypto:fake")


def test_restoration_capable_operation_has_backend_owned_rollback_readiness() -> None:
    command = _command(MatrixCryptoOperation.local_backup_restore)
    assert command.rollback_ref == (
        "rollback-readiness-ref:matrix-crypto:local-backup-restore"
    )


@pytest.mark.parametrize("operation", list(MatrixCryptoOperation))
def test_each_operation_is_exactly_bound_and_runtime_unsupported(
    tmp_path: Path,
    operation: MatrixCryptoOperation,
) -> None:
    command = _command(operation)
    lane = MATRIX_CRYPTO_LANES[operation]
    issue = build_matrix_crypto_lease_issue_request(command)
    action = build_matrix_crypto_authority_action(command)
    assert issue.scope == "session"
    assert issue.requested_domains == {
        lane.authority_domain: [lane.authority_capability]
    }
    assert issue.constraints["exact_request_fingerprint_ref"] == (
        command.request_fingerprint_ref
    )
    assert lane.lane_ref in issue.authority_constraints[0].allowed_refs
    assert command.crypto_store_ref in issue.authority_constraints[0].allowed_refs
    assert action.unsupported_adapter is True
    assert action.adapter_ref == lane.adapter_ref
    approval_authority = LocalApprovalAuthority()
    approval_ref = (
        capture_exact_matrix_crypto_lease_approval(
            command,
            approval_authority=approval_authority,
            confirmed=True,
        )
        if lane.approval_required
        else None
    )
    lease, receipt = issue_exact_matrix_crypto_lease(
        command,
        store=AuthorityLeaseStore(tmp_path / operation.value),
        approval_authority=approval_authority,
        approval_ref=approval_ref,
    )
    assert receipt.status == "issued"
    assert lease.lease_ref == command.lease_ref
    assert lease.constraints["exact_lane_ref"] == lane.lane_ref


def test_confirmation_or_identifier_alone_cannot_issue_lease(tmp_path: Path) -> None:
    command = _command(MatrixCryptoOperation.verification_confirm)
    authority = LocalApprovalAuthority()
    with pytest.raises(ValueError, match="MATRIX_CRYPTO_LEASE_APPROVAL_REQUIRED"):
        issue_exact_matrix_crypto_lease(
            command,
            store=AuthorityLeaseStore(tmp_path / "missing"),
            approval_authority=authority,
            approval_ref=None,
        )
    with pytest.raises(ValueError, match="MATRIX_CRYPTO_LEASE_APPROVAL_INVALID"):
        issue_exact_matrix_crypto_lease(
            command,
            store=AuthorityLeaseStore(tmp_path / "unknown"),
            approval_authority=authority,
            approval_ref="approval-ref:matrix-crypto-lease:arbitrary",
        )


def test_revoked_exact_lease_approval_cannot_issue(tmp_path: Path) -> None:
    command = _command(MatrixCryptoOperation.verification_confirm)
    authority = LocalApprovalAuthority()
    approval_ref = capture_exact_matrix_crypto_lease_approval(
        command,
        approval_authority=authority,
        confirmed=True,
    )
    authority.revoke(approval_ref, "operator_revoked")
    with pytest.raises(ValueError, match="MATRIX_CRYPTO_LEASE_APPROVAL_INVALID"):
        issue_exact_matrix_crypto_lease(
            command,
            store=AuthorityLeaseStore(tmp_path / "revoked"),
            approval_authority=authority,
            approval_ref=approval_ref,
        )


def test_approval_is_exact_but_never_grants_execution() -> None:
    command = _command(MatrixCryptoOperation.verification_confirm)
    request = build_matrix_crypto_approval_request(command)
    action = build_matrix_crypto_authority_action(command)
    assert request.subject_id == action.action_ref
    assert command.verification_transaction_ref in request.resource_refs
    approval_ref = capture_exact_matrix_crypto_approval(
        command,
        approval_authority=LocalApprovalAuthority(),
        confirmed=True,
    )
    proposal = build_matrix_crypto_proposal(command)
    assert approval_ref.startswith("approval-ref:matrix-crypto:")
    assert proposal.execution_permitted is False
    assert proposal.mutation_performed is False
    assert proposal.approval_ref_authorizes_execution is False


def test_read_posture_forbids_approval_capture() -> None:
    command = _command(MatrixCryptoOperation.backup_status_read)
    with pytest.raises(ValueError, match="MATRIX_CRYPTO_READ_APPROVAL_FORBIDDEN"):
        build_matrix_crypto_approval_request(command)


@pytest.mark.parametrize(
    "update",
    [
        {"account_ref": "account-ref:matrix:other"},
        {"device_ref": "device-ref:matrix:other"},
        {"store_generation_ref": "store-generation-ref:matrix:test:2"},
        {"backup_version_ref": "backup-version-ref:matrix:test:2"},
        {"recovery_attempt_ref": "recovery-attempt-ref:matrix:test:2"},
    ],
)
def test_scope_or_generation_substitution_invalidates_fingerprint(
    update: dict[str, object],
) -> None:
    command = _command()
    payload = command.model_dump(mode="python")
    payload.update(update)
    with pytest.raises(
        ValidationError,
        match="MATRIX_CRYPTO_REQUEST_FINGERPRINT_MISMATCH",
    ):
        MatrixCryptoCommand(**payload)


def test_verification_and_restore_require_fresh_exact_bindings() -> None:
    with pytest.raises(
        ValidationError,
        match="MATRIX_CRYPTO_EXACT_VERIFICATION_SCOPE_REQUIRED",
    ):
        _command(MatrixCryptoOperation.verification_request, peer_device_ref=None)
    with pytest.raises(
        ValidationError,
        match="MATRIX_CRYPTO_TRANSCRIPT_HASH_REQUIRED",
    ):
        _command(MatrixCryptoOperation.verification_confirm, transcript_hash_ref=None)
    with pytest.raises(
        ValidationError,
        match="MATRIX_CRYPTO_IN_PLACE_RESTORE_DENIED",
    ):
        _command(
            MatrixCryptoOperation.recovery_restore,
            staging_store_ref="crypto-store-ref:matrix:test",
        )


def test_rotations_and_identity_reset_require_distinct_or_reviewed_scope() -> None:
    with pytest.raises(
        ValidationError,
        match="MATRIX_CRYPTO_NEXT_STORE_KEY_VERSION_REQUIRED",
    ):
        _command(
            MatrixCryptoOperation.crypto_store_key_rotate,
            next_crypto_key_version_ref="crypto-key-version-ref:matrix:test:1",
        )
    with pytest.raises(
        ValidationError,
        match="MATRIX_CRYPTO_NEXT_BACKUP_VERSION_REQUIRED",
    ):
        _command(
            MatrixCryptoOperation.backup_rotate,
            next_backup_version_ref="backup-version-ref:matrix:test:1",
        )
    with pytest.raises(
        ValidationError,
        match="MATRIX_CRYPTO_CONSEQUENCE_REVIEW_REQUIRED",
    ):
        _command(MatrixCryptoOperation.identity_reset, consequence_review_ref=None)


def test_secret_like_refs_and_live_runtime_claims_fail_closed() -> None:
    with pytest.raises(ValidationError, match="unsafe content"):
        _command(account_ref="account-ref:api_key=abcdefghijklmnop")
    posture = build_default_matrix_crypto_posture()
    assert posture.runtime_status == MatrixCryptoRuntimeStatus.adapter_required
    assert posture.live_executor_operation_refs == ()
    payload = posture.model_dump(mode="python")
    payload["live_executor_operation_refs"] = (
        "operation-ref:matrix-crypto:verification-confirm",
    )
    with pytest.raises(
        ValidationError,
        match="MATRIX_CRYPTO_LIVE_EXECUTOR_CLAIM_NOT_PROVEN",
    ):
        MatrixCryptoPosture(**payload)


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("runtime_status", "ready", "MATRIX_CRYPTO_RUNTIME_STATUS_NOT_PROVEN"),
        ("freshness", "current", "MATRIX_CRYPTO_FRESHNESS_NOT_PROVEN"),
        (
            "authority_lane_refs",
            (),
            "MATRIX_CRYPTO_AUTHORITY_LANE_SET_MISMATCH",
        ),
        (
            "accepted_authority_operation_refs",
            (),
            "MATRIX_CRYPTO_ACCEPTED_OPERATION_SET_MISMATCH",
        ),
        (
            "blocked_operation_refs",
            (),
            "MATRIX_CRYPTO_BLOCKED_OPERATION_SET_MISMATCH",
        ),
    ],
)
def test_crypto_posture_rejects_contradictory_or_incomplete_truth(
    field: str,
    value: object,
    reason: str,
) -> None:
    payload = build_default_matrix_crypto_posture().model_dump(mode="python")
    payload[field] = value
    with pytest.raises(ValidationError, match=reason):
        MatrixCryptoPosture(**payload)


def test_unknown_backend_and_safe_disable_posture_derive_unknown_readiness() -> None:
    snapshot = build_matrix_crypto_availability(checked_at=utc_now())
    assert snapshot.compatibility_status == "unknown"
    assert snapshot.configuration_status == "not_configured"
    assert snapshot.safe_disable_status == "unknown"
    assert snapshot.runtime_readiness_status == "unknown"
    assert "SAFE_DISABLE_STATUS_UNKNOWN" in snapshot.blocker_codes
