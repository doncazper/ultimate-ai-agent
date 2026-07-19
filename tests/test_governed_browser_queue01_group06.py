from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

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
    ExactGovernedBrowserOriginSessionService,
    ExternalActionAuthorityBinding,
    ExternalActionTargetKind,
    GovernedBrowserKeychainError,
    GovernedBrowserKeychainOperation,
    GovernedBrowserKeychainOperationReceipt,
    GovernedBrowserOriginSessionOperation,
    GovernedBrowserOriginSessionRecipeRegistry,
    GovernedBrowserOriginSessionState,
    GovernedBrowserOriginSessionStateConflict,
    GovernedBrowserOriginSessionStore,
    build_governed_browser_credential_registration,
    build_governed_browser_origin_session_recipe,
    governed_browser_origin_session_operation_authority_ref,
    governed_browser_origin_session_ref,
)
from ultimate_ai_agent.core.time import utc_now


def _opaque_material(seed: int, length: int = 32) -> bytearray:
    return bytearray((seed + index) % 256 for index in range(length))


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
                "helper-receipt-ref:governed-browser-keychain:"
                f"{operation.value}-{len(self.calls)}"
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
            created=None,
            present=False,
            deleted_or_absent=True,
        )


def _lifecycle_context(
    *,
    target_kind: ExternalActionTargetKind = ExternalActionTargetKind.local_validation,
):  # type: ignore[no-untyped-def]
    base = _binding(suffix="lifecycle-base", target_kind=target_kind)
    registration = build_governed_browser_credential_registration(
        origin_ref=base.origin_ref,
        credential_handle_ref="credential-handle-ref:governed-browser:lifecycle",
        credential_generation_ref=(
            "credential-generation-ref:governed-browser:lifecycle-01"
        ),
    )
    generation_ref = "browser-session-generation-ref:governed-browser:session-01"
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
            suffix=f"lifecycle-{operation.value}",
            target_kind=target_kind,
        )
        binding = ExternalActionAuthorityBinding.model_validate(
            {
                **current.model_dump(mode="json"),
                "authority_capability": AuthorityCapability.execute,
                "field_schema_ref": registration.registration_ref,
                "resource_refs": [
                    _ref("resource", f"lifecycle-{operation.value}"),
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
    assert ambiguous.keychain_receipt is None
    assert ambiguous.session is None
    assert replay.receipt.status == "replayed"
    assert sum(operation == "delete" for operation, _ in keychain.calls) == 1
    assert registration.registration_ref not in keychain.present
    persisted = sessions.inspect(prepared.session.session_ref)
    assert persisted is not None
    assert persisted.state == GovernedBrowserOriginSessionState.prepared_inactive


def test_queue01_group06_verifier() -> None:
    assert verify() == []
