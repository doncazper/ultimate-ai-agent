from __future__ import annotations

import base64
import os
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ultimate_ai_agent.core.evidence_signing import lifecycle as lifecycle_module
from ultimate_ai_agent.core.evidence_signing.lifecycle import (
    PORTABLE_EVIDENCE_KEY_LEDGER_ENTRY_MAX_BYTES,
    PORTABLE_EVIDENCE_KEY_LEDGER_FILE,
    PortableEvidenceKeyLifecycleConflictError,
    PortableEvidenceKeyLifecycleCorruptionError,
    PortableEvidenceKeyLifecycleLedger,
)
from ultimate_ai_agent.core.evidence_signing.portable import (
    ed25519_public_key_fingerprint_ref,
)


def _public() -> tuple[str, str]:
    raw = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
    encoded = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    return encoded, ed25519_public_key_fingerprint_ref(raw)


def _create(ledger: PortableEvidenceKeyLifecycleLedger):  # type: ignore[no-untyped-def]
    public, fingerprint = _public()
    return ledger.append_created(
        request_ref="request-ref:portable-evidence-key:create:1",
        request_fingerprint_ref="request-fingerprint-ref:portable-evidence-key:create:1",
        receipt_ref="receipt-ref:portable-evidence-key:create:1",
        key_ref="signing-key-ref:portable-evidence:operator",
        key_version_ref="signing-key-version-ref:portable-evidence:operator:1",
        public_key_base64url=public,
        public_key_fingerprint_ref=fingerprint,
    )


def _max_ref(prefix: str, suffix: str = "a") -> str:
    start = f"{prefix}:"
    return start + suffix * (lifecycle_module.PORTABLE_EVIDENCE_KEY_LEDGER_REF_MAX_LENGTH - len(start))


def test_lifecycle_create_rotate_revoke_and_public_projection(tmp_path: Path) -> None:
    ledger = PortableEvidenceKeyLifecycleLedger(tmp_path)
    created = _create(ledger)

    assert ledger.inspect().status == "active"
    assert ledger.active_record().key_version_ref == created.key_version_ref

    public, fingerprint = _public()
    rotated = ledger.append_rotated(
        request_ref="request-ref:portable-evidence-key:rotate:2",
        request_fingerprint_ref="request-fingerprint-ref:portable-evidence-key:rotate:2",
        receipt_ref="receipt-ref:portable-evidence-key:rotate:2",
        key_ref=created.key_ref,
        key_version_ref="signing-key-version-ref:portable-evidence:operator:2",
        public_key_base64url=public,
        public_key_fingerprint_ref=fingerprint,
    )
    bundle = ledger.public_key_bundle(
        issuer_ref="issuer-ref:portable-evidence:local-operator"
    )

    assert rotated.generation == 2
    assert [record.status for record in bundle.records] == ["retired", "active"]
    assert bundle.records[1].predecessor_key_version_ref == created.key_version_ref
    ledger.append_retired_key_delete_completed(
        request_ref="request-ref:portable-evidence-key:rotate-delete:1",
        request_fingerprint_ref=(
            "request-fingerprint-ref:portable-evidence-key:rotate-delete:1"
        ),
        receipt_ref="receipt-ref:portable-evidence-key:rotate-delete:1",
        retired_key_version_ref=created.key_version_ref,
    )

    revoked = ledger.append_revoked(
        request_ref="request-ref:portable-evidence-key:revoke:2",
        request_fingerprint_ref="request-fingerprint-ref:portable-evidence-key:revoke:2",
        receipt_ref="receipt-ref:portable-evidence-key:revoke:2",
        revocation_ref="revocation-ref:portable-evidence-key:operator:2",
    )

    assert revoked.previous_entry_hash_ref != rotated.entry_hash_ref
    assert ledger.inspect().status == "revoked_deletion_pending"
    ledger.append_revocation_delete_completed(
        request_ref="request-ref:portable-evidence-key:revoke-delete:2",
        request_fingerprint_ref=(
            "request-fingerprint-ref:portable-evidence-key:revoke-delete:2"
        ),
        receipt_ref="receipt-ref:portable-evidence-key:revoke-delete:2",
        revocation_ref="revocation-ref:portable-evidence-key:operator:2",
    )
    assert ledger.inspect().status == "revoked"
    assert (
        ledger.public_key_bundle(
            issuer_ref="issuer-ref:portable-evidence:local-operator"
        )
        .records[-1]
        .status
        == "revoked"
    )
    with pytest.raises(
        PortableEvidenceKeyLifecycleConflictError,
        match="PORTABLE_EVIDENCE_ACTIVE_KEY_REQUIRED",
    ):
        ledger.active_record()


