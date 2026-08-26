from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseScope,
    AuthorityLeaseStatus,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_backend_approval,
)
from ultimate_ai_agent.core.finance.authority import (
    FINANCE_SAFE_DISABLE_REF,
    FinanceAuthorityError,
    FinanceMutationGate,
    FinanceMutationRequest,
    build_exact_finance_lease,
    build_finance_lease_issue_request,
)
from ultimate_ai_agent.core.capabilities.enums import PolicyDecisionStatus
from ultimate_ai_agent.core.finance.crypto import (
    InMemoryFinanceCryptoBackend,
    MacOSFinanceCryptoBackend,
)
from ultimate_ai_agent.core.finance.fixtures import (
    load_finance_fixture,
    load_finance_fixture_manifest,
)
from ultimate_ai_agent.core.finance.models import JournalEntry, stable_finance_ref
from ultimate_ai_agent.core.finance.repository import (
    FINANCE_REPOSITORY_ENCRYPTED_FILE,
    FINANCE_REPOSITORY_METADATA_FILE,
    FINANCE_REPOSITORY_RECEIPTS_FILE,
    FinanceRepository,
    FinanceRepositoryError,
)
from ultimate_ai_agent.core.finance.service import (
    FinanceKernelService,
    finance_repository_ref,
    finance_target_ref,
)


FIXTURE_REF = "fixture-ref:finance/FIN-001:balanced-local-book:v1"


def _request(
    root: Path,
    operation: str,
    *,
    suffix: str,
    expected_revision: int,
    backup_path: Path | None = None,
) -> FinanceMutationRequest:
    return FinanceMutationRequest(
        operation=operation,
        repository_ref=finance_repository_ref(root),
        fixture_ref=FIXTURE_REF if operation == "create" else None,
        target_ref=(
            finance_target_ref(backup_path) if backup_path is not None else None
        ),
        expected_revision=expected_revision,
        request_ref=f"request-ref:finance:test-{suffix}",
        idempotency_ref=f"idempotency-ref:finance:test-{suffix}",
    )


def _authorize(
    service: FinanceKernelService,
    request: FinanceMutationRequest,
    *,
    now: datetime,
):
    preview = service.prepare(request, now=now)
    authority = LocalApprovalAuthority()
    authority.create_request(preview.approval_request)
    authority.grant(
        preview.approval_request.approval_request_id,
        approved_by_actor_id="actor-ref:finance:test-operator",
        approval_ref=preview.expected_approval_ref,
        expires_at=now + timedelta(minutes=10),
    )
    bound = FinanceMutationRequest.model_validate(
        {
            **request.model_dump(mode="python"),
            "approval_ref": preview.expected_approval_ref,
            "exact_scope_ref": preview.exact_scope_ref,
            "action_envelope_ref": preview.action_envelope_ref,
        }
    )
    lease = build_exact_finance_lease(
        preview,
        lease_ref=stable_finance_ref(
            "authority-lease-ref:finance:test",
            {"preview_ref": preview.preview_ref},
        ),
        issued_at=now - timedelta(seconds=1),
        expires_at=now + timedelta(minutes=10),
    )
    return bound, preview, authority, lease


def _execute(
    service: FinanceKernelService,
    request: FinanceMutationRequest,
    *,
    now: datetime,
    backup_path: Path | None = None,
):
    bound, preview, authority, lease = _authorize(service, request, now=now)
    return service.execute(
        bound,
        preview=preview,
        approval_authority=authority,
        lease_provider=lambda: [lease],
        clock=lambda: now,
        backup_path=backup_path,
    )


@pytest.fixture
def kernel(tmp_path: Path):
    root = tmp_path / "protected-book"
    crypto = InMemoryFinanceCryptoBackend()
    service = FinanceKernelService(FinanceRepository(root, crypto_backend=crypto))
    return service, crypto, root


