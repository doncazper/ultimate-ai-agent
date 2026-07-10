#!/usr/bin/env python3
"""Inspect self-hosted Firecrawl markdown posture without echoing a target."""

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
    FIRECRAWL_SELF_HOSTED_PROVIDER_REF,
    FirecrawlMarkdownRequest,
    WebProviderCapabilityState,
    WebProviderDeploymentKind,
    WebProviderOperation,
    build_web_provider_capability_state,
    execute_firecrawl_markdown,
    firecrawl_target_source_ref,
)


def inspect_markdown_payload(
    *,
    request: FirecrawlMarkdownRequest,
    capability_state: WebProviderCapabilityState,
    approval_authority: LocalApprovalAuthority,
    authority_leases: Sequence[AuthorityLease],
    transport: Any | None = None,
    target_validator: Any | None = None,
    evaluated_at: datetime | None = None,
) -> dict[str, Any]:
    result = execute_firecrawl_markdown(
        request,
        capability_state=capability_state,
        approval_authority=approval_authority,
        authority_leases=authority_leases,
        transport=transport,
        target_validator=target_validator,
        evaluated_at=evaluated_at,
    )
    evidence = result.evidence
    return {
        "schema_version": "uaa-firecrawl-markdown-cli.v1",
        "request_ref": result.request_ref,
        "target_source_ref": request.target_source_ref,
        "status": result.status.value,
        "execution_succeeded": result.execution_succeeded,
        "invocation_outcome": result.invocation_decision.outcome.value,
        "invocation_decision_ref": result.invocation_decision.decision_ref,
        "transport_receipt_ref": result.transport_receipt.receipt_ref,
        "gateway_audit_ref": result.gateway_audit_ref,
        "content_hash_ref": evidence.content_hash_ref if evidence else None,
        "bounded_redacted_preview": (
            evidence.bounded_redacted_preview if evidence else None
        ),
        "preview_redaction_status": (
            evidence.preview_redaction_status.value if evidence else None
        ),
        "content_untrusted": True,
        "instruction_authority": False,
        "raw_target_returned": False,
        "full_markdown_returned": False,
        "raw_provider_payload_returned": False,
        "reason_codes": list(result.reason_codes),
        "blocker_codes": list(result.blocker_codes),
    }


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "Firecrawl governed one-page markdown extraction",
        f"Status: {payload['status']}",
        f"Invocation: {payload['invocation_outcome']}",
        f"Execution succeeded: {'yes' if payload['execution_succeeded'] else 'no'}",
        f"Target source: {payload['target_source_ref']}",
        f"Receipt: {payload['transport_receipt_ref']}",
        f"Audit: {payload['gateway_audit_ref']}",
        "Extracted markdown is transient untrusted evidence, never instructions or authority.",
    ]
    if payload.get("bounded_redacted_preview"):
        lines.append("Preview: " + str(payload["bounded_redacted_preview"]))
    blockers = payload.get("blocker_codes") or payload.get("reason_codes") or []
    if blockers:
        lines.append("Posture: " + ", ".join(str(item) for item in blockers))
    return "\n".join(lines)


def _blocked_inspection_state(now: datetime) -> WebProviderCapabilityState:
    return build_web_provider_capability_state(
        state_ref="web-provider-capability-state-ref:firecrawl-markdown:cli-unobserved",
        provider_ref=FIRECRAWL_SELF_HOSTED_PROVIDER_REF,
        deployment=WebProviderDeploymentKind.firecrawl_self_hosted,
        operation=WebProviderOperation.scrape_markdown,
        version_ref="version-ref:firecrawl:configured-pin-unobserved",
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
        reason_codes=("FIRECRAWL_CLI_INSPECTION_HAS_NO_LIVE_OBSERVATION",),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the self-hosted Firecrawl markdown lane. The target is accepted "
            "transiently and is never echoed in the safe CLI summary."
        )
    )
    parser.add_argument("--target-url", required=True)
    parser.add_argument("--allowed-domain", required=True)
    parser.add_argument(
        "--request-ref",
        default="web-extract-request-ref:cli-inspection",
    )
    parser.add_argument(
        "--task-ref",
        default="task-ref:web-extract:cli-inspection",
    )
    parser.add_argument("--approval-ref")
    parser.add_argument("--json", action="store_true", help="Emit safe JSON instead.")
    args = parser.parse_args(argv)
    now = datetime.now(timezone.utc)
    request = FirecrawlMarkdownRequest(
        request_ref=args.request_ref,
        task_ref=args.task_ref,
        approval_ref=args.approval_ref,
        target_url=args.target_url,
        target_source_ref=firecrawl_target_source_ref(args.target_url),
        allowed_domains=(args.allowed_domain,),
        expected_execution_receipt_ref=(
            "execution-receipt-ref:web-extract:cli-inspection"
        ),
    )
    payload = inspect_markdown_payload(
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
