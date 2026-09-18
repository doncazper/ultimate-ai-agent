"""Create/import recovery retains exact authority at the shared write boundary."""

from datetime import UTC, datetime, timedelta
import json

import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.finance.authority import (
    FinanceAuthorityError,
    FinanceMutationRequest,
    build_exact_finance_lease,
)
from ultimate_ai_agent.core.finance.crypto import InMemoryFinanceCryptoBackend
from ultimate_ai_agent.core.finance.import_commit import FIN002_IMPORT_SAFE_DISABLE_REF
from ultimate_ai_agent.core.finance.import_preview import preview_synthetic_csv_fixture
from ultimate_ai_agent.core.finance.models import stable_finance_ref
from ultimate_ai_agent.core.finance.repository import (
    FinanceMutationReceipt,
    FinanceRepository,
)
from ultimate_ai_agent.core.finance.service import (
    FinanceKernelService,
    finance_repository_ref,
    finance_target_ref,
)


def authorize(service, request, now):
    preview = service.prepare(request, now=now)
    approvals = LocalApprovalAuthority()
    approvals.create_request(preview.approval_request)
    approvals.grant(
        preview.approval_request.approval_request_id,
        approved_by_actor_id="actor-ref:finance:recovery-test",
        approval_ref=preview.expected_approval_ref,
        expires_at=preview.expires_at,
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
            "authority-lease-ref:finance:recovery-test",
            {"preview_ref": preview.preview_ref},
        ),
        issued_at=now - timedelta(seconds=1),
        expires_at=preview.expires_at,
    )
    return bound, preview, approvals, lease


def execute(service, request, now, **kwargs):
    bound, preview, approvals, lease = authorize(service, request, now)
    return service.execute(
        bound,
        preview=preview,
        approval_authority=approvals,
        lease_provider=lambda: [lease],
        clock=lambda: now,
        **kwargs,
    )


@pytest.fixture(params=["create", "import_commit"])
def operation(request, tmp_path):
    crypto = InMemoryFinanceCryptoBackend()
    service = FinanceKernelService(
        FinanceRepository(tmp_path / "book", crypto_backend=crypto)
    )
    now = datetime.now(UTC)
    common = {"repository_ref": finance_repository_ref(service.repository.root)}
    create = FinanceMutationRequest(
        **common,
        operation="create",
        expected_revision=0,
        fixture_ref="fixture-ref:finance/FIN-001:balanced-local-book:v1",
        request_ref="request-ref:finance:recovery-create",
        idempotency_ref="idempotency-ref:finance:recovery-create",
    )
    if request.param == "create":
        return service, create, now
    execute(service, create, now)
    preview = preview_synthetic_csv_fixture(
        "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1"
    )
    imported = FinanceMutationRequest(
        **common,
        operation="import_commit",
        expected_revision=1,
        request_ref="request-ref:finance:recovery-import",
        idempotency_ref="idempotency-ref:finance:recovery-import",
        fixture_ref=preview.fixture_ref,
        import_preview_ref=preview.preview_ref,
        import_profile_ref=preview.profile_ref,
        import_fixture_manifest_ref=preview.import_fixture_manifest_ref,
        import_candidate_refs=tuple(item.candidate_ref for item in preview.candidates),
        import_source_fingerprint_refs=tuple(
            item.source_fingerprint_ref for item in preview.observations
        ),
        safe_disable_ref=FIN002_IMPORT_SAFE_DISABLE_REF,
    )
    return service, imported, now


def files(repository):
    return {
        path.name: path.read_bytes()
        for path in repository.root.iterdir()
        if path.is_file()
    }


def interrupt(operation, monkeypatch, boundary="pending"):
    service, request, now = operation
    repo = service.repository
    write = repo._atomic_write

    def interrupted(path, payload):
        write(path, payload)
        target = {
            "pending": repo.pending_commit_path,
            "ciphertext": repo.encrypted_path,
            "metadata": repo.metadata_path,
            "committed": repo.receipts_path,
        }[boundary]
        if path == target and (
            boundary != "committed"
            or json.loads(payload.splitlines()[-1])["phase"] == "committed"
        ):
            raise OSError("FINANCE_TEST_INTERRUPTED")

    with monkeypatch.context() as patch:
        patch.setattr(repo, "_atomic_write", interrupted)
        # _atomic_write_json is a classmethod, so cover metadata writes too.
        patch.setattr(FinanceRepository, "_atomic_write", staticmethod(interrupted))
        with pytest.raises(OSError, match="FINANCE_TEST_INTERRUPTED"):
            execute(service, request, now)
    assert repo.pending_commit_path.exists()


