import os
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AUTHORITY_LEASE_KILL_SWITCH_ENV,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.extension_catalog import (
    ExtensionInstallDisabledAuthorityState,
    ExtensionInstallDisabledRecordReceipt,
    ExtensionInstallDisabledRecordStore,
    build_extension_install_disabled_approval_request,
    build_extension_install_disabled_delete_approval_request,
    build_extension_install_disabled_record_delete_receipt,
    build_extension_install_disabled_record_receipt,
)
from ultimate_ai_agent.core.extension_catalog import install_disabled as install_module


@dataclass(frozen=True)
class _StoreTestAuthority:
    receipt: ExtensionInstallDisabledRecordReceipt
    approval_authority: LocalApprovalAuthority
    lease: AuthorityLease
    authority_state: ExtensionInstallDisabledAuthorityState

    def record(self, store: ExtensionInstallDisabledRecordStore):
        return store.record_receipt(
            self.receipt,
            authority_state=self.authority_state,
            approval_authority=self.approval_authority,
        )


def _build_store_test_authority(suffix: str) -> _StoreTestAuthority:
    approval_authority = LocalApprovalAuthority()
    request = approval_authority.create_request(
        build_extension_install_disabled_approval_request()
    )
    grant = approval_authority.grant(
        request.approval_request_id,
        approved_by_actor_id="actor:operator",
        approval_ref=f"approval-ref:extension-install-disabled:{suffix}",
    )
    lease = AuthorityLease(
        lease_ref=f"authority-lease-ref:extension-install-disabled:{suffix}",
        mode=TrustMode.approved_safe_local_work_session,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        safe_summary="Allow exact disabled extension record storage test.",
    )
    return _StoreTestAuthority(
        receipt=build_extension_install_disabled_record_receipt(
            leases=[lease],
            approval_authority=approval_authority,
            approval_ref=grant.approval_ref,
        ),
        approval_authority=approval_authority,
        lease=lease,
        authority_state=ExtensionInstallDisabledAuthorityState(
            leases=[lease],
            safe_disable_active=False,
        ),
    )


@pytest.mark.parametrize("substitution", ["symlink", "fifo"])
def test_extension_install_disabled_store_rejects_special_file_substitution(
    tmp_path: Path,
    substitution: str,
) -> None:
    authority = _build_store_test_authority("special-file")
    records_dir = tmp_path / "extension_install_disabled_records"
    records_dir.mkdir()
    record_path = records_dir / "uaa-plugin-skill-boundary.disabled-install.json"
    target = tmp_path / "unrelated.json"
    if substitution == "symlink":
        target.write_text("preserve-me", encoding="utf-8")
        record_path.symlink_to(target)
    else:
        os.mkfifo(record_path)

    with pytest.raises(
        ValueError,
        match="EXTENSION_INSTALL_DISABLED_STORAGE_FILE_INVALID",
    ):
        authority.record(ExtensionInstallDisabledRecordStore(tmp_path))
    if substitution == "symlink":
        assert target.read_text(encoding="utf-8") == "preserve-me"


def test_extension_install_disabled_store_recovers_stale_regular_pending_file(
    tmp_path: Path,
) -> None:
    records_dir = tmp_path / "extension_install_disabled_records"
    records_dir.mkdir()
    stale = (
        records_dir / ".uaa-plugin-skill-boundary.disabled-install.json.crashed.pending"
    )
    stale.write_text("prepared", encoding="utf-8")

    authority = _build_store_test_authority("stale-pending")
    persisted = authority.record(ExtensionInstallDisabledRecordStore(tmp_path))

    assert persisted.durable_store_persistence is True
    assert not stale.exists()


