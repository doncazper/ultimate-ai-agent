from __future__ import annotations

import hashlib
import json
import os
import stat
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from scripts.verification import verification_receipt_store as receipt_store_module
from scripts.verification.verification_contracts import (
    VerificationReceipt,
    VerificationRunManifest,
    VerificationTerminalStatus,
    verification_receipt_payload,
    verification_receipt_fingerprint,
    verification_run_manifest_payload,
    verification_run_manifest_fingerprint,
)
from scripts.verification.verification_receipt_store import (
    VerificationArtifactKind,
    VerificationReceiptStore,
    VerificationReceiptStoreError,
)


_DIGEST_A = "a" * 64
_DIGEST_B = "b" * 64
_SHA = "1" * 40
_START = "2026-07-15T00:00:00Z"
_END = "2026-07-15T00:00:01Z"


def _receipt() -> VerificationReceipt:
    initial = VerificationReceipt(
        schema_version="uaa_verification_receipt.v2",
        receipt_ref=f"receipt:verification:{'0' * 64}",
        plan_fingerprint=_DIGEST_A,
        unit_ref="verify-unit:test:receipt-store",
        repository_sha=_SHA,
        dependency_state_fingerprint=_DIGEST_B,
        platform_fingerprint="c" * 64,
        command_manifest_fingerprint="d" * 64,
        verifier_definition_fingerprint="e" * 64,
        test_collection_fingerprint="f" * 64,
        status=VerificationTerminalStatus.PASSED,
        started_at=_START,
        completed_at=_END,
        duration_ms=1_000,
        result_refs=("result-ref:test:receipt-store",),
        output_byte_count=0,
        output_digest="9" * 64,
        execution_surface_ref="surface-ref:local",
        receipt_fingerprint="0" * 64,
    )
    fingerprint = verification_receipt_fingerprint(initial)
    receipt = replace(
        initial,
        receipt_ref=f"receipt:verification:{fingerprint}",
        receipt_fingerprint=fingerprint,
    )
    receipt.validate()
    return receipt


def _run(receipt: VerificationReceipt) -> VerificationRunManifest:
    initial = VerificationRunManifest(
        schema_version="uaa_verification_run.v2",
        run_ref=f"run:verification:{'0' * 64}",
        plan_fingerprint=receipt.plan_fingerprint,
        repository_sha=receipt.repository_sha,
        receipt_refs=(receipt.receipt_ref,),
        started_at=receipt.started_at,
        completed_at=receipt.completed_at,
        status=VerificationTerminalStatus.PASSED,
        run_fingerprint="0" * 64,
        dependency_state_fingerprint=receipt.dependency_state_fingerprint,
        command_manifest_fingerprint=receipt.command_manifest_fingerprint,
        execution_surface_ref=receipt.execution_surface_ref,
        unit_receipt_bindings=((receipt.unit_ref, receipt.receipt_ref),),
    )
    fingerprint = verification_run_manifest_fingerprint(initial)
    run = replace(
        initial,
        run_ref=f"run:verification:{fingerprint}",
        run_fingerprint=fingerprint,
    )
    run.validate()
    return run


def _v3_receipt() -> VerificationReceipt:
    initial = replace(
        _receipt(),
        schema_version="uaa_verification_receipt.v3",
        receipt_ref=f"receipt:verification:{'0' * 64}",
        receipt_fingerprint="0" * 64,
        dependency_lock_set_fingerprint="2" * 64,
        pytest_shard_plan_fingerprint="3" * 64,
        execution_identity_ref=f"execution-identity:{'5' * 64}",
        result_refs=(f"result-ref:verification:{'6' * 64}",),
        observed_platform_fingerprint="7" * 64,
    )
    fingerprint = verification_receipt_fingerprint(initial)
    receipt = replace(
        initial,
        receipt_ref=f"receipt:verification:{fingerprint}",
        receipt_fingerprint=fingerprint,
    )
    receipt.validate()
    return receipt