@pytest.mark.parametrize("boundary", ["pending", "ciphertext", "metadata", "committed"])
def test_fresh_exact_recovery_authenticates_each_partial_generation(
    operation, monkeypatch, boundary
):
    interrupt(operation, monkeypatch, boundary)
    service, request, now = operation
    repo = service.repository
    original = repo._read_pending_generation()[1]
    before = files(repo)
    with pytest.raises(RuntimeError, match="PENDING_MUTATION_AUTHORITY_REQUIRED"):
        repo.load_snapshot(request_ref="request-ref:finance:unapproved-recovery")
    with pytest.raises(RuntimeError, match="PENDING_COMMIT_REQUIRES_MUTATING_RECOVERY"):
        repo.load_snapshot_read_only(request_ref="request-ref:finance:read-only")
    assert files(repo) == before
    reopened = FinanceKernelService(
        FinanceRepository(repo.root, crypto_backend=repo.crypto)
    )
    result = execute(reopened, request, now + timedelta(seconds=1))
    receipt = result[1] if isinstance(result, tuple) else result
    assert receipt.replayed is True
    assert receipt.receipt_ref == original.receipt_ref
    assert (
        reopened.repository.load_snapshot_read_only(
            request_ref="request-ref:finance:resolved"
        ).revision
        == request.expected_revision + 1
    )
    assert not repo.pending_commit_path.exists()
    receipts = [
        FinanceMutationReceipt.model_validate_json(line)
        for line in repo.receipts_path.read_bytes().splitlines()
    ]
    recovered = [item for item in receipts if item.phase == "recovered"]
    assert len(recovered) == 1
    assert original.receipt_ref in recovered[0].proof_refs
    assert recovered[0].permit_ref != original.permit_ref
    before_lookup = files(repo)
    assert (
        repo.inspect_committed_receipt_read_only(
            **historical_binding(service, request, now)
        )
        == original
    )
    assert files(repo) == before_lookup


@pytest.mark.parametrize("revoked", ["approval", "lease", "safe_disable", "expiry"])
def test_current_authority_is_rechecked_after_authenticated_inspection(
    operation, monkeypatch, revoked
):
    interrupt(operation, monkeypatch)
    service, request, now = operation
    repo = service.repository
    bound, preview, approvals, lease = authorize(
        service, request, now + timedelta(seconds=1)
    )
    checked = False
    inspect = repo._validate_pending_mutation

    def inspected(**kwargs):
        nonlocal checked
        inspect(**kwargs)
        checked = True
        if revoked == "approval":
            approvals.revoke(
                preview.expected_approval_ref, "Synthetic recovery revocation."
            )

    monkeypatch.setattr(repo, "_validate_pending_mutation", inspected)
    before = files(repo)
    with pytest.raises(FinanceAuthorityError):
        service.execute(
            bound,
            preview=preview,
            approval_authority=approvals,
            lease_provider=lambda: [] if checked and revoked == "lease" else [lease],
            safe_disable_engaged=lambda: checked and revoked == "safe_disable",
            clock=lambda: (
                now + timedelta(hours=1)
                if checked and revoked == "expiry"
                else now + timedelta(seconds=1)
            ),
        )
    assert checked
    assert files(repo) == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("request_ref", "request-ref:finance:substituted"),
        ("idempotency_ref", "idempotency-ref:finance:substituted"),
    ],
)
def test_current_authority_cannot_relabel_another_pending_request(
    operation, monkeypatch, field, value
):
    interrupt(operation, monkeypatch)
    service, request, now = operation
    changed = FinanceMutationRequest.model_validate(
        {**request.model_dump(mode="python"), field: value}
    )
    before = files(service.repository)
    with pytest.raises(RuntimeError, match="PENDING_MUTATION_BINDING_INVALID"):
        execute(service, changed, now)
    assert files(service.repository) == before


def test_rehashed_header_and_prepared_receipt_cannot_substitute_encrypted_identity(
    operation, monkeypatch
):
    interrupt(operation, monkeypatch)
    service, request, now = operation
    repo = service.repository
    header, ciphertext = repo.pending_commit_path.read_bytes().split(b"\n", 1)
    data = json.loads(header)
    changed = FinanceMutationRequest.model_validate(
        {
            **request.model_dump(mode="python"),
            "request_ref": "request-ref:finance:forged-header",
        }
    )
    fingerprint = service.prepare(changed, now=now).payload_fingerprint_ref

    def rewrite(receipt):
        if receipt["request_ref"] != request.request_ref:
            return receipt
        receipt.update(
            request_ref=changed.request_ref, payload_fingerprint_ref=fingerprint
        )
        receipt["receipt_ref"] = stable_finance_ref(
            "finance-mutation-receipt-ref",
            {
                key: value
                for key, value in receipt.items()
                if key not in {"receipt_ref", "replayed"}
            },
        )
        return FinanceMutationReceipt.model_validate(receipt).model_dump(mode="json")

    data["receipt"] = rewrite(data["receipt"])
    repo._atomic_write(
        repo.pending_commit_path, json.dumps(data).encode() + b"\n" + ciphertext
    )
    rewritten = [
        rewrite(json.loads(line))
        for line in repo.receipts_path.read_bytes().splitlines()
    ]
    repo._atomic_write(
        repo.receipts_path,
        b"".join(json.dumps(item).encode() + b"\n" for item in rewritten),
    )
    before = files(repo)
    with pytest.raises(RuntimeError, match="PENDING_COMMIT_BINDING_MISMATCH"):
        execute(service, changed, now)
    assert files(repo) == before


