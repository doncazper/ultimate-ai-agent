from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from tests.test_governed_browser_queue01_group01 import _authorized_kernel, _request
from tests.test_governed_browser_queue01_group06 import (
    _FakeKeychain,
    _execute,
    _lifecycle_context,
)
from ultimate_ai_agent.core.governed_browser import (
    ExactGovernedBrowserOriginSessionRequest,
    ExactGovernedBrowserOriginSessionService,
    ExternalActionAuthorityBinding,
    GovernedBrowserKeychainError,
    GovernedBrowserOriginSessionOperation,
    GovernedBrowserOriginSessionRecipeRegistry,
    GovernedBrowserOriginSessionState,
    GovernedBrowserOriginSessionStore,
    build_governed_browser_origin_session_recipe,
    governed_browser_origin_session_operation_authority_ref,
)
from ultimate_ai_agent.core.time import utc_now


def test_lifecycle_approval_scope_binds_exactly_one_operation() -> None:
    registration, contexts, _ = _lifecycle_context()
    for operation, (request, recipe) in contexts.items():
        expected = governed_browser_origin_session_operation_authority_ref(
            registration_ref=registration.registration_ref,
            session_generation_ref=recipe.session_generation_ref,
            operation=operation,
        )
        assert recipe.operation_authority_ref == expected
        assert tuple(
            ref
            for ref in request.binding.resource_refs
            if ref.startswith(
                "browser-origin-session-operation-authority-ref:"
                "governed-browser:"
            )
        ) == (expected,)

    prepare_request, prepare_recipe = contexts[
        GovernedBrowserOriginSessionOperation.prepare_session
    ]
    with pytest.raises(ValueError, match="OPERATION_AUTHORITY_MISMATCH"):
        build_governed_browser_origin_session_recipe(
            prepare_request,
            registration=registration,
            operation=GovernedBrowserOriginSessionOperation.revoke_credential,
            session_generation_ref=prepare_recipe.session_generation_ref,
            created_at=prepare_recipe.created_at,
            expires_at=prepare_recipe.expires_at,
        )

    revoke_ref = governed_browser_origin_session_operation_authority_ref(
        registration_ref=registration.registration_ref,
        session_generation_ref=prepare_recipe.session_generation_ref,
        operation=GovernedBrowserOriginSessionOperation.revoke_credential,
    )
    overbroad_binding = ExternalActionAuthorityBinding.model_validate(
        {
            **prepare_request.binding.model_dump(mode="json"),
            "resource_refs": [*prepare_request.binding.resource_refs, revoke_ref],
        }
    )
    with pytest.raises(ValueError, match="OPERATION_AUTHORITY_MISMATCH"):
        build_governed_browser_origin_session_recipe(
            _request(overbroad_binding),
            registration=registration,
            operation=GovernedBrowserOriginSessionOperation.prepare_session,
            session_generation_ref=prepare_recipe.session_generation_ref,
            created_at=prepare_recipe.created_at,
            expires_at=prepare_recipe.expires_at,
        )


def test_expired_prepare_is_blocked_before_keychain_or_state_write(
    tmp_path: Path,
) -> None:
    registration, contexts, _ = _lifecycle_context()
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.prepare_session
    ]
    created_at = utc_now() - timedelta(minutes=20)
    expired_recipe = build_governed_browser_origin_session_recipe(
        request,
        registration=registration,
        operation=GovernedBrowserOriginSessionOperation.prepare_session,
        session_generation_ref=recipe.session_generation_ref,
        created_at=created_at,
        expires_at=created_at + timedelta(minutes=5),
    )
    registry = GovernedBrowserOriginSessionRecipeRegistry(
        registrations=[registration],
        recipes=[expired_recipe],
    )
    kernel, _ = _authorized_kernel(tmp_path / "kernel", request)
    keychain = _FakeKeychain()
    keychain.present.add(registration.registration_ref)
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=keychain,
        sessions=sessions,
    )

    result = service.execute(
        ExactGovernedBrowserOriginSessionRequest(
            recipe_ref=expired_recipe.recipe_ref,
            execution_request=request,
        )
    )

    assert result.receipt.status == "blocked"
    assert result.receipt.external_action_receipt_ref is None
    assert keychain.calls == []
    assert sessions.inspect(expired_recipe.session_ref) is None


def test_service_rejects_immutable_credential_buffer_without_masking_result(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context()
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.enroll_credential
    ]
    kernel, _ = _authorized_kernel(tmp_path / "kernel", request)
    keychain = _FakeKeychain()
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=keychain,
        sessions=GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3"),
    )

    result = service.execute(
        ExactGovernedBrowserOriginSessionRequest(
            recipe_ref=recipe.recipe_ref,
            execution_request=request,
        ),
        credential_material=bytes(range(32)),  # type: ignore[arg-type]
    )

    assert result.receipt.status == "blocked"
    assert result.receipt.external_action_receipt_ref is None
    assert keychain.calls == []


