from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path

import pytest

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
