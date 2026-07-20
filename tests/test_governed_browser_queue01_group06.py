from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

import ultimate_ai_agent.core.governed_browser.origin_sessions as origin_sessions_module
from scripts.verify_governed_browser_queue01_group06 import verify
from tests.test_governed_browser_queue01_group01 import (
    _authorized_kernel,
    _binding,
    _readiness,
    _ref,
    _request,
)
from ultimate_ai_agent.core.authority import AuthorityCapability
from ultimate_ai_agent.core.governed_browser import (
    ExactGovernedBrowserOriginSessionRequest,
    ExactGovernedBrowserOriginSessionResult,
    ExactGovernedBrowserOriginSessionService,
    ExternalActionAuthorityBinding,
    ExternalActionTargetKind,
    GovernedBrowserKeychainError,
    GovernedBrowserKeychainOperation,
    GovernedBrowserKeychainOperationReceipt,
    GovernedBrowserOriginSessionOperation,
    GovernedBrowserOriginSessionReceipt,
    GovernedBrowserOriginSessionRecipeRegistry,
    GovernedBrowserOriginSessionState,
    GovernedBrowserOriginSessionStateConflict,
    GovernedBrowserOriginSessionStore,
    build_governed_browser_credential_registration,
    build_governed_browser_origin_session_recipe,
    governed_browser_keychain_helper_receipt_ref,
    governed_browser_origin_session_operation_authority_ref,
    governed_browser_origin_session_ref,
    stable_governed_browser_ref,
)
from ultimate_ai_agent.core.governed_browser.replay_provenance import (
    replay_validation_context,
)
from ultimate_ai_agent.core.time import utc_now


def _opaque_material(seed: int, length: int = 32) -> bytearray:
    return bytearray((seed + index) % 256 for index in range(length))


def _rehash_origin_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    identity_payload = {
        key: value
        for key, value in payload.items()
        if key
        not in {
            "receipt_ref",
            "recipe_snapshot",
            "external_receipt_snapshot",
        }
    }
    if identity_payload.get("budget_release_ref") is None:
        identity_payload.pop("budget_release_ref", None)
    payload["receipt_ref"] = stable_governed_browser_ref(
        "browser-origin-session-operation-receipt-ref:governed-browser",
        identity_payload,
    )
    return payload


def _rehash_origin_external_projection(
    payload: dict[str, Any],
) -> dict[str, Any]:
    external = dict(payload["external_receipt_snapshot"])
    external_identity = {
        key: value
        for key, value in external.items()
        if key
        not in {
            "receipt_ref",
            "schema_version",
            "replayed",
            "content_free",
            "automatic_retry_allowed",
        }
    }
    if external_identity.get("budget_release_ref") is None:
        external_identity.pop("budget_release_ref", None)
    external["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-action",
        external_identity,
    )
    payload["external_action_receipt_ref"] = external["receipt_ref"]
    payload["external_receipt_snapshot"] = external
    return _rehash_origin_receipt(payload)


def _origin_replay_validation_context(
    *,
    service: ExactGovernedBrowserOriginSessionService,
    request,
    recipe,
    replay: ExactGovernedBrowserOriginSessionResult,
):  # type: ignore[no-untyped-def]
    external_receipt = replay.receipt.external_receipt_snapshot
    assert external_receipt is not None
    return origin_sessions_module._origin_session_replay_context(
        service._kernel,
        expected_execution=(
            origin_sessions_module._origin_session_kernel_execution(
                request,
                recipe=recipe,
            )
        ),
        recipe=recipe,
        replay_receipt=external_receipt,
    )


class _FakeKeychain:
    def __init__(self, *, fail_store: bool = False) -> None:
        self.present: set[str] = set()
        self.calls: list[tuple[str, str]] = []
        self.fail_store = fail_store

    def _receipt(
        self,
        operation: GovernedBrowserKeychainOperation,
        registration,  # type: ignore[no-untyped-def]
        *,
        request_ref: str,
        created: bool | None,
        present: bool,
        deleted_or_absent: bool | None = None,
    ) -> GovernedBrowserKeychainOperationReceipt:
        return GovernedBrowserKeychainOperationReceipt(
            operation=operation,
            registration_ref=registration.registration_ref,
            origin_ref=registration.origin_ref,
            credential_handle_ref=registration.credential_handle_ref,
            credential_generation_ref=registration.credential_generation_ref,
            keychain_item_ref=registration.keychain_item_ref,
            helper_receipt_ref=(
                governed_browser_keychain_helper_receipt_ref(
                    operation=operation,
                    request_ref=request_ref,
                )
            ),
            created=created,
            present=present,
            deleted_or_absent=deleted_or_absent,
        )

    def store(
        self,
        registration,  # type: ignore[no-untyped-def]
        *,
        request_ref: str,
        credential_material: bytearray,
    ) -> GovernedBrowserKeychainOperationReceipt:
        self.calls.append(("store", request_ref))
        if self.fail_store:
            raise GovernedBrowserKeychainError(
                "GOVERNED_BROWSER_KEYCHAIN_HELPER_EXECUTION_FAILED"
            )
        created = registration.registration_ref not in self.present
        if not created:
            raise GovernedBrowserKeychainError(
                "GOVERNED_BROWSER_KEYCHAIN_ITEM_ALREADY_EXISTS"
            )
        self.present.add(registration.registration_ref)
        return self._receipt(
            GovernedBrowserKeychainOperation.store,
            registration,
            request_ref=request_ref,
            created=created,
            present=True,
        )

    def probe(
        self,
        registration,  # type: ignore[no-untyped-def]
        *,
        request_ref: str,
    ) -> GovernedBrowserKeychainOperationReceipt:
        self.calls.append(("probe", request_ref))
        if registration.registration_ref not in self.present:
            raise GovernedBrowserKeychainError(
                "GOVERNED_BROWSER_KEYCHAIN_ITEM_NOT_FOUND"
            )
        return self._receipt(
            GovernedBrowserKeychainOperation.probe,
            registration,
            request_ref=request_ref,
            created=None,
            present=True,
        )

    def delete(
        self,
        registration,  # type: ignore[no-untyped-def]
        *,
        request_ref: str,
    ) -> GovernedBrowserKeychainOperationReceipt:
        self.calls.append(("delete", request_ref))
        self.present.discard(registration.registration_ref)
        return self._receipt(
            GovernedBrowserKeychainOperation.delete,
            registration,
            request_ref=request_ref,
            created=None,
            present=False,
            deleted_or_absent=True,
        )


