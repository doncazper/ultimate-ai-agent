import ipaddress
from typing import Any, Dict

from ultimate_ai_agent.core.approvals import ApprovalDecisionStatus, ApprovalValidationDecision
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope
from ultimate_ai_agent.core.model_runtime.enums import (
    ModelRuntimeResponseStatus,
    ModelRuntimeSafetyMode,
)
from ultimate_ai_agent.core.model_runtime.execution_policy import LocalRuntimeExecutionDecision, LoopbackRuntimePolicy
from ultimate_ai_agent.core.model_runtime.loopback import SECRET_QUERY_KEYS, LoopbackRuntimeEndpoint
from ultimate_ai_agent.core.model_runtime.manifests import ModelRuntimeAdapterManifest
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.model_runtime.requests import ModelRuntimeRequest
from ultimate_ai_agent.core.model_runtime.responses import ModelRuntimeResponse
from ultimate_ai_agent.core.model_runtime.simulator import SimulatedModelRuntimeAdapter
from ultimate_ai_agent.core.model_runtime.transports import DisabledNetworkTransport, ModelRuntimeTransport
from ultimate_ai_agent.core.model_runtime.validation import validate_runtime_request


class LocalLoopbackModelRuntimeAdapter:
    def validate_endpoint(
        self,
        endpoint: LoopbackRuntimeEndpoint,
        policy: LoopbackRuntimePolicy,
    ) -> LocalRuntimeExecutionDecision:
        reasons: list[str] = []
        parsed = endpoint.parsed_url
        host = endpoint.host
        configured_hosts = set(policy.allowed_hosts).intersection(endpoint.allowed_hosts)
        allowed_hosts = {candidate for candidate in configured_hosts if self._is_loopback_host(candidate)}
        non_loopback_allowlist_entries = sorted(candidate for candidate in configured_hosts if not self._is_loopback_host(candidate))
        if not endpoint.enabled:
            reasons.append("ENDPOINT_DISABLED")
        if parsed.scheme not in set(policy.allowed_schemes):
            reasons.append("SCHEME_NOT_ALLOWED")
        if policy.deny_credentials and (parsed.username or parsed.password):
            reasons.append("URL_CREDENTIALS_DENIED")
        if SECRET_QUERY_KEYS.intersection(endpoint.query_keys):
            reasons.append("SECRET_QUERY_DENIED")
        if host not in allowed_hosts:
            reasons.append("HOST_NOT_ALLOWLISTED")
        if not self._is_loopback_host(host):
            if host in non_loopback_allowlist_entries:
                reasons.append("ALLOWED_HOST_NOT_LOOPBACK")
            if not policy.deny_non_loopback:
                reasons.append("POLICY_CANNOT_DISABLE_LOOPBACK_GUARD")
            reasons.append("NON_LOOPBACK_HOST_DENIED")

        return self._decision(
            allowed=not reasons,
            status="allowed" if not reasons else "blocked",
            reason_codes=["ENDPOINT_ALLOWED"] if not reasons else reasons,
            safe_message="Loopback endpoint is allowed by local/dev policy."
            if not reasons
            else "Loopback endpoint is blocked by local/dev policy.",
            endpoint_id=endpoint.endpoint_id,
            simulated_fallback_available=policy.require_simulated_fallback,
        )

    def validate_execution(
        self,
        request: ModelRuntimeRequest,
        manifest: ModelRuntimeAdapterManifest,
        endpoint: LoopbackRuntimeEndpoint,
        policy: LoopbackRuntimePolicy,
        approval_decision: ApprovalValidationDecision | None,
    ) -> LocalRuntimeExecutionDecision:
        reasons: list[str] = []
        endpoint_decision = self.validate_endpoint(endpoint, policy)
        if not endpoint_decision.allowed:
            reasons.extend(endpoint_decision.reason_codes)
        if not policy.allow_real_loopback_execution:
            reasons.append("REAL_LOOPBACK_EXECUTION_NOT_ENABLED")
        if not manifest.enabled:
            reasons.append("ADAPTER_DISABLED")
        if policy.require_local_dev_mode and request.safety_mode != ModelRuntimeSafetyMode.local_loopback_dev:
            reasons.append("LOCAL_DEV_MODE_REQUIRED")
        if not request.route_decision_ref:
            reasons.append("SELECTED_ROUTE_DECISION_REQUIRED")
        if request.model_profile_id not in manifest.accepts_model_profile_ids:
            reasons.append("MODEL_PROFILE_NOT_ACCEPTED_BY_ADAPTER")
        if manifest.requires_credential_ref or manifest.allowed_credential_refs or request.secret_handle_refs:
            reasons.append("CREDENTIALS_NOT_ALLOWED_FOR_M9")
        if policy.max_input_tokens is not None and request.estimated_input_tokens > policy.max_input_tokens:
            reasons.append("INPUT_TOKEN_LIMIT_EXCEEDED")
        if policy.max_output_tokens is not None and request.max_output_tokens > policy.max_output_tokens:
            reasons.append("OUTPUT_TOKEN_LIMIT_EXCEEDED")

        validation = validate_runtime_request(request, manifest)
        if not validation.success and validation.error:
            reasons.append(validation.error.code)

        if policy.require_approval:
            reasons.extend(self._approval_reasons(request, approval_decision))

        return self._decision(
            allowed=not reasons,
            status="allowed" if not reasons else "blocked",
            reason_codes=["LOCAL_LOOPBACK_EXECUTION_ALLOWED", "APPROVAL_VALIDATED"] if not reasons else sorted(set(reasons)),
            safe_message="Local loopback dev execution is authorized."
            if not reasons
            else "Local loopback dev execution is blocked.",
            endpoint_id=endpoint.endpoint_id,
            adapter_id=manifest.adapter_id,
            runtime_request_id=request.runtime_request_id,
            simulated_fallback_available=policy.require_simulated_fallback,
            event_ref=request.event_ref,
        )

    def build_payload(self, request: ModelRuntimeRequest) -> Dict[str, Any]:
        return {
            "runtime_request_id": request.runtime_request_id,
            "run_id": request.run_id,
            "model_id": request.model_id,
            "model_profile_id": request.model_profile_id,
            "output_format": str(request.output_format),
            "input_refs": list(request.input_refs),
            "max_output_tokens": request.max_output_tokens,
            "metadata": {
                "prompt_content_omitted": True,
                "truth_authority": False,
            },
        }

    def execute_dev(
        self,
        request: ModelRuntimeRequest,
        manifest: ModelRuntimeAdapterManifest,
        endpoint: LoopbackRuntimeEndpoint,
        policy: LoopbackRuntimePolicy,
        approval_decision: ApprovalValidationDecision | None,
        transport: ModelRuntimeTransport | None = None,
    ) -> ModelRuntimeResponse:
        decision = self.validate_execution(request, manifest, endpoint, policy, approval_decision)
        if not decision.allowed:
            if policy.require_simulated_fallback:
                response = self.fallback_simulated(request, manifest)
                response.metadata["fallback_reason_codes"] = decision.reason_codes
                response.warnings.extend(decision.reason_codes)
                return response
            return self._error_response(request, manifest, decision.reason_codes)

        active_transport = transport or DisabledNetworkTransport()
        transport_response = active_transport.send(self.build_payload(request), endpoint, policy.timeout_seconds)
        if transport_response.simulated or transport_response.status_code >= 400:
            return self._error_response(
                request,
                manifest,
                transport_response.body.get("reason_codes", ["LOCAL_LOOPBACK_TRANSPORT_BLOCKED"]),
            )
        if contains_secret_like(transport_response.body):
            return self._error_response(request, manifest, ["TRANSPORT_RESPONSE_SECRET_BLOCKED"])

        return ModelRuntimeResponse(
            runtime_response_id=f"mrt_resp_{request.runtime_request_id}",
            runtime_request_id=request.runtime_request_id,
            run_id=request.run_id,
            status=ModelRuntimeResponseStatus.local_loopback_success,
            output_format=request.output_format,
            output_summary=transport_response.body.get(
                "output_summary",
                f"Local loopback dev response for request {request.runtime_request_id}; model output is not authoritative evidence.",
            ),
            structured_output=transport_response.body.get("structured_output"),
            simulated_latency_ms=transport_response.elapsed_ms,
            simulated_token_usage={
                "input_tokens": request.estimated_input_tokens,
                "output_tokens": min(request.max_output_tokens, 64),
                "total_tokens": request.estimated_input_tokens + min(request.max_output_tokens, 64),
            },
            model_profile_id=request.model_profile_id,
            adapter_id=manifest.adapter_id,
            event_refs=[request.event_ref] if request.event_ref else [],
            redactions_applied=["prompt_content_omitted"],
            warnings=list(request.metadata.get("route_reason_codes", [])),
            metadata={
                "truth_authority": False,
                "runtime_boundary": "local_loopback_dev",
                "network_destination": "loopback_only",
                "endpoint_id": endpoint.endpoint_id,
                "transport_simulated": transport_response.simulated,
            },
            response_origin="fake_transport" if transport.__class__.__name__ == "FakeModelRuntimeTransport" else "local_loopback_dev",
        )

    def fallback_simulated(self, request: ModelRuntimeRequest, manifest: ModelRuntimeAdapterManifest) -> ModelRuntimeResponse:
        simulated = SimulatedModelRuntimeAdapter().simulate_response(
            request.model_copy(update={"safety_mode": ModelRuntimeSafetyMode.simulated}),
            manifest.model_copy(update={"safety_mode": ModelRuntimeSafetyMode.simulated, "runtime_kind": "simulated"}),
        )
        simulated.metadata["response_origin"] = "simulated_fallback"
        simulated.metadata["truth_authority"] = False
        return simulated.model_copy(update={"response_origin": "simulated"})

    def preview(self, request: ModelRuntimeRequest, manifest: ModelRuntimeAdapterManifest) -> ResultEnvelope:
        return ResultEnvelope(
            success=True,
            operation="preview_local_loopback_runtime",
            service="ModelRuntimeAPI",
            trace_id=request.trace_id or request.run_id,
            data={
                "runtime_request_id": request.runtime_request_id,
                "adapter_id": manifest.adapter_id,
                "would_call_remote_network": False,
                "requires_explicit_transport": True,
                "truth_authority": False,
            },
        )

    def _approval_reasons(
        self,
        request: ModelRuntimeRequest,
        approval_decision: ApprovalValidationDecision | None,
    ) -> list[str]:
        if not request.approval_ref:
            return ["APPROVAL_REQUIRED"]
        if approval_decision is None:
            return ["APPROVAL_DECISION_REQUIRED"]
        if approval_decision.approval_ref != request.approval_ref:
            return ["APPROVAL_REF_MISMATCH"]
        if not approval_decision.allowed:
            return approval_decision.reason_codes or ["APPROVAL_NOT_ALLOWED"]
        if approval_decision.status != ApprovalDecisionStatus.approved:
            return approval_decision.reason_codes or ["APPROVAL_NOT_APPROVED"]
        return []

    def _error_response(
        self,
        request: ModelRuntimeRequest,
        manifest: ModelRuntimeAdapterManifest,
        reason_codes: list[str],
    ) -> ModelRuntimeResponse:
        return ModelRuntimeResponse(
            runtime_response_id=f"mrt_resp_{request.runtime_request_id}",
            runtime_request_id=request.runtime_request_id,
            run_id=request.run_id,
            status=ModelRuntimeResponseStatus.local_loopback_error,
            output_format=request.output_format,
            output_summary="Local loopback dev execution was blocked; no remote model was called.",
            model_profile_id=request.model_profile_id,
            adapter_id=manifest.adapter_id,
            errors=reason_codes,
            metadata={"truth_authority": False, "runtime_boundary": "local_loopback_dev"},
            response_origin="local_loopback_dev",
        )

    def _decision(
        self,
        *,
        allowed: bool,
        status: str,
        reason_codes: list[str],
        safe_message: str,
        endpoint_id: str | None = None,
        adapter_id: str | None = None,
        runtime_request_id: str | None = None,
        simulated_fallback_available: bool = False,
        event_ref: str | None = None,
    ) -> LocalRuntimeExecutionDecision:
        return LocalRuntimeExecutionDecision(
            allowed=allowed,
            status=status,
            reason_codes=reason_codes,
            safe_message=safe_message,
            endpoint_id=endpoint_id,
            adapter_id=adapter_id,
            runtime_request_id=runtime_request_id,
            simulated_fallback_available=simulated_fallback_available,
            event_ref=event_ref,
        )

    def _is_loopback_host(self, host: str) -> bool:
        if host in {"localhost", "::1"}:
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False