def test_fixture_manifest_is_exact_balanced_and_covers_required_flows() -> None:
    manifest = load_finance_fixture_manifest()
    assert manifest.manifest_ref == (
        "fixture-manifest-ref:finance/FIN-001:sha256:"
        "b4d927f85c4b0edda60860be4387c7b9d3da1a4c23e00b18012708a61264833b"
    )
    fixture = load_finance_fixture(FIXTURE_REF)
    assert {entry.flow for entry in fixture.journal_entries} == {
        "opening_balance",
        "transfer",
        "split",
        "adjustment",
        "reversal",
        "suspense",
    }
    for entry in fixture.journal_entries:
        by_commodity: dict[str, int] = {}
        for posting in entry.postings:
            by_commodity[posting.commodity_ref] = (
                by_commodity.get(posting.commodity_ref, 0) + posting.signed_amount_minor
            )
        assert set(by_commodity.values()) == {0}


def test_unbalanced_and_arbitrary_input_fail_closed() -> None:
    fixture = load_finance_fixture(FIXTURE_REF)
    payload = fixture.journal_entries[0].model_dump(mode="python")
    postings = list(payload["postings"])
    postings[0] = {**postings[0], "amount_minor": postings[0]["amount_minor"] + 1}
    payload["postings"] = postings
    with pytest.raises(ValidationError, match="FINANCE_JOURNAL_ENTRY_UNBALANCED"):
        JournalEntry.model_validate(payload)
    with pytest.raises(ValidationError):
        FinanceMutationRequest.model_validate(
            {
                "operation": "create",
                "repository_ref": "repository-ref:finance:test",
                "fixture_ref": FIXTURE_REF,
                "expected_revision": 0,
                "request_ref": "request-ref:finance:test",
                "idempotency_ref": "idempotency-ref:finance:test",
                "amount_minor": 10,
            }
        )
    with pytest.raises(ValueError, match="FINANCE_FIXTURE_REF_UNKNOWN"):
        load_finance_fixture("fixture-ref:finance/FIN-001:not-allowlisted:v1")


def test_create_encrypts_at_rest_and_returns_only_redacted_reads(kernel) -> None:
    service, _crypto, root = kernel
    now = datetime.now(UTC)
    receipt = _execute(
        service,
        _request(root, "create", suffix="create", expected_revision=0),
        now=now,
    )
    assert receipt.phase == "committed"
    ciphertext = (root / FINANCE_REPOSITORY_ENCRYPTED_FILE).read_bytes()
    assert ciphertext.startswith(b"UAAFIN1\x00")
    assert b"SQLite format 3" not in ciphertext
    assert FIXTURE_REF.encode() not in ciphertext
    metadata = json.loads((root / FINANCE_REPOSITORY_METADATA_FILE).read_text())
    assert metadata["key_material_included"] is False
    assert metadata["keychain_handle_opaque"] is True
    read_model = service.repository.export_redacted(
        request_ref="request-ref:finance:test-read"
    )
    assert read_model["counts"] == {
        "books": 1,
        "legal_entities": 1,
        "accounts": 5,
        "journal_entries": 6,
        "postings": 13,
    }
    assert "account_balances" not in read_model
    assert service.repository.check_integrity(
        request_ref="request-ref:finance:test-check"
    )["balanced"]


def test_create_replays_exact_receipt_and_conflicts_on_reused_key(kernel) -> None:
    service, _crypto, root = kernel
    now = datetime.now(UTC)
    request = _request(root, "create", suffix="replay", expected_revision=0)
    first = _execute(service, request, now=now)
    second = _execute(service, request, now=now)
    assert second.replayed is True
    assert second.receipt_ref == first.receipt_ref
    changed = request.model_copy(
        update={"request_ref": "request-ref:finance:test-replay-changed"}
    )
    with pytest.raises(FinanceRepositoryError, match="FINANCE_IDEMPOTENCY_CONFLICT"):
        _execute(service, changed, now=now)