def _v3_run(receipt: VerificationReceipt) -> VerificationRunManifest:
    initial = replace(
        _run(receipt),
        schema_version="uaa_verification_run.v3",
        run_ref=f"run:verification:{'0' * 64}",
        run_fingerprint="0" * 64,
        dependency_lock_set_fingerprint=receipt.dependency_lock_set_fingerprint,
        platform_fingerprint=receipt.platform_fingerprint,
        verifier_definition_fingerprint=receipt.verifier_definition_fingerprint,
        test_collection_fingerprint=receipt.test_collection_fingerprint,
        pytest_shard_plan_fingerprint=receipt.pytest_shard_plan_fingerprint,
        typescript_project_fingerprint="4" * 64,
        required_unit_refs=(receipt.unit_ref,),
    )
    fingerprint = verification_run_manifest_fingerprint(initial)
    run = replace(
        initial,
        run_ref=f"run:verification:{fingerprint}",
        run_fingerprint=fingerprint,
    )
    run.validate()
    return run


def _canonical_payload(value: object) -> bytes:
    if isinstance(value, VerificationReceipt):
        payload = verification_receipt_payload(value)
    elif isinstance(value, VerificationRunManifest):
        payload = verification_run_manifest_payload(value)
    else:
        raise TypeError
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _artifact_path(
    root: Path, kind: VerificationArtifactKind, digest: str
) -> Path:
    return root / kind.directory_name / f"{digest}.json"


def _install_raw(root: Path, kind: VerificationArtifactKind, encoded: bytes) -> str:
    digest = hashlib.sha256(encoded).hexdigest()
    path = _artifact_path(root, kind, digest)
    path.write_bytes(encoded)
    path.chmod(0o600)
    return digest


def test_store_round_trips_canonical_receipt_and_run_immutably(tmp_path: Path) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    receipt = _receipt()
    run = _run(receipt)

    stored_receipt = store.put_receipt(receipt)
    stored_run = store.put_run_manifest(run)
    repeated_receipt = store.put_receipt(receipt)

    assert stored_receipt.created is True
    assert stored_receipt.artifact_ref == (
        f"verification-artifact:receipt:{stored_receipt.artifact_digest}"
    )
    assert stored_run.created is True
    assert repeated_receipt == replace(stored_receipt, created=False)
    assert store.get_receipt(stored_receipt.artifact_digest) == receipt
    assert store.get_run_manifest(stored_run.artifact_digest) == run
    assert _artifact_path(
        root, VerificationArtifactKind.RECEIPT, stored_receipt.artifact_digest
    ).read_bytes() == _canonical_payload(receipt)
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    assert stat.S_IMODE((root / "receipts").stat().st_mode) == 0o700
    assert stat.S_IMODE(
        _artifact_path(
            root, VerificationArtifactKind.RECEIPT, stored_receipt.artifact_digest
        ).stat().st_mode
    ) == 0o600


def test_legacy_v2_canonical_byte_shape_excludes_v3_fields() -> None:
    receipt = _receipt()
    run = _run(receipt)
    receipt_bytes = _canonical_payload(receipt)
    run_bytes = _canonical_payload(run)

    assert hashlib.sha256(receipt_bytes).hexdigest() == (
        "2b48fada3779cb8944f84d4d65c61275aa0cf619367273b871685ee435b500c4"
    )
    assert hashlib.sha256(run_bytes).hexdigest() == (
        "0981a24d2bbd6d316c30f13b80713c7729db7b459770ad85c5425bae78bf4894"
    )
    receipt_payload = json.loads(receipt_bytes)
    run_payload = json.loads(run_bytes)
    assert not {
        "dependency_lock_set_fingerprint",
        "pytest_shard_plan_fingerprint",
        "execution_identity_ref",
        "executed_command_result_bindings",
        "reused_command_receipt_bindings",
    } & set(receipt_payload)
    assert not {
        "dependency_lock_set_fingerprint",
        "platform_fingerprint",
        "verifier_definition_fingerprint",
        "test_collection_fingerprint",
        "pytest_shard_plan_fingerprint",
        "typescript_project_fingerprint",
        "required_unit_refs",
        "missing_unit_refs",
        "failed_unit_refs",
        "reason_refs",
        "observed_test_collection_bindings",
    } & set(run_payload)