def test_lifecycle_request_idempotency_and_conflict(tmp_path: Path) -> None:
    ledger = PortableEvidenceKeyLifecycleLedger(tmp_path)
    created = _create(ledger)
    public, fingerprint = _public()

    repeated = ledger.append_created(
        request_ref=created.request_ref,
        request_fingerprint_ref=created.request_fingerprint_ref,
        receipt_ref="receipt-ref:ignored-on-idempotent-replay",
        key_ref=created.key_ref,
        key_version_ref=created.key_version_ref,
        public_key_base64url=public,
        public_key_fingerprint_ref=fingerprint,
    )

    assert repeated == created
    assert len(ledger.load_entries()) == 1
    with pytest.raises(
        PortableEvidenceKeyLifecycleConflictError,
        match="PORTABLE_EVIDENCE_KEY_REQUEST_CONFLICT",
    ):
        ledger.append_created(
            request_ref=created.request_ref,
            request_fingerprint_ref="request-fingerprint-ref:changed",
            receipt_ref="receipt-ref:portable-evidence-key:create:changed",
            key_ref=created.key_ref,
            key_version_ref=created.key_version_ref,
            public_key_base64url=public,
            public_key_fingerprint_ref=fingerprint,
        )


def test_lifecycle_tamper_and_unsafe_file_substitution_fail_closed(
    tmp_path: Path,
) -> None:
    ledger = PortableEvidenceKeyLifecycleLedger(tmp_path)
    _create(ledger)
    path = tmp_path / PORTABLE_EVIDENCE_KEY_LEDGER_FILE
    raw = path.read_text(encoding="utf-8")
    path.write_text(raw.replace('"sequence":1', '"sequence":2'), encoding="utf-8")

    with pytest.raises(PortableEvidenceKeyLifecycleCorruptionError):
        ledger.load_entries()

    path.unlink()
    target = tmp_path / "other.jsonl"
    target.write_text("", encoding="utf-8")
    os.chmod(target, 0o600)
    path.symlink_to(target)
    with pytest.raises(OSError):
        ledger.load_entries()


def test_unterminated_record_rejects_load_and_append_without_mutation(
    tmp_path: Path,
) -> None:
    ledger = PortableEvidenceKeyLifecycleLedger(tmp_path)
    _create(ledger)
    path = tmp_path / PORTABLE_EVIDENCE_KEY_LEDGER_FILE
    truncated = path.read_bytes()[:-1]
    path.write_bytes(truncated)

    with pytest.raises(
        PortableEvidenceKeyLifecycleCorruptionError,
        match="PORTABLE_EVIDENCE_KEY_LEDGER_UNTERMINATED_RECORD",
    ):
        ledger.load_entries()
    with pytest.raises(
        PortableEvidenceKeyLifecycleCorruptionError,
        match="PORTABLE_EVIDENCE_KEY_LEDGER_UNTERMINATED_RECORD",
    ):
        ledger.append_marked_lost(
            request_ref="request-ref:portable-evidence-key:lost:truncated",
            request_fingerprint_ref=(
                "request-fingerprint-ref:portable-evidence-key:lost:truncated"
            ),
            receipt_ref="receipt-ref:portable-evidence-key:lost:truncated",
        )
    assert path.read_bytes() == truncated


def test_terminal_transition_preserves_final_settlement_entry_slot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger = PortableEvidenceKeyLifecycleLedger(tmp_path)
    _create(ledger)
    monkeypatch.setattr(lifecycle_module, "PORTABLE_EVIDENCE_KEY_LEDGER_MAX_ENTRIES", 2)

    with pytest.raises(
        PortableEvidenceKeyLifecycleConflictError,
        match="PORTABLE_EVIDENCE_KEY_LEDGER_FULL",
    ):
        ledger.append_marked_lost(
            request_ref="request-ref:portable-evidence-key:lost:no-settlement-slot",
            request_fingerprint_ref=(
                "request-fingerprint-ref:portable-evidence-key:lost:no-settlement-slot"
            ),
            receipt_ref="receipt-ref:portable-evidence-key:lost:no-settlement-slot",
        )
    assert ledger.inspect().status == "active"