def test_header_cannot_relabel_pending_action_as_legacy_restore(operation, monkeypatch):
    interrupt(operation, monkeypatch)
    service, _request, _now = operation
    repo = service.repository
    header, ciphertext = repo.pending_commit_path.read_bytes().split(b"\n", 1)
    data = json.loads(header)
    receipt = data["receipt"]
    receipt["operation"] = "restore"
    receipt["receipt_ref"] = stable_finance_ref(
        "finance-mutation-receipt-ref",
        {
            key: value
            for key, value in receipt.items()
            if key not in {"receipt_ref", "replayed"}
        },
    )
    data["receipt"] = FinanceMutationReceipt.model_validate(receipt).model_dump(
        mode="json"
    )
    repo._atomic_write(
        repo.pending_commit_path, json.dumps(data).encode() + b"\n" + ciphertext
    )
    before = files(repo)
    with pytest.raises(RuntimeError, match="PENDING_COMMIT_BINDING_MISMATCH"):
        repo.load_snapshot(request_ref="request-ref:finance:legacy-read")
    assert files(repo) == before


def historical_binding(service, request, now):
    return {
        "operation": request.operation,
        "repository_ref": request.repository_ref,
        "request_ref": request.request_ref,
        "idempotency_ref": request.idempotency_ref,
        "payload_fingerprint_ref": service.prepare(
            request, now=now
        ).payload_fingerprint_ref,
    }


def test_historical_lookup_preserves_original_receipt_after_later_operation(operation):
    service, request, now = operation
    result = execute(service, request, now)
    receipt = result[1] if isinstance(result, tuple) else result
    repo = service.repository
    backup_path = repo.root.parent / "synthetic-backup.enc"
    backup = FinanceMutationRequest(
        operation="backup",
        repository_ref=request.repository_ref,
        target_ref=finance_target_ref(backup_path),
        expected_revision=request.expected_revision + 1,
        request_ref="request-ref:finance:later-backup",
        idempotency_ref="idempotency-ref:finance:later-backup",
    )
    execute(service, backup, now, backup_path=backup_path)
    before = files(repo)
    assert (
        repo.inspect_committed_receipt_read_only(
            **historical_binding(service, request, now)
        )
        == receipt
    )
    assert files(repo) == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("request_ref", "request-ref:finance:other"),
        ("idempotency_ref", "idempotency-ref:finance:other"),
        ("payload_fingerprint_ref", "finance-mutation-payload-ref:other"),
        ("repository_ref", "repository-ref:finance:other"),
        ("operation", "review_decision"),
    ],
)
def test_historical_lookup_rejects_identity_collisions_without_writes(
    operation, field, value
):
    service, request, now = operation
    execute(service, request, now)
    binding = historical_binding(service, request, now)
    binding[field] = value
    before = files(service.repository)
    with pytest.raises(
        RuntimeError, match="FINANCE_(IDEMPOTENCY|REQUEST_REF)_CONFLICT"
    ):
        service.repository.inspect_committed_receipt_read_only(**binding)
    assert files(service.repository) == before


def test_historical_lookup_does_not_promote_prepared_or_pending_state(
    operation, monkeypatch
):
    interrupt(operation, monkeypatch)
    service, request, now = operation
    before = files(service.repository)
    assert (
        service.repository.inspect_committed_receipt_read_only(
            **historical_binding(service, request, now)
        )
        is None
    )
    assert files(service.repository) == before


def test_historical_lookup_does_not_initialize_missing_or_empty_repository(tmp_path):
    repo = FinanceRepository(
        tmp_path / "absent", crypto_backend=InMemoryFinanceCryptoBackend()
    )
    binding = {
        "operation": "create",
        "repository_ref": finance_repository_ref(repo.root),
        "request_ref": "request-ref:finance:absent",
        "idempotency_ref": "idempotency-ref:finance:absent",
        "payload_fingerprint_ref": "finance-mutation-payload-ref:absent",
    }
    assert repo.inspect_committed_receipt_read_only(**binding) is None
    assert not repo.root.exists()
    repo.root.mkdir(mode=0o700)
    assert repo.inspect_committed_receipt_read_only(**binding) is None
    assert list(repo.root.iterdir()) == []