def _lifecycle_context(
    *,
    target_kind: ExternalActionTargetKind = ExternalActionTargetKind.local_validation,
    suffix: str = "lifecycle",
):  # type: ignore[no-untyped-def]
    base = _binding(suffix=f"{suffix}-base", target_kind=target_kind)
    registration = build_governed_browser_credential_registration(
        origin_ref=base.origin_ref,
        credential_handle_ref=(
            f"credential-handle-ref:governed-browser:{suffix}"
        ),
        credential_generation_ref=(
            f"credential-generation-ref:governed-browser:{suffix}-01"
        ),
    )
    generation_ref = (
        "browser-session-generation-ref:governed-browser:session-01"
        if suffix == "lifecycle"
        else (
            "browser-session-generation-ref:governed-browser:"
            f"{suffix}-session-01"
        )
    )
    session_ref = governed_browser_origin_session_ref(
        registration_ref=registration.registration_ref,
        session_generation_ref=generation_ref,
    )
    created_at = utc_now()
    expires_at = created_at + timedelta(minutes=20)
    contexts: dict[
        GovernedBrowserOriginSessionOperation,
        tuple[Any, Any],
    ] = {}
    for operation in GovernedBrowserOriginSessionOperation:
        operation_authority_ref = (
            governed_browser_origin_session_operation_authority_ref(
                registration_ref=registration.registration_ref,
                session_generation_ref=generation_ref,
                operation=operation,
            )
        )
        current = _binding(
            suffix=f"{suffix}-{operation.value}",
            target_kind=target_kind,
        )
        binding = ExternalActionAuthorityBinding.model_validate(
            {
                **current.model_dump(mode="json"),
                "authority_capability": AuthorityCapability.execute,
                "field_schema_ref": registration.registration_ref,
                "resource_refs": [
                    _ref("resource", f"{suffix}-{operation.value}"),
                    operation_authority_ref,
                    registration.registration_ref,
                    registration.credential_handle_ref,
                    registration.credential_generation_ref,
                    registration.keychain_item_ref,
                    session_ref,
                    generation_ref,
                ],
            }
        )
        request = _request(binding)
        recipe = build_governed_browser_origin_session_recipe(
            request,
            registration=registration,
            operation=operation,
            session_generation_ref=generation_ref,
            created_at=created_at,
            expires_at=expires_at,
        )
        contexts[operation] = (request, recipe)
    registry = GovernedBrowserOriginSessionRecipeRegistry(
        registrations=[registration],
        recipes=[recipe for _, recipe in contexts.values()],
    )
    return registration, contexts, registry


def _execute(
    *,
    tmp_path: Path,
    operation: GovernedBrowserOriginSessionOperation,
    contexts,
    registry,
    keychain: _FakeKeychain,
    sessions: GovernedBrowserOriginSessionStore,
    material: bytearray | None = None,
    readiness_provider=None,  # type: ignore[no-untyped-def]
):  # type: ignore[no-untyped-def]
    request, recipe = contexts[operation]
    kernel, _ = _authorized_kernel(
        tmp_path / operation.value,
        request,
        readiness_provider=readiness_provider,
    )
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=keychain,
        sessions=sessions,
    )
    result = service.execute(
        ExactGovernedBrowserOriginSessionRequest(
            recipe_ref=recipe.recipe_ref,
            execution_request=request,
        ),
        credential_material=material,
    )
    return result, service


def test_exact_per_origin_lifecycle_is_governed_content_free_and_inactive(
    tmp_path: Path,
) -> None:
    registration, contexts, registry = _lifecycle_context()
    keychain = _FakeKeychain()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    material = _opaque_material(29)
    material_fingerprint = hashlib.sha256(material).hexdigest()

    enrolled, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
        material=material,
    )
    prepared, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.prepare_session,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    revalidated, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.revalidate_session,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    closed, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.close_session,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    revoked, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.revoke_credential,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )

    assert all(value == 0 for value in material)
    assert enrolled.receipt.status == "credential_stored"
    assert prepared.receipt.status == "session_prepared"
    assert prepared.session is not None
    assert prepared.session.state == GovernedBrowserOriginSessionState.prepared_inactive
    assert revalidated.receipt.status == "session_revalidated"
    assert closed.session is not None
    assert closed.session.state == GovernedBrowserOriginSessionState.closed
    assert revoked.receipt.status == "credential_revoked"
    assert revoked.session is not None
    assert revoked.session.state == GovernedBrowserOriginSessionState.revoked
    assert registration.registration_ref not in keychain.present
    payload = json.dumps(
        [
            item.model_dump(mode="json")
            for item in (enrolled, prepared, revalidated, closed, revoked)
        ],
        sort_keys=True,
    )
    assert material_fingerprint not in payload
    assert "127.0.0.1" not in payload
    assert '"browser_session_started": false' in payload
    assert '"authentication_performed": false' in payload
    assert '"cookies_used": false' in payload
    assert '"network_call_performed": false' in payload
    assert material_fingerprint.encode("ascii") not in sessions.path.read_bytes()


