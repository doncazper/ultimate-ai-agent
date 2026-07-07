import json
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AUTHORITY_STATE_DIR_ENV,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.providers import (
    DeterministicProviderCredentialValidationAdapter,
    ExactProviderCredentialValidationReceipt,
    ExactProviderCredentialValidationRequest,
    OpenAICompatibleCredentialValidationAdapter,
    ProviderCredentialValidationAdapter,
    ProviderCredentialValidationAdapterRequest,
    ProviderCredentialValidationReceiptStore,
    ProviderCredentialValidationStatus,
    build_provider_credential_validation_approval_request,
    build_provider_credential_validation_readiness,
    evaluate_provider_credential_validation,
)
from ultimate_ai_agent.core.providers.credential_validation import (
    PROVIDER_CREDENTIAL_VALIDATION_POLICY_REF,
    PROVIDER_CREDENTIAL_VALIDATION_PROVIDER_REF,
    PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_SUMMARY,
    PROVIDER_CREDENTIAL_VALIDATION_ROUTE,
)


def validation_request(**overrides: object) -> ExactProviderCredentialValidationRequest:
    values: dict[str, object] = {
        "validation_ref": "provider-credential-validation-ref:test",
        "run_id": "run-ref:provider-credential-validation-test",
        "provider_ref": PROVIDER_CREDENTIAL_VALIDATION_PROVIDER_REF,
        "credential_ref": "credential-ref:openai-compatible:validation-test",
        "policy_ref": PROVIDER_CREDENTIAL_VALIDATION_POLICY_REF,
        "approval_ref": "approval-ref:provider-credential-validation:test",
        "approval_scope_ref": "approval-scope-ref:provider-credential-validation:test",
        "idempotency_ref": "idempotency:provider-credential-validation:test",
        "validation_receipt_ref": "receipt:provider-credential-validation:test",
        "revocation_ref": "revocation-ref:provider-credential-validation:test",
        "safe_disable_ref": "safe-disable-ref:provider-credential-validation:test",
        "provider_manifest_ref": "provider-manifest-ref:openai-compatible:validation",
        "provider_allowlist_ref": "provider-allowlist-ref:openai-compatible:validation",
        "rate_budget_ref": "rate-budget-ref:provider-credential-validation:test",
        "redacted_validation_summary_ref": (
            "redacted-validation-summary-ref:provider-credential-validation:test"
        ),
    }
    values.update(overrides)
    return ExactProviderCredentialValidationRequest(**values)


def exact_authority_for(
    request: ExactProviderCredentialValidationRequest,
) -> LocalApprovalAuthority:
    authority = LocalApprovalAuthority()
    approval_request = build_provider_credential_validation_approval_request(request)
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator:local",
        approval_ref=request.approval_ref,
    )
    authority.issue_authority_lease(provider_validation_authority_lease())
    return authority


def exact_approval_only_authority_for(
    request: ExactProviderCredentialValidationRequest,
) -> LocalApprovalAuthority:
    authority = LocalApprovalAuthority()
    approval_request = build_provider_credential_validation_approval_request(request)
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator:local",
        approval_ref=request.approval_ref,
    )
    return authority


def provider_validation_authority_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:provider-credential-validation-execute-test",
        mode=TrustMode.full_machine_access_session,
        domains={
            AuthorityDomain.provider_model_calls: [
                AuthorityCapability.read,
                AuthorityCapability.execute,
            ]
        },
        constraints={
            "provider_lane_ref": (
                "provider-credential-validation-lane:exact-approved:v1"
            ),
            "model_invocation_allowed": False,
        },
        safe_summary=(
            "Test lease grants exact provider credential validation execution "
            "without model invocation authority."
        ),
    )


def evaluate_with_exact_approval(
    request: ExactProviderCredentialValidationRequest,
    *,
    credential_secret: str | None = "redacted-safe-test-credential",
    **kwargs: object,
):
    return evaluate_provider_credential_validation(
        request,
        approval_authority=exact_authority_for(request),
        credential_secret=credential_secret,
        **kwargs,
    )


