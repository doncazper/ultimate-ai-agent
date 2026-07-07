from __future__ import annotations

from pathlib import Path

from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
    build_authority_lease_approval_requirement_for_request,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    build_authority_lease_test_grant,
    validate_authority_lease_approval,
)


def _issue_test_authority_lease(
    state_dir: Path,
    request: AuthorityLeaseIssueRequest,
    *,
    idempotency_ref: str,
) -> None:
    requirement = build_authority_lease_approval_requirement_for_request(
        request,
        idempotency_ref=idempotency_ref,
    )
    if requirement.approval_required:
        grant = build_authority_lease_test_grant(
            requirement,
            approval_ref=f"approval-ref:test-authority-lease:{idempotency_ref.rsplit(':', 1)[-1]}",
        )
        request = request.model_copy(
            update={
                "approval_ref": grant.approval_ref,
                "approval_grants": [grant.model_dump(mode="json")],
            }
        )
    lease, receipt = AuthorityLeaseStore(state_dir).issue_lease(
        request,
        idempotency_ref=idempotency_ref,
        approval_validator=validate_authority_lease_approval,
    )
    assert receipt.status == "issued"
    assert lease is not None


def memory_write_authority_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:test-memory-review-write",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.memory: [AuthorityCapability.write]},
        safe_summary="Test lease grants Memory write for exact Memory Review accept/correct.",
    )


def issue_memory_write_authority_lease(state_dir: Path) -> None:
    _issue_test_authority_lease(
        state_dir,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.ask_before_changes,
            requested_domains={AuthorityDomain.memory: [AuthorityCapability.write]},
            decision_reason_ref="decision-reason-ref:test-memory-review-authority",
            safe_summary=(
                "Test session lease grants Memory write for exact Memory Review "
                "accept/correct."
            ),
        ),
        idempotency_ref="idempotency-ref:test-memory-review-authority",
    )


def contacts_write_authority_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:test-contacts-write",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.contacts: [AuthorityCapability.write]},
        safe_summary="Test lease grants Contacts write for exact local CRM mutation.",
    )


def issue_contacts_write_authority_lease(state_dir: Path) -> None:
    _issue_test_authority_lease(
        state_dir,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.ask_before_changes,
            requested_domains={AuthorityDomain.contacts: [AuthorityCapability.write]},
            decision_reason_ref="decision-reason-ref:test-crm-local-authority",
            safe_summary=(
                "Test session lease grants Contacts write for exact local CRM "
                "mutation."
            ),
        ),
        idempotency_ref="idempotency-ref:test-crm-local-authority",
    )


def files_write_authority_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:test-files-review-write",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.files: [AuthorityCapability.write]},
        safe_summary=(
            "Test lease grants Files write for review-only file approval capture."
        ),
    )


def files_read_prepare_authority_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:test-files-read-prepare",
        mode=TrustMode.read_only,
        domains={
            AuthorityDomain.files: [
                AuthorityCapability.read,
                AuthorityCapability.prepare,
            ]
        },
        safe_summary=(
            "Test lease grants Files read and prepare for safe preview routes."
        ),
    )


def issue_files_read_prepare_authority_lease(state_dir: Path) -> None:
    _issue_test_authority_lease(
        state_dir,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.read_only,
            requested_domains={
                AuthorityDomain.files: [
                    AuthorityCapability.read,
                    AuthorityCapability.prepare,
                ]
            },
            decision_reason_ref="decision-reason-ref:test-file-preview-authority",
            safe_summary=(
                "Test session lease grants Files read and prepare for safe "
                "preview routes."
            ),
        ),
        idempotency_ref="idempotency-ref:test-file-preview-authority",
    )


def issue_files_write_authority_lease(state_dir: Path) -> None:
    _issue_test_authority_lease(
        state_dir,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.ask_before_changes,
            requested_domains={AuthorityDomain.files: [AuthorityCapability.write]},
            decision_reason_ref="decision-reason-ref:test-file-review-authority",
            safe_summary=(
                "Test session lease grants Files write for review-only file "
                "approval capture."
            ),
        ),
        idempotency_ref="idempotency-ref:test-file-review-authority",
    )


def workspace_write_authority_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:test-workspace-write",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        safe_summary=(
            "Test lease grants Workspace write for exact Control Center local "
            "state mutations."
        ),
    )


def issue_workspace_write_authority_lease(state_dir: Path) -> None:
    _issue_test_authority_lease(
        state_dir,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.ask_before_changes,
            requested_domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
            decision_reason_ref="decision-reason-ref:test-workspace-write-authority",
            safe_summary=(
                "Test session lease grants Workspace write for exact Control "
                "Center local state mutations."
            ),
        ),
        idempotency_ref="idempotency-ref:test-workspace-write-authority",
    )


def workspace_execute_authority_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:test-workspace-execute",
        mode=TrustMode.approved_safe_local_work_session,
        domains={
            AuthorityDomain.workspace: [
                AuthorityCapability.read,
                AuthorityCapability.execute,
            ]
        },
        safe_summary=(
            "Test lease grants Workspace read and execute for exact runtime "
            "commands."
        ),
    )


def workspace_execute_mission_authority_lease(mission_ref: str) -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:test-workspace-execute-mission",
        mode=TrustMode.approved_safe_local_work_session,
        scope="mission",
        mission_ref=mission_ref,
        domains={
            AuthorityDomain.workspace: [
                AuthorityCapability.read,
                AuthorityCapability.execute,
            ]
        },
        safe_summary=(
            "Test mission lease grants Workspace read and execute for exact "
            "mission-bound runtime commands."
        ),
    )


def issue_workspace_execute_authority_lease(state_dir: Path) -> None:
    _issue_test_authority_lease(
        state_dir,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.approved_safe_local_work_session,
            requested_domains={
                AuthorityDomain.workspace: [
                    AuthorityCapability.read,
                    AuthorityCapability.execute,
                ]
            },
            decision_reason_ref="decision-reason-ref:test-workspace-execute-authority",
            safe_summary=(
                "Test session lease grants Workspace read and execute for exact "
                "local orchestration/runtime commands."
            ),
        ),
        idempotency_ref="idempotency-ref:test-workspace-execute-authority",
    )


def provider_model_execute_authority_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:test-provider-model-execute",
        mode=TrustMode.full_machine_access_session,
        domains={
            AuthorityDomain.provider_model_calls: [
                AuthorityCapability.read,
                AuthorityCapability.execute,
            ]
        },
        safe_summary=(
            "Test lease grants provider model call read and execute authority "
            "for exact local loopback runtime calls."
        ),
    )


def issue_provider_model_execute_authority_lease(state_dir: Path) -> None:
    _issue_test_authority_lease(
        state_dir,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.full_machine_access_session,
            requested_domains={
                AuthorityDomain.provider_model_calls: [
                    AuthorityCapability.read,
                    AuthorityCapability.execute,
                ]
            },
            decision_reason_ref="decision-reason-ref:test-provider-model-authority",
            safe_summary=(
                "Test session lease grants provider model call execute authority "
                "for exact local loopback runtime calls."
            ),
        ),
        idempotency_ref="idempotency-ref:test-provider-model-authority",
    )