def test_origin_receipt_snapshot_preserves_outer_identity_and_is_required(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context()
    result, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=_FakeKeychain(),
        sessions=GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3"),
        material=_opaque_material(31),
    )
    receipt = result.receipt
    assert receipt.recipe_snapshot is not None
    assert receipt.recipe_snapshot.recipe_ref == receipt.recipe_ref
    assert receipt.external_receipt_snapshot is not None
    assert receipt.external_receipt_snapshot.receipt_ref == (
        receipt.external_action_receipt_ref
    )
    historical_identity = receipt.model_dump(
        mode="json",
        exclude={
            "receipt_ref",
            "recipe_snapshot",
            "external_receipt_snapshot",
        },
    )
    if historical_identity.get("budget_release_ref") is None:
        historical_identity.pop("budget_release_ref", None)
    assert receipt.receipt_ref == stable_governed_browser_ref(
        "browser-origin-session-operation-receipt-ref:governed-browser",
        historical_identity,
    )

    missing_snapshot = receipt.model_dump(mode="json")
    missing_snapshot["external_receipt_snapshot"] = None
    with pytest.raises(
        ValueError,
        match=(
            "GOVERNED_BROWSER_ORIGIN_SESSION_"
            "EXTERNAL_RECEIPT_SNAPSHOT_REQUIRED"
        ),
    ):
        GovernedBrowserOriginSessionReceipt.model_validate(missing_snapshot)

    missing_recipe = receipt.model_dump(mode="json")
    missing_recipe["recipe_snapshot"] = None
    with pytest.raises(
        ValueError,
        match="GOVERNED_BROWSER_ORIGIN_SESSION_RECIPE_SNAPSHOT_REQUIRED",
    ):
        GovernedBrowserOriginSessionReceipt.model_validate(missing_recipe)


def test_origin_receipt_rejects_conflicting_or_rebound_kernel_snapshot(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context()
    result, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=_FakeKeychain(),
        sessions=GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3"),
        material=_opaque_material(37),
    )
    conflicting = result.receipt.model_dump(mode="json")
    snapshot = dict(conflicting["external_receipt_snapshot"])
    snapshot["budget_release_ref"] = _ref(
        "budget-release",
        "origin-conflicting-proofs",
    )
    snapshot["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-action",
        {
            "transaction_ref": snapshot["transaction_ref"],
            "intent_ref": snapshot["intent_ref"],
            "binding_ref": snapshot["binding_ref"],
            "state": snapshot["state"],
            "approval_validation_ref": snapshot["approval_validation_ref"],
            "authority_decision_ref": snapshot["authority_decision_ref"],
            "budget_reservation_ref": snapshot["budget_reservation_ref"],
            "budget_release_ref": snapshot["budget_release_ref"],
            "budget_settlement_ref": snapshot["budget_settlement_ref"],
            "evidence_refs": snapshot["evidence_refs"],
            "reason_refs": snapshot["reason_refs"],
        },
    )
    conflicting["external_receipt_snapshot"] = snapshot
    with pytest.raises(
        ValueError,
        match="GOVERNED_BROWSER_BUDGET_ACCOUNTING_PROOF_CONFLICT",
    ):
        GovernedBrowserOriginSessionReceipt.model_validate(conflicting)

    rebound = result.receipt.model_dump(mode="json")
    rebound["reason_refs"] = ["reason-ref:governed-browser-origin-session:rebound"]
    _rehash_origin_receipt(rebound)
    with pytest.raises(
        ValueError,
        match=(
            "GOVERNED_BROWSER_ORIGIN_SESSION_"
            "EXTERNAL_RECEIPT_PROJECTION_MISMATCH"
        ),
    ):
        GovernedBrowserOriginSessionReceipt.model_validate(rebound)


def test_origin_receipt_rejects_cross_operation_recipe_rebinding(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context()
    enrolled, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=_FakeKeychain(),
        sessions=GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3"),
        material=_opaque_material(41),
    )

    rebound_operation = enrolled.receipt.model_dump(mode="json")
    rebound_operation.update(
        {
            "operation": "revoke_credential",
            "status": "credential_revoked",
        }
    )
    _rehash_origin_receipt(rebound_operation)
    with pytest.raises(
        ValueError,
        match=(
            "GOVERNED_BROWSER_ORIGIN_SESSION_"
            "RECIPE_SNAPSHOT_SCOPE_MISMATCH"
        ),
    ):
        GovernedBrowserOriginSessionReceipt.model_validate(rebound_operation)

    rebound_recipe = enrolled.receipt.model_dump(mode="json")
    _, revoke_recipe = contexts[
        GovernedBrowserOriginSessionOperation.revoke_credential
    ]
    rebound_recipe.update(
        {
            "operation": "revoke_credential",
            "status": "credential_revoked",
            "recipe_ref": revoke_recipe.recipe_ref,
            "recipe_snapshot": revoke_recipe.model_dump(mode="json"),
        }
    )
    _rehash_origin_receipt(rebound_recipe)
    with pytest.raises(
        ValueError,
        match=(
            "GOVERNED_BROWSER_ORIGIN_SESSION_"
            "RECIPE_SNAPSHOT_SCOPE_MISMATCH"
        ),
    ):
        GovernedBrowserOriginSessionReceipt.model_validate(rebound_recipe)


def test_origin_receipt_binds_success_evidence_to_exact_recipe_snapshot(
    tmp_path: Path,
) -> None:
    registration, contexts, registry = _lifecycle_context()
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.enroll_credential
    ]
    result, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=_FakeKeychain(),
        sessions=GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3"),
        material=_opaque_material(42),
    )
    shifted_recipe = build_governed_browser_origin_session_recipe(
        request,
        registration=registration,
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        session_generation_ref=recipe.session_generation_ref,
        created_at=recipe.created_at + timedelta(seconds=1),
        expires_at=recipe.expires_at + timedelta(seconds=1),
    )
    assert shifted_recipe.binding_ref == recipe.binding_ref
    assert shifted_recipe.recipe_ref != recipe.recipe_ref
    forged = result.receipt.model_dump(mode="json")
    forged.update(
        {
            "recipe_ref": shifted_recipe.recipe_ref,
            "recipe_snapshot": shifted_recipe.model_dump(mode="json"),
        }
    )
    _rehash_origin_receipt(forged)

    with pytest.raises(
        ValueError,
        match="GOVERNED_BROWSER_ORIGIN_SESSION_RECIPE_EVIDENCE_MISMATCH",
    ):
        GovernedBrowserOriginSessionReceipt.model_validate(forged)