class SpyProviderCredentialValidationAdapter(ProviderCredentialValidationAdapter):
    enabled = True

    def __init__(self) -> None:
        self.called = False

    def validate(self, request: ProviderCredentialValidationAdapterRequest):
        self.called = True
        return DeterministicProviderCredentialValidationAdapter().validate(request)


def test_default_readiness_is_blocked_and_non_authorizing() -> None:
    readiness = build_provider_credential_validation_readiness()

    assert readiness.status == ProviderCredentialValidationStatus.validation_blocked
    assert readiness.validation_enabled is False
    assert readiness.provider_network_call_enabled_by_default is False
    assert readiness.provider_sdk_call_enabled is False
    assert readiness.model_invocation_enabled is False
    assert readiness.billing_authority_granted is False
    assert set(readiness.ui_states) == {
        "validation blocked",
        "credential valid",
        "credential invalid",
        "approval required",
        "no provider authority",
    }


def test_public_request_is_safe_refs_only_and_adapter_request_hides_transient_secret() -> None:
    request = validation_request()
    public_payload = request.model_dump(mode="json")
    public_schema = ExactProviderCredentialValidationRequest.model_json_schema()
    with pytest.raises(ValidationError):
        ExactProviderCredentialValidationRequest(
            **public_payload,
            credential_secret="redacted-safe-test-credential",
        )

    adapter_request = ProviderCredentialValidationAdapterRequest(
        **public_payload,
        credential_secret="redacted-safe-test-credential",
    )
    payload = adapter_request.model_dump(mode="json")
    serialized = json.dumps(payload, sort_keys=True)

    assert "credential_secret" not in public_payload
    assert "credential_secret" not in public_schema["properties"]
    assert "credential_secret" not in payload
    assert "redacted-safe-test-credential" not in serialized


def test_request_rejects_unsafe_ref_fields() -> None:
    with pytest.raises(
        ValidationError,
        match="PROVIDER_CREDENTIAL_VALIDATION_REQUEST_UNSAFE_REF_REJECTED",
    ):
        validation_request(credential_ref="credential-ref:provider-runtime:../secret")


def test_request_rejects_data_classification_downgrade() -> None:
    with pytest.raises(
        ValidationError,
        match="PROVIDER_CREDENTIAL_VALIDATION_REQUEST_DATA_CLASSIFICATION_DENIED",
    ):
        validation_request(
            data_classification=DataClassification(
                classification=ClassificationValue.public,
                source="client-supplied-downgrade",
                requires_redaction=False,
                requires_consent=False,
            )
        )


def test_client_supplied_approval_grants_are_not_accepted() -> None:
    values = validation_request().model_dump(mode="json")
    values["approval_grants"] = []

    with pytest.raises(ValidationError):
        ExactProviderCredentialValidationRequest(**values)


def test_authority_lease_is_required_before_credential_validation() -> None:
    adapter = SpyProviderCredentialValidationAdapter()
    decision = evaluate_provider_credential_validation(
        validation_request(),
        adapter=adapter,
        approval_authority=exact_approval_only_authority_for(validation_request()),
    )

    assert decision.status == ProviderCredentialValidationStatus.validation_blocked
    assert "AUTHORITY_LEASE_REQUIRED" in decision.reason_codes
    assert decision.authority_decision is not None
    assert decision.authority_decision.outcome == "deny"
    assert adapter.called is False
    assert decision.receipt is None


def test_missing_exact_approval_blocks_after_authority_lease() -> None:
    adapter = SpyProviderCredentialValidationAdapter()
    decision = evaluate_provider_credential_validation(
        validation_request(),
        adapter=adapter,
        active_authority_leases=[provider_validation_authority_lease()],
    )

    assert decision.status == ProviderCredentialValidationStatus.validation_blocked
    assert "APPROVAL_REF_UNKNOWN" in decision.reason_codes
    assert decision.authority_decision is not None
    assert decision.authority_decision.outcome == "allow"
    assert adapter.called is False
    assert decision.receipt is None


