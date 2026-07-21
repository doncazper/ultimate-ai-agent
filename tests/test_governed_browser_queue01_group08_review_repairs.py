from __future__ import annotations

import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Event, get_ident

import pytest

from tests.test_governed_browser_queue01_group08 import (
    _exact,
    _pinned,
    _service,
    _transfer_context,
)
from tests.test_governed_browser_queue01_group01 import _readiness
from ultimate_ai_agent.core.governed_browser import (
    ExactGovernedArtifactTransferRequest,
    ExactGovernedArtifactTransferResult,
    ExactGovernedArtifactTransferService,
    ExternalActionState,
    ExternalActionTargetKind,
    ExternalActionTransactionStore,
    GovernedArtifactMediaType,
    GovernedArtifactPayloadRejected,
    GovernedArtifactQuarantineError,
    GovernedArtifactQuarantineStore,
    GovernedArtifactTransferOperation,
    GovernedArtifactTransferReceipt,
    GovernedArtifactTransferRecipe,
    build_governed_artifact_transfer_recipe,
    governed_artifact_quarantine_ref,
    governed_artifact_ref,
    stable_governed_browser_ref,
)
from ultimate_ai_agent.core.governed_browser.contracts import (
    governed_receipt_identity_payload,
)
from ultimate_ai_agent.core.governed_browser import artifact_transfers as artifact_module
from ultimate_ai_agent.core.governed_browser.operation_proofs import (
    _terminal_binding_filename,
)
from ultimate_ai_agent.core.governed_browser.replay_provenance import (
    ExternalActionReplayValidationContext,
    replay_validation_context,
)
from ultimate_ai_agent.core.time import utc_now


def _rehash_receipt(payload: dict[str, object]) -> dict[str, object]:
    provisional = GovernedArtifactTransferReceipt.model_construct(**payload)
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-artifact-transfer",
        governed_receipt_identity_payload(provisional),
    )
    return payload


def _rehash_external_and_artifact_receipt(
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
    return _rehash_receipt(payload)


def _rehash_terminal_kernel_receipt(
    payload: dict[str, object],
) -> dict[str, object]:
    identity_payload = {
        "transaction_ref": payload["transaction_ref"],
        "intent_ref": payload["intent_ref"],
        "binding_ref": payload["binding_ref"],
        "state": payload["state"],
        "approval_validation_ref": payload["approval_validation_ref"],
        "authority_decision_ref": payload["authority_decision_ref"],
        "budget_reservation_ref": payload["budget_reservation_ref"],
        "budget_settlement_ref": payload["budget_settlement_ref"],
        "evidence_refs": payload["evidence_refs"],
        "reason_refs": payload["reason_refs"],
    }
    if payload.get("budget_release_ref") is not None:
        identity_payload["budget_release_ref"] = payload["budget_release_ref"]
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-action",
        identity_payload,
    )
    return payload


def _read_terminal_kernel_receipt(
    kernel_path: Path,
    *,
    transaction_ref: str,
) -> dict[str, object]:
    with sqlite3.connect(kernel_path / "transactions.sqlite3") as connection:
        row = connection.execute(
            "SELECT receipt_json FROM governed_external_actions "
            "WHERE transaction_ref = ?",
            (transaction_ref,),
        ).fetchone()
    assert row is not None and row[0] is not None
    payload = json.loads(row[0])
    assert isinstance(payload, dict)
    return payload


def _rewrite_terminal_kernel_evidence(
    kernel_path: Path,
    *,
    transaction_ref: str,
    evidence_refs: list[str],
) -> None:
    payload = _read_terminal_kernel_receipt(
        kernel_path,
        transaction_ref=transaction_ref,
    )
    payload["evidence_refs"] = evidence_refs
    _rehash_terminal_kernel_receipt(payload)
    with sqlite3.connect(kernel_path / "transactions.sqlite3") as connection:
        changed = connection.execute(
            "UPDATE governed_external_actions SET receipt_json = ? "
            "WHERE transaction_ref = ?",
            (
                json.dumps(payload, sort_keys=True, separators=(",", ":")),
                transaction_ref,
            ),
        ).rowcount
        connection.commit()
    assert changed == 1


def _seed_download_success_replay(
    tmp_path: Path,
    *,
    suffix: str,
) -> tuple[
    ExactGovernedArtifactTransferService,
    ExactGovernedArtifactTransferRequest,
    GovernedArtifactTransferRecipe,
    GovernedArtifactQuarantineStore,
    Path,
    ExactGovernedArtifactTransferResult,
]:
    store = GovernedArtifactQuarantineStore(tmp_path / f"{suffix}-artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix=suffix,
    )
    kernel_path = tmp_path / f"{suffix}-kernel"
    service, _, _ = _service(
        kernel_path,
        store=store,
        request=request,
        registry=registry,
    )
    exact = _exact(request, recipe)
    result = service.execute(
        exact,
        injected_download_payload=bytearray(f"{suffix}-payload".encode()),
    )
    assert result.quarantine is not None
    return service, exact, recipe, store, kernel_path, result


def _seed_upload_success_replay(
    tmp_path: Path,
    *,
    suffix: str,
) -> tuple[
    ExactGovernedArtifactTransferService,
    ExactGovernedArtifactTransferRequest,
    GovernedArtifactTransferRecipe,
    GovernedArtifactQuarantineStore,
    Path,
    ExactGovernedArtifactTransferResult,
]:
    store = GovernedArtifactQuarantineStore(tmp_path / f"{suffix}-artifacts")
    download_request, download_recipe, download_registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix=f"{suffix}-download",
    )
    download_service, download_kernel, _ = _service(
        tmp_path / f"{suffix}-download-kernel",
        store=store,
        request=download_request,
        registry=download_registry,
    )
    downloaded = download_service.execute(
        _exact(download_request, download_recipe),
        injected_download_payload=bytearray(f"{suffix}-payload".encode()),
    )
    assert downloaded.quarantine is not None
    upload_request, upload_recipe, upload_registry = _transfer_context(
        store,
        operation=(
            GovernedArtifactTransferOperation.upload_quarantined_artifact_plan
        ),
        suffix=f"{suffix}-upload",
        artifact_ref=download_recipe.artifact_ref,
        quarantine_ref=download_recipe.quarantine_ref,
        download_transaction_ref=download_recipe.download_transaction_ref,
        content_fingerprint_ref=downloaded.quarantine.content_fingerprint_ref,
        source_download_receipt_ref=(
            downloaded.receipt.external_action_receipt_ref
        ),
        source_download_recipe_ref=download_recipe.recipe_ref,
    )
    kernel_path = tmp_path / f"{suffix}-upload-kernel"
    upload_service, _, _ = _service(
        kernel_path,
        store=store,
        request=upload_request,
        registry=upload_registry,
        source_download_kernel=download_kernel,
        source_download_registry=download_registry,
        source_download_request=_exact(download_request, download_recipe),
    )
    exact = _exact(upload_request, upload_recipe)
    result = upload_service.execute(exact)
    assert result.upload_plan is not None
    return upload_service, exact, upload_recipe, store, kernel_path, result


def _download_replay_proof(
    tmp_path: Path,
    *,
    suffix: str,
) -> tuple[
    dict[str, object],
    ExternalActionReplayValidationContext,
]:
    store = GovernedArtifactQuarantineStore(tmp_path / f"{suffix}-artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix=suffix,
    )
    service, kernel, _ = _service(
        tmp_path / f"{suffix}-kernel",
        store=store,
        request=request,
        registry=registry,
    )
    exact = _exact(request, recipe)
    service.execute(
        exact,
        injected_download_payload=bytearray(f"{suffix}-payload".encode()),
    )
    replay_result = service.execute(exact)
    kernel_execution = artifact_module._artifact_transfer_kernel_execution(
        exact.execution_request,
        recipe_ref=recipe.recipe_ref,
    )
    replay_receipt = kernel.replay_if_terminal(kernel_execution)
    assert replay_receipt is not None
    service_binding = (
        artifact_module._require_artifact_transfer_service_binding(service)
    )
    context = artifact_module._artifact_replay_validation_context(
        kernel=kernel,
        expected_execution=kernel_execution,
        recipe=recipe,
        replay_receipt=replay_receipt,
        service_binding=service_binding,
    )
    return replay_result.receipt.model_dump(mode="json"), context


def _upload_replay_proof(
    tmp_path: Path,
    *,
    suffix: str,
) -> tuple[
    dict[str, object],
    ExternalActionReplayValidationContext,
]:
    store = GovernedArtifactQuarantineStore(tmp_path / f"{suffix}-artifacts")
    download_request, download_recipe, download_registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix=f"{suffix}-download",
    )
    download_service, download_kernel, _ = _service(
        tmp_path / f"{suffix}-download-kernel",
        store=store,
        request=download_request,
        registry=download_registry,
    )
    downloaded = download_service.execute(
        _exact(download_request, download_recipe),
        injected_download_payload=bytearray(f"{suffix}-payload".encode()),
    )
    assert downloaded.quarantine is not None
    upload_request, upload_recipe, upload_registry = _transfer_context(
        store,
        operation=(
            GovernedArtifactTransferOperation.upload_quarantined_artifact_plan
        ),
        suffix=f"{suffix}-upload",
        artifact_ref=download_recipe.artifact_ref,
        quarantine_ref=download_recipe.quarantine_ref,
        download_transaction_ref=download_recipe.download_transaction_ref,
        content_fingerprint_ref=downloaded.quarantine.content_fingerprint_ref,
        source_download_receipt_ref=(
            downloaded.receipt.external_action_receipt_ref
        ),
        source_download_recipe_ref=download_recipe.recipe_ref,
    )
    upload_service, upload_kernel, _ = _service(
        tmp_path / f"{suffix}-upload-kernel",
        store=store,
        request=upload_request,
        registry=upload_registry,
        source_download_kernel=download_kernel,
        source_download_registry=download_registry,
        source_download_request=_exact(download_request, download_recipe),
    )
    exact = _exact(upload_request, upload_recipe)
    upload_service.execute(exact)
    replay_result = upload_service.execute(exact)
    kernel_execution = artifact_module._artifact_transfer_kernel_execution(
        exact.execution_request,
        recipe_ref=upload_recipe.recipe_ref,
    )
    replay_receipt = upload_kernel.replay_if_terminal(kernel_execution)
    assert replay_receipt is not None
    context = artifact_module._artifact_replay_validation_context(
        kernel=upload_kernel,
        expected_execution=kernel_execution,
        recipe=upload_recipe,
        replay_receipt=replay_receipt,
        service_binding=(
            artifact_module._require_artifact_transfer_service_binding(
                upload_service
            )
        ),
    )
    return replay_result.receipt.model_dump(mode="json"), context