@pytest.mark.parametrize(
    "missing_field",
    (
        "approval_validation_ref",
        "authority_decision_ref",
        "budget_reservation_ref",
        "budget_settlement_ref",
        "evidence_refs",
    ),
)
def test_origin_succeeded_snapshot_requires_complete_kernel_proof(
    tmp_path: Path,
    missing_field: str,
) -> None:
    _, contexts, registry = _lifecycle_context()
    result, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=_FakeKeychain(),
        sessions=GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3"),
        material=_opaque_material(43),
    )
    forged = result.receipt.model_dump(mode="json")
    external = dict(forged["external_receipt_snapshot"])
    external[missing_field] = [] if missing_field == "evidence_refs" else None
    external_identity = {
        key: value
        for key, value in external.items()
        if key
        not in {
            "receipt_ref",
            "schema_version",
            "budget_release_ref",
            "replayed",
            "content_free",
            "automatic_retry_allowed",
        }
    }
    external["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-action",
        external_identity,
    )
    forged.update(
        {
            "external_action_receipt_ref": external["receipt_ref"],
            "external_receipt_snapshot": external,
        }
    )
    if missing_field != "evidence_refs":
        forged[missing_field] = None
    _rehash_origin_receipt(forged)

    with pytest.raises(
        ValueError,
        match=(
            "GOVERNED_BROWSER_ORIGIN_SESSION_"
            "SUCCESS_KERNEL_PROOF_REQUIRED"
        ),
    ):
        GovernedBrowserOriginSessionReceipt.model_validate(forged)


def test_origin_non_preflight_receipt_requires_kernel_context(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context()
    result, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=_FakeKeychain(),
        sessions=GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3"),
        material=_opaque_material(43),
    )
    forged = result.receipt.model_dump(mode="json")
    forged.update(
        {
            "status": "failed",
            "external_action_receipt_ref": None,
            "recipe_snapshot": None,
            "external_receipt_snapshot": None,
            "approval_validation_ref": None,
            "authority_decision_ref": None,
            "budget_reservation_ref": None,
            "budget_release_ref": None,
            "budget_settlement_ref": None,
            "reason_refs": [
                "reason-ref:governed-browser-origin-session:proofless-failure"
            ],
            "replayed": False,
        }
    )
    _rehash_origin_receipt(forged)

    with pytest.raises(
        ValueError,
        match="GOVERNED_BROWSER_ORIGIN_SESSION_EXTERNAL_PROOF_CONTEXT_REQUIRED",
    ):
        GovernedBrowserOriginSessionReceipt.model_validate(forged)


def test_origin_preflight_rejects_orphan_kernel_proof(tmp_path: Path) -> None:
    _, contexts, registry = _lifecycle_context()
    result, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=_FakeKeychain(),
        sessions=GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3"),
        material=_opaque_material(47),
    )
    forged = result.receipt.model_dump(mode="json")
    forged.update(
        {
            "status": "blocked",
            "external_action_receipt_ref": None,
            "recipe_snapshot": None,
            "external_receipt_snapshot": None,
            "approval_validation_ref": None,
            "authority_decision_ref": None,
            "budget_reservation_ref": None,
            "budget_release_ref": _ref(
                "budget-release",
                "origin-preflight-orphan-proof",
            ),
            "budget_settlement_ref": None,
            "reason_refs": [
                "reason-ref:governed-browser-origin-session:preflight-blocked"
            ],
            "replayed": False,
        }
    )
    _rehash_origin_receipt(forged)

    with pytest.raises(
        ValueError,
        match="GOVERNED_BROWSER_ORIGIN_SESSION_EXTERNAL_PROOF_CONTEXT_INVALID",
    ):
        GovernedBrowserOriginSessionReceipt.model_validate(forged)


def test_origin_receipt_rejects_external_state_status_or_operation_mismatch(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context()
    result, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=_FakeKeychain(),
        sessions=GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3"),
        material=_opaque_material(53),
    )
    status_mismatch = result.receipt.model_dump(mode="json")
    status_mismatch["status"] = "failed"
    _rehash_origin_receipt(status_mismatch)
    with pytest.raises(
        ValueError,
        match="GOVERNED_BROWSER_ORIGIN_SESSION_EXTERNAL_STATE_MISMATCH",
    ):
        GovernedBrowserOriginSessionReceipt.model_validate(status_mismatch)

    missing_operation = result.receipt.model_dump(mode="json")
    missing_operation["operation"] = None
    _rehash_origin_receipt(missing_operation)
    with pytest.raises(
        ValueError,
        match="GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_REQUIRED",
    ):
        GovernedBrowserOriginSessionReceipt.model_validate(missing_operation)


def test_origin_result_requires_exact_success_projections(tmp_path: Path) -> None:
    _, contexts, registry = _lifecycle_context()
    keychain = _FakeKeychain()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    enrolled, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
        material=_opaque_material(59),
    )
    prepared, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.prepare_session,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    closed, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.close_session,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    assert prepared.keychain_receipt is not None
    assert prepared.session is not None
    assert closed.session is not None

    with pytest.raises(
        ValueError,
        match="GOVERNED_BROWSER_ORIGIN_SESSION_SUCCESS_PROJECTION_REQUIRED",
    ):
        ExactGovernedBrowserOriginSessionResult(receipt=enrolled.receipt)

    with pytest.raises(
        ValueError,
        match="GOVERNED_BROWSER_ORIGIN_SESSION_KEYCHAIN_PROJECTION_MISMATCH",
    ):
        ExactGovernedBrowserOriginSessionResult(
            receipt=enrolled.receipt,
            keychain_receipt=prepared.keychain_receipt,
        )

    with pytest.raises(
        ValueError,
        match="GOVERNED_BROWSER_ORIGIN_SESSION_RECORD_PROJECTION_MISMATCH",
    ):
        ExactGovernedBrowserOriginSessionResult(
            receipt=prepared.receipt,
            keychain_receipt=prepared.keychain_receipt,
            session=closed.session,
        )