def test_store_round_trips_v3_exact_execution_contracts(tmp_path: Path) -> None:
    store = VerificationReceiptStore(tmp_path / "proof-store")
    receipt = _v3_receipt()
    run = _v3_run(receipt)

    receipt_artifact = store.write_receipt(receipt)
    run_artifact = store.write_run_manifest(run)

    assert store.read_receipt(receipt_artifact.artifact_digest) == receipt
    assert store.read_run_manifest(run_artifact.artifact_digest) == run


def test_concurrent_identical_writers_converge_to_one_artifact(tmp_path: Path) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    second_store = VerificationReceiptStore(root)
    receipt = _receipt()

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = tuple(
            pool.map(
                lambda index: (store, second_store)[index % 2].put_receipt(receipt),
                range(24),
            )
        )

    assert len({result.artifact_digest for result in results}) == 1
    assert sum(result.created for result in results) == 1
    assert store.get_receipt(results[0].artifact_digest) == receipt


@pytest.mark.parametrize("recovery_operation", ["read", "put"])
def test_crash_after_final_link_recovers_only_exact_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    recovery_operation: str,
) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    receipt = _receipt()
    encoded = _canonical_payload(receipt)
    digest = hashlib.sha256(encoded).hexdigest()
    original_unlink = os.unlink

    def interrupt_stage_unlink(path: str, *args: object, **kwargs: object) -> None:
        if path.startswith(f".{digest}.") and path.endswith(".tmp"):
            raise OSError("simulated-crash-after-final-link")
        original_unlink(path, *args, **kwargs)

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "unlink", interrupt_stage_unlink)
        with pytest.raises(VerificationReceiptStoreError, match="publish-failed"):
            store.put_receipt(receipt)

    final_path = _artifact_path(root, VerificationArtifactKind.RECEIPT, digest)
    stage_names = tuple(
        path.name
        for path in (root / "receipts").iterdir()
        if path.name.startswith(f".{digest}.") and path.name.endswith(".tmp")
    )
    assert len(stage_names) == 1
    assert final_path.stat().st_nlink == 2

    reopened = VerificationReceiptStore(root)
    if recovery_operation == "read":
        assert reopened.get_receipt(digest) == receipt
    else:
        recovered = reopened.put_receipt(receipt)
        assert recovered.created is False
        assert recovered.artifact_digest == digest
    assert final_path.stat().st_nlink == 1
    assert not (root / "receipts" / stage_names[0]).exists()


def test_crash_before_final_link_recovers_canonical_orphan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    receipt = _receipt()
    original_unlink = os.unlink

    def interrupt_link(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated-crash-before-final-link")

    def preserve_new_stage(path: str, *args: object, **kwargs: object) -> None:
        if path.startswith(".") and path.endswith(".tmp"):
            raise OSError("simulated-process-exit")
        original_unlink(path, *args, **kwargs)

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "link", interrupt_link)
        scoped.setattr(os, "unlink", preserve_new_stage)
        with pytest.raises(VerificationReceiptStoreError, match="publish-failed"):
            store.put_receipt(receipt)

    receipt_directory = root / "receipts"
    assert len(tuple(receipt_directory.glob(".*.tmp"))) == 1
    recovered = store.put_receipt(receipt)
    assert recovered.created is True
    assert store.get_receipt(recovered.artifact_digest) == receipt
    assert tuple(receipt_directory.glob(".*.tmp")) == ()


