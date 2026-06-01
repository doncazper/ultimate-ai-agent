from ultimate_ai_agent.core.approvals import ApprovalValidationDecision
from ultimate_ai_agent.core.model_router import ModelRouteDecision, ModelRouteRequest, ModelRouteStatus
from ultimate_ai_agent.core.model_runtime.enums import ModelRuntimeOutputFormat, ModelRuntimeSafetyMode
from ultimate_ai_agent.core.model_runtime.manifests import ModelRuntimeAdapterManifest
from ultimate_ai_agent.core.model_runtime.requests import ModelRuntimeRequest


class ModelRuntimeRequestFactory:
    @staticmethod
    def from_route_decision(
        route_decision: ModelRouteDecision,
        route_request: ModelRouteRequest,
        adapter_manifest: ModelRuntimeAdapterManifest,
        output_format: ModelRuntimeOutputFormat = ModelRuntimeOutputFormat.text,
        approval_decision: ApprovalValidationDecision | None = None,
    ) -> ModelRuntimeRequest:
        if route_decision.status == ModelRouteStatus.approval_required or route_decision.required_approval:
            raise ValueError("Cannot create runtime request from approval-required route decision.")
        if route_decision.status != ModelRouteStatus.selected:
            raise ValueError("Cannot create runtime request unless route decision status is selected.")
        if not route_decision.selected_profile_id or not route_decision.selected_model_id:
            raise ValueError("Selected route decision is missing selected model metadata.")
        if not adapter_manifest.enabled:
            raise ValueError("Cannot create runtime request for disabled adapter manifest.")
        if route_request.approval_ref and not route_request.approval_ref.startswith("approval_test_"):
            if approval_decision is None or not approval_decision.allowed or approval_decision.approval_ref != route_request.approval_ref:
                raise ValueError("Runtime request creation requires a validated approval decision for non-test approval refs.")

        profile_by_id = {profile.model_profile_id: profile for profile in route_request.available_profiles}
        selected_profile = profile_by_id[route_decision.selected_profile_id]
        secret_refs = [selected_profile.credential_ref] if selected_profile.credential_ref else []

        return ModelRuntimeRequest(
            runtime_request_id=f"mrt_req_{route_decision.decision_id}",
            run_id=route_decision.run_id,
            route_decision_ref=route_decision.decision_id,
            model_profile_id=route_decision.selected_profile_id,
            model_id=route_decision.selected_model_id,
            adapter_id=adapter_manifest.adapter_id,
            actor_context=route_request.actor_context,
            prompt_summary=route_request.prompt_summary,
            input_refs=[f"route_request:{route_request.request_id}"],
            output_format=output_format,
            estimated_input_tokens=route_request.estimated_input_tokens,
            max_output_tokens=route_request.estimated_output_tokens,
            safety_mode=ModelRuntimeSafetyMode.simulated,
            data_classification=route_request.data_classification,
            consent_refs=route_decision.consent_refs,
            approval_ref=route_request.approval_ref,
            secret_handle_refs=secret_refs,
            event_ref=route_decision.event_ref,
            trace_id=route_request.request_id,
            metadata={
                "route_decision_ref": route_decision.decision_id,
                "route_reason_codes": route_decision.reason_codes,
                "simulated": True,
            },
        )