def test_fresh_store_revoke_allows_absent_session_projection(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context()
    result, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.revoke_credential,
        contexts=contexts,
        registry=registry,
        keychain=_FakeKeychain(),
        sessions=GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3"),
    )

    assert result.receipt.status == "credential_revoked"
    assert result.keychain_receipt is not None
    assert result.session is None


def test_non_success_origin_result_rejects_unrelated_projection(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context()
    keychain = _FakeKeychain()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.enroll_credential
    ]
    kernel, _ = _authorized_kernel(tmp_path / "kernel", request)
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=keychain,
        sessions=sessions,
    )
    exact = ExactGovernedBrowserOriginSessionRequest(
        recipe_ref=recipe.recipe_ref,
        execution_request=request,
    )
    first = service.execute(exact, credential_material=_opaque_material(61))
    replay = service.execute(exact, credential_material=_opaque_material(62))
    assert first.keychain_receipt is not None
    assert replay.receipt.status == "replayed"
    context = _origin_replay_validation_context(
        service=service,
        request=request,
        recipe=recipe,
        replay=replay,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_BROWSER_ORIGIN_SESSION_NON_SUCCESS_PROJECTION_DENIED",
    ):
        ExactGovernedBrowserOriginSessionResult.model_validate(
            {
                "receipt": replay.receipt.model_dump(mode="json"),
                "keychain_receipt": first.keychain_receipt,
            },
            context=replay_validation_context(context),
        )


def test_idempotent_distinct_origin_transactions_accept_existing_record(
    tmp_path: Path,
) -> None:
    registration, contexts, registry = _lifecycle_context()
    keychain = _FakeKeychain()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
        material=_opaque_material(63),
    )
    first_prepare, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.prepare_session,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    assert first_prepare.session is not None

    def execute_distinct(
        operation: GovernedBrowserOriginSessionOperation,
        suffix: str,
    ) -> ExactGovernedBrowserOriginSessionResult:
        _, original_recipe = contexts[operation]
        operation_authority_ref = (
            governed_browser_origin_session_operation_authority_ref(
                registration_ref=registration.registration_ref,
                session_generation_ref=original_recipe.session_generation_ref,
                operation=operation,
            )
        )
        base = _binding(suffix=suffix)
        binding = ExternalActionAuthorityBinding.model_validate(
            {
                **base.model_dump(mode="json"),
                "authority_capability": AuthorityCapability.execute,
                "field_schema_ref": registration.registration_ref,
                "resource_refs": [
                    _ref("resource", suffix),
                    operation_authority_ref,
                    registration.registration_ref,
                    registration.credential_handle_ref,
                    registration.credential_generation_ref,
                    registration.keychain_item_ref,
                    original_recipe.session_ref,
                    original_recipe.session_generation_ref,
                ],
            }
        )
        request = _request(binding)
        recipe = build_governed_browser_origin_session_recipe(
            request,
            registration=registration,
            operation=operation,
            session_generation_ref=original_recipe.session_generation_ref,
            created_at=original_recipe.created_at,
            expires_at=original_recipe.expires_at,
        )
        distinct_registry = GovernedBrowserOriginSessionRecipeRegistry(
            registrations=[registration],
            recipes=[recipe],
        )
        kernel, _ = _authorized_kernel(tmp_path / suffix, request)
        service = ExactGovernedBrowserOriginSessionService(
            registry=distinct_registry,
            kernel=kernel,
            keychain=keychain,
            sessions=sessions,
        )
        return service.execute(
            ExactGovernedBrowserOriginSessionRequest(
                recipe_ref=recipe.recipe_ref,
                execution_request=request,
            )
        )

    second_prepare = execute_distinct(
        GovernedBrowserOriginSessionOperation.prepare_session,
        "distinct-prepare",
    )
    assert second_prepare.receipt.status == "session_prepared"
    assert second_prepare.session == first_prepare.session

    first_close, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.close_session,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    second_close = execute_distinct(
        GovernedBrowserOriginSessionOperation.close_session,
        "distinct-close",
    )
    assert first_close.session is not None
    assert second_close.receipt.status == "session_closed"
    assert second_close.session == first_close.session


def test_lifecycle_replay_is_at_most_once_and_suppresses_projection(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context()
    keychain = _FakeKeychain()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.enroll_credential
    ]
    kernel, _ = _authorized_kernel(tmp_path / "kernel", request)
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=keychain,
        sessions=sessions,
    )
    first_material = _opaque_material(41)
    replay_material = _opaque_material(53)
    exact = ExactGovernedBrowserOriginSessionRequest(
        recipe_ref=recipe.recipe_ref,
        execution_request=request,
    )

    first = service.execute(exact, credential_material=first_material)
    replay = service.execute(exact, credential_material=replay_material)

    assert first.receipt.status == "credential_stored"
    assert replay.receipt.status == "replayed"
    assert replay.receipt.replayed is True
    assert replay.keychain_receipt is None
    assert replay.session is None
    assert len(keychain.calls) == 1
    assert all(value == 0 for value in first_material)
    assert all(value == 0 for value in replay_material)


