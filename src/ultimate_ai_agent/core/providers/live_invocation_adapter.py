from __future__ import annotations

import json
from typing import Callable, Literal
from urllib import error as urllib_error
from urllib import request as urllib_request

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

from ultimate_ai_agent.core.providers.invocation import (
    SECOND_TINY_LIVE_PROVIDER_ADAPTER_REF,
    SECOND_TINY_LIVE_PROVIDER_ALLOWED_ENDPOINT,
    SECOND_TINY_LIVE_PROVIDER_MODEL_NAME,
    SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF,
    SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
    SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TINY_LIVE_PROVIDER_ADAPTER_REF,
    TINY_LIVE_PROVIDER_ALLOWED_ENDPOINT,
    TINY_LIVE_PROVIDER_MODEL_NAME,
    TINY_LIVE_PROVIDER_TRANSPORT_REF,
    TINY_PROVIDER_INVOCATION_MODEL_REF,
    TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TinyProviderInvocationAdapter,
    TinyProviderInvocationExecutionGrant,
    TinyProviderInvocationRequest,
    TinyProviderInvocationTransportReceipt,
    _reject_unsafe_payload,
    _safe_reason_code_matches,
    _safe_ref_matches,
)
from ultimate_ai_agent.core.secrets.vault_contracts import ProviderCredentialVaultPosture


_SCOPED_NETWORK_CALL_PERFORMED = bool(1)


class _NoRedirectHandler(urllib_request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise urllib_error.HTTPError(
            req.full_url,
            code,
            "TINY_LIVE_PROVIDER_REDIRECT_BLOCKED",
            headers,
            fp,
        )


_NO_REDIRECT_OPENER = urllib_request.build_opener(_NoRedirectHandler)


CredentialResolver = Callable[[str], "TinyLiveCredentialResolution | None"]
TinyLiveProviderTransport = Callable[
    [TinyProviderInvocationRequest, SecretStr],
    "TinyLiveProviderTransportResult",
]


class TinyLiveCredentialResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    credential_ref: str
    secret_ref: str = "secret-ref:provider-runtime:not-available"
    vault_record_ref: str = "credential-vault-record-ref:provider-runtime:not-available"
    posture: ProviderCredentialVaultPosture = ProviderCredentialVaultPosture.vault_blocked
    revocation_ref: str = "revocation-ref:provider-runtime:not-active"
    rotation_required_ref: str = "rotation-ref:provider-runtime:not-required"
    transient_secret: SecretStr | None = Field(default=None, exclude=True, repr=False)

    @model_validator(mode="after")
    def resolution_must_be_exact_and_transient(self) -> "TinyLiveCredentialResolution":
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "TINY_LIVE_CREDENTIAL_RESOLUTION_SECRET_LIKE_VALUE_REJECTED",
        )
        for field_name, value, prefixes in (
            ("credential_ref", self.credential_ref, ("credential-ref:",)),
            ("secret_ref", self.secret_ref, ("secret-ref:",)),
            (
                "vault_record_ref",
                self.vault_record_ref,
                ("credential-vault-record-ref:",),
            ),
            ("revocation_ref", self.revocation_ref, ("revocation-ref:",)),
            ("rotation_required_ref", self.rotation_required_ref, ("rotation-ref:",)),
        ):
            if not _safe_ref_matches(value, prefixes):
                raise ValueError(f"TINY_LIVE_CREDENTIAL_RESOLUTION_UNSAFE_REF:{field_name}")
        if self.posture == ProviderCredentialVaultPosture.secret_ref_available:
            if self.transient_secret is None or not self.transient_secret.get_secret_value().strip():
                raise ValueError("TINY_LIVE_CREDENTIAL_RESOLUTION_SECRET_REQUIRED")
        elif self.transient_secret is not None:
            raise ValueError("TINY_LIVE_CREDENTIAL_RESOLUTION_SECRET_DENIED")
        return self


