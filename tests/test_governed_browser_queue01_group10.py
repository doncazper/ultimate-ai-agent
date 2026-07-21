from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import ultimate_ai_agent.core.governed_browser.financial_operation_contracts as financial_operation_module
from scripts.verify_governed_browser_queue01_group10 import verify
from tests.test_governed_browser_queue01_group01 import (
    _authorized_kernel,
    _binding,
    _readiness,
    _ref,
    _request,
)
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityCapability
from ultimate_ai_agent.core.authority.budgets import AuthorityBudgetStore
from ultimate_ai_agent.core.governed_browser import (
    AuthorityBudgetStoreGate,
    ExactGovernedFinancialRequest,
    ExactGovernedFinancialService,
    ExternalActionAuthorityBinding,
    ExternalActionState,
    ExternalActionTargetKind,
    ExternalActionTransactionStore,
    GovernedExternalActionKernel,
    GovernedFinancialOperation,
    GovernedFinancialReceipt,
    GovernedFinancialRecipeRegistry,
    GovernedFinancialReversibility,
    build_exact_governed_financial_scope,
    build_external_action_approval_request,
    build_governed_financial_recipe,
    governed_financial_authority_ref,
    governed_financial_contract_ref,
    governed_financial_target_ref,
    stable_governed_browser_ref,
)
from ultimate_ai_agent.core.governed_browser.contracts import (
    governed_receipt_identity_payload,
)
from ultimate_ai_agent.core.governed_browser.replay_provenance import (
    ExternalActionReplayValidationContext,
    replay_validation_context,
)
from ultimate_ai_agent.core.time import utc_now


_CAPABILITY_BY_OPERATION = {
    GovernedFinancialOperation.purchase: AuthorityCapability.purchase,
    GovernedFinancialOperation.booking: AuthorityCapability.purchase_under_budget,
    GovernedFinancialOperation.checkout_payment: AuthorityCapability.purchase,
    GovernedFinancialOperation.financial_transaction: (
        AuthorityCapability.purchase_under_budget
    ),
}

_REVERSIBILITY_BY_OPERATION = {
    GovernedFinancialOperation.purchase: (
        GovernedFinancialReversibility.manual_recovery
    ),
    GovernedFinancialOperation.booking: (
        GovernedFinancialReversibility.manual_recovery
    ),
    GovernedFinancialOperation.checkout_payment: (
        GovernedFinancialReversibility.irreversible
    ),
    GovernedFinancialOperation.financial_transaction: (
        GovernedFinancialReversibility.irreversible
    ),
}


def _pinned(prefix: str, *, suffix: str) -> str:
    return stable_governed_browser_ref(prefix, {"suffix": suffix})


def _financial_context(
    *,
    operation: GovernedFinancialOperation,
    suffix: str,
    amount_minor_units: int = 1250,
    spend_limit_minor_units: int = 1500,
    target_kind: ExternalActionTargetKind = ExternalActionTargetKind.local_validation,
    human_present: bool = True,
    capability: AuthorityCapability | None = None,
    target_descriptor_ref: str | None = None,
    created_at=None,  # type: ignore[no-untyped-def]
    expires_at=None,  # type: ignore[no-untyped-def]
):
    base = _binding(
        suffix=suffix,
        target_kind=target_kind,
        human_present=human_present,
    )
    exact_created_at = created_at or utc_now()
    exact_expires_at = expires_at or min(
        exact_created_at + timedelta(minutes=5),
        base.start_deadline - timedelta(seconds=1),
    )
    target_ref = governed_financial_target_ref(
        operation=operation,
        target_descriptor_ref=(
            target_descriptor_ref or _ref("financial-target-descriptor", suffix)
        ),
    )
    artifact_refs = [_pinned("financial-artifact-ref:governed-browser", suffix=suffix)]
    booking_ref = (
        _pinned("booking-ref:governed-browser", suffix=suffix)
        if operation == GovernedFinancialOperation.booking
        else None
    )
    checkout_ref = (
        _pinned("checkout-ref:governed-browser", suffix=suffix)
        if operation == GovernedFinancialOperation.checkout_payment
        else None
    )
    financial_instrument_ref = (
        _pinned("financial-instrument-ref:governed-browser", suffix=suffix)
        if operation == GovernedFinancialOperation.financial_transaction
        else None
    )
    cancellation_policy_ref = (
        _pinned("cancellation-policy-ref:governed-browser", suffix=suffix)
        if operation == GovernedFinancialOperation.booking
        else None
    )
    refund_policy_ref = (
        _pinned("refund-policy-ref:governed-browser", suffix=suffix)
        if operation
        in {
            GovernedFinancialOperation.purchase,
            GovernedFinancialOperation.checkout_payment,
        }
        else None
    )
    scope = build_exact_governed_financial_scope(
        operation=operation,
        target_ref=target_ref,
        quote_ref=_pinned("financial-quote-ref:governed-browser", suffix=suffix),
        currency_ref=_pinned(
            "financial-currency-ref:governed-browser",
            suffix=suffix,
        ),
        payment_handle_ref=_pinned(
            "payment-handle-ref:governed-browser",
            suffix=suffix,
        ),
        amount_minor_units=amount_minor_units,
        spend_limit_minor_units=spend_limit_minor_units,
        artifact_refs=artifact_refs,
        booking_ref=booking_ref,
        checkout_ref=checkout_ref,
        financial_instrument_ref=financial_instrument_ref,
        cancellation_policy_ref=cancellation_policy_ref,
        refund_policy_ref=refund_policy_ref,
        reversibility=_REVERSIBILITY_BY_OPERATION[operation],
        rollback_ref=_pinned(
            "financial-rollback-ref:governed-browser",
            suffix=suffix,
        ),
        reconciliation_ref=_pinned(
            "financial-reconciliation-ref:governed-browser",
            suffix=suffix,
        ),
    )
    authority_ref = governed_financial_authority_ref(
        operation=operation,
        origin_ref=base.origin_ref,
        target_ref=scope.target_ref,
        schema_ref=scope.schema_ref,
    )
    contract_ref = governed_financial_contract_ref(
        operation=operation,
        origin_ref=base.origin_ref,
        page_snapshot_ref=base.page_snapshot_ref,
        authority_ref=authority_ref,
        scope=scope,
        expires_at=exact_expires_at,
    )
    binding = ExternalActionAuthorityBinding.model_validate(
        {
            **base.model_dump(mode="json"),
            "authority_capability": capability or _CAPABILITY_BY_OPERATION[operation],
            "recipient_ref": scope.target_ref,
            "field_schema_ref": scope.schema_ref,
            "artifact_refs": scope.artifact_refs,
            "resource_refs": sorted(
                scope.exact_resource_refs(
                    authority_ref=authority_ref,
                    contract_ref=contract_ref,
                )
            ),
        }
    )
    request = _request(binding)
    recipe = build_governed_financial_recipe(
        request,
        scope=scope,
        created_at=exact_created_at,
        expires_at=exact_expires_at,
    )
    return request, recipe, GovernedFinancialRecipeRegistry([recipe])