def _artifact_terminal_replay_proof(
    tmp_path: Path,
    *,
    terminal_state: ExternalActionState,
) -> tuple[
    dict[str, object],
    ExternalActionReplayValidationContext,
    list[str],
]:
    suffix = f"terminal-replay-{terminal_state.value}"
    store = GovernedArtifactQuarantineStore(tmp_path / f"{suffix}-artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix=suffix,
    )
    kernel_path = tmp_path / f"{suffix}-kernel"
    service, kernel, _ = _service(
        kernel_path,
        store=store,
        request=request,
        registry=registry,
        readiness_provider=(
            (lambda item: _readiness(item, safe_disable=True))
            if terminal_state == ExternalActionState.blocked
            else None
        ),
    )
    exact = _exact(request, recipe)
    kernel_execution = artifact_module._artifact_transfer_kernel_execution(
        exact.execution_request,
        recipe_ref=recipe.recipe_ref,
    )
    if terminal_state == ExternalActionState.outcome_ambiguous:
        durable_store = ExternalActionTransactionStore(
            kernel_path / "transactions.sqlite3"
        )
        durable_store.prepare(kernel_execution)
        assert durable_store.claim_start(kernel_execution) is True
        with sqlite3.connect(kernel_path / "transactions.sqlite3") as connection:
            connection.execute(
                "UPDATE governed_external_actions SET updated_at = ? "
                "WHERE transaction_ref = ?",
                (
                    (utc_now() - timedelta(minutes=2)).isoformat(),
                    kernel_execution.binding.transaction_ref,
                ),
            )

    payload_size = (
        recipe.max_bytes + 1
        if terminal_state == ExternalActionState.failed
        else 16
    )
    first = service.execute(
        exact,
        injected_download_payload=bytearray(payload_size),
    )
    replay = service.execute(
        exact,
        injected_download_payload=bytearray(payload_size),
    )
    terminal_receipt = kernel.replay_if_terminal(kernel_execution)
    assert terminal_receipt is not None
    context = artifact_module._artifact_replay_validation_context(
        kernel=kernel,
        expected_execution=kernel_execution,
        recipe=recipe,
        replay_receipt=terminal_receipt,
        service_binding=(
            artifact_module._require_artifact_transfer_service_binding(service)
        ),
    )
    expected_evidence = {
        ExternalActionState.blocked: [],
        ExternalActionState.failed: [
            stable_governed_browser_ref(
                "evidence-ref:governed-artifact:download-payload-rejected",
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


def _seed_arbitrary_artifact_terminal_evidence(
    tmp_path: Path,
    *,
    terminal_state: ExternalActionState,
) -> tuple[
    ExactGovernedArtifactTransferService,
    ExactGovernedArtifactTransferRequest,
]:
    suffix = f"arbitrary-terminal-evidence-{terminal_state.value}"
    quarantine_store = GovernedArtifactQuarantineStore(
        tmp_path / f"{suffix}-artifacts"
    )
    request, recipe, registry = _transfer_context(
        quarantine_store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix=suffix,
    )
    kernel_path = tmp_path / f"{suffix}-kernel"
    service, kernel, _ = _service(
        kernel_path,
        store=quarantine_store,
        request=request,
        registry=registry,
    )
    exact = _exact(request, recipe)
    kernel_execution = artifact_module._artifact_transfer_kernel_execution(
        exact.execution_request,
        recipe_ref=recipe.recipe_ref,
    )
    durable_store = ExternalActionTransactionStore(
        kernel_path / "transactions.sqlite3"
    )
    durable_store.prepare(kernel_execution)
    expected_state = ExternalActionState.prepared
    if terminal_state != ExternalActionState.blocked:
        assert durable_store.claim_start(kernel_execution) is True
        expected_state = ExternalActionState.started
    arbitrary_ref = stable_governed_browser_ref(
        "evidence-ref:governed-artifact:arbitrary-non-success",
        {"state": terminal_state.value},
    )
    terminal_receipt = kernel._build_receipt(
        kernel_execution,
        terminal_state,
        ["reason-ref:governed-external-action:test-terminal-state"],
        evidence_refs=[arbitrary_ref],
    )
    durable_store.finish(terminal_receipt, expected_state=expected_state)
    return (
        service,
        exact,
    )


def test_exact_scope_real_targets_and_receipt_forgery_fail_closed(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, _ = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="exact-scope",
    )
    with pytest.raises(ValueError, match="EXACT_ARTIFACT_SCOPE_REQUIRED"):
        build_governed_artifact_transfer_recipe(
            request,
            operation=GovernedArtifactTransferOperation.download_quarantine,
            artifact_ref=_pinned(
                "artifact-ref:governed-browser",
                suffix="wrong",
            ),
            quarantine_ref=recipe.quarantine_ref,
            download_transaction_ref=recipe.download_transaction_ref,
            quarantine_store_ref=store.binding_ref,
            transfer_surface_ref=recipe.transfer_surface_ref,
            visibility_proof_ref=recipe.visibility_proof_ref,
            declared_media_type=GovernedArtifactMediaType.text_plain,
            max_bytes=1024,
            content_fingerprint_ref=None,
            created_at=recipe.created_at,
            expires_at=recipe.expires_at,
        )
    with pytest.raises(ValueError, match="REAL_TARGETS_INACTIVE"):
        _transfer_context(
            store,
            operation=GovernedArtifactTransferOperation.download_quarantine,
            suffix="external-target",
            target_kind=ExternalActionTargetKind.external,
        )
    other_artifact_ref = governed_artifact_ref(
        source_ref=_pinned(
            "artifact-source-ref:governed-browser",
            suffix="other-artifact",
        ),
        declared_media_type=GovernedArtifactMediaType.text_plain,
    )
    other_quarantine_ref = governed_artifact_quarantine_ref(
        origin_ref=recipe.origin_ref,
        artifact_ref=other_artifact_ref,
        download_transaction_ref=recipe.download_transaction_ref,
    )
    with pytest.raises(ValueError, match="QUARANTINE_SCOPE_MISMATCH"):
        build_governed_artifact_transfer_recipe(
            request,
            operation=GovernedArtifactTransferOperation.download_quarantine,
            artifact_ref=recipe.artifact_ref,
            quarantine_ref=other_quarantine_ref,
            download_transaction_ref=recipe.download_transaction_ref,
            quarantine_store_ref=store.binding_ref,
            transfer_surface_ref=recipe.transfer_surface_ref,
            visibility_proof_ref=recipe.visibility_proof_ref,
            declared_media_type=GovernedArtifactMediaType.text_plain,
            max_bytes=1024,
            content_fingerprint_ref=None,
            created_at=recipe.created_at,
            expires_at=recipe.expires_at,
        )

    receipt_payload = {
        "recipe_ref": recipe.recipe_ref,
        "operation": recipe.operation,
        "artifact_ref": recipe.artifact_ref,
        "quarantine_ref": recipe.quarantine_ref,
        "download_transaction_ref": recipe.download_transaction_ref,
        "origin_ref": recipe.origin_ref,
        "transaction_ref": request.binding.transaction_ref,
        "intent_ref": request.intent_ref,
        "binding_ref": request.binding.binding_ref,
        "status": "preflight_blocked",
        "external_action_state": "blocked",
        "reason_refs": ["reason-ref:governed-artifact:test"],
    }
    provisional = GovernedArtifactTransferReceipt.model_construct(
        receipt_ref="receipt-ref:governed-artifact-transfer:pending",
        **receipt_payload,
    )
    receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-artifact-transfer",
        governed_receipt_identity_payload(provisional),
    )
    parsed = GovernedArtifactTransferReceipt(
        receipt_ref=receipt_ref,
        **receipt_payload,
    )
    forged = parsed.model_dump(mode="json")
    forged["artifact_ref"] = other_artifact_ref
    with pytest.raises(ValueError, match="QUARANTINE_SCOPE_MISMATCH"):
        GovernedArtifactTransferReceipt.model_validate(forged)
    forged = parsed.model_dump(mode="json")
    forged["receipt_ref"] = "receipt-ref:governed-artifact-transfer:forged"
    with pytest.raises(ValueError, match="RECEIPT_REF_MISMATCH"):
        GovernedArtifactTransferReceipt.model_validate(forged)
    forged = parsed.model_dump(mode="json")
    forged["raw_artifact_recorded"] = True
    with pytest.raises(ValueError):
        GovernedArtifactTransferReceipt.model_validate(forged)
    forged = parsed.model_dump(mode="json")
    forged["status"] = "quarantined"
    forged["operation"] = "upload_quarantined_artifact_plan"
    provisional = GovernedArtifactTransferReceipt.model_construct(**forged)
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-artifact-transfer",
        governed_receipt_identity_payload(provisional),
    )
    with pytest.raises(ValueError, match="OPERATION_STATUS_MISMATCH"):
        GovernedArtifactTransferReceipt.model_validate(forged)


def test_upload_source_transaction_must_be_prior_and_distinct(tmp_path: Path) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    fingerprint = store.validate_payload(
        payload=b"source transaction",
        declared_media_type=GovernedArtifactMediaType.text_plain,
        max_bytes=1024,
    ).content_fingerprint_ref

    with pytest.raises(ValueError, match="SOURCE_TRANSACTION_MUST_BE_DISTINCT"):
        _transfer_context(
            store,
            operation=(
                GovernedArtifactTransferOperation.upload_quarantined_artifact_plan
            ),
            suffix="same-source-transaction",
            content_fingerprint_ref=fingerprint,
        )


@pytest.mark.parametrize(
    "missing_ref",
    [
        "external_action_receipt_ref",
        "approval_validation_ref",
        "authority_decision_ref",
        "budget_reservation_ref",
        "budget_settlement_ref",
    ],
)
def test_ready_receipts_require_complete_kernel_proof(
    tmp_path: Path,
    missing_ref: str,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix=f"receipt-proof-{missing_ref}",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    result = service.execute(
        _exact(request, recipe),
        injected_download_payload=bytearray(b"kernel proof"),
    )
    forged = result.receipt.model_dump(mode="json")
    forged[missing_ref] = None
    _rehash_receipt(forged)

    with pytest.raises(ValueError, match="READY_KERNEL_PROOF_REQUIRED"):
        GovernedArtifactTransferReceipt.model_validate(forged)
    if missing_ref == "external_action_receipt_ref":
        missing_evidence = result.receipt.model_dump(mode="json")
        missing_evidence["evidence_refs"] = []
        _rehash_receipt(missing_evidence)
        with pytest.raises(ValueError, match="READY_EVIDENCE_MISMATCH"):
            GovernedArtifactTransferReceipt.model_validate(missing_evidence)


@pytest.mark.parametrize("tampered_field", ["byte_count", "content_fingerprint_ref"])
def test_quarantine_projection_must_match_receipt_evidence(
    tmp_path: Path,
    tampered_field: str,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix=f"quarantine-evidence-{tampered_field}",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    result = service.execute(
        _exact(request, recipe),
        injected_download_payload=bytearray(b"quarantine evidence"),
    )
    assert result.quarantine is not None
    forged = result.quarantine.model_dump(mode="python")
    if tampered_field == "byte_count":
        forged["byte_count"] += 1
    else:
        forged["content_fingerprint_ref"] = _pinned(
            "content-fingerprint-ref:governed-browser",
            suffix="tampered-quarantine",
        )
    provisional = type(result.quarantine).model_construct(**forged)
    forged["quarantine_projection_ref"] = stable_governed_browser_ref(
        "artifact-quarantine-projection-ref:governed-browser",
        provisional.model_dump(
            mode="json",
            exclude={"quarantine_projection_ref"},
        ),
    )
    tampered = type(result.quarantine).model_validate(forged)

    with pytest.raises(ValueError, match="QUARANTINE_RESULT_EVIDENCE_MISMATCH"):
        ExactGovernedArtifactTransferResult(
            receipt=result.receipt,
            quarantine=tampered,
        )


def test_upload_plan_must_match_receipt_fingerprint_and_plan_evidence(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    download_request, download_recipe, download_registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="plan-evidence-download",
    )
    download_service, download_kernel, _ = _service(
        tmp_path / "download-kernel",
        store=store,
        request=download_request,
        registry=download_registry,
    )
    downloaded = download_service.execute(
        _exact(download_request, download_recipe),
        injected_download_payload=bytearray(b"plan evidence"),
    )
    assert downloaded.quarantine is not None
    upload_request, upload_recipe, upload_registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.upload_quarantined_artifact_plan,
        suffix="plan-evidence-upload",
        artifact_ref=download_recipe.artifact_ref,
        quarantine_ref=download_recipe.quarantine_ref,
        download_transaction_ref=download_recipe.download_transaction_ref,
        content_fingerprint_ref=downloaded.quarantine.content_fingerprint_ref,
        source_download_receipt_ref=(downloaded.receipt.external_action_receipt_ref),
        source_download_recipe_ref=download_recipe.recipe_ref,
    )
    upload_service, _, _ = _service(
        tmp_path / "upload-kernel",
        store=store,
        request=upload_request,
        registry=upload_registry,
        source_download_kernel=download_kernel,
        source_download_registry=download_registry,
        source_download_request=_exact(download_request, download_recipe),
    )
    result = upload_service.execute(_exact(upload_request, upload_recipe))
    assert result.upload_plan is not None
    forged = result.upload_plan.model_dump(mode="python")
    forged["transfer_surface_ref"] = _pinned(
        "artifact-transfer-surface-ref:governed-browser",
        suffix="tampered-plan",
    )
    provisional = type(result.upload_plan).model_construct(**forged)
    forged["plan_ref"] = stable_governed_browser_ref(
        "artifact-upload-plan-ref:governed-browser",
        provisional.model_dump(mode="json", exclude={"plan_ref"}),
    )
    tampered = type(result.upload_plan).model_validate(forged)

    with pytest.raises(ValueError, match="UPLOAD_PLAN_RESULT_EVIDENCE_MISMATCH"):
        ExactGovernedArtifactTransferResult(
            receipt=result.receipt,
            upload_plan=tampered,
        )


def test_upload_plan_requires_bound_source_ledger_and_registered_download_recipe(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    download_request, download_recipe, download_registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="source-proof-download",
    )
    download_service, download_kernel, _ = _service(
        tmp_path / "download-kernel",
        store=store,
        request=download_request,
        registry=download_registry,
    )
    downloaded = download_service.execute(
        _exact(download_request, download_recipe),
        injected_download_payload=bytearray(b"surviving quarantine file"),
    )
    assert downloaded.quarantine is not None
    upload_request, upload_recipe, upload_registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.upload_quarantined_artifact_plan,
        suffix="source-proof-upload",
        artifact_ref=download_recipe.artifact_ref,
        quarantine_ref=download_recipe.quarantine_ref,
        download_transaction_ref=download_recipe.download_transaction_ref,
        content_fingerprint_ref=downloaded.quarantine.content_fingerprint_ref,
        source_download_receipt_ref=(downloaded.receipt.external_action_receipt_ref),
        source_download_recipe_ref=download_recipe.recipe_ref,
    )
    upload_service, _, _ = _service(
        tmp_path / "upload-kernel",
        store=store,
        request=upload_request,
        registry=upload_registry,
        source_download_kernel=download_kernel,
        source_download_registry=upload_registry,
        source_download_request=_exact(download_request, download_recipe),
    )

    result = upload_service.execute(_exact(upload_request, upload_recipe))

    assert result.receipt.status == "failed"
    assert result.receipt.external_action_state == "failed"
    assert result.receipt.evidence_refs[0].startswith(
        "evidence-ref:governed-artifact:source-download-receipt-required:"
    )
    assert result.upload_plan is None


def test_full_bounded_text_payload_is_scanned_for_active_content(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    payload = b"bounded-prefix-" + (b"a" * 1024) + b"<ScRiPt>denied</sCrIpT>"

    with pytest.raises(GovernedArtifactPayloadRejected, match="CONTENT_TYPE_MISMATCH"):
        store.validate_payload(
            payload=payload,
            declared_media_type=GovernedArtifactMediaType.text_plain,
            max_bytes=2048,
        )


@pytest.mark.parametrize(
    ("mode", "reason_ref"),
    [
        ("raises", "reason-ref:governed-artifact:trusted-clock-failed"),
        ("naive", "reason-ref:governed-artifact:trusted-clock-invalid"),
    ],
)
def test_invalid_service_clock_returns_a_content_free_blocked_receipt(
    tmp_path: Path,
    mode: str,
    reason_ref: str,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix=f"invalid-clock-{mode}",
    )

    def invalid_clock():  # type: ignore[no-untyped-def]
        if mode == "raises":
            raise RuntimeError("clock unavailable")
        return recipe.created_at.replace(tzinfo=None)

    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
        clock=invalid_clock,
    )
    payload = bytearray(b"clock-blocked payload")

    result = service.execute(
        _exact(request, recipe),
        injected_download_payload=payload,
    )

    assert result.receipt.status == "preflight_blocked"
    assert result.receipt.reason_refs == [reason_ref]
    assert result.receipt.content_free is True
    assert result.quarantine is None
    assert payload == bytearray(len(payload))
    assert list((tmp_path / "artifacts" / "artifact-quarantine").iterdir()) == []


def test_raw_upload_payload_is_denied_and_zeroized_before_transaction(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    fingerprint = store.validate_payload(
        payload=b"expected",
        declared_media_type=GovernedArtifactMediaType.text_plain,
        max_bytes=1024,
    ).content_fingerprint_ref
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.upload_quarantined_artifact_plan,
        suffix="raw-upload",
        download_transaction_ref=_pinned(
            "transaction-ref:governed-browser",
            suffix="raw-upload-source",
        ),
        content_fingerprint_ref=fingerprint,
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    terminal = service.execute(_exact(request, recipe))
    assert terminal.receipt.status == "failed"
    ledger_before_raw_replay = (
        tmp_path / "kernel" / "transactions.sqlite3"
    ).read_bytes()
    payload = bytearray(b"raw upload body")

    result = service.execute(
        _exact(request, recipe),
        injected_download_payload=payload,
    )

    assert result.receipt.status == "preflight_blocked"
    assert result.receipt.reason_refs == [
        "reason-ref:governed-artifact:raw-upload-payload-denied"
    ]
    assert payload == bytearray(len(payload))
    assert (
        ledger_before_raw_replay
        == (tmp_path / "kernel" / "transactions.sqlite3").read_bytes()
    )


def test_timed_out_quarantine_dispatch_owns_an_independent_mutable_buffer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="timed-out-payload-handoff",
    )
    service, kernel, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    kernel._dispatch_timeout_seconds = 0.01
    original_quarantine = store.quarantine
    entered = Event()
    proceed = Event()
    dispatched_buffers: list[bytearray] = []
    dispatched_snapshots: list[bytes] = []

    def delayed_quarantine(
        _store: GovernedArtifactQuarantineStore,
        *,
        payload: bytearray,
        **kwargs,  # type: ignore[no-untyped-def]
    ):  # type: ignore[no-untyped-def]
        dispatched_buffers.append(payload)
        dispatched_snapshots.append(bytes(payload))
        entered.set()
        assert proceed.wait(timeout=2)
        return original_quarantine(payload=payload, **kwargs)

    monkeypatch.setattr(
        GovernedArtifactQuarantineStore,
        "quarantine",
        delayed_quarantine,
    )
    payload = bytearray(b"bounded timeout artifact")
    expected_payload = bytes(payload)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            service.execute,
            _exact(request, recipe),
            injected_download_payload=payload,
        )
        assert entered.wait(timeout=2)
        time.sleep(0.03)
        assert future.done() is False
        proceed.set()
        result = future.result(timeout=2)

    assert result.receipt.status == "outcome_ambiguous"
    assert payload == bytearray(len(payload))
    assert dispatched_snapshots == [expected_payload]
    assert dispatched_buffers[0] is not payload
    assert dispatched_buffers[0] == bytearray(len(dispatched_buffers[0]))


