from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Event

import pytest

import ultimate_ai_agent.core.governed_browser.origin_sessions as origin_sessions_module
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
    GovernedBrowserOriginSessionStateConflict,
    GovernedBrowserOriginSessionStore,
    build_governed_browser_origin_session_recipe,
    governed_browser_origin_session_operation_authority_ref,
)
from ultimate_ai_agent.core.governed_browser.operation_proofs import (
    GovernedBrowserOperationProofError,
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


def test_request_normalization_failure_zeroizes_credential_material(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context()
    request, _ = contexts[
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
    malformed = ExactGovernedBrowserOriginSessionRequest.model_construct(
        recipe_ref="",
        execution_request=request,
    )
    material = bytearray(range(32))

    with pytest.raises(ValueError):
        service.execute(malformed, credential_material=material)

    assert all(value == 0 for value in material)
    assert keychain.calls == []


def test_service_binding_failure_zeroizes_credential_material(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context(suffix="binding-zeroize")
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
    service._registry = object()
    material = bytearray(range(32))

    with pytest.raises(
        GovernedBrowserOperationProofError,
        match="GOVERNED_BROWSER_OPERATION_PROOF_SERVICE_BINDING_INVALID",
    ):
        service.execute(
            ExactGovernedBrowserOriginSessionRequest(
                recipe_ref=recipe.recipe_ref,
                execution_request=request,
            ),
            credential_material=material,
        )

    assert material == bytearray(len(material))


def test_store_attestation_failure_zeroizes_credential_material(
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context(
        suffix="store-attestation-zeroize"
    )
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.enroll_credential
    ]
    kernel, _ = _authorized_kernel(tmp_path / "kernel", request)
    sessions = GovernedBrowserOriginSessionStore(
        tmp_path / "sessions.sqlite3"
    )
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=_FakeKeychain(),
        sessions=sessions,
    )
    sessions.path = tmp_path / "substituted.sqlite3"
    material = bytearray(range(32))

    with pytest.raises(
        GovernedBrowserOriginSessionStateConflict,
        match="GOVERNED_BROWSER_ORIGIN_SESSION_STORE_SOURCE_INVALID",
    ):
        service.execute(
            ExactGovernedBrowserOriginSessionRequest(
                recipe_ref=recipe.recipe_ref,
                execution_request=request,
            ),
            credential_material=material,
        )

    assert material == bytearray(len(material))


def test_throwing_clock_base_exception_zeroizes_credential_material(
    tmp_path: Path,
) -> None:
    class ClockFailure(BaseException):
        pass

    def fail_clock():  # type: ignore[no-untyped-def]
        raise ClockFailure

    _, contexts, registry = _lifecycle_context(suffix="clock-zeroize")
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.prepare_session
    ]
    kernel, _ = _authorized_kernel(tmp_path / "kernel", request)
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=_FakeKeychain(),
        sessions=GovernedBrowserOriginSessionStore(
            tmp_path / "sessions.sqlite3"
        ),
        clock=fail_clock,
    )
    material = bytearray(range(32))

    with pytest.raises(ClockFailure):
        service.execute(
            ExactGovernedBrowserOriginSessionRequest(
                recipe_ref=recipe.recipe_ref,
                execution_request=request,
            ),
            credential_material=material,
        )

    assert material == bytearray(len(material))


def test_timed_out_credential_dispatch_owns_an_independent_mutable_buffer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    coordination_timeout_seconds = 30.0
    _, contexts, registry = _lifecycle_context()
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.enroll_credential
    ]
    kernel, _ = _authorized_kernel(tmp_path / "kernel", request)
    kernel._dispatch_timeout_seconds = 0.01
    keychain = _FakeKeychain()
    original_store = keychain.store
    entered = Event()
    proceed = Event()
    dispatched_buffers: list[bytearray] = []
    dispatched_snapshots: list[bytes] = []

    def delayed_store(
        registration,  # type: ignore[no-untyped-def]
        *,
        request_ref: str,
        credential_material: bytearray,
    ):
        dispatched_buffers.append(credential_material)
        dispatched_snapshots.append(bytes(credential_material))
        entered.set()
        assert proceed.wait(timeout=coordination_timeout_seconds)
        return original_store(
            registration,
            request_ref=request_ref,
            credential_material=credential_material,
        )

    monkeypatch.setattr(keychain, "store", delayed_store)
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=keychain,
        sessions=GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3"),
    )
    material = bytearray(range(32))
    expected_material = bytes(material)
    exact = ExactGovernedBrowserOriginSessionRequest(
        recipe_ref=recipe.recipe_ref,
        execution_request=request,
    )

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            service.execute,
            exact,
            credential_material=material,
        )
        assert entered.wait(timeout=coordination_timeout_seconds)
        time.sleep(0.03)
        assert future.done() is False
        proceed.set()
        result = future.result(timeout=coordination_timeout_seconds)

    assert result.receipt.status == "outcome_ambiguous"
    assert material == bytearray(len(material))
    assert dispatched_snapshots == [expected_material]
    assert dispatched_buffers[0] is not material
    assert dispatched_buffers[0] == bytearray(len(dispatched_buffers[0]))