def test_wrong_policy_and_provider_refs_block() -> None:
    wrong_policy = evaluate_with_exact_approval(
        validation_request(policy_ref="policy-ref:provider-credential-validation:wrong")
    )
    wrong_provider = evaluate_provider_credential_validation(
        validation_request(provider_ref="provider-ref:provider-runtime:not-bound")
    )

    assert "POLICY_REF_NOT_ALLOWED" in wrong_policy.reason_codes
    assert "PROVIDER_REF_REQUIRED" in wrong_provider.reason_codes


def test_exact_approval_with_default_adapter_stays_blocked() -> None:
    decision = evaluate_with_exact_approval(validation_request())

    assert decision.status == ProviderCredentialValidationStatus.validation_blocked
    assert (
        "PROVIDER_CREDENTIAL_VALIDATION_ADAPTER_DISABLED_BY_DEFAULT"
        in decision.reason_codes
    )
    assert decision.receipt is None


def test_enabled_adapter_requires_transient_secret() -> None:
    decision = evaluate_with_exact_approval(
        validation_request(),
        credential_secret=None,
        adapter=DeterministicProviderCredentialValidationAdapter(),
    )

    assert decision.status == ProviderCredentialValidationStatus.validation_blocked
    assert (
        "TRANSIENT_CREDENTIAL_SECRET_REQUIRED_FOR_VALIDATION" in decision.reason_codes
    )


def test_valid_and_invalid_credentials_record_redacted_receipts(tmp_path: Path) -> None:
    store = ProviderCredentialValidationReceiptStore(tmp_path / "receipts.jsonl")
    valid = evaluate_with_exact_approval(
        validation_request(validation_ref="provider-credential-validation-ref:valid"),
        adapter=DeterministicProviderCredentialValidationAdapter(
            ProviderCredentialValidationStatus.credential_valid
        ),
        receipt_store=store,
    )
    invalid = evaluate_with_exact_approval(
        validation_request(
            validation_ref="provider-credential-validation-ref:invalid",
            validation_receipt_ref="receipt:provider-credential-validation:invalid",
        ),
        adapter=DeterministicProviderCredentialValidationAdapter(
            ProviderCredentialValidationStatus.credential_invalid
        ),
        receipt_store=store,
    )

    assert valid.allowed is True
    assert valid.status == ProviderCredentialValidationStatus.credential_valid
    assert valid.authority_decision is not None
    assert valid.authority_decision.outcome == "allow"
    assert invalid.allowed is True
    assert invalid.status == ProviderCredentialValidationStatus.credential_invalid
    receipts = store.list_receipts()
    assert len(receipts) == 2
    receipt_json = json.dumps(
        [receipt.model_dump(mode="json") for receipt in receipts],
        sort_keys=True,
    )
    assert "redacted-safe-test-credential" not in receipt_json
    assert "prompt" not in receipt_json
    assert "response" not in receipt_json
    assert all(
        receipt.safe_summary == PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_SUMMARY
        for receipt in receipts
    )
    assert all(receipt.model_invocation_performed is False for receipt in receipts)
    assert all(receipt.provider_payload_persisted is False for receipt in receipts)


def test_blocked_provider_network_attempt_records_redacted_receipt(
    tmp_path: Path,
) -> None:
    store = ProviderCredentialValidationReceiptStore(tmp_path / "receipts.jsonl")

    def transport(endpoint_url: str, credential_secret: str, timeout: float) -> int:
        assert endpoint_url.endswith("/v1/models")
        assert credential_secret == "redacted-safe-test-credential"
        assert timeout > 0
        return 500

    decision = evaluate_with_exact_approval(
        validation_request(
            validation_ref="provider-credential-validation-ref:blocked-transport",
            validation_receipt_ref="receipt:provider-credential-validation:blocked-transport",
        ),
        adapter=OpenAICompatibleCredentialValidationAdapter(
            enabled=True,
            transport=transport,
        ),
        receipt_store=store,
    )

    assert decision.allowed is False
    assert decision.status == ProviderCredentialValidationStatus.validation_blocked
    assert decision.receipt is not None
    assert decision.receipt.validation_performed is True
    assert decision.receipt.provider_network_called is True
    assert decision.receipt.provider_http_status_class == "blocked_or_unknown"
    assert "PROVIDER_VALIDATION_TRANSPORT_BLOCKED_OR_UNKNOWN" in decision.reason_codes
    assert store.list_receipts()[0].receipt_ref == decision.receipt.receipt_ref


