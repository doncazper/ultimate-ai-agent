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
    FIRECRAWL_MARKDOWN_ADAPTER_REF,
    FIRECRAWL_MARKDOWN_CAPABILITY_REF,
    FIRECRAWL_SELF_HOSTED_PROVIDER_REF,
    FirecrawlConfiguredEndpoint,
    FirecrawlMarkdownRequest,
    FirecrawlPreviewRedactionStatus,
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
    execute_firecrawl_markdown,
    firecrawl_target_source_ref,
)


NOW = datetime(2026, 7, 10, 19, 0, tzinfo=timezone.utc)
TARGET_URL = "https://example.org/"


def _request(**overrides: Any) -> FirecrawlMarkdownRequest:
    values: dict[str, Any] = {
        "request_ref": "web-extract-request-ref:test",
        "task_ref": "task-ref:web-extract:test",
        "approval_ref": "approval-ref:web-extract:test",
        "target_url": TARGET_URL,
        "target_source_ref": firecrawl_target_source_ref(TARGET_URL),
        "allowed_domains": ("example.org",),
        "max_markdown_chars": 10_000,
        "expected_execution_receipt_ref": "execution-receipt-ref:web-extract:test",
    }
    values.update(overrides)
    return FirecrawlMarkdownRequest(**values)


def _state(**overrides: Any):  # type: ignore[no-untyped-def]
    values: dict[str, Any] = {
        "state_ref": "web-provider-capability-state-ref:firecrawl-markdown:test",
        "provider_ref": FIRECRAWL_SELF_HOSTED_PROVIDER_REF,
        "deployment": WebProviderDeploymentKind.firecrawl_self_hosted,
        "operation": WebProviderOperation.scrape_markdown,
        "version_ref": "version-ref:firecrawl:v2.9.0",
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
        "reason_codes": ("FIRECRAWL_LOOPBACK_HEALTHY",),
    }
    values.update(overrides)
    return build_web_provider_capability_state(**values)


def _approval_authority(
    request: FirecrawlMarkdownRequest,
    *,
    capability_ref: str = FIRECRAWL_MARKDOWN_CAPABILITY_REF,
) -> LocalApprovalAuthority:
    return LocalApprovalAuthority(
        [
            CapabilityApprovalGrant(
                approval_ref=request.approval_ref or "approval-ref:web-extract:missing",
                capability_id=capability_ref,
                task_id=request.task_ref,
                granted_by="operator-ref:test",
            )
        ]
    )


def _exact_resource_refs(request: FirecrawlMarkdownRequest) -> list[str]:
    return [
        request.request_ref,
        request.task_ref,
        request.target_source_ref,
        FIRECRAWL_MARKDOWN_CAPABILITY_REF,
        FIRECRAWL_SELF_HOSTED_PROVIDER_REF,
        FIRECRAWL_MARKDOWN_ADAPTER_REF,
    ]


def _exact_lease(request: FirecrawlMarkdownRequest) -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:web-extract:test",
        mode=TrustMode.read_only,
        domains={AuthorityDomain.browser: [AuthorityCapability.read]},
        authority_constraints=[
            AuthorityConstraint(
                constraint_ref="authority-constraint-ref:web-extract:exact-resources",
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=_exact_resource_refs(request),
                safe_summary="Restrict one extraction lease to exact target and provider refs.",
            )
        ],
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=10),
        safe_summary="Allow one exact governed one-page markdown extraction.",
    )


def _broad_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:web-extract:broad",
        mode=TrustMode.read_only,
        domains={AuthorityDomain.browser: [AuthorityCapability.read]},
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=10),
        safe_summary="Broad browser read lease lacks exact target and provider resources.",
    )


def _fixture_transport(calls: list[FirecrawlMarkdownRequest]):  # type: ignore[no-untyped-def]
    def transport(request: FirecrawlMarkdownRequest) -> dict[str, Any]:
        calls.append(request)
        return {
            "success": True,
            "data": {
                "markdown": "# Example\n\nBounded public-page evidence.",
                "metadata": {
                    "sourceURL": request.target_url,
                    "url": request.target_url,
                    "statusCode": 200,
                    "title": "Example page",
                },
            },
            "providerInternal": {"must": "not escape"},
        }

    return transport


def _target_validator(calls: list[str]):  # type: ignore[no-untyped-def]
    def validate(url: str) -> None:
        calls.append(url)

    return validate


def _web_request(**overrides: Any) -> WebAccessRequest:
    values: dict[str, Any] = {
        "kind": WebAccessRequestKind.EXTRACT_MARKDOWN,
        "url": TARGET_URL,
        "method": "GET",
        "authority_mode": WebAccessAuthorityMode.READ_ONLY,
        "network_lane": WebAccessNetworkLane.AGENT_PUBLIC_WEB,
        "allowed_domains": ("example.org",),
        "metadata": {
            "format": "markdown",
            "page_count": 1,
            "attempt_count": 1,
            "max_markdown_chars": 10_000,
            "target_source_ref": firecrawl_target_source_ref(TARGET_URL),
        },
    }
    values.update(overrides)
    return WebAccessRequest(**values)


