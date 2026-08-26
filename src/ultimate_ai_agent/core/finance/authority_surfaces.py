"""Authority-catalog registration for the exact FIN-001 mutation lane."""

from __future__ import annotations


def build_finance_synthetic_book_authority_mapping():
    from ultimate_ai_agent.core.authority.contracts import (
        AuthorityCapability,
        AuthorityDomain,
        TrustMode,
        _mapping,
    )

    return _mapping(
        "authority-lane-ref:finance/FIN-001/synthetic-book-mutation",
        "FIN-001 synthetic protected-book mutation",
        AuthorityDomain.workspace,
        AuthorityCapability.write,
        TrustMode.ask_before_changes,
        "implemented_exact_session_lease_and_local_approval_required",
        [],
        [
            "scripts/dev/uaa_finance.py prepare",
            "scripts/dev/uaa_finance.py run --confirmed",
            "scripts/dev/uaa_finance.py inspect",
            "scripts/dev/uaa_finance.py check",
            "scripts/dev/uaa_finance.py export",
        ],
        (
            "Mutates only an encrypted synthetic FIN-001 book after current "
            "policy, exact local approval, and exact session-lease validation, "
            "with revision/idempotency binding, safe-disable, content-free "
            "receipts, and pre-persist revalidation. Coarse leases, arbitrary or "
            "real values, routes, connectors, payments, filing, and advice are denied."
        ),
    )
