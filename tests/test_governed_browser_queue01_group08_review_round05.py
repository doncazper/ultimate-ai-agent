from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path

import pytest

from tests.test_governed_browser_queue01_group01 import _authorized_kernel, _request
from tests.test_governed_browser_queue01_group08 import (
    _exact,
    _pinned,
    _service,
    _transfer_context,
)
from ultimate_ai_agent.core.governed_browser import (
    MAX_GOVERNED_ARTIFACT_BYTES,
    ExactGovernedArtifactQuarantine,
    ExactGovernedArtifactTransferService,
    ExternalActionAuthorityBinding,
    ExternalActionDispatchOutcome,
    ExternalActionDispatchResult,
    ExternalActionExecutionRequest,
    GovernedArtifactMediaType,
    GovernedArtifactPayloadRejected,
    GovernedArtifactQuarantineStore,
    GovernedArtifactServiceProof,
    GovernedArtifactTransferOperation,
    GovernedArtifactTransferRecipe,
    GovernedArtifactTransferRecipeRegistry,
    build_governed_artifact_transfer_recipe,
    governed_artifact_service_proof_ref,
    stable_governed_browser_ref,
)


def _source_projection_and_service_proof(
    recipe: GovernedArtifactTransferRecipe,
    inspection,  # type: ignore[no-untyped-def]
) -> tuple[ExactGovernedArtifactQuarantine, GovernedArtifactServiceProof]:
    projection_payload = {
        "recipe_ref": recipe.recipe_ref,
        "artifact_ref": recipe.artifact_ref,
        "quarantine_ref": recipe.quarantine_ref,
        "download_transaction_ref": recipe.download_transaction_ref,
        "origin_ref": recipe.origin_ref,
        "quarantine_store_ref": recipe.quarantine_store_ref,
        "content_fingerprint_ref": inspection.content_fingerprint_ref,
        "declared_media_type": inspection.declared_media_type,
        "byte_count": inspection.byte_count,
        "expires_at": recipe.expires_at,
    }
    provisional_projection = ExactGovernedArtifactQuarantine.model_construct(
        quarantine_projection_ref=(
            "artifact-quarantine-projection-ref:governed-browser:pending"
        ),
        **projection_payload,
    )
    projection_ref = stable_governed_browser_ref(
        "artifact-quarantine-projection-ref:governed-browser",
        provisional_projection.model_dump(
            mode="json",
            exclude={"quarantine_projection_ref"},
        ),
    )
    projection = ExactGovernedArtifactQuarantine(
        quarantine_projection_ref=projection_ref,
        **projection_payload,
    )
    proof_payload = {
        "recipe_ref": recipe.recipe_ref,
        "origin_ref": recipe.origin_ref,
        "artifact_ref": recipe.artifact_ref,
        "quarantine_ref": recipe.quarantine_ref,
        "download_transaction_ref": recipe.download_transaction_ref,
        "quarantine_projection_ref": projection_ref,
        "content_fingerprint_ref": inspection.content_fingerprint_ref,
        "expires_at": recipe.expires_at,
    }
    proof = GovernedArtifactServiceProof(
        proof_ref=governed_artifact_service_proof_ref(
            recipe_ref=recipe.recipe_ref,
            origin_ref=recipe.origin_ref,
            quarantine_ref=recipe.quarantine_ref,
            quarantine_projection_ref=projection_ref,
            content_fingerprint_ref=inspection.content_fingerprint_ref,
        ),
        **proof_payload,
    )
    return projection, proof


def _rebuild_recipe(
    request,  # type: ignore[no-untyped-def]
    recipe: GovernedArtifactTransferRecipe,
    *,
    expires_at,
) -> GovernedArtifactTransferRecipe:  # type: ignore[no-untyped-def]
    return build_governed_artifact_transfer_recipe(
        request,
        operation=GovernedArtifactTransferOperation(recipe.operation),
        artifact_ref=recipe.artifact_ref,
        quarantine_ref=recipe.quarantine_ref,
        download_transaction_ref=recipe.download_transaction_ref,
        quarantine_store_ref=recipe.quarantine_store_ref,
        transfer_surface_ref=recipe.transfer_surface_ref,
        visibility_proof_ref=recipe.visibility_proof_ref,
        declared_media_type=GovernedArtifactMediaType(recipe.declared_media_type),
        max_bytes=recipe.max_bytes,
        content_fingerprint_ref=recipe.content_fingerprint_ref,
        created_at=recipe.created_at,
        expires_at=expires_at,
        source_download_receipt_ref=recipe.source_download_receipt_ref,
        source_download_recipe_ref=recipe.source_download_recipe_ref,
    )