def test_missing_approval_coarse_lease_and_prepersist_revocation_fail(kernel) -> None:
    service, _crypto, root = kernel
    now = datetime.now(UTC)
    request = _request(root, "create", suffix="authority", expected_revision=0)
    preview = service.prepare(request, now=now)
    lease = build_exact_finance_lease(
        preview,
        lease_ref=stable_finance_ref(
            "authority-lease-ref:finance:test",
            {"preview_ref": preview.preview_ref},
        ),
        issued_at=now - timedelta(seconds=1),
        expires_at=now + timedelta(minutes=10),
    )
    bound = FinanceMutationRequest.model_validate(
        {
            **request.model_dump(mode="python"),
            "approval_ref": preview.expected_approval_ref,
            "exact_scope_ref": preview.exact_scope_ref,
            "action_envelope_ref": preview.action_envelope_ref,
        }
    )
    with pytest.raises(FinanceAuthorityError, match="FINANCE_LOCAL_APPROVAL_DENIED"):
        service.execute(
            bound,
            preview=preview,
            approval_authority=LocalApprovalAuthority(),
            lease_provider=lambda: [lease],
            clock=lambda: now,
        )

    authority = LocalApprovalAuthority()
    authority.create_request(preview.approval_request)
    authority.grant(
        preview.approval_request.approval_request_id,
        approved_by_actor_id="actor-ref:finance:test-operator",
        approval_ref=preview.expected_approval_ref,
        expires_at=now + timedelta(minutes=10),
    )
    coarse = AuthorityLease(
        lease_ref="authority-lease-ref:finance:coarse",
        mode=TrustMode.ask_before_changes,
        scope=AuthorityLeaseScope.session,
        status=AuthorityLeaseStatus.active,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        issued_at=now - timedelta(seconds=1),
        expires_at=now + timedelta(minutes=10),
        safe_disable_ref=FINANCE_SAFE_DISABLE_REF,
        rollback_ref="rollback-ref:finance/FIN-001:reversal-or-restore",
        safe_summary="Coarse workspace write lease that must not authorize Finance.",
    )
    with pytest.raises(
        FinanceAuthorityError, match="FINANCE_EXACT_AUTHORITY_LEASE_DENIED"
    ):
        service.execute(
            bound,
            preview=preview,
            approval_authority=authority,
            lease_provider=lambda: [coarse],
            clock=lambda: now,
        )

    calls = 0

    def revoke_after_first_authorization():
        nonlocal calls
        calls += 1
        if calls == 2:
            authority.revoke(preview.expected_approval_ref, "test revocation")
        return [lease]

    with pytest.raises(FinanceAuthorityError, match="FINANCE_LOCAL_APPROVAL_DENIED"):
        service.execute(
            bound,
            preview=preview,
            approval_authority=authority,
            lease_provider=revoke_after_first_authorization,
            clock=lambda: now,
        )
    assert not root.exists() or not (root / FINANCE_REPOSITORY_ENCRYPTED_FILE).exists()


def test_backup_restore_stale_revision_tamper_key_loss_and_delete(kernel) -> None:
    service, crypto, root = kernel
    now = datetime.now(UTC)
    _execute(
        service,
        _request(root, "create", suffix="lifecycle-create", expected_revision=0),
        now=now,
    )
    backup_path = root.parent / "book-backup.enc"
    backup_metadata, backup_receipt = _execute(
        service,
        _request(
            root,
            "backup",
            suffix="lifecycle-backup",
            expected_revision=1,
            backup_path=backup_path,
        ),
        now=now,
        backup_path=backup_path,
    )
    assert backup_receipt.phase == "committed"
    assert (
        backup_metadata.ciphertext_ref
        != json.loads((root / FINANCE_REPOSITORY_METADATA_FILE).read_text())[
            "ciphertext_ref"
        ]
    )
    with pytest.raises(FinanceRepositoryError, match="FINANCE_STALE_REVISION"):
        _execute(
            service,
            _request(
                root,
                "restore",
                suffix="stale-restore",
                expected_revision=2,
                backup_path=backup_path,
            ),
            now=now,
            backup_path=backup_path,
        )

    tampered = root.parent / "tampered-backup.enc"
    raw = backup_path.read_bytes()
    tampered.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
    tampered.chmod(0o600)
    with pytest.raises(FinanceRepositoryError, match="FINANCE_BACKUP_BINDING_MISMATCH"):
        _execute(
            service,
            _request(
                root,
                "restore",
                suffix="tampered-restore",
                expected_revision=1,
                backup_path=tampered,
            ),
            now=now,
            backup_path=tampered,
        )

    restore = _execute(
        service,
        _request(
            root,
            "restore",
            suffix="lifecycle-restore",
            expected_revision=1,
            backup_path=backup_path,
        ),
        now=now,
        backup_path=backup_path,
    )
    assert restore.phase == "committed"
    assert (
        service.repository.load_snapshot(
            request_ref="request-ref:finance:test-restored"
        ).generation
        == 2
    )

    metadata = json.loads((root / FINANCE_REPOSITORY_METADATA_FILE).read_text())
    crypto.delete_key(
        key_handle_ref=metadata["key_handle_ref"],
        key_version_ref=metadata["key_version_ref"],
        request_ref="request-ref:finance:test-key-loss",
    )
    with pytest.raises(
        FinanceRepositoryError, match="FINANCE_REPOSITORY_KEY_UNAVAILABLE"
    ):
        service.repository.load_snapshot(
            request_ref="request-ref:finance:test-key-loss"
        )