def _exact(request, recipe) -> ExactGovernedFinancialRequest:  # type: ignore[no-untyped-def]
    return ExactGovernedFinancialRequest(
        execution_request=request,
        recipe_ref=recipe.recipe_ref,
        contract_ref=recipe.contract_ref,
        operation=recipe.scope.operation,
        target_ref=recipe.scope.target_ref,
        financial_input_ref=recipe.scope.financial_input_ref,
    )


def _service(
    tmp_path: Path,
    *,
    request,
    registry,
    readiness_provider=None,  # type: ignore[no-untyped-def]
    clock=utc_now,  # type: ignore[no-untyped-def]
):  # type: ignore[no-untyped-def]
    kernel, authority = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=readiness_provider,
        clock=clock,
    )
    return (
        ExactGovernedFinancialService(
            registry=registry,
            kernel=kernel,
            clock=clock,
        ),
        authority,
    )


def _rehash_financial_receipt(payload: dict[str, object]) -> dict[str, object]:
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-financial-contract",
        governed_receipt_identity_payload(
            GovernedFinancialReceipt.model_construct(**payload)
        ),
    )
    return payload


def _rehash_external_and_financial_receipt(
    payload: dict[str, object],
) -> dict[str, object]:
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
    return _rehash_financial_receipt(payload)


def _financial_replay_proof(
    tmp_path: Path,
    *,
    operation: GovernedFinancialOperation,
    suffix: str,
) -> tuple[dict[str, object], ExternalActionReplayValidationContext]:
    request, recipe, registry = _financial_context(
        operation=operation,
        suffix=suffix,
    )
    service, _ = _service(
        tmp_path / suffix,
        request=request,
        registry=registry,
    )
    exact = _exact(request, recipe)
    service.prepare(exact)
    replay = service.prepare(exact)
    kernel_execution = financial_operation_module._kernel_execution(
        exact.execution_request,
        recipe_ref=recipe.recipe_ref,
    )
    replay_receipt = service._kernel.replay_if_terminal(kernel_execution)
    assert replay_receipt is not None
    context = financial_operation_module._financial_replay_validation_context(
        kernel=service._kernel,
        expected_execution=kernel_execution,
        recipe=recipe,
        replay_receipt=replay_receipt,
    )
    return replay.receipt.model_dump(mode="json"), context


