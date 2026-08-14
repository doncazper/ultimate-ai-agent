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
    issue_authority_lease_from_backend_state,
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
    lease, receipt = issue_authority_lease_from_backend_state(
        AuthorityLeaseStore(authority_dir),
        lease_request,
        idempotency_ref=idempotency_ref,
    )
    return lease is not None and receipt.status == "issued"
