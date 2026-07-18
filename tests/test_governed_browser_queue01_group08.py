from __future__ import annotations

import os
import stat
from datetime import timedelta
from pathlib import Path

import pytest

from tests.test_governed_browser_queue01_group01 import (
    _authorized_kernel,
    _binding,
    _lease,
    _readiness,
    _ref,
    _request,
)
from ultimate_ai_agent.core.authority import AuthorityCapability, AuthorityDomain
from ultimate_ai_agent.core.governed_browser import (
    MAX_GOVERNED_ARTIFACT_BYTES,
    ExactGovernedArtifactTransferRequest,
    ExactGovernedArtifactTransferResult,
    ExactGovernedArtifactTransferService,
    ExactGovernedArtifactUploadPlan,
    ExternalActionAuthorityBinding,
    ExternalActionTargetKind,
    GovernedArtifactMediaType,
    GovernedArtifactQuarantineStore,
    GovernedArtifactTransferOperation,
    GovernedArtifactTransferRecipeRegistry,
    build_governed_artifact_transfer_recipe,
    governed_artifact_quarantine_ref,
    governed_artifact_ref,
    governed_artifact_transfer_operation_authority_ref,
    governed_artifact_transfer_schema_ref,
    stable_governed_browser_ref,
)
from ultimate_ai_agent.core.time import utc_now


def _pinned(prefix: str, *, suffix: str) -> str:
    return stable_governed_browser_ref(prefix, {"suffix": suffix})


def _transfer_context(
    store: GovernedArtifactQuarantineStore,
    *,
    operation: GovernedArtifactTransferOperation,
    suffix: str,
    artifact_ref: str | None = None,
    quarantine_ref: str | None = None,
    download_transaction_ref: str | None = None,
    content_fingerprint_ref: str | None = None,
    target_kind: ExternalActionTargetKind = ExternalActionTargetKind.local_validation,
    human_present: bool = True,
):  # type: ignore[no-untyped-def]
    base = _binding(
        suffix=suffix,
        target_kind=target_kind,
        human_present=human_present,
    )
    exact_artifact_ref = artifact_ref or governed_artifact_ref(
        source_ref=_pinned(
            "artifact-source-ref:governed-browser",
            suffix=suffix,
        ),
        declared_media_type=GovernedArtifactMediaType.text_plain,
    )
    exact_download_transaction_ref = download_transaction_ref or base.transaction_ref
    exact_quarantine_ref = quarantine_ref or governed_artifact_quarantine_ref(
        origin_ref=base.origin_ref,
        artifact_ref=exact_artifact_ref,
        download_transaction_ref=exact_download_transaction_ref,
    )
    transfer_surface_ref = _pinned(
        "artifact-transfer-surface-ref:governed-browser",
        suffix=suffix,
    )
    visibility_proof_ref = _pinned(
        "visibility-proof-ref:governed-browser",
        suffix=suffix,
    )
    operation_authority_ref = governed_artifact_transfer_operation_authority_ref(
        operation=operation,
        origin_ref=base.origin_ref,
        artifact_ref=exact_artifact_ref,
        quarantine_ref=exact_quarantine_ref,
    )
    schema_ref = governed_artifact_transfer_schema_ref(
        operation=operation,
        artifact_ref=exact_artifact_ref,
        quarantine_ref=exact_quarantine_ref,
        download_transaction_ref=exact_download_transaction_ref,
        declared_media_type=GovernedArtifactMediaType.text_plain,
        max_bytes=1024,
        content_fingerprint_ref=content_fingerprint_ref,
    )
    resources = [
        _ref("resource", suffix),
        operation_authority_ref,
        exact_quarantine_ref,
        store.binding_ref,
        transfer_surface_ref,
        visibility_proof_ref,
    ]
    if content_fingerprint_ref is not None:
        resources.append(content_fingerprint_ref)
    if exact_download_transaction_ref != base.transaction_ref:
        resources.append(exact_download_transaction_ref)
    binding = ExternalActionAuthorityBinding.model_validate(
        {
            **base.model_dump(mode="json"),
            "authority_capability": {
                GovernedArtifactTransferOperation.download_quarantine: (
                    AuthorityCapability.download
                ),
                GovernedArtifactTransferOperation.upload_quarantined_artifact_plan: (
                    AuthorityCapability.upload
                ),
            }[operation],
            "field_schema_ref": schema_ref,
            "artifact_refs": [exact_artifact_ref],
            "resource_refs": resources,
        }
    )
    request = _request(binding)
    created_at = utc_now()
    expires_at = min(
        created_at + timedelta(minutes=5),
        binding.start_deadline - timedelta(seconds=1),
    )
    recipe = build_governed_artifact_transfer_recipe(
        request,
        operation=operation,
        artifact_ref=exact_artifact_ref,
        quarantine_ref=exact_quarantine_ref,
        download_transaction_ref=exact_download_transaction_ref,
        quarantine_store_ref=store.binding_ref,
        transfer_surface_ref=transfer_surface_ref,
        visibility_proof_ref=visibility_proof_ref,
        declared_media_type=GovernedArtifactMediaType.text_plain,
        max_bytes=1024,
        content_fingerprint_ref=content_fingerprint_ref,
        created_at=created_at,
        expires_at=expires_at,
    )
    registry = GovernedArtifactTransferRecipeRegistry([recipe])
    return request, recipe, registry