def _financial_terminal_replay_proof(
    tmp_path: Path,
    *,
    terminal_state: ExternalActionState,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    dict[str, object],
    ExternalActionReplayValidationContext,
    list[str],
]:
    suffix = f"terminal-replay-{terminal_state.value}"
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.purchase,
        suffix=suffix,
    )
    service, _ = _service(
        tmp_path / suffix,
        request=request,
        registry=registry,
        readiness_provider=(
            (lambda item: _readiness(item, safe_disable=True))
            if terminal_state == ExternalActionState.blocked
            else None
        ),
    )
    exact = _exact(request, recipe)
    kernel_execution = financial_operation_module._kernel_execution(
        exact.execution_request,
        recipe_ref=recipe.recipe_ref,
    )
    if terminal_state == ExternalActionState.outcome_ambiguous:
        durable_store = ExternalActionTransactionStore(
            tmp_path / suffix / "transactions.sqlite3"
        )
        durable_store.prepare(kernel_execution)
        assert durable_store.claim_start(kernel_execution) is True
        with sqlite3.connect(
            tmp_path / suffix / "transactions.sqlite3"
        ) as connection:
            connection.execute(
                "UPDATE governed_external_actions SET updated_at = ? "
                "WHERE transaction_ref = ?",
                (
                    (utc_now() - timedelta(minutes=2)).isoformat(),
                    kernel_execution.binding.transaction_ref,
                ),
            )
    elif terminal_state == ExternalActionState.failed:
        original_execute = service._kernel.execute

        def execute_with_invalid_dispatch_clock(*args, **kwargs):  # type: ignore[no-untyped-def]
            monkeypatch.setattr(
                service,
                "_clock",
                lambda: datetime(2026, 7, 20, 12, 0, 0),
            )
            return original_execute(*args, **kwargs)

        monkeypatch.setattr(
            service._kernel,
            "execute",
            execute_with_invalid_dispatch_clock,
        )

    first = service.prepare(exact)
    if terminal_state == ExternalActionState.failed:
        monkeypatch.setattr(service._kernel, "execute", original_execute)
        monkeypatch.setattr(service, "_clock", utc_now)
    replay = service.prepare(exact)
    terminal_receipt = service._kernel.replay_if_terminal(kernel_execution)
    assert terminal_receipt is not None
    context = financial_operation_module._financial_replay_validation_context(
        kernel=service._kernel,
        expected_execution=kernel_execution,
        recipe=recipe,
        replay_receipt=terminal_receipt,
    )
    expected_evidence = {
        ExternalActionState.blocked: [],
        ExternalActionState.failed: [
            stable_governed_browser_ref(
                "evidence-ref:governed-financial:trusted-clock-invalid",
                {"intent_ref": kernel_execution.intent_ref},
            )
        ],
        ExternalActionState.outcome_ambiguous: [
            stable_governed_browser_ref(
                "evidence-ref:governed-external-action:prior-start-recovery",
                {
                    "transaction_ref": kernel_execution.binding.transaction_ref,
                    "intent_ref": kernel_execution.intent_ref,
                    "binding_ref": kernel_execution.binding.binding_ref,
                },
            )
        ],
    }[terminal_state]
    assert first.receipt.replayed is False
    assert first.receipt.external_action_state == terminal_state.value
    assert first.receipt.evidence_refs == expected_evidence
    assert replay.receipt.replayed is True
    assert replay.receipt.external_action_state == terminal_state.value
    assert replay.receipt.evidence_refs == expected_evidence
    return replay.receipt.model_dump(mode="json"), context, expected_evidence


def _seed_arbitrary_financial_terminal_evidence(
    tmp_path: Path,
    *,
    terminal_state: ExternalActionState,
) -> tuple[ExactGovernedFinancialService, ExactGovernedFinancialRequest]:
    suffix = f"arbitrary-terminal-evidence-{terminal_state.value}"
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.purchase,
        suffix=suffix,
    )
    service, _ = _service(
        tmp_path / suffix,
        request=request,
        registry=registry,
    )
    exact = _exact(request, recipe)
    kernel_execution = financial_operation_module._kernel_execution(
        exact.execution_request,
        recipe_ref=recipe.recipe_ref,
    )
    durable_store = ExternalActionTransactionStore(
        tmp_path / suffix / "transactions.sqlite3"
    )
    durable_store.prepare(kernel_execution)
    expected_state = ExternalActionState.prepared
    if terminal_state != ExternalActionState.blocked:
        assert durable_store.claim_start(kernel_execution) is True
        expected_state = ExternalActionState.started
    arbitrary_ref = stable_governed_browser_ref(
        "evidence-ref:governed-financial:arbitrary-non-success",
        {"state": terminal_state.value},
    )
    terminal_receipt = service._kernel._build_receipt(
        kernel_execution,
        terminal_state,
        ["reason-ref:governed-external-action:test-terminal-state"],
        evidence_refs=[arbitrary_ref],
    )
    durable_store.finish(terminal_receipt, expected_state=expected_state)
    return service, exact


@pytest.mark.parametrize("operation", list(GovernedFinancialOperation))
def test_registered_financial_operations_prepare_exact_inactive_contracts(
    tmp_path: Path,
    operation: GovernedFinancialOperation,
) -> None:
    request, recipe, registry = _financial_context(
        operation=operation,
        suffix=operation.value,
    )
    service, _ = _service(
        tmp_path / operation.value,
        request=request,
        registry=registry,
    )

    result = service.prepare(_exact(request, recipe))

    assert result.receipt.status == "contract_ready"
    assert result.receipt.external_action_state == "succeeded"
    assert result.receipt.evidence_refs == [
        recipe.contract_ref,
        recipe.authority_ref,
        recipe.scope.financial_input_ref,
        recipe.scope.quote_ref,
        recipe.scope.payment_handle_ref,
        recipe.scope.rollback_ref,
        recipe.scope.reconciliation_ref,
    ]
    assert result.contract is not None
    assert "binding_ref" not in result.contract.model_dump(mode="json")
    assert result.contract.scope.operation == operation.value
    assert result.contract.scope.required_capability == (
        _CAPABILITY_BY_OPERATION[operation].value
    )
    assert result.contract.scope.amount_minor_units == 1250
    assert result.contract.scope.spend_limit_minor_units == 1500
    assert result.contract.scope.raw_payment_data_allowed is False
    assert result.contract.separate_financial_execution_required is True
    assert result.contract.monetary_execution_budget_revalidation_required is True
    assert result.contract.payment_handle_resolved is False
    assert result.contract.checkout_opened is False
    assert result.contract.purchase_performed is False
    assert result.contract.booking_performed is False
    assert result.contract.payment_performed is False
    assert result.contract.financial_transaction_performed is False
    assert result.contract.network_call_performed is False
    assert result.contract.external_mutation_performed is False
    assert result.contract.real_external_target is False


