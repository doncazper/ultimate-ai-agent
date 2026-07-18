from __future__ import annotations

from pathlib import Path

import pytest

from tests.test_governed_browser_queue01_group08 import (
    _exact,
    _pinned,
    _service,
    _transfer_context,
)
from ultimate_ai_agent.core.governed_browser import (
    ExactGovernedArtifactTransferResult,
    ExternalActionTargetKind,
    GovernedArtifactMediaType,
    GovernedArtifactQuarantineStore,
    GovernedArtifactTransferOperation,
    GovernedArtifactTransferReceipt,
    build_governed_artifact_transfer_recipe,
    governed_artifact_quarantine_ref,
    governed_artifact_ref,
    stable_governed_browser_ref,
)


def _rehash_receipt(payload: dict[str, object]) -> dict[str, object]:
    provisional = GovernedArtifactTransferReceipt.model_construct(**payload)
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-artifact-transfer",
        provisional.model_dump(mode="json", exclude={"receipt_ref"}),
    )
    return payload


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
        provisional.model_dump(mode="json", exclude={"receipt_ref"}),
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
        provisional.model_dump(mode="json", exclude={"receipt_ref"}),
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
    )
    upload_service, _, _ = _service(
        tmp_path / "upload-kernel",
        store=store,
        request=upload_request,
        registry=upload_registry,
        source_download_kernel=download_kernel,
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


def test_upload_plan_requires_the_bound_source_download_ledger_receipt(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    download_request, download_recipe, download_registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="source-proof-download",
    )
    download_service, _, _ = _service(
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
    )
    upload_service, _, _ = _service(
        tmp_path / "upload-kernel",
        store=store,
        request=upload_request,
        registry=upload_registry,
    )

    result = upload_service.execute(_exact(upload_request, upload_recipe))

    assert result.receipt.status == "failed"
    assert result.receipt.external_action_state == "failed"
    assert result.receipt.evidence_refs[0].startswith(
        "evidence-ref:governed-artifact:source-download-receipt-required:"
    )
    assert result.upload_plan is None
