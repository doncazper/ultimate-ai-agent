from __future__ import annotations

from pathlib import Path

import pytest

from tests.test_portable_evidence_signing_dispatcher import (
    _FakeManagedBackend,
    _adapter_setup,
    _approved_dispatch,
    _create_active_key,
    _lease,
    _request,
)
from tests.test_portable_mission_evidence import _bundle
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityLeaseStore,
)
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


def test_rotation_binds_exact_predecessor_and_settles_retired_key_deletion(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "authority"
    store = AuthorityLeaseStore(state_dir)
    lifecycle = PortableEvidenceKeyLifecycleLedger(state_dir / "signing")
    backend = _FakeManagedBackend()
    key_ref, predecessor_ref = _create_active_key(
        state_dir=state_dir,
        store=store,
        lifecycle=lifecycle,
        backend=backend,
        suffix="rotation",
    )
    adapter = PortableEvidenceSigningAuthorityAdapter(
        operation=PortableEvidenceSigningOperation.key_rotate,
        backend=backend,
        lifecycle=lifecycle,
        lease_store=store,
        safe_disable_engaged=lambda: False,
        artifact_store=PortableEvidenceSignedArtifactStore(state_dir / "signing"),
    )
    next_ref = "signing-key-version-ref:portable-evidence:rotation:2"
    stale_ref = "signing-key-version-ref:portable-evidence:rotation:stale"
    stale_resources = adapter.binding_resource_refs | {key_ref, next_ref, stale_ref}
    denied, _request_value = _approved_dispatch(
        state_dir=state_dir,
        store=store,
        adapter=adapter,
        resources=stale_resources,
        metadata={
            "operation": "key_rotate",
            "key_ref": key_ref,
            "key_version_ref": next_ref,
            "predecessor_key_version_ref": stale_ref,
        },
        suffix="rotation-stale",
    )
    assert denied.receipt.status == "denied"
    assert "reason-ref:portable-evidence-signing:predecessor-mismatch" in (
        denied.receipt.reason_refs
    )
    assert backend.create_count == 1

    resources = adapter.binding_resource_refs | {key_ref, next_ref, predecessor_ref}
    result, _request_value = _approved_dispatch(
        state_dir=state_dir,
        store=store,
        adapter=adapter,
        resources=resources,
        metadata={
            "operation": "key_rotate",
            "key_ref": key_ref,
            "key_version_ref": next_ref,
            "predecessor_key_version_ref": predecessor_ref,
        },
        suffix="rotation-exact",
    )
    assert result.receipt.status == "succeeded"
    assert lifecycle.inspect().status == "active"
    assert predecessor_ref not in backend.keys
    assert next_ref in backend.keys


def test_failed_revocation_deletion_is_recoverable_only_through_exact_cleanup(
    tmp_path: Path,
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
        suffix="revocation-cleanup",
    )
    revoke = PortableEvidenceSigningAuthorityAdapter(
        operation=PortableEvidenceSigningOperation.key_revoke,
        backend=backend,
        lifecycle=lifecycle,
        lease_store=store,
        safe_disable_engaged=lambda: False,
        artifact_store=PortableEvidenceSignedArtifactStore(state_dir / "signing"),
    )
    revocation_ref = "revocation-ref:portable-evidence:revocation-cleanup"
    resources = revoke.binding_resource_refs | {
        key_ref,
        key_version_ref,
        revocation_ref,
    }
    backend.fail_delete = True
    failed, _request_value = _approved_dispatch(
        state_dir=state_dir,
        store=store,
        adapter=revoke,
        resources=resources,
        metadata={
            "operation": "key_revoke",
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
            "revocation_ref": revocation_ref,
        },
        suffix="revocation-delete-fails",
    )
    assert failed.receipt.status != "succeeded"
    assert lifecycle.inspect().status == "revoked_deletion_pending"
    assert key_version_ref in backend.keys

    cleanup = PortableEvidenceSigningAuthorityAdapter(
        operation=PortableEvidenceSigningOperation.key_material_cleanup,
        backend=backend,
        lifecycle=lifecycle,
        lease_store=store,
        safe_disable_engaged=lambda: False,
        artifact_store=PortableEvidenceSignedArtifactStore(state_dir / "signing"),
    )
    cleanup_resources = cleanup.binding_resource_refs | {
        key_ref,
        key_version_ref,
        revocation_ref,
    }
    backend.fail_delete = False
    recovered, _request_value = _approved_dispatch(
        state_dir=state_dir,
        store=store,
        adapter=cleanup,
        resources=cleanup_resources,
        metadata={
            "operation": "key_material_cleanup",
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
            "revocation_ref": revocation_ref,
            "deletion_reason": "revocation",
        },
        suffix="revocation-delete-recovery",
    )
    assert recovered.receipt.status == "succeeded"
    assert lifecycle.inspect().status == "revoked"
    assert key_version_ref not in backend.keys


def test_safe_disable_flip_is_rechecked_inside_locked_prestart_boundary(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "authority"
    store = AuthorityLeaseStore(state_dir)
    lifecycle = PortableEvidenceKeyLifecycleLedger(state_dir / "signing")
    backend = _FakeManagedBackend()
    calls = 0

    def safe_disabled() -> bool:
        nonlocal calls
        calls += 1
        return calls >= 2

    adapter = PortableEvidenceSigningAuthorityAdapter(
        operation=PortableEvidenceSigningOperation.key_create,
        backend=backend,
        lifecycle=lifecycle,
        lease_store=store,
        safe_disable_engaged=safe_disabled,
        artifact_store=PortableEvidenceSignedArtifactStore(state_dir / "signing"),
    )
    key_ref = "signing-key-ref:portable-evidence:safe-disable"
    key_version_ref = "signing-key-version-ref:portable-evidence:safe-disable:1"
    resources = adapter.binding_resource_refs | {key_ref, key_version_ref}
    result, _request_value = _approved_dispatch(
        state_dir=state_dir,
        store=store,
        adapter=adapter,
        resources=resources,
        metadata={
            "operation": "key_create",
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
        },
        suffix="safe-disable-race",
    )
    assert result.receipt.status != "succeeded"
    assert backend.create_count == 0
    assert backend.readiness_count == 0
    assert backend.probe_count == 0


def test_pending_unsigned_bundle_bindings_are_bounded(tmp_path: Path) -> None:
    state_dir, store, lifecycle, backend, adapter = _adapter_setup(
        tmp_path,
        PortableEvidenceSigningOperation.bundle_sign,
    )
    del state_dir, store, lifecycle, backend
    bundle = _bundle(tmp_path / "bundle-limit")
    for index in range(8):
        adapter.bind_bundle(
            dispatch_ref=f"authority-dispatch-ref:portable-evidence:pending:{index}",
            bundle=bundle,
        )
    with pytest.raises(
        ValueError,
        match="PORTABLE_EVIDENCE_PENDING_BUNDLE_LIMIT_EXCEEDED",
    ):
        adapter.bind_bundle(
            dispatch_ref="authority-dispatch-ref:portable-evidence:pending:overflow",
            bundle=bundle,
        )


def test_corrupt_lifecycle_denies_before_dispatcher_start(tmp_path: Path) -> None:
    state_dir = tmp_path / "authority"
    signing_dir = state_dir / "signing"
    signing_dir.mkdir(parents=True, mode=0o700)
    ledger_path = signing_dir / "portable_evidence_key_lifecycle.jsonl"
    ledger_path.write_text('"unsafe-state-sentinel"\n', encoding="utf-8")
    ledger_path.chmod(0o600)
    store = AuthorityLeaseStore(state_dir)
    lifecycle = PortableEvidenceKeyLifecycleLedger(signing_dir)
    backend = _FakeManagedBackend()
    adapter = PortableEvidenceSigningAuthorityAdapter(
        operation=PortableEvidenceSigningOperation.key_create,
        backend=backend,
        lifecycle=lifecycle,
        lease_store=store,
        safe_disable_engaged=lambda: False,
        artifact_store=PortableEvidenceSignedArtifactStore(signing_dir),
    )
    key_ref = "signing-key-ref:portable-evidence:corrupt-denied"
    key_version_ref = "signing-key-version-ref:portable-evidence:corrupt-denied:1"
    resources = adapter.binding_resource_refs | {key_ref, key_version_ref}

    result, _request_value = _approved_dispatch(
        state_dir=state_dir,
        store=store,
        adapter=adapter,
        resources=resources,
        metadata={
            "operation": "key_create",
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
        },
        suffix="corrupt-lifecycle-denied",
    )

    assert result.receipt.status == "denied"
    assert "reason-ref:portable-evidence-signing:lifecycle-state-invalid" in (
        result.receipt.reason_refs
    )
    assert backend.create_count == 0


def test_unapproved_active_key_request_never_probes_helper_or_keychain(
    tmp_path: Path,
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
        suffix="unapproved-probe-denied",
    )
    baseline_readiness = backend.readiness_count
    baseline_probes = backend.probe_count
    adapter = PortableEvidenceSigningAuthorityAdapter(
        operation=PortableEvidenceSigningOperation.key_revoke,
        backend=backend,
        lifecycle=lifecycle,
        lease_store=store,
        safe_disable_engaged=lambda: False,
        artifact_store=PortableEvidenceSignedArtifactStore(state_dir / "signing"),
    )
    revocation_ref = "revocation-ref:portable-evidence:unapproved-probe-denied"
    resources = adapter.binding_resource_refs | {
        key_ref,
        key_version_ref,
        revocation_ref,
    }
    lease = _lease(
        store,
        capability=AuthorityCapability.mutate,
        resources=resources,
        suffix="unapproved-probe-denied",
    )
    request = _request(
        adapter=adapter,
        lease_ref=lease.lease_ref,
        resources=resources,
        metadata={
            "operation": "key_revoke",
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
            "revocation_ref": revocation_ref,
        },
        suffix="unapproved-probe-denied",
    )

    result = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=store,
        approval_authority=LocalApprovalAuthority(),
    ).dispatch(request)

    assert result.receipt.status == "denied"
    assert backend.readiness_count == baseline_readiness
    assert backend.probe_count == baseline_probes


@pytest.mark.parametrize(
    ("operation", "extra_metadata", "extra_resource"),
    [
        (PortableEvidenceSigningOperation.key_mark_lost, {}, None),
        (
            PortableEvidenceSigningOperation.key_revoke,
            {"revocation_ref": "revocation-ref:portable-evidence:absent-key"},
            "revocation-ref:portable-evidence:absent-key",
        ),
    ],
)
def test_terminal_key_postures_settle_when_key_material_is_already_absent(
    tmp_path: Path,
    operation: PortableEvidenceSigningOperation,
    extra_metadata: dict[str, str],
    extra_resource: str | None,
) -> None:
    state_dir = tmp_path / operation.value
    store = AuthorityLeaseStore(state_dir)
    lifecycle = PortableEvidenceKeyLifecycleLedger(state_dir / "signing")
    backend = _FakeManagedBackend()
    key_ref, key_version_ref = _create_active_key(
        state_dir=state_dir,
        store=store,
        lifecycle=lifecycle,
        backend=backend,
        suffix=operation.value,
    )
    backend.keys.pop(key_version_ref)
    adapter = PortableEvidenceSigningAuthorityAdapter(
        operation=operation,
        backend=backend,
        lifecycle=lifecycle,
        lease_store=store,
        safe_disable_engaged=lambda: False,
        artifact_store=PortableEvidenceSignedArtifactStore(state_dir / "signing"),
    )
    resources = adapter.binding_resource_refs | {key_ref, key_version_ref}
    if extra_resource is not None:
        resources.add(extra_resource)
    result, _request_value = _approved_dispatch(
        state_dir=state_dir,
        store=store,
        adapter=adapter,
        resources=resources,
        metadata={
            "operation": operation.value,
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
            **extra_metadata,
        },
        suffix=f"{operation.value}-absent-key",
    )

    assert result.receipt.status == "succeeded"
    assert lifecycle.inspect().status == (
        "lost"
        if operation == PortableEvidenceSigningOperation.key_mark_lost
        else "revoked"
    )
    assert backend.probe_count == 0