def test_exported_financial_contract_cannot_be_rebound_to_another_binding(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.purchase,
        suffix="contract-binding",
    )
    service, _ = _service(tmp_path, request=request, registry=registry)
    result = service.prepare(_exact(request, recipe))
    assert result.contract is not None
    payload = result.contract.model_dump(mode="json")
    payload["binding_ref"] = _ref("binding", "rebound")

    with pytest.raises(ValueError):
        type(result.contract).model_validate(payload)


def test_operation_specific_financial_scope_is_fail_closed() -> None:
    request, recipe, _ = _financial_context(
        operation=GovernedFinancialOperation.booking,
        suffix="booking-scope",
    )
    del request
    payload = recipe.scope.model_dump(mode="json")
    payload["booking_ref"] = None
    with pytest.raises(ValueError, match="OPERATION_SCOPE_MISMATCH"):
        type(recipe.scope).model_validate(payload)

    checkout_payload = recipe.scope.model_dump(mode="json")
    checkout_payload["operation"] = GovernedFinancialOperation.checkout_payment
    checkout_payload["required_capability"] = AuthorityCapability.purchase
    with pytest.raises(ValueError, match="OPERATION_SCOPE_MISMATCH"):
        type(recipe.scope).model_validate(checkout_payload)


def test_amount_must_fit_exact_positive_spend_ceiling() -> None:
    with pytest.raises(ValueError, match="AMOUNT_OUTSIDE_EXACT_BUDGET"):
        _financial_context(
            operation=GovernedFinancialOperation.purchase,
            suffix="over-budget",
            amount_minor_units=1501,
            spend_limit_minor_units=1500,
        )
    with pytest.raises(ValueError):
        _financial_context(
            operation=GovernedFinancialOperation.purchase,
            suffix="boolean-budget",
            amount_minor_units=True,
            spend_limit_minor_units=1500,
        )


def test_wrong_capability_real_target_and_absent_human_are_denied() -> None:
    with pytest.raises(ValueError, match="EXACT_CAPABILITY_MISMATCH"):
        _financial_context(
            operation=GovernedFinancialOperation.purchase,
            suffix="wrong-capability",
            capability=AuthorityCapability.purchase_under_budget,
        )
    with pytest.raises(ValueError, match="REAL_TARGETS_INACTIVE"):
        _financial_context(
            operation=GovernedFinancialOperation.checkout_payment,
            suffix="real-target",
            target_kind=ExternalActionTargetKind.external,
        )
    with pytest.raises(ValueError, match="HUMAN_PRESENCE_REQUIRED"):
        _financial_context(
            operation=GovernedFinancialOperation.booking,
            suffix="absent-human",
            human_present=False,
        )


def test_exact_target_schema_and_resource_binding_cannot_drift() -> None:
    request, recipe, _ = _financial_context(
        operation=GovernedFinancialOperation.purchase,
        suffix="binding-drift",
    )
    target_drift = _request(
        ExternalActionAuthorityBinding.model_validate(
            {
                **request.binding.model_dump(mode="json"),
                "recipient_ref": governed_financial_target_ref(
                    operation=GovernedFinancialOperation.purchase,
                    target_descriptor_ref=_ref(
                        "financial-target-descriptor",
                        "other",
                    ),
                ),
            }
        )
    )
    with pytest.raises(ValueError, match="TARGET_NOT_AUTHORITY_BOUND"):
        build_governed_financial_recipe(
            target_drift,
            scope=recipe.scope,
            created_at=recipe.created_at,
            expires_at=recipe.expires_at,
        )

    schema_drift = _request(
        ExternalActionAuthorityBinding.model_validate(
            {
                **request.binding.model_dump(mode="json"),
                "field_schema_ref": _pinned(
                    "financial-schema-ref:governed-browser",
                    suffix="other",
                ),
            }
        )
    )
    with pytest.raises(ValueError, match="SCHEMA_NOT_AUTHORITY_BOUND"):
        build_governed_financial_recipe(
            schema_drift,
            scope=recipe.scope,
            created_at=recipe.created_at,
            expires_at=recipe.expires_at,
        )

    extra_resource = _request(
        ExternalActionAuthorityBinding.model_validate(
            {
                **request.binding.model_dump(mode="json"),
                "resource_refs": [
                    *request.binding.resource_refs,
                    _pinned(
                        "financial-quote-ref:governed-browser",
                        suffix="unrelated",
                    ),
                ],
            }
        )
    )
    with pytest.raises(ValueError, match="RESOURCE_NOT_EXACTLY_BOUND"):
        build_governed_financial_recipe(
            extra_resource,
            scope=recipe.scope,
            created_at=recipe.created_at,
            expires_at=recipe.expires_at,
        )


