from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from pydantic import SecretStr, ValidationError

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
    ResourceBudgetStatus,
    SafeDisableStatus,
)
from ultimate_ai_agent.core.web_access.firecrawl_cloud import (
    FIRECRAWL_CLOUD_ADAPTER_REF,
    FIRECRAWL_CLOUD_CAPABILITY_REF,
    FIRECRAWL_CLOUD_CREDENTIAL_REF,
    FIRECRAWL_CLOUD_PROVIDER_REF,
    FIRECRAWL_FREE_PLAN_CONCURRENCY,
    FIRECRAWL_FREE_PLAN_CREDITS,
    FirecrawlCloudCredential,
    FirecrawlCloudMarkdownRequest,
    FirecrawlCloudTransportError,
    build_firecrawl_cloud_scrape_payload,
    execute_firecrawl_cloud_markdown,
    reconcile_firecrawl_cloud_credits,
    resolve_firecrawl_cloud_credential,
)
from ultimate_ai_agent.core.web_access.firecrawl_markdown import (
    firecrawl_target_source_ref,
)
from ultimate_ai_agent.core.web_access.hybrid_contracts import (
    WebCreditReservationStatus,
    WebProviderDeploymentKind,
    WebProviderOperation,
    WebProviderPlanKind,
    WebProviderTransportStatus,
    build_web_provider_capability_state,
)
from ultimate_ai_agent.core.web_access.hybrid_ledger import InMemoryWebCreditLedger


NOW = datetime(2026, 7, 10, 20, 0, tzinfo=timezone.utc)
TARGET_URL = "https://example.org/"


def _credential() -> FirecrawlCloudCredential:
    return FirecrawlCloudCredential(value=SecretStr("fc-" + "x" * 32))


def _credit_payload(*, remaining: int = 10, plan: int = 1_000) -> dict[str, Any]:
    return {
        "success": True,
        "data": {
            "remainingCredits": remaining,
            "planCredits": plan,
            "billingPeriodStart": "2026-07-01T00:00:00Z",
            "billingPeriodEnd": "2026-08-01T00:00:00Z",
            "providerPrivateField": "must not escape",
        },
        "providerAccountPayload": {"must": "not escape"},
    }


def _reconcile(*, remaining: int = 10, plan: int = 1_000, at: datetime = NOW):
    return reconcile_firecrawl_cloud_credits(
        _credential(),
        transport=lambda _credential: _credit_payload(remaining=remaining, plan=plan),
        fetched_at=at,
    )


def _request(**overrides: Any) -> FirecrawlCloudMarkdownRequest:
    values: dict[str, Any] = {
        "request_ref": "web-extract-request-ref:cloud:test",
        "task_ref": "task-ref:web-extract:cloud:test",
        "approval_ref": "approval-ref:web-extract:cloud:test",
        "target_url": TARGET_URL,
        "target_source_ref": firecrawl_target_source_ref(TARGET_URL),
        "allowed_domains": ("example.org",),
        "max_markdown_chars": 10_000,
        "expected_execution_receipt_ref": "execution-receipt-ref:web-extract:cloud:test",
        "idempotency_ref": "idempotency-ref:web-extract:cloud:test",
        "routing_decision_ref": "web-routing-decision-ref:cloud:test",
        "run_credit_ceiling": 100,
    }
    values.update(overrides)
    return FirecrawlCloudMarkdownRequest(**values)


def _state(**overrides: Any):  # type: ignore[no-untyped-def]
    values: dict[str, Any] = {
        "state_ref": "web-provider-capability-state-ref:firecrawl-cloud:test",
        "provider_ref": FIRECRAWL_CLOUD_PROVIDER_REF,
        "deployment": WebProviderDeploymentKind.firecrawl_cloud,
        "operation": WebProviderOperation.scrape_markdown,
        "version_ref": "version-ref:firecrawl-cloud:v2",
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
        "reason_codes": ("FIRECRAWL_CLOUD_CREDENTIAL_READY",),
    }
    values.update(overrides)
    return build_web_provider_capability_state(**values)


def _approval(request: FirecrawlCloudMarkdownRequest) -> LocalApprovalAuthority:
    return LocalApprovalAuthority(
        [
            CapabilityApprovalGrant(
                approval_ref=request.approval_ref or "approval-ref:missing",
                capability_id=FIRECRAWL_CLOUD_CAPABILITY_REF,
                task_id=request.task_ref,
                granted_by="operator-ref:test",
            )
        ]
    )


def _resource_refs(request: FirecrawlCloudMarkdownRequest, snapshot: Any) -> list[str]:
    return [
        request.request_ref,
        request.task_ref,
        request.target_source_ref,
        request.idempotency_ref,
        request.routing_decision_ref,
        snapshot.snapshot_ref,
        snapshot.billing_period_ref,
        FIRECRAWL_CLOUD_CAPABILITY_REF,
        FIRECRAWL_CLOUD_PROVIDER_REF,
        FIRECRAWL_CLOUD_ADAPTER_REF,
        "cost-policy-ref:firecrawl-standard-scrape:v1",
    ]


