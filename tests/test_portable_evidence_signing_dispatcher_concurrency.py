from __future__ import annotations

import threading
from contextlib import contextmanager
from pathlib import Path

import pytest

from tests.test_authority_dispatcher import _approval
from tests.test_portable_evidence_signing_dispatcher import (
    _FakeManagedBackend,
    _create_active_key,
    _lease,
    _request,
)
from tests.test_portable_mission_evidence import _bundle
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityCapability, AuthorityLeaseStore
from ultimate_ai_agent.core.authority.dispatcher import AuthorityDispatcher
from ultimate_ai_agent.core.evidence_signing.artifact_store import (
    PortableEvidenceSignedArtifactStore,
)
from ultimate_ai_agent.core.evidence_signing.dispatcher_adapter import (
    PortableEvidenceSigningAuthorityAdapter,
    PortableEvidenceSigningOperation,
)
from ultimate_ai_agent.core.evidence_signing.lifecycle import (
    PortableEvidenceKeyLifecycleLedger,
)


def test_concurrent_started_replay_does_not_release_winning_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "authority"
    store = AuthorityLeaseStore(state_dir)
    lifecycle = PortableEvidenceKeyLifecycleLedger(state_dir / "signing")
    backend = _FakeManagedBackend()
    key_ref, key_version_ref = _create_active_key(
        state_dir=state_dir,
        store=store,
        lifecycle=lifecycle,
        backend=backend,
        suffix="concurrent-bundle",
    )
    adapter = PortableEvidenceSigningAuthorityAdapter(
        operation=PortableEvidenceSigningOperation.bundle_sign,
        backend=backend,
        lifecycle=lifecycle,
        lease_store=store,
        safe_disable_engaged=lambda: False,
        artifact_store=PortableEvidenceSignedArtifactStore(state_dir / "signing"),
    )
    bundle = _bundle(tmp_path / "concurrent-bundle-source")
    resources = adapter.binding_resource_refs | {
        key_ref,
        key_version_ref,
        bundle.bundle_ref,
        bundle.terminal_entry_hash_ref,
    }
    lease = _lease(
        store,
        capability=AuthorityCapability.execute,
        resources=resources,
        suffix="concurrent-bundle",
    )
    pending = _request(
        adapter=adapter,
        lease_ref=lease.lease_ref,
        resources=resources,
        metadata={
            "operation": "bundle_sign",
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
            "bundle_ref": bundle.bundle_ref,
            "bundle_terminal_entry_hash_ref": bundle.terminal_entry_hash_ref,
        },
        suffix="concurrent-bundle",
    )
    approval = LocalApprovalAuthority()
    request = pending.model_copy(
        update={"approval_validation_request": _approval(approval, pending)}
    )
    adapter.bind_bundle(dispatch_ref=request.dispatch_ref, bundle=bundle)
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=store,
        approval_authority=approval,
    )
    entered = threading.Event()
    release = threading.Event()
    original_invoke = adapter.invoke

    def blocking_invoke(request_value):  # type: ignore[no-untyped-def]
        entered.set()
        assert release.wait(timeout=5)
        return original_invoke(request_value)

    monkeypatch.setattr(adapter, "invoke", blocking_invoke)
    winner_results = []
    winner = threading.Thread(
        target=lambda: winner_results.append(dispatcher.dispatch(request)),
        daemon=True,
    )
    winner.start()
    assert entered.wait(timeout=5)

    replay = dispatcher.dispatch(request)

    assert replay.receipt.status == "started"
    assert replay.recovery_required is True
    assert request.dispatch_ref in adapter._pending_bundles

    recovery_adapter = PortableEvidenceSigningAuthorityAdapter(
        operation=PortableEvidenceSigningOperation.bundle_sign,
        backend=backend,
        lifecycle=lifecycle,
        lease_store=store,
        safe_disable_engaged=lambda: False,
        artifact_store=PortableEvidenceSignedArtifactStore(state_dir / "signing"),
    )
    recovery_adapter.bind_bundle(dispatch_ref=request.dispatch_ref, bundle=bundle)
    recovery_dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[recovery_adapter],
        lease_store=store,
        approval_authority=approval,
    )
    recovery_replay = recovery_dispatcher.dispatch(request)
    assert recovery_replay.receipt.status == "started"
    assert recovery_replay.recovery_required is True
    assert request.dispatch_ref not in recovery_adapter._pending_bundles
    assert request.dispatch_ref in adapter._pending_bundles

    release.set()
    winner.join(timeout=5)
    assert not winner.is_alive()
    assert winner_results[0].receipt.status == "succeeded"
    assert backend.sign_count == 1


def test_post_start_invoke_does_not_reverse_authority_lifecycle_lock_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "authority"
    store = AuthorityLeaseStore(state_dir)
    lifecycle = PortableEvidenceKeyLifecycleLedger(state_dir / "signing")
    backend = _FakeManagedBackend()
    key_ref, key_version_ref = _create_active_key(
        state_dir=state_dir,
        store=store,
        lifecycle=lifecycle,
        backend=backend,
        suffix="lock-order",
    )
    adapter = PortableEvidenceSigningAuthorityAdapter(
        operation=PortableEvidenceSigningOperation.key_mark_lost,
        backend=backend,
        lifecycle=lifecycle,
        lease_store=store,
        safe_disable_engaged=lambda: False,
        artifact_store=PortableEvidenceSignedArtifactStore(state_dir / "signing"),
    )
    resources = adapter.binding_resource_refs | {key_ref, key_version_ref}
    lease = _lease(
        store,
        capability=AuthorityCapability.mutate,
        resources=resources,
        suffix="lock-order",
    )
    request = _request(
        adapter=adapter,
        lease_ref=lease.lease_ref,
        resources=resources,
        metadata={
            "operation": "key_mark_lost",
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
        },
        suffix="lock-order",
    )
    result_sentinel = object()
    lifecycle_locked = False
    list_calls = 0
    original_operation_lock = lifecycle.operation_lock
    original_list_leases = store.list_leases

    @contextmanager
    def tracked_operation_lock():  # type: ignore[no-untyped-def]
        nonlocal lifecycle_locked
        with original_operation_lock():
            lifecycle_locked = True
            try:
                yield
            finally:
                lifecycle_locked = False

    def checked_list_leases(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal list_calls
        assert lifecycle_locked is False
        list_calls += 1
        return original_list_leases(*args, **kwargs)

    monkeypatch.setattr(lifecycle, "operation_lock", tracked_operation_lock)
    monkeypatch.setattr(store, "list_leases", checked_list_leases)
    monkeypatch.setattr(adapter, "_invoke_locked", lambda _request: result_sentinel)

    assert adapter.invoke(request) is result_sentinel
    assert list_calls == 1

    assert adapter.runtime_prestart_reason_refs(request) == []
    assert list_calls == 2

    invalid = request.model_copy(
        update={"lease_ref": "authority-lease-ref:portable-evidence:missing"}
    )
    with pytest.raises(
        RuntimeError,
        match="PORTABLE_EVIDENCE_SIGNING_PRESTART_STATE_CHANGED",
    ):
        adapter.invoke(invalid)
    assert list_calls == 3
