from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

import ultimate_ai_agent.core.governed_browser.external_operation_contracts as external_operation_module
from scripts.verify_governed_browser_queue01_group09 import verify
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
    ExactGovernedExternalOperationRequest,
    ExactGovernedExternalOperationService,
    ExternalActionAuthorityBinding,
    ExternalActionTargetKind,
    ExternalActionState,
    ExternalActionTransactionStore,
    GovernedExternalOperation,
    GovernedExternalActionKernel,
    GovernedExternalOperationReceipt,
    GovernedExternalOperationRecipeRegistry,
    GovernedExternalOperationReversibility,
    GovernedLegalConsentDecision,
    build_external_action_approval_request,
    build_governed_external_operation_recipe,
    governed_external_operation_authority_ref,
    governed_external_operation_contract_ref,
    governed_external_operation_input_ref,
    governed_external_operation_schema_ref,
    governed_external_operation_target_ref,
    stable_governed_browser_ref,
)
from ultimate_ai_agent.core.governed_browser.replay_provenance import (
    ExternalActionReplayValidationContext,
    replay_validation_context,
)
from ultimate_ai_agent.core.time import utc_now


_CAPABILITY_BY_OPERATION = {
    GovernedExternalOperation.send_communication: AuthorityCapability.send,
    GovernedExternalOperation.publish_artifact: AuthorityCapability.send,
    GovernedExternalOperation.create_account: AuthorityCapability.write,
    GovernedExternalOperation.record_legal_consent: AuthorityCapability.mutate,
    GovernedExternalOperation.delete_resource: AuthorityCapability.destructive,
}

_REVERSIBILITY_BY_OPERATION = {
    GovernedExternalOperation.send_communication: (
        GovernedExternalOperationReversibility.irreversible
    ),
    GovernedExternalOperation.publish_artifact: (
        GovernedExternalOperationReversibility.manual_recovery
    ),
    GovernedExternalOperation.create_account: (
        GovernedExternalOperationReversibility.manual_recovery
    ),
    GovernedExternalOperation.record_legal_consent: (
        GovernedExternalOperationReversibility.manual_recovery
    ),
    GovernedExternalOperation.delete_resource: (
        GovernedExternalOperationReversibility.irreversible
    ),
}


def _raising_clock() -> datetime:
    raise RuntimeError("unavailable")


def _pinned(prefix: str, *, suffix: str) -> str:
    return stable_governed_browser_ref(prefix, {"suffix": suffix})


def _operation_context(
    *,
    operation: GovernedExternalOperation,
    suffix: str,
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
    target_ref = governed_external_operation_target_ref(
        operation=operation,
        target_descriptor_ref=(
            target_descriptor_ref or _ref("target-descriptor", suffix)
        ),
    )
    artifact_refs = [
        _pinned(
            "external-operation-artifact-ref:governed-browser",
            suffix=suffix,
        )
    ]
    operation_input_ref = governed_external_operation_input_ref(
        operation=operation,
        target_ref=target_ref,
        artifact_refs=artifact_refs,
    )
    legal_instrument_ref = (
        _pinned("legal-instrument-ref:governed-browser", suffix=suffix)
        if operation == GovernedExternalOperation.record_legal_consent
        else None
    )
    legal_decision = (
        GovernedLegalConsentDecision.accept
        if operation == GovernedExternalOperation.record_legal_consent
        else None
    )
    delete_resource_ref = (
        target_ref if operation == GovernedExternalOperation.delete_resource else None
    )
    reversibility = _REVERSIBILITY_BY_OPERATION[operation]
    rollback_ref = _pinned(
        "external-operation-rollback-ref:governed-browser",
        suffix=suffix,
    )
    reconciliation_ref = _pinned(
        "external-operation-reconciliation-ref:governed-browser",
        suffix=suffix,
    )
    schema_ref = governed_external_operation_schema_ref(
        operation=operation,
        target_ref=target_ref,
        operation_input_ref=operation_input_ref,
        artifact_refs=artifact_refs,
        legal_instrument_ref=legal_instrument_ref,
        legal_decision=legal_decision,
        delete_resource_ref=delete_resource_ref,
        reversibility=reversibility,
        rollback_ref=rollback_ref,
        reconciliation_ref=reconciliation_ref,
    )
    operation_authority_ref = governed_external_operation_authority_ref(
        operation=operation,
        origin_ref=base.origin_ref,
        target_ref=target_ref,
        schema_ref=schema_ref,
    )
    contract_ref = governed_external_operation_contract_ref(
        operation=operation,
        origin_ref=base.origin_ref,
        page_snapshot_ref=base.page_snapshot_ref,
        target_ref=target_ref,
        operation_input_ref=operation_input_ref,
        schema_ref=schema_ref,
        operation_authority_ref=operation_authority_ref,
        artifact_refs=artifact_refs,
        legal_instrument_ref=legal_instrument_ref,
        legal_decision=legal_decision,
        delete_resource_ref=delete_resource_ref,
        reversibility=reversibility,
        rollback_ref=rollback_ref,
        reconciliation_ref=reconciliation_ref,
        expires_at=exact_expires_at,
    )
    resources = [
        operation_authority_ref,
        operation_input_ref,
        rollback_ref,
        reconciliation_ref,
        contract_ref,
    ]
    if legal_instrument_ref is not None:
        resources.append(legal_instrument_ref)
    if delete_resource_ref is not None:
        resources.append(delete_resource_ref)
    binding = ExternalActionAuthorityBinding.model_validate(
        {
            **base.model_dump(mode="json"),
            "authority_capability": (capability or _CAPABILITY_BY_OPERATION[operation]),
            "recipient_ref": target_ref,
            "field_schema_ref": schema_ref,
            "artifact_refs": artifact_refs,
            "resource_refs": resources,
        }
    )
    request = _request(binding)
    recipe = build_governed_external_operation_recipe(
        request,
        operation=operation,
        target_ref=target_ref,
        operation_input_ref=operation_input_ref,
        legal_instrument_ref=legal_instrument_ref,
        legal_decision=legal_decision,
        delete_resource_ref=delete_resource_ref,
        reversibility=reversibility,
        rollback_ref=rollback_ref,
        reconciliation_ref=reconciliation_ref,
        created_at=exact_created_at,
        expires_at=exact_expires_at,
    )
    registry = GovernedExternalOperationRecipeRegistry([recipe])
    return request, recipe, registry


def _exact(request, recipe) -> ExactGovernedExternalOperationRequest:  # type: ignore[no-untyped-def]
    return ExactGovernedExternalOperationRequest(
        execution_request=request,
        recipe_ref=recipe.recipe_ref,
        contract_ref=recipe.contract_ref,
        operation=recipe.operation,
        target_ref=recipe.target_ref,
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
        ExactGovernedExternalOperationService(
            registry=registry,
            kernel=kernel,
            clock=clock,
        ),
        authority,
    )


def _rehash_external_operation_replay(
    payload: dict[str, Any],
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
        "reason_refs": payload["external_action_reason_refs"],
    }
    if payload["budget_release_ref"] is not None:
        external_payload["budget_release_ref"] = payload["budget_release_ref"]
    payload["external_action_receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-action",
        external_payload,
    )
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-operation",
        external_operation_module._external_operation_receipt_identity_payload(
            GovernedExternalOperationReceipt.model_construct(
                **{
                    **payload,
                    "external_action_reason_refs": tuple(
                        payload["external_action_reason_refs"]
                    ),
                }
            )
        ),
    )
    return payload