def test_origin_replay_reconstruction_requires_exact_terminal_provenance(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context(suffix="replay-provenance")
    keychain = _FakeKeychain()
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.enroll_credential
    ]
    kernel, _ = _authorized_kernel(tmp_path / "kernel", request)
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=keychain,
        sessions=GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3"),
    )
    exact = ExactGovernedBrowserOriginSessionRequest(
        recipe_ref=recipe.recipe_ref,
        execution_request=request,
    )
    service.execute(exact, credential_material=_opaque_material(71))
    replay = service.execute(exact, credential_material=_opaque_material(72))
    payload = replay.receipt.model_dump(mode="json")
    context = _origin_replay_validation_context(
        service=service,
        request=request,
        recipe=recipe,
        replay=replay,
    )

    restored = GovernedBrowserOriginSessionReceipt.model_validate(
        payload,
        context=replay_validation_context(context),
    )
    assert restored == replay.receipt
    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_REQUIRED",
    ):
        GovernedBrowserOriginSessionReceipt.model_validate(payload)


@pytest.mark.parametrize(
    ("terminal_state", "first_status"),
    (
        ("blocked", "blocked"),
        ("failed", "failed"),
        ("outcome_ambiguous", "outcome_ambiguous"),
    ),
)
def test_origin_non_success_terminal_replays_use_complete_envelope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    terminal_state: str,
    first_status: str,
) -> None:
    _, contexts, registry = _lifecycle_context(
        suffix=f"replay-terminal-{terminal_state}"
    )
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.enroll_credential
    ]
    keychain = _FakeKeychain(fail_store=terminal_state == "outcome_ambiguous")
    if terminal_state == "failed":

        def locked_store(
            registration,  # type: ignore[no-untyped-def]
            *,
            request_ref: str,
            credential_material: bytearray,
        ) -> GovernedBrowserKeychainOperationReceipt:
            del registration, credential_material
            keychain.calls.append(("store", request_ref))
            raise GovernedBrowserKeychainError(
                "GOVERNED_BROWSER_KEYCHAIN_LOCKED"
            )

        monkeypatch.setattr(keychain, "store", locked_store)
    kernel, _ = _authorized_kernel(
        tmp_path / "kernel",
        request,
        readiness_provider=(
            (lambda item: _readiness(item, safe_disable=True))
            if terminal_state == "blocked"
            else None
        ),
    )
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=keychain,
        sessions=GovernedBrowserOriginSessionStore(
            tmp_path / "sessions.sqlite3"
        ),
    )
    exact = ExactGovernedBrowserOriginSessionRequest(
        recipe_ref=recipe.recipe_ref,
        execution_request=request,
    )

    first = service.execute(exact, credential_material=_opaque_material(81))
    replay = service.execute(exact, credential_material=_opaque_material(82))

    assert first.receipt.status == first_status
    assert first.receipt.external_receipt_snapshot is not None
    assert first.receipt.external_receipt_snapshot.state == terminal_state
    assert first.receipt.replayed is False
    assert replay.receipt.status == "replayed"
    assert replay.receipt.external_receipt_snapshot is not None
    assert replay.receipt.external_receipt_snapshot.state == terminal_state
    assert replay.receipt.replayed is True
    assert replay.keychain_receipt is None
    assert replay.session is None
    context = _origin_replay_validation_context(
        service=service,
        request=request,
        recipe=recipe,
        replay=replay,
    )
    assert (
        GovernedBrowserOriginSessionReceipt.model_validate(
            replay.receipt.model_dump(mode="json"),
            context=replay_validation_context(context),
        )
        == replay.receipt
    )


@pytest.mark.parametrize(
    ("state", "evidence_mode"),
    (
        ("blocked", "arbitrary"),
        ("failed", "arbitrary"),
        ("outcome_ambiguous", "arbitrary"),
        ("started", "success"),
        ("prepared", "empty"),
    ),
)
def test_origin_replay_expectation_rejects_invalid_non_success_envelopes(
    tmp_path: Path,
    state: str,
    evidence_mode: str,
) -> None:
    _, contexts, registry = _lifecycle_context(
        suffix=f"replay-invalid-envelope-{state}-{evidence_mode}"
    )
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.enroll_credential
    ]
    kernel, _ = _authorized_kernel(tmp_path / "kernel", request)
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=_FakeKeychain(),
        sessions=GovernedBrowserOriginSessionStore(
            tmp_path / "sessions.sqlite3"
        ),
    )
    exact = ExactGovernedBrowserOriginSessionRequest(
        recipe_ref=recipe.recipe_ref,
        execution_request=request,
    )
    service.execute(exact, credential_material=_opaque_material(83))
    replay = service.execute(exact, credential_material=_opaque_material(84))
    baseline = replay.receipt.external_receipt_snapshot
    assert baseline is not None
    evidence_refs = {
        "arbitrary": (_ref("evidence", f"origin-{state}-arbitrary"),),
        "success": tuple(baseline.evidence_refs),
        "empty": (),
    }[evidence_mode]
    candidate = baseline.model_copy(
        update={
            "state": state,
            "evidence_refs": evidence_refs,
        }
    )

    with pytest.raises(
        ValueError,
        match=(
            "GOVERNED_BROWSER_ORIGIN_SESSION_"
            "REPLAY_EVIDENCE_ENVELOPE_MISMATCH"
        ),
    ):
        origin_sessions_module._origin_session_replay_context(
            service._kernel,
            expected_execution=(
                origin_sessions_module._origin_session_kernel_execution(
                    request,
                    recipe=recipe,
                )
            ),
            recipe=recipe,
            replay_receipt=candidate,
        )