def test_oversized_download_payload_uses_bounded_owned_sentinel_before_dispatch(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="oversized-before-copy",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    payload = bytearray(recipe.max_bytes + 1)

    result = service.execute(
        _exact(request, recipe),
        injected_download_payload=payload,
    )

    expected_evidence_ref = stable_governed_browser_ref(
        "evidence-ref:governed-artifact:download-payload-rejected",
        {"intent_ref": request.intent_ref},
    )
    expected_external_receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-external-action",
        {
            "transaction_ref": result.receipt.transaction_ref,
            "intent_ref": result.receipt.intent_ref,
            "binding_ref": result.receipt.binding_ref,
            "state": result.receipt.external_action_state,
            "approval_validation_ref": result.receipt.approval_validation_ref,
            "authority_decision_ref": result.receipt.authority_decision_ref,
            "budget_reservation_ref": result.receipt.budget_reservation_ref,
            "budget_settlement_ref": result.receipt.budget_settlement_ref,
            "evidence_refs": [expected_evidence_ref],
            "reason_refs": [],
        },
    )
    assert result.receipt.status == "failed"
    assert result.receipt.reason_refs == [
        "reason-ref:governed-artifact:transfer-preparation-failed"
    ]
    assert result.receipt.evidence_refs == [expected_evidence_ref]
    assert result.receipt.external_action_receipt_ref == expected_external_receipt_ref
    assert payload == bytearray(len(payload))


