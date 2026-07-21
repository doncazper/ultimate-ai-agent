from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from scripts.verify_governed_browser_queue01_group05 import verify
from tests.test_governed_browser_queue01_group01 import (
    _authorized_kernel,
    _binding,
    _readiness,
    _ref,
    _request,
)
from ultimate_ai_agent.core.authority import AuthorityCapability
from ultimate_ai_agent.core.governed_browser import (
    ExactBrowserActionReceipt,
    ExactBrowserActionStatus,
    ExactPostFormDryRunTransportResult,
    ExactPostFormRequest,
    ExactPostFormService,
    ExternalActionAuthorityBinding,
    ExternalActionState,
    ExternalActionTargetKind,
    GovernedPostFormFieldSchema,
    GovernedPostFormFieldValueBinding,
    GovernedPostFormRecipeRegistry,
    GovernedPostFormSchema,
    GovernedPostFormSchemaRegistry,
    GovernedPostFormValueKind,
    IsolatedBrowserActionDryRunBrokerAdapter,
    build_governed_post_form_recipe,
    build_governed_post_form_schema,
    create_isolated_browser_action_dry_run_gateway,
)
from ultimate_ai_agent.core.governed_browser.contracts import (
    governed_receipt_identity_payload,
    stable_governed_browser_ref,
)
from ultimate_ai_agent.core.governed_browser.post_forms import (
    _post_form_kernel_execution,
    _post_form_replay_expectation,
)
from ultimate_ai_agent.core.governed_browser.replay_provenance import (
    ExternalActionReplayEvidenceExpectation,
    _build_external_action_replay_validation_context,
    replay_validation_context,
)
from ultimate_ai_agent.core.governed_browser.transaction import BudgetSettlement
from ultimate_ai_agent.core.web_access import (
    WebAccessAuthorityMode,
    WebAccessNetworkLane,
    WebAccessPolicyStatus,
    WebAccessRequest,
    WebAccessRequestKind,
)


def _post_refs(suffix: str) -> dict[str, str]:
    return {
        "observation": (f"browser-observe-output:governed-browser:post-form-{suffix}"),
        "source_url": f"browser-url:governed-browser:post-source-{suffix}",
        "destination_url": (f"browser-url:governed-browser:post-destination-{suffix}"),
        "element": f"browser-element-ref:governed-browser:post-form-{suffix}",
        "visibility": (f"visibility-proof-ref:governed-browser:post-form-{suffix}"),
        "first_field": f"form-field-ref:governed-browser:first-{suffix}",
        "second_field": f"form-field-ref:governed-browser:second-{suffix}",
        "first_value": f"form-field-value-ref:governed-browser:first-{suffix}",
        "second_value": (f"form-field-value-ref:governed-browser:second-{suffix}"),
    }


def _post_context(
    *,
    suffix: str,
    target_kind: ExternalActionTargetKind = ExternalActionTargetKind.local_validation,
    include_optional: bool = True,
):  # type: ignore[no-untyped-def]
    base = _binding(suffix=suffix, target_kind=target_kind)
    refs = _post_refs(suffix)
    fields = (
        GovernedPostFormFieldSchema(
            field_ref=refs["first_field"],
            value_kind=GovernedPostFormValueKind.opaque_text_ref,
            required=True,
            max_encoded_bytes=512,
        ),
        GovernedPostFormFieldSchema(
            field_ref=refs["second_field"],
            value_kind=GovernedPostFormValueKind.opaque_choice_ref,
            required=False,
            max_encoded_bytes=512,
        ),
    )
    schema = build_governed_post_form_schema(
        exact_origin_ref=base.origin_ref,
        page_snapshot_ref=base.page_snapshot_ref,
        source_observation_ref=refs["observation"],
        source_safe_url_ref=refs["source_url"],
        destination_origin_ref=base.origin_ref,
        destination_safe_url_ref=refs["destination_url"],
        element_ref=refs["element"],
        visibility_proof_ref=refs["visibility"],
        fields=fields,
        max_total_encoded_bytes=768,
    )
    values = [
        GovernedPostFormFieldValueBinding(
            field_ref=refs["first_field"],
            field_value_ref=refs["first_value"],
        )
    ]
    if include_optional:
        values.append(
            GovernedPostFormFieldValueBinding(
                field_ref=refs["second_field"],
                field_value_ref=refs["second_value"],
            )
        )
    binding = ExternalActionAuthorityBinding.model_validate(
        {
            **base.model_dump(mode="json"),
            "authority_capability": AuthorityCapability.form_fill,
            "field_schema_ref": schema.schema_ref,
            "resource_refs": [
                _ref("resource", suffix),
                refs["observation"],
                refs["source_url"],
                refs["destination_url"],
                refs["element"],
                refs["visibility"],
                refs["first_field"],
                refs["second_field"],
                refs["first_value"],
                refs["second_value"],
            ],
        }
    )
    request = _request(binding)
    recipe = build_governed_post_form_recipe(
        request,
        schema=schema,
        field_value_bindings=values,
    )
    return request, schema, recipe, refs