def test_settled_rotation_preserves_emergency_terminal_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger = PortableEvidenceKeyLifecycleLedger(tmp_path)
    monkeypatch.setattr(lifecycle_module, "PORTABLE_EVIDENCE_KEY_LEDGER_MAX_ENTRIES", 5)
    created = _create(ledger)
    public, fingerprint = _public()
    rotated = ledger.append_rotated(
        request_ref="request-ref:portable-evidence-key:rotate:reserve",
        request_fingerprint_ref=(
            "request-fingerprint-ref:portable-evidence-key:rotate:reserve"
        ),
        receipt_ref="receipt-ref:portable-evidence-key:rotate:reserve",
        key_ref=created.key_ref,
        key_version_ref="signing-key-version-ref:portable-evidence:reserve:2",
        public_key_base64url=public,
        public_key_fingerprint_ref=fingerprint,
    )
    ledger.append_retired_key_delete_completed(
        request_ref="request-ref:portable-evidence-key:rotate-delete:reserve",
        request_fingerprint_ref=(
            "request-fingerprint-ref:portable-evidence-key:rotate-delete:reserve"
        ),
        receipt_ref="receipt-ref:portable-evidence-key:rotate-delete:reserve",
        retired_key_version_ref=created.key_version_ref,
    )

    with pytest.raises(
        PortableEvidenceKeyLifecycleConflictError,
        match="PORTABLE_EVIDENCE_KEY_LEDGER_FULL",
    ):
        ledger.append_rotated(
            request_ref="request-ref:portable-evidence-key:rotate:no-emergency-pair",
            request_fingerprint_ref=(
                "request-fingerprint-ref:portable-evidence-key:rotate:no-emergency-pair"
            ),
            receipt_ref="receipt-ref:portable-evidence-key:rotate:no-emergency-pair",
            key_ref=rotated.key_ref,
            key_version_ref="signing-key-version-ref:portable-evidence:reserve:3",
            public_key_base64url=public,
            public_key_fingerprint_ref=fingerprint,
        )

    ledger.append_marked_lost(
        request_ref="request-ref:portable-evidence-key:lost:reserve",
        request_fingerprint_ref=(
            "request-fingerprint-ref:portable-evidence-key:lost:reserve"
        ),
        receipt_ref="receipt-ref:portable-evidence-key:lost:reserve",
    )
    ledger.append_lost_key_delete_completed(
        request_ref="request-ref:portable-evidence-key:lost-delete:reserve",
        request_fingerprint_ref=(
            "request-fingerprint-ref:portable-evidence-key:lost-delete:reserve"
        ),
        receipt_ref="receipt-ref:portable-evidence-key:lost-delete:reserve",
    )
    assert ledger.inspect().status == "lost"


def test_maximum_bounded_refs_fit_one_reserved_ledger_entry(
    tmp_path: Path,
) -> None:
    ledger = PortableEvidenceKeyLifecycleLedger(tmp_path)
    public, fingerprint = _public()
    created = ledger.append_created(
        request_ref=_max_ref("request-ref", "a"),
        request_fingerprint_ref=_max_ref("request-fingerprint-ref", "b"),
        receipt_ref=_max_ref("receipt-ref", "c"),
        key_ref=_max_ref("signing-key-ref", "d"),
        key_version_ref=_max_ref("signing-key-version-ref", "e"),
        public_key_base64url=public,
        public_key_fingerprint_ref=fingerprint,
    )
    rotated_public, rotated_fingerprint = _public()
    ledger.append_rotated(
        request_ref=_max_ref("request-ref", "f"),
        request_fingerprint_ref=_max_ref("request-fingerprint-ref", "g"),
        receipt_ref=_max_ref("receipt-ref", "h"),
        key_ref=created.key_ref,
        key_version_ref=_max_ref("signing-key-version-ref", "i"),
        public_key_base64url=rotated_public,
        public_key_fingerprint_ref=rotated_fingerprint,
    )

    for line in (tmp_path / PORTABLE_EVIDENCE_KEY_LEDGER_FILE).read_bytes().splitlines(
        keepends=True
    ):
        assert len(line) <= PORTABLE_EVIDENCE_KEY_LEDGER_ENTRY_MAX_BYTES


