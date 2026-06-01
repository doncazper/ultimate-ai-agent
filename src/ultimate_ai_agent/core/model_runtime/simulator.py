from typing import Any, Dict

from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope
from ultimate_ai_agent.core.model_runtime.enums import ModelRuntimeOutputFormat, ModelRuntimeResponseStatus
from ultimate_ai_agent.core.model_runtime.manifests import ModelRuntimeAdapterManifest
from ultimate_ai_agent.core.model_runtime.requests import ModelRuntimeRequest
from ultimate_ai_agent.core.model_runtime.responses import ModelRuntimeResponse
from ultimate_ai_agent.core.model_runtime.validation import validate_runtime_request


class SimulatedModelRuntimeAdapter:
    def validate_request(self, request: ModelRuntimeRequest, manifest: ModelRuntimeAdapterManifest) -> ResultEnvelope:
        return validate_runtime_request(request, manifest)

    def simulate_response(self, request: ModelRuntimeRequest, manifest: ModelRuntimeAdapterManifest) -> ModelRuntimeResponse:
        validation = self.validate_request(request, manifest)
        if not validation.success:
            return ModelRuntimeResponse(
                runtime_response_id=f"mrt_resp_{request.runtime_request_id}",
                runtime_request_id=request.runtime_request_id,
                run_id=request.run_id,
                status=ModelRuntimeResponseStatus.validation_failed,
                output_format=request.output_format,
                output_summary="Simulated validation failure; no model was called.",
                model_profile_id=request.model_profile_id,
                adapter_id=manifest.adapter_id,
                errors=[validation.error.code if validation.error else "MODEL_RUNTIME_VALIDATION_FAILED"],
                created_at=request.created_at,
                metadata={"simulated": True, "truth_authority": False},
            )

        structured_output = self._structured_output(request)
        status = (
            ModelRuntimeResponseStatus.simulated_refusal
            if request.output_format == ModelRuntimeOutputFormat.refusal
            else ModelRuntimeResponseStatus.simulated_success
        )
        return ModelRuntimeResponse(
            runtime_response_id=f"mrt_resp_{request.runtime_request_id}",
            runtime_request_id=request.runtime_request_id,
            run_id=request.run_id,
            status=status,
            output_format=request.output_format,
            output_summary=f"Simulated response for request {request.runtime_request_id}; no model was called.",
            structured_output=structured_output,
            refusal_reason="SIMULATED_REFUSAL_REQUESTED" if status == ModelRuntimeResponseStatus.simulated_refusal else None,
            simulated_latency_ms=self._latency_ms(request),
            simulated_token_usage={
                "input_tokens": request.estimated_input_tokens,
                "output_tokens": min(request.max_output_tokens, 64),
                "total_tokens": request.estimated_input_tokens + min(request.max_output_tokens, 64),
            },
            model_profile_id=request.model_profile_id,
            adapter_id=manifest.adapter_id,
            event_refs=[request.event_ref] if request.event_ref else [],
            redactions_applied=["input_content_omitted"],
            warnings=list(request.metadata["route_reason_codes"]) if "route_reason_codes" in request.metadata else [],
            created_at=request.created_at,
            metadata={"simulated": True, "truth_authority": False, "adapter_id": manifest.adapter_id},
        )

    def preview(self, request: ModelRuntimeRequest, manifest: ModelRuntimeAdapterManifest) -> ResultEnvelope:
        validation = self.validate_request(request, manifest)
        if not validation.success:
            return validation
        return ResultEnvelope(
            success=True,
            operation="preview_model_runtime_simulation",
            service="ModelRuntimeAPI",
            trace_id=request.trace_id or request.run_id,
            data={
                "runtime_request_id": request.runtime_request_id,
                "adapter_id": manifest.adapter_id,
                "simulated": True,
                "would_call_model": False,
                "would_call_network": False,
            },
        )

    def _latency_ms(self, request: ModelRuntimeRequest) -> int:
        return 10 + (len(request.runtime_request_id) % 25)

    def _structured_output(self, request: ModelRuntimeRequest) -> Dict[str, Any] | None:
        if request.output_format == ModelRuntimeOutputFormat.text:
            return None
        return {
            "simulated": True,
            "runtime_request_id": request.runtime_request_id,
            "run_id": request.run_id,
            "output_format": str(request.output_format),
        }