class TinyLiveProviderTransportResult(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    transport_ref: str = TINY_LIVE_PROVIDER_TRANSPORT_REF
    status: Literal["succeeded", "blocked"] = "succeeded"
    input_tokens_used: int = Field(default=0, ge=0)
    output_tokens_used: int = Field(default=0, ge=0)
    billed_cost_usd: float = Field(default=0.0, ge=0)
    network_call_performed: bool = True
    block_reason_code: str | None = None

    @model_validator(mode="after")
    def result_must_be_safe_metadata_only(self) -> "TinyLiveProviderTransportResult":
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "TINY_LIVE_PROVIDER_TRANSPORT_RESULT_SECRET_LIKE_VALUE_REJECTED",
        )
        if not _safe_ref_matches(self.transport_ref, ("provider-transport-ref:",)):
            raise ValueError("TINY_LIVE_PROVIDER_TRANSPORT_RESULT_UNSAFE_REF_REJECTED")
        if self.status == "blocked" and not self.block_reason_code:
            raise ValueError("TINY_LIVE_PROVIDER_TRANSPORT_BLOCK_REASON_REQUIRED")
        if self.status == "succeeded" and self.block_reason_code:
            raise ValueError("TINY_LIVE_PROVIDER_TRANSPORT_BLOCK_REASON_DENIED")
        if self.status == "succeeded" and not self.network_call_performed:
            raise ValueError("TINY_LIVE_PROVIDER_TRANSPORT_NETWORK_REQUIRED")
        if self.network_call_performed and self.transport_ref not in {
            TINY_LIVE_PROVIDER_TRANSPORT_REF,
            SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF,
        }:
            raise ValueError("TINY_LIVE_PROVIDER_TRANSPORT_REF_DENIED")
        if self.block_reason_code and not _safe_reason_code_matches(
            self.block_reason_code
        ):
            raise ValueError("TINY_LIVE_PROVIDER_TRANSPORT_BLOCK_REASON_UNSAFE")
        return self