def test_delete_cryptographically_erases_keys_and_ciphertext(kernel) -> None:
    service, crypto, root = kernel
    now = datetime.now(UTC)
    _execute(
        service,
        _request(root, "create", suffix="delete-create", expected_revision=0),
        now=now,
    )
    metadata = json.loads((root / FINANCE_REPOSITORY_METADATA_FILE).read_text())
    receipt = _execute(
        service,
        _request(root, "delete", suffix="delete", expected_revision=1),
        now=now,
    )
    assert receipt.phase == "committed"
    assert not (root / FINANCE_REPOSITORY_ENCRYPTED_FILE).exists()
    tombstone = json.loads((root / FINANCE_REPOSITORY_METADATA_FILE).read_text())
    assert tombstone["deleted"] is True
    for handle_name, version_name in (
        ("key_handle_ref", "key_version_ref"),
        ("backup_key_handle_ref", "backup_key_version_ref"),
    ):
        with pytest.raises(RuntimeError, match="FINANCE_KEY_UNAVAILABLE"):
            crypto.probe_key(
                key_handle_ref=metadata[handle_name],
                key_version_ref=metadata[version_name],
                request_ref="request-ref:finance:test-deleted-probe",
            )


def test_safe_disable_and_kill_switch_deny_before_persistence(kernel) -> None:
    service, _crypto, root = kernel
    now = datetime.now(UTC)
    request = _request(root, "create", suffix="disabled", expected_revision=0)
    bound, preview, authority, lease = _authorize(service, request, now=now)
    with pytest.raises(FinanceAuthorityError, match="FINANCE_SAFE_DISABLE_ENGAGED"):
        service.execute(
            bound,
            preview=preview,
            approval_authority=authority,
            lease_provider=lambda: [lease],
            clock=lambda: now,
            safe_disable_engaged=lambda: True,
        )
    with pytest.raises(
        FinanceAuthorityError, match="FINANCE_EXACT_AUTHORITY_LEASE_DENIED"
    ):
        service.execute(
            bound,
            preview=preview,
            approval_authority=authority,
            lease_provider=lambda: [lease],
            clock=lambda: now,
            kill_switch_engaged=lambda: True,
        )
    assert not root.exists()


