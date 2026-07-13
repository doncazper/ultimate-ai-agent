from __future__ import annotations

from pathlib import Path

import pytest

from tests.test_portable_evidence_signing_dispatcher import (
    _FakeManagedBackend,
    _adapter_setup,
    _approved_dispatch,
    _create_active_key,
)
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.evidence_signing import lifecycle as lifecycle_module
from ultimate_ai_agent.core.evidence_signing.artifact_store import (
    PortableEvidenceSignedArtifactStore,
)
from ultimate_ai_agent.core.evidence_signing.backend import (
    PortableEvidenceSigningBackendDeletion,
)
from ultimate_ai_agent.core.evidence_signing.dispatcher_adapter import (
    PortableEvidenceSigningAuthorityAdapter,
    PortableEvidenceSigningOperation,
)
from ultimate_ai_agent.core.evidence_signing.lifecycle import (
    PortableEvidenceKeyLifecycleLedger,
)


@pytest.mark.parametrize("capacity_kind", ["entries", "bytes"])
def test_terminal_capacity_denial_precedes_backend_deletion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capacity_kind: str,
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
        suffix=f"{capacity_kind}-capacity-denied",
    )
    if capacity_kind == "entries":
        monkeypatch.setattr(
            lifecycle_module,
            "PORTABLE_EVIDENCE_KEY_LEDGER_MAX_ENTRIES",
            2,
        )
    else:
        current_size = lifecycle.path.stat().st_size
        monkeypatch.setattr(
            lifecycle_module,
            "PORTABLE_EVIDENCE_KEY_LEDGER_MAX_BYTES",
            current_size
            + 2 * lifecycle_module.PORTABLE_EVIDENCE_KEY_LEDGER_ENTRY_MAX_BYTES
            - 1,
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
    result, _request_value = _approved_dispatch(
        state_dir=state_dir,
        store=store,
        adapter=adapter,
        resources=resources,
        metadata={
            "operation": "key_mark_lost",
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
        },
        suffix=f"{capacity_kind}-capacity-denied",
    )

    assert result.receipt.status == "cancelled_before_start"
    assert "reason-ref:portable-evidence-signing:ledger-capacity-exhausted" in (
        result.receipt.reason_refs
    )
    assert backend.delete_count == 0
    assert key_version_ref in backend.keys
    assert lifecycle.inspect().status == "active"


def test_oversized_lifecycle_ref_is_denied_before_backend_mutation(
    tmp_path: Path,
) -> None:
    state_dir, store, lifecycle, backend, adapter = _adapter_setup(
        tmp_path,
        PortableEvidenceSigningOperation.key_create,
    )
    del lifecycle
    key_ref = "signing-key-ref:portable-evidence:" + "x" * 600
    key_version_ref = "signing-key-version-ref:portable-evidence:bounded:1"
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
        suffix="oversized-lifecycle-ref",
    )

    assert result.receipt.status == "denied"
    assert result.receipt.execution_started is False
    assert "reason-ref:portable-evidence-signing:lifecycle-ref-too-long" in (
        result.receipt.reason_refs
    )
    assert backend.create_count == 0


def test_deletion_helper_receipt_is_evidence_not_lifecycle_settlement_binding(
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
        suffix="long-helper-receipt",
    )
    original_delete = backend.delete_key
    helper_receipt_ref = "helper-receipt-ref:test:" + "h" * 600

    def long_receipt_delete(**kwargs):  # type: ignore[no-untyped-def]
        deleted = original_delete(**kwargs)
        return PortableEvidenceSigningBackendDeletion.model_validate(
            deleted.model_dump(mode="python")
            | {"helper_receipt_ref": helper_receipt_ref}
        )

    backend.delete_key = long_receipt_delete  # type: ignore[method-assign]
    adapter = PortableEvidenceSigningAuthorityAdapter(
        operation=PortableEvidenceSigningOperation.key_mark_lost,
        backend=backend,
        lifecycle=lifecycle,
        lease_store=store,
        safe_disable_engaged=lambda: False,
        artifact_store=PortableEvidenceSignedArtifactStore(state_dir / "signing"),
    )
    resources = adapter.binding_resource_refs | {key_ref, key_version_ref}
    result, _request_value = _approved_dispatch(
        state_dir=state_dir,
        store=store,
        adapter=adapter,
        resources=resources,
        metadata={
            "operation": "key_mark_lost",
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
        },
        suffix="long-helper-receipt",
    )

    assert result.receipt.status == "succeeded"
    assert result.adapter_result is not None
    entries = lifecycle.load_entries()
    assert entries[-1].receipt_ref == result.adapter_result.safe_output["receipt_ref"]
    assert entries[-1].receipt_ref != helper_receipt_ref
    assert helper_receipt_ref in result.adapter_result.evidence_refs