def _service(
    tmp_path: Path,
    *,
    store: GovernedArtifactQuarantineStore,
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
        ExactGovernedArtifactTransferService(
            registry=registry,
            kernel=kernel,
            quarantine_store=store,
            clock=clock,
        ),
        kernel,
        authority,
    )


def _exact(request, recipe) -> ExactGovernedArtifactTransferRequest:  # type: ignore[no-untyped-def]
    return ExactGovernedArtifactTransferRequest(
        execution_request=request,
        recipe_ref=recipe.recipe_ref,
        operation=recipe.operation,
        artifact_ref=recipe.artifact_ref,
        quarantine_ref=recipe.quarantine_ref,
        download_transaction_ref=recipe.download_transaction_ref,
    )


def _quarantine_file(root: Path) -> Path:
    files = list((root / "artifact-quarantine").iterdir())
    assert len(files) == 1
    return files[0]


def test_bounded_download_is_quarantined_only_and_receipts_are_content_free(
    tmp_path: Path,
) -> None:
    quarantine_root = tmp_path / "artifacts"
    store = GovernedArtifactQuarantineStore(quarantine_root)
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="download-happy",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    secret = "bounded local validation artifact"
    payload = bytearray(secret, "utf-8")

    result = service.execute(
        _exact(request, recipe),
        injected_download_payload=payload,
    )

    assert result.receipt.status == "quarantined"
    assert result.receipt.external_action_state == "succeeded"
    assert result.receipt.content_free is True
    assert result.receipt.raw_path_recorded is False
    assert result.receipt.raw_artifact_recorded is False
    assert result.receipt.live_download_performed is False
    assert result.receipt.network_call_performed is False
    assert result.receipt.external_mutation_performed is False
    assert result.quarantine is not None
    assert result.quarantine.trusted_for_use is False
    assert result.quarantine.raw_artifact_returned is False
    assert payload == bytearray(len(payload))
    quarantined = _quarantine_file(quarantine_root)
    assert quarantined.read_text(encoding="utf-8") == secret
    assert stat.S_IMODE(os.lstat(quarantined).st_mode) == 0o600
    durable_receipt = (tmp_path / "kernel" / "transactions.sqlite3").read_bytes()
    assert secret.encode() not in durable_receipt
    assert str(quarantine_root).encode() not in durable_receipt
    assert secret not in result.model_dump_json()
    assert str(quarantine_root) not in result.model_dump_json()
    assert result.quarantine is not None
    foreign_quarantine = result.quarantine.model_copy(
        update={
            "recipe_ref": _pinned(
                "artifact-transfer-recipe-ref:governed-browser",
                suffix="foreign-projection",
            )
        }
    )
    with pytest.raises(ValueError, match="QUARANTINE_RESULT_SCOPE_MISMATCH"):
        ExactGovernedArtifactTransferResult(
            receipt=result.receipt,
            quarantine=foreign_quarantine,
        )