def test_oversized_download_snapshot_is_immune_to_concurrent_caller_mutation(
    tmp_path: Path,
) -> None:
    class DispatchBarrierClock:
        def __init__(self, value):  # type: ignore[no-untyped-def]
            self.value = value
            self.execution_thread_id: int | None = None
            self.dispatch_entered = Event()
            self.proceed = Event()

        def __call__(self):  # type: ignore[no-untyped-def]
            if (
                self.execution_thread_id is not None
                and get_ident() != self.execution_thread_id
            ):
                self.dispatch_entered.set()
                assert self.proceed.wait(timeout=2)
            return self.value

    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="oversized-snapshot-mutation",
    )
    clock = DispatchBarrierClock(recipe.created_at + timedelta(seconds=1))
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
        clock=clock,
    )
    payload = bytearray(recipe.max_bytes + 1)

    def execute():  # type: ignore[no-untyped-def]
        clock.execution_thread_id = get_ident()
        return service.execute(
            _exact(request, recipe),
            injected_download_payload=payload,
        )

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(execute)
        assert clock.dispatch_entered.wait(timeout=2)
        payload[:] = b"tiny"
        clock.proceed.set()
        result = future.result(timeout=2)

    assert result.receipt.status == "failed"
    assert result.receipt.evidence_refs[0].startswith(
        "evidence-ref:governed-artifact:download-payload-rejected:"
    )
    assert list((tmp_path / "artifacts").rglob("*.quarantine")) == []
    assert payload == bytearray(4)


def test_oversized_download_uses_only_a_bounded_worker_sentinel(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="oversized-bounded-sentinel",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    payload = bytearray(recipe.max_bytes * 4)
    observed_zeroizations: list[tuple[bool, int]] = []
    original_zeroize = artifact_module._zeroize_mutable_payload

    def record_zeroize(candidate: bytearray) -> None:
        observed_zeroizations.append((candidate is payload, len(candidate)))
        original_zeroize(candidate)

    monkeypatch.setattr(
        artifact_module,
        "_zeroize_mutable_payload",
        record_zeroize,
    )

    result = service.execute(
        _exact(request, recipe),
        injected_download_payload=payload,
    )

    assert result.receipt.status == "failed"
    assert (False, 1) in observed_zeroizations
    assert (True, recipe.max_bytes * 4) in observed_zeroizations
    assert all(
        length <= 1
        for is_caller, length in observed_zeroizations
        if not is_caller
    )
    assert payload == bytearray(len(payload))


def test_service_proof_failure_precedes_quarantine_and_retry_is_clean(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="proof-first-failure",
    )
    service, _, _ = _service(
        tmp_path / "first-kernel",
        store=store,
        request=request,
        registry=registry,
    )
    original_record = GovernedArtifactQuarantineStore._record_service_proof

    def fail_record(*_args: object, **_kwargs: object) -> None:
        raise GovernedArtifactQuarantineError(
            "GOVERNED_ARTIFACT_SERVICE_PROOF_WRITE_FAILED"
        )

    monkeypatch.setattr(
        GovernedArtifactQuarantineStore,
        "_record_service_proof",
        fail_record,
    )
    first = service.execute(
        _exact(request, recipe),
        injected_download_payload=bytearray(b"proof must precede file"),
    )

    assert first.receipt.status == "failed"
    assert list((tmp_path / "artifacts").rglob("*.quarantine")) == []
    assert list((tmp_path / "artifacts").rglob("*.service-proof")) == []

    monkeypatch.setattr(
        GovernedArtifactQuarantineStore,
        "_record_service_proof",
        original_record,
    )
    retry_service, _, _ = _service(
        tmp_path / "retry-kernel",
        store=store,
        request=request,
        registry=registry,
    )
    retry = retry_service.execute(
        _exact(request, recipe),
        injected_download_payload=bytearray(b"proof must precede file"),
    )

    assert retry.receipt.status == "quarantined"
    assert len(list((tmp_path / "artifacts").rglob("*.quarantine"))) == 1
    assert len(list((tmp_path / "artifacts").rglob("*.service-proof"))) == 1


def test_quarantine_failure_reuses_exact_durable_proof_on_clean_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="quarantine-failure-proof-retry",
    )
    service, _, _ = _service(
        tmp_path / "first-kernel",
        store=store,
        request=request,
        registry=registry,
    )
    original_quarantine = GovernedArtifactQuarantineStore.quarantine

    def fail_quarantine(*_args: object, **_kwargs: object) -> None:
        raise GovernedArtifactQuarantineError(
            "GOVERNED_ARTIFACT_QUARANTINE_WRITE_UNCERTAIN"
        )

    monkeypatch.setattr(
        GovernedArtifactQuarantineStore,
        "quarantine",
        fail_quarantine,
    )
    first = service.execute(
        _exact(request, recipe),
        injected_download_payload=bytearray(b"durable proof retry payload"),
    )

    assert first.receipt.status == "outcome_ambiguous"
    assert list((tmp_path / "artifacts").rglob("*.quarantine")) == []
    assert len(list((tmp_path / "artifacts").rglob("*.service-proof"))) == 1

    monkeypatch.setattr(
        GovernedArtifactQuarantineStore,
        "quarantine",
        original_quarantine,
    )
    retry_service, _, _ = _service(
        tmp_path / "retry-kernel",
        store=store,
        request=request,
        registry=registry,
    )
    retry = retry_service.execute(
        _exact(request, recipe),
        injected_download_payload=bytearray(
            b"durable proof retry payload"
        ),
    )

    assert retry.receipt.status == "quarantined"
    assert len(list((tmp_path / "artifacts").rglob("*.quarantine"))) == 1
    assert len(list((tmp_path / "artifacts").rglob("*.service-proof"))) == 1


def test_download_requires_exact_quarantine_return_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="quarantine-return-projection",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    original_quarantine = GovernedArtifactQuarantineStore.quarantine

    def substitute_projection(
        exact_store: GovernedArtifactQuarantineStore,
        **kwargs: object,
    ):  # type: ignore[no-untyped-def]
        inspection = original_quarantine(exact_store, **kwargs)
        return inspection.model_copy(
            update={"byte_count": inspection.byte_count + 1}
        )

    monkeypatch.setattr(
        GovernedArtifactQuarantineStore,
        "quarantine",
        substitute_projection,
    )

    result = service.execute(
        _exact(request, recipe),
        injected_download_payload=bytearray(b"exact projection required"),
    )

    assert result.receipt.status == "outcome_ambiguous"
    assert result.quarantine is None
    assert len(list((tmp_path / "artifacts").rglob("*.quarantine"))) == 1
    assert len(list((tmp_path / "artifacts").rglob("*.service-proof"))) == 1


def test_artifact_receipt_rejects_rehashed_conflicting_kernel_proofs(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="conflicting-kernel-proofs",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    result = service.execute(
        _exact(request, recipe),
        injected_download_payload=bytearray(b"bounded artifact"),
    )
    forged = result.receipt.model_dump(mode="json")
    forged["budget_release_ref"] = stable_governed_browser_ref(
        "budget-release-ref:governed-artifact",
        {"case": "conflicting-kernel-proofs"},
    )
    forged["external_action_receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-action",
        {
            "transaction_ref": forged["transaction_ref"],
            "intent_ref": forged["intent_ref"],
            "binding_ref": forged["binding_ref"],
            "state": forged["external_action_state"],
            "approval_validation_ref": forged["approval_validation_ref"],
            "authority_decision_ref": forged["authority_decision_ref"],
            "budget_reservation_ref": forged["budget_reservation_ref"],
            "budget_release_ref": forged["budget_release_ref"],
            "budget_settlement_ref": forged["budget_settlement_ref"],
            "evidence_refs": forged["evidence_refs"],
            "reason_refs": forged["reason_refs"],
        },
    )
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-artifact-transfer",
        {key: value for key, value in forged.items() if key != "receipt_ref"},
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_EXTERNAL_RECEIPT_REF_MISMATCH",
    ):
        GovernedArtifactTransferReceipt.model_validate(forged)


