from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from scripts.verify_governed_browser_queue01_group04 import verify
from tests.test_governed_browser_queue01_group01 import (
    _authorized_kernel,
    _binding,
    _readiness,
    _request,
    _ref,
)
from ultimate_ai_agent.core.authority import AuthorityCapability
from ultimate_ai_agent.core.governed_browser import (
    BrowserActionDryRunTransportResult,
    ExactBrowserActionRequest,
    ExactBrowserActionReceipt,
    ExactBrowserActionService,
    ExactBrowserActionStatus,
    ExternalActionAuthorityBinding,
    ExternalActionState,
    ExternalActionTargetKind,
    GovernedBrowserActionKind,
    GovernedBrowserActionRecipe,
    GovernedBrowserActionRecipeRegistry,
    IsolatedBrowserActionDryRunBrokerAdapter,
    build_governed_browser_action_recipe,
    create_isolated_browser_action_dry_run_gateway,
)
from ultimate_ai_agent.core.governed_browser.browser_actions import (
    _browser_action_kernel_execution,
    _browser_action_replay_expectation,
)
from ultimate_ai_agent.core.governed_browser.contracts import (
    governed_receipt_identity_payload,
    stable_governed_browser_ref,
)
from ultimate_ai_agent.core.governed_browser.replay_provenance import (
    _build_external_action_replay_validation_context,
    replay_validation_context,
)
from ultimate_ai_agent.core.governed_browser.transaction import BudgetSettlement


SOURCE_OBSERVATION_REF = (
    "browser-observe-output:governed-browser:exact-page-observation"
)
SOURCE_SAFE_URL_REF = "browser-url:governed-browser/local-source"
DESTINATION_SAFE_URL_REF = "browser-url:governed-browser/local-destination"
ELEMENT_REF = "browser-element-ref:governed-browser:visible-target"
VISIBILITY_PROOF_REF = "visibility-proof-ref:governed-browser:visible-target"
FIELD_VALUE_REFS = (
    "form-field-value-ref:governed-browser:query-one",
    "form-field-value-ref:governed-browser:query-two",
)


def _exact_request(
    *,
    suffix: str = "action",
    operation: GovernedBrowserActionKind = GovernedBrowserActionKind.visible_click,
    target_kind: ExternalActionTargetKind = ExternalActionTargetKind.local_validation,
):  # type: ignore[no-untyped-def]
    base = _binding(suffix=suffix, target_kind=target_kind)
    capability = {
        GovernedBrowserActionKind.visible_click: AuthorityCapability.click,
        GovernedBrowserActionKind.get_form: AuthorityCapability.form_fill,
    }[operation]
    field_refs = (
        FIELD_VALUE_REFS if operation == GovernedBrowserActionKind.get_form else ()
    )
    binding = ExternalActionAuthorityBinding.model_validate(
        {
            **base.model_dump(mode="json"),
            "authority_capability": capability,
            "resource_refs": [
                _ref("resource", suffix),
                SOURCE_OBSERVATION_REF,
                SOURCE_SAFE_URL_REF,
                DESTINATION_SAFE_URL_REF,
                ELEMENT_REF,
                VISIBILITY_PROOF_REF,
                *field_refs,
            ],
        }
    )
    return _request(binding)


def _recipe(
    request,
    operation: GovernedBrowserActionKind,
):  # type: ignore[no-untyped-def]
    return build_governed_browser_action_recipe(
        request,
        operation=operation,
        source_observation_ref=SOURCE_OBSERVATION_REF,
        source_safe_url_ref=SOURCE_SAFE_URL_REF,
        destination_safe_url_ref=DESTINATION_SAFE_URL_REF,
        element_ref=ELEMENT_REF,
        visibility_proof_ref=VISIBILITY_PROOF_REF,
        field_value_refs=(
            FIELD_VALUE_REFS if operation == GovernedBrowserActionKind.get_form else ()
        ),
    )