def test_download_replay_is_at_most_once_content_free_and_zeroizes_input(
    tmp_path: Path,
) -> None:
    quarantine_root = tmp_path / "artifacts"
    store = GovernedArtifactQuarantineStore(quarantine_root)
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="download-replay",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    exact = _exact(request, recipe)
    first_payload = bytearray(b"first bounded artifact")
    replay_payload = bytearray(b"different content never dispatched")

    first = service.execute(exact, injected_download_payload=first_payload)
    replay = service.execute(exact, injected_download_payload=replay_payload)

    assert first.receipt.status == "quarantined"
    assert replay.receipt.status == "replayed_content_free"
    assert replay.receipt.replayed is True
    assert replay.quarantine is None
    assert replay.upload_plan is None
    assert first_payload == bytearray(len(first_payload))
    assert replay_payload == bytearray(len(replay_payload))
    assert _quarantine_file(quarantine_root).read_bytes() == b"first bounded artifact"


def test_upload_is_an_exact_fingerprinted_plan_from_quarantine_only(
    tmp_path: Path,
) -> None:
    quarantine_root = tmp_path / "artifacts"
    store = GovernedArtifactQuarantineStore(quarantine_root)
    download_request, download_recipe, download_registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="download-for-upload",
    )
    download_service, _, _ = _service(
        tmp_path / "download-kernel",
        store=store,
        request=download_request,
        registry=download_registry,
    )
    downloaded = download_service.execute(
        _exact(download_request, download_recipe),
        injected_download_payload=bytearray(b"exact upload source"),
    )
    assert downloaded.quarantine is not None
    upload_request, upload_recipe, upload_registry = _transfer_context(
        store,
        operation=(GovernedArtifactTransferOperation.upload_quarantined_artifact_plan),
        suffix="upload-plan",
        artifact_ref=download_recipe.artifact_ref,
        quarantine_ref=download_recipe.quarantine_ref,
        download_transaction_ref=download_recipe.download_transaction_ref,
        content_fingerprint_ref=(downloaded.quarantine.content_fingerprint_ref),
    )
    upload_service, _, _ = _service(
        tmp_path / "upload-kernel",
        store=store,
        request=upload_request,
        registry=upload_registry,
    )

    result = upload_service.execute(_exact(upload_request, upload_recipe))

    assert result.receipt.status == "upload_plan_ready"
    assert result.upload_plan is not None
    assert result.upload_plan.artifact_fingerprint_verified is True
    assert result.upload_plan.quarantined_source_required is True
    assert result.upload_plan.upload_plan_only is True
    assert result.upload_plan.raw_artifact_returned is False
    assert result.upload_plan.upload_body_materialized is False
    assert result.upload_plan.upload_performed is False
    assert result.upload_plan.browser_opened is False
    assert result.upload_plan.network_call_performed is False
    assert result.upload_plan.external_mutation_performed is False
    assert result.upload_plan.real_external_target is False
    foreign_plan_payload = result.upload_plan.model_dump(mode="python")
    foreign_plan_payload["recipe_ref"] = _pinned(
        "artifact-transfer-recipe-ref:governed-browser",
        suffix="foreign-plan",
    )
    provisional_foreign_plan = ExactGovernedArtifactUploadPlan.model_construct(
        **foreign_plan_payload
    )
    foreign_plan_payload["plan_ref"] = stable_governed_browser_ref(
        "artifact-upload-plan-ref:governed-browser",
        provisional_foreign_plan.model_dump(
            mode="json",
            exclude={"plan_ref"},
        ),
    )
    foreign_plan = ExactGovernedArtifactUploadPlan.model_validate(foreign_plan_payload)
    with pytest.raises(ValueError, match="UPLOAD_PLAN_RESULT_SCOPE_MISMATCH"):
        ExactGovernedArtifactTransferResult(
            receipt=result.receipt,
            upload_plan=foreign_plan,
        )
    assert (
        b"exact upload source"
        not in (tmp_path / "upload-kernel" / "transactions.sqlite3").read_bytes()
    )


