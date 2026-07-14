from ultimate_ai_agent.core.approvals import (
    ApprovalDecisionStatus,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.model_router import (
    ModelRouteDecision,
    ModelRouteRequest,
    ModelRouteStatus,
    ModelRouter,
)
from ultimate_ai_agent.core.model_router.decisions import (
    build_approval_validation_decision_ref,
    build_model_route_decision_ref,
)
from ultimate_ai_agent.core.model_runtime.enums import (
    ModelRuntimeOutputFormat,
    ModelRuntimeSafetyMode,
)
from ultimate_ai_agent.core.model_runtime.manifests import ModelRuntimeAdapterManifest
from ultimate_ai_agent.core.model_runtime.requests import ModelRuntimeRequest


class ModelRuntimeRequestFactory:
    @staticmethod
    def from_route_decision(
        route_decision: ModelRouteDecision,
        route_request: ModelRouteRequest,
        adapter_manifest: ModelRuntimeAdapterManifest,
        output_format: ModelRuntimeOutputFormat = ModelRuntimeOutputFormat.text,
        approval_authority: LocalApprovalAuthority | None = None,
    ) -> ModelRuntimeRequest:
        route_decision = ModelRouteDecision.model_validate(
            route_decision.model_dump(mode="python")
        )
        route_request = ModelRouteRequest.model_validate(
            route_request.model_dump(mode="python")
        )
        adapter_manifest = ModelRuntimeAdapterManifest.model_validate(
            adapter_manifest.model_dump(mode="python")
        )
        if (
            route_decision.status == ModelRouteStatus.approval_required
            or route_decision.required_approval
        ):
            raise ValueError(
                "Cannot create runtime request from approval-required route decision."
            )
        if route_decision.status != ModelRouteStatus.selected:
            raise ValueError(
                "Cannot create runtime request unless route decision status is selected."
            )
        if (
            not route_decision.selected_profile_id
            or not route_decision.selected_model_id
        ):
            raise ValueError(
                "Selected route decision is missing selected model metadata."
            )
        if not adapter_manifest.enabled:
            raise ValueError(
                "Cannot create runtime request for disabled adapter manifest."
            )
        if route_decision.request_id != route_request.request_id:
            raise ValueError("Route decision request binding mismatch.")
        if route_decision.run_id != route_request.run_id:
            raise ValueError("Route decision run binding mismatch.")

        profile_by_id = {
            profile.model_profile_id: profile
            for profile in route_request.available_profiles
        }
        if len(profile_by_id) != len(route_request.available_profiles):
            raise ValueError("Route request contains duplicate model profiles.")
        if route_decision.selected_profile_id not in profile_by_id:
            raise ValueError(
                "Selected route profile is not bound to the route request."
            )
        selected_profile = profile_by_id[route_decision.selected_profile_id]
        if route_decision.selected_model_id != selected_profile.model_id:
            raise ValueError("Selected route model binding mismatch.")
        if (
            route_decision.selected_profile_id
            not in route_decision.candidate_profile_ids
        ):
            raise ValueError(
                "Selected route profile is absent from candidate evidence."
            )
        provider_kind = str(selected_profile.provider_kind)
        if provider_kind not in adapter_manifest.supported_provider_kinds:
            raise ValueError(
                "Adapter manifest does not support selected provider kind."
            )
        if (
            adapter_manifest.accepts_model_profile_ids
            and selected_profile.model_profile_id
            not in adapter_manifest.accepts_model_profile_ids
        ):
            raise ValueError("Adapter manifest does not accept selected model profile.")
        required_capabilities = {
            str(value)
            for value in (
                route_request.required_capabilities
                or route_request.routing_policy.required_capabilities
            )
        }
        if not required_capabilities.issubset(
            set(adapter_manifest.supported_capabilities)
        ):
            raise ValueError("Adapter manifest lacks required model capabilities.")
        if adapter_manifest.requires_credential_ref:
            if (
                not selected_profile.credential_ref
                or selected_profile.credential_ref
                not in adapter_manifest.allowed_credential_refs
            ):
                raise ValueError("Adapter manifest credential binding mismatch.")

        if route_request.approval_ref and route_request.approval_ref.startswith(
            "approval_test_"
        ):
            raise ValueError("APPROVAL_TEST_REF_DENIED")

        expected_route_decision = ModelRouter(
            approval_authority=approval_authority
        ).route(route_request)
        reproducible_fields = (
            "status",
            "selected_profile_id",
            "selected_model_id",
            "candidate_profile_ids",
            "rejected_profile_ids",
            "reason_codes",
            "safe_message",
            "estimated_cost",
            "estimated_latency_ms",
            "cost_mode",
            "fallback_plan_ref",
            "fallback_used",
            "verification_required",
            "verification_route_id",
            "privacy_notes",
            "required_approval",
            "approval_validation_decision_ref",
            "consent_refs",
            "event_ref",
        )
        if (
            route_request.approval_ref
            and route_decision.approval_validation_decision_ref
            != expected_route_decision.approval_validation_decision_ref
        ):
            raise ValueError("Runtime request approval revalidation failed.")
        if any(
            getattr(route_decision, field_name)
            != getattr(expected_route_decision, field_name)
            for field_name in reproducible_fields
        ):
            raise ValueError(
                "Route decision is not reproducible from the bound route request."
            )

        if route_request.approval_ref:
            if (
                "APPROVAL_VALIDATED" not in route_decision.reason_codes
                or route_decision.approval_validation_decision_ref is None
            ):
                raise ValueError(
                    "Runtime request creation requires validated approval evidence."
                )
            if approval_authority is None:
                raise ValueError(
                    "Runtime request creation requires LocalApprovalAuthority."
                )
            approval_request = LocalApprovalAuthority.request_for_model_route(
                route_request,
                subject_type=ApprovalSubjectType.model_route,
                subject_id=route_request.request_id,
                requested_action="route_cloud_model",
                resource_refs=[selected_profile.model_profile_id],
                risk_level=ApprovalRiskLevel.high,
            )
            validation_request = approval_request.to_validation_request(
                route_request.approval_ref,
            )
            approval_decision = approval_authority.validate(validation_request)
            if not (
                approval_decision.allowed
                and approval_decision.status == ApprovalDecisionStatus.approved.value
                and approval_decision.approval_ref == route_request.approval_ref
                and approval_decision.matched_grant_ref == route_request.approval_ref
                and "APPROVAL_VALIDATED" in approval_decision.reason_codes
            ):
                raise ValueError("Runtime request approval revalidation failed.")
            if (
                build_approval_validation_decision_ref(
                    validation_request,
                    approval_decision,
                )
                != route_decision.approval_validation_decision_ref
            ):
                raise ValueError("Runtime request approval evidence binding mismatch.")
        elif (
            "APPROVAL_VALIDATED" in route_decision.reason_codes
            or route_decision.approval_validation_decision_ref is not None
        ):
            raise ValueError("Route decision contains unbound approval evidence.")

        secret_refs = (
            [selected_profile.credential_ref] if selected_profile.credential_ref else []
        )
        # Runtime identity is derived only from the freshly reproduced route
        # decision. Caller-supplied diagnostic refs are not authority and must
        # not create a second idempotency identity for the same exact route.
        route_decision_ref = build_model_route_decision_ref(expected_route_decision)
        route_decision_digest = route_decision_ref.rsplit(":", maxsplit=1)[1]

        return ModelRuntimeRequest(
            runtime_request_id=f"mrt_req_{route_decision_digest}",
            run_id=route_decision.run_id,
            route_decision_ref=route_decision_ref,
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
                "route_decision_ref": route_decision_ref,
                "route_reason_codes": route_decision.reason_codes,
                "simulated": True,
            },
        )
