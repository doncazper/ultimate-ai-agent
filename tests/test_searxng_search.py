from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintKind,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.capabilities.approval import (
    CapabilityApprovalGrant,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.capability_availability import (
    AuthorityPosture,
    CatalogStatus,
    CompatibilityStatus,
    ConfigurationStatus,
    FreshnessStatus,
    HealthStatus,
    InvocationDecisionOutcome,
    ResourceBudgetStatus,
    SafeDisableStatus,
)
from ultimate_ai_agent.core.web_access import (
    SEARXNG_SEARCH_ADAPTER_REF,
    SEARXNG_SEARCH_CAPABILITY_REF,
    SEARXNG_SEARCH_PROVIDER_REF,
    SearxngConfiguredEndpoint,
    SearxngSearchRequest,
    WebAccessAuthorityMode,
    WebAccessNetworkLane,
    WebAccessPolicy,
    WebAccessPolicyStatus,
    WebAccessRequest,
    WebAccessRequestKind,
    WebProviderDeploymentKind,
    WebProviderOperation,
    WebProviderTransportStatus,
    build_web_provider_capability_state,
    execute_searxng_search,
    searxng_query_ref,
)


NOW = datetime(2026, 7, 10, 18, 0, tzinfo=timezone.utc)


def _request(**overrides: Any) -> SearxngSearchRequest:
    values: dict[str, Any] = {
        "request_ref": "web-search-request-ref:test",
        "task_ref": "task-ref:web-search:test",
        "approval_ref": "approval-ref:web-search:test",
        "query": "bounded public evidence",
        "max_results": 2,
        "expected_execution_receipt_ref": "execution-receipt-ref:web-search:test",
    }
    values.update(overrides)
    return SearxngSearchRequest(**values)


def _state(**overrides: Any):  # type: ignore[no-untyped-def]
    values: dict[str, Any] = {
        "state_ref": "web-provider-capability-state-ref:searxng-search:test",
        "provider_ref": SEARXNG_SEARCH_PROVIDER_REF,
        "deployment": WebProviderDeploymentKind.searxng_self_hosted,
        "operation": WebProviderOperation.search,
        "version_ref": "version-ref:searxng:2026.7.10-6a4d5148d",
        "catalog_status": CatalogStatus.supported,
        "compatibility_status": CompatibilityStatus.supported,
        "configuration_status": ConfigurationStatus.configured,
        "health_status": HealthStatus.healthy,
        "authority_posture": AuthorityPosture.lease_required,
        "resource_status": ResourceBudgetStatus.available,
        "safe_disable_status": SafeDisableStatus.inactive,
        "freshness_status": FreshnessStatus.current,
        "observed_at": NOW,
        "expires_at": NOW + timedelta(minutes=5),
        "reason_codes": ("SEARXNG_LOOPBACK_HEALTHY",),
    }
    values.update(overrides)
    return build_web_provider_capability_state(**values)


def _approval_authority(
    request: SearxngSearchRequest,
    *,
    capability_ref: str = SEARXNG_SEARCH_CAPABILITY_REF,
) -> LocalApprovalAuthority:
    return LocalApprovalAuthority(
        [
            CapabilityApprovalGrant(
                approval_ref=request.approval_ref or "approval-ref:web-search:missing",
                capability_id=capability_ref,
                task_id=request.task_ref,
                granted_by="operator-ref:test",
            )
        ]
    )


def _exact_resource_refs(request: SearxngSearchRequest) -> list[str]:
    return [
        request.request_ref,
        request.task_ref,
        SEARXNG_SEARCH_CAPABILITY_REF,
        SEARXNG_SEARCH_PROVIDER_REF,
        SEARXNG_SEARCH_ADAPTER_REF,
        searxng_query_ref(request.query),
    ]


def _exact_lease(request: SearxngSearchRequest) -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:web-search:test",
        mode=TrustMode.read_only,
        domains={AuthorityDomain.browser: [AuthorityCapability.read]},
        authority_constraints=[
            AuthorityConstraint(
                constraint_ref="authority-constraint-ref:web-search:exact-resources",
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=_exact_resource_refs(request),
                safe_summary="Restrict one search lease to exact request and provider refs.",
            )
        ],
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=10),
        safe_summary="Allow one exact governed read-only search request.",
    )