@pytest.mark.parametrize("mode", ["missing", "fingerprint-drift"])
def test_upload_fails_closed_without_exact_quarantined_fingerprint(
    tmp_path: Path,
    mode: str,
) -> None:
    quarantine_root = tmp_path / "artifacts"
    store = GovernedArtifactQuarantineStore(quarantine_root)
    artifact_ref = governed_artifact_ref(
        source_ref=_pinned(
            "artifact-source-ref:governed-browser",
            suffix=mode,
        ),
        declared_media_type=GovernedArtifactMediaType.text_plain,
    )
    base = _binding(suffix=f"{mode}-download")
    quarantine_ref = governed_artifact_quarantine_ref(
        origin_ref=base.origin_ref,
        artifact_ref=artifact_ref,
        download_transaction_ref=base.transaction_ref,
    )
    expected = store.validate_payload(
        payload=b"expected artifact",
        declared_media_type=GovernedArtifactMediaType.text_plain,
        max_bytes=1024,
    ).content_fingerprint_ref
    if mode == "fingerprint-drift":
        store.quarantine(
            quarantine_ref=quarantine_ref,
            payload=b"different artifact",
            declared_media_type=GovernedArtifactMediaType.text_plain,
            max_bytes=1024,
        )
    request, recipe, registry = _transfer_context(
        store,
        operation=(GovernedArtifactTransferOperation.upload_quarantined_artifact_plan),
        suffix=mode,
        artifact_ref=artifact_ref,
        quarantine_ref=quarantine_ref,
        download_transaction_ref=base.transaction_ref,
        content_fingerprint_ref=expected,
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )

    result = service.execute(_exact(request, recipe))

    assert result.receipt.status == "failed"
    assert result.receipt.external_action_state == "failed"
    assert result.upload_plan is None
    assert result.quarantine is None


def test_unknown_recipe_and_operation_mismatch_are_truthfully_blocked(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="recipe-scope",
    )
    fingerprint = store.validate_payload(
        payload=b"scope-only",
        declared_media_type=GovernedArtifactMediaType.text_plain,
        max_bytes=1024,
    ).content_fingerprint_ref
    upload_request, _, _ = _transfer_context(
        store,
        operation=(GovernedArtifactTransferOperation.upload_quarantined_artifact_plan),
        suffix="recipe-scope-upload",
        artifact_ref=recipe.artifact_ref,
        quarantine_ref=recipe.quarantine_ref,
        download_transaction_ref=recipe.download_transaction_ref,
        content_fingerprint_ref=fingerprint,
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=upload_request,
        registry=registry,
    )
    unknown_payload = bytearray(b"never written")
    unknown = service.execute(
        ExactGovernedArtifactTransferRequest(
            execution_request=upload_request,
            recipe_ref="artifact-transfer-recipe-ref:governed-browser:unknown",
            operation=(
                GovernedArtifactTransferOperation.upload_quarantined_artifact_plan
            ),
            artifact_ref=recipe.artifact_ref,
            quarantine_ref=recipe.quarantine_ref,
            download_transaction_ref=recipe.download_transaction_ref,
        ),
        injected_download_payload=unknown_payload,
    )
    assert unknown.receipt.status == "preflight_blocked"
    assert unknown.receipt.operation == "upload_quarantined_artifact_plan"
    assert unknown_payload == bytearray(len(unknown_payload))

    mismatch_payload = bytearray(b"also never written")
    mismatch = service.execute(
        ExactGovernedArtifactTransferRequest(
            execution_request=upload_request,
            recipe_ref=recipe.recipe_ref,
            operation=(
                GovernedArtifactTransferOperation.upload_quarantined_artifact_plan
            ),
            artifact_ref=recipe.artifact_ref,
            quarantine_ref=recipe.quarantine_ref,
            download_transaction_ref=recipe.download_transaction_ref,
        ),
        injected_download_payload=mismatch_payload,
    )
    assert mismatch.receipt.status == "preflight_blocked"
    assert mismatch.receipt.reason_refs == [
        "reason-ref:governed-artifact:operation-mismatch"
    ]
    assert mismatch_payload == bytearray(len(mismatch_payload))
    assert list((tmp_path / "artifacts" / "artifact-quarantine").iterdir()) == []