class _ExactActionPlanTransport:
    def __init__(self, **overrides: Any) -> None:
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
            "origin_ref": request.metadata["exact_origin_ref"],
            "page_snapshot_ref": request.metadata["page_snapshot_ref"],
            "source_observation_ref": request.metadata["source_observation_ref"],
            "source_safe_url_ref": request.metadata["source_safe_url_ref"],
            "destination_origin_ref": request.metadata["destination_origin_ref"],
            "destination_safe_url_ref": request.metadata["destination_safe_url_ref"],
            "element_ref": request.metadata["element_ref"],
            "visibility_proof_ref": request.metadata["visibility_proof_ref"],
            "field_schema_ref": request.metadata["field_schema_ref"],
            "field_value_refs": request.metadata["field_value_refs"],
            "operation": request.metadata["operation"],
            "method": "GET",
            "target_visible": True,
            "same_origin_verified": True,
            "field_schema_verified": True,
            "plan_generated": True,
            "source_observation_content_untrusted": True,
            "web_content_instruction_use_allowed": False,
        }
        payload.update(self.overrides)
        return payload


def _service(
    *,
    request,
    recipe,
    kernel,
    transport: _ExactActionPlanTransport,
):  # type: ignore[no-untyped-def]
    broker = IsolatedBrowserActionDryRunBrokerAdapter(
        transport=transport,
        allowed_origin_refs={request.binding.origin_ref},
    )
    service = ExactBrowserActionService(
        registry=GovernedBrowserActionRecipeRegistry([recipe]),
        kernel=kernel,
        gateway=create_isolated_browser_action_dry_run_gateway(broker),
    )
    return service, broker


def _plan(service, request, recipe_ref):  # type: ignore[no-untyped-def]
    return service.plan(
        ExactBrowserActionRequest(
            recipe_ref=recipe_ref,
            execution_request=request,
        )
    )