def _broad_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:web-search:broad",
        mode=TrustMode.read_only,
        domains={AuthorityDomain.browser: [AuthorityCapability.read]},
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=10),
        safe_summary="Broad read-only browser lease lacks exact provider resources.",
    )


def _fixture_transport(calls: list[SearxngSearchRequest]):  # type: ignore[no-untyped-def]
    def transport(request: SearxngSearchRequest) -> dict[str, Any]:
        calls.append(request)
        return {
            "results": [
                {
                    "url": "https://example.org/one",
                    "title": "First public source",
                    "content": "Bounded untrusted snippet one.",
                },
                {
                    "url": "http://127.0.0.1/private",
                    "title": "Private target must be filtered",
                    "content": "Filtered.",
                },
                {
                    "url": "https://example.net/two",
                    "title": "Second public source",
                    "content": "Bounded untrusted snippet two.",
                },
                {
                    "url": "https://example.com/three",
                    "title": "Over the result limit",
                    "content": "Filtered by the result ceiling.",
                },
            ]
        }

    return transport


def test_default_web_policy_keeps_search_denied() -> None:
    request = WebAccessRequest(
        kind=WebAccessRequestKind.SEARCH,
        query="bounded query",
        metadata={
            "page": 1,
            "max_results": 2,
            "category": "general",
            "language": "en",
            "safe_search": 1,
        },
    )

    decision = WebAccessPolicy().evaluate(request)

    assert decision.status == WebAccessPolicyStatus.DENIED
    assert decision.reasons == ("request_kind_not_enabled:search",)


def test_enabled_policy_allows_only_exact_bounded_shape() -> None:
    policy = WebAccessPolicy(allow_searxng_search=True)
    base = WebAccessRequest(
        kind=WebAccessRequestKind.SEARCH,
        query="bounded query",
        authority_mode=WebAccessAuthorityMode.READ_ONLY,
        network_lane=WebAccessNetworkLane.AGENT_PUBLIC_WEB,
        metadata={
            "page": 1,
            "max_results": 2,
            "category": "general",
            "language": "en",
            "safe_search": 1,
        },
    )

    assert policy.evaluate(base).allowed is True
    assert policy.evaluate(replace(base, url="https://example.org")).allowed is False
    assert policy.evaluate(replace(base, method="POST")).allowed is False
    assert (
        policy.evaluate(
            replace(base, metadata={**base.metadata, "max_results": 11})
        ).allowed
        is False
    )
    assert (
        policy.evaluate(
            replace(base, metadata={**base.metadata, "category": "images"})
        ).allowed
        is False
    )
    assert (
        policy.evaluate(
            replace(base, metadata={**base.metadata, "caller_endpoint": True})
        ).allowed
        is False
    )


def test_approval_identifier_without_exact_grant_never_calls_transport() -> None:
    request = _request()
    calls: list[SearxngSearchRequest] = []

    result = execute_searxng_search(
        request,
        capability_state=_state(),
        approval_authority=LocalApprovalAuthority(),
        authority_leases=[_exact_lease(request)],
        transport=_fixture_transport(calls),
        evaluated_at=NOW,
    )

    assert calls == []
    assert result.execution_succeeded is False
    assert result.status == WebProviderTransportStatus.blocked
    assert result.invocation_decision.outcome == InvocationDecisionOutcome.blocked
    assert result.transport_receipt.network_call_performed is False
    assert result.gateway_audit_ref.startswith(
        "web-access-audit-correlation-ref:sha256:"
    )


def test_broad_authority_lease_never_calls_transport() -> None:
    request = _request()
    calls: list[SearxngSearchRequest] = []

    result = execute_searxng_search(
        request,
        capability_state=_state(),
        approval_authority=_approval_authority(request),
        authority_leases=[_broad_lease()],
        transport=_fixture_transport(calls),
        evaluated_at=NOW,
    )

    assert calls == []
    assert (
        result.invocation_decision.outcome == InvocationDecisionOutcome.lease_required
    )
    assert "EXACT_AUTHORITY_LEASE_SCOPE_REQUIRED" in result.reason_codes
    assert result.transport_receipt.network_call_performed is False