def test_non_allowlisted_validation_endpoint_blocks_before_secret_transport() -> None:
    called = False

    def transport(endpoint_url: str, credential_secret: str, timeout: float) -> int:
        nonlocal called
        called = True
        return 200

    decision = evaluate_with_exact_approval(
        validation_request(
            validation_ref="provider-credential-validation-ref:bad-endpoint",
            validation_receipt_ref="receipt:provider-credential-validation:bad-endpoint",
        ),
        adapter=OpenAICompatibleCredentialValidationAdapter(
            enabled=True,
            endpoint_url="https://example.invalid/collect",
            transport=transport,
        ),
    )

    assert called is False
    assert decision.allowed is False
    assert decision.status == ProviderCredentialValidationStatus.validation_blocked
    assert decision.receipt is not None
    assert decision.receipt.validation_performed is False
    assert decision.receipt.provider_network_called is False
    assert "PROVIDER_VALIDATION_ENDPOINT_NOT_ALLOWLISTED" in decision.reason_codes
    receipt_json = json.dumps(decision.receipt.model_dump(mode="json"), sort_keys=True)
    assert "redacted-safe-test-credential" not in receipt_json


def test_openai_compatible_adapter_without_injected_transport_blocks() -> None:
    decision = evaluate_with_exact_approval(
        validation_request(
            validation_ref="provider-credential-validation-ref:no-transport",
            validation_receipt_ref="receipt:provider-credential-validation:no-transport",
        ),
        adapter=OpenAICompatibleCredentialValidationAdapter(enabled=True),
    )

    assert decision.allowed is False
    assert decision.status == ProviderCredentialValidationStatus.validation_blocked
    assert decision.receipt is not None
    assert decision.receipt.validation_performed is False
    assert decision.receipt.provider_network_called is False
    assert "PROVIDER_VALIDATION_TRANSPORT_NOT_CONFIGURED" in decision.reason_codes


def test_receipt_rejects_model_or_provider_payload_authority() -> None:
    values = {
        "receipt_ref": "receipt:provider-credential-validation:test",
        "validation_ref": "provider-credential-validation-ref:test",
        "run_id": "run-ref:provider-credential-validation-test",
        "provider_ref": PROVIDER_CREDENTIAL_VALIDATION_PROVIDER_REF,
        "credential_ref": "credential-ref:openai-compatible:validation-test",
        "policy_ref": PROVIDER_CREDENTIAL_VALIDATION_POLICY_REF,
        "approval_ref": "approval-ref:provider-credential-validation:test",
        "approval_scope_ref": "approval-scope-ref:provider-credential-validation:test",
        "idempotency_ref": "idempotency:provider-credential-validation:test",
        "validation_receipt_ref": "receipt:provider-credential-validation:test",
        "revocation_ref": "revocation-ref:provider-credential-validation:test",
        "safe_disable_ref": "safe-disable-ref:provider-credential-validation:test",
        "provider_manifest_ref": "provider-manifest-ref:openai-compatible:validation",
        "provider_allowlist_ref": "provider-allowlist-ref:openai-compatible:validation",
        "rate_budget_ref": "rate-budget-ref:provider-credential-validation:test",
        "redacted_validation_summary_ref": (
            "redacted-validation-summary-ref:provider-credential-validation:test"
        ),
        "status": ProviderCredentialValidationStatus.credential_valid,
        "validation_performed": True,
        "provider_network_called": True,
        "provider_payload_persisted": True,
        "safe_summary": PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_SUMMARY,
    }

    with pytest.raises(
        ValidationError,
        match="PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_AUTHORITY_DENIED",
    ):
        ExactProviderCredentialValidationReceipt(**values)


