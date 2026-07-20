from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

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
    GovernedArtifactPayloadRejected,
    GovernedArtifactQuarantineStore,
    GovernedArtifactTransferOperation,
    GovernedArtifactTransferReceipt,
    build_governed_artifact_transfer_recipe,
    governed_artifact_quarantine_ref,
    governed_artifact_ref,
    stable_governed_browser_ref,
)
from ultimate_ai_agent.core.governed_browser.contracts import (
    governed_receipt_identity_payload,
)


def _rehash_receipt(payload: dict[str, object]) -> dict[str, object]:
    provisional = GovernedArtifactTransferReceipt.model_construct(**payload)
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-artifact-transfer",
        governed_receipt_identity_payload(provisional),
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

    def delayed_quarantine(*, payload: bytearray, **kwargs):  # type: ignore[no-untyped-def]
        dispatched_buffers.append(payload)
        entered.set()
        assert proceed.wait(timeout=2)
        return original_quarantine(payload=payload, **kwargs)

    monkeypatch.setattr(store, "quarantine", delayed_quarantine)
    payload = bytearray(b"bounded timeout artifact")
    expected_payload = bytes(payload)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            service.execute,
            _exact(request, recipe),
            injected_download_payload=payload,
        )
        assert entered.wait(timeout=2)
        result = future.result(timeout=2)

    assert result.receipt.status == "outcome_ambiguous"
    assert payload == bytearray(len(payload))
    assert dispatched_buffers == [bytearray(expected_payload)]
    assert dispatched_buffers[0] is not payload

    proceed.set()
    deadline = time.monotonic() + 2
    while any(dispatched_buffers[0]) and time.monotonic() < deadline:
        time.sleep(0.005)
    assert dispatched_buffers[0] == bytearray(len(dispatched_buffers[0]))


def test_oversized_download_payload_is_rejected_before_owned_copy(
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
