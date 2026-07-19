from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

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
        "reason-ref:governed-external-action:prior-start-unsettled"
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