def test_openai_compatible_adapter_maps_status_without_provider_sdk() -> None:
    seen: dict[str, object] = {}

    def transport(endpoint_url: str, credential_secret: str, timeout: float) -> int:
        seen["endpoint_url"] = endpoint_url
        seen["credential_secret"] = credential_secret
        seen["timeout"] = timeout
        return 401

    adapter = OpenAICompatibleCredentialValidationAdapter(
        enabled=True,
        transport=transport,
    )
    decision = evaluate_with_exact_approval(
        validation_request(),
        adapter=adapter,
    )

    assert decision.status == ProviderCredentialValidationStatus.credential_invalid
    assert decision.receipt is not None
    assert decision.receipt.provider_sdk_used is False
    assert decision.receipt.model_invocation_performed is False
    assert seen["credential_secret"] == "redacted-safe-test-credential"


def test_provider_credential_validation_route_is_authority_bound() -> None:
    manifest = build_api_manifest(app).model_dump(mode="json")
    route = {(item["method"], item["path"]): item for item in manifest["routes"]}[
        ("POST", PROVIDER_CREDENTIAL_VALIDATION_ROUTE)
    ]

    assert route["route_classification"] == "mutating_requires_authority"
    assert route["side_effect_class"] == "governed_network_read_only"
    assert route["idempotency_required"] is True
    assert route["rate_limit_group"] == "provider_credential_validation"


def test_provider_credential_validation_route_rejects_missing_idempotency() -> None:
    client = TestClient(app)

    response = client.post(
        PROVIDER_CREDENTIAL_VALIDATION_ROUTE,
        json=validation_request().model_dump(mode="json"),
    )

    assert response.status_code == 428
    assert response.json()["code"] == "API_IDEMPOTENCY_REQUIRED"


def test_provider_credential_validation_route_defaults_to_authority_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "authority"))
    client = TestClient(app)
    request = validation_request()

    response = client.post(
        PROVIDER_CREDENTIAL_VALIDATION_ROUTE,
        headers={"X-UAA-Idempotency-Key": request.idempotency_ref},
        json=request.model_dump(mode="json"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"]["status"] == "validation_blocked"
    assert payload["data"]["receipt"] is None
    assert "AUTHORITY_LEASE_REQUIRED" in payload["data"]["reason_codes"]
    assert payload["data"]["authority_decision"]["outcome"] == "deny"
    evidence_refs = [item["evidence_ref"] for item in payload["evidence"]]
    assert request.validation_receipt_ref not in evidence_refs
    assert request.provider_manifest_ref in evidence_refs


def test_provider_credential_validation_route_uses_persisted_authority_lease(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_dir))
    lease, receipt = AuthorityLeaseStore(authority_dir).issue_lease(
        AuthorityLeaseIssueRequest(
            mode=TrustMode.full_machine_access_session,
            requested_domains={
                AuthorityDomain.provider_model_calls: [AuthorityCapability.execute]
            },
            decision_reason_ref="reason-ref:test-provider-validation-route-authority",
            safe_summary="Select provider validation authority for this session.",
        ),
        idempotency_ref="idempotency-ref:test-provider-validation-route-authority",
    )
    assert lease is not None
    assert receipt.status == "issued"
    client = TestClient(app)
    request = validation_request(
        validation_ref="provider-credential-validation-ref:route-authority"
    )

    response = client.post(
        PROVIDER_CREDENTIAL_VALIDATION_ROUTE,
        headers={"X-UAA-Idempotency-Key": request.idempotency_ref},
        json=request.model_dump(mode="json"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"]["status"] == "validation_blocked"
    assert "APPROVAL_REF_UNKNOWN" in payload["data"]["reason_codes"]
    assert payload["data"]["authority_decision"]["outcome"] == "allow"
    assert payload["data"]["authority_decision"]["lease_ref"] == lease.lease_ref


def test_provider_credential_validation_route_rejects_conflicting_idempotency_headers() -> None:
    client = TestClient(app)
    request = validation_request()

    response = client.post(
        PROVIDER_CREDENTIAL_VALIDATION_ROUTE,
        headers={
            "X-UAA-Idempotency-Key": request.idempotency_ref,
            "X-UAA-Idempotency-Ref": "idempotency:provider-credential-validation:other",
        },
        json=request.model_dump(mode="json"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"]["status"] == "validation_blocked"
    assert payload["data"]["reason_codes"] == ["IDEMPOTENCY_HEADER_CONFLICT"]