def test_lifecycle_mark_lost_is_terminal_for_current_signing(tmp_path: Path) -> None:
    ledger = PortableEvidenceKeyLifecycleLedger(tmp_path)
    _create(ledger)
    ledger.append_marked_lost(
        request_ref="request-ref:portable-evidence-key:lost:1",
        request_fingerprint_ref="request-fingerprint-ref:portable-evidence-key:lost:1",
        receipt_ref="receipt-ref:portable-evidence-key:lost:1",
    )

    assert ledger.inspect().status == "lost_deletion_pending"
    ledger.append_lost_key_delete_completed(
        request_ref="request-ref:portable-evidence-key:lost-delete:1",
        request_fingerprint_ref=(
            "request-fingerprint-ref:portable-evidence-key:lost-delete:1"
        ),
        receipt_ref="receipt-ref:portable-evidence-key:lost-delete:1",
    )
    assert ledger.inspect().status == "lost"
    with pytest.raises(PortableEvidenceKeyLifecycleConflictError):
        ledger.active_record()


def test_rotation_rejects_duplicate_version_and_fingerprint_without_mutation(
    tmp_path: Path,
) -> None:
    ledger = PortableEvidenceKeyLifecycleLedger(tmp_path)
    created = _create(ledger)
    before = ledger.load_entries()
    replacement_public, replacement_fingerprint = _public()

    with pytest.raises(
        PortableEvidenceKeyLifecycleCorruptionError,
        match="PORTABLE_EVIDENCE_KEY_LEDGER_VERSION_DUPLICATE",
    ):
        ledger.append_rotated(
            request_ref="request-ref:portable-evidence-key:rotate:duplicate-version",
            request_fingerprint_ref=(
                "request-fingerprint-ref:portable-evidence-key:rotate:duplicate-version"
            ),
            receipt_ref="receipt-ref:portable-evidence-key:rotate:duplicate-version",
            key_ref=created.key_ref,
            key_version_ref=created.key_version_ref,
            public_key_base64url=replacement_public,
            public_key_fingerprint_ref=replacement_fingerprint,
        )
    assert ledger.load_entries() == before

    with pytest.raises(
        PortableEvidenceKeyLifecycleCorruptionError,
        match="PORTABLE_EVIDENCE_KEY_LEDGER_FINGERPRINT_DUPLICATE",
    ):
        ledger.append_rotated(
            request_ref="request-ref:portable-evidence-key:rotate:duplicate-fingerprint",
            request_fingerprint_ref=(
                "request-fingerprint-ref:portable-evidence-key:rotate:duplicate-fingerprint"
            ),
            receipt_ref="receipt-ref:portable-evidence-key:rotate:duplicate-fingerprint",
            key_ref=created.key_ref,
            key_version_ref="signing-key-version-ref:portable-evidence:operator:2",
            public_key_base64url=created.public_key_base64url,
            public_key_fingerprint_ref=created.public_key_fingerprint_ref,
        )
    assert ledger.load_entries() == before


def test_unsettled_rotation_blocks_other_lifecycle_transitions(tmp_path: Path) -> None:
    ledger = PortableEvidenceKeyLifecycleLedger(tmp_path)
    created = _create(ledger)
    public, fingerprint = _public()
    ledger.append_rotated(
        request_ref="request-ref:portable-evidence-key:rotate:pending",
        request_fingerprint_ref=(
            "request-fingerprint-ref:portable-evidence-key:rotate:pending"
        ),
        receipt_ref="receipt-ref:portable-evidence-key:rotate:pending",
        key_ref=created.key_ref,
        key_version_ref="signing-key-version-ref:portable-evidence:operator:2",
        public_key_base64url=public,
        public_key_fingerprint_ref=fingerprint,
    )

    assert ledger.inspect().status == "active_rotation_delete_pending"
    with pytest.raises(
        PortableEvidenceKeyLifecycleConflictError,
        match="PORTABLE_EVIDENCE_KEY_LIFECYCLE_NOT_SETTLED",
    ):
        ledger.append_marked_lost(
            request_ref="request-ref:portable-evidence-key:lost:pending",
            request_fingerprint_ref=(
                "request-fingerprint-ref:portable-evidence-key:lost:pending"
            ),
            receipt_ref="receipt-ref:portable-evidence-key:lost:pending",
        )