def test_approval_identifier_alone_and_broader_lease_grant_nothing(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="authority-denial",
    )
    service, _, _ = _service(
        tmp_path / "approval-kernel",
        store=store,
        request=request,
        registry=registry,
    )
    ungranted = request.model_copy(
        update={"approval_ref": "approval-ref:governed-artifact:identifier-only"}
    )
    approval_payload = bytearray(b"approval cannot authorize")
    blocked = service.execute(
        ExactGovernedArtifactTransferRequest(
            execution_request=ungranted,
            recipe_ref=recipe.recipe_ref,
            operation=recipe.operation,
            artifact_ref=recipe.artifact_ref,
            quarantine_ref=recipe.quarantine_ref,
            download_transaction_ref=recipe.download_transaction_ref,
        ),
        injected_download_payload=approval_payload,
    )
    assert blocked.receipt.status == "transaction_blocked"
    assert blocked.receipt.approval_validation_ref
    assert blocked.receipt.authority_decision_ref is None
    assert blocked.receipt.budget_reservation_ref is None
    assert approval_payload == bytearray(len(approval_payload))

    lease_service, lease_kernel, _ = _service(
        tmp_path / "lease-kernel",
        store=store,
        request=request,
        registry=registry,
    )
    broader_lease = _lease(request).model_copy(
        update={
            "domains": {
                AuthorityDomain.browser: [AuthorityCapability.destructive],
            }
        }
    )
    lease_kernel._authority_leases_provider = lambda: [broader_lease]
    lease_payload = bytearray(b"broad lease cannot authorize")
    denied = lease_service.execute(
        _exact(request, recipe),
        injected_download_payload=lease_payload,
    )
    assert denied.receipt.status == "transaction_blocked"
    assert denied.receipt.reason_refs == [
        "reason-ref:governed-external-action:exact-lease-required"
    ]
    assert lease_payload == bytearray(len(lease_payload))
    assert list((tmp_path / "artifacts" / "artifact-quarantine").iterdir()) == []


@pytest.mark.parametrize(
    "readiness",
    [
        {"safe_disable": True},
        {"kill_switch": True},
        {"ready": False},
        {"snapshot_ref": _ref("page-snapshot", "transfer-drift")},
    ],
)
def test_shared_gates_block_before_quarantine_write(
    tmp_path: Path,
    readiness: dict[str, object],
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix=f"gate-{next(iter(readiness))}",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
        readiness_provider=lambda item: _readiness(item, **readiness),
    )
    payload = bytearray(b"gated content")

    result = service.execute(
        _exact(request, recipe),
        injected_download_payload=payload,
    )

    assert result.receipt.status == "transaction_blocked"
    assert result.quarantine is None
    assert payload == bytearray(len(payload))
    assert list((tmp_path / "artifacts" / "artifact-quarantine").iterdir()) == []


@pytest.mark.parametrize(
    "payload",
    [
        bytearray(MAX_GOVERNED_ARTIFACT_BYTES + 1),
        bytearray(b"\x89PNG\r\n\x1a\nnot declared as text"),
        bytearray(b"<script>untrusted active content</script>"),
    ],
)
def test_invalid_download_payloads_fail_without_materialization(
    tmp_path: Path,
    payload: bytearray,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix=f"payload-{len(payload)}",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
    original_length = len(payload)

    result = service.execute(
        _exact(request, recipe),
        injected_download_payload=payload,
    )

    assert result.receipt.status == "failed"
    assert result.quarantine is None
    assert payload == bytearray(original_length)
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
        operation=(GovernedArtifactTransferOperation.upload_quarantined_artifact_plan),
        suffix="raw-upload",
        content_fingerprint_ref=fingerprint,
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )
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
        recipe.recipe_ref.encode()
        not in (tmp_path / "kernel" / "transactions.sqlite3").read_bytes()
    )
