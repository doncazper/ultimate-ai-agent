from __future__ import annotations

from pathlib import Path

import pytest

from tests.test_governed_browser_queue01_group08 import (
    _pinned,
    _transfer_context,
)
from ultimate_ai_agent.core.governed_browser import (
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
