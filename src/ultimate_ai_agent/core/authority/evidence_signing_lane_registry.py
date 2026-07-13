from __future__ import annotations


def build_evidence_signing_lane_authority_mappings():
    from ultimate_ai_agent.core.authority.contracts import (
        AuthorityCapability,
        AuthorityDomain,
        TrustMode,
        _mapping,
    )

    return [
        _mapping(
            "lane-ref:portable-evidence-managed-signing",
            "Managed portable evidence signing",
            AuthorityDomain.evidence_signing,
            AuthorityCapability.execute,
            TrustMode.ask_before_changes,
            "implemented_core_dispatcher_cli_inspection",
            ["GET /api/runtime/authority-missions/completions"],
            [
                "scripts/dev/uaa_runtime.py verify-authority-mission-evidence",
                "scripts/dev/uaa_runtime.py export-portable-evidence-public-key-bundle",
            ],
            (
                "A purpose-specific Ed25519 lane signs verified content-free mission "
                "evidence only through an exact dispatcher adapter, current policy, "
                "LocalApprovalAuthority validation, exact AuthorityLease resources, "
                "budget, kill switch, safe-disable, and pinned macOS Keychain helper "
                "readiness. Evidence never grants execution authority."
            ),
        ),
        _mapping(
            "lane-ref:portable-evidence-key-lifecycle",
            "Portable evidence signing-key lifecycle",
            AuthorityDomain.evidence_signing,
            AuthorityCapability.mutate,
            TrustMode.ask_before_changes,
            "implemented_core_dispatcher_cli_inspection",
            ["GET /api/runtime/authority-missions/completions"],
            ["scripts/dev/uaa_runtime.py inspect-authority-mission-completions"],
            (
                "Exact create, rotate, revoke, mark-lost, and interrupted-deletion "
                "cleanup adapters are dispatcher-governed and persist public lifecycle "
                "refs only. The Ed25519 seed is held by a non-synchronizing, "
                "device-only macOS Keychain item and is never returned to Python or "
                "durable UAA state."
            ),
        ),
    ]
