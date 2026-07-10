from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.capability_availability import (
    AuthorityPosture,
    CatalogStatus,
    CompatibilityStatus,
    ConfigurationStatus,
    DerivedRuntimeReadinessStatus,
    FreshnessStatus,
    HealthStatus,
    ResourceBudgetStatus,
    SafeDisableStatus,
)
from ultimate_ai_agent.core.web_access import (
    WebAccessPolicy,
    WebAccessPolicyStatus,
    WebAccessRequest,
    WebAccessRequestKind,
    WebProviderDeploymentKind,
    WebProviderOperation,
    WebProviderTransportMethod,
    WebProviderTransportReceipt,
    WebProviderTransportStatus,
    build_web_provider_capability_state,
)


NOW = datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc)


def test_extract_markdown_contract_remains_policy_denied_in_phase_001() -> None:
    request = WebAccessRequest(
        kind=WebAccessRequestKind.EXTRACT_MARKDOWN,
        url="https://example.invalid/page",
    )

    decision = WebAccessPolicy().evaluate(request)

    assert decision.status == WebAccessPolicyStatus.DENIED
    assert "request_kind_not_enabled:extract_markdown" in decision.reasons


def test_provider_capability_unknown_health_fails_closed() -> None:
    state = build_web_provider_capability_state(
        state_ref="web-provider-state-ref:searxng-search",
        provider_ref="web-provider-ref:searxng",
        deployment=WebProviderDeploymentKind.searxng_self_hosted,
        operation=WebProviderOperation.search,
        version_ref="version-ref:searxng:pinned",
        catalog_status=CatalogStatus.supported,
        compatibility_status=CompatibilityStatus.supported,
        configuration_status=ConfigurationStatus.configured,
        health_status=HealthStatus.unknown,
        authority_posture=AuthorityPosture.lease_required,
        resource_status=ResourceBudgetStatus.available,
        safe_disable_status=SafeDisableStatus.inactive,
        freshness_status=FreshnessStatus.current,
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
    )

    assert state.runtime_readiness == DerivedRuntimeReadinessStatus.unknown
    assert "HEALTH_STATUS_UNKNOWN" in state.blocker_codes
    assert state.provider_catalog_visible is True
    assert state.standing_authority_granted is False


def test_safe_disable_overrides_otherwise_ready_provider_state() -> None:
    state = build_web_provider_capability_state(
        state_ref="web-provider-state-ref:firecrawl-local",
        provider_ref="web-provider-ref:firecrawl",
        deployment=WebProviderDeploymentKind.firecrawl_self_hosted,
        operation=WebProviderOperation.scrape_markdown,
        version_ref="version-ref:firecrawl:pinned",
        catalog_status=CatalogStatus.supported,
        compatibility_status=CompatibilityStatus.supported,
        configuration_status=ConfigurationStatus.configured,
        health_status=HealthStatus.healthy,
        authority_posture=AuthorityPosture.eligible_for_policy_evaluation,
        resource_status=ResourceBudgetStatus.available,
        safe_disable_status=SafeDisableStatus.active,
        freshness_status=FreshnessStatus.current,
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
    )

    assert state.runtime_readiness == DerivedRuntimeReadinessStatus.blocked
    assert "SAFE_DISABLE_ACTIVE" in state.blocker_codes


def test_transport_receipt_distinguishes_target_get_from_provider_post() -> None:
    receipt = WebProviderTransportReceipt(
        receipt_ref="web-provider-transport-receipt-ref:simulated",
        request_ref="web-request-ref:simulated",
        provider_ref="web-provider-ref:firecrawl-self-hosted",
        deployment=WebProviderDeploymentKind.firecrawl_self_hosted,
        operation=WebProviderOperation.scrape_markdown,
        target_source_ref="web-source-ref:target",
        configured_endpoint_ref="configured-endpoint-ref:firecrawl-self-hosted",
        provider_transport_method=WebProviderTransportMethod.post,
        request_schema_ref="schema-ref:firecrawl-scrape-markdown:v1",
        status=WebProviderTransportStatus.simulated,
        authority_decision_ref="authority-decision-ref:not-evaluated",
        approval_decision_ref="approval-decision-ref:not-evaluated",
        budget_decision_ref="budget-decision-ref:not-metered",
    )

    assert receipt.target_method == "GET"
    assert receipt.provider_transport_method == WebProviderTransportMethod.post
    assert receipt.network_call_performed is False
    assert receipt.raw_provider_payload_stored is False


def test_simulated_transport_receipt_cannot_claim_network_execution() -> None:
    with pytest.raises(
        ValidationError, match="WEB_PROVIDER_BLOCKED_OR_SIMULATED_CALL_DENIED"
    ):
        WebProviderTransportReceipt(
            receipt_ref="web-provider-transport-receipt-ref:invalid",
            request_ref="web-request-ref:invalid",
            provider_ref="web-provider-ref:firecrawl-self-hosted",
            deployment=WebProviderDeploymentKind.firecrawl_self_hosted,
            operation=WebProviderOperation.scrape_markdown,
            configured_endpoint_ref="configured-endpoint-ref:firecrawl-self-hosted",
            provider_transport_method=WebProviderTransportMethod.post,
            request_schema_ref="schema-ref:firecrawl-scrape-markdown:v1",
            status=WebProviderTransportStatus.simulated,
            authority_decision_ref="authority-decision-ref:not-evaluated",
            approval_decision_ref="approval-decision-ref:not-evaluated",
            budget_decision_ref="budget-decision-ref:not-metered",
            network_call_performed=True,
        )


def test_hybrid_contracts_reject_secret_and_local_path_material() -> None:
    base = {
        "receipt_ref": "web-provider-transport-receipt-ref:unsafe",
        "request_ref": "web-request-ref:unsafe",
        "provider_ref": "web-provider-ref:firecrawl-cloud",
        "deployment": WebProviderDeploymentKind.firecrawl_cloud,
        "operation": WebProviderOperation.scrape_markdown,
        "configured_endpoint_ref": "configured-endpoint-ref:firecrawl-cloud",
        "provider_transport_method": WebProviderTransportMethod.post,
        "request_schema_ref": "schema-ref:firecrawl-scrape-markdown:v1",
        "status": WebProviderTransportStatus.blocked,
        "authority_decision_ref": "authority-decision-ref:not-evaluated",
        "approval_decision_ref": "approval-decision-ref:not-evaluated",
        "budget_decision_ref": "budget-decision-ref:unknown",
    }
    with pytest.raises(ValidationError):
        WebProviderTransportReceipt(
            **base, response_receipt_hash_ref="Bearer secret-value"
        )
    with pytest.raises(ValidationError):
        WebProviderTransportReceipt(**base, target_source_ref="/Users/example/page")
    with pytest.raises(ValidationError):
        WebProviderTransportReceipt(**base, raw_payload={"page": "unsafe"})