def _external_operation_replay_proof(
    tmp_path: Path,
    *,
    operation: GovernedExternalOperation,
    suffix: str,
) -> tuple[
    dict[str, Any],
    ExternalActionReplayValidationContext,
]:
    request, recipe, registry = _operation_context(
        operation=operation,
        suffix=suffix,
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    exact = _exact(request, recipe)
    service.prepare(exact)
    replay_result = service.prepare(exact)
    kernel_execution = external_operation_module._operation_kernel_execution(
        exact.execution_request,
        recipe_ref=recipe.recipe_ref,
    )
    replay_receipt = service._kernel.replay_if_terminal(kernel_execution)
    assert replay_receipt is not None
    context = (
        external_operation_module._external_operation_replay_validation_context(
            kernel=service._kernel,
            expected_execution=kernel_execution,
            recipe=recipe,
            replay_receipt=replay_receipt,
        )
    )
    return replay_result.receipt.model_dump(mode="json"), context


def _external_operation_terminal_replay_proof(
    tmp_path: Path,
    *,
    terminal_state: ExternalActionState,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    dict[str, Any],
    ExternalActionReplayValidationContext,
    list[str],
]:
    suffix = f"terminal-replay-{terminal_state.value}"
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.send_communication,
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
    kernel_execution = external_operation_module._operation_kernel_execution(
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
    context = external_operation_module._external_operation_replay_validation_context(
        kernel=service._kernel,
        expected_execution=kernel_execution,
        recipe=recipe,
        replay_receipt=terminal_receipt,
    )
    expected_evidence = {
        ExternalActionState.blocked: [],
        ExternalActionState.failed: [
            stable_governed_browser_ref(
                (
                    "evidence-ref:governed-external-operation:"
                    "trusted-clock-invalid"
                ),
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


def _seed_arbitrary_external_operation_terminal_evidence(
    tmp_path: Path,
    *,
    terminal_state: ExternalActionState,
) -> tuple[
    ExactGovernedExternalOperationService,
    ExactGovernedExternalOperationRequest,
]:
    suffix = f"arbitrary-terminal-evidence-{terminal_state.value}"
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.send_communication,
        suffix=suffix,
    )
    service, _ = _service(
        tmp_path / suffix,
        request=request,
        registry=registry,
    )
    exact = _exact(request, recipe)
    kernel_execution = external_operation_module._operation_kernel_execution(
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
        "evidence-ref:governed-external-operation:arbitrary-non-success",
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


@pytest.mark.parametrize("operation", list(GovernedExternalOperation))
def test_registered_operations_prepare_exact_inactive_contracts(
    tmp_path: Path,
    operation: GovernedExternalOperation,
) -> None:
    request, recipe, registry = _operation_context(
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
    assert result.receipt.content_free is True
    assert result.receipt.approval_validation_ref
    assert result.receipt.authority_decision_ref
    assert result.receipt.budget_reservation_ref
    assert result.receipt.budget_settlement_ref
    assert result.receipt.evidence_refs == [
        recipe.contract_ref,
        recipe.operation_authority_ref,
        recipe.operation_input_ref,
        recipe.rollback_ref,
        recipe.reconciliation_ref,
    ]
    assert result.contract is not None
    assert result.contract.operation == operation.value
    assert result.contract.required_capability == _CAPABILITY_BY_OPERATION[operation]
    assert result.contract.contract_prepared is True
    assert result.contract.separate_exact_execution_required is True
    assert result.contract.payload_materialized is False
    assert result.contract.browser_opened is False
    assert result.contract.network_call_performed is False
    assert result.contract.communication_sent is False
    assert result.contract.artifact_published is False
    assert result.contract.account_created is False
    assert result.contract.legal_consent_recorded is False
    assert result.contract.resource_deleted is False
    assert result.contract.external_mutation_performed is False
    assert result.contract.real_external_target is False


def test_legal_consent_is_explicit_and_account_creation_cannot_imply_it(
    tmp_path: Path,
) -> None:
    legal_request, legal_recipe, legal_registry = _operation_context(
        operation=GovernedExternalOperation.record_legal_consent,
        suffix="legal-explicit",
    )
    legal_service, _ = _service(
        tmp_path / "legal",
        request=legal_request,
        registry=legal_registry,
    )
    legal = legal_service.prepare(_exact(legal_request, legal_recipe))
    assert legal.contract is not None
    assert legal.contract.legal_instrument_ref
    assert legal.contract.legal_decision == "accept"
    assert legal.contract.legal_consent_recorded is False

    account_request, account_recipe, account_registry = _operation_context(
        operation=GovernedExternalOperation.create_account,
        suffix="account-no-consent",
    )
    account_service, _ = _service(
        tmp_path / "account",
        request=account_request,
        registry=account_registry,
    )
    account = account_service.prepare(_exact(account_request, account_recipe))
    assert account.contract is not None
    assert account.contract.legal_instrument_ref is None
    assert account.contract.legal_decision is None
    assert account.contract.account_created is False
    assert account.contract.legal_consent_recorded is False


def test_legal_and_delete_operation_specific_scope_is_fail_closed() -> None:
    operation = GovernedExternalOperation.record_legal_consent
    target_ref = governed_external_operation_target_ref(
        operation=operation,
        target_descriptor_ref=_ref("target-descriptor", "legal-missing"),
    )
    artifacts = [
        _pinned(
            "external-operation-artifact-ref:governed-browser",
            suffix="legal-missing",
        )
    ]
    input_ref = governed_external_operation_input_ref(
        operation=operation,
        target_ref=target_ref,
        artifact_refs=artifacts,
    )
    rollback_ref = _pinned(
        "external-operation-rollback-ref:governed-browser",
        suffix="legal-missing",
    )
    reconciliation_ref = _pinned(
        "external-operation-reconciliation-ref:governed-browser",
        suffix="legal-missing",
    )
    with pytest.raises(ValueError, match="LEGAL_SCOPE_MISMATCH"):
        governed_external_operation_schema_ref(
            operation=operation,
            target_ref=target_ref,
            operation_input_ref=input_ref,
            artifact_refs=artifacts,
            legal_instrument_ref=None,
            legal_decision=None,
            delete_resource_ref=None,
            reversibility=GovernedExternalOperationReversibility.manual_recovery,
            rollback_ref=rollback_ref,
            reconciliation_ref=reconciliation_ref,
        )
    with pytest.raises(ValueError, match="INPUT_REF_MISMATCH"):
        governed_external_operation_schema_ref(
            operation=GovernedExternalOperation.send_communication,
            target_ref=governed_external_operation_target_ref(
                operation=GovernedExternalOperation.send_communication,
                target_descriptor_ref=_ref("target-descriptor", "wrong-input"),
            ),
            operation_input_ref=_pinned(
                "external-operation-input-ref:governed-browser",
                suffix="wrong-input",
            ),
            artifact_refs=artifacts,
            legal_instrument_ref=None,
            legal_decision=None,
            delete_resource_ref=None,
            reversibility=GovernedExternalOperationReversibility.irreversible,
            rollback_ref=rollback_ref,
            reconciliation_ref=reconciliation_ref,
        )
    account_target_ref = governed_external_operation_target_ref(
        operation=GovernedExternalOperation.create_account,
        target_descriptor_ref=_ref("target-descriptor", "unproven-reversible"),
    )
    with pytest.raises(ValueError, match="REVERSIBILITY_UNPROVEN"):
        governed_external_operation_schema_ref(
            operation=GovernedExternalOperation.create_account,
            target_ref=account_target_ref,
            operation_input_ref=governed_external_operation_input_ref(
                operation=GovernedExternalOperation.create_account,
                target_ref=account_target_ref,
                artifact_refs=artifacts,
            ),
            artifact_refs=artifacts,
            legal_instrument_ref=None,
            legal_decision=None,
            delete_resource_ref=None,
            reversibility=GovernedExternalOperationReversibility.reversible,
            rollback_ref=rollback_ref,
            reconciliation_ref=reconciliation_ref,
        )
    with pytest.raises(ValueError, match="DELETE_TARGET_MISMATCH"):
        governed_external_operation_schema_ref(
            operation=GovernedExternalOperation.delete_resource,
            target_ref=governed_external_operation_target_ref(
                operation=GovernedExternalOperation.delete_resource,
                target_descriptor_ref=_ref("target-descriptor", "delete-target"),
            ),
            operation_input_ref=governed_external_operation_input_ref(
                operation=GovernedExternalOperation.delete_resource,
                target_ref=governed_external_operation_target_ref(
                    operation=GovernedExternalOperation.delete_resource,
                    target_descriptor_ref=_ref(
                        "target-descriptor",
                        "delete-target",
                    ),
                ),
                artifact_refs=artifacts,
            ),
            artifact_refs=artifacts,
            legal_instrument_ref=None,
            legal_decision=None,
            delete_resource_ref=governed_external_operation_target_ref(
                operation=GovernedExternalOperation.delete_resource,
                target_descriptor_ref=_ref("target-descriptor", "wrong-delete"),
            ),
            reversibility=GovernedExternalOperationReversibility.irreversible,
            rollback_ref=rollback_ref,
            reconciliation_ref=reconciliation_ref,
        )


def test_unknown_recipe_and_request_scope_drift_are_preflight_blocked(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.publish_artifact,
        suffix="preflight-scope",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    unknown = service.prepare(
        ExactGovernedExternalOperationRequest(
            execution_request=request,
            recipe_ref=("external-operation-recipe-ref:governed-browser:unknown"),
            contract_ref=recipe.contract_ref,
            operation=recipe.operation,
            target_ref=recipe.target_ref,
        )
    )
    assert unknown.receipt.status == "preflight_blocked"
    assert unknown.contract is None

    drifted = service.prepare(
        ExactGovernedExternalOperationRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
            contract_ref=recipe.contract_ref,
            operation=GovernedExternalOperation.send_communication,
            target_ref=recipe.target_ref,
        )
    )
    assert drifted.receipt.status == "preflight_blocked"
    assert drifted.contract is None


def test_exact_target_schema_artifact_and_operation_authority_are_required(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.send_communication,
        suffix="exact-scope",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    binding_payload = request.binding.model_dump(mode="json")
    binding_payload["resource_refs"] = [
        *binding_payload["resource_refs"],
        _pinned(
            "external-operation-authority-ref:governed-browser",
            suffix="extra-authority",
        ),
    ]
    drifted_binding = ExternalActionAuthorityBinding.model_validate(binding_payload)
    drifted_request = _request(
        drifted_binding,
        approval_ref=request.approval_ref,
    )

    result = service.prepare(
        ExactGovernedExternalOperationRequest(
            execution_request=drifted_request,
            recipe_ref=recipe.recipe_ref,
            contract_ref=recipe.contract_ref,
            operation=recipe.operation,
            target_ref=recipe.target_ref,
        )
    )

    assert result.receipt.status == "preflight_blocked"
    assert result.contract is None


def test_wrong_capability_and_real_targets_cannot_build_recipes() -> None:
    with pytest.raises(ValueError, match="EXACT_CAPABILITY_MISMATCH"):
        _operation_context(
            operation=GovernedExternalOperation.create_account,
            suffix="wrong-capability",
            capability=AuthorityCapability.send,
        )
    with pytest.raises(ValueError, match="REAL_TARGETS_INACTIVE"):
        _operation_context(
            operation=GovernedExternalOperation.publish_artifact,
            suffix="real-target",
            target_kind=ExternalActionTargetKind.external,
        )


def test_approval_identifier_alone_grants_nothing(tmp_path: Path) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.create_account,
        suffix="approval-only",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    ungranted = request.model_copy(
        update={
            "approval_ref": ("approval-ref:governed-external-operation:identifier-only")
        }
    )

    result = service.prepare(
        ExactGovernedExternalOperationRequest(
            execution_request=ungranted,
            recipe_ref=recipe.recipe_ref,
            contract_ref=recipe.contract_ref,
            operation=recipe.operation,
            target_ref=recipe.target_ref,
        )
    )

    assert result.receipt.status == "transaction_blocked"
    assert result.contract is None
    assert result.receipt.approval_validation_ref


def test_exact_approval_without_matching_authority_lease_grants_nothing(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.create_account,
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
    service = ExactGovernedExternalOperationService(
        registry=registry,
        kernel=kernel,
    )

    result = service.prepare(_exact(request, recipe))

    assert result.receipt.status == "transaction_blocked"
    assert result.contract is None
    assert result.receipt.external_mutation_performed is False


@pytest.mark.parametrize(
    ("safe_disable", "kill_switch"), [(True, False), (False, True)]
)
def test_safe_disable_and_kill_switch_deny_contract_preparation_and_replay(
    tmp_path: Path,
    safe_disable: bool,
    kill_switch: bool,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.delete_resource,
        suffix=f"disable-{safe_disable}-{kill_switch}",
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
    assert first.contract is None
    assert replay.receipt.status == "transaction_blocked"
    assert replay.receipt.replayed is True
    assert replay.contract is None


def test_success_replay_is_content_free_and_at_most_once(tmp_path: Path) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.publish_artifact,
        suffix="replay",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    exact = _exact(request, recipe)

    first = service.prepare(exact)
    replay = service.prepare(exact)

    assert first.receipt.status == "contract_ready"
    assert first.contract is not None
    assert replay.receipt.status == "replayed_content_free"
    assert replay.receipt.replayed is True
    assert replay.contract is None


def test_external_operation_replay_requires_exact_durable_provenance(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.publish_artifact,
        suffix="durable-replay-provenance",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    exact = _exact(request, recipe)
    service.prepare(exact)
    replay = service.prepare(exact)
    kernel_execution = external_operation_module._operation_kernel_execution(
        exact.execution_request,
        recipe_ref=recipe.recipe_ref,
    )
    replay_receipt = service._kernel.replay_if_terminal(kernel_execution)
    assert replay_receipt is not None
    context = (
        external_operation_module._external_operation_replay_validation_context(
            kernel=service._kernel,
            expected_execution=kernel_execution,
            recipe=recipe,
            replay_receipt=replay_receipt,
        )
    )
    payload = replay.receipt.model_dump(mode="json")
    GovernedExternalOperationReceipt.model_validate(
        payload,
        context=replay_validation_context(context),
    )
    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_REQUIRED",
    ):
        GovernedExternalOperationReceipt.model_validate(payload)

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
            "reason_refs": payload["external_action_reason_refs"],
        },
    )
    payload["external_action_reason_refs"] = tuple(
        payload["external_action_reason_refs"]
    )
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-operation",
        external_operation_module._external_operation_receipt_identity_payload(
            GovernedExternalOperationReceipt.model_construct(**payload)
        ),
    )
    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH",
    ):
        GovernedExternalOperationReceipt.model_validate(
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
def test_external_operation_terminal_replay_reconstructs_exact_operation_evidence(
    tmp_path: Path,
    terminal_state: ExternalActionState,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload, context, expected_evidence = (
        _external_operation_terminal_replay_proof(
            tmp_path,
            terminal_state=terminal_state,
            monkeypatch=monkeypatch,
        )
    )

    reconstructed = GovernedExternalOperationReceipt.model_validate(
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
def test_external_operation_terminal_replay_rejects_arbitrary_non_success_evidence(
    tmp_path: Path,
    terminal_state: ExternalActionState,
) -> None:
    service, exact = _seed_arbitrary_external_operation_terminal_evidence(
        tmp_path,
        terminal_state=terminal_state,
    )

    with pytest.raises(
        ValueError,
        match=(
            "GOVERNED_EXTERNAL_OPERATION_REPLAY_EVIDENCE_ENVELOPE_MISMATCH"
        ),
    ):
        service.prepare(exact)


@pytest.mark.parametrize(
    ("evidence_index", "scope_field", "prefix"),
    (
        (
            0,
            "contract_ref",
            "external-operation-contract-ref:governed-browser",
        ),
        (
            1,
            "operation_authority_ref",
            "external-operation-authority-ref:governed-browser",
        ),
        (
            2,
            "operation_input_ref",
            "external-operation-input-ref:governed-browser",
        ),
        (
            3,
            "rollback_ref",
            "external-operation-rollback-ref:governed-browser",
        ),
        (
            4,
            "reconciliation_ref",
            "external-operation-reconciliation-ref:governed-browser",
        ),
    ),
)
def test_external_operation_replay_rejects_every_rehashed_evidence_field_tamper(
    tmp_path: Path,
    evidence_index: int,
    scope_field: str,
    prefix: str,
) -> None:
    payload, context = _external_operation_replay_proof(
        tmp_path,
        operation=GovernedExternalOperation.publish_artifact,
        suffix=f"field-{evidence_index}",
    )
    substituted_ref = _pinned(
        prefix,
        suffix=f"field-{evidence_index}-substitution",
    )
    payload[scope_field] = substituted_ref
    evidence_refs = list(payload["evidence_refs"])
    evidence_refs[evidence_index] = substituted_ref
    payload["evidence_refs"] = evidence_refs
    _rehash_external_operation_replay(payload)

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH",
    ):
        GovernedExternalOperationReceipt.model_validate(
            payload,
            context=replay_validation_context(context),
        )


@pytest.mark.parametrize(
    "mutation",
    ("reverse", "drop", "append", "duplicate"),
)
def test_external_operation_replay_rejects_rehashed_evidence_order_and_arity_tamper(
    tmp_path: Path,
    mutation: str,
) -> None:
    payload, context = _external_operation_replay_proof(
        tmp_path,
        operation=GovernedExternalOperation.publish_artifact,
        suffix=f"shape-{mutation}",
    )
    evidence_refs = list(payload["evidence_refs"])
    if mutation == "reverse":
        evidence_refs.reverse()
    elif mutation == "drop":
        evidence_refs.pop()
    elif mutation == "append":
        evidence_refs.append(
            _pinned(
                "external-operation-reconciliation-ref:governed-browser",
                suffix="shape-extra",
            )
        )
    else:
        evidence_refs.append(evidence_refs[-1])
    payload["evidence_refs"] = evidence_refs
    _rehash_external_operation_replay(payload)

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_OPERATION_SUCCESS_EVIDENCE_MISMATCH",
    ):
        GovernedExternalOperationReceipt.model_validate(
            payload,
            context=replay_validation_context(context),
        )


def test_external_operation_replay_rejects_cross_operation_and_transaction_substitution(
    tmp_path: Path,
) -> None:
    original, original_context = _external_operation_replay_proof(
        tmp_path / "original",
        operation=GovernedExternalOperation.publish_artifact,
        suffix="cross-original",
    )
    foreign_operation, _ = _external_operation_replay_proof(
        tmp_path / "foreign-operation",
        operation=GovernedExternalOperation.send_communication,
        suffix="cross-operation",
    )
    foreign_transaction, _ = _external_operation_replay_proof(
        tmp_path / "foreign-transaction",
        operation=GovernedExternalOperation.publish_artifact,
        suffix="cross-transaction",
    )

    _rehash_external_operation_replay(foreign_operation)
    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_LANE_MISMATCH",
    ):
        GovernedExternalOperationReceipt.model_validate(
            foreign_operation,
            context=replay_validation_context(original_context),
        )

    for field in (
        "transaction_ref",
        "intent_ref",
        "binding_ref",
        "external_action_state",
        "approval_validation_ref",
        "authority_decision_ref",
        "budget_reservation_ref",
        "budget_release_ref",
        "budget_settlement_ref",
        "external_action_reason_refs",
        "replayed",
    ):
        original[field] = foreign_transaction[field]
    _rehash_external_operation_replay(original)
    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH",
    ):
        GovernedExternalOperationReceipt.model_validate(
            original,
            context=replay_validation_context(original_context),
        )


def test_idempotency_drift_returns_content_free_blocked_receipt(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.publish_artifact,
        suffix="idempotency-drift",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    first = service.prepare(_exact(request, recipe))
    drifted_request = request.model_copy(
        update={
            "idempotency_ref": stable_governed_browser_ref(
                "idempotency-ref:governed-external-operation:drifted",
                {"source_idempotency_ref": request.idempotency_ref},
            )
        }
    )

    drifted = service.prepare(_exact(drifted_request, recipe))

    assert first.receipt.status == "contract_ready"
    assert drifted.receipt.status == "preflight_blocked"
    assert drifted.receipt.reason_refs == [
        "reason-ref:governed-external-operation:idempotency-conflict"
    ]
    assert drifted.receipt.content_free is True
    assert drifted.receipt.external_mutation_performed is False
    assert drifted.contract is None


def test_exported_contract_cannot_be_rebound_to_another_recipe(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.create_account,
        suffix="contract-recipe-binding",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    result = service.prepare(_exact(request, recipe))
    assert result.contract is not None
    payload = result.contract.model_dump(mode="json")
    assert "recipe_ref" not in payload
    payload["recipe_ref"] = _pinned(
        "external-operation-recipe-ref:governed-browser",
        suffix="rebound",
    )

    with pytest.raises(ValueError):
        type(result.contract).model_validate(payload)


def test_success_and_replay_receipts_require_complete_kernel_proof(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.publish_artifact,
        suffix="kernel-proof",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    exact = _exact(request, recipe)
    first = service.prepare(exact)
    replay = service.prepare(exact)

    for receipt in (first.receipt, replay.receipt):
        payload = receipt.model_dump(mode="json")
        payload["approval_validation_ref"] = None
        with pytest.raises(ValueError, match="SUCCESS_KERNEL_PROOF_REQUIRED"):
            GovernedExternalOperationReceipt.model_validate(payload)


def test_success_receipt_rejects_tampered_operation_evidence(tmp_path: Path) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.publish_artifact,
        suffix="receipt-evidence",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    result = service.prepare(_exact(request, recipe))
    payload = result.receipt.model_dump(mode="json")
    payload["evidence_refs"] = [
        *payload["evidence_refs"][:-1],
        _pinned(
            "external-operation-reconciliation-ref:governed-browser",
            suffix="tampered",
        ),
    ]

    with pytest.raises(ValueError, match="SUCCESS_EVIDENCE_MISMATCH"):
        GovernedExternalOperationReceipt.model_validate(payload)


def test_operation_receipt_rejects_rebound_kernel_receipt_fields(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.publish_artifact,
        suffix="kernel-receipt-binding",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    result = service.prepare(_exact(request, recipe))
    payload = result.receipt.model_dump(mode="json")
    payload["binding_ref"] = _ref("binding", "rebound-kernel-receipt")
    identity_payload = {
        key: value for key, value in payload.items() if key != "receipt_ref"
    }
    if identity_payload["budget_release_ref"] is None:
        identity_payload.pop("budget_release_ref")
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-operation",
        identity_payload,
    )

    with pytest.raises(ValueError, match="EXTERNAL_RECEIPT_REF_MISMATCH"):
        GovernedExternalOperationReceipt.model_validate(payload)


def test_operation_preflight_rejects_release_proof_without_kernel_receipt(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.publish_artifact,
        suffix="orphaned-release-proof",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    result = service.prepare(
        ExactGovernedExternalOperationRequest(
            execution_request=request,
            recipe_ref="external-operation-recipe-ref:governed-browser:unknown",
            contract_ref=recipe.contract_ref,
            operation=recipe.operation,
            target_ref=recipe.target_ref,
        )
    )
    payload = result.receipt.model_dump(mode="json")
    payload["budget_release_ref"] = _pinned(
        "receipt-ref:authority-budget",
        suffix="orphaned-release-proof",
    )
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-operation",
        external_operation_module._external_operation_receipt_identity_payload(
            GovernedExternalOperationReceipt.model_construct(**payload)
        ),
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_OPERATION_EXTERNAL_PROOF_CONTEXT_INVALID",
    ):
        GovernedExternalOperationReceipt.model_validate(payload)


def test_operation_non_preflight_receipt_requires_kernel_context(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.publish_artifact,
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
            "external_action_reason_refs": [],
            "reason_refs": [
                (
                    "reason-ref:governed-external-operation:"
                    "contract-preparation-failed"
                )
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
        "receipt-ref:governed-external-operation",
        identity_payload,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_OPERATION_EXTERNAL_PROOF_CONTEXT_REQUIRED",
    ):
        GovernedExternalOperationReceipt.model_validate(payload)


def test_operation_receipt_rejects_kernel_state_status_mismatch(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.publish_artifact,
        suffix="state-status-mismatch",
    )
    service, _ = _service(tmp_path, request=request, registry=registry)
    payload = service.prepare(_exact(request, recipe)).receipt.model_dump(mode="json")
    payload["status"] = "failed"
    identity_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"receipt_ref", "budget_release_ref"}
    }
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-operation",
        identity_payload,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_OPERATION_RECEIPT_STATE_MISMATCH",
    ):
        GovernedExternalOperationReceipt.model_validate(payload)


@pytest.mark.parametrize(
    ("updates", "expected_error"),
    (
        (
            {
                "external_action_state": ExternalActionState.blocked.value,
                "external_action_receipt_ref": None,
            },
            "GOVERNED_EXTERNAL_OPERATION_READY_STATE_MISMATCH",
        ),
        (
            {
                "replayed": True,
                "external_action_receipt_ref": None,
            },
            "GOVERNED_EXTERNAL_OPERATION_READY_PROOF_REQUIRED",
        ),
    ),
)
def test_operation_ready_receipt_preserves_validation_precedence(
    tmp_path: Path,
    updates: dict[str, object],
    expected_error: str,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.publish_artifact,
        suffix=f"ready-validation-precedence-{expected_error}",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    payload = service.prepare(_exact(request, recipe)).receipt.model_dump(mode="json")
    payload.update(updates)

    with pytest.raises(ValueError, match=expected_error):
        GovernedExternalOperationReceipt.model_validate(payload)


def test_operation_receipt_rejects_conflicting_rehashed_kernel_proofs(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.publish_artifact,
        suffix="conflicting-rehashed-kernel-proofs",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
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
            "reason_refs": payload["external_action_reason_refs"],
        },
    )
    payload["external_action_reason_refs"] = tuple(
        payload["external_action_reason_refs"]
    )
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-operation",
        external_operation_module._external_operation_receipt_identity_payload(
            GovernedExternalOperationReceipt.model_construct(**payload)
        ),
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_OPERATION_EXTERNAL_RECEIPT_REF_MISMATCH",
    ):
        GovernedExternalOperationReceipt.model_validate(payload)


def test_operation_receipt_preserves_prestart_budget_release_proof(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.delete_resource,
        suffix="budget-release-proof",
    )

    def readiness(item):  # type: ignore[no-untyped-def]
        return _readiness(item, safe_disable=True)

    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
        readiness_provider=readiness,
    )

    result = service.prepare(_exact(request, recipe))

    assert result.receipt.status == "transaction_blocked"
    assert result.receipt.budget_reservation_ref is not None
    assert result.receipt.budget_release_ref is not None
    assert result.receipt.budget_settlement_ref is None
    replayed = service.prepare(_exact(request, recipe))
    assert replayed.receipt.budget_release_ref == result.receipt.budget_release_ref


def test_failed_kernel_receipt_keeps_original_reason_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.send_communication,
        suffix="failed-kernel-reason-identity",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    kernel = service._kernel
    kernel_execution = external_operation_module._operation_kernel_execution(
        request,
        recipe_ref=recipe.recipe_ref,
    )
    failed_receipt = kernel._build_receipt(
        kernel_execution,
        ExternalActionState.failed,
        [],
    )
    monkeypatch.setattr(kernel, "execute", lambda *args, **kwargs: failed_receipt)

    result = service.prepare(_exact(request, recipe))

    assert result.receipt.status == "failed"
    assert result.receipt.external_action_reason_refs == ()
    assert result.receipt.reason_refs == [
        "reason-ref:governed-external-operation:contract-preparation-failed"
    ]
    assert result.receipt.external_action_receipt_ref is not None


def test_legacy_failed_operation_receipt_preserves_empty_kernel_reasons(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.send_communication,
        suffix="legacy-failed-kernel-reasons",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    kernel = service._kernel
    kernel_execution = external_operation_module._operation_kernel_execution(
        request,
        recipe_ref=recipe.recipe_ref,
    )
    failed_receipt = kernel._build_receipt(
        kernel_execution,
        ExternalActionState.failed,
        [],
    )
    monkeypatch.setattr(kernel, "execute", lambda *args, **kwargs: failed_receipt)
    result = service.prepare(_exact(request, recipe))
    legacy_payload = result.receipt.model_dump(mode="json")
    legacy_payload.pop("external_action_reason_refs")
    legacy_payload.pop("budget_release_ref", None)
    legacy_payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-operation",
        {key: value for key, value in legacy_payload.items() if key != "receipt_ref"},
    )

    restored = GovernedExternalOperationReceipt.model_validate(legacy_payload)

    assert restored.external_action_reason_refs is None
    assert restored.external_action_receipt_ref == (
        result.receipt.external_action_receipt_ref
    )
    assert restored.reason_refs == [
        "reason-ref:governed-external-operation:contract-preparation-failed"
    ]


def test_legacy_failed_operation_receipt_preserves_nonempty_kernel_reasons(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.send_communication,
        suffix="legacy-failed-nonempty-kernel-reasons",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    kernel = service._kernel
    kernel_execution = external_operation_module._operation_kernel_execution(
        request,
        recipe_ref=recipe.recipe_ref,
    )
    kernel_reason_ref = "reason-ref:governed-external-action:dispatch-exception"
    failed_receipt = kernel._build_receipt(
        kernel_execution,
        ExternalActionState.failed,
        [kernel_reason_ref],
    )
    monkeypatch.setattr(kernel, "execute", lambda *args, **kwargs: failed_receipt)
    result = service.prepare(_exact(request, recipe))
    legacy_payload = result.receipt.model_dump(mode="json")
    legacy_payload.pop("external_action_reason_refs")
    legacy_payload.pop("budget_release_ref", None)
    legacy_payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-operation",
        {key: value for key, value in legacy_payload.items() if key != "receipt_ref"},
    )

    restored = GovernedExternalOperationReceipt.model_validate(legacy_payload)

    assert restored.external_action_reason_refs is None
    assert restored.external_action_receipt_ref == (
        result.receipt.external_action_receipt_ref
    )
    assert restored.reason_refs == [kernel_reason_ref]


def test_expired_recipe_is_non_mutating_preflight_denial(tmp_path: Path) -> None:
    now = utc_now()
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.send_communication,
        suffix="expired",
        created_at=now - timedelta(minutes=2),
        expires_at=now - timedelta(minutes=1),
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
        clock=lambda: now,
    )

    result = service.prepare(_exact(request, recipe))

    assert result.receipt.status == "preflight_blocked"
    assert result.receipt.reason_refs == [
        "reason-ref:governed-external-operation:recipe-expired"
    ]
    assert result.contract is None


def test_prior_started_transaction_remains_outcome_ambiguous_after_recipe_expiry(
    tmp_path: Path,
) -> None:
    now = utc_now()
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.delete_resource,
        suffix="prior-start-expired",
        created_at=now - timedelta(minutes=2),
        expires_at=now - timedelta(minutes=1),
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
        clock=lambda: now,
    )
    kernel_request = request.model_copy(
        update={
            "idempotency_ref": stable_governed_browser_ref(
                "idempotency-ref:governed-external-operation",
                {
                    "source_idempotency_ref": request.idempotency_ref,
                    "recipe_ref": recipe.recipe_ref,
                },
            )
        }
    )
    store = ExternalActionTransactionStore(tmp_path / "transactions.sqlite3")
    prepared_state, prepared_receipt = store.prepare(kernel_request)
    assert prepared_state == "prepared"
    assert prepared_receipt is None
    assert store.claim_start(kernel_request) is True
    with sqlite3.connect(tmp_path / "transactions.sqlite3") as connection:
        connection.execute(
            "UPDATE governed_external_actions SET updated_at = ? "
            "WHERE transaction_ref = ?",
            (
                (utc_now() - timedelta(minutes=2)).isoformat(),
                kernel_request.binding.transaction_ref,
            ),
        )

    result = service.prepare(_exact(request, recipe))

    assert result.receipt.status == "outcome_ambiguous"
    assert result.receipt.external_action_state == "outcome_ambiguous"
    assert result.receipt.reason_refs == [
        "reason-ref:governed-external-action:prior-start-unsettled",
        "reason-ref:governed-external-action:budget-reservation-proof-missing",
    ]
    assert result.receipt.external_mutation_performed is False
    assert result.contract is None


@pytest.mark.parametrize(
    ("clock", "reason_ref"),
    [
        (
            _raising_clock,
            "reason-ref:governed-external-operation:trusted-clock-failed",
        ),
        (
            lambda: datetime(2026, 7, 18, 12, 0, 0),
            "reason-ref:governed-external-operation:trusted-clock-invalid",
        ),
    ],
    ids=["raising", "naive"],
)
def test_invalid_service_clock_is_content_free_preflight_denial(
    tmp_path: Path,
    clock,
    reason_ref: str,
) -> None:  # type: ignore[no-untyped-def]
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.record_legal_consent,
        suffix=f"clock-{reason_ref.rsplit(':', 1)[-1]}",
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
        clock=clock,
    )

    result = service.prepare(_exact(request, recipe))

    assert result.receipt.status == "preflight_blocked"
    assert result.receipt.reason_refs == [reason_ref]
    assert result.receipt.content_free is True
    assert result.receipt.external_mutation_performed is False
    assert result.contract is None


def test_receipts_and_durable_ledger_never_record_descriptor_material(
    tmp_path: Path,
) -> None:
    secret_marker = "private-recipient-marker"
    request, recipe, registry = _operation_context(
        operation=GovernedExternalOperation.send_communication,
        suffix="redaction",
        target_descriptor_ref=f"target-descriptor-ref:{secret_marker}",
    )
    assert secret_marker not in recipe.target_ref
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )

    result = service.prepare(_exact(request, recipe))

    serialized = json.dumps(result.model_dump(mode="json"), sort_keys=True)
    ledger = (tmp_path / "transactions.sqlite3").read_bytes()
    assert secret_marker not in serialized
    assert secret_marker.encode() not in ledger
    assert request.binding.origin.encode() not in ledger
    assert result.receipt.payload_recorded is False
    assert result.receipt.browser_action_performed is False
    assert result.receipt.network_call_performed is False
    assert result.receipt.external_mutation_performed is False


def test_group09_verifier_passes() -> None:
    assert verify() == []