def _rehash_action_replay(
    payload: dict[str, Any],
    *,
    receipt_prefix: str = "receipt-ref:governed-browser-action",
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


@pytest.mark.parametrize(
    "operation",
    [
        GovernedBrowserActionKind.visible_click,
        GovernedBrowserActionKind.get_form,
    ],
)
def test_registered_same_origin_visible_action_is_governed_and_inactive(
    tmp_path: Path,
    operation: GovernedBrowserActionKind,
) -> None:
    request = _exact_request(suffix=operation.value, operation=operation)
    recipe = _recipe(request, operation)
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactActionPlanTransport()
    service, broker = _service(
        request=request,
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
    assert result.plan.recipe_ref == recipe.recipe_ref
    assert result.plan.plan_ref == recipe.plan_ref
    assert result.plan.operation == operation.value
    assert result.plan.method == "GET"
    assert result.plan.origin_ref == request.binding.origin_ref
    assert result.plan.page_snapshot_ref == request.binding.page_snapshot_ref
    assert result.plan.target_visible is True
    assert result.plan.same_origin_verified is True
    assert result.plan.field_schema_verified is True
    assert result.plan.injected_local_validation is True
    assert result.plan.browser_session_started is False
    assert result.plan.action_execution_performed is False
    assert result.plan.live_network_performed is False
    assert result.plan.external_mutation_performed is False
    assert result.plan.content_untrusted is True
    assert result.plan.web_content_instruction_use_allowed is False
    if operation == GovernedBrowserActionKind.visible_click:
        assert result.plan.field_value_refs == ()
        assert request.binding.authority_capability == AuthorityCapability.click.value
    else:
        assert result.plan.field_value_refs == FIELD_VALUE_REFS
        assert (
            request.binding.authority_capability == AuthorityCapability.form_fill.value
        )
    assert transport.calls == 1
    assert broker.closed_profile_refs
    assert all(not path.exists() for path in transport.profile_directories)
    metadata = transport.requests[0].metadata
    assert metadata["browser_action_execution"] is False
    assert metadata["browser_session_start"] is False
    assert metadata["navigation_execution"] is False
    assert metadata["click_execution"] is False
    assert metadata["form_fill_execution"] is False
    assert metadata["request_body"] is False
    assert metadata["network_call"] is False


def test_unknown_recipe_is_blocked_before_authority_or_gateway(
    tmp_path: Path,
) -> None:
    operation = GovernedBrowserActionKind.visible_click
    request = _exact_request(suffix="unknown", operation=operation)
    recipe = _recipe(request, operation)
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactActionPlanTransport()
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _plan(
        service,
        request,
        "browser-action-recipe-ref:governed-browser:unregistered",
    )

    assert result.receipt.status == ExactBrowserActionStatus.preflight_blocked.value
    assert result.receipt.reason_refs == [
        "reason-ref:governed-browser-action:recipe-unregistered"
    ]
    assert result.receipt.approval_validation_ref is None
    assert result.receipt.authority_decision_ref is None
    assert result.receipt.budget_reservation_ref is None
    assert result.plan is None
    assert transport.calls == 0


def test_approval_identifier_alone_grants_nothing(tmp_path: Path) -> None:
    operation = GovernedBrowserActionKind.visible_click
    authorized = _exact_request(suffix="approval-id", operation=operation)
    recipe = _recipe(authorized, operation)
    kernel, _ = _authorized_kernel(tmp_path, authorized)
    guessed = authorized.model_copy(
        update={"approval_ref": "approval-ref:governed-browser:guessed"}
    )
    transport = _ExactActionPlanTransport()
    service, _ = _service(
        request=authorized,
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
def test_revalidation_denies_before_action_plan(
    tmp_path: Path,
    mode: str,
) -> None:
    operation = GovernedBrowserActionKind.get_form
    request = _exact_request(suffix=f"revalidate-{mode}", operation=operation)
    recipe = _recipe(request, operation)

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
    transport = _ExactActionPlanTransport()
    service, _ = _service(
        request=request,
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


def test_recipe_scope_cannot_cross_bindings_or_capabilities(
    tmp_path: Path,
) -> None:
    operation = GovernedBrowserActionKind.visible_click
    original = _exact_request(suffix="scope-original", operation=operation)
    recipe = _recipe(original, operation)
    drifted = _exact_request(suffix="scope-drifted", operation=operation)
    kernel, _ = _authorized_kernel(tmp_path, drifted)
    transport = _ExactActionPlanTransport()
    service, _ = _service(
        request=drifted,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _plan(service, drifted, recipe.recipe_ref)

    assert result.receipt.status == ExactBrowserActionStatus.preflight_blocked.value
    assert result.receipt.reason_refs == [
        "reason-ref:governed-browser-action:binding-mismatch"
    ]
    assert result.plan is None
    assert transport.calls == 0

    generic = _request(_binding(suffix="generic-capability"))
    with pytest.raises(ValueError, match="EXACT_CAPABILITY_MISMATCH"):
        build_governed_browser_action_recipe(
            generic,
            operation=operation,
            source_observation_ref=generic.binding.resource_refs[0],
            source_safe_url_ref=generic.binding.resource_refs[0],
            destination_safe_url_ref=generic.binding.resource_refs[0],
            element_ref=generic.binding.resource_refs[0],
            visibility_proof_ref=generic.binding.resource_refs[0],
        )


def test_action_plan_is_at_most_once_and_replay_is_content_free(
    tmp_path: Path,
) -> None:
    operation = GovernedBrowserActionKind.get_form
    request = _exact_request(suffix="replay", operation=operation)
    recipe = _recipe(request, operation)
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactActionPlanTransport()
    service, _ = _service(
        request=request,
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
    assert SOURCE_OBSERVATION_REF not in replay.receipt.model_dump_json()
    with pytest.raises(
        ValidationError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_REQUIRED",
    ):
        ExactBrowserActionReceipt.model_validate_json(
            replay.receipt.model_dump_json()
        )


@pytest.mark.parametrize("terminal_state", ("blocked", "failed"))
def test_action_blocked_and_failed_terminals_replay_content_free(
    tmp_path: Path,
    terminal_state: str,
) -> None:
    operation = GovernedBrowserActionKind.visible_click
    request = _exact_request(
        suffix=f"terminal-replay-{terminal_state}",
        operation=operation,
    )
    recipe = _recipe(request, operation)
    kernel, _ = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=lambda item: _readiness(
            item,
            safe_disable=terminal_state == "blocked",
        ),
    )
    transport = _ExactActionPlanTransport(
        **(
            {"raw_dom": "<html>terminal replay private action</html>"}
            if terminal_state == "failed"
            else {}
        )
    )
    service, _ = _service(
        request=request,
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
    assert "terminal replay private action" not in replay.model_dump_json()


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
def test_action_replay_requires_exact_durable_provenance(
    tmp_path: Path,
    mutation: str,
) -> None:
    operation = GovernedBrowserActionKind.get_form
    request = _exact_request(suffix=f"replay-provenance-{mutation}", operation=operation)
    recipe = _recipe(request, operation)
    kernel, _ = _authorized_kernel(tmp_path, request)
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=_ExactActionPlanTransport(),
    )
    _plan(service, request, recipe.recipe_ref)
    replay = _plan(service, request, recipe.recipe_ref)
    kernel_request = _browser_action_kernel_execution(
        request,
        recipe_ref=recipe.recipe_ref,
    )
    replay_receipt = kernel.replay_if_terminal(kernel_request)
    assert replay_receipt is not None
    expectation = _browser_action_replay_expectation(recipe, replay_receipt)
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

    receipt_prefix = "receipt-ref:governed-browser-action"
    if mutation == "evidence_plan_substitution":
        payload["evidence_refs"][0] = _ref(
            "evidence",
            "action-replay-provenance-plan-substitute",
        )
    elif mutation == "evidence_projection_substitution":
        payload["evidence_refs"][1] = _ref(
            "evidence",
            "action-replay-provenance-projection-substitute",
        )
    elif mutation == "evidence_order":
        payload["evidence_refs"] = list(reversed(payload["evidence_refs"]))
    elif mutation == "evidence_arity_drop":
        payload["evidence_refs"] = payload["evidence_refs"][:-1]
    elif mutation == "evidence_arity_extra":
        payload["evidence_refs"].append(
            _ref("evidence", "action-replay-provenance-extra")
        )
    elif mutation == "cross_lane":
        receipt_prefix = "receipt-ref:governed-post-form"
    elif mutation == "cross_recipe":
        payload["recipe_ref"] = _ref("recipe", "action-replay-provenance-cross")
    elif mutation == "cross_operation":
        foreign_operation = GovernedBrowserActionKind.visible_click
        foreign_request = _exact_request(
            suffix="action-replay-provenance-cross-operation",
            operation=foreign_operation,
        )
        foreign_recipe = _recipe(foreign_request, foreign_operation)
        foreign_kernel, _ = _authorized_kernel(
            tmp_path / "foreign-operation",
            foreign_request,
        )
        foreign_service, _ = _service(
            request=foreign_request,
            recipe=foreign_recipe,
            kernel=foreign_kernel,
            transport=_ExactActionPlanTransport(),
        )
        _plan(foreign_service, foreign_request, foreign_recipe.recipe_ref)
        foreign_kernel_request = _browser_action_kernel_execution(
            foreign_request,
            recipe_ref=foreign_recipe.recipe_ref,
        )
        foreign = foreign_kernel.replay_if_terminal(foreign_kernel_request)
        assert foreign is not None
        payload.update(
            {
                "recipe_ref": foreign_recipe.recipe_ref,
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
    else:
        foreign_request = _exact_request(
            suffix="action-replay-provenance-foreign",
            operation=operation,
        )
        foreign_recipe = _recipe(foreign_request, operation)
        foreign_kernel, _ = _authorized_kernel(
            tmp_path / "foreign",
            foreign_request,
        )
        foreign_service, _ = _service(
            request=foreign_request,
            recipe=foreign_recipe,
            kernel=foreign_kernel,
            transport=_ExactActionPlanTransport(),
        )
        _plan(foreign_service, foreign_request, foreign_recipe.recipe_ref)
        foreign_kernel_request = _browser_action_kernel_execution(
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
    forged = _rehash_action_replay(payload, receipt_prefix=receipt_prefix)

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
def test_action_replay_expectation_rejects_nonterminal_or_arbitrary_ambiguity(
    tmp_path: Path,
    state: ExternalActionState,
) -> None:
    operation = GovernedBrowserActionKind.visible_click
    request = _exact_request(
        suffix=f"replay-envelope-reject-{state.value}",
        operation=operation,
    )
    recipe = _recipe(request, operation)
    kernel, _ = _authorized_kernel(tmp_path, request)
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=_ExactActionPlanTransport(),
    )
    _plan(service, request, recipe.recipe_ref)
    kernel_request = _browser_action_kernel_execution(
        request,
        recipe_ref=recipe.recipe_ref,
    )
    durable = kernel.replay_if_terminal(kernel_request)
    assert durable is not None
    evidence_refs = (
        (_ref("evidence", "arbitrary-action-ambiguity"),)
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
        match="GOVERNED_BROWSER_ACTION_REPLAY_EVIDENCE_PROVENANCE_REQUIRED",
    ):
        _browser_action_replay_expectation(recipe, malformed)


def test_settlement_failure_suppresses_plan_and_forbids_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    operation = GovernedBrowserActionKind.visible_click
    request = _exact_request(suffix="settlement", operation=operation)
    recipe = _recipe(request, operation)
    kernel, _ = _authorized_kernel(tmp_path, request)
    monkeypatch.setattr(
        kernel._budget_gate,
        "settle",
        lambda _request, _reservation_ref, _outcome, _evidence_refs: BudgetSettlement(
            allowed=False,
            reason_refs=["reason-ref:governed-browser-action:settlement-unconfirmed"],
        ),
    )
    transport = _ExactActionPlanTransport()
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _plan(service, request, recipe.recipe_ref)

    assert result.receipt.status == ExactBrowserActionStatus.outcome_ambiguous.value
    assert (
        result.receipt.external_action_state
        == ExternalActionState.outcome_ambiguous.value
    )
    assert result.receipt.automatic_retry_allowed is False
    assert result.plan is None
    assert transport.calls == 1


@pytest.mark.parametrize(
    "override",
    [
        {"target_visible": False},
        {"same_origin_verified": False},
        {"method": "POST"},
        {"request_body_included": True},
        {"browser_session_started": True},
        {"click_performed": True},
        {"network_call_performed": True},
        {"raw_dom": "<html>private content</html>"},
        {"preview": "raw private preview"},
    ],
)
def test_hidden_cross_origin_or_executed_transport_output_fails_content_free(
    tmp_path: Path,
    override: dict[str, Any],
) -> None:
    operation = GovernedBrowserActionKind.visible_click
    suffix = f"unsafe-{next(iter(override))}"
    request = _exact_request(suffix=suffix, operation=operation)
    recipe = _recipe(request, operation)
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactActionPlanTransport(**override)
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _plan(service, request, recipe.recipe_ref)

    assert result.receipt.status == ExactBrowserActionStatus.failed.value
    assert result.receipt.external_action_state == ExternalActionState.failed.value
    assert result.receipt.reason_refs == [
        "reason-ref:governed-browser-action:plan-dispatch-failed"
    ]
    assert result.plan is None
    assert transport.calls == 1
    payload = result.receipt.model_dump_json()
    assert "<html>" not in payload
    assert "private content" not in payload
    assert "raw private preview" not in payload


def test_action_recipe_contract_rejects_cross_origin_post_and_raw_values() -> None:
    operation = GovernedBrowserActionKind.get_form
    request = _exact_request(suffix="contract", operation=operation)
    recipe = _recipe(request, operation)
    payload = recipe.model_dump(mode="json")

    with pytest.raises(ValidationError, match="CROSS_ORIGIN_DENIED"):
        GovernedBrowserActionRecipe.model_validate(
            {
                **payload,
                "destination_origin_ref": ("origin-ref:governed-browser:cross-origin"),
            }
        )
    with pytest.raises(ValidationError):
        GovernedBrowserActionRecipe.model_validate({**payload, "method": "POST"})
    with pytest.raises(ValidationError):
        GovernedBrowserActionRecipe.model_validate(
            {**payload, "action_execution_allowed": True}
        )
    with pytest.raises(ValidationError):
        GovernedBrowserActionRecipe.model_validate(
            {**payload, "live_network_allowed": True}
        )
    with pytest.raises(ValidationError, match="structured safe ref"):
        GovernedBrowserActionRecipe.model_validate(
            {
                **payload,
                "field_value_refs": ["query=raw-private-value"],
            }
        )
    with pytest.raises(ValidationError):
        BrowserActionDryRunTransportResult.model_validate(
            {
                "recipe_ref": recipe.recipe_ref,
                "plan_ref": recipe.plan_ref,
                "binding_ref": recipe.binding_ref,
                "origin_ref": recipe.exact_origin_ref,
                "page_snapshot_ref": recipe.page_snapshot_ref,
                "source_observation_ref": recipe.source_observation_ref,
                "source_safe_url_ref": recipe.source_safe_url_ref,
                "destination_origin_ref": recipe.destination_origin_ref,
                "destination_safe_url_ref": recipe.destination_safe_url_ref,
                "element_ref": recipe.element_ref,
                "visibility_proof_ref": recipe.visibility_proof_ref,
                "field_schema_ref": recipe.field_schema_ref,
                "field_value_refs": recipe.field_value_refs,
                "operation": recipe.operation,
                "request_body_included": True,
            }
        )


def test_registry_revalidates_tampered_recipe_copy() -> None:
    operation = GovernedBrowserActionKind.visible_click
    request = _exact_request(suffix="tamper", operation=operation)
    recipe = _recipe(request, operation)

    with pytest.raises(ValidationError):
        GovernedBrowserActionRecipeRegistry(
            [
                recipe.model_copy(
                    update={
                        "element_ref": ("browser-element-ref:governed-browser:unbound")
                    }
                )
            ]
        )


def test_real_external_target_cannot_create_an_action_recipe() -> None:
    operation = GovernedBrowserActionKind.visible_click
    external = _exact_request(
        suffix="external",
        operation=operation,
        target_kind=ExternalActionTargetKind.external,
    )

    with pytest.raises(ValueError, match="REAL_TARGETS_INACTIVE"):
        _recipe(external, operation)


def test_receipt_never_serializes_raw_origin_or_approval_identifier(
    tmp_path: Path,
) -> None:
    operation = GovernedBrowserActionKind.visible_click
    request = _exact_request(suffix="content-free", operation=operation)
    recipe = _recipe(request, operation)
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactActionPlanTransport()
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _plan(service, request, recipe.recipe_ref)
    receipt_payload = json.dumps(result.receipt.model_dump(mode="json"), sort_keys=True)

    assert request.binding.origin not in receipt_payload
    assert request.approval_ref not in receipt_payload
    assert SOURCE_SAFE_URL_REF not in receipt_payload
    assert result.raw_gateway_result_returned is False
    assert result.raw_transport_result_returned is False


def test_queue01_group04_verifier() -> None:
    assert verify() == []