def test_artifact_non_preflight_receipt_requires_kernel_context(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="kernel-context-required",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    result = service.execute(
        _exact(request, recipe),
        injected_download_payload=bytearray(b"bounded artifact"),
    )
    forged = result.receipt.model_dump(mode="json")
    forged.update(
        {
            "status": "failed",
            "external_action_state": "failed",
            "external_action_receipt_ref": None,
            "approval_validation_ref": None,
            "authority_decision_ref": None,
            "budget_reservation_ref": None,
            "budget_release_ref": None,
            "budget_settlement_ref": None,
            "content_fingerprint_ref": None,
            "quarantine_projection_ref": None,
            "evidence_refs": [],
            "reason_refs": [
                "reason-ref:governed-artifact:transfer-preparation-failed"
            ],
            "replayed": False,
        }
    )
    identity_payload = {
        key: value
        for key, value in forged.items()
        if key not in {"receipt_ref", "budget_release_ref"}
    }
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-artifact-transfer",
        identity_payload,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_EXTERNAL_PROOF_CONTEXT_REQUIRED",
    ):
        GovernedArtifactTransferReceipt.model_validate(forged)


def test_artifact_non_preflight_rejects_orphan_kernel_proof(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="non-preflight-orphan-proof",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    result = service.execute(
        _exact(request, recipe),
        injected_download_payload=bytearray(b"bounded artifact"),
    )
    forged = result.receipt.model_dump(mode="json")
    forged.update(
        {
            "status": "failed",
            "external_action_state": "failed",
            "external_action_receipt_ref": None,
            "approval_validation_ref": None,
            "authority_decision_ref": None,
            "budget_reservation_ref": None,
            "budget_release_ref": stable_governed_browser_ref(
                "budget-release-ref:governed-artifact",
                {"case": "non-preflight-orphan-proof"},
            ),
            "budget_settlement_ref": None,
            "content_fingerprint_ref": None,
            "quarantine_projection_ref": None,
            "evidence_refs": [],
            "reason_refs": [
                "reason-ref:governed-artifact:transfer-preparation-failed"
            ],
            "replayed": False,
        }
    )
    _rehash_receipt(forged)

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_EXTERNAL_PROOF_CONTEXT_INVALID",
    ):
        GovernedArtifactTransferReceipt.model_validate(forged)


def test_artifact_preflight_rejects_orphan_kernel_proof(tmp_path: Path) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="preflight-orphan-proof",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    forged = service.execute(
        _exact(request, recipe).model_copy(
            update={
                "recipe_ref": (
                    "artifact-transfer-recipe-ref:governed-browser:unknown"
                )
            }
        )
    ).receipt.model_dump(mode="json")
    forged["budget_release_ref"] = stable_governed_browser_ref(
        "budget-release-ref:governed-artifact",
        {"case": "preflight-orphan-proof"},
    )
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-artifact-transfer",
        {key: value for key, value in forged.items() if key != "receipt_ref"},
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_PREFLIGHT_EXTERNAL_PROOF_DENIED",
    ):
        GovernedArtifactTransferReceipt.model_validate(forged)


def test_artifact_receipt_rejects_kernel_state_status_mismatch(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="state-status-mismatch",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    forged = service.execute(
        _exact(request, recipe),
        injected_download_payload=bytearray(b"bounded artifact"),
    ).receipt.model_dump(mode="json")
    forged["status"] = "failed"
    forged["content_fingerprint_ref"] = None
    forged["quarantine_projection_ref"] = None
    identity_payload = {
        key: value
        for key, value in forged.items()
        if key not in {"receipt_ref", "budget_release_ref"}
    }
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-artifact-transfer",
        identity_payload,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_RECEIPT_STATE_MISMATCH",
    ):
        GovernedArtifactTransferReceipt.model_validate(forged)


def test_artifact_replayed_content_free_requires_succeeded_kernel_state(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="replay-state-mismatch",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    exact = _exact(request, recipe)
    service.execute(
        exact,
        injected_download_payload=bytearray(b"bounded artifact"),
    )
    forged = service.execute(
        exact,
        injected_download_payload=bytearray(b"replayed artifact"),
    ).receipt.model_dump(mode="json")
    assert forged["status"] == "replayed_content_free"
    forged["external_action_state"] = "failed"
    identity_payload = {
        key: value
        for key, value in forged.items()
        if key not in {"receipt_ref", "budget_release_ref"}
    }
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-artifact-transfer",
        identity_payload,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_REPLAY_FLAG_REQUIRED",
    ):
        GovernedArtifactTransferReceipt.model_validate(forged)


def test_artifact_replayed_success_rejects_standalone_rehashed_scope_forgery(
    tmp_path: Path,
) -> None:
    forged, context = _download_replay_proof(
        tmp_path,
        suffix="replay-evidence-scope",
    )
    assert forged["status"] == "replayed_content_free"
    original_evidence_refs = list(forged["evidence_refs"])
    forged["artifact_ref"] = governed_artifact_ref(
        source_ref=_pinned(
            "artifact-source-ref:governed-browser",
            suffix="other-replay-artifact",
        ),
        declared_media_type=GovernedArtifactMediaType.text_plain,
    )
    forged["quarantine_ref"] = governed_artifact_quarantine_ref(
        origin_ref=str(forged["origin_ref"]),
        artifact_ref=str(forged["artifact_ref"]),
        download_transaction_ref=str(forged["download_transaction_ref"]),
    )
    assert forged["evidence_refs"] == original_evidence_refs
    assert forged["evidence_refs"][:2] != [
        forged["artifact_ref"],
        forged["quarantine_ref"],
    ]
    _rehash_receipt(forged)

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_REPLAY_SCOPE_ENVELOPE_MISMATCH",
    ):
        GovernedArtifactTransferReceipt.model_validate(
            forged,
            context=replay_validation_context(context),
        )
    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_REQUIRED",
    ):
        GovernedArtifactTransferReceipt.model_validate(forged)


@pytest.mark.parametrize("operation", ("download", "upload"))
def test_artifact_replay_requires_exact_durable_provenance_context(
    tmp_path: Path,
    operation: str,
) -> None:
    payload, context = (
        _download_replay_proof(tmp_path, suffix="exact-download-context")
        if operation == "download"
        else _upload_replay_proof(tmp_path, suffix="exact-upload-context")
    )

    exact = GovernedArtifactTransferReceipt.model_validate(
        payload,
        context=replay_validation_context(context),
    )
    assert exact.replayed is True
    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_REQUIRED",
    ):
        GovernedArtifactTransferReceipt.model_validate(payload)


@pytest.mark.parametrize(
    "terminal_state",
    (
        ExternalActionState.blocked,
        ExternalActionState.failed,
        ExternalActionState.outcome_ambiguous,
    ),
)
def test_artifact_terminal_replay_reconstructs_exact_operation_evidence(
    tmp_path: Path,
    terminal_state: ExternalActionState,
) -> None:
    payload, context, expected_evidence = _artifact_terminal_replay_proof(
        tmp_path,
        terminal_state=terminal_state,
    )

    reconstructed = GovernedArtifactTransferReceipt.model_validate(
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
def test_artifact_terminal_replay_rejects_arbitrary_non_success_evidence(
    tmp_path: Path,
    terminal_state: ExternalActionState,
) -> None:
    service, exact = _seed_arbitrary_artifact_terminal_evidence(
        tmp_path,
        terminal_state=terminal_state,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
    ):
        service.execute(
            exact,
            injected_download_payload=bytearray(b"replay-only"),
        )


@pytest.mark.parametrize(
    ("operation", "evidence_index"),
    (
        ("download", 0),
        ("download", 1),
        ("download", 2),
        ("download", 3),
        ("download", 4),
        ("upload", 0),
        ("upload", 1),
        ("upload", 2),
        ("upload", 3),
        ("upload", 4),
        ("upload", 5),
    ),
)
def test_artifact_replay_rejects_every_rehashed_evidence_field_tamper(
    tmp_path: Path,
    operation: str,
    evidence_index: int,
) -> None:
    payload, context = (
        _download_replay_proof(
            tmp_path,
            suffix=f"field-download-{evidence_index}",
        )
        if operation == "download"
        else _upload_replay_proof(
            tmp_path,
            suffix=f"field-upload-{evidence_index}",
        )
    )
    evidence_refs = list(payload["evidence_refs"])
    evidence_refs[evidence_index] = stable_governed_browser_ref(
        "tampered-evidence-ref:governed-artifact",
        {
            "operation": operation,
            "evidence_index": evidence_index,
        },
    )
    payload["evidence_refs"] = evidence_refs
    _rehash_external_and_artifact_receipt(payload)

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH",
    ):
        GovernedArtifactTransferReceipt.model_validate(
            payload,
            context=replay_validation_context(context),
        )


@pytest.mark.parametrize(
    ("operation", "mutation"),
    (
        ("download", "reverse"),
        ("download", "drop"),
        ("download", "append"),
        ("download", "duplicate"),
        ("upload", "reverse"),
        ("upload", "drop"),
        ("upload", "append"),
        ("upload", "duplicate"),
    ),
)
def test_artifact_replay_rejects_rehashed_evidence_order_and_arity_tamper(
    tmp_path: Path,
    operation: str,
    mutation: str,
) -> None:
    payload, context = (
        _download_replay_proof(
            tmp_path,
            suffix=f"shape-download-{mutation}",
        )
        if operation == "download"
        else _upload_replay_proof(
            tmp_path,
            suffix=f"shape-upload-{mutation}",
        )
    )
    evidence_refs = list(payload["evidence_refs"])
    if mutation == "reverse":
        evidence_refs.reverse()
    elif mutation == "drop":
        evidence_refs.pop()
    elif mutation == "append":
        evidence_refs.append(
            stable_governed_browser_ref(
                "tampered-evidence-ref:governed-artifact",
                {"operation": operation, "mutation": mutation},
            )
        )
    else:
        evidence_refs.append(evidence_refs[-1])
    payload["evidence_refs"] = evidence_refs
    _rehash_external_and_artifact_receipt(payload)

    with pytest.raises(
        ValueError,
        match=(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH"
            "|GOVERNED_ARTIFACT_SUCCESS_KERNEL_PROOF_REQUIRED"
        ),
    ):
        GovernedArtifactTransferReceipt.model_validate(
            payload,
            context=replay_validation_context(context),
        )


