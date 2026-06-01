from ultimate_ai_agent.core.hygiene.envelopes import ErrorCategory, ErrorEnvelope, ResultEnvelope, Severity
from ultimate_ai_agent.core.model_runtime.enums import ModelRuntimeSafetyMode
from ultimate_ai_agent.core.model_runtime.manifests import ModelRuntimeAdapterManifest
from ultimate_ai_agent.core.model_runtime.requests import ModelRuntimeRequest
from ultimate_ai_agent.core.model_runtime.responses import ModelRuntimeResponse


def _error(code: str, message: str, severity: Severity = Severity.medium) -> ErrorEnvelope:
    return ErrorEnvelope(
        code=code,
        category=ErrorCategory.validation_error if severity != Severity.critical else ErrorCategory.security_blocked,
        safe_message=message,
        severity=severity,
        retryable=False,
        details_redacted=True,
        source="ModelRuntime",
    )


def validate_runtime_manifest(manifest: ModelRuntimeAdapterManifest) -> ResultEnvelope:
    if not manifest.enabled:
        return ResultEnvelope(
            success=False,
            operation="validate_model_runtime_manifest",
            service="ModelRuntimeAPI",
            trace_id=manifest.adapter_id,
            error=_error("MODEL_RUNTIME_ADAPTER_DISABLED", "Model runtime adapter is disabled."),
        )
    return ResultEnvelope(
        success=True,
        operation="validate_model_runtime_manifest",
        service="ModelRuntimeAPI",
        trace_id=manifest.adapter_id,
        data={"adapter_id": manifest.adapter_id, "status": "validated"},
    )


def validate_runtime_request(request: ModelRuntimeRequest, manifest: ModelRuntimeAdapterManifest) -> ResultEnvelope:
    manifest_result = validate_runtime_manifest(manifest)
    if not manifest_result.success:
        return manifest_result
    if request.adapter_id != manifest.adapter_id:
        return ResultEnvelope(
            success=False,
            operation="validate_model_runtime_request",
            service="ModelRuntimeAPI",
            trace_id=request.trace_id or request.run_id,
            error=_error("MODEL_RUNTIME_ADAPTER_MISMATCH", "Runtime request adapter does not match manifest."),
        )
    if manifest.accepts_model_profile_ids and request.model_profile_id not in manifest.accepts_model_profile_ids:
        return ResultEnvelope(
            success=False,
            operation="validate_model_runtime_request",
            service="ModelRuntimeAPI",
            trace_id=request.trace_id or request.run_id,
            error=_error("MODEL_RUNTIME_PROFILE_NOT_ACCEPTED", "Runtime adapter does not accept the selected model profile."),
        )
    if request.safety_mode == ModelRuntimeSafetyMode.disabled:
        return ResultEnvelope(
            success=False,
            operation="validate_model_runtime_request",
            service="ModelRuntimeAPI",
            trace_id=request.trace_id or request.run_id,
            error=_error("MODEL_RUNTIME_DISABLED_MODE", "Runtime request safety mode is disabled."),
        )
    if manifest.max_input_tokens is not None and request.estimated_input_tokens > manifest.max_input_tokens:
        return ResultEnvelope(
            success=False,
            operation="validate_model_runtime_request",
            service="ModelRuntimeAPI",
            trace_id=request.trace_id or request.run_id,
            error=_error("MODEL_RUNTIME_TOKEN_LIMIT_EXCEEDED", "Runtime request exceeds adapter input token limit."),
        )
    if manifest.max_output_tokens is not None and request.max_output_tokens > manifest.max_output_tokens:
        return ResultEnvelope(
            success=False,
            operation="validate_model_runtime_request",
            service="ModelRuntimeAPI",
            trace_id=request.trace_id or request.run_id,
            error=_error("MODEL_RUNTIME_TOKEN_LIMIT_EXCEEDED", "Runtime request exceeds adapter output token limit."),
        )
    return ResultEnvelope(
        success=True,
        operation="validate_model_runtime_request",
        service="ModelRuntimeAPI",
        trace_id=request.trace_id or request.run_id,
        data={
            "runtime_request_id": request.runtime_request_id,
            "status": "validated",
            "secret_handle_refs": request.secret_handle_refs,
        },
    )


def validate_runtime_response(response: ModelRuntimeResponse) -> ResultEnvelope:
    return ResultEnvelope(
        success=True,
        operation="validate_model_runtime_response",
        service="ModelRuntimeAPI",
        trace_id=response.run_id,
        data={"runtime_response_id": response.runtime_response_id, "status": "validated"},
    )