def test_upload_rejects_generic_receipt_without_recipe_bound_request_fingerprint(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    download_request, download_recipe, download_registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="generic-source-receipt",
    )
    inspection = store.quarantine(
        quarantine_ref=download_recipe.quarantine_ref,
        payload=bytearray(b"preseeded artifact"),
        declared_media_type=GovernedArtifactMediaType.text_plain,
        max_bytes=download_recipe.max_bytes,
    )
    projection, service_proof = _source_projection_and_service_proof(
        download_recipe,
        inspection,
    )
    store._record_service_proof(service_proof)
    download_kernel, _ = _authorized_kernel(
        tmp_path / "download-kernel",
        download_request,
    )
    generic_receipt = download_kernel.execute(
        download_request,
        dispatch=lambda _request: ExternalActionDispatchResult(
            outcome=ExternalActionDispatchOutcome.succeeded,
            evidence_refs=[
                download_recipe.artifact_ref,
                download_recipe.quarantine_ref,
                inspection.content_fingerprint_ref,
                projection.quarantine_projection_ref,
                service_proof.proof_ref,
            ],
            verified=True,
        ),
    )
    upload_request, upload_recipe, upload_registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.upload_quarantined_artifact_plan,
        suffix="generic-source-upload",
        artifact_ref=download_recipe.artifact_ref,
        quarantine_ref=download_recipe.quarantine_ref,
        download_transaction_ref=download_recipe.download_transaction_ref,
        content_fingerprint_ref=inspection.content_fingerprint_ref,
        source_download_receipt_ref=generic_receipt.receipt_ref,
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

    assert result.receipt.status == "failed"
    assert result.upload_plan is None
    assert result.receipt.evidence_refs[0].startswith(
        "evidence-ref:governed-artifact:source-download-receipt-required:"
    )


def test_upload_requires_service_owned_proof_beyond_exact_kernel_evidence(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    download_request, download_recipe, download_registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="arbitrary-source-projection",
    )
    inspection = store.quarantine(
        quarantine_ref=download_recipe.quarantine_ref,
        payload=bytearray(b"preseeded recipe-bound artifact"),
        declared_media_type=GovernedArtifactMediaType.text_plain,
        max_bytes=download_recipe.max_bytes,
    )
    recipe_bound_request = ExternalActionExecutionRequest.model_validate(
        {
            **download_request.model_dump(mode="json"),
            "idempotency_ref": stable_governed_browser_ref(
                "idempotency-ref:governed-artifact-transfer",
                {
                    "source_idempotency_ref": download_request.idempotency_ref,
                    "recipe_ref": download_recipe.recipe_ref,
                },
            ),
        }
    )
    download_kernel, _ = _authorized_kernel(
        tmp_path / "download-kernel",
        recipe_bound_request,
    )
    projection, service_proof = _source_projection_and_service_proof(
        download_recipe,
        inspection,
    )
    generic_receipt = download_kernel.execute(
        recipe_bound_request,
        dispatch=lambda _request: ExternalActionDispatchResult(
            outcome=ExternalActionDispatchOutcome.succeeded,
            evidence_refs=[
                download_recipe.artifact_ref,
                download_recipe.quarantine_ref,
                inspection.content_fingerprint_ref,
                projection.quarantine_projection_ref,
                service_proof.proof_ref,
            ],
            verified=True,
        ),
    )
    upload_request, upload_recipe, upload_registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.upload_quarantined_artifact_plan,
        suffix="arbitrary-source-projection-upload",
        artifact_ref=download_recipe.artifact_ref,
        quarantine_ref=download_recipe.quarantine_ref,
        download_transaction_ref=download_recipe.download_transaction_ref,
        content_fingerprint_ref=inspection.content_fingerprint_ref,
        source_download_receipt_ref=generic_receipt.receipt_ref,
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

    assert result.receipt.status == "failed"
    assert result.upload_plan is None


def test_oversized_payload_is_rejected_before_immutable_snapshot(
    tmp_path: Path,
) -> None:
    class CopyDetectingPayload(bytearray):
        def __bytes__(self) -> bytes:
            raise AssertionError("oversized payload must not be copied")

    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    payload = CopyDetectingPayload(b"x" * (MAX_GOVERNED_ARTIFACT_BYTES + 1))
    with pytest.raises(
        GovernedArtifactPayloadRejected,
        match="SIZE_LIMIT_EXCEEDED",
    ):
        store.quarantine(
            quarantine_ref=_pinned(
                "artifact-quarantine-ref:governed-browser",
                suffix="oversized-precopy",
            ),
            payload=payload,
            declared_media_type=GovernedArtifactMediaType.text_plain,
            max_bytes=MAX_GOVERNED_ARTIFACT_BYTES,
        )