def test_unknown_recipe_and_exact_request_drift_are_preflight_blocked(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.purchase,
        suffix="request-drift",
    )
    service, _ = _service(tmp_path, request=request, registry=registry)
    exact = _exact(request, recipe)
    unknown = exact.model_copy(
        update={
            "recipe_ref": _pinned(
                "financial-recipe-ref:governed-browser",
                suffix="unknown",
            )
        }
    )
    drifted = exact.model_copy(
        update={
            "financial_input_ref": _pinned(
                "financial-input-ref:governed-browser",
                suffix="drifted",
            )
        }
    )

    unknown_result = service.prepare(unknown)
    drifted_result = service.prepare(drifted)

    assert unknown_result.receipt.status == "preflight_blocked"
    assert unknown_result.contract is None
    assert drifted_result.receipt.status == "preflight_blocked"
    assert drifted_result.contract is None


def test_approval_identifier_alone_grants_no_financial_contract(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.checkout_payment,
        suffix="approval-only",
    )
    service, _ = _service(tmp_path, request=request, registry=registry)
    ungranted = request.model_copy(
        update={"approval_ref": "approval-ref:governed-financial:identifier-only"}
    )

    result = service.prepare(_exact(ungranted, recipe))

    assert result.receipt.status == "transaction_blocked"
    assert result.contract is None
    assert result.receipt.approval_validation_ref
    assert result.receipt.financial_effect_performed is False


def test_exact_approval_without_matching_lease_grants_no_financial_contract(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.financial_transaction,
        suffix="missing-lease",
    )
    authority = LocalApprovalAuthority()
    approval_request = authority.create_request(
        build_external_action_approval_request(request)
    )
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref=request.approval_ref,
    )
    budget_store = AuthorityBudgetStore(tmp_path / "authority")
    kernel = GovernedExternalActionKernel(
        store=ExternalActionTransactionStore(tmp_path / "transactions.sqlite3"),
        approval_authority=authority,
        authority_leases_provider=lambda: [],
        readiness_provider=lambda item: _readiness(item),
        budget_gate=AuthorityBudgetStoreGate(budget_store, authority),
        local_validation_enabled=True,
    )
    service = ExactGovernedFinancialService(registry=registry, kernel=kernel)

    result = service.prepare(_exact(request, recipe))

    assert result.receipt.status == "transaction_blocked"
    assert result.contract is None
    assert result.receipt.financial_effect_performed is False


@pytest.mark.parametrize(
    ("safe_disable", "kill_switch"),
    [(True, False), (False, True)],
)
def test_safe_disable_and_kill_switch_deny_financial_preparation_and_replay(
    tmp_path: Path,
    safe_disable: bool,
    kill_switch: bool,
) -> None:
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.purchase,
        suffix=f"disabled-{safe_disable}-{kill_switch}",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
        readiness_provider=lambda item: _readiness(
            item,
            safe_disable=safe_disable,
            kill_switch=kill_switch,
        ),
    )
    exact = _exact(request, recipe)

    first = service.prepare(exact)
    replay = service.prepare(exact)

    assert first.receipt.status == "transaction_blocked"
    assert first.receipt.budget_reservation_ref is not None
    assert first.receipt.budget_release_ref is not None
    assert first.receipt.budget_settlement_ref is None
    assert first.contract is None
    assert replay.receipt.status == "transaction_blocked"
    assert replay.receipt.budget_release_ref == first.receipt.budget_release_ref
    assert replay.receipt.replayed is True
    assert replay.contract is None


def test_success_replay_and_idempotency_drift_are_content_free(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.booking,
        suffix="replay",
    )
    service, _ = _service(tmp_path, request=request, registry=registry)
    exact = _exact(request, recipe)

    first = service.prepare(exact)
    replay = service.prepare(exact)
    drifted = service.prepare(
        _exact(
            request.model_copy(
                update={
                    "idempotency_ref": stable_governed_browser_ref(
                        "idempotency-ref:governed-financial-contract:drifted",
                        {"source_idempotency_ref": request.idempotency_ref},
                    )
                }
            ),
            recipe,
        )
    )

    assert first.receipt.status == "contract_ready"
    assert first.contract is not None
    assert replay.receipt.status == "replayed_content_free"
    assert replay.receipt.replayed is True
    assert replay.contract is None
    assert drifted.receipt.status == "preflight_blocked"
    assert drifted.receipt.reason_refs == [
        "reason-ref:governed-financial:idempotency-conflict"
    ]
    assert drifted.contract is None