def test_extension_install_disabled_store_serializes_identical_concurrent_writes(
    tmp_path: Path,
) -> None:
    authority = _build_store_test_authority("concurrent-identical")

    def record_once(_: int) -> str:
        return (
            authority.record(ExtensionInstallDisabledRecordStore(tmp_path))
            .receipt_ref
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        receipt_refs = list(pool.map(record_once, range(8)))

    assert receipt_refs == [authority.receipt.receipt_ref] * 8
    assert (
        len(list((tmp_path / "extension_install_disabled_records").glob("*.json"))) == 1
    )


def test_store_revalidates_approval_inside_locked_start_boundary(tmp_path: Path) -> None:
    authority = _build_store_test_authority("approval-revoked")
    authority.approval_authority.revoke(
        authority.receipt.approval_ref,
        reason="revoked-before-durable-start",
    )

    with pytest.raises(
        ValueError,
        match="EXTENSION_INSTALL_DISABLED_RECORD_AUTHORITY_REQUIRED",
    ):
        authority.record(ExtensionInstallDisabledRecordStore(tmp_path))
    assert not list(tmp_path.rglob("*.json"))


def test_atomic_start_lock_fences_concurrent_authority_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _build_store_test_authority("atomic-fence")
    at_binding = threading.Event()
    completed = [threading.Event() for _ in range(3)]
    original_binding = install_module._require_live_receipt_binding

    def revoke_approval() -> None:
        at_binding.wait()
        authority.approval_authority.revoke(
            authority.receipt.approval_ref,
            reason="concurrent-revocation",
        )
        completed[0].set()

    def revoke_lease() -> None:
        at_binding.wait()
        authority.authority_state.replace_leases([])
        completed[1].set()

    def engage_safe_disable() -> None:
        at_binding.wait()
        authority.authority_state.engage_safe_disable()
        completed[2].set()

    def binding_with_barrier(*args, **kwargs) -> None:
        original_binding(*args, **kwargs)
        at_binding.set()
        assert not any(event.wait(0.02) for event in completed)

    monkeypatch.setattr(
        install_module,
        "_require_live_receipt_binding",
        binding_with_barrier,
    )
    workers = [
        threading.Thread(target=target)
        for target in (revoke_approval, revoke_lease, engage_safe_disable)
    ]
    for worker in workers:
        worker.start()

    persisted = authority.record(ExtensionInstallDisabledRecordStore(tmp_path))
    for worker in workers:
        worker.join(timeout=1)

    assert persisted.durable_store_persistence is True
    assert all(event.is_set() for event in completed)
    assert list((tmp_path / "extension_install_disabled_records").glob("*.json"))


def test_store_revalidates_lease_inside_locked_start_boundary(tmp_path: Path) -> None:
    authority = _build_store_test_authority("lease-revoked")

    with pytest.raises(
        ValueError,
        match="EXTENSION_INSTALL_DISABLED_RECORD_AUTHORITY_REQUIRED",
    ):
        ExtensionInstallDisabledRecordStore(tmp_path).record_receipt(
            authority.receipt,
            authority_state=ExtensionInstallDisabledAuthorityState(
                leases=[],
                safe_disable_active=False,
            ),
            approval_authority=authority.approval_authority,
        )
    assert not list(tmp_path.rglob("*.json"))


def test_authority_state_owns_immutable_lease_snapshots() -> None:
    authority = _build_store_test_authority("lease-snapshot")
    authority.lease.status = "revoked"
    first_snapshot = authority.authority_state.active_leases_locked()
    assert len(first_snapshot) == 1
    first_snapshot[0].status = "revoked"
    assert len(authority.authority_state.active_leases_locked()) == 1


def test_store_rechecks_kill_switch_inside_locked_start_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _build_store_test_authority("kill-switch")
    monkeypatch.setenv(AUTHORITY_LEASE_KILL_SWITCH_ENV, "engaged")

    with pytest.raises(
        ValueError,
        match="EXTENSION_INSTALL_DISABLED_KILL_SWITCH_ENGAGED",
    ):
        authority.record(ExtensionInstallDisabledRecordStore(tmp_path))
    assert not list(tmp_path.rglob("*.json"))


def test_store_rechecks_safe_disable_inside_locked_start_boundary(tmp_path: Path) -> None:
    authority = _build_store_test_authority("safe-disable")

    with pytest.raises(
        ValueError,
        match="EXTENSION_INSTALL_DISABLED_SAFE_DISABLE_ACTIVE",
    ):
        ExtensionInstallDisabledRecordStore(tmp_path).record_receipt(
            authority.receipt,
            authority_state=ExtensionInstallDisabledAuthorityState(
                leases=[authority.lease],
                safe_disable_active=True,
            ),
            approval_authority=authority.approval_authority,
        )
    assert not list(tmp_path.rglob("*.json"))


@pytest.mark.parametrize(
    "unsafe_ref",
    [
        "approval-ref:workstation.internal",
        "secret:abcd",
        "token:abcd",
        "password:abcd",
    ],
)
def test_install_disabled_contract_rejects_unsafe_refs(unsafe_ref: str) -> None:
    authority = _build_store_test_authority("unsafe-ref")
    with pytest.raises(
        ValueError,
        match=(
            "EXTENSION_INSTALL_DISABLED_(UNSAFE_DURABLE_REF|"
            "SECRET_NAMESPACE_DENIED|REF_NAMESPACE_INVALID)"
        ),
    ):
        ExtensionInstallDisabledRecordReceipt.model_validate(
            authority.receipt.model_dump(mode="json")
            | {"approval_ref": unsafe_ref}
        )


def test_delete_revalidates_approval_inside_locked_start_boundary(tmp_path: Path) -> None:
    record_authority = _build_store_test_authority("delete-revoked-record")
    store = ExtensionInstallDisabledRecordStore(tmp_path)
    record_authority.record(store)
    delete_authority = LocalApprovalAuthority()
    request = delete_authority.create_request(
        build_extension_install_disabled_delete_approval_request()
    )
    grant = delete_authority.grant(
        request.approval_request_id,
        approved_by_actor_id="actor:operator",
        approval_ref="approval-ref:extension-install-disabled-delete:revoked",
    )
    receipt = build_extension_install_disabled_record_delete_receipt(
        leases=[record_authority.lease],
        approval_authority=delete_authority,
        approval_ref=grant.approval_ref,
    )
    delete_authority.revoke(grant.approval_ref, reason="revoked-before-delete-start")

    with pytest.raises(
        ValueError,
        match="EXTENSION_INSTALL_DISABLED_DELETE_AUTHORITY_REQUIRED",
    ):
        store.delete_record(
            receipt,
            authority_state=record_authority.authority_state,
            approval_authority=delete_authority,
        )
    assert list((tmp_path / "extension_install_disabled_records").glob("*.json"))
    assert not list(tmp_path.glob("extension_install_disabled_deletions/*.json"))


@pytest.mark.parametrize(
    "directory_name",
    [
        "extension_install_disabled_records",
        "extension_install_disabled_locks",
    ],
)
def test_extension_install_disabled_store_rejects_symlinked_directories(
    tmp_path: Path,
    directory_name: str,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / directory_name).symlink_to(outside, target_is_directory=True)

    with pytest.raises((ValueError, OSError)):
        authority = _build_store_test_authority(f"symlink-{directory_name}")
        authority.record(ExtensionInstallDisabledRecordStore(tmp_path))