def test_policy_approval_and_lease_staleness_fail_closed(kernel) -> None:
    service, _crypto, root = kernel
    now = datetime.now(UTC)
    request = _request(root, "create", suffix="staleness", expected_revision=0)
    with pytest.raises(ValidationError):
        FinanceMutationRequest.model_validate(
            {
                **request.model_dump(mode="python"),
                "policy_revision_ref": "policy-ref:stale",
            }
        )

    bound, preview, authority, lease = _authorize(service, request, now=now)
    service.gate.policy.can_execute = lambda *_args, **_kwargs: SimpleNamespace(
        status=PolicyDecisionStatus.denied,
        allowed=False,
    )
    with pytest.raises(FinanceAuthorityError, match="FINANCE_POLICY_DENIED"):
        service.execute(
            bound,
            preview=preview,
            approval_authority=authority,
            lease_provider=lambda: [lease],
            clock=lambda: now,
        )
    service.gate = FinanceMutationGate()

    expired_authority = LocalApprovalAuthority()
    expired_authority.create_request(preview.approval_request)
    expired_authority.grant(
        preview.approval_request.approval_request_id,
        approved_by_actor_id="actor-ref:finance:test-operator",
        approval_ref=preview.expected_approval_ref,
        expires_at=now + timedelta(seconds=1),
    )
    with pytest.raises(FinanceAuthorityError, match="FINANCE_LOCAL_APPROVAL_DENIED"):
        service.execute(
            bound,
            preview=preview,
            approval_authority=expired_authority,
            lease_provider=lambda: [lease],
            clock=lambda: now + timedelta(seconds=2),
        )

    expired_lease = build_exact_finance_lease(
        preview,
        lease_ref=stable_finance_ref(
            "authority-lease-ref:finance:test-expired",
            {"preview_ref": preview.preview_ref},
        ),
        issued_at=now - timedelta(seconds=1),
        expires_at=now + timedelta(seconds=1),
    )
    with pytest.raises(
        FinanceAuthorityError, match="FINANCE_EXACT_AUTHORITY_LEASE_DENIED"
    ):
        service.execute(
            bound,
            preview=preview,
            approval_authority=authority,
            lease_provider=lambda: [expired_lease],
            clock=lambda: now + timedelta(seconds=2),
        )
    revoked_lease = lease.model_copy(update={"status": AuthorityLeaseStatus.revoked})
    with pytest.raises(
        FinanceAuthorityError, match="FINANCE_EXACT_AUTHORITY_LEASE_DENIED"
    ):
        service.execute(
            bound,
            preview=preview,
            approval_authority=authority,
            lease_provider=lambda: [revoked_lease],
            clock=lambda: now,
        )


def test_ciphertext_tamper_and_symlink_root_fail_closed(kernel, tmp_path: Path) -> None:
    service, _crypto, root = kernel
    now = datetime.now(UTC)
    _execute(
        service,
        _request(root, "create", suffix="tamper-create", expected_revision=0),
        now=now,
    )
    encrypted = root / FINANCE_REPOSITORY_ENCRYPTED_FILE
    raw = encrypted.read_bytes()
    encrypted.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
    with pytest.raises(
        FinanceRepositoryError, match="FINANCE_REPOSITORY_CIPHERTEXT_DRIFT"
    ):
        service.repository.load_snapshot(request_ref="request-ref:finance:test-tamper")

    real = tmp_path / "real-root"
    real.mkdir(mode=0o700)
    linked = tmp_path / "linked-root"
    linked.symlink_to(real, target_is_directory=True)
    linked_service = FinanceKernelService(
        FinanceRepository(linked, crypto_backend=InMemoryFinanceCryptoBackend())
    )
    linked_request = _request(
        linked, "create", suffix="symlink-root", expected_revision=0
    )
    with pytest.raises(
        FinanceRepositoryError, match="FINANCE_REPOSITORY_ROOT_NOT_PRIVATE"
    ):
        _execute(linked_service, linked_request, now=now)


def test_receipts_are_content_free_safe_refs(kernel) -> None:
    service, _crypto, root = kernel
    _execute(
        service,
        _request(root, "create", suffix="receipts", expected_revision=0),
        now=datetime.now(UTC),
    )
    receipt_text = (root / FINANCE_REPOSITORY_RECEIPTS_FILE).read_text()
    assert str(root) not in receipt_text
    assert "amount_minor" not in receipt_text
    assert "SQLite format 3" not in receipt_text
    for line in receipt_text.splitlines():
        payload = json.loads(line)
        assert payload["content_free"] is True
        assert payload["key_material_included"] is False


