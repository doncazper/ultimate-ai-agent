from __future__ import annotations

from pathlib import Path

from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    build_authority_lease_operator_approval_grant,
    validate_authority_lease_approval,
)


def issue_file_preview_probe_authority_lease(authority_dir: Path) -> bool:
    lease_request = AuthorityLeaseIssueRequest(
        mode=TrustMode.read_only,
        requested_domains={
            AuthorityDomain.files: [
                AuthorityCapability.read,
                AuthorityCapability.prepare,
            ]
        },
        decision_reason_ref="decision-reason-ref:gate-v0292-file-preview-authority",
        safe_summary=(
            "Gate probe grants Files read and prepare for a metadata-only file preview."
        ),
    )
    idempotency_ref = "idempotency-ref:gate-v0292-file-preview-authority"
    _, approval_grant = build_authority_lease_operator_approval_grant(
        lease_request,
        idempotency_ref=idempotency_ref,
        approved_by_actor_id="operator-ref:foundation-gate",
    )
    if approval_grant is not None:
        lease_request = lease_request.model_copy(
            update={
                "approval_ref": approval_grant.approval_ref,
                "approval_grants": [approval_grant.model_dump(mode="json")],
            }
        )
    lease, receipt = AuthorityLeaseStore(authority_dir).issue_lease(
        lease_request,
        idempotency_ref=idempotency_ref,
        approval_validator=validate_authority_lease_approval,
    )
    return lease is not None and receipt.status == "issued"