def test_financial_replay_requires_exact_durable_provenance(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.booking,
        suffix="durable-replay-provenance",
    )
    service, _ = _service(tmp_path, request=request, registry=registry)
    exact = _exact(request, recipe)
    service.prepare(exact)
    replay = service.prepare(exact)
    kernel_execution = financial_operation_module._kernel_execution(
        exact.execution_request,
        recipe_ref=recipe.recipe_ref,
    )
    replay_receipt = service._kernel.replay_if_terminal(kernel_execution)
    assert replay_receipt is not None
    context = financial_operation_module._financial_replay_validation_context(
        kernel=service._kernel,
        expected_execution=kernel_execution,
        recipe=recipe,
        replay_receipt=replay_receipt,
    )
    payload = replay.receipt.model_dump(mode="json")
    GovernedFinancialReceipt.model_validate(
        payload,
        context=replay_validation_context(context),
    )
    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_REQUIRED",
    ):
        GovernedFinancialReceipt.model_validate(payload)

    payload["budget_settlement_ref"] = _pinned(
        "receipt-ref:authority-budget",
        suffix="forged-replay-settlement",
    )
    payload["external_action_receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-action",
        {
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
        },
    )
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-financial-contract",
        governed_receipt_identity_payload(
            GovernedFinancialReceipt.model_construct(**payload)
        ),
    )
    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH",
    ):
        GovernedFinancialReceipt.model_validate(
            payload,
            context=replay_validation_context(context),
        )


@pytest.mark.parametrize(
    "terminal_state",
    (
        ExternalActionState.blocked,
        ExternalActionState.failed,
        ExternalActionState.outcome_ambiguous,
    ),
)
def test_financial_terminal_replay_reconstructs_exact_operation_evidence(
    tmp_path: Path,
    terminal_state: ExternalActionState,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload, context, expected_evidence = _financial_terminal_replay_proof(
        tmp_path,
        terminal_state=terminal_state,
        monkeypatch=monkeypatch,
    )

    reconstructed = GovernedFinancialReceipt.model_validate(
        payload,
        context=replay_validation_context(context),
    )

    assert reconstructed.replayed is True
    assert reconstructed.external_action_state == terminal_state.value
    assert reconstructed.evidence_refs == expected_evidence


@pytest.mark.parametrize(
    "terminal_state",
    (
        ExternalActionState.blocked,
        ExternalActionState.failed,
        ExternalActionState.outcome_ambiguous,
    ),
)
def test_financial_terminal_replay_rejects_arbitrary_non_success_evidence(
    tmp_path: Path,
    terminal_state: ExternalActionState,
) -> None:
    service, exact = _seed_arbitrary_financial_terminal_evidence(
        tmp_path,
        terminal_state=terminal_state,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_FINANCIAL_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
    ):
        service.prepare(exact)


@pytest.mark.parametrize(
    ("evidence_index", "receipt_field", "replacement_prefix"),
    (
        (
            0,
            "contract_ref",
            "financial-contract-ref:governed-browser",
        ),
        (
            1,
            "authority_ref",
            "financial-operation-authority-ref:governed-browser",
        ),
        (
            2,
            "financial_input_ref",
            "financial-input-ref:governed-browser",
        ),
        (
            3,
            "quote_ref",
            "financial-quote-ref:governed-browser",
        ),
        (
            4,
            "payment_handle_ref",
            "payment-handle-ref:governed-browser",
        ),
        (
            5,
            "rollback_ref",
            "financial-rollback-ref:governed-browser",
        ),
        (
            6,
            "reconciliation_ref",
            "financial-reconciliation-ref:governed-browser",
        ),
    ),
)
def test_financial_replay_rejects_every_rehashed_evidence_field_tamper(
    tmp_path: Path,
    evidence_index: int,
    receipt_field: str,
    replacement_prefix: str,
) -> None:
    payload, context = _financial_replay_proof(
        tmp_path,
        operation=GovernedFinancialOperation.purchase,
        suffix=f"replay-field-{evidence_index}",
    )
    replacement = _pinned(
        replacement_prefix,
        suffix=f"replay-field-{evidence_index}-replacement",
    )
    evidence_refs = list(payload["evidence_refs"])
    evidence_refs[evidence_index] = replacement
    payload["evidence_refs"] = evidence_refs
    payload[receipt_field] = replacement
    _rehash_external_and_financial_receipt(payload)

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH",
    ):
        GovernedFinancialReceipt.model_validate(
            payload,
            context=replay_validation_context(context),
        )


@pytest.mark.parametrize(
    "mutation",
    ("reverse", "drop", "append", "duplicate"),
)
def test_financial_replay_rejects_rehashed_evidence_order_and_arity_tamper(
    tmp_path: Path,
    mutation: str,
) -> None:
    payload, context = _financial_replay_proof(
        tmp_path,
        operation=GovernedFinancialOperation.purchase,
        suffix=f"replay-shape-{mutation}",
    )
    evidence_refs = list(payload["evidence_refs"])
    if mutation == "reverse":
        evidence_refs.reverse()
    elif mutation == "drop":
        evidence_refs.pop()
    elif mutation == "append":
        evidence_refs.append(
            _pinned(
                "financial-reconciliation-ref:governed-browser",
                suffix="replay-shape-appended",
            )
        )
    else:
        evidence_refs.append(evidence_refs[-1])
    payload["evidence_refs"] = evidence_refs
    _rehash_external_and_financial_receipt(payload)

    with pytest.raises(
        ValueError,
        match=(
            "GOVERNED_FINANCIAL_SUCCESS_EVIDENCE_MISMATCH"
            "|GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH"
        ),
    ):
        GovernedFinancialReceipt.model_validate(
            payload,
            context=replay_validation_context(context),
        )


