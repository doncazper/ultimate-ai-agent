from __future__ import annotations

import json
import subprocess

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.control_center.dashboard import (
    build_provider_credential_readiness_summary,
)
from ultimate_ai_agent.core.providers import (
    ProviderRouterDryRunProviderStatus,
    ProviderRouterDryRunRequest,
    build_provider_router_dry_run_request,
    evaluate_provider_router_dry_run,
)


client = TestClient(app)


def test_provider_router_dry_run_read_model_is_proposal_only() -> None:
    readiness = build_provider_credential_readiness_summary()
    proposal = readiness.router_dry_run_readiness

    assert proposal.status == "proposal_only"
    assert proposal.proposal_only is True
    assert proposal.invocation_authorized is False
    assert proposal.fallback_execution_authorized is False
    assert proposal.network_call_performed is False
    assert proposal.provider_sdk_call_performed is False
    assert proposal.credential_validation_performed is False
    assert proposal.model_invocation_performed is False
    assert proposal.billing_authority_granted is False
    assert proposal.autonomous_background_execution_enabled is False
    assert proposal.eligible_provider_refs == []
    assert len(proposal.blocked_provider_refs) == 3
    assert len(proposal.missing_credential_refs) == 3
    assert len(proposal.cost_risky_refs) == 3
    assert len(proposal.validation_required_refs) == 3
    assert len(proposal.no_authority_refs) == 3
    assert "NO_PROVIDER_INVOCATION" in proposal.blocker_codes
    assert "NO_FALLBACK_EXECUTION" in proposal.blocker_codes


def test_provider_router_dry_run_manifest_language_is_non_authorizing() -> None:
    manifest = client.get("/api/manifest").json()

    assert (
        "control_center_provider_router_dry_run_proposal_only"
        in manifest["capabilities_declared"]
    )
    assert (
        "control_center_provider_router_dry_run_cli_inspection"
        in manifest["capabilities_declared"]
    )
    assert (
        "control_center_provider_router_dry_run_as_invocation_authority"
        in manifest["capabilities_blocked"]
    )
    assert (
        "control_center_provider_router_dry_run_fallback_execution"
        in manifest["capabilities_blocked"]
    )
    assert (
        "control_center_provider_router_dry_run_provider_sdk_calls"
        in manifest["capabilities_blocked"]
    )
    assert (
        "control_center_provider_router_dry_run_credential_validation"
        in manifest["capabilities_blocked"]
    )
    assert (
        "control_center_provider_router_dry_run_model_calls"
        in manifest["capabilities_blocked"]
    )
    assert (
        "control_center_provider_router_dry_run_billing_authority"
        in manifest["capabilities_blocked"]
    )


def test_provider_router_dry_run_manifest_route_is_validation_only() -> None:
    manifest = client.get("/api/manifest").json()
    routes_by_path = {route["path"]: route for route in manifest["routes"]}
    route = routes_by_path["/control-center/providers/router/dry-run"]

    assert route["route_classification"] == "mutating_requires_authority"
    assert route["side_effect_class"] == "validation_only"
    assert route["rate_limit_group"] == "provider_router_dry_run"


def test_provider_router_dry_run_request_rejects_execution_claims() -> None:
    with pytest.raises(ValidationError, match="PROVIDER_ROUTER_DRY_RUN_REQUEST_EXECUTION_DENIED"):
        ProviderRouterDryRunRequest(invocation_requested=True)

    with pytest.raises(ValidationError, match="PROVIDER_ROUTER_DRY_RUN_REQUEST_EXECUTION_DENIED"):
        ProviderRouterDryRunRequest(provider_sdk_call_requested=True)

    with pytest.raises(ValidationError, match="PROVIDER_ROUTER_DRY_RUN_REQUEST_EXECUTION_DENIED"):
        ProviderRouterDryRunRequest(credential_validation_requested=True)


