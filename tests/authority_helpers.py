from __future__ import annotations

from pathlib import Path

from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
)


def memory_write_authority_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:test-memory-review-write",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.memory: [AuthorityCapability.write]},
        safe_summary="Test lease grants Memory write for exact Memory Review accept/correct.",
    )


def issue_memory_write_authority_lease(state_dir: Path) -> None:
    AuthorityLeaseStore(state_dir).issue_lease(
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
    AuthorityLeaseStore(state_dir).issue_lease(
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