def test_artifact_replay_rejects_cross_operation_and_transaction_substitution(
    tmp_path: Path,
) -> None:
    download_a, download_context_a = _download_replay_proof(
        tmp_path,
        suffix="cross-download-a",
    )
    download_b, _ = _download_replay_proof(
        tmp_path,
        suffix="cross-download-b",
    )
    upload, upload_context = _upload_replay_proof(
        tmp_path,
        suffix="cross-upload",
    )

    for payload, context, error in (
        (
            download_b,
            download_context_a,
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_OPERATION_MISMATCH"
            "|GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH",
        ),
        (
            upload,
            download_context_a,
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_LANE_MISMATCH",
        ),
        (
            download_a,
            upload_context,
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_LANE_MISMATCH",
        ),
    ):
        with pytest.raises(ValueError, match=error):
            GovernedArtifactTransferReceipt.model_validate(
                payload,
                context=replay_validation_context(context),
            )


@pytest.mark.parametrize(
    ("operation", "evidence_index"),
    tuple(("download", index) for index in range(5))
    + tuple(("upload", index) for index in range(6)),
)
def test_artifact_durable_replay_rejects_every_rehashed_evidence_field_tamper(
    tmp_path: Path,
    operation: str,
    evidence_index: int,
) -> None:
    service, exact, recipe, _, kernel_path, _ = (
        _seed_download_success_replay(
            tmp_path,
            suffix=f"durable-field-download-{evidence_index}",
        )
        if operation == "download"
        else _seed_upload_success_replay(
            tmp_path,
            suffix=f"durable-field-upload-{evidence_index}",
        )
    )
    terminal = _read_terminal_kernel_receipt(
        kernel_path,
        transaction_ref=recipe.transaction_ref,
    )
    evidence_refs = list(terminal["evidence_refs"])
    evidence_prefix, separator, _ = evidence_refs[evidence_index].rpartition(
        ":sha256:"
    )
    assert separator == ":sha256:"
    evidence_refs[evidence_index] = stable_governed_browser_ref(
        evidence_prefix,
        {"operation": operation, "evidence_index": evidence_index},
    )
    _rewrite_terminal_kernel_evidence(
        kernel_path,
        transaction_ref=recipe.transaction_ref,
        evidence_refs=evidence_refs,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
    ):
        service.execute(exact)


@pytest.mark.parametrize(
    ("operation", "mutation"),
    (
        ("download", "reverse"),
        ("download", "drop"),
        ("download", "append"),
        ("download", "duplicate"),
        ("upload", "reverse"),
        ("upload", "drop"),
        ("upload", "append"),
        ("upload", "duplicate"),
    ),
)
def test_artifact_durable_replay_rejects_rehashed_order_and_arity_tamper(
    tmp_path: Path,
    operation: str,
    mutation: str,
) -> None:
    service, exact, recipe, _, kernel_path, _ = (
        _seed_download_success_replay(
            tmp_path,
            suffix=f"durable-shape-download-{mutation}",
        )
        if operation == "download"
        else _seed_upload_success_replay(
            tmp_path,
            suffix=f"durable-shape-upload-{mutation}",
        )
    )
    terminal = _read_terminal_kernel_receipt(
        kernel_path,
        transaction_ref=recipe.transaction_ref,
    )
    evidence_refs = list(terminal["evidence_refs"])
    if mutation == "reverse":
        evidence_refs.reverse()
    elif mutation == "drop":
        evidence_refs.pop()
    elif mutation == "append":
        evidence_refs.append(
            stable_governed_browser_ref(
                "substituted-evidence-ref:governed-artifact",
                {"operation": operation, "mutation": mutation},
            )
        )
    else:
        evidence_refs.append(evidence_refs[-1])
    _rewrite_terminal_kernel_evidence(
        kernel_path,
        transaction_ref=recipe.transaction_ref,
        evidence_refs=evidence_refs,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
    ):
        service.execute(exact)


def test_artifact_durable_replay_rejects_correlated_download_triple_tamper(
    tmp_path: Path,
) -> None:
    service, exact, recipe, store, kernel_path, result = (
        _seed_download_success_replay(
            tmp_path,
            suffix="durable-correlated-download",
        )
    )
    assert result.quarantine is not None
    foreign_fingerprint_ref = stable_governed_browser_ref(
        "content-fingerprint-ref:governed-browser",
        {"case": "correlated-terminal-row-tamper"},
    )
    foreign_inspection = artifact_module.GovernedArtifactInspection(
        declared_media_type=result.quarantine.declared_media_type,
        byte_count=result.quarantine.byte_count,
        content_fingerprint_ref=foreign_fingerprint_ref,
    )
    foreign_quarantine = artifact_module._build_exact_quarantine(
        recipe,
        foreign_inspection,
    )
    foreign_proof = artifact_module._build_service_proof(
        recipe,
        foreign_quarantine,
    )
    _rewrite_terminal_kernel_evidence(
        kernel_path,
        transaction_ref=recipe.transaction_ref,
        evidence_refs=[
            recipe.artifact_ref,
            recipe.quarantine_ref,
            foreign_fingerprint_ref,
            foreign_quarantine.quarantine_projection_ref,
            foreign_proof.proof_ref,
        ],
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
    ):
        service.execute(exact)
    assert store.inspect(
        quarantine_ref=recipe.quarantine_ref,
        declared_media_type=GovernedArtifactMediaType(recipe.declared_media_type),
        max_bytes=recipe.max_bytes,
        expected_content_fingerprint_ref=(
            result.quarantine.content_fingerprint_ref
        ),
    ).content_fingerprint_ref == result.quarantine.content_fingerprint_ref


def test_artifact_durable_replay_rejects_foreign_valid_upload_plan(
    tmp_path: Path,
) -> None:
    service, exact, recipe, _, kernel_path, result = _seed_upload_success_replay(
        tmp_path,
        suffix="durable-foreign-upload-plan",
    )
    assert result.upload_plan is not None
    foreign_payload = result.upload_plan.model_dump(mode="python")
    foreign_payload["transfer_surface_ref"] = stable_governed_browser_ref(
        "artifact-transfer-surface-ref:governed-browser",
        {"case": "foreign-valid-upload-plan"},
    )
    provisional = type(result.upload_plan).model_construct(**foreign_payload)
    foreign_payload["plan_ref"] = stable_governed_browser_ref(
        "artifact-upload-plan-ref:governed-browser",
        provisional.model_dump(mode="json", exclude={"plan_ref"}),
    )
    foreign_plan = type(result.upload_plan).model_validate(foreign_payload)
    terminal = _read_terminal_kernel_receipt(
        kernel_path,
        transaction_ref=recipe.transaction_ref,
    )
    evidence_refs = list(terminal["evidence_refs"])
    evidence_refs[-1] = foreign_plan.plan_ref
    _rewrite_terminal_kernel_evidence(
        kernel_path,
        transaction_ref=recipe.transaction_ref,
        evidence_refs=evidence_refs,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
    ):
        service.execute(exact)


def test_artifact_durable_replay_rejects_cross_operation_substitution(
    tmp_path: Path,
) -> None:
    download = _seed_download_success_replay(
        tmp_path,
        suffix="durable-cross-operation-download",
    )
    upload = _seed_upload_success_replay(
        tmp_path,
        suffix="durable-cross-operation-upload",
    )
    download_service, download_exact, download_recipe, _, download_path, _ = (
        download
    )
    upload_service, upload_exact, upload_recipe, _, upload_path, _ = upload
    download_evidence = list(
        _read_terminal_kernel_receipt(
            download_path,
            transaction_ref=download_recipe.transaction_ref,
        )["evidence_refs"]
    )
    upload_evidence = list(
        _read_terminal_kernel_receipt(
            upload_path,
            transaction_ref=upload_recipe.transaction_ref,
        )["evidence_refs"]
    )
    _rewrite_terminal_kernel_evidence(
        download_path,
        transaction_ref=download_recipe.transaction_ref,
        evidence_refs=upload_evidence,
    )
    _rewrite_terminal_kernel_evidence(
        upload_path,
        transaction_ref=upload_recipe.transaction_ref,
        evidence_refs=download_evidence,
    )

    for service, exact in (
        (download_service, download_exact),
        (upload_service, upload_exact),
    ):
        with pytest.raises(
            ValueError,
            match="GOVERNED_ARTIFACT_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
        ):
            service.execute(exact)


@pytest.mark.parametrize("operation", ("download", "upload"))
def test_artifact_durable_replay_rejects_cross_transaction_substitution(
    tmp_path: Path,
    operation: str,
) -> None:
    seed = (
        _seed_download_success_replay
        if operation == "download"
        else _seed_upload_success_replay
    )
    primary = seed(tmp_path, suffix=f"durable-cross-transaction-{operation}-a")
    foreign = seed(tmp_path, suffix=f"durable-cross-transaction-{operation}-b")
    service, exact, recipe, _, kernel_path, _ = primary
    _, _, foreign_recipe, _, foreign_path, _ = foreign
    foreign_evidence = list(
        _read_terminal_kernel_receipt(
            foreign_path,
            transaction_ref=foreign_recipe.transaction_ref,
        )["evidence_refs"]
    )
    _rewrite_terminal_kernel_evidence(
        kernel_path,
        transaction_ref=recipe.transaction_ref,
        evidence_refs=foreign_evidence,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
    ):
        service.execute(exact)


@pytest.mark.parametrize(
    ("operation", "durable_state"),
    (
        ("download", "valid"),
        ("download", "payload-missing"),
        ("download", "proof-missing"),
        ("download", "payload-drift"),
        ("download", "proof-drift"),
        ("upload", "valid"),
        ("upload", "payload-missing"),
        ("upload", "payload-drift"),
    ),
)
def test_artifact_replay_revalidates_exact_durable_quarantine_evidence(
    tmp_path: Path,
    operation: str,
    durable_state: str,
) -> None:
    service, exact, recipe, store, _, _ = (
        _seed_download_success_replay(
            tmp_path,
            suffix=f"durable-control-download-{durable_state}",
        )
        if operation == "download"
        else _seed_upload_success_replay(
            tmp_path,
            suffix=f"durable-control-upload-{durable_state}",
        )
    )
    payload_path = store._quarantine / store._filename(recipe.quarantine_ref)
    proof_path = store._quarantine / store._proof_filename(recipe.quarantine_ref)
    if durable_state == "payload-missing":
        payload_path.unlink()
    elif durable_state == "proof-missing":
        proof_path.unlink()
    elif durable_state == "payload-drift":
        payload_path.write_bytes(b"drifted bounded artifact")
    elif durable_state == "proof-drift":
        proof_path.write_text("{}", encoding="utf-8")

    if durable_state == "valid":
        replay = service.execute(exact)
        assert replay.receipt.replayed is True
        assert replay.receipt.status == "replayed_content_free"
        assert replay.quarantine is None
        assert replay.upload_plan is None
    else:
        with pytest.raises(
            ValueError,
            match="GOVERNED_ARTIFACT_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
        ):
            service.execute(exact)