def test_missing_credential_probe_is_failed_not_ambiguous_and_not_retried(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context()
    keychain = _FakeKeychain()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    failed, service = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.prepare_session,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.prepare_session
    ]
    replay = service.execute(
        ExactGovernedBrowserOriginSessionRequest(
            recipe_ref=recipe.recipe_ref,
            execution_request=request,
        )
    )

    assert failed.receipt.status == "failed"
    assert failed.receipt.replayed is False
    assert failed.session is None
    assert replay.receipt.status == "replayed"
    assert [operation for operation, _ in keychain.calls] == ["probe"]
    assert sessions.inspect(recipe.session_ref) is None


def test_native_helper_rejects_duplicate_stores() -> None:
    source = (
        "tools/macos/governed-browser-keychain-helper/"
        "Sources/UAAGovernedBrowserKeychainHelper/main.swift"
    )
    text = Path(source).read_text(encoding="utf-8")
    assert "HELPER_CREDENTIAL_ALREADY_EXISTS" in text
    assert text.count("throw HelperFailure.credentialAlreadyExists") == 2


def test_non_mutating_keychain_preconditions_are_not_ambiguous(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registration, contexts, registry = _lifecycle_context()
    enroll_request, enroll_recipe = contexts[
        GovernedBrowserOriginSessionOperation.enroll_credential
    ]
    untrusted_keychain = _FakeKeychain()

    def untrusted_store(*args, **kwargs):  # type: ignore[no-untyped-def]
        del args, kwargs
        untrusted_keychain.calls.append(("store", "request-ref:redacted"))
        raise GovernedBrowserKeychainError(
            "GOVERNED_BROWSER_KEYCHAIN_HELPER_FINGERPRINT_MISMATCH"
        )

    monkeypatch.setattr(untrusted_keychain, "store", untrusted_store)
    untrusted_kernel, _ = _authorized_kernel(
        tmp_path / "untrusted-kernel",
        enroll_request,
    )
    untrusted_service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=untrusted_kernel,
        keychain=untrusted_keychain,
        sessions=GovernedBrowserOriginSessionStore(
            tmp_path / "untrusted-sessions.sqlite3"
        ),
    )
    material = bytearray(range(32))
    enroll_exact = ExactGovernedBrowserOriginSessionRequest(
        recipe_ref=enroll_recipe.recipe_ref,
        execution_request=enroll_request,
    )
    failed_untrusted = untrusted_service.execute(
        enroll_exact,
        credential_material=material,
    )
    replay_material = bytearray(range(32))
    replay_untrusted = untrusted_service.execute(
        enroll_exact,
        credential_material=replay_material,
    )
    assert failed_untrusted.receipt.status == "failed"
    assert replay_untrusted.receipt.status == "replayed"
    assert [operation for operation, _ in untrusted_keychain.calls] == ["store"]
    assert all(value == 0 for value in material)
    assert all(value == 0 for value in replay_material)

    prepare_request, prepare_recipe = contexts[
        GovernedBrowserOriginSessionOperation.prepare_session
    ]
    locked_keychain = _FakeKeychain()
    locked_keychain.present.add(registration.registration_ref)

    def locked_probe(*args, **kwargs):  # type: ignore[no-untyped-def]
        del args, kwargs
        locked_keychain.calls.append(("probe", "request-ref:redacted"))
        raise GovernedBrowserKeychainError("GOVERNED_BROWSER_KEYCHAIN_LOCKED")

    monkeypatch.setattr(locked_keychain, "probe", locked_probe)
    locked_kernel, _ = _authorized_kernel(
        tmp_path / "locked-kernel",
        prepare_request,
    )
    locked_service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=locked_kernel,
        keychain=locked_keychain,
        sessions=GovernedBrowserOriginSessionStore(
            tmp_path / "locked-sessions.sqlite3"
        ),
    )
    exact = ExactGovernedBrowserOriginSessionRequest(
        recipe_ref=prepare_recipe.recipe_ref,
        execution_request=prepare_request,
    )
    failed = locked_service.execute(exact)
    replay = locked_service.execute(exact)

    assert failed.receipt.status == "failed"
    assert replay.receipt.status == "replayed"
    assert [operation for operation, _ in locked_keychain.calls] == ["probe"]


def test_expired_revalidation_persists_expiry_but_reports_failure(
    tmp_path: Path,
) -> None:
    registration, contexts, registry = _lifecycle_context()
    keychain = _FakeKeychain()
    keychain.present.add(registration.registration_ref)
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    prepared, _ = _execute(
        tmp_path=tmp_path,
        operation=GovernedBrowserOriginSessionOperation.prepare_session,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    assert prepared.session is not None

    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.revalidate_session
    ]
    kernel, _ = _authorized_kernel(tmp_path / "revalidate-kernel", request)
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=keychain,
        sessions=sessions,
        clock=lambda: recipe.expires_at + timedelta(seconds=1),
    )
    result = service.execute(
        ExactGovernedBrowserOriginSessionRequest(
            recipe_ref=recipe.recipe_ref,
            execution_request=request,
        )
    )

    assert result.receipt.status == "failed"
    assert result.session is None
    persisted = sessions.inspect(recipe.session_ref)
    assert persisted is not None
    assert persisted.state == GovernedBrowserOriginSessionState.expired.value