@pytest.mark.parametrize(
    "operation",
    list(GovernedBrowserOriginSessionOperation),
)
def test_operation_proof_failure_leaves_no_origin_session_mutation(
    operation: GovernedBrowserOriginSessionOperation,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, contexts, registry = _lifecycle_context(
        suffix=f"proof-failure-{operation.value}"
    )
    keychain = _FakeKeychain()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    if operation != GovernedBrowserOriginSessionOperation.enroll_credential:
        _execute(
            tmp_path=tmp_path / "baseline-enroll",
            operation=GovernedBrowserOriginSessionOperation.enroll_credential,
            contexts=contexts,
            registry=registry,
            keychain=keychain,
            sessions=sessions,
            material=bytearray(range(32)),
        )
    if operation in {
        GovernedBrowserOriginSessionOperation.revalidate_session,
        GovernedBrowserOriginSessionOperation.close_session,
        GovernedBrowserOriginSessionOperation.revoke_credential,
    }:
        _execute(
            tmp_path=tmp_path / "baseline-prepare",
            operation=GovernedBrowserOriginSessionOperation.prepare_session,
            contexts=contexts,
            registry=registry,
            keychain=keychain,
            sessions=sessions,
        )
    _, recipe = contexts[operation]
    before_keychain = set(keychain.present)
    before_session = sessions.inspect(recipe.session_ref)
    calls_before = len(keychain.calls)

    def fail_proof(*args, **kwargs):  # type: ignore[no-untyped-def]
        del args, kwargs
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_WRITE_FAILED"
        )

    monkeypatch.setattr(
        origin_sessions_module,
        "_record_operation_proof",
        fail_proof,
    )
    material = (
        bytearray(range(32))
        if operation
        == GovernedBrowserOriginSessionOperation.enroll_credential
        else None
    )

    result, _ = _execute(
        tmp_path=tmp_path / "proof-failure",
        operation=operation,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
        material=material,
    )

    assert result.receipt.status == "outcome_ambiguous"
    assert result.keychain_receipt is None
    assert result.session is None
    assert keychain.present == before_keychain
    assert sessions.inspect(recipe.session_ref) == before_session
    mutating_calls = [
        name for name, _ in keychain.calls[calls_before:] if name != "probe"
    ]
    assert mutating_calls == []
    if material is not None:
        assert material == bytearray(len(material))


