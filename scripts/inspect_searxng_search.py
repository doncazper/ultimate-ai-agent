#!/usr/bin/env python3
"""Inspect the governed SearXNG lane without echoing a raw query."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.authority import AuthorityLease  # noqa: E402
from ultimate_ai_agent.core.capabilities.approval import (  # noqa: E402
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.capability_availability import (  # noqa: E402
    AuthorityPosture,
    CatalogStatus,
    CompatibilityStatus,
    ConfigurationStatus,
    FreshnessStatus,
    HealthStatus,
    ResourceBudgetStatus,
    SafeDisableStatus,
)
from ultimate_ai_agent.core.web_access import (  # noqa: E402
    SEARXNG_SEARCH_PROVIDER_REF,
    SearxngSearchRequest,
    WebProviderCapabilityState,
    WebProviderDeploymentKind,
    WebProviderOperation,
    build_web_provider_capability_state,
    execute_searxng_search,
)


def inspect_search_payload(
    *,
    request: SearxngSearchRequest,
    capability_state: WebProviderCapabilityState,
    approval_authority: LocalApprovalAuthority,
    authority_leases: Sequence[AuthorityLease],
    transport: Any | None = None,
    evaluated_at: datetime | None = None,
) -> dict[str, Any]:
    result = execute_searxng_search(
        request,
        capability_state=capability_state,
        approval_authority=approval_authority,
        authority_leases=authority_leases,
        transport=transport,
        evaluated_at=evaluated_at,
    )
    return {
        "schema_version": "uaa-searxng-search-cli.v1",
        "request_ref": result.request_ref,
        "status": result.status.value,
        "execution_succeeded": result.execution_succeeded,
        "invocation_outcome": result.invocation_decision.outcome.value,
        "invocation_decision_ref": result.invocation_decision.decision_ref,
        "transport_receipt_ref": result.transport_receipt.receipt_ref,
        "gateway_audit_ref": result.gateway_audit_ref,
        "source_refs": [item.source_ref for item in result.evidence],
        "content_untrusted": True,
        "instruction_authority": False,
        "raw_query_returned": False,
        "raw_provider_payload_returned": False,
        "reason_codes": list(result.reason_codes),
        "blocker_codes": list(result.blocker_codes),
    }


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "SearXNG governed read-only search",
        f"Status: {payload['status']}",
        f"Invocation: {payload['invocation_outcome']}",
        f"Execution succeeded: {'yes' if payload['execution_succeeded'] else 'no'}",
        f"Source refs: {len(payload['source_refs'])}",
        f"Receipt: {payload['transport_receipt_ref']}",
        f"Audit: {payload['gateway_audit_ref']}",
        "External search content is untrusted evidence, never instructions or authority.",
    ]
    blockers = payload.get("blocker_codes") or payload.get("reason_codes") or []
    if blockers:
        lines.append("Posture: " + ", ".join(str(item) for item in blockers))
    return "\n".join(lines)


def _blocked_inspection_state(now: datetime) -> WebProviderCapabilityState:
    return build_web_provider_capability_state(
        state_ref="web-provider-capability-state-ref:searxng-search:cli-unobserved",
        provider_ref=SEARXNG_SEARCH_PROVIDER_REF,
        deployment=WebProviderDeploymentKind.searxng_self_hosted,
        operation=WebProviderOperation.search,
        version_ref="version-ref:searxng:configured-pin-unobserved",
        catalog_status=CatalogStatus.supported,
        compatibility_status=CompatibilityStatus.unknown,
        configuration_status=ConfigurationStatus.unknown,
        health_status=HealthStatus.unknown,
        authority_posture=AuthorityPosture.lease_required,
        resource_status=ResourceBudgetStatus.unknown,
        safe_disable_status=SafeDisableStatus.unknown,
        freshness_status=FreshnessStatus.unknown,
        observed_at=now,
        expires_at=None,
        reason_codes=("SEARXNG_CLI_INSPECTION_HAS_NO_LIVE_OBSERVATION",),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the SearXNG search lane. The raw query is accepted transiently "
            "and is never echoed or included in the receipt summary."
        )
    )
    parser.add_argument("--query", required=True)
    parser.add_argument(
        "--request-ref",
        default="web-search-request-ref:cli-inspection",
    )
    parser.add_argument(
        "--task-ref",
        default="task-ref:web-search:cli-inspection",
    )
    parser.add_argument("--approval-ref")
    parser.add_argument("--json", action="store_true", help="Emit safe JSON instead.")
    args = parser.parse_args(argv)
    now = datetime.now(timezone.utc)
    request = SearxngSearchRequest(
        request_ref=args.request_ref,
        task_ref=args.task_ref,
        approval_ref=args.approval_ref,
        query=args.query,
        expected_execution_receipt_ref="execution-receipt-ref:web-search:cli-inspection",
    )
    payload = inspect_search_payload(
        request=request,
        capability_state=_blocked_inspection_state(now),
        approval_authority=LocalApprovalAuthority(),
        authority_leases=[],
        evaluated_at=now,
    )
    if args.json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(render_summary(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