def test_artifact_replay_uses_exact_store_readers_not_instance_shadows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exact, _, store, _, _ = _seed_download_success_replay(
        tmp_path,
        suffix="durable-store-reader-shadow",
    )

    def shadowed_reader(**_kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("instance-shadowed durable reader was invoked")

    monkeypatch.setattr(store, "inspect", shadowed_reader)
    monkeypatch.setattr(store, "_inspect_service_proof", shadowed_reader)

    replay = service.execute(exact)

    assert replay.receipt.replayed is True
    assert replay.receipt.status == "replayed_content_free"


@pytest.mark.parametrize(
    "attribute",
    (
        "binding_ref",
        "_root",
        "_quarantine",
        "_root_identity",
        "_quarantine_identity",
    ),
)
def test_artifact_replay_rejects_construction_binding_attribute_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    attribute: str,
) -> None:
    service, exact, recipe, store, _, _ = _seed_download_success_replay(
        tmp_path,
        suffix=f"durable-store-binding-{attribute}",
    )
    kernel = service._kernel
    kernel_execution = artifact_module._artifact_transfer_kernel_execution(
        exact.execution_request,
        recipe_ref=recipe.recipe_ref,
    )
    replay_receipt = kernel.replay_if_terminal(kernel_execution)
    assert replay_receipt is not None
    service_binding = (
        artifact_module._require_artifact_transfer_service_binding(service)
    )
    if attribute == "binding_ref":
        replacement: object = stable_governed_browser_ref(
            "artifact-quarantine-store-ref:governed-browser",
            {"case": "binding-substitution"},
        )
    elif attribute in {"_root", "_quarantine"}:
        replacement = tmp_path / f"foreign-{attribute}"
    else:
        identity = getattr(store, attribute)
        replacement = (identity[0], identity[1] + 1)
    monkeypatch.setattr(store, attribute, replacement)

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
    ):
        artifact_module._artifact_replay_validation_context(
            kernel=kernel,
            expected_execution=kernel_execution,
            recipe=recipe,
            replay_receipt=replay_receipt,
            service_binding=service_binding,
        )


def test_artifact_replay_rejects_complete_quarantine_source_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exact, recipe, store, _, _ = _seed_download_success_replay(
        tmp_path,
        suffix="durable-complete-store-substitution",
    )
    foreign_store = GovernedArtifactQuarantineStore(tmp_path / "foreign-store")
    kernel = service._kernel
    kernel_execution = artifact_module._artifact_transfer_kernel_execution(
        exact.execution_request,
        recipe_ref=recipe.recipe_ref,
    )
    replay_receipt = kernel.replay_if_terminal(kernel_execution)
    assert replay_receipt is not None
    service_binding = (
        artifact_module._require_artifact_transfer_service_binding(service)
    )
    for attribute in (
        "_root",
        "_quarantine",
        "_root_identity",
        "_quarantine_identity",
    ):
        monkeypatch.setattr(store, attribute, getattr(foreign_store, attribute))

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
    ):
        artifact_module._artifact_replay_validation_context(
            kernel=kernel,
            expected_execution=kernel_execution,
            recipe=recipe,
            replay_receipt=replay_receipt,
            service_binding=service_binding,
        )


@pytest.mark.parametrize(
    "durable_state",
    (
        "source-ledger-missing",
        "source-row-missing",
        "source-row-state-drift",
        "source-terminal-binding-missing",
        "source-service-proof-missing",
    ),
)
def test_upload_replay_requires_exact_durable_source_terminal_attestation(
    tmp_path: Path,
    durable_state: str,
) -> None:
    suffix = f"source-terminal-attestation-{durable_state}"
    service, exact, recipe, store, _, _ = _seed_upload_success_replay(
        tmp_path,
        suffix=suffix,
    )
    source_kernel_path = tmp_path / f"{suffix}-download-kernel"
    source_ledger_path = source_kernel_path / "transactions.sqlite3"
    if durable_state == "source-ledger-missing":
        source_ledger_path.unlink()
    elif durable_state == "source-row-missing":
        with sqlite3.connect(source_ledger_path) as connection:
            changed = connection.execute(
                "DELETE FROM governed_external_actions "
                "WHERE transaction_ref = ?",
                (recipe.download_transaction_ref,),
            ).rowcount
            connection.commit()
        assert changed == 1
    elif durable_state == "source-row-state-drift":
        with sqlite3.connect(source_ledger_path) as connection:
            changed = connection.execute(
                "UPDATE governed_external_actions SET state = ? "
                "WHERE transaction_ref = ?",
                (
                    ExternalActionState.failed.value,
                    recipe.download_transaction_ref,
                ),
            ).rowcount
            connection.commit()
        assert changed == 1
    elif durable_state == "source-terminal-binding-missing":
        assert recipe.source_download_receipt_ref is not None
        (
            source_kernel_path
            / ".transactions.sqlite3.operation-proofs"
            / "terminal-bindings"
            / _terminal_binding_filename(recipe.source_download_receipt_ref)
        ).unlink()
    else:
        (
            store._quarantine
            / store._proof_filename(recipe.quarantine_ref)
        ).unlink()

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
    ):
        service.execute(exact)


@pytest.mark.parametrize("evidence_index", range(5))
def test_upload_replay_rejects_every_rehashed_source_terminal_evidence_tamper(
    tmp_path: Path,
    evidence_index: int,
) -> None:
    suffix = f"source-terminal-field-{evidence_index}"
    service, exact, recipe, _, _, _ = _seed_upload_success_replay(
        tmp_path,
        suffix=suffix,
    )
    source_kernel_path = tmp_path / f"{suffix}-download-kernel"
    terminal = _read_terminal_kernel_receipt(
        source_kernel_path,
        transaction_ref=recipe.download_transaction_ref,
    )
    evidence_refs = list(terminal["evidence_refs"])
    prefix, separator, _ = evidence_refs[evidence_index].rpartition(":sha256:")
    assert separator == ":sha256:"
    evidence_refs[evidence_index] = stable_governed_browser_ref(
        prefix,
        {
            "case": "source-terminal-field-tamper",
            "evidence_index": evidence_index,
        },
    )
    _rewrite_terminal_kernel_evidence(
        source_kernel_path,
        transaction_ref=recipe.download_transaction_ref,
        evidence_refs=evidence_refs,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
    ):
        service.execute(exact)


@pytest.mark.parametrize(
    "mutation",
    ("reverse", "drop", "append", "duplicate"),
)
def test_upload_replay_rejects_rehashed_source_terminal_order_and_arity_tamper(
    tmp_path: Path,
    mutation: str,
) -> None:
    suffix = f"source-terminal-shape-{mutation}"
    service, exact, recipe, _, _, _ = _seed_upload_success_replay(
        tmp_path,
        suffix=suffix,
    )
    source_kernel_path = tmp_path / f"{suffix}-download-kernel"
    terminal = _read_terminal_kernel_receipt(
        source_kernel_path,
        transaction_ref=recipe.download_transaction_ref,
    )
    evidence_refs = list(terminal["evidence_refs"])
    if mutation == "reverse":
        evidence_refs.reverse()
    elif mutation == "drop":
        evidence_refs.pop()
    elif mutation == "append":
        evidence_refs.append(
            stable_governed_browser_ref(
                "source-terminal-extra-ref:governed-browser",
                {"case": "source-terminal-arity-tamper"},
            )
        )
    else:
        evidence_refs.append(evidence_refs[-1])
    _rewrite_terminal_kernel_evidence(
        source_kernel_path,
        transaction_ref=recipe.download_transaction_ref,
        evidence_refs=evidence_refs,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
    ):
        service.execute(exact)


@pytest.mark.parametrize(
    "substitution",
    ("cross-operation", "cross-transaction"),
)
def test_upload_replay_rejects_rehashed_source_terminal_substitution(
    tmp_path: Path,
    substitution: str,
) -> None:
    suffix = f"source-terminal-substitution-{substitution}"
    service, exact, recipe, _, upload_kernel_path, _ = (
        _seed_upload_success_replay(
            tmp_path,
            suffix=suffix,
        )
    )
    source_kernel_path = tmp_path / f"{suffix}-download-kernel"
    if substitution == "cross-operation":
        substituted_evidence = list(
            _read_terminal_kernel_receipt(
                upload_kernel_path,
                transaction_ref=recipe.transaction_ref,
            )["evidence_refs"]
        )
    else:
        foreign_suffix = f"{suffix}-foreign"
        _, _, foreign_recipe, _, _, _ = _seed_upload_success_replay(
            tmp_path,
            suffix=foreign_suffix,
        )
        substituted_evidence = list(
            _read_terminal_kernel_receipt(
                tmp_path / f"{foreign_suffix}-download-kernel",
                transaction_ref=foreign_recipe.download_transaction_ref,
            )["evidence_refs"]
        )
    _rewrite_terminal_kernel_evidence(
        source_kernel_path,
        transaction_ref=recipe.download_transaction_ref,
        evidence_refs=substituted_evidence,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
    ):
        service.execute(exact)


