#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.api.rate_limits import route_rate_limit_group  # noqa: E402
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority  # noqa: E402
from ultimate_ai_agent.core.providers import (  # noqa: E402
    DeterministicProviderCredentialValidationAdapter,
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
from ultimate_ai_agent.core.providers.credential_validation import (  # noqa: E402
    PROVIDER_CREDENTIAL_VALIDATION_POLICY_REF,
    PROVIDER_CREDENTIAL_VALIDATION_PROVIDER_REF,
    PROVIDER_CREDENTIAL_VALIDATION_ROUTE,
)


FORBIDDEN_PROVIDER_SDK_FRAGMENTS = (
    "import openai",
    "from openai import",
    "openai.OpenAI(",
    "import anthropic",
    "from anthropic import",
    "anthropic.Anthropic(",
    "chat.completions.create(",
    "/v1/chat/completions",
    "responses.create(",
)


def _request(**overrides: object) -> ExactProviderCredentialValidationRequest:
    values: dict[str, object] = {
        "validation_ref": "provider-credential-validation-ref:verify",
        "run_id": "run-ref:provider-credential-validation-verify",
        "provider_ref": PROVIDER_CREDENTIAL_VALIDATION_PROVIDER_REF,
        "credential_ref": "credential-ref:openai-compatible:validation-test",
        "policy_ref": PROVIDER_CREDENTIAL_VALIDATION_POLICY_REF,
        "approval_ref": "approval-ref:provider-credential-validation:verify",
        "approval_scope_ref": "approval-scope-ref:provider-credential-validation:verify",
        "idempotency_ref": "idempotency:provider-credential-validation:verify",
        "validation_receipt_ref": "receipt:provider-credential-validation:verify",
        "revocation_ref": "revocation-ref:provider-credential-validation:verify",
        "safe_disable_ref": "safe-disable-ref:provider-credential-validation:verify",
        "provider_manifest_ref": "provider-manifest-ref:openai-compatible:validation",
        "provider_allowlist_ref": "provider-allowlist-ref:openai-compatible:validation",
        "rate_budget_ref": "rate-budget-ref:provider-credential-validation:verify",
        "redacted_validation_summary_ref": (
            "redacted-validation-summary-ref:provider-credential-validation:verify"
        ),
    }
    values.update(overrides)
    return ExactProviderCredentialValidationRequest(**values)


def _exact_authority_for(
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


def _evaluate_with_exact_approval(
    request: ExactProviderCredentialValidationRequest,
    *,
    credential_secret: str | None = "redacted-safe-test-credential",
    **kwargs: object,
):
    return evaluate_provider_credential_validation(
        request,
        approval_authority=_exact_authority_for(request),
        credential_secret=credential_secret,
        **kwargs,
    )


class _SpyValidationAdapter(ProviderCredentialValidationAdapter):
    enabled = True

    def __init__(self) -> None:
        self.called = False

    def validate(self, request: ProviderCredentialValidationAdapterRequest):
        self.called = True
        return DeterministicProviderCredentialValidationAdapter().validate(request)


def main() -> int:
    failures: list[str] = []

    readiness = build_provider_credential_validation_readiness()
    if readiness.validation_enabled:
        failures.append("default validation readiness is enabled")
    if readiness.status != ProviderCredentialValidationStatus.validation_blocked:
        failures.append("default validation readiness is not blocked")
    for state in {
        "validation blocked",
        "credential valid",
        "credential invalid",
        "approval required",
        "no provider authority",
    }:
        if state not in readiness.ui_states:
            failures.append(f"readiness missing UI state: {state}")

    public_schema = ExactProviderCredentialValidationRequest.model_json_schema()
    if "credential_secret" in public_schema.get("properties", {}):
        failures.append("public provider credential validation schema exposes credential_secret")
    try:
        ExactProviderCredentialValidationRequest(
            **_request().model_dump(mode="json"),
            credential_secret="redacted-safe-test-credential",
        )
        failures.append("public request accepted transient credential material")
    except Exception:
        pass

    missing_provider = evaluate_provider_credential_validation(
        _request(provider_ref="provider-ref:provider-runtime:not-bound")
    )
    if missing_provider.status != ProviderCredentialValidationStatus.validation_blocked:
        failures.append("missing provider ref did not block")
    if "PROVIDER_REF_REQUIRED" not in missing_provider.reason_codes:
        failures.append("missing provider ref did not report required ref")

    no_approval_spy = _SpyValidationAdapter()
    no_approval = evaluate_provider_credential_validation(
        _request(),
        adapter=no_approval_spy,
    )
    if no_approval.status != ProviderCredentialValidationStatus.validation_blocked:
        failures.append("missing exact approval did not block")
    if "APPROVAL_REF_UNKNOWN" not in no_approval.reason_codes:
        failures.append("missing exact approval did not report unknown approval")
    if no_approval_spy.called:
        failures.append("adapter executed before approval validation")

    bad_policy = _evaluate_with_exact_approval(
        _request(policy_ref="policy-ref:provider-credential-validation:wrong")
    )
    if "POLICY_REF_NOT_ALLOWED" not in bad_policy.reason_codes:
        failures.append("wrong policy ref did not block")

    disabled = _evaluate_with_exact_approval(_request())
    if (
        "PROVIDER_CREDENTIAL_VALIDATION_ADAPTER_DISABLED_BY_DEFAULT"
        not in disabled.reason_codes
    ):
        failures.append("default adapter did not remain disabled")
    if disabled.receipt is not None:
        failures.append("disabled adapter produced a receipt")

    no_transient_secret = _evaluate_with_exact_approval(
        _request(),
        adapter=DeterministicProviderCredentialValidationAdapter(),
        credential_secret=None,
    )
    if (
        "TRANSIENT_CREDENTIAL_SECRET_REQUIRED_FOR_VALIDATION"
        not in no_transient_secret.reason_codes
    ):
        failures.append("missing transient credential material did not block")

    with tempfile.TemporaryDirectory() as tmpdir:
        store = ProviderCredentialValidationReceiptStore(
            Path(tmpdir) / "receipts.jsonl"
        )
        valid = _evaluate_with_exact_approval(
            _request(validation_ref="provider-credential-validation-ref:valid"),
            adapter=DeterministicProviderCredentialValidationAdapter(
                ProviderCredentialValidationStatus.credential_valid
            ),
            receipt_store=store,
        )
        invalid = _evaluate_with_exact_approval(
            _request(
                validation_ref="provider-credential-validation-ref:invalid",
                validation_receipt_ref="receipt:provider-credential-validation:invalid",
            ),
            adapter=DeterministicProviderCredentialValidationAdapter(
                ProviderCredentialValidationStatus.credential_invalid
            ),
            receipt_store=store,
        )
        blocked_transport = _evaluate_with_exact_approval(
            _request(
                validation_ref="provider-credential-validation-ref:blocked-transport",
                validation_receipt_ref=(
                    "receipt:provider-credential-validation:blocked-transport"
                ),
            ),
            adapter=OpenAICompatibleCredentialValidationAdapter(
                enabled=True,
                transport=lambda _endpoint, _secret, _timeout: 500,
            ),
            receipt_store=store,
        )
        if valid.status != ProviderCredentialValidationStatus.credential_valid:
            failures.append("valid credential status was not returned")
        if invalid.status != ProviderCredentialValidationStatus.credential_invalid:
            failures.append("invalid credential status was not returned")
        if blocked_transport.receipt is None:
            failures.append("blocked validation transport did not return a receipt")
        elif not blocked_transport.receipt.provider_network_called:
            failures.append("blocked validation transport receipt did not mark network attempt")
        if len(store.list_receipts()) != 3:
            failures.append(
                "validation receipt store did not persist redacted receipts"
            )
        receipt_json = json.dumps(
            [receipt.model_dump(mode="json") for receipt in store.list_receipts()],
            sort_keys=True,
        )
        for fragment in (
            "redacted-safe-test-credential",
            "raw provider payload",
            "raw prompt",
            "raw response",
        ):
            if fragment in receipt_json:
                failures.append(f"unsafe receipt fragment persisted: {fragment}")

        secret_was_sent_to_bad_endpoint = False

        def bad_endpoint_transport(
            endpoint_url: str,
            credential_secret: str,
            timeout: float,
        ) -> int:
            nonlocal secret_was_sent_to_bad_endpoint
            secret_was_sent_to_bad_endpoint = True
            return 200

        bad_endpoint = _evaluate_with_exact_approval(
            _request(
                validation_ref="provider-credential-validation-ref:bad-endpoint",
                validation_receipt_ref=(
                    "receipt:provider-credential-validation:bad-endpoint"
                ),
            ),
            adapter=OpenAICompatibleCredentialValidationAdapter(
                enabled=True,
                endpoint_url="https://example.invalid/collect",
                transport=bad_endpoint_transport,
            ),
        )
        if secret_was_sent_to_bad_endpoint:
            failures.append("credential material was sent to a non-allowlisted endpoint")
        if "PROVIDER_VALIDATION_ENDPOINT_NOT_ALLOWLISTED" not in bad_endpoint.reason_codes:
            failures.append("non-allowlisted endpoint did not report endpoint block")

        cli_result = subprocess.run(
            [
                sys.executable,
                "scripts/inspect_provider_credential_validation_lane.py",
                "--receipts-path",
                str(store.path),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if cli_result.returncode != 0:
            failures.append("credential validation CLI inspection failed")
        else:
            cli_payload = json.loads(cli_result.stdout)
            if cli_payload["receipt_storage"]["receipt_count"] != 3:
                failures.append(
                    "credential validation CLI did not inspect receipt refs"
                )
            cli_json = json.dumps(cli_payload, sort_keys=True)
            if "redacted-safe-test-credential" in cli_json:
                failures.append(
                    "credential validation CLI exposed transient credential material"
                )

    manifest = build_api_manifest(app).model_dump(mode="json")
    routes = {(route["method"], route["path"]): route for route in manifest["routes"]}
    route = routes.get(("POST", PROVIDER_CREDENTIAL_VALIDATION_ROUTE))
    if route is None:
        failures.append("credential validation route missing from API manifest")
    else:
        if route["route_classification"] != "mutating_requires_authority":
            failures.append("credential validation route is not authority-bound")
        if route["side_effect_class"] != "governed_network_read_only":
            failures.append(
                "credential validation route is not governed network read-only"
            )
        if route["idempotency_required"] is not True:
            failures.append("credential validation route does not require idempotency")
        if route["rate_limit_group"] != "provider_credential_validation":
            failures.append("credential validation route has wrong rate-limit group")
    if (
        route_rate_limit_group("POST", PROVIDER_CREDENTIAL_VALIDATION_ROUTE)
        != "provider_credential_validation"
    ):
        failures.append("credential validation route rate-limit lookup failed")

    source = Path(
        "src/ultimate_ai_agent/core/providers/credential_validation.py"
    ).read_text(encoding="utf-8")
    for fragment in FORBIDDEN_PROVIDER_SDK_FRAGMENTS:
        if fragment in source:
            failures.append(
                f"forbidden provider SDK/model call fragment present: {fragment}"
            )

    if failures:
        print("FAIL: provider credential validation lane verification failed")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        "OK: provider credential validation lane is exact-approved, redacted, and non-invoking"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