@pytest.mark.parametrize(
    ("operation", "expected_presence"),
    (
        (
            GovernedBrowserOriginSessionOperation.enroll_credential,
            (False, True),
        ),
        (
            GovernedBrowserOriginSessionOperation.revoke_credential,
            (True, False),
        ),
    ),
)
def test_keychain_success_proof_follows_the_validated_helper_receipt(
    operation: GovernedBrowserOriginSessionOperation,
    expected_presence: tuple[bool, bool],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registration, contexts, registry = _lifecycle_context(
        suffix=f"keychain-proof-order-{operation.value}"
    )
    keychain = _FakeKeychain()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    if operation == GovernedBrowserOriginSessionOperation.revoke_credential:
        _execute(
            tmp_path=tmp_path / "baseline-enroll",
            operation=GovernedBrowserOriginSessionOperation.enroll_credential,
            contexts=contexts,
            registry=registry,
            keychain=keychain,
            sessions=sessions,
            material=bytearray(range(32)),
        )
        _execute(
            tmp_path=tmp_path / "baseline-prepare",
            operation=GovernedBrowserOriginSessionOperation.prepare_session,
            contexts=contexts,
            registry=registry,
            keychain=keychain,
            sessions=sessions,
        )
    original_record = origin_sessions_module._record_operation_proof
    observed: list[tuple[str, bool]] = []

    def record_with_helper_state(*args, **kwargs):  # type: ignore[no-untyped-def]
        material = kwargs["material"]
        if material.disposition in {
            "keychain_mutation_pending",
            "succeeded",
        }:
            observed.append(
                (
                    material.disposition,
                    registration.registration_ref in keychain.present,
                )
            )
        return original_record(*args, **kwargs)

    monkeypatch.setattr(
        origin_sessions_module,
        "_record_operation_proof",
        record_with_helper_state,
    )
    material = (
        bytearray(range(32))
        if operation
        == GovernedBrowserOriginSessionOperation.enroll_credential
        else None
    )

    result, _ = _execute(
        tmp_path=tmp_path / operation.value,
        operation=operation,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
        material=material,
    )

    assert result.receipt.status == (
        "credential_stored"
        if operation
        == GovernedBrowserOriginSessionOperation.enroll_credential
        else "credential_revoked"
    )
    assert observed == [
        ("keychain_mutation_pending", expected_presence[0]),
        ("succeeded", expected_presence[1]),
    ]


@pytest.mark.parametrize(
    "operation",
    [
        GovernedBrowserOriginSessionOperation.prepare_session,
        GovernedBrowserOriginSessionOperation.close_session,
        GovernedBrowserOriginSessionOperation.revoke_credential,
    ],
)
def test_proof_failure_hides_transition_from_cross_store_adopter(
    operation: GovernedBrowserOriginSessionOperation,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registration, contexts, registry = _lifecycle_context(
        suffix=f"proof-failure-adopter-{operation.value}"
    )
    keychain = _FakeKeychain()
    keychain.present.add(registration.registration_ref)
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    if operation != GovernedBrowserOriginSessionOperation.prepare_session:
        prepared, _ = _execute(
            tmp_path=tmp_path / "baseline-prepare",
            operation=GovernedBrowserOriginSessionOperation.prepare_session,
            contexts=contexts,
            registry=registry,
            keychain=keychain,
            sessions=sessions,
        )
        assert prepared.session is not None
    _, recipe = contexts[operation]
    before = sessions.inspect(recipe.session_ref)
    adopter_store = GovernedBrowserOriginSessionStore(
        tmp_path / "sessions.sqlite3"
    )
    actor_operation_ref = (
        "browser-origin-session-operation-ref:governed-browser:"
        f"proof-failure-adopter-{operation.value}"
    )
    actor_started = Event()
    actor_future = None

    def adopt_transition():  # type: ignore[no-untyped-def]
        actor_started.set()
        now = recipe.created_at + timedelta(seconds=1)
        if operation == GovernedBrowserOriginSessionOperation.prepare_session:
            return adopter_store.prepare(
                recipe,
                operation_ref=actor_operation_ref,
                now=now,
            )
        if operation == GovernedBrowserOriginSessionOperation.close_session:
            return adopter_store.close(
                recipe,
                operation_ref=actor_operation_ref,
                now=now,
            )
        return adopter_store.mark_revoked(
            recipe,
            operation_ref=actor_operation_ref,
            now=now,
        )

    def fail_proof(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal actor_future
        del args, kwargs
        actor_future = actor_pool.submit(adopt_transition)
        assert actor_started.wait(timeout=2)
        assert adopter_store.inspect(recipe.session_ref) == before
        time.sleep(0.03)
        assert actor_future.done() is False
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_WRITE_FAILED"
        )

    with ThreadPoolExecutor(max_workers=1) as actor_pool:
        monkeypatch.setattr(
            origin_sessions_module,
            "_record_operation_proof",
            fail_proof,
        )
        result, _ = _execute(
            tmp_path=tmp_path / "proof-failure",
            operation=operation,
            contexts=contexts,
            registry=registry,
            keychain=keychain,
            sessions=sessions,
        )
        assert actor_future is not None
        adopted = actor_future.result(timeout=2)

    assert result.receipt.status == "outcome_ambiguous"
    persisted = sessions.inspect(recipe.session_ref)
    assert adopted is not None
    assert persisted == adopted
    assert persisted.last_operation_ref == actor_operation_ref
    assert (
        sum(name == "delete" for name, _ in keychain.calls)
        == 0
    )


def test_revoke_delete_mutation_error_is_non_retryable_ambiguity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registration, contexts, registry = _lifecycle_context(
        suffix="revoke-delete-error"
    )
    keychain = _FakeKeychain()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    _execute(
        tmp_path=tmp_path / "baseline-enroll",
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
        material=bytearray(range(32)),
    )
    prepared, _ = _execute(
        tmp_path=tmp_path / "baseline-prepare",
        operation=GovernedBrowserOriginSessionOperation.prepare_session,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    assert prepared.session is not None

    def mutate_then_fail(
        registration,  # type: ignore[no-untyped-def]
        *,
        request_ref: str,
    ):  # type: ignore[no-untyped-def]
        keychain.calls.append(("delete", request_ref))
        keychain.present.discard(registration.registration_ref)
        raise GovernedBrowserKeychainError(
            "GOVERNED_BROWSER_KEYCHAIN_HELPER_EXECUTION_FAILED"
        )

    monkeypatch.setattr(keychain, "delete", mutate_then_fail)
    ambiguous, service = _execute(
        tmp_path=tmp_path / "revoke",
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
    assert ambiguous.receipt.automatic_retry_allowed is False
    assert replay.receipt.status == "replayed"
    assert sum(name == "delete" for name, _ in keychain.calls) == 1
    assert registration.registration_ref not in keychain.present
    assert sessions.inspect(recipe.session_ref) == prepared.session


def test_revoke_commit_failure_after_delete_has_exact_ambiguity_proof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registration, contexts, registry = _lifecycle_context(
        suffix="revoke-commit-failure"
    )
    keychain = _FakeKeychain()
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    _execute(
        tmp_path=tmp_path / "baseline-enroll",
        operation=GovernedBrowserOriginSessionOperation.enroll_credential,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
        material=bytearray(range(32)),
    )
    prepared, _ = _execute(
        tmp_path=tmp_path / "baseline-prepare",
        operation=GovernedBrowserOriginSessionOperation.prepare_session,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    assert prepared.session is not None

    def fail_commit(
        pending: origin_sessions_module._PendingOriginSessionTransition,
    ):  # type: ignore[no-untyped-def]
        pending.rollback()
        raise GovernedBrowserOriginSessionStateConflict(
            "GOVERNED_BROWSER_ORIGIN_SESSION_COMMIT_FAILED"
        )

    monkeypatch.setattr(
        origin_sessions_module._PendingOriginSessionTransition,
        "commit",
        fail_commit,
    )
    ambiguous, service = _execute(
        tmp_path=tmp_path / "revoke",
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
    assert ambiguous.receipt.automatic_retry_allowed is False
    external_snapshot = ambiguous.receipt.external_receipt_snapshot
    assert external_snapshot is not None
    exact_evidence_refs = external_snapshot.evidence_refs
    assert len(exact_evidence_refs) == 4
    assert exact_evidence_refs[0].startswith(
        "evidence-ref:governed-browser-origin-session:state-conflict:"
    )
    assert exact_evidence_refs[1].startswith(
        "helper-receipt-ref:governed-browser-keychain:"
    )
    assert exact_evidence_refs[2] == recipe.keychain_item_ref
    assert exact_evidence_refs[3].startswith(
        "operation-proof-ref:governed-browser:"
    )
    assert replay.receipt.status == "replayed"
    replay_snapshot = replay.receipt.external_receipt_snapshot
    assert replay_snapshot is not None
    assert replay_snapshot.evidence_refs == exact_evidence_refs
    assert registration.registration_ref not in keychain.present
    assert sessions.inspect(recipe.session_ref) == prepared.session


@pytest.mark.parametrize(
    "operation",
    [
        GovernedBrowserOriginSessionOperation.prepare_session,
        GovernedBrowserOriginSessionOperation.revalidate_session,
        GovernedBrowserOriginSessionOperation.close_session,
    ],
)
def test_session_commit_failure_after_preproof_is_non_retryable_ambiguity(
    operation: GovernedBrowserOriginSessionOperation,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registration, contexts, registry = _lifecycle_context(
        suffix=f"commit-failure-{operation.value}"
    )
    keychain = _FakeKeychain()
    keychain.present.add(registration.registration_ref)
    sessions = GovernedBrowserOriginSessionStore(tmp_path / "sessions.sqlite3")
    if operation != GovernedBrowserOriginSessionOperation.prepare_session:
        prepared, _ = _execute(
            tmp_path=tmp_path / "baseline-prepare",
            operation=GovernedBrowserOriginSessionOperation.prepare_session,
            contexts=contexts,
            registry=registry,
            keychain=keychain,
            sessions=sessions,
        )
        assert prepared.session is not None
    _, recipe = contexts[operation]
    before = sessions.inspect(recipe.session_ref)

    def fail_commit(
        pending: origin_sessions_module._PendingOriginSessionTransition,
    ):  # type: ignore[no-untyped-def]
        pending.rollback()
        raise GovernedBrowserOriginSessionStateConflict(
            "GOVERNED_BROWSER_ORIGIN_SESSION_COMMIT_FAILED"
        )

    monkeypatch.setattr(
        origin_sessions_module._PendingOriginSessionTransition,
        "commit",
        fail_commit,
    )
    ambiguous, service = _execute(
        tmp_path=tmp_path / operation.value,
        operation=operation,
        contexts=contexts,
        registry=registry,
        keychain=keychain,
        sessions=sessions,
    )
    request, _ = contexts[operation]
    replay = service.execute(
        ExactGovernedBrowserOriginSessionRequest(
            recipe_ref=recipe.recipe_ref,
            execution_request=request,
        )
    )

    assert ambiguous.receipt.status == "outcome_ambiguous"
    assert ambiguous.receipt.automatic_retry_allowed is False
    assert replay.receipt.status == "replayed"
    assert sessions.inspect(recipe.session_ref) == before


def test_native_helper_bounds_stdin_and_disables_authentication_ui() -> None:
    source = (
        "tools/macos/governed-browser-keychain-helper/"
        "Sources/UAAGovernedBrowserKeychainHelper/main.swift"
    )
    text = Path(source).read_text(encoding="utf-8")

    assert "readDataToEndOfFile" not in text
    assert "readBoundedStandardInput" in text
    assert "read(upToCount: remaining)" in text
    assert "maximumInputBytes + 1 - input.count" in text
    assert "context.interactionNotAllowed = true" in text
    assert "kSecUseAuthenticationContext as String: context" in text