def test_default_policy_keeps_markdown_extraction_denied() -> None:
    decision = WebAccessPolicy().evaluate(_web_request())

    assert decision.status == WebAccessPolicyStatus.DENIED
    assert decision.reasons == ("request_kind_not_enabled:extract_markdown",)


def test_enabled_policy_separates_target_get_from_provider_transport() -> None:
    policy = WebAccessPolicy(allow_firecrawl_markdown_extract=True)
    base = _web_request()

    decision = policy.evaluate(base)

    assert decision.allowed is True
    assert decision.allowed_methods == ("GET",)
    assert policy.evaluate(replace(base, method="POST")).allowed is False
    assert policy.evaluate(replace(base, url="https://127.0.0.1/")).allowed is False
    assert policy.evaluate(replace(base, url=f"{TARGET_URL}?q=denied")).allowed is False
    assert (
        policy.evaluate(
            replace(base, metadata={**base.metadata, "actions": True})
        ).allowed
        is False
    )
    assert (
        policy.evaluate(
            replace(base, metadata={**base.metadata, "page_count": 2})
        ).allowed
        is False
    )


def test_approval_identifier_without_exact_grant_never_calls_transport() -> None:
    request = _request()
    transport_calls: list[FirecrawlMarkdownRequest] = []
    target_calls: list[str] = []

    result = execute_firecrawl_markdown(
        request,
        capability_state=_state(),
        approval_authority=LocalApprovalAuthority(),
        authority_leases=[_exact_lease(request)],
        transport=_fixture_transport(transport_calls),
        target_validator=_target_validator(target_calls),
        evaluated_at=NOW,
    )

    assert transport_calls == []
    assert target_calls == []
    assert result.status == WebProviderTransportStatus.blocked
    assert result.invocation_decision.outcome == InvocationDecisionOutcome.blocked
    assert result.transport_receipt.network_call_performed is False
    assert result.gateway_audit_ref.startswith(
        "web-access-audit-correlation-ref:sha256:"
    )


def test_broad_lease_never_calls_transport() -> None:
    request = _request()
    transport_calls: list[FirecrawlMarkdownRequest] = []

    result = execute_firecrawl_markdown(
        request,
        capability_state=_state(),
        approval_authority=_approval_authority(request),
        authority_leases=[_broad_lease()],
        transport=_fixture_transport(transport_calls),
        target_validator=lambda _url: None,
        evaluated_at=NOW,
    )

    assert transport_calls == []
    assert (
        result.invocation_decision.outcome == InvocationDecisionOutcome.lease_required
    )
    assert "EXACT_AUTHORITY_LEASE_SCOPE_REQUIRED" in result.reason_codes


@pytest.mark.parametrize(
    "state_update",
    [
        {"safe_disable_status": SafeDisableStatus.active},
        {
            "health_status": HealthStatus.stale,
            "freshness_status": FreshnessStatus.stale,
        },
    ],
)
def test_safe_disabled_or_stale_state_never_calls_transport(
    state_update: dict[str, Any],
) -> None:
    request = _request()
    transport_calls: list[FirecrawlMarkdownRequest] = []

    result = execute_firecrawl_markdown(
        request,
        capability_state=_state(**state_update),
        approval_authority=_approval_authority(request),
        authority_leases=[_exact_lease(request)],
        transport=_fixture_transport(transport_calls),
        target_validator=lambda _url: None,
        evaluated_at=NOW,
    )

    assert transport_calls == []
    assert result.status == WebProviderTransportStatus.blocked
    assert "RUNTIME_READINESS_NOT_READY" in result.blocker_codes


def test_exact_gates_return_transient_untrusted_markdown_and_safe_receipt() -> None:
    request = _request()
    transport_calls: list[FirecrawlMarkdownRequest] = []
    target_calls: list[str] = []

    result = execute_firecrawl_markdown(
        request,
        capability_state=_state(),
        approval_authority=_approval_authority(request),
        authority_leases=[_exact_lease(request)],
        transport=_fixture_transport(transport_calls),
        target_validator=_target_validator(target_calls),
        evaluated_at=NOW,
    )

    assert len(transport_calls) == 1
    assert target_calls == [request.target_url, request.target_url]
    assert result.status == WebProviderTransportStatus.simulated
    assert result.execution_succeeded is False
    assert result.invocation_decision.outcome == InvocationDecisionOutcome.allow
    assert result.evidence is not None
    assert result.evidence.markdown.startswith("# Example")
    assert result.evidence.content_untrusted is True
    assert result.evidence.instruction_use_allowed is False
    assert result.evidence.memory_write_allowed is False
    assert result.evidence.context_injection_allowed is False
    assert "providerInternal" not in result.model_dump_json()
    receipt_json = result.transport_receipt.model_dump_json()
    assert request.target_url not in receipt_json
    assert result.evidence.markdown not in receipt_json
    assert result.transport_receipt.target_method == "GET"
    assert result.transport_receipt.provider_transport_method == "POST"
    assert result.gateway_audit_ref.startswith("web-access-audit-ref:sha256:")