def _lease(request: FirecrawlCloudMarkdownRequest, snapshot: Any) -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:web-extract:cloud:test",
        mode=TrustMode.read_only,
        domains={AuthorityDomain.browser: [AuthorityCapability.read]},
        authority_constraints=[
            AuthorityConstraint(
                constraint_ref="authority-constraint-ref:web-extract:cloud:resources",
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=_resource_refs(request, snapshot),
                safe_summary="Restrict cloud extraction to exact provider and budget refs.",
            )
        ],
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=10),
        safe_summary="Allow one exact governed free-plan cloud extraction.",
    )


def _scrape(calls: list[FirecrawlCloudMarkdownRequest]):  # type: ignore[no-untyped-def]
    def transport(
        request: FirecrawlCloudMarkdownRequest,
        _credential: FirecrawlCloudCredential,
    ) -> dict[str, Any]:
        calls.append(request)
        return {
            "success": True,
            "data": {
                "markdown": "# Cloud evidence\n\nTransient and untrusted.",
                "metadata": {
                    "sourceURL": request.target_url,
                    "url": request.target_url,
                    "statusCode": 200,
                },
            },
            "providerPrivateField": "must not escape",
        }

    return transport


def test_credit_snapshot_normalizes_only_current_free_plan_safe_truth() -> None:
    result = _reconcile()

    assert result.status == WebProviderTransportStatus.simulated
    assert result.snapshot is not None
    assert result.snapshot.plan_kind == WebProviderPlanKind.free
    assert result.snapshot.plan_credits == FIRECRAWL_FREE_PLAN_CREDITS
    assert result.snapshot.max_concurrency == FIRECRAWL_FREE_PLAN_CONCURRENCY
    assert result.snapshot.credential_ref == FIRECRAWL_CLOUD_CREDENTIAL_REF
    assert "providerPrivateField" not in result.model_dump_json()
    assert "providerAccountPayload" not in result.model_dump_json()


def test_provider_additional_balance_does_not_change_free_plan_classification() -> None:
    result = _reconcile(remaining=1_400)

    assert result.snapshot is not None
    assert result.snapshot.plan_kind == WebProviderPlanKind.free
    assert result.snapshot.plan_credits == 1_000
    assert result.snapshot.remaining_credits == 1_400


def test_paid_or_unknown_plan_preserves_uncertainty_and_cannot_execute() -> None:
    paid = _reconcile(plan=5_000).snapshot
    unknown = _reconcile(plan=500).snapshot

    assert paid is not None and paid.plan_kind == WebProviderPlanKind.paid
    assert unknown is not None and unknown.plan_kind == WebProviderPlanKind.unknown
    assert paid.max_concurrency is None
    assert unknown.max_concurrency is None


def test_cloud_payload_is_exact_basic_one_page_without_provider_cache() -> None:
    payload = build_firecrawl_cloud_scrape_payload(_request())

    assert payload == {
        "url": TARGET_URL,
        "formats": ["markdown"],
        "onlyMainContent": True,
        "maxAge": 0,
        "waitFor": 0,
        "timeout": 15_000,
        "removeBase64Images": True,
        "blockAds": True,
        "proxy": "basic",
        "storeInCache": False,
    }
    assert not {
        "actions",
        "headers",
        "location",
        "screenshot",
        "extract",
        "skipTlsVerification",
    }.intersection(payload)


def test_missing_snapshot_or_approval_identifier_alone_blocks_before_scrape() -> None:
    request = _request()
    scrape_calls: list[FirecrawlCloudMarkdownRequest] = []

    missing_snapshot = execute_firecrawl_cloud_markdown(
        request,
        capability_state=_state(),
        credit_snapshot=None,
        ledger=InMemoryWebCreditLedger(),
        credential=_credential(),
        approval_authority=_approval(request),
        authority_leases=[],
        scrape_transport=_scrape(scrape_calls),
        target_validator=lambda _url: None,
        evaluated_at=NOW,
    )
    snapshot = _reconcile().snapshot
    assert snapshot is not None
    identifier_only = execute_firecrawl_cloud_markdown(
        request,
        capability_state=_state(),
        credit_snapshot=snapshot,
        ledger=InMemoryWebCreditLedger(),
        credential=_credential(),
        approval_authority=LocalApprovalAuthority(),
        authority_leases=[_lease(request, snapshot)],
        scrape_transport=_scrape(scrape_calls),
        target_validator=lambda _url: None,
        evaluated_at=NOW,
    )

    assert scrape_calls == []
    assert missing_snapshot.status == WebProviderTransportStatus.blocked
    assert "CLOUD_CREDIT_SNAPSHOT_MISSING" in missing_snapshot.reason_codes
    assert identifier_only.status == WebProviderTransportStatus.blocked
    assert identifier_only.reservation is None