class _ExactPostFormPlanTransport:
    def __init__(
        self,
        *,
        omit: set[str] | None = None,
        **overrides: Any,
    ) -> None:
        self.omit = omit or set()
        self.overrides = overrides
        self.calls = 0
        self.requests = []
        self.profile_directories: list[Path] = []

    def plan(self, *, request, profile_directory, profile_ref):  # type: ignore[no-untyped-def]
        del profile_ref
        self.calls += 1
        self.requests.append(request)
        self.profile_directories.append(profile_directory)
        assert profile_directory.exists()
        payload = {
            "recipe_ref": request.metadata["recipe_ref"],
            "plan_ref": request.metadata["plan_ref"],
            "binding_ref": request.metadata["binding_ref"],
            "schema_ref": request.metadata["schema_ref"],
            "origin_ref": request.metadata["exact_origin_ref"],
            "page_snapshot_ref": request.metadata["page_snapshot_ref"],
            "source_observation_ref": request.metadata["source_observation_ref"],
            "source_safe_url_ref": request.metadata["source_safe_url_ref"],
            "destination_origin_ref": request.metadata["destination_origin_ref"],
            "destination_safe_url_ref": request.metadata["destination_safe_url_ref"],
            "element_ref": request.metadata["element_ref"],
            "visibility_proof_ref": request.metadata["visibility_proof_ref"],
            "field_value_bindings": request.metadata["field_value_bindings"],
            "operation": request.metadata["operation"],
            "method": request.metadata["planned_method"],
            "encoding": request.metadata["encoding"],
            "target_visible": True,
            "same_origin_verified": True,
            "registered_schema_verified": True,
            "field_bindings_verified": True,
            "plan_generated": True,
            "source_observation_content_untrusted": True,
            "web_content_instruction_use_allowed": False,
        }
        payload.update(self.overrides)
        for key in self.omit:
            payload.pop(key, None)
        return payload


def _service(
    *,
    request,
    schema,
    recipe,
    kernel,
    transport: _ExactPostFormPlanTransport,
):  # type: ignore[no-untyped-def]
    broker = IsolatedBrowserActionDryRunBrokerAdapter(
        transport=transport,
        allowed_origin_refs={request.binding.origin_ref},
    )
    schema_registry = GovernedPostFormSchemaRegistry([schema])
    registry = GovernedPostFormRecipeRegistry(
        recipes=[recipe],
        schema_registry=schema_registry,
    )
    service = ExactPostFormService(
        registry=registry,
        kernel=kernel,
        gateway=create_isolated_browser_action_dry_run_gateway(broker),
    )
    return service, broker


def _plan(service, request, recipe_ref):  # type: ignore[no-untyped-def]
    return service.plan(
        ExactPostFormRequest(
            recipe_ref=recipe_ref,
            execution_request=request,
        )
    )


def _rehash_post_form_replay(
    payload: dict[str, Any],
    *,
    receipt_prefix: str = "receipt-ref:governed-post-form",
) -> dict[str, Any]:
    external_payload = {
        "transaction_ref": payload["transaction_ref"],
        "intent_ref": payload["intent_ref"],
        "binding_ref": payload["binding_ref"],
        "state": payload["external_action_state"],
        "approval_validation_ref": payload["approval_validation_ref"],
        "authority_decision_ref": payload["authority_decision_ref"],
        "budget_reservation_ref": payload["budget_reservation_ref"],
        "budget_settlement_ref": payload["budget_settlement_ref"],
        "evidence_refs": payload["evidence_refs"],
        "reason_refs": payload["reason_refs"],
    }
    if payload["budget_release_ref"] is not None:
        external_payload["budget_release_ref"] = payload["budget_release_ref"]
    payload["external_action_receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-action",
        external_payload,
    )
    payload["receipt_ref"] = stable_governed_browser_ref(
        receipt_prefix,
        governed_receipt_identity_payload(
            ExactBrowserActionReceipt.model_construct(**payload)
        ),
    )
    return payload