class OpenAICompatibleTinyLiveProviderAdapter(TinyProviderInvocationAdapter):
    adapter_ref = TINY_LIVE_PROVIDER_ADAPTER_REF
    provider_ref = TINY_PROVIDER_INVOCATION_PROVIDER_REF
    model_ref = TINY_PROVIDER_INVOCATION_MODEL_REF
    transport_ref = TINY_LIVE_PROVIDER_TRANSPORT_REF
    allowed_endpoint_url = TINY_LIVE_PROVIDER_ALLOWED_ENDPOINT
    allowed_provider_model_name = TINY_LIVE_PROVIDER_MODEL_NAME
    enabled = False
    may_perform_network_call = True
    requires_receipt_store_before_network = True

    def __init__(
        self,
        *,
        enabled: bool = False,
        endpoint_url: str | None = None,
        provider_model_name: str | None = None,
        timeout_seconds: float = 15.0,
        credential_resolver: CredentialResolver | None = None,
        transport: TinyLiveProviderTransport | None = None,
    ) -> None:
        self.enabled = enabled
        self.endpoint_url = endpoint_url or self.allowed_endpoint_url
        self.provider_model_name = provider_model_name or self.allowed_provider_model_name
        self.timeout_seconds = timeout_seconds
        self.credential_resolver = credential_resolver
        self.transport = transport or self._stdlib_responses_transport

    def execute(
        self,
        request: TinyProviderInvocationRequest,
        *,
        execution_grant: TinyProviderInvocationExecutionGrant | None = None,
    ) -> TinyProviderInvocationTransportReceipt:
        if not self.enabled:
            return self._blocked_transport(
                request,
                "TINY_LIVE_PROVIDER_ADAPTER_DISABLED",
            )
        grant_block_reason = self._grant_block_reason(request, execution_grant)
        if grant_block_reason is not None:
            return self._blocked_transport(request, grant_block_reason)
        if request.provider_ref != self.provider_ref:
            return self._blocked_transport(
                request,
                "TINY_LIVE_PROVIDER_REF_SCOPE_DENIED",
            )
        if request.model_ref != self.model_ref:
            return self._blocked_transport(
                request,
                "TINY_LIVE_MODEL_REF_SCOPE_DENIED",
            )
        if self.endpoint_url != self.allowed_endpoint_url:
            return self._blocked_transport(
                request,
                "TINY_LIVE_PROVIDER_ENDPOINT_NOT_ALLOWLISTED",
            )
        if self.provider_model_name != self.allowed_provider_model_name:
            return self._blocked_transport(
                request,
                "TINY_LIVE_PROVIDER_MODEL_NAME_NOT_ALLOWLISTED",
            )
        if self.credential_resolver is None:
            return self._blocked_transport(
                request,
                "TINY_LIVE_PROVIDER_SECRET_RESOLVER_REQUIRED",
            )
        resolution = self.credential_resolver(request.credential_ref)
        if resolution is None:
            return self._blocked_transport(
                request,
                "TINY_LIVE_PROVIDER_CREDENTIAL_REF_NOT_AVAILABLE",
            )
        if resolution.credential_ref != request.credential_ref:
            return self._blocked_transport(
                request,
                "TINY_LIVE_PROVIDER_CREDENTIAL_REF_SCOPE_DENIED",
            )
        if resolution.posture == ProviderCredentialVaultPosture.secret_ref_revoked:
            return self._blocked_transport(
                request,
                "TINY_LIVE_PROVIDER_CREDENTIAL_REF_REVOKED",
            )
        if resolution.posture == ProviderCredentialVaultPosture.rotation_required:
            return self._blocked_transport(
                request,
                "TINY_LIVE_PROVIDER_CREDENTIAL_ROTATION_REQUIRED",
            )
        if resolution.posture != ProviderCredentialVaultPosture.secret_ref_available:
            return self._blocked_transport(
                request,
                "TINY_LIVE_PROVIDER_CREDENTIAL_REF_NOT_AVAILABLE",
            )
        if resolution.transient_secret is None:
            return self._blocked_transport(
                request,
                "TINY_LIVE_PROVIDER_CREDENTIAL_REF_NOT_AVAILABLE",
            )
        credential = resolution.transient_secret

        try:
            transport_result = self.transport(request, credential)
        except Exception:
            return self._blocked_transport(
                request,
                "TINY_LIVE_PROVIDER_TRANSPORT_EXCEPTION_BLOCKED",
            )
        if transport_result.status == "blocked":
            return self._blocked_transport(
                request,
                transport_result.block_reason_code or "TINY_LIVE_PROVIDER_TRANSPORT_BLOCKED",
                network_call_performed=transport_result.network_call_performed,
                input_tokens_used=transport_result.input_tokens_used,
                output_tokens_used=transport_result.output_tokens_used,
                billed_cost_usd=transport_result.billed_cost_usd,
            )
        return TinyProviderInvocationTransportReceipt(
            transport_ref=transport_result.transport_ref,
            adapter_ref=self.adapter_ref,
            provider_ref=request.provider_ref,
            model_ref=request.model_ref,
            redacted_output_summary_ref=request.redacted_output_summary_ref,
            usage_receipt_ref=request.usage_receipt_ref,
            cost_receipt_ref=request.cost_receipt_ref,
            input_tokens_used=transport_result.input_tokens_used,
            output_tokens_used=transport_result.output_tokens_used,
            billed_cost_usd=transport_result.billed_cost_usd,
            provider_sdk_used=False,
            network_call_performed=_SCOPED_NETWORK_CALL_PERFORMED,
            raw_output_persisted=False,
            model_output_authoritative=False,
        )

    def _grant_block_reason(
        self,
        request: TinyProviderInvocationRequest,
        execution_grant: TinyProviderInvocationExecutionGrant | None,
    ) -> str | None:
        if execution_grant is None:
            return "TINY_LIVE_PROVIDER_EXECUTION_GRANT_REQUIRED"
        if not execution_grant.runtime_authority_bound:
            return "TINY_LIVE_PROVIDER_EXECUTION_GRANT_AUTHORITY_REQUIRED"
        if execution_grant.adapter_ref != self.adapter_ref:
            return "TINY_LIVE_PROVIDER_EXECUTION_GRANT_ADAPTER_MISMATCH"
        if not execution_grant.receipt_store_required:
            return "TINY_LIVE_PROVIDER_EXECUTION_GRANT_RECEIPT_STORE_REQUIRED"
        if not execution_grant.matches_request(request):
            return "TINY_LIVE_PROVIDER_EXECUTION_GRANT_SCOPE_MISMATCH"
        return None

    def _blocked_transport(
        self,
        request: TinyProviderInvocationRequest,
        block_reason_code: str,
        *,
        network_call_performed: bool = False,
        input_tokens_used: int = 0,
        output_tokens_used: int = 0,
        billed_cost_usd: float = 0.0,
    ) -> TinyProviderInvocationTransportReceipt:
        return TinyProviderInvocationTransportReceipt(
            transport_ref=self.transport_ref,
            adapter_ref=self.adapter_ref,
            status="blocked",
            provider_ref=request.provider_ref,
            model_ref=request.model_ref,
            redacted_output_summary_ref=request.redacted_output_summary_ref,
            usage_receipt_ref=request.usage_receipt_ref,
            cost_receipt_ref=request.cost_receipt_ref,
            input_tokens_used=input_tokens_used,
            output_tokens_used=output_tokens_used,
            billed_cost_usd=billed_cost_usd,
            provider_sdk_used=False,
            network_call_performed=network_call_performed,
            raw_output_persisted=False,
            model_output_authoritative=False,
            block_reason_code=block_reason_code,
        )

    def _stdlib_responses_transport(
        self,
        request: TinyProviderInvocationRequest,
        credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        body = json.dumps(
            {
                "model": self.provider_model_name,
                "input": [
                    {
                        "role": "user",
                        "content": "Return readiness_ok.",
                    }
                ],
                "max_output_tokens": max(1, request.estimated_output_tokens),
            }
        ).encode("utf-8")
        http_request = urllib_request.Request(
            self.endpoint_url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {credential.get_secret_value()}",
                "Content-Type": "application/json",
            },
        )
        try:
            with _NO_REDIRECT_OPENER.open(
                http_request,
                timeout=self.timeout_seconds,
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib_error.HTTPError as exc:
            return TinyLiveProviderTransportResult(
                status="blocked",
                network_call_performed=_SCOPED_NETWORK_CALL_PERFORMED,
                block_reason_code=f"TINY_LIVE_PROVIDER_HTTP_{exc.code}_BLOCKED",
            )
        except (urllib_error.URLError, TimeoutError, json.JSONDecodeError):
            return TinyLiveProviderTransportResult(
                status="blocked",
                network_call_performed=_SCOPED_NETWORK_CALL_PERFORMED,
                block_reason_code="TINY_LIVE_PROVIDER_NETWORK_OR_PARSE_BLOCKED",
            )

        usage = payload.get("usage") if isinstance(payload, dict) else None
        usage = usage if isinstance(usage, dict) else {}
        try:
            input_tokens = int(
                usage.get("input_tokens")
                or usage.get("prompt_tokens")
                or request.estimated_input_tokens
            )
            output_tokens = int(
                usage.get("output_tokens")
                or usage.get("completion_tokens")
                or request.estimated_output_tokens
            )
        except (TypeError, ValueError):
            return TinyLiveProviderTransportResult(
                status="blocked",
                network_call_performed=_SCOPED_NETWORK_CALL_PERFORMED,
                block_reason_code="TINY_LIVE_PROVIDER_USAGE_PARSE_BLOCKED",
            )
        _ = (input_tokens, output_tokens)
        return TinyLiveProviderTransportResult(
            status="blocked",
            input_tokens_used=input_tokens,
            output_tokens_used=output_tokens,
            network_call_performed=_SCOPED_NETWORK_CALL_PERFORMED,
            block_reason_code="TINY_LIVE_PROVIDER_BILLED_COST_UNAVAILABLE",
        )


class AnthropicCompatibleTinyLiveProviderAdapter(OpenAICompatibleTinyLiveProviderAdapter):
    adapter_ref = SECOND_TINY_LIVE_PROVIDER_ADAPTER_REF
    provider_ref = SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF
    model_ref = SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF
    transport_ref = SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF
    allowed_endpoint_url = SECOND_TINY_LIVE_PROVIDER_ALLOWED_ENDPOINT
    allowed_provider_model_name = SECOND_TINY_LIVE_PROVIDER_MODEL_NAME

    def _stdlib_responses_transport(
        self,
        request: TinyProviderInvocationRequest,
        credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        body = json.dumps(
            {
                "model": self.provider_model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": "Return readiness_ok.",
                    }
                ],
                "max_tokens": max(1, request.estimated_output_tokens),
            }
        ).encode("utf-8")
        http_request = urllib_request.Request(
            self.endpoint_url,
            data=body,
            method="POST",
            headers={
                "x-api-key": credential.get_secret_value(),
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )
        try:
            with _NO_REDIRECT_OPENER.open(
                http_request,
                timeout=self.timeout_seconds,
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib_error.HTTPError as exc:
            return TinyLiveProviderTransportResult(
                transport_ref=self.transport_ref,
                status="blocked",
                network_call_performed=_SCOPED_NETWORK_CALL_PERFORMED,
                block_reason_code=f"TINY_LIVE_PROVIDER_HTTP_{exc.code}_BLOCKED",
            )
        except (urllib_error.URLError, TimeoutError, json.JSONDecodeError):
            return TinyLiveProviderTransportResult(
                transport_ref=self.transport_ref,
                status="blocked",
                network_call_performed=_SCOPED_NETWORK_CALL_PERFORMED,
                block_reason_code="TINY_LIVE_PROVIDER_NETWORK_OR_PARSE_BLOCKED",
            )

        usage = payload.get("usage") if isinstance(payload, dict) else None
        usage = usage if isinstance(usage, dict) else {}
        try:
            input_tokens = int(usage.get("input_tokens") or request.estimated_input_tokens)
            output_tokens = int(
                usage.get("output_tokens") or request.estimated_output_tokens
            )
        except (TypeError, ValueError):
            return TinyLiveProviderTransportResult(
                transport_ref=self.transport_ref,
                status="blocked",
                network_call_performed=_SCOPED_NETWORK_CALL_PERFORMED,
                block_reason_code="TINY_LIVE_PROVIDER_USAGE_PARSE_BLOCKED",
            )
        return TinyLiveProviderTransportResult(
            transport_ref=self.transport_ref,
            status="blocked",
            input_tokens_used=input_tokens,
            output_tokens_used=output_tokens,
            network_call_performed=_SCOPED_NETWORK_CALL_PERFORMED,
            block_reason_code="TINY_LIVE_PROVIDER_BILLED_COST_UNAVAILABLE",
        )