def test_expired_recipe_is_preflight_blocked_without_poisoning_refresh(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, refreshed_recipe, _ = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="expired-preflight",
    )
    expired_recipe = _rebuild_recipe(
        request,
        refreshed_recipe,
        expires_at=refreshed_recipe.created_at + timedelta(seconds=1),
    )
    observed_time = [expired_recipe.expires_at + timedelta(seconds=1)]
    kernel, _ = _authorized_kernel(
        tmp_path / "kernel",
        request,
        clock=lambda: observed_time[0],
    )
    expired_service = ExactGovernedArtifactTransferService(
        registry=GovernedArtifactTransferRecipeRegistry([expired_recipe]),
        kernel=kernel,
        quarantine_store=store,
        clock=lambda: observed_time[0],
    )

    blocked = expired_service.execute(
        _exact(request, expired_recipe),
        injected_download_payload=bytearray(b"expired attempt"),
    )

    assert blocked.receipt.status == "preflight_blocked"
    assert blocked.receipt.reason_refs == [
        "reason-ref:governed-artifact:recipe-expired"
    ]
    with sqlite3.connect(tmp_path / "kernel" / "transactions.sqlite3") as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM governed_external_actions"
        ).fetchone() == (0,)

    refreshed_service = ExactGovernedArtifactTransferService(
        registry=GovernedArtifactTransferRecipeRegistry([refreshed_recipe]),
        kernel=kernel,
        quarantine_store=store,
        clock=lambda: observed_time[0],
    )
    completed = refreshed_service.execute(
        _exact(request, refreshed_recipe),
        injected_download_payload=bytearray(b"refreshed attempt"),
    )
    assert completed.receipt.status == "quarantined"


def test_upload_rejects_an_expired_source_quarantine_recipe(tmp_path: Path) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    download_request, download_recipe, _ = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="expired-source",
    )
    short_download_recipe = _rebuild_recipe(
        download_request,
        download_recipe,
        expires_at=download_recipe.created_at + timedelta(seconds=2),
    )
    download_registry = GovernedArtifactTransferRecipeRegistry([short_download_recipe])
    download_time = short_download_recipe.created_at + timedelta(seconds=1)
    download_service, download_kernel, _ = _service(
        tmp_path / "download-kernel",
        store=store,
        request=download_request,
        registry=download_registry,
        clock=lambda: download_time,
    )
    downloaded = download_service.execute(
        _exact(download_request, short_download_recipe),
        injected_download_payload=bytearray(b"expiring source"),
    )
    assert downloaded.quarantine is not None
    upload_request, upload_recipe, upload_registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.upload_quarantined_artifact_plan,
        suffix="expired-source-upload",
        artifact_ref=short_download_recipe.artifact_ref,
        quarantine_ref=short_download_recipe.quarantine_ref,
        download_transaction_ref=short_download_recipe.download_transaction_ref,
        content_fingerprint_ref=downloaded.quarantine.content_fingerprint_ref,
        source_download_receipt_ref=downloaded.receipt.external_action_receipt_ref,
        source_download_recipe_ref=short_download_recipe.recipe_ref,
    )
    upload_time = short_download_recipe.expires_at + timedelta(seconds=1)
    upload_service, _, _ = _service(
        tmp_path / "upload-kernel",
        store=store,
        request=upload_request,
        registry=upload_registry,
        source_download_kernel=download_kernel,
        source_download_registry=download_registry,
        source_download_request=_exact(
            download_request,
            short_download_recipe,
        ),
        clock=lambda: upload_time,
    )

    result = upload_service.execute(_exact(upload_request, upload_recipe))

    assert result.receipt.status == "failed"
    assert result.upload_plan is None


def test_execution_rejects_extra_artifact_transfer_operation_authority(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    _, recipe, _ = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="broadened-operation-authority",
    )
    base_request, _, _ = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="broadened-operation-authority",
    )
    broadened_binding = ExternalActionAuthorityBinding.model_validate(
        {
            **base_request.binding.model_dump(mode="json"),
            "resource_refs": [
                *base_request.binding.resource_refs,
                _pinned(
                    "artifact-transfer-operation-authority-ref:governed-browser",
                    suffix="extra-operation",
                ),
            ],
        }
    )
    broadened_request = _request(broadened_binding)
    persisted_payload = {
        **recipe.model_dump(mode="python"),
        "binding_ref": broadened_binding.binding_ref,
    }
    provisional = GovernedArtifactTransferRecipe.model_construct(
        **persisted_payload,
    )
    persisted_payload["recipe_ref"] = stable_governed_browser_ref(
        "artifact-transfer-recipe-ref:governed-browser",
        provisional.model_dump(mode="json", exclude={"recipe_ref"}),
    )
    persisted_recipe = GovernedArtifactTransferRecipe.model_validate(persisted_payload)
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=broadened_request,
        registry=GovernedArtifactTransferRecipeRegistry([persisted_recipe]),
    )

    result = service.execute(_exact(broadened_request, persisted_recipe))

    assert result.receipt.status == "preflight_blocked"
    assert result.receipt.reason_refs == [
        "reason-ref:governed-artifact:operation-authority-mismatch"
    ]