def test_financial_replay_rejects_cross_operation_substitution(
    tmp_path: Path,
) -> None:
    _, purchase_context = _financial_replay_proof(
        tmp_path,
        operation=GovernedFinancialOperation.purchase,
        suffix="cross-operation-purchase",
    )
    booking_payload, _ = _financial_replay_proof(
        tmp_path,
        operation=GovernedFinancialOperation.booking,
        suffix="cross-operation-booking",
    )
    _rehash_external_and_financial_receipt(booking_payload)

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_LANE_MISMATCH",
    ):
        GovernedFinancialReceipt.model_validate(
            booking_payload,
            context=replay_validation_context(purchase_context),
        )


def test_financial_replay_rejects_cross_transaction_substitution(
    tmp_path: Path,
) -> None:
    payload, context = _financial_replay_proof(
        tmp_path,
        operation=GovernedFinancialOperation.purchase,
        suffix="cross-transaction-a",
    )
    foreign_payload, _ = _financial_replay_proof(
        tmp_path,
        operation=GovernedFinancialOperation.purchase,
        suffix="cross-transaction-b",
    )
    for field in (
        "transaction_ref",
        "intent_ref",
        "binding_ref",
        "approval_validation_ref",
        "authority_decision_ref",
        "budget_reservation_ref",
        "budget_release_ref",
        "budget_settlement_ref",
    ):
        payload[field] = foreign_payload[field]
    _rehash_external_and_financial_receipt(payload)

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH",
    ):
        GovernedFinancialReceipt.model_validate(
            payload,
            context=replay_validation_context(context),
        )


def test_success_receipt_requires_complete_exact_evidence(tmp_path: Path) -> None:
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.purchase,
        suffix="receipt-proof",
    )
    service, _ = _service(tmp_path, request=request, registry=registry)
    receipt = service.prepare(_exact(request, recipe)).receipt
    payload = receipt.model_dump(mode="json")
    payload["approval_validation_ref"] = None
    with pytest.raises(ValueError, match="SUCCESS_KERNEL_PROOF_REQUIRED"):
        GovernedFinancialReceipt.model_validate(payload)

    payload = receipt.model_dump(mode="json")
    payload["evidence_refs"][-1] = _pinned(
        "financial-reconciliation-ref:governed-browser",
        suffix="tampered",
    )
    with pytest.raises(ValueError, match="SUCCESS_EVIDENCE_MISMATCH"):
        GovernedFinancialReceipt.model_validate(payload)

    payload = receipt.model_dump(mode="json")
    payload["authority_ref"] = "financial-operation-authority-ref:governed-browser:raw"
    payload["evidence_refs"][1] = payload["authority_ref"]
    with pytest.raises(ValueError, match="HASH_PIN_REQUIRED"):
        GovernedFinancialReceipt.model_validate(payload)

    payload = receipt.model_dump(mode="json")
    payload["status"] = "failed"
    with pytest.raises(ValueError, match="RECEIPT_STATE_MISMATCH"):
        GovernedFinancialReceipt.model_validate(payload)


def test_financial_receipt_rejects_budget_proof_without_kernel_receipt(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.purchase,
        suffix="orphaned-release-proof",
    )
    service, _ = _service(tmp_path, request=request, registry=registry)
    payload = service.prepare(_exact(request, recipe)).receipt.model_dump(mode="json")
    payload.update(
        {
            "status": "preflight_blocked",
            "external_action_state": "blocked",
            "external_action_receipt_ref": None,
            "approval_validation_ref": None,
            "authority_decision_ref": None,
            "budget_reservation_ref": None,
            "budget_release_ref": _pinned(
                "receipt-ref:authority-budget",
                suffix="orphaned-release-proof",
            ),
            "budget_settlement_ref": None,
            "evidence_refs": [],
        }
    )
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-financial-contract",
        governed_receipt_identity_payload(
            GovernedFinancialReceipt.model_construct(**payload)
        ),
    )
    with pytest.raises(
        ValueError,
        match="GOVERNED_FINANCIAL_EXTERNAL_PROOF_CONTEXT_INVALID",
    ):
        GovernedFinancialReceipt.model_validate(payload)