def test_redirected_final_url_is_rejected_after_provider_attempt() -> None:
    request = _request()

    def redirected(_request: FirecrawlMarkdownRequest) -> dict[str, Any]:
        return {
            "success": True,
            "data": {
                "markdown": "Redirected content must not be accepted.",
                "metadata": {
                    "sourceURL": request.target_url,
                    "url": "https://example.org/redirected",
                    "statusCode": 200,
                },
            },
        }

    result = execute_firecrawl_markdown(
        request,
        capability_state=_state(),
        approval_authority=_approval_authority(request),
        authority_leases=[_exact_lease(request)],
        transport=redirected,
        target_validator=lambda _url: None,
        evaluated_at=NOW,
    )

    assert result.status == WebProviderTransportStatus.failed
    assert result.evidence is None
    assert result.reason_codes == ("FIRECRAWL_TARGET_REDIRECT_DENIED",)


def test_target_resolution_failure_never_calls_provider_transport() -> None:
    request = _request()
    transport_calls: list[FirecrawlMarkdownRequest] = []

    def reject_target(_url: str) -> None:
        raise RuntimeError("unsafe target detail must remain private")

    result = execute_firecrawl_markdown(
        request,
        capability_state=_state(),
        approval_authority=_approval_authority(request),
        authority_leases=[_exact_lease(request)],
        transport=_fixture_transport(transport_calls),
        target_validator=reject_target,
        evaluated_at=NOW,
    )

    assert transport_calls == []
    assert result.status == WebProviderTransportStatus.failed
    assert result.evidence is None
    assert result.reason_codes == ("FIRECRAWL_TARGET_VALIDATION_FAILED",)
    assert result.transport_receipt.network_call_performed is False
    assert "unsafe target detail" not in result.model_dump_json()


def test_oversized_markdown_and_provider_payload_fields_fail_closed() -> None:
    request = _request(max_markdown_chars=1_024)

    result = execute_firecrawl_markdown(
        request,
        capability_state=_state(),
        approval_authority=_approval_authority(request),
        authority_leases=[_exact_lease(request)],
        transport=lambda _request: {
            "success": True,
            "data": {
                "markdown": "x" * 1_025,
                "metadata": {
                    "sourceURL": request.target_url,
                    "url": request.target_url,
                },
            },
            "rawHtml": "must not escape",
        },
        target_validator=lambda _url: None,
        evaluated_at=NOW,
    )

    assert result.status == WebProviderTransportStatus.failed
    assert result.reason_codes == ("FIRECRAWL_MARKDOWN_LIMIT_EXCEEDED",)
    assert "rawHtml" not in result.model_dump_json()


def test_preview_redacts_untrusted_contact_value() -> None:
    request = _request()
    untrusted_contact = "contact" + "@example.invalid"

    result = execute_firecrawl_markdown(
        request,
        capability_state=_state(),
        approval_authority=_approval_authority(request),
        authority_leases=[_exact_lease(request)],
        transport=lambda _request: {
            "success": True,
            "data": {
                "markdown": f"Public page contact: {untrusted_contact}",
                "metadata": {
                    "sourceURL": request.target_url,
                    "url": request.target_url,
                },
            },
        },
        target_validator=lambda _url: None,
        evaluated_at=NOW,
    )

    assert result.evidence is not None
    assert untrusted_contact not in result.evidence.bounded_redacted_preview
    assert (
        result.evidence.preview_redaction_status
        == FirecrawlPreviewRedactionStatus.redacted
    )


def test_request_and_config_reject_unsafe_target_or_endpoint_options() -> None:
    with pytest.raises((ValidationError, ValueError), match="FIRECRAWL_.*INVALID"):
        _request(
            target_url="https://127.0.0.1/",
            target_source_ref=firecrawl_target_source_ref("https://127.0.0.1/"),
            allowed_domains=("127.0.0.1",),
        )
    with pytest.raises(ValidationError):
        FirecrawlMarkdownRequest(
            **_request().model_dump(mode="python"),
            actions=[{"type": "click"}],
        )
    with pytest.raises((ValidationError, ValueError), match="FIRECRAWL_CONFIGURED"):
        FirecrawlConfiguredEndpoint(base_url="https://example.org")


def test_schema_extraction_stays_denied_in_markdown_phase() -> None:
    decision = WebAccessPolicy(allow_firecrawl_markdown_extract=True).evaluate(
        WebAccessRequest(
            kind=WebAccessRequestKind.EXTRACT_SCHEMA,
            url=TARGET_URL,
        )
    )

    assert decision.status == WebAccessPolicyStatus.DENIED
    assert decision.reasons == ("request_kind_not_enabled:extract_schema",)
