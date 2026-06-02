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


def validate_local_runtime_activation_manifest(manifest):
    from ultimate_ai_agent.core.model_runtime.enums import LocalModelRuntimeStatus
    from ultimate_ai_agent.core.model_runtime.endpoint_policy import validate_local_runtime_endpoint_descriptor
    from ultimate_ai_agent.core.model_runtime.health_plan import validate_local_runtime_health_probe_plan
    from ultimate_ai_agent.core.model_runtime.provider_profiles import validate_local_runtime_provider_profile
    from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean

    if manifest.status != LocalModelRuntimeStatus.contract_only:
        raise ValueError("local runtime activation manifest must remain contract-only")
    if manifest.activation_allowed_now:
        raise ValueError("local runtime activation is not allowed in M22")
    if manifest.real_model_call_allowed:
        raise ValueError("real model call is not allowed in M22")
    if manifest.runtime_execution_allowed:
        raise ValueError("runtime execution is not allowed in M22")
    if manifest.provider_call_allowed:
        raise ValueError("provider call is not allowed in M22")
    if manifest.endpoint_probe_allowed:
        raise ValueError("endpoint probe is not allowed in M22")
    if manifest.user_content_allowed:
        raise ValueError("user content is not allowed in M22")
    if manifest.tool_call_allowed:
        raise ValueError("tool call is not allowed in M22")
    if manifest.memory_write_allowed:
        raise ValueError("memory write is not allowed in M22")
    if manifest.secret_material_allowed:
        raise ValueError("secret material is not allowed in M22")
    if not manifest.no_model_called:
        raise ValueError("M22 manifest must record that no model was called")
    if not manifest.no_runtime_activated:
        raise ValueError("M22 manifest must record that no runtime was activated")
    if not manifest.no_endpoint_contacted:
        raise ValueError("M22 manifest must record that no endpoint was contacted")
    for value in [manifest.safe_summary, *manifest.docs_refs, *manifest.warnings, *manifest.metadata_refs]:
        assert_secret_clean(value, "local runtime activation manifest metadata")
    for profile in manifest.provider_profiles:
        validate_local_runtime_provider_profile(profile)
    validate_local_runtime_activation_policy(manifest.activation_policy)
    validate_local_runtime_health_probe_plan(manifest.health_probe_plan)
    for endpoint in getattr(manifest, "endpoint_descriptors", []):
        validate_local_runtime_endpoint_descriptor(endpoint)
    return manifest


def validate_local_runtime_activation_policy(policy):
    from ultimate_ai_agent.core.model_runtime.enums import LocalModelRuntimeStatus
    from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean

    if policy.status != LocalModelRuntimeStatus.contract_only:
        raise ValueError("local runtime activation policy must remain contract-only")
    if policy.activation_allowed_now:
        raise ValueError("local runtime activation is not allowed in M22")
    if policy.real_model_call_allowed:
        raise ValueError("real model call is not allowed in M22")
    if policy.runtime_execution_allowed:
        raise ValueError("runtime execution is not allowed in M22")
    if policy.endpoint_probe_allowed:
        raise ValueError("endpoint probe is not allowed in M22")
    if policy.provider_call_allowed:
        raise ValueError("provider call is not allowed in M22")
    if policy.user_content_allowed:
        raise ValueError("user content is not allowed in M22")
    if policy.tool_call_allowed:
        raise ValueError("tool call is not allowed in M22")
    if policy.memory_write_allowed:
        raise ValueError("memory write is not allowed in M22")
    if policy.remote_host_allowed:
        raise ValueError("remote host is not allowed in M22")
    if policy.secret_material_allowed:
        raise ValueError("secret material is not allowed in M22")
    if policy.approval_ref_can_authorize_activation:
        raise ValueError("approval_ref cannot authorize local runtime activation in M22")
    if not policy.requires_m23_for_real_call:
        raise ValueError("M22 policy must require M23 for a real local model call")
    assert_secret_clean(policy.safe_summary, "local runtime activation policy safe_summary")
    for value in [*policy.metadata_refs, *[str(item) for item in policy.metadata.values()]]:
        assert_secret_clean(value, "local runtime activation policy metadata")
    return policy


def validate_local_runtime_activation_request(request):
    from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean

    assert_secret_clean(request.request_ref, "local runtime activation request_ref")
    assert_secret_clean(request.safe_summary, "local runtime activation request safe_summary")
    for value in request.metadata_refs:
        assert_secret_clean(value, "local runtime activation request metadata_refs")
    for value in request.metadata.values():
        assert_secret_clean(str(value), "local runtime activation request metadata")
    if request.runtime_execution_requested:
        if request.approval_ref:
            raise ValueError("approval_ref is not authority for local runtime execution in M22")
        raise ValueError("runtime execution is not allowed in M22")
    if request.provider_call_requested:
        raise ValueError("provider call is not allowed in M22")
    if request.endpoint_probe_requested:
        raise ValueError("endpoint probe is not allowed in M22")
    if request.prompt_present:
        raise ValueError("prompt content is not allowed in M22")
    if request.user_content_present:
        raise ValueError("user content is not allowed in M22")
    if request.secret_present:
        raise ValueError("secret content is not allowed in M22")
    if request.tool_call_requested:
        raise ValueError("tool call is not allowed in M22")
    if request.memory_write_requested:
        raise ValueError("memory write is not allowed in M22")
    return request


def validate_local_runtime_activation_decision(decision):
    from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean

    assert_secret_clean(decision.decision_ref, "local runtime activation decision_ref")
    assert_secret_clean(decision.safe_message, "local runtime activation decision safe_message")
    for value in decision.metadata_refs:
        assert_secret_clean(value, "local runtime activation decision metadata_refs")
    for value in decision.metadata.values():
        assert_secret_clean(str(value), "local runtime activation decision metadata")
    if decision.allowed:
        raise ValueError("M22 local runtime activation decisions cannot authorize activation")
    if decision.approval_ref_authorized:
        raise ValueError("approval_ref cannot authorize local runtime activation in M22")
    if not decision.no_model_called:
        raise ValueError("M22 decision must record that no model was called")
    if not decision.no_runtime_activated:
        raise ValueError("M22 decision must record that no runtime was activated")
    if not decision.no_endpoint_contacted:
        raise ValueError("M22 decision must record that no endpoint was contacted")
    if not decision.no_user_content_processed:
        raise ValueError("M22 decision must record that no user content was processed")
    if not decision.no_tool_call_performed:
        raise ValueError("M22 decision must record that no tool call was performed")
    if not decision.no_memory_write_performed:
        raise ValueError("M22 decision must record that no memory write was performed")
    return decision