@pytest.mark.parametrize(
    "attribute",
    (
        "_registry",
        "_kernel",
        "_store",
        "_source_download_kernel",
        "_source_download_registry",
        "_source_download_request",
        "_clock",
    ),
)
def test_artifact_service_rejects_construction_dependency_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    attribute: str,
) -> None:
    service, exact, recipe, store, _, _ = _seed_upload_success_replay(
        tmp_path,
        suffix=f"service-dependency-substitution-{attribute}",
    )
    binding = artifact_module._require_artifact_transfer_service_binding(service)
    if attribute == "_registry":
        replacement: object = (
            artifact_module.GovernedArtifactTransferRecipeRegistry([recipe])
        )
    elif attribute == "_kernel":
        replacement = binding.source_download_kernel
    elif attribute == "_store":
        replacement = GovernedArtifactQuarantineStore(store._root)
    elif attribute == "_source_download_kernel":
        replacement = binding.kernel
    elif attribute == "_source_download_registry":
        replacement = binding.registry
    elif attribute == "_source_download_request":
        replacement = exact
    else:
        def replacement_clock():  # type: ignore[no-untyped-def]
            return utc_now()

        replacement = replacement_clock
    assert replacement is not None
    monkeypatch.setattr(service, attribute, replacement)

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_SERVICE_BINDING_INVALID",
    ):
        service.execute(exact)


def test_artifact_service_rejects_bound_source_request_content_drift(
    tmp_path: Path,
) -> None:
    service, exact, _, _, _, _ = _seed_upload_success_replay(
        tmp_path,
        suffix="bound-source-request-content-drift",
    )
    source_request = service._source_download_request
    assert source_request is not None
    original_recipe_ref = source_request.recipe_ref
    object.__setattr__(
        source_request,
        "recipe_ref",
        _pinned(
            "artifact-transfer-recipe-ref:governed-browser",
            suffix="bound-source-request-content-drift",
        ),
    )
    try:
        with pytest.raises(
            ValueError,
            match="GOVERNED_ARTIFACT_SERVICE_BINDING_INVALID",
        ):
            service.execute(exact)
    finally:
        object.__setattr__(
            source_request,
            "recipe_ref",
            original_recipe_ref,
        )


def test_upload_replay_uses_exact_bound_methods_not_instance_shadows(
    tmp_path: Path,
) -> None:
    service, exact, _, _, _, _ = _seed_upload_success_replay(
        tmp_path,
        suffix="exact-bound-methods",
    )
    binding = artifact_module._require_artifact_transfer_service_binding(service)
    assert binding.source_download_kernel is not None
    assert binding.source_download_registry is not None
    assert binding.source_download_request is not None

    def shadowed_method(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("instance-shadowed method was invoked")

    shadowed_objects = (
        (service, "_execute"),
        (exact, "model_dump"),
        (binding.registry, "resolve"),
        (binding.kernel, "replay_if_terminal"),
        (binding.source_download_registry, "resolve"),
        (binding.source_download_kernel, "attest_terminal_replay"),
        (binding.source_download_request, "model_dump"),
        (binding.source_download_request, "model_dump_json"),
    )
    try:
        for target, attribute in shadowed_objects:
            object.__getattribute__(target, "__dict__")[attribute] = (
                shadowed_method
            )
        replay = service.execute(exact)
    finally:
        for target, attribute in shadowed_objects:
            object.__getattribute__(target, "__dict__").pop(attribute, None)

    assert replay.receipt.replayed is True
    assert replay.receipt.status == "replayed_content_free"


def test_download_execution_uses_exact_store_methods_not_instance_shadows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="exact-live-store-methods",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    shadow_calls: list[str] = []

    def shadowed_method(*_args: object, **_kwargs: object) -> object:
        shadow_calls.append("redirected")
        raise AssertionError("instance-shadowed store method was invoked")

    monkeypatch.setattr(store, "quarantine", shadowed_method)
    monkeypatch.setattr(store, "_record_service_proof", shadowed_method)

    result = service.execute(
        _exact(request, recipe),
        injected_download_payload=bytearray(b"exact live store payload"),
    )

    assert result.receipt.status == "quarantined"
    assert shadow_calls == []


def test_artifact_service_binding_failure_still_zeroizes_mutable_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exact, recipe, _, _, _ = _seed_download_success_replay(
        tmp_path,
        suffix="binding-failure-zeroization",
    )
    monkeypatch.setattr(
        service,
        "_registry",
        artifact_module.GovernedArtifactTransferRecipeRegistry([recipe]),
    )
    payload = bytearray(b"must be zeroized on binding failure")

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_SERVICE_BINDING_INVALID",
    ):
        service.execute(
            exact,
            injected_download_payload=payload,
        )

    assert payload == bytearray(len(payload))


def test_failed_upload_replay_preserves_legacy_source_independence(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "failed-upload-artifacts")
    download_request, download_recipe, download_registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="failed-upload-source",
    )
    download_service, _, _ = _service(
        tmp_path / "failed-upload-download-kernel",
        store=store,
        request=download_request,
        registry=download_registry,
    )
    downloaded = download_service.execute(
        _exact(download_request, download_recipe),
        injected_download_payload=bytearray(b"failed upload source"),
    )
    assert downloaded.quarantine is not None
    upload_request, upload_recipe, upload_registry = _transfer_context(
        store,
        operation=(
            GovernedArtifactTransferOperation.upload_quarantined_artifact_plan
        ),
        suffix="failed-upload-without-source-dependencies",
        artifact_ref=download_recipe.artifact_ref,
        quarantine_ref=download_recipe.quarantine_ref,
        download_transaction_ref=download_recipe.download_transaction_ref,
        content_fingerprint_ref=downloaded.quarantine.content_fingerprint_ref,
        source_download_receipt_ref=(
            downloaded.receipt.external_action_receipt_ref
        ),
        source_download_recipe_ref=download_recipe.recipe_ref,
    )
    upload_service, _, _ = _service(
        tmp_path / "failed-upload-kernel",
        store=store,
        request=upload_request,
        registry=upload_registry,
    )
    exact = _exact(upload_request, upload_recipe)

    first = upload_service.execute(exact)
    replay = upload_service.execute(exact)

    assert first.receipt.external_action_state == ExternalActionState.failed.value
    assert first.receipt.replayed is False
    assert replay.receipt.external_action_state == ExternalActionState.failed.value
    assert replay.receipt.status == "failed"
    assert replay.receipt.replayed is True
    assert replay.receipt.evidence_refs == first.receipt.evidence_refs
    assert replay.upload_plan is None


def test_successful_upload_replay_does_not_reapply_current_recipe_expiry(
    tmp_path: Path,
) -> None:
    observed_time = [utc_now()]

    def controlled_clock():  # type: ignore[no-untyped-def]
        return observed_time[0]

    store = GovernedArtifactQuarantineStore(tmp_path / "expiry-replay-artifacts")
    download_request, download_recipe, download_registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="expiry-replay-download",
    )
    observed_time[0] = download_recipe.created_at + timedelta(milliseconds=1)
    download_service, download_kernel, _ = _service(
        tmp_path / "expiry-replay-download-kernel",
        store=store,
        request=download_request,
        registry=download_registry,
        clock=controlled_clock,
    )
    downloaded = download_service.execute(
        _exact(download_request, download_recipe),
        injected_download_payload=bytearray(b"expiry replay source"),
    )
    assert downloaded.quarantine is not None
    upload_request, upload_recipe, upload_registry = _transfer_context(
        store,
        operation=(
            GovernedArtifactTransferOperation.upload_quarantined_artifact_plan
        ),
        suffix="expiry-replay-upload",
        artifact_ref=download_recipe.artifact_ref,
        quarantine_ref=download_recipe.quarantine_ref,
        download_transaction_ref=download_recipe.download_transaction_ref,
        content_fingerprint_ref=downloaded.quarantine.content_fingerprint_ref,
        source_download_receipt_ref=(
            downloaded.receipt.external_action_receipt_ref
        ),
        source_download_recipe_ref=download_recipe.recipe_ref,
    )
    observed_time[0] = upload_recipe.created_at + timedelta(milliseconds=1)
    upload_service, _, _ = _service(
        tmp_path / "expiry-replay-upload-kernel",
        store=store,
        request=upload_request,
        registry=upload_registry,
        source_download_kernel=download_kernel,
        source_download_registry=download_registry,
        source_download_request=_exact(download_request, download_recipe),
        clock=controlled_clock,
    )
    exact = _exact(upload_request, upload_recipe)
    first = upload_service.execute(exact)
    assert first.receipt.status == "upload_plan_ready"
    observed_time[0] = max(
        download_recipe.expires_at,
        upload_recipe.expires_at,
    ) + timedelta(seconds=1)

    replay = upload_service.execute(exact)

    assert replay.receipt.replayed is True
    assert replay.receipt.status == "replayed_content_free"
    assert replay.upload_plan is None


@pytest.mark.parametrize(
    "missing_field",
    (
        "external_action_receipt_ref",
        "approval_validation_ref",
        "authority_decision_ref",
        "budget_reservation_ref",
        "budget_settlement_ref",
        "evidence_refs",
    ),
)
def test_artifact_replayed_success_requires_complete_kernel_proof(
    tmp_path: Path,
    missing_field: str,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="proofless-replay",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    exact = _exact(request, recipe)
    service.execute(
        exact,
        injected_download_payload=bytearray(b"bounded artifact"),
    )
    forged = service.execute(
        exact,
        injected_download_payload=bytearray(b"replayed artifact"),
    ).receipt.model_dump(mode="json")
    assert forged["status"] == "replayed_content_free"
    forged[missing_field] = [] if missing_field == "evidence_refs" else None
    if missing_field != "external_action_receipt_ref":
        external_payload = {
            "transaction_ref": forged["transaction_ref"],
            "intent_ref": forged["intent_ref"],
            "binding_ref": forged["binding_ref"],
            "state": forged["external_action_state"],
            "approval_validation_ref": forged["approval_validation_ref"],
            "authority_decision_ref": forged["authority_decision_ref"],
            "budget_reservation_ref": forged["budget_reservation_ref"],
            "budget_settlement_ref": forged["budget_settlement_ref"],
            "evidence_refs": forged["evidence_refs"],
            "reason_refs": forged["reason_refs"],
        }
        if forged["budget_release_ref"] is not None:
            external_payload["budget_release_ref"] = forged["budget_release_ref"]
        forged["external_action_receipt_ref"] = stable_governed_browser_ref(
            "receipt-ref:governed-external-action",
            external_payload,
        )
    _rehash_receipt(forged)

    with pytest.raises(
        ValueError,
        match="GOVERNED_ARTIFACT_SUCCESS_KERNEL_PROOF_REQUIRED",
    ):
        GovernedArtifactTransferReceipt.model_validate(forged)