@pytest.mark.parametrize(
    "tamper_mode",
    ("slot-0", "slot-1", "slot-2", "slot-3", "order", "drop", "append"),
)
def test_origin_replay_rejects_fully_rehashed_evidence_tampering(
    tmp_path: Path,
    tamper_mode: str,
) -> None:
    _, contexts, registry = _lifecycle_context(
        suffix=f"replay-tamper-{tamper_mode}"
    )
    keychain = _FakeKeychain()
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.enroll_credential
    ]
    kernel, _ = _authorized_kernel(tmp_path / "kernel", request)
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=keychain,
        sessions=GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3"),
    )
    exact = ExactGovernedBrowserOriginSessionRequest(
        recipe_ref=recipe.recipe_ref,
        execution_request=request,
    )
    service.execute(exact, credential_material=_opaque_material(73))
    replay = service.execute(exact, credential_material=_opaque_material(74))
    context = _origin_replay_validation_context(
        service=service,
        request=request,
        recipe=recipe,
        replay=replay,
    )
    forged = replay.receipt.model_dump(mode="json")
    external = dict(forged["external_receipt_snapshot"])
    evidence_refs = list(external["evidence_refs"])
    if tamper_mode == "slot-0":
        evidence_refs[0] = stable_governed_browser_ref(
            "browser-origin-session-operation-ref:governed-browser",
            {"tamper": tamper_mode},
        )
    elif tamper_mode == "slot-1":
        evidence_refs[1] = stable_governed_browser_ref(
            "helper-receipt-ref:governed-browser-keychain",
            {"tamper": tamper_mode},
        )
    elif tamper_mode == "slot-2":
        evidence_refs[2] = _ref("resource", "unrelated-keychain-item")
    elif tamper_mode == "slot-3":
        evidence_refs[3] = stable_governed_browser_ref(
            "operation-proof-ref:governed-browser",
            {"tamper": tamper_mode},
        )
    elif tamper_mode == "order":
        evidence_refs.reverse()
    elif tamper_mode == "drop":
        evidence_refs.pop()
    else:
        evidence_refs.append(_ref("evidence", "origin-extra"))
    external["evidence_refs"] = evidence_refs
    forged["external_receipt_snapshot"] = external
    _rehash_origin_external_projection(forged)

    with pytest.raises(
        ValueError,
            match=(
                "GOVERNED_BROWSER_ORIGIN_SESSION_RECIPE_EVIDENCE_MISMATCH"
                "|GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_PROOF_REQUIRED"
                "|GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH"
            ),
    ):
        GovernedBrowserOriginSessionReceipt.model_validate(
            forged,
            context=replay_validation_context(context),
        )


@pytest.mark.parametrize("substitution", ("cross-operation", "cross-transaction"))
def test_origin_replay_rejects_cross_scope_provenance_substitution(
    tmp_path: Path,
    substitution: str,
) -> None:
    _, contexts, registry = _lifecycle_context(suffix="replay-scope-a")
    keychain = _FakeKeychain()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "a-sessions.sqlite3")
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.enroll_credential
    ]
    kernel, _ = _authorized_kernel(tmp_path / "a-kernel", request)
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=keychain,
        sessions=sessions,
    )
    exact = ExactGovernedBrowserOriginSessionRequest(
        recipe_ref=recipe.recipe_ref,
        execution_request=request,
    )
    service.execute(exact, credential_material=_opaque_material(75))
    replay = service.execute(exact, credential_material=_opaque_material(76))
    context = _origin_replay_validation_context(
        service=service,
        request=request,
        recipe=recipe,
        replay=replay,
    )

    if substitution == "cross-operation":
        other_request, other_recipe = contexts[
            GovernedBrowserOriginSessionOperation.prepare_session
        ]
        other_result, other_service = _execute(
            tmp_path=tmp_path / "other",
            operation=GovernedBrowserOriginSessionOperation.prepare_session,
            contexts=contexts,
            registry=registry,
            keychain=keychain,
            sessions=sessions,
        )
        assert other_result.receipt.status == "session_prepared"
        other_exact = ExactGovernedBrowserOriginSessionRequest(
            recipe_ref=other_recipe.recipe_ref,
            execution_request=other_request,
        )
        other_replay = other_service.execute(other_exact)
    else:
        _, other_contexts, other_registry = _lifecycle_context(
            suffix="replay-scope-b"
        )
        other_request, other_recipe = other_contexts[
            GovernedBrowserOriginSessionOperation.enroll_credential
        ]
        other_kernel, _ = _authorized_kernel(
            tmp_path / "b-kernel",
            other_request,
        )
        other_service = ExactGovernedBrowserOriginSessionService(
            registry=other_registry,
            kernel=other_kernel,
            keychain=_FakeKeychain(),
            sessions=GovernedBrowserOriginSessionStore(
                tmp_path / "b-sessions.sqlite3"
            ),
        )
        other_exact = ExactGovernedBrowserOriginSessionRequest(
            recipe_ref=other_recipe.recipe_ref,
            execution_request=other_request,
        )
        other_service.execute(
            other_exact,
            credential_material=_opaque_material(77),
        )
        other_replay = other_service.execute(
            other_exact,
            credential_material=_opaque_material(78),
        )

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_OPERATION_MISMATCH",
    ):
        GovernedBrowserOriginSessionReceipt.model_validate(
            other_replay.receipt.model_dump(mode="json"),
            context=replay_validation_context(context),
        )


def test_revoked_session_cannot_be_reopened_or_closed(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context()
    keychain = _FakeKeychain()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")

    _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
        material=_opaque_material(61),
    )
    _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.prepare_session,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    revoked, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.revoke_credential,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    closed_after_revoke, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.close_session,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )

    assert revoked.session is not None
    assert revoked.session.state == GovernedBrowserOriginSessionState.revoked
    assert closed_after_revoke.receipt.status == "failed"
    assert closed_after_revoke.session is None
    persisted = sessions.inspect(revoked.session.session_ref)
    assert persisted is not None
    assert persisted.state == GovernedBrowserOriginSessionState.revoked