def test_registered_exact_post_schema_is_governed_and_inactive(
    tmp_path: Path,
) -> None:
    request, schema, recipe, _ = _post_context(suffix="happy")
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactPostFormPlanTransport()
    service, broker = _service(
        request=request,
        schema=schema,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _plan(service, request, recipe.recipe_ref)

    assert result.receipt.status == ExactBrowserActionStatus.plan_ready.value
    assert result.receipt.external_action_state == ExternalActionState.succeeded.value
    assert result.receipt.approval_validation_ref is not None
    assert result.receipt.authority_decision_ref is not None
    assert result.receipt.budget_reservation_ref is not None
    assert result.receipt.budget_settlement_ref is not None
    assert result.receipt.content_free is True
    assert result.receipt.automatic_retry_allowed is False
    assert result.receipt.browser_action_performed is False
    assert result.receipt.network_call_performed is False
    assert result.plan is not None
    assert result.plan.schema_ref == schema.schema_ref
    assert result.plan.recipe_ref == recipe.recipe_ref
    assert result.plan.method == "POST"
    assert result.plan.encoding == "application/x-www-form-urlencoded"
    assert result.plan.origin_ref == request.binding.origin_ref
    assert result.plan.page_snapshot_ref == request.binding.page_snapshot_ref
    assert result.plan.target_visible is True
    assert result.plan.same_origin_verified is True
    assert result.plan.registered_schema_verified is True
    assert result.plan.field_bindings_verified is True
    assert result.plan.browser_session_started is False
    assert result.plan.navigation_performed is False
    assert result.plan.form_fill_performed is False
    assert result.plan.form_submission_performed is False
    assert result.plan.field_values_resolved is False
    assert result.plan.request_body_materialized is False
    assert result.plan.authenticated_profile_used is False
    assert result.plan.download_or_upload_performed is False
    assert result.plan.action_execution_performed is False
    assert result.plan.live_network_performed is False
    assert result.plan.external_mutation_performed is False
    assert request.binding.authority_capability == AuthorityCapability.form_fill.value
    assert transport.calls == 1
    assert broker.closed_profile_refs
    assert all(not path.exists() for path in transport.profile_directories)
    metadata = transport.requests[0].metadata
    assert transport.requests[0].method == "GET"
    assert metadata["planned_method"] == "POST"
    assert metadata["form_submission_execution"] is False
    assert metadata["field_value_resolution"] is False
    assert metadata["request_body_materialization"] is False
    assert metadata["form_submission_performed"] is False
    assert metadata["field_values_resolved"] is False
    assert metadata["request_body_materialized"] is False
    assert metadata["request_body"] is False
    assert metadata["network_call"] is False


@pytest.mark.parametrize(
    ("flag", "reason"),
    [
        (
            "form_submission_execution",
            "browser_action_dry_run_form_submission_execution_denied",
        ),
        (
            "field_value_resolution",
            "browser_action_dry_run_field_value_resolution_denied",
        ),
        (
            "request_body_materialization",
            "browser_action_dry_run_request_body_materialization_denied",
        ),
        (
            "form_submission_performed",
            "browser_action_dry_run_form_submission_performed_denied",
        ),
        (
            "field_values_resolved",
            "browser_action_dry_run_field_values_resolved_denied",
        ),
        (
            "request_body_materialized",
            "browser_action_dry_run_request_body_materialized_denied",
        ),
    ],
)
def test_web_access_policy_denies_post_execution_flags_before_broker(
    flag: str,
    reason: str,
) -> None:
    request, schema, recipe, _ = _post_context(suffix=f"policy-{flag}")
    transport = _ExactPostFormPlanTransport()
    broker = IsolatedBrowserActionDryRunBrokerAdapter(
        transport=transport,
        allowed_origin_refs={request.binding.origin_ref},
    )
    gateway = create_isolated_browser_action_dry_run_gateway(broker)

    result = gateway.execute(
        WebAccessRequest(
            kind=WebAccessRequestKind.BROWSER_ACTION_DRY_RUN,
            method="GET",
            authority_mode=WebAccessAuthorityMode.BROWSER_ACTION_DRY_RUN,
            network_lane=WebAccessNetworkLane.BROWSER_ACTION_DRY_RUN,
            metadata={
                "safe_url_ref": schema.source_safe_url_ref,
                "source_observation_ref": schema.source_observation_ref,
                "plan_ref": recipe.plan_ref,
                "source_observation_content_untrusted": True,
                "web_content_instruction_use_allowed": False,
                "exact_origin_ref": request.binding.origin_ref,
                flag: True,
            },
        )
    )

    assert result.status == WebAccessPolicyStatus.DENIED
    assert reason in (result.error or "")
    assert transport.calls == 0


def test_unknown_recipe_is_blocked_before_authority_or_gateway(
    tmp_path: Path,
) -> None:
    request, schema, recipe, _ = _post_context(suffix="unknown")
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactPostFormPlanTransport()
    service, _ = _service(
        request=request,
        schema=schema,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _plan(
        service,
        request,
        "browser-post-form-recipe-ref:governed-browser:unregistered",
    )

    assert result.receipt.status == ExactBrowserActionStatus.preflight_blocked.value
    assert result.receipt.reason_refs == [
        "reason-ref:governed-post-form:recipe-unregistered"
    ]
    assert result.receipt.approval_validation_ref is None
    assert result.receipt.authority_decision_ref is None
    assert result.receipt.budget_reservation_ref is None
    assert result.plan is None
    assert transport.calls == 0


def test_approval_identifier_alone_grants_nothing(tmp_path: Path) -> None:
    request, schema, recipe, _ = _post_context(suffix="approval-id")
    kernel, _ = _authorized_kernel(tmp_path, request)
    guessed = request.model_copy(
        update={"approval_ref": "approval-ref:governed-browser:guessed-post"}
    )
    transport = _ExactPostFormPlanTransport()
    service, _ = _service(
        request=request,
        schema=schema,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _plan(service, guessed, recipe.recipe_ref)

    assert result.receipt.status == ExactBrowserActionStatus.transaction_blocked.value
    assert result.receipt.external_action_state == ExternalActionState.blocked.value
    assert result.receipt.approval_validation_ref is not None
    assert result.receipt.authority_decision_ref is None
    assert result.plan is None
    assert transport.calls == 0
    assert guessed.approval_ref not in result.receipt.model_dump_json()


@pytest.mark.parametrize("mode", ["safe_disable", "kill_switch", "snapshot"])
def test_post_form_revalidation_denies_before_plan(
    tmp_path: Path,
    mode: str,
) -> None:
    request, schema, recipe, _ = _post_context(suffix=f"revalidate-{mode}")

    def readiness(item):  # type: ignore[no-untyped-def]
        return _readiness(
            item,
            safe_disable=mode == "safe_disable",
            kill_switch=mode == "kill_switch",
            snapshot_ref=(
                _ref("page-snapshot", "changed") if mode == "snapshot" else None
            ),
        )

    kernel, _ = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=readiness,
    )
    transport = _ExactPostFormPlanTransport()
    service, _ = _service(
        request=request,
        schema=schema,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _plan(service, request, recipe.recipe_ref)

    assert result.receipt.status == ExactBrowserActionStatus.transaction_blocked.value
    assert result.receipt.budget_reservation_ref is not None
    assert result.receipt.budget_release_ref is not None
    assert result.receipt.budget_settlement_ref is None
    assert result.plan is None
    assert transport.calls == 0


def test_schema_and_recipe_require_exact_registered_field_set() -> None:
    request, schema, recipe, refs = _post_context(suffix="field-set")

    with pytest.raises(ValueError, match="REQUIRED_FIELD_MISSING"):
        build_governed_post_form_recipe(
            request,
            schema=schema,
            field_value_bindings=[
                GovernedPostFormFieldValueBinding(
                    field_ref=refs["second_field"],
                    field_value_ref=refs["second_value"],
                )
            ],
        )
    with pytest.raises(ValueError, match="UNREGISTERED_FIELD_BINDING"):
        build_governed_post_form_recipe(
            request,
            schema=schema,
            field_value_bindings=[
                *recipe.field_value_bindings,
                GovernedPostFormFieldValueBinding(
                    field_ref="form-field-ref:governed-browser:not-registered",
                    field_value_ref="form-field-value-ref:governed-browser:not-registered",
                ),
            ],
        )
    generic = _request(_binding(suffix="generic-post-capability"))
    with pytest.raises(ValueError, match="EXACT_CAPABILITY_MISMATCH"):
        build_governed_post_form_recipe(
            generic,
            schema=schema,
            field_value_bindings=recipe.field_value_bindings,
        )


def test_post_schema_fields_and_values_must_be_authority_bound() -> None:
    request, schema, recipe, refs = _post_context(suffix="resource-scope")
    drifted_binding = ExternalActionAuthorityBinding.model_validate(
        {
            **request.binding.model_dump(mode="json"),
            "resource_refs": [
                ref
                for ref in request.binding.resource_refs
                if ref not in {refs["second_field"], refs["second_value"]}
            ],
        }
    )
    drifted = _request(drifted_binding)

    with pytest.raises(ValueError, match="RESOURCE_NOT_AUTHORITY_BOUND"):
        build_governed_post_form_recipe(
            drifted,
            schema=schema,
            field_value_bindings=recipe.field_value_bindings,
        )


def test_post_schema_field_limit_matches_authority_resource_capacity() -> None:
    suffix = "resource-capacity"
    base = _binding(suffix=suffix)
    refs = _post_refs(suffix)
    fields = tuple(
        GovernedPostFormFieldSchema(
            field_ref=f"form-field-ref:governed-browser:capacity-{index}",
            value_kind=GovernedPostFormValueKind.opaque_text_ref,
            max_encoded_bytes=128,
        )
        for index in range(5)
    )
    schema = build_governed_post_form_schema(
        exact_origin_ref=base.origin_ref,
        page_snapshot_ref=base.page_snapshot_ref,
        source_observation_ref=refs["observation"],
        source_safe_url_ref=refs["source_url"],
        destination_origin_ref=base.origin_ref,
        destination_safe_url_ref=refs["destination_url"],
        element_ref=refs["element"],
        visibility_proof_ref=refs["visibility"],
        fields=fields,
        max_total_encoded_bytes=640,
    )
    values = tuple(
        GovernedPostFormFieldValueBinding(
            field_ref=field.field_ref,
            field_value_ref=f"form-field-value-ref:governed-browser:capacity-{index}",
        )
        for index, field in enumerate(fields)
    )
    binding = ExternalActionAuthorityBinding.model_validate(
        {
            **base.model_dump(mode="json"),
            "authority_capability": AuthorityCapability.form_fill,
            "field_schema_ref": schema.schema_ref,
            "resource_refs": [
                refs["observation"],
                refs["source_url"],
                refs["destination_url"],
                refs["element"],
                refs["visibility"],
                *(field.field_ref for field in fields),
                *(value.field_value_ref for value in values),
            ],
        }
    )

    recipe = build_governed_post_form_recipe(
        _request(binding),
        schema=schema,
        field_value_bindings=values,
    )

    assert len(binding.resource_refs) == 15
    assert len(recipe.field_value_bindings) == 5
    with pytest.raises(ValidationError):
        build_governed_post_form_schema(
            exact_origin_ref=base.origin_ref,
            page_snapshot_ref=base.page_snapshot_ref,
            source_observation_ref=refs["observation"],
            source_safe_url_ref=refs["source_url"],
            destination_origin_ref=base.origin_ref,
            destination_safe_url_ref=refs["destination_url"],
            element_ref=refs["element"],
            visibility_proof_ref=refs["visibility"],
            fields=[
                *fields,
                GovernedPostFormFieldSchema(
                    field_ref="form-field-ref:governed-browser:capacity-six",
                    value_kind=GovernedPostFormValueKind.opaque_text_ref,
                    max_encoded_bytes=128,
                ),
            ],
            max_total_encoded_bytes=640,
        )


def test_schema_contract_rejects_cross_origin_raw_fields_and_raw_values() -> None:
    _, schema, recipe, _ = _post_context(suffix="contract")
    schema_payload = schema.model_dump(mode="json")

    with pytest.raises(ValidationError, match="CROSS_ORIGIN_DENIED"):
        GovernedPostFormSchema.model_validate(
            {
                **schema_payload,
                "destination_origin_ref": ("origin-ref:governed-browser:cross-origin"),
            }
        )
    with pytest.raises(ValidationError):
        GovernedPostFormSchema.model_validate({**schema_payload, "method": "GET"})
    with pytest.raises(ValidationError):
        GovernedPostFormSchema.model_validate(
            {**schema_payload, "form_submission_allowed": True}
        )
    with pytest.raises(ValidationError, match="structured safe ref"):
        GovernedPostFormFieldSchema(
            field_ref="email",
            value_kind=GovernedPostFormValueKind.opaque_text_ref,
            max_encoded_bytes=128,
        )
    with pytest.raises(ValidationError, match="structured safe ref"):
        GovernedPostFormFieldValueBinding(
            field_ref=recipe.field_value_bindings[0].field_ref,
            field_value_ref="email=raw-private-value",
        )


def test_schema_and_recipe_registries_revalidate_tampered_copies() -> None:
    _, schema, recipe, _ = _post_context(suffix="tamper")

    with pytest.raises(ValidationError):
        GovernedPostFormSchemaRegistry(
            [
                schema.model_copy(
                    update={
                        "destination_safe_url_ref": (
                            "browser-url:governed-browser:tampered"
                        )
                    }
                )
            ]
        )
    with pytest.raises(ValidationError):
        GovernedPostFormRecipeRegistry(
            recipes=[
                recipe.model_copy(
                    update={
                        "binding_ref": (
                            "authority-binding-ref:governed-external-action:tampered"
                        )
                    }
                )
            ],
            schema_registry=GovernedPostFormSchemaRegistry([schema]),
        )


def test_post_form_plan_is_at_most_once_and_replay_is_content_free(
    tmp_path: Path,
) -> None:
    request, schema, recipe, refs = _post_context(suffix="replay")
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactPostFormPlanTransport()
    service, _ = _service(
        request=request,
        schema=schema,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    first = _plan(service, request, recipe.recipe_ref)
    replay = _plan(service, request, recipe.recipe_ref)

    assert first.plan is not None
    assert replay.receipt.status == ExactBrowserActionStatus.replayed_content_free.value
    assert replay.receipt.replayed is True
    assert replay.plan is None
    assert transport.calls == 1
    assert refs["first_value"] not in replay.receipt.model_dump_json()
    with pytest.raises(
        ValidationError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_REQUIRED",
    ):
        ExactBrowserActionReceipt.model_validate_json(
            replay.receipt.model_dump_json()
        )


@pytest.mark.parametrize("terminal_state", ("blocked", "failed"))
def test_post_form_blocked_and_failed_terminals_replay_content_free(
    tmp_path: Path,
    terminal_state: str,
) -> None:
    request, schema, recipe, _ = _post_context(
        suffix=f"terminal-replay-{terminal_state}"
    )
    kernel, _ = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=lambda item: _readiness(
            item,
            safe_disable=terminal_state == "blocked",
        ),
    )
    transport = _ExactPostFormPlanTransport(
        **(
            {"raw_dom": "<html>terminal replay private post form</html>"}
            if terminal_state == "failed"
            else {}
        )
    )
    service, _ = _service(
        request=request,
        schema=schema,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    first = _plan(service, request, recipe.recipe_ref)
    replay = _plan(service, request, recipe.recipe_ref)

    expected_state = {
        "blocked": ExternalActionState.blocked.value,
        "failed": ExternalActionState.failed.value,
    }[terminal_state]
    expected_first_status = {
        "blocked": ExactBrowserActionStatus.transaction_blocked.value,
        "failed": ExactBrowserActionStatus.failed.value,
    }[terminal_state]
    assert first.receipt.status == expected_first_status
    assert replay.receipt.status == ExactBrowserActionStatus.replayed_content_free.value
    assert replay.receipt.external_action_state == expected_state
    assert (
        replay.receipt.external_action_receipt_ref
        == first.receipt.external_action_receipt_ref
    )
    assert replay.receipt.replayed is True
    assert replay.receipt.content_free is True
    assert replay.receipt.automatic_retry_allowed is False
    assert replay.plan is None
    assert transport.calls == {"blocked": 0, "failed": 1}[terminal_state]
    assert "terminal replay private post form" not in replay.model_dump_json()


@pytest.mark.parametrize(
    "mutation",
    (
        "evidence_plan_substitution",
        "evidence_projection_substitution",
        "evidence_order",
        "evidence_arity_drop",
        "evidence_arity_extra",
        "cross_lane",
        "cross_operation",
        "cross_recipe",
        "cross_transaction",
    ),
)
def test_post_form_replay_requires_exact_durable_provenance(
    tmp_path: Path,
    mutation: str,
) -> None:
    request, schema, recipe, _ = _post_context(
        suffix=f"replay-provenance-{mutation}"
    )
    kernel, _ = _authorized_kernel(tmp_path, request)
    service, _ = _service(
        request=request,
        schema=schema,
        recipe=recipe,
        kernel=kernel,
        transport=_ExactPostFormPlanTransport(),
    )
    _plan(service, request, recipe.recipe_ref)
    replay = _plan(service, request, recipe.recipe_ref)
    kernel_request = _post_form_kernel_execution(
        request,
        recipe_ref=recipe.recipe_ref,
    )
    replay_receipt = kernel.replay_if_terminal(kernel_request)
    assert replay_receipt is not None
    expectation = _post_form_replay_expectation(
        recipe,
        schema,
        replay_receipt,
        kernel=kernel,
        expected_execution=kernel_request,
    )
    provenance = _build_external_action_replay_validation_context(
        kernel,
        expected_execution=kernel_request,
        replay_receipt=replay_receipt,
        expectation=expectation,
    )
    context = replay_validation_context(provenance)
    payload = replay.receipt.model_dump(mode="json")

    with pytest.raises(
        ValidationError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_REQUIRED",
    ):
        ExactBrowserActionReceipt.model_validate(payload)
    assert (
        ExactBrowserActionReceipt.model_validate(payload, context=context)
        == replay.receipt
    )

    receipt_prefix = "receipt-ref:governed-post-form"
    if mutation == "cross_operation":
        wrong_expectation = ExternalActionReplayEvidenceExpectation(
            lane_ref=expectation.lane_ref,
            operation_ref=_ref("replay-operation", "post-form-cross"),
            scope_refs=expectation.scope_refs,
            evidence_refs=expectation.evidence_refs,
            operation_proof_ref=expectation.operation_proof_ref,
        )
        with pytest.raises(
            ValueError,
            match="GOVERNED_EXTERNAL_ACTION_REPLAY_OPERATION_PROOF_INVALID",
        ):
            _build_external_action_replay_validation_context(
                kernel,
                expected_execution=kernel_request,
                replay_receipt=replay_receipt,
                expectation=wrong_expectation,
            )
        return
    elif mutation == "evidence_plan_substitution":
        payload["evidence_refs"][0] = _ref(
            "evidence",
            "post-form-replay-provenance-plan-substitute",
        )
    elif mutation == "evidence_projection_substitution":
        payload["evidence_refs"][1] = _ref(
            "evidence",
            "post-form-replay-provenance-projection-substitute",
        )
    elif mutation == "evidence_order":
        payload["evidence_refs"] = list(reversed(payload["evidence_refs"]))
    elif mutation == "evidence_arity_drop":
        payload["evidence_refs"] = payload["evidence_refs"][:-1]
    elif mutation == "evidence_arity_extra":
        payload["evidence_refs"].append(
            _ref("evidence", "post-form-replay-provenance-extra")
        )
    elif mutation == "cross_lane":
        receipt_prefix = "receipt-ref:governed-browser-action"
    elif mutation == "cross_recipe":
        payload["recipe_ref"] = _ref("recipe", "post-form-replay-provenance-cross")
    else:
        foreign_request, foreign_schema, foreign_recipe, _ = _post_context(
            suffix="post-form-replay-provenance-foreign"
        )
        foreign_kernel, _ = _authorized_kernel(
            tmp_path / "foreign",
            foreign_request,
        )
        foreign_service, _ = _service(
            request=foreign_request,
            schema=foreign_schema,
            recipe=foreign_recipe,
            kernel=foreign_kernel,
            transport=_ExactPostFormPlanTransport(),
        )
        _plan(foreign_service, foreign_request, foreign_recipe.recipe_ref)
        foreign_kernel_request = _post_form_kernel_execution(
            foreign_request,
            recipe_ref=foreign_recipe.recipe_ref,
        )
        foreign = foreign_kernel.replay_if_terminal(foreign_kernel_request)
        assert foreign is not None
        payload.update(
            {
                "transaction_ref": foreign.transaction_ref,
                "intent_ref": foreign.intent_ref,
                "binding_ref": foreign.binding_ref,
                "external_action_state": foreign.state,
                "approval_validation_ref": foreign.approval_validation_ref,
                "authority_decision_ref": foreign.authority_decision_ref,
                "budget_reservation_ref": foreign.budget_reservation_ref,
                "budget_release_ref": foreign.budget_release_ref,
                "budget_settlement_ref": foreign.budget_settlement_ref,
                "evidence_refs": list(foreign.evidence_refs),
                "reason_refs": list(foreign.reason_refs),
                "replayed": foreign.replayed,
            }
        )
    forged = _rehash_post_form_replay(
        payload,
        receipt_prefix=receipt_prefix,
    )

    with pytest.raises(
        ValidationError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_",
    ):
        ExactBrowserActionReceipt.model_validate(forged, context=context)


@pytest.mark.parametrize(
    "state",
    (
        ExternalActionState.prepared,
        ExternalActionState.started,
        ExternalActionState.outcome_ambiguous,
    ),
)
def test_post_form_replay_expectation_rejects_nonterminal_or_arbitrary_ambiguity(
    tmp_path: Path,
    state: ExternalActionState,
) -> None:
    request, schema, recipe, _ = _post_context(
        suffix=f"replay-envelope-reject-{state.value}"
    )
    kernel, _ = _authorized_kernel(tmp_path, request)
    service, _ = _service(
        request=request,
        schema=schema,
        recipe=recipe,
        kernel=kernel,
        transport=_ExactPostFormPlanTransport(),
    )
    _plan(service, request, recipe.recipe_ref)
    kernel_request = _post_form_kernel_execution(
        request,
        recipe_ref=recipe.recipe_ref,
    )
    durable = kernel.replay_if_terminal(kernel_request)
    assert durable is not None
    evidence_refs = (
        (_ref("evidence", "arbitrary-post-form-ambiguity"),)
        if state == ExternalActionState.outcome_ambiguous
        else durable.evidence_refs
    )
    malformed = durable.model_copy(
        update={
            "state": state.value,
            "evidence_refs": evidence_refs,
        }
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_POST_FORM_REPLAY_EVIDENCE_PROVENANCE_REQUIRED",
    ):
        _post_form_replay_expectation(
            recipe,
            schema,
            malformed,
            kernel=kernel,
            expected_execution=kernel_request,
        )


def test_post_form_settlement_failure_suppresses_plan_and_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, schema, recipe, _ = _post_context(suffix="settlement")
    kernel, _ = _authorized_kernel(tmp_path, request)
    monkeypatch.setattr(
        kernel._budget_gate,
        "settle",
        lambda _request, _reservation_ref, _outcome, _evidence_refs: BudgetSettlement(
            allowed=False,
            reason_refs=["reason-ref:governed-post-form:settlement-unconfirmed"],
        ),
    )
    transport = _ExactPostFormPlanTransport()
    service, _ = _service(
        request=request,
        schema=schema,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _plan(service, request, recipe.recipe_ref)

    assert result.receipt.status == ExactBrowserActionStatus.outcome_ambiguous.value
    assert result.receipt.automatic_retry_allowed is False
    assert result.plan is None
    assert transport.calls == 1


@pytest.mark.parametrize(
    "override",
    [
        {"method": "GET"},
        {"target_visible": False},
        {"same_origin_verified": False},
        {"registered_schema_verified": False},
        {"field_bindings_verified": False},
        {"request_body_materialized": True},
        {"request_body_included": True},
        {"form_submission_performed": True},
        {"field_values_resolved": True},
        {"network_call_performed": True},
        {"external_mutation_performed": True},
        {"raw_dom": "<html>private post form</html>"},
        {"body": "raw-private-post-body"},
    ],
)
def test_post_transport_drift_or_execution_fails_content_free(
    tmp_path: Path,
    override: dict[str, Any],
) -> None:
    request, schema, recipe, _ = _post_context(suffix=f"unsafe-{next(iter(override))}")
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactPostFormPlanTransport(**override)
    service, _ = _service(
        request=request,
        schema=schema,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _plan(service, request, recipe.recipe_ref)

    assert result.receipt.status == ExactBrowserActionStatus.failed.value
    assert result.receipt.external_action_state == ExternalActionState.failed.value
    assert result.receipt.reason_refs == [
        "reason-ref:governed-post-form:plan-dispatch-failed"
    ]
    assert result.plan is None
    assert transport.calls == 1
    payload = result.receipt.model_dump_json()
    assert "<html>" not in payload
    assert "raw-private-post-body" not in payload


@pytest.mark.parametrize(
    "proof_flag",
    [
        "target_visible",
        "same_origin_verified",
        "registered_schema_verified",
        "field_bindings_verified",
        "plan_generated",
    ],
)
def test_post_transport_requires_explicit_proof_flags(
    tmp_path: Path,
    proof_flag: str,
) -> None:
    request, schema, recipe, _ = _post_context(suffix=f"missing-{proof_flag}")
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactPostFormPlanTransport(omit={proof_flag})
    service, _ = _service(
        request=request,
        schema=schema,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _plan(service, request, recipe.recipe_ref)

    assert result.receipt.status == ExactBrowserActionStatus.failed.value
    assert result.plan is None
    assert transport.calls == 1


def test_transport_contract_rejects_body_materialization() -> None:
    request, schema, recipe, _ = _post_context(suffix="transport-contract")
    del request
    item = recipe.field_value_bindings[0]

    with pytest.raises(ValidationError):
        ExactPostFormDryRunTransportResult(
            recipe_ref=recipe.recipe_ref,
            plan_ref=recipe.plan_ref,
            binding_ref=recipe.binding_ref,
            schema_ref=schema.schema_ref,
            origin_ref=schema.exact_origin_ref,
            page_snapshot_ref=schema.page_snapshot_ref,
            source_observation_ref=schema.source_observation_ref,
            source_safe_url_ref=schema.source_safe_url_ref,
            destination_origin_ref=schema.destination_origin_ref,
            destination_safe_url_ref=schema.destination_safe_url_ref,
            element_ref=schema.element_ref,
            visibility_proof_ref=schema.visibility_proof_ref,
            field_value_bindings=[item],
            target_visible=True,
            same_origin_verified=True,
            registered_schema_verified=True,
            field_bindings_verified=True,
            plan_generated=True,
            request_body_materialized=True,
        )


def test_real_external_target_cannot_create_post_recipe() -> None:
    with pytest.raises(ValueError, match="REAL_TARGETS_INACTIVE"):
        _post_context(
            suffix="external",
            target_kind=ExternalActionTargetKind.external,
        )


def test_post_receipt_omits_origin_approval_and_value_refs(
    tmp_path: Path,
) -> None:
    request, schema, recipe, refs = _post_context(suffix="content-free")
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactPostFormPlanTransport()
    service, _ = _service(
        request=request,
        schema=schema,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _plan(service, request, recipe.recipe_ref)
    payload = json.dumps(result.receipt.model_dump(mode="json"), sort_keys=True)

    assert request.binding.origin not in payload
    assert request.approval_ref not in payload
    assert refs["first_value"] not in payload
    assert result.raw_gateway_result_returned is False
    assert result.raw_transport_result_returned is False


def test_queue01_group05_verifier() -> None:
    assert verify() == []