@pytest.mark.parametrize("write_posture", ["zero", "partial"])
def test_crash_during_stage_write_recovers_incomplete_orphan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    write_posture: str,
) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    receipt = _receipt()
    original_write = os.write
    original_unlink = os.unlink
    write_calls = 0

    def interrupt_write(
        descriptor: int, data: bytes | bytearray | memoryview
    ) -> int:
        nonlocal write_calls
        write_calls += 1
        if write_posture == "partial" and write_calls == 1:
            view = memoryview(data)
            return original_write(descriptor, view[: max(1, len(view) // 3)])
        raise OSError("simulated-crash-during-stage-write")

    def preserve_stage(path: str, *args: object, **kwargs: object) -> None:
        if path.startswith(".") and path.endswith(".tmp"):
            raise OSError("simulated-process-exit")
        original_unlink(path, *args, **kwargs)

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "write", interrupt_write)
        scoped.setattr(os, "unlink", preserve_stage)
        with pytest.raises(VerificationReceiptStoreError, match="write-failed"):
            store.put_receipt(receipt)

    receipt_directory = root / "receipts"
    stages = tuple(receipt_directory.glob(".*.tmp"))
    assert len(stages) == 1
    if write_posture == "zero":
        assert stages[0].stat().st_size == 0
    else:
        assert 0 < stages[0].stat().st_size < len(_canonical_payload(receipt))

    stored = store.put_receipt(receipt)
    assert stored.created is True
    assert store.get_receipt(stored.artifact_digest) == receipt
    assert tuple(receipt_directory.glob(".*.tmp")) == ()


@pytest.mark.parametrize("attack", ["fifo", "mode", "hardlink"])
def test_incomplete_stage_recovery_rejects_filesystem_violations(
    tmp_path: Path,
    attack: str,
) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    stage = root / "receipts" / f".{'a' * 64}.123.{'b' * 24}.tmp"
    if attack == "fifo":
        os.mkfifo(stage, 0o600)
    else:
        stage.write_bytes(b"")
        stage.chmod(0o600)
        if attack == "mode":
            stage.chmod(0o644)
        else:
            os.link(stage, root / "stage-hardlink")

    with pytest.raises(
        VerificationReceiptStoreError,
        match="stale-stage-unsafe|artifact-unsafe",
    ):
        store.put_receipt(_receipt())
    assert stage.exists()


def test_repeated_prelink_crashes_are_reclaimed_without_growth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    receipt = _receipt()
    receipt_directory = root / "receipts"
    original_unlink = os.unlink

    def interrupt_link(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated-crash-before-final-link")

    for _attempt in range(8):
        preexisting_stages = {
            path.name for path in receipt_directory.glob(".*.tmp")
        }

        def preserve_only_new_stage(
            path: str, *args: object, **kwargs: object
        ) -> None:
            if (
                path.startswith(".")
                and path.endswith(".tmp")
                and path not in preexisting_stages
            ):
                raise OSError("simulated-process-exit")
            original_unlink(path, *args, **kwargs)

        with monkeypatch.context() as scoped:
            scoped.setattr(os, "link", interrupt_link)
            scoped.setattr(os, "unlink", preserve_only_new_stage)
            with pytest.raises(VerificationReceiptStoreError, match="publish-failed"):
                store.put_receipt(receipt)
        assert len(tuple(receipt_directory.glob(".*.tmp"))) == 1

    stored = store.put_receipt(receipt)
    assert stored.created is True
    assert tuple(receipt_directory.glob(".*.tmp")) == ()


def test_every_publish_enforces_bounded_directory_capacity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    receipt_directory = root / "receipts"
    for index in range(2):
        inert = receipt_directory / f"inert-{index}"
        inert.write_bytes(b"bounded")
        inert.chmod(0o600)
    monkeypatch.setattr(receipt_store_module, "MAX_DIRECTORY_ENTRIES", 4)

    with pytest.raises(VerificationReceiptStoreError, match="entry-capacity"):
        store.put_receipt(_receipt())
    assert tuple(receipt_directory.glob(".*.tmp")) == ()


def test_hardlink_with_stage_shaped_wrong_digest_is_not_recovered(
    tmp_path: Path,
) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    stored = store.put_receipt(_receipt())
    final_path = _artifact_path(
        root, VerificationArtifactKind.RECEIPT, stored.artifact_digest
    )
    deceptive_stage = (
        root
        / "receipts"
        / f".{('0' * 64)}.123.{'1' * 24}.tmp"
    )
    os.link(final_path, deceptive_stage)

    with pytest.raises(VerificationReceiptStoreError, match="artifact-unsafe"):
        store.get_receipt(stored.artifact_digest)
    assert deceptive_stage.exists()
    assert final_path.stat().st_nlink == 2


def test_same_digest_stage_hardlink_to_unrelated_file_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    receipt = _receipt()
    stored = store.put_receipt(receipt)
    unrelated = tmp_path / "unrelated"
    unrelated.write_bytes(b"unrelated")
    unrelated.chmod(0o600)
    deceptive_stage = root / "receipts" / (
        f".{stored.artifact_digest}.123.{'c' * 24}.tmp"
    )
    os.link(unrelated, deceptive_stage)

    with pytest.raises(VerificationReceiptStoreError, match="artifact-unsafe"):
        store.put_receipt(receipt)

    assert deceptive_stage.exists()
    assert unrelated.stat().st_nlink == 2


def test_publication_lock_hardlink_substitution_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    stored = store.put_receipt(_receipt())
    lock_path = root / "receipts" / ".publication.lock"
    os.link(lock_path, root / "lock-hardlink")

    with pytest.raises(VerificationReceiptStoreError, match="lock-unsafe"):
        store.get_receipt(stored.artifact_digest)


def test_existing_different_content_at_digest_is_a_conflict(tmp_path: Path) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    receipt = _receipt()
    expected = _canonical_payload(receipt)
    expected_digest = hashlib.sha256(expected).hexdigest()
    target = _artifact_path(root, VerificationArtifactKind.RECEIPT, expected_digest)
    target.write_bytes(b"{}")
    target.chmod(0o600)

    with pytest.raises(
        VerificationReceiptStoreError,
        match="verification-store-artifact-digest-mismatch",
    ):
        store.put_receipt(receipt)


@pytest.mark.parametrize("attack", ["symlink", "fifo", "hardlink", "mode"])
def test_reader_rejects_unsafe_artifact_substitution(
    tmp_path: Path, attack: str
) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    stored = store.put_receipt(_receipt())
    path = _artifact_path(root, VerificationArtifactKind.RECEIPT, stored.artifact_digest)
    if attack == "symlink":
        path.unlink()
        path.symlink_to(root / "missing")
    elif attack == "fifo":
        path.unlink()
        os.mkfifo(path, 0o600)
    elif attack == "hardlink":
        os.link(path, root / "receipt-hardlink")
    else:
        path.chmod(0o644)

    with pytest.raises(VerificationReceiptStoreError, match="artifact-unsafe"):
        store.get_receipt(stored.artifact_digest)


def test_reader_rejects_digest_mismatch_and_noncanonical_json(tmp_path: Path) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    receipt = _receipt()
    stored = store.put_receipt(receipt)
    path = _artifact_path(root, VerificationArtifactKind.RECEIPT, stored.artifact_digest)
    path.write_bytes(b"{}")
    path.chmod(0o600)
    with pytest.raises(VerificationReceiptStoreError, match="digest-mismatch"):
        store.get_receipt(stored.artifact_digest)

    payload = json.dumps(asdict(receipt), indent=2, sort_keys=True).encode()
    digest = _install_raw(root, VerificationArtifactKind.RECEIPT, payload)
    with pytest.raises(VerificationReceiptStoreError, match="json-not-canonical"):
        store.get_receipt(digest)


@pytest.mark.parametrize(
    ("encoded", "reason"),
    [
        (b'{"schema_version":"a","schema_version":"b"}', "duplicate-field"),
        (b'{"duration_ms":NaN}', "nonfinite-number"),
        (b'{"duration_ms":1e9999}', "nonfinite-number"),
    ],
)
def test_reader_rejects_duplicate_keys_and_nonfinite_numbers(
    tmp_path: Path, encoded: bytes, reason: str
) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    digest = _install_raw(root, VerificationArtifactKind.RECEIPT, encoded)
    with pytest.raises(VerificationReceiptStoreError, match=reason):
        store.get_receipt(digest)


def test_reader_rejects_unknown_contract_fields(tmp_path: Path) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    payload = asdict(_receipt())
    payload["raw_output"] = "must-not-enter-proof"
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    digest = _install_raw(root, VerificationArtifactKind.RECEIPT, encoded)

    with pytest.raises(VerificationReceiptStoreError, match="contract-unknown-field"):
        store.get_receipt(digest)


def test_store_rejects_relative_symlink_fifo_and_unsafe_mode_roots(
    tmp_path: Path,
) -> None:
    with pytest.raises(VerificationReceiptStoreError, match="base-invalid"):
        VerificationReceiptStore(Path("relative-proof-store"))

    symlink_root = tmp_path / "symlink-store"
    symlink_root.symlink_to(tmp_path / "target")
    with pytest.raises(VerificationReceiptStoreError, match="base-unsafe"):
        VerificationReceiptStore(symlink_root)

    fifo_root = tmp_path / "fifo-store"
    os.mkfifo(fifo_root, 0o600)
    with pytest.raises(VerificationReceiptStoreError, match="base-unsafe"):
        VerificationReceiptStore(fifo_root)

    unsafe_root = tmp_path / "unsafe-store"
    unsafe_root.mkdir(mode=0o755)
    with pytest.raises(VerificationReceiptStoreError, match="directory-unsafe"):
        VerificationReceiptStore(unsafe_root)


def test_store_creates_every_ancestor_privately_and_rejects_unsafe_intermediate(
    tmp_path: Path,
) -> None:
    nested_root = tmp_path / "first" / "second" / "proof-store"
    VerificationReceiptStore(nested_root)
    assert all(
        stat.S_IMODE(path.stat().st_mode) == 0o700
        for path in (tmp_path / "first", tmp_path / "first" / "second", nested_root)
    )

    unsafe_parent = tmp_path / "unsafe-parent"
    unsafe_parent.mkdir(mode=0o700)
    unsafe_parent.chmod(0o777)
    with pytest.raises(VerificationReceiptStoreError, match="ancestor-unsafe"):
        VerificationReceiptStore(unsafe_parent / "store")

    target = tmp_path / "intermediate-target"
    target.mkdir(mode=0o700)
    intermediate_link = tmp_path / "intermediate-link"
    intermediate_link.symlink_to(target)
    with pytest.raises(VerificationReceiptStoreError, match="base-unsafe"):
        VerificationReceiptStore(intermediate_link / "store")


def test_store_rejects_subdirectory_substitution_and_base_replacement(
    tmp_path: Path,
) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    receipt = _receipt()
    receipts = root / "receipts"
    (receipts / ".publication.lock").unlink()
    receipts.rmdir()
    receipts.symlink_to(root / "runs")
    with pytest.raises(VerificationReceiptStoreError, match="directory-unsafe"):
        store.put_receipt(receipt)

    receipts.unlink()
    receipts.mkdir(mode=0o700)
    moved = tmp_path / "moved-store"
    root.rename(moved)
    root.mkdir(mode=0o700)
    (root / "receipts").mkdir(mode=0o700)
    (root / "runs").mkdir(mode=0o700)
    with pytest.raises(VerificationReceiptStoreError, match="base-substituted"):
        store.put_receipt(receipt)


def test_store_rejects_owner_mode_directory_replacement(tmp_path: Path) -> None:
    root = tmp_path / "proof-store"
    store = VerificationReceiptStore(root)
    receipts = root / "receipts"
    (receipts / ".publication.lock").unlink()
    receipts.rmdir()
    receipts.mkdir(mode=0o700)

    with pytest.raises(VerificationReceiptStoreError, match="directory-substituted"):
        store.put_receipt(_receipt())


def test_public_failures_are_content_free(tmp_path: Path) -> None:
    raw_marker = "raw-provider-output-must-not-escape"
    root = tmp_path / raw_marker
    root.mkdir(mode=0o755)
    with pytest.raises(VerificationReceiptStoreError) as captured:
        VerificationReceiptStore(root)

    assert str(tmp_path) not in str(captured.value)
    assert raw_marker not in str(captured.value)
    assert captured.value.__cause__ is None


def test_invalid_contract_and_digest_fail_before_filesystem_trust(tmp_path: Path) -> None:
    store = VerificationReceiptStore(tmp_path / "proof-store")
    invalid = replace(_receipt(), repository_sha="not-a-sha")
    with pytest.raises(VerificationReceiptStoreError, match="contract-invalid"):
        store.put_receipt(invalid)
    with pytest.raises(VerificationReceiptStoreError, match="digest-invalid"):
        store.get_receipt("../unsafe")