def test_unknown_recipe_and_approval_identifier_alone_never_reach_keychain(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context()
    keychain = _FakeKeychain()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.enroll_credential
    ]
    kernel, _ = _authorized_kernel(tmp_path / "kernel", request)
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=keychain,
        sessions=sessions,
    )
    unknown_material = _opaque_material(67)
    unknown = service.execute(
        ExactGovernedBrowserOriginSessionRequest(
            recipe_ref=(
                "browser-origin-session-recipe-ref:governed-browser:unknown"
            ),
            execution_request=request,
        ),
        credential_material=unknown_material,
    )
    guessed_material = _opaque_material(79)
    guessed = service.execute(
        ExactGovernedBrowserOriginSessionRequest(
            recipe_ref=recipe.recipe_ref,
            execution_request=request.model_copy(
                update={
                    "approval_ref": (
                        "approval-ref:governed-browser:guessed-session"
                    )
                }
            ),
        ),
        credential_material=guessed_material,
    )

    assert unknown.receipt.status == "blocked"
    assert unknown.receipt.approval_validation_ref is None
    assert guessed.receipt.status == "blocked"
    assert guessed.receipt.external_action_receipt_ref is not None
    assert keychain.calls == []
    assert all(value == 0 for value in unknown_material)
    assert all(value == 0 for value in guessed_material)
    assert "guessed-session" not in guessed.receipt.model_dump_json()


@pytest.mark.parametrize("mode", ["safe_disable", "kill_switch", "snapshot"])
def test_lifecycle_revalidation_denies_before_keychain(
    tmp_path: Path,
    mode: str,
) -> None:
    _, contexts, registry = _lifecycle_context()
    keychain = _FakeKeychain()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    request, _ = contexts[
        GovernedBrowserOriginSessionOperation.enroll_credential
    ]

    def readiness(item):  # type: ignore[no-untyped-def]
        return _readiness(
            item,
            safe_disable=mode == "safe_disable",
            kill_switch=mode == "kill_switch",
            snapshot_ref=(
                _ref("page-snapshot", "drifted") if mode == "snapshot" else None
            ),
        )

    material = _opaque_material(97)
    result, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
        material=material,
        readiness_provider=readiness,
    )

    assert result.receipt.status == "blocked"
    assert result.receipt.budget_reservation_ref is not None
    assert result.receipt.budget_release_ref is not None
    assert result.receipt.budget_settlement_ref is None
    assert keychain.calls == []
    assert all(value == 0 for value in material)
    assert request.binding.origin not in result.receipt.model_dump_json()


def test_scope_drift_external_target_and_helper_failure_fail_closed(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.enroll_credential
    ]
    kernel, _ = _authorized_kernel(tmp_path / "scope", request)
    keychain = _FakeKeychain()
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=keychain,
        sessions=sessions,
    )
    drifted_binding = ExternalActionAuthorityBinding.model_validate(
        {
            **request.binding.model_dump(mode="json"),
            "resource_refs": [
                ref
                for ref in request.binding.resource_refs
                if ref != recipe.session_generation_ref
            ],
        }
    )
    drifted_material = _opaque_material(109)
    drifted = service.execute(
        ExactGovernedBrowserOriginSessionRequest(
            recipe_ref=recipe.recipe_ref,
            execution_request=_request(drifted_binding),
        ),
        credential_material=drifted_material,
    )
    assert drifted.receipt.status == "blocked"
    assert drifted.receipt.approval_validation_ref is None
    assert keychain.calls == []
    assert all(value == 0 for value in drifted_material)

    with pytest.raises(ValueError, match="REAL_TARGETS_INACTIVE"):
        _lifecycle_context(target_kind=ExternalActionTargetKind.external)

    failing = _FakeKeychain(fail_store=True)
    failing_material = _opaque_material(127)
    ambiguous, failing_service = _execute(
        tmp_path=tmp_path / "failure",
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=failing,
        sessions=GovernedBrowserOriginSessionStore(
            tmp_path / "failure-sessions.sqlite3"
        ),
        material=failing_material,
    )
    replay_material = _opaque_material(149)
    replay = failing_service.execute(
        ExactGovernedBrowserOriginSessionRequest(
            recipe_ref=recipe.recipe_ref,
            execution_request=request,
        ),
        credential_material=replay_material,
    )
    assert ambiguous.receipt.status == "outcome_ambiguous"
    assert replay.receipt.status == "replayed"
    assert len(failing.calls) == 1
    assert all(value == 0 for value in failing_material)
    assert all(value == 0 for value in replay_material)


def test_revoke_state_conflict_after_keychain_delete_is_ambiguous_and_no_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registration, contexts, registry = _lifecycle_context()
    keychain = _FakeKeychain()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
        material=_opaque_material(173),
    )
    prepared, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.prepare_session,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    assert prepared.session is not None

    def conflict(*args, **kwargs):  # type: ignore[no-untyped-def]
        del args, kwargs
        raise GovernedBrowserOriginSessionStateConflict(
            "GOVERNED_BROWSER_ORIGIN_SESSION_UPDATE_CONFLICT"
        )

    monkeypatch.setattr(sessions, "mark_revoked", conflict)
    ambiguous, service = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.revoke_credential,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.revoke_credential
    ]
    replay = service.execute(
        ExactGovernedBrowserOriginSessionRequest(
            recipe_ref=recipe.recipe_ref,
            execution_request=request,
        )
    )

    assert ambiguous.receipt.status == "outcome_ambiguous"
    assert ambiguous.receipt.reason_refs[0] == (
        "reason-ref:governed-external-action:dispatch-outcome-ambiguous"
    )
    assert ambiguous.keychain_receipt is None
    assert ambiguous.session is None
    assert replay.receipt.status == "replayed"
    assert replay.receipt.reason_refs == ambiguous.receipt.reason_refs
    assert sum(operation == "delete" for operation, _ in keychain.calls) == 1
    assert registration.registration_ref not in keychain.present
    persisted = sessions.inspect(prepared.session.session_ref)
    assert persisted is not None
    assert persisted.state == GovernedBrowserOriginSessionState.prepared_inactive


def test_queue01_group06_verifier() -> None:
    assert verify() == []