def test_financial_non_preflight_receipt_requires_kernel_context(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.purchase,
        suffix="kernel-context-required",
    )
    service, _ = _service(tmp_path, request=request, registry=registry)
    payload = service.prepare(_exact(request, recipe)).receipt.model_dump(mode="json")
    payload.update(
        {
            "status": "failed",
            "external_action_state": "failed",
            "external_action_receipt_ref": None,
            "approval_validation_ref": None,
            "authority_decision_ref": None,
            "budget_reservation_ref": None,
            "budget_release_ref": None,
            "budget_settlement_ref": None,
            "evidence_refs": [],
            "reason_refs": [
                "reason-ref:governed-financial:contract-preparation-failed"
            ],
            "replayed": False,
        }
    )
    identity_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"receipt_ref", "budget_release_ref"}
    }
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-financial-contract",
        identity_payload,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_FINANCIAL_EXTERNAL_PROOF_CONTEXT_REQUIRED",
    ):
        GovernedFinancialReceipt.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "rebound_ref"),
    (
        (
            "transaction_ref",
            _pinned(
                "transaction-ref:governed-external-action",
                suffix="rebound-financial-transaction",
            ),
        ),
        (
            "budget_settlement_ref",
            _pinned(
                "receipt-ref:authority-budget",
                suffix="rebound-financial-settlement",
            ),
        ),
    ),
)
def test_financial_receipt_rejects_rebound_kernel_receipt_fields(
    tmp_path: Path,
    field: str,
    rebound_ref: str,
) -> None:
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.purchase,
        suffix=f"kernel-receipt-binding-{field}",
    )
    service, _ = _service(tmp_path, request=request, registry=registry)
    payload = service.prepare(_exact(request, recipe)).receipt.model_dump(mode="json")
    payload[field] = rebound_ref
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-financial-contract",
        governed_receipt_identity_payload(
            GovernedFinancialReceipt.model_construct(**payload)
        ),
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_FINANCIAL_EXTERNAL_RECEIPT_REF_MISMATCH",
    ):
        GovernedFinancialReceipt.model_validate(payload)


def test_financial_receipt_rejects_conflicting_rehashed_kernel_proofs(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.purchase,
        suffix="conflicting-rehashed-kernel-proofs",
    )
    service, _ = _service(tmp_path, request=request, registry=registry)
    payload = service.prepare(_exact(request, recipe)).receipt.model_dump(mode="json")
    payload["budget_release_ref"] = _pinned(
        "receipt-ref:authority-budget",
        suffix="conflicting-rehashed-kernel-proofs",
    )
    payload["external_action_receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-action",
        {
            "transaction_ref": payload["transaction_ref"],
            "intent_ref": payload["intent_ref"],
            "binding_ref": payload["binding_ref"],
            "state": payload["external_action_state"],
            "approval_validation_ref": payload["approval_validation_ref"],
            "authority_decision_ref": payload["authority_decision_ref"],
            "budget_reservation_ref": payload["budget_reservation_ref"],
            "budget_release_ref": payload["budget_release_ref"],
            "budget_settlement_ref": payload["budget_settlement_ref"],
            "evidence_refs": payload["evidence_refs"],
            "reason_refs": payload["reason_refs"],
        },
    )
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-financial-contract",
        governed_receipt_identity_payload(
            GovernedFinancialReceipt.model_construct(**payload)
        ),
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_FINANCIAL_EXTERNAL_RECEIPT_REF_MISMATCH",
    ):
        GovernedFinancialReceipt.model_validate(payload)


def test_expired_recipe_is_preflight_denial_but_prior_start_is_ambiguous(
    tmp_path: Path,
) -> None:
    now = utc_now()
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.financial_transaction,
        suffix="expired",
        created_at=now - timedelta(minutes=2),
        expires_at=now - timedelta(minutes=1),
    )
    first_service, _ = _service(
        tmp_path / "new",
        request=request,
        registry=registry,
        clock=lambda: now,
    )
    expired = first_service.prepare(_exact(request, recipe))
    assert expired.receipt.status == "preflight_blocked"
    assert expired.receipt.reason_refs == [
        "reason-ref:governed-financial:recipe-expired"
    ]

    recovery_path = tmp_path / "recovery"
    recovery_service, _ = _service(
        recovery_path,
        request=request,
        registry=registry,
        clock=lambda: now,
    )
    kernel_request = request.model_copy(
        update={
            "idempotency_ref": stable_governed_browser_ref(
                "idempotency-ref:governed-financial-contract",
                {
                    "source_idempotency_ref": request.idempotency_ref,
                    "recipe_ref": recipe.recipe_ref,
                },
            )
        }
    )
    store = ExternalActionTransactionStore(recovery_path / "transactions.sqlite3")
    store.prepare(kernel_request)
    assert store.claim_start(kernel_request) is True
    with sqlite3.connect(recovery_path / "transactions.sqlite3") as connection:
        connection.execute(
            "UPDATE governed_external_actions SET updated_at = ? "
            "WHERE transaction_ref = ?",
            (
                (utc_now() - timedelta(minutes=2)).isoformat(),
                kernel_request.binding.transaction_ref,
            ),
        )
    recovered = recovery_service.prepare(_exact(request, recipe))

    assert recovered.receipt.status == "outcome_ambiguous"
    assert recovered.receipt.reason_refs == [
        "reason-ref:governed-external-action:prior-start-unsettled",
        "reason-ref:governed-external-action:budget-reservation-proof-missing",
    ]
    assert recovered.contract is None


def test_group10_verifier_passes() -> None:
    assert verify() == []