def test_cli_prepare_is_non_mutating_and_confirmation_is_required(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "cli-repository"
    helper = tmp_path / "missing-helper"
    prepare = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_finance.py",
            "prepare",
            "--repository-dir",
            str(repository),
            "--helper-path",
            str(helper),
            "--helper-sha256",
            "a" * 64,
            "--operation",
            "create",
            "--expected-revision",
            "0",
            "--request-ref",
            "request-ref:finance:test-cli-prepare",
            "--idempotency-ref",
            "idempotency-ref:finance:test-cli-prepare",
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert prepare.returncode == 0
    payload = json.loads(prepare.stdout)
    assert payload["mutation_performed"] is False
    assert payload["operator_confirmation_required"] is True
    assert not repository.exists()

    denied = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_finance.py",
            "run",
            "--repository-dir",
            str(repository),
            "--helper-path",
            str(helper),
            "--helper-sha256",
            "a" * 64,
            "--bundle",
            str(tmp_path / "not-read-without-confirmation.json"),
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert denied.returncode == 2
    assert json.loads(denied.stdout)["error_code"] == (
        "FINANCE_OPERATOR_CONFIRMATION_REQUIRED"
    )


def test_fin001_verifier_passes() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/verify_fin001_synthetic_kernel.py"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout)["status"] == "verified"


def test_macos_crypto_facade_keeps_finance_scope_and_keys_opaque(
    tmp_path: Path,
) -> None:
    class FakeNativeHelper:
        aad = b""

        def readiness(self):
            return "ready", ("reason-ref:test:ready",)

        def create(self, **_kwargs):
            return "helper-receipt-ref:test:create"

        def probe(self, **_kwargs):
            return "helper-receipt-ref:test:probe"

        def delete(self, **_kwargs):
            return "helper-receipt-ref:test:delete"

        def encrypt(self, *, aad: bytes, **_kwargs):
            self.aad = aad
            return b"ciphertext"

        def decrypt(self, *, aad: bytes, **_kwargs):
            self.aad = aad
            return b"plaintext"

    backend = MacOSFinanceCryptoBackend(
        helper_path=tmp_path / "helper",
        expected_helper_sha256="a" * 64,
    )
    fake = FakeNativeHelper()
    backend._delegate = fake
    readiness = backend.readiness()
    assert readiness.status == "ready"
    created = backend.create_key(
        key_handle_ref="key-handle-ref:finance:test",
        key_version_ref="key-version-ref:finance:test:v1",
        request_ref="request-ref:finance:test-key-create",
    )
    assert created.key_material_returned is False
    assert created.key_material_included is False
    assert (
        backend.seal(
            key_handle_ref="key-handle-ref:finance:test",
            key_version_ref="key-version-ref:finance:test:v1",
            context_ref="crypto-context-ref:finance:test",
            request_ref="request-ref:finance:test-seal",
            plaintext=b"synthetic",
        )
        == b"ciphertext"
    )
    assert fake.aad.startswith(b"uaa:finance-protected-repository:aes256gcm:v1\x00")
    assert b"key-handle-ref:finance:test" in fake.aad


def test_backend_approved_store_lease_authorizes_exact_finance_request(kernel) -> None:
    service, _crypto, root = kernel
    now = datetime.now(UTC)
    request = _request(root, "create", suffix="store-lease", expected_revision=0)
    preview = service.prepare(request, now=now)
    approvals = LocalApprovalAuthority()
    approvals.create_request(preview.approval_request)
    approvals.grant(
        preview.approval_request.approval_request_id,
        approved_by_actor_id="actor-ref:finance:test-operator",
        approval_ref=preview.expected_approval_ref,
        expires_at=now + timedelta(minutes=10),
    )
    bound = FinanceMutationRequest.model_validate(
        {
            **request.model_dump(mode="python"),
            "approval_ref": preview.expected_approval_ref,
            "exact_scope_ref": preview.exact_scope_ref,
            "action_envelope_ref": preview.action_envelope_ref,
        }
    )
    store = AuthorityLeaseStore(root.parent / "authority-state")
    _requirement, _grant, lease, receipt = issue_authority_lease_with_backend_approval(
        store,
        build_finance_lease_issue_request(preview),
        idempotency_ref="idempotency-ref:finance:test-store-lease-issue",
        approved_by_actor_id="actor-ref:finance:test-operator",
    )
    assert lease is not None
    assert receipt.status == "issued"
    result = service.execute(
        bound,
        preview=preview,
        approval_authority=approvals,
        lease_provider=lambda: store.list_leases(active_only=True),
        clock=lambda: now,
    )
    assert result.phase == "committed"