def test_provider_router_dry_run_classifies_eligible_blocked_and_cost_risky_refs() -> None:
    proposal = evaluate_provider_router_dry_run(
        build_provider_router_dry_run_request(),
        provider_readiness_items=[
            {
                "provider_id": "provider:eligible-compatible:reference",
                "provider_label": "Eligible-compatible provider",
                "provider_manifest_ref": "provider-manifest-ref:eligible-compatible:reference-only",
                "credential_ref": "credential-ref:eligible-compatible:available",
                "credential_ref_status": "reference_available",
                "provider_model_refs_bound": True,
                "readiness_status": "reference_readiness_only",
                "cost_governor_binding": {
                    "model_ref": "model-ref:eligible-compatible:review-model",
                    "unknown_paid_cost_requires_approval": False,
                    "estimated_cost_above_budget_blocks_use": False,
                },
            },
            {
                "provider_id": "provider:blocked-compatible:reference",
                "provider_label": "Blocked-compatible provider",
                "provider_manifest_ref": "provider-manifest-ref:blocked-compatible:reference-only",
                "credential_ref": "credential-ref:blocked-compatible:not-configured",
                "credential_ref_status": "reference_missing",
                "provider_model_refs_bound": False,
                "cost_governor_binding": {
                    "model_ref": "model-ref:blocked-compatible:not-selected",
                },
            },
            {
                "provider_id": "provider:degraded-compatible:reference",
                "provider_label": "Degraded-compatible provider",
                "provider_manifest_ref": "provider-manifest-ref:degraded-compatible:reference-only",
                "credential_ref": "credential-ref:degraded-compatible:available",
                "credential_ref_status": "reference_available",
                "readiness_status": "degraded_reference_only",
                "provider_model_refs_bound": True,
                "cost_governor_binding": {
                    "model_ref": "model-ref:degraded-compatible:review-model",
                    "unknown_paid_cost_requires_approval": False,
                    "estimated_cost_above_budget_blocks_use": False,
                },
            },
            {
                "provider_id": "provider:cost-compatible:reference",
                "provider_label": "Cost-compatible provider",
                "provider_manifest_ref": "provider-manifest-ref:cost-compatible:reference-only",
                "credential_ref": "credential-ref:cost-compatible:available",
                "credential_ref_status": "reference_available",
                "provider_model_refs_bound": True,
                "cost_governor_binding": {
                    "model_ref": "model-ref:cost-compatible:review-model",
                    "unknown_paid_cost_requires_approval": True,
                    "estimated_cost_above_budget_blocks_use": False,
                },
            },
        ],
    )

    statuses = {
        provider.provider_ref: provider.status for provider in proposal.provider_proposals
    }
    assert statuses["provider:eligible-compatible:reference"] == (
        ProviderRouterDryRunProviderStatus.eligible
    )
    assert statuses["provider:blocked-compatible:reference"] == (
        ProviderRouterDryRunProviderStatus.blocked
    )
    assert statuses["provider:degraded-compatible:reference"] == (
        ProviderRouterDryRunProviderStatus.degraded
    )
    assert statuses["provider:cost-compatible:reference"] == (
        ProviderRouterDryRunProviderStatus.cost_risky
    )
    assert proposal.eligible_provider_refs == ["provider:eligible-compatible:reference"]
    assert "provider:blocked-compatible:reference" in proposal.blocked_provider_refs
    assert "provider:degraded-compatible:reference" in proposal.degraded_provider_refs
    assert "cost-estimate-ref:cost-compatible:router-review-required" in (
        proposal.cost_risky_refs
    )
    assert all(not provider.execution_authorized for provider in proposal.provider_proposals)


def test_provider_router_dry_run_route_returns_safe_proposal() -> None:
    request = build_provider_router_dry_run_request()
    response = client.post(
        "/control-center/providers/router/dry-run",
        json=request.model_dump(mode="json"),
        headers={"X-UAA-Idempotency-Ref": request.idempotency_ref},
    )

    assert response.status_code == 200
    envelope = response.json()
    assert envelope["success"] is True
    assert envelope["operation"] == "control_center_providers_router_dry_run"
    data = envelope["data"]
    assert data["proposal_only"] is True
    assert data["invocation_authorized"] is False
    assert data["fallback_execution_authorized"] is False
    assert data["provider_sdk_call_performed"] is False
    assert data["credential_validation_performed"] is False
    assert data["model_invocation_performed"] is False
    assert data["billing_authority_granted"] is False
    assert data["eligible_provider_refs"] == []
    assert len(data["blocked_provider_refs"]) == 3
    assert "provider_router_safe_refs_only" in envelope["redactions_applied"]


def test_provider_router_dry_run_route_blocks_idempotency_mismatch() -> None:
    request = build_provider_router_dry_run_request()
    response = client.post(
        "/control-center/providers/router/dry-run",
        json=request.model_dump(mode="json"),
        headers={"X-UAA-Idempotency-Key": "idempotency-ref:provider-router:mismatch"},
    )

    assert response.status_code == 200
    envelope = response.json()
    assert envelope["success"] is False
    assert envelope["data"]["invocation_authorized"] is False
    assert envelope["data"]["fallback_execution_authorized"] is False
    assert "IDEMPOTENCY_REF_MISMATCH" in envelope["data"]["reason_codes"]


def test_provider_router_dry_run_cli_inspection_outputs_safe_schema() -> None:
    result = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/inspect_provider_router_dry_run.py",
            "--router-run-ref",
            "provider-router-run-ref:dry-run:test-cli",
            "--idempotency-ref",
            "idempotency-ref:provider-router:dry-run:test-cli",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)

    assert data["proposal_only"] is True
    assert data["invocation_authorized"] is False
    assert data["provider_sdk_call_performed"] is False
    assert data["billing_authority_granted"] is False
    assert "provider_exchange" not in result.stdout.lower()
    assert "sk-" not in result.stdout.lower()