def test_query_change_cannot_reuse_prior_exact_authority_scope() -> None:
    original = _request()
    changed = original.model_copy(update={"query": "different safe query"})
    calls: list[SearxngSearchRequest] = []

    result = execute_searxng_search(
        changed,
        capability_state=_state(),
        approval_authority=_approval_authority(changed),
        authority_leases=[_exact_lease(original)],
        transport=_fixture_transport(calls),
        evaluated_at=NOW,
    )

    assert searxng_query_ref(original.query) != searxng_query_ref(changed.query)
    assert calls == []
    assert result.invocation_decision.outcome == InvocationDecisionOutcome.lease_required
    assert "EXACT_AUTHORITY_LEASE_SCOPE_REQUIRED" in result.reason_codes


@pytest.mark.parametrize(
    ("state_update", "expected_code"),
    [
        (
            {"safe_disable_status": SafeDisableStatus.active},
            "SAFE_DISABLE_NOT_INACTIVE",
        ),
        (
            {
                "health_status": HealthStatus.stale,
                "freshness_status": FreshnessStatus.stale,
            },
            "RUNTIME_READINESS_NOT_READY",
        ),
    ],
)
def test_unready_or_safe_disabled_state_never_calls_transport(
    state_update: dict[str, Any],
    expected_code: str,
) -> None:
    request = _request()
    calls: list[SearxngSearchRequest] = []

    result = execute_searxng_search(
        request,
        capability_state=_state(**state_update),
        approval_authority=_approval_authority(request),
        authority_leases=[_exact_lease(request)],
        transport=_fixture_transport(calls),
        evaluated_at=NOW,
    )

    assert calls == []
    assert result.status == WebProviderTransportStatus.blocked
    assert expected_code in result.blocker_codes


def test_exact_gates_route_through_gateway_and_normalize_untrusted_results() -> None:
    request = _request(query="sensitive ephemeral query text")
    calls: list[SearxngSearchRequest] = []

    result = execute_searxng_search(
        request,
        capability_state=_state(),
        approval_authority=_approval_authority(request),
        authority_leases=[_exact_lease(request)],
        transport=_fixture_transport(calls),
        evaluated_at=NOW,
    )

    assert len(calls) == 1
    assert result.status == WebProviderTransportStatus.simulated
    assert result.execution_succeeded is False
    assert result.invocation_decision.outcome == InvocationDecisionOutcome.allow
    assert result.invocation_decision.cache_posture == "not_cacheable"
    assert result.invocation_decision.authority_lease_required is True
    assert result.invocation_decision.local_approval_required is True
    assert [item.host for item in result.evidence] == ["example.org", "example.net"]
    assert all(item.content_untrusted for item in result.evidence)
    assert all(item.instruction_use_allowed is False for item in result.evidence)
    assert result.transport_receipt.network_call_performed is False
    serialized = result.model_dump_json()
    assert result.gateway_audit_ref.startswith("web-access-audit-ref:sha256:")
    assert request.query not in serialized
    assert result.query_ref == searxng_query_ref(request.query)
    assert result.raw_provider_payload_stored is False
    assert '"results"' not in serialized


def test_invalid_provider_shape_fails_closed_without_retaining_payload() -> None:
    request = _request()

    result = execute_searxng_search(
        request,
        capability_state=_state(),
        approval_authority=_approval_authority(request),
        authority_leases=[_exact_lease(request)],
        transport=lambda _request: {"results": "not-a-list", "unsafe": "omitted"},
        evaluated_at=NOW,
    )

    assert result.status == WebProviderTransportStatus.failed
    assert result.evidence == ()
    assert result.transport_receipt.network_call_performed is False
    assert result.reason_codes == ("SEARXNG_RESULTS_LIST_REQUIRED",)
    assert "not-a-list" not in result.model_dump_json()


def test_request_rejects_caller_endpoint_and_config_rejects_remote_endpoint() -> None:
    with pytest.raises(ValidationError):
        SearxngSearchRequest(
            **_request().model_dump(mode="python"),
            caller_endpoint="http://127.0.0.1:9999",
        )

    with pytest.raises((ValidationError, ValueError), match="SEARXNG_CONFIGURED"):
        SearxngConfiguredEndpoint(base_url="https://example.org")


def test_firecrawl_operations_remain_policy_denied_in_search_phase() -> None:
    decision = WebAccessPolicy(allow_searxng_search=True).evaluate(
        WebAccessRequest(
            kind=WebAccessRequestKind.EXTRACT_MARKDOWN,
            url="https://example.org",
        )
    )

    assert decision.status == WebAccessPolicyStatus.DENIED
    assert decision.reasons == ("request_kind_not_enabled:extract_markdown",)