def test_exact_fake_cloud_attempt_reserves_reconciles_and_settles_one_credit() -> None:
    request = _request()
    before = _reconcile(remaining=10).snapshot
    assert before is not None
    scrape_calls: list[FirecrawlCloudMarkdownRequest] = []

    result = execute_firecrawl_cloud_markdown(
        request,
        capability_state=_state(),
        credit_snapshot=before,
        ledger=InMemoryWebCreditLedger(),
        credential=_credential(),
        approval_authority=_approval(request),
        authority_leases=[_lease(request, before)],
        scrape_transport=_scrape(scrape_calls),
        credit_transport=lambda _credential: _credit_payload(remaining=9),
        target_validator=lambda _url: None,
        evaluated_at=NOW,
    )

    assert len(scrape_calls) == 1
    assert result.status == WebProviderTransportStatus.simulated
    assert result.execution_succeeded is False
    assert result.evidence is not None
    assert result.evidence.content_untrusted is True
    assert result.evidence.instruction_use_allowed is False
    assert result.reservation is not None
    assert result.reservation.status == WebCreditReservationStatus.settled
    assert result.credit_snapshot_before_ref == before.snapshot_ref
    assert result.credit_snapshot_after_ref is not None
    serialized = result.model_dump_json()
    assert _credential().value.get_secret_value() not in serialized
    assert "providerPrivateField" not in serialized


def test_incomplete_usage_delta_fails_closed_and_blocks_follow_on_credit() -> None:
    request = _request()
    before = _reconcile(remaining=10).snapshot
    assert before is not None
    ledger = InMemoryWebCreditLedger()

    result = execute_firecrawl_cloud_markdown(
        request,
        capability_state=_state(),
        credit_snapshot=before,
        ledger=ledger,
        credential=_credential(),
        approval_authority=_approval(request),
        authority_leases=[_lease(request, before)],
        scrape_transport=_scrape([]),
        credit_transport=lambda _credential: _credit_payload(remaining=10),
        target_validator=lambda _url: None,
        evaluated_at=NOW,
    )

    assert result.status == WebProviderTransportStatus.failed
    assert result.evidence is None
    assert result.reservation is not None
    assert result.reservation.status == WebCreditReservationStatus.incomplete
    assert "FIRECRAWL_CLOUD_USAGE_PROOF_INCOMPLETE" in result.reason_codes


def test_safe_cloud_transport_error_survives_gateway_without_raw_detail() -> None:
    request = _request()
    before = _reconcile(remaining=10).snapshot
    assert before is not None

    def failed_transport(
        _request: FirecrawlCloudMarkdownRequest,
        _credential: FirecrawlCloudCredential,
    ) -> dict[str, Any]:
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_PROVIDER_NON_SUCCESS",
            network_call_performed=True,
        )

    failed_transport.real_world_transport_performed = True  # type: ignore[attr-defined]
    result = execute_firecrawl_cloud_markdown(
        request,
        capability_state=_state(),
        credit_snapshot=before,
        ledger=InMemoryWebCreditLedger(),
        credential=_credential(),
        approval_authority=_approval(request),
        authority_leases=[_lease(request, before)],
        scrape_transport=failed_transport,
        credit_transport=lambda _credential: _credit_payload(remaining=10),
        target_validator=lambda _url: None,
        evaluated_at=NOW,
    )

    assert result.status == WebProviderTransportStatus.failed
    assert result.evidence is None
    assert result.reason_codes == ("FIRECRAWL_CLOUD_PROVIDER_NON_SUCCESS",)


def test_credential_resolver_rejects_wrong_path_and_permissions(tmp_path: Path) -> None:
    wrong = tmp_path / "credential"
    wrong.write_text("fc-" + "x" * 32, encoding="ascii")
    with pytest.raises(FirecrawlCloudTransportError) as wrong_path:
        resolve_firecrawl_cloud_credential(wrong)
    assert wrong_path.value.code == "FIRECRAWL_CLOUD_CREDENTIAL_SOURCE_DENIED"

    exact = tmp_path / ".uaa" / "local-web-services" / "firecrawl_cloud_api_key"
    exact.parent.mkdir(parents=True)
    exact.write_text("fc-" + "x" * 32, encoding="ascii")
    os.chmod(exact, 0o644)
    with pytest.raises(FirecrawlCloudTransportError) as permissions:
        resolve_firecrawl_cloud_credential(exact)
    assert permissions.value.code == "FIRECRAWL_CLOUD_CREDENTIAL_FILE_MODE_DENIED"

    os.chmod(exact, 0o600)
    credential = resolve_firecrawl_cloud_credential(exact)
    assert credential.credential_ref == FIRECRAWL_CLOUD_CREDENTIAL_REF
    assert credential.value.get_secret_value() not in repr(credential)


def test_cloud_request_forbids_provider_actions() -> None:
    with pytest.raises(ValidationError):
        FirecrawlCloudMarkdownRequest(
            **_request().model_dump(mode="python"),
            actions=[{"type": "click"}],
        )
