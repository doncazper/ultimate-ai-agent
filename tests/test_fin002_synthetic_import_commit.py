from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError
from scripts.dev import uaa_finance

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.finance.authority import (
    FinanceAuthorityError,
    FinanceMutationRequest,
    build_exact_finance_lease,
    build_finance_import_commit_capability_manifest,
)
from ultimate_ai_agent.core.finance.crypto import InMemoryFinanceCryptoBackend
from ultimate_ai_agent.core.finance.import_commit import (
    FIN002_IMPORT_SAFE_DISABLE_REF,
    FIN002_SYNTHETIC_IMPORT_COMMIT_CAPABILITY_REF,
)
from ultimate_ai_agent.core.finance.import_preview import (
    preview_synthetic_csv_fixture,
)
from ultimate_ai_agent.core.finance.models import FinanceSnapshot, stable_finance_ref
from ultimate_ai_agent.core.finance.repository import (
    FINANCE_REPOSITORY_ENCRYPTED_FILE,
    FINANCE_REPOSITORY_PENDING_COMMIT_FILE,
    FINANCE_REPOSITORY_RECEIPTS_FILE,
    FinanceRepository,
    FinanceRepositoryError,
)
from ultimate_ai_agent.core.finance.service import (
    FinanceKernelService,
    finance_repository_ref,
)


BOOK_FIXTURE_REF = "fixture-ref:finance/FIN-001:balanced-local-book:v1"
IMPORT_FIXTURE_REF = "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1"


def _request(
    root: Path,
    operation: str,
    *,
    suffix: str,
    expected_revision: int,
) -> FinanceMutationRequest:
    if operation == "create":
        return FinanceMutationRequest(
            operation=operation,
            repository_ref=finance_repository_ref(root),
            fixture_ref=BOOK_FIXTURE_REF,
            expected_revision=expected_revision,
            request_ref=f"request-ref:finance:fin002b-{suffix}",
            idempotency_ref=f"idempotency-ref:finance:fin002b-{suffix}",
        )
    preview = preview_synthetic_csv_fixture(IMPORT_FIXTURE_REF)
    return FinanceMutationRequest(
        operation="import_commit",
        repository_ref=finance_repository_ref(root),
        fixture_ref=preview.fixture_ref,
        import_preview_ref=preview.preview_ref,
        import_profile_ref=preview.profile_ref,
        import_fixture_manifest_ref=preview.import_fixture_manifest_ref,
        import_candidate_refs=tuple(item.candidate_ref for item in preview.candidates),
        import_source_fingerprint_refs=tuple(
            item.source_fingerprint_ref for item in preview.observations
        ),
        expected_revision=expected_revision,
        request_ref=f"request-ref:finance:fin002b-{suffix}",
        idempotency_ref=f"idempotency-ref:finance:fin002b-{suffix}",
        safe_disable_ref=FIN002_IMPORT_SAFE_DISABLE_REF,
    )


def _authorize(
    service: FinanceKernelService,
    request: FinanceMutationRequest,
    *,
    now: datetime,
):
    preview = service.prepare(request, now=now)
    approvals = LocalApprovalAuthority()
    approvals.create_request(preview.approval_request)
    approvals.grant(
        preview.approval_request.approval_request_id,
        approved_by_actor_id="actor-ref:finance:fin002b-test-operator",
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
            "authority-lease-ref:finance:fin002b-test",
            {"preview_ref": preview.preview_ref},
        ),
        issued_at=now - timedelta(seconds=1),
        expires_at=now + timedelta(minutes=10),
    )
    return bound, preview, approvals, lease


def _execute(
    service: FinanceKernelService,
    request: FinanceMutationRequest,
    *,
    now: datetime,
):
    bound, preview, approvals, lease = _authorize(service, request, now=now)
    return service.execute(
        bound,
        preview=preview,
        approval_authority=approvals,
        lease_provider=lambda: [lease],
        clock=lambda: now,
    )


@pytest.fixture
def initialized_kernel(tmp_path: Path):
    root = tmp_path / "protected-book"
    service = FinanceKernelService(
        FinanceRepository(root, crypto_backend=InMemoryFinanceCryptoBackend())
    )
    now = datetime.now(UTC)
    _execute(
        service,
        _request(root, "create", suffix="create", expected_revision=0),
        now=now,
    )
    return service, root, now


def test_import_commit_has_separate_exact_capability_contract() -> None:
    capability = build_finance_import_commit_capability_manifest()
    assert capability.metadata["capability_ref"] == (
        FIN002_SYNTHETIC_IMPORT_COMMIT_CAPABILITY_REF
    )
    assert capability.approval_required is True
    assert capability.single_writer_required is True
    assert capability.connector_write_allowed is False
    assert capability.metadata["preview_revalidation_required"] is True
    assert capability.metadata["fingerprint_census_revalidation_required"] is True


def test_exact_preview_commit_is_atomic_balanced_and_redacted(
    initialized_kernel,
) -> None:
    service, root, now = initialized_kernel
    request = _request(root, "import_commit", suffix="commit", expected_revision=1)
    proof, receipt = _execute(service, request, now=now)

    assert receipt.phase == "committed"
    assert receipt.operation == "import_commit"
    assert proof.mutation_receipt_ref == receipt.receipt_ref
    assert proof.before_revision == 1
    assert proof.after_revision == 2
    assert proof.mutation_performed is True
    assert proof.raw_source_content_included is False
    assert proof.real_financial_data_included is False

    snapshot = service.repository.load_snapshot(
        request_ref="request-ref:finance:fin002b-read"
    )
    assert snapshot.revision == snapshot.generation == 2
    assert len(snapshot.import_commits) == 1
    assert len(snapshot.journal_entries) == 8
    record = snapshot.import_commits[0]
    assert record.commit_ref == proof.commit_ref
    assert record.candidate_refs == proof.candidate_refs
    assert record.journal_entry_refs == proof.journal_entry_refs
    assert set(record.journal_entry_refs).issubset(
        {item.journal_entry_ref for item in snapshot.journal_entries}
    )
    imported = [
        item
        for item in snapshot.journal_entries
        if item.journal_entry_ref in record.journal_entry_refs
    ]
    assert all(
        sum(p.signed_amount_minor for p in item.postings) == 0 for item in imported
    )
    assert {
        tuple((posting.account_ref, posting.side) for posting in item.postings)
        for item in imported
    } == {
        (
            ("financial-account-ref:finance:synthetic-cash", "credit"),
            ("financial-account-ref:finance:synthetic-suspense", "debit"),
        ),
        (
            ("financial-account-ref:finance:synthetic-cash", "debit"),
            ("financial-account-ref:finance:synthetic-suspense", "credit"),
        ),
    }
    redacted = snapshot.redacted_read_model()
    assert redacted["counts"]["import_commits"] == 1
    assert redacted["counts"]["imported_candidates"] == 2
    assert "source_fingerprint_refs" not in redacted
    ciphertext = (root / FINANCE_REPOSITORY_ENCRYPTED_FILE).read_bytes()
    assert IMPORT_FIXTURE_REF.encode() not in ciphertext
    receipt_text = (root / FINANCE_REPOSITORY_RECEIPTS_FILE).read_text()
    assert "amount_minor" not in receipt_text
    assert str(root) not in receipt_text


def test_exact_replay_returns_same_receipt_without_second_commit(
    initialized_kernel,
) -> None:
    service, root, now = initialized_kernel
    request = _request(root, "import_commit", suffix="replay", expected_revision=1)
    first_proof, first_receipt = _execute(service, request, now=now)
    second_proof, second_receipt = _execute(service, request, now=now)

    assert second_receipt.replayed is True
    assert second_receipt.receipt_ref == first_receipt.receipt_ref
    assert second_proof.replayed is True
    assert second_proof.proof_ref == first_proof.proof_ref
    snapshot = service.repository.load_snapshot(
        request_ref="request-ref:finance:fin002b-replay-read"
    )
    assert snapshot.revision == 2
    assert len(snapshot.import_commits) == 1


def test_changed_or_stale_preview_fails_at_final_repository_boundary(
    initialized_kernel,
) -> None:
    service, root, now = initialized_kernel
    first = _request(root, "import_commit", suffix="first", expected_revision=1)
    stale = _request(root, "import_commit", suffix="stale", expected_revision=1)
    tampered = stale.model_copy(
        update={
            "import_candidate_refs": (
                "transaction-candidate-ref:finance/FIN-002:changed",
                *stale.import_candidate_refs[1:],
            )
        }
    )

    with pytest.raises(FinanceRepositoryError, match="FIN002_IMPORT_PREVIEW_STALE"):
        _execute(service, tampered, now=now)
    _execute(service, first, now=now)
    with pytest.raises(FinanceRepositoryError, match="FINANCE_STALE_REVISION"):
        _execute(service, stale, now=now)


def test_import_requires_its_exact_approval_lease_and_safe_disable(
    initialized_kernel,
) -> None:
    service, root, now = initialized_kernel
    request = _request(root, "import_commit", suffix="authority", expected_revision=1)
    bound, preview, approvals, _lease = _authorize(service, request, now=now)

    create_request = _request(root, "create", suffix="wrong-lease", expected_revision=0)
    create_preview = service.prepare(create_request, now=now)
    wrong_lease = build_exact_finance_lease(
        create_preview,
        lease_ref="authority-lease-ref:finance:fin002b-wrong",
        issued_at=now - timedelta(seconds=1),
        expires_at=now + timedelta(minutes=10),
    )
    with pytest.raises(
        FinanceAuthorityError, match="FINANCE_EXACT_AUTHORITY_LEASE_DENIED"
    ):
        service.execute(
            bound,
            preview=preview,
            approval_authority=approvals,
            lease_provider=lambda: [wrong_lease],
            clock=lambda: now,
        )

    exact_lease = build_exact_finance_lease(
        preview,
        lease_ref="authority-lease-ref:finance:fin002b-disabled",
        issued_at=now - timedelta(seconds=1),
        expires_at=now + timedelta(minutes=10),
    )
    with pytest.raises(FinanceAuthorityError, match="FINANCE_SAFE_DISABLE_ENGAGED"):
        service.execute(
            bound,
            preview=preview,
            approval_authority=approvals,
            lease_provider=lambda: [exact_lease],
            clock=lambda: now,
            safe_disable_engaged=lambda: True,
        )
    assert (
        service.repository.load_snapshot(
            request_ref="request-ref:finance:fin002b-no-mutation"
        ).revision
        == 1
    )


def test_import_request_and_snapshot_lineage_tamper_fail_closed(
    initialized_kernel,
) -> None:
    _service, root, _now = initialized_kernel
    request = _request(root, "import_commit", suffix="shape", expected_revision=1)
    payload = request.model_dump(mode="python")
    payload["import_source_fingerprint_refs"] = ()
    with pytest.raises(
        ValidationError, match="FIN002_IMPORT_COMMIT_REQUEST_SCOPE_INVALID"
    ):
        FinanceMutationRequest.model_validate(payload)

    wrong_safe_disable = request.model_dump(mode="python")
    wrong_safe_disable["safe_disable_ref"] = (
        "safe-disable-ref:finance/FIN-001:synthetic-mutations"
    )
    with pytest.raises(
        ValidationError, match="FIN002_IMPORT_COMMIT_REQUEST_SCOPE_INVALID"
    ):
        FinanceMutationRequest.model_validate(wrong_safe_disable)

    preview = preview_synthetic_csv_fixture(IMPORT_FIXTURE_REF)
    empty = FinanceSnapshot(
        repository_ref="repository-ref:finance:fin002b-empty",
        revision=1,
        generation=1,
        fixture_manifest_ref="fixture-manifest-ref:finance:fin002b-empty",
    )
    with pytest.raises(Exception, match="FIN002_IMPORT_SUSPENSE_ACCOUNT_UNAVAILABLE"):
        from ultimate_ai_agent.core.finance.import_commit import (
            build_import_commit_record,
        )

        build_import_commit_record(preview, before=empty)


def test_commit_proof_json_contains_safe_refs_only(initialized_kernel) -> None:
    service, root, now = initialized_kernel
    proof, receipt = _execute(
        service,
        _request(root, "import_commit", suffix="safe-proof", expected_revision=1),
        now=now,
    )
    serialized = json.dumps(proof.model_dump(mode="json"), sort_keys=True)
    assert receipt.receipt_ref in serialized
    for forbidden in ("office-supply", "service-income", "amount_minor", str(root)):
        assert forbidden not in serialized


def test_prepersist_approval_revocation_blocks_import(initialized_kernel) -> None:
    service, root, now = initialized_kernel
    request = _request(root, "import_commit", suffix="revoked", expected_revision=1)
    bound, preview, approvals, lease = _authorize(service, request, now=now)
    calls = 0

    def revoke_before_final_boundary():
        nonlocal calls
        calls += 1
        if calls == 2:
            approvals.revoke(preview.expected_approval_ref, "test revocation")
        return [lease]

    with pytest.raises(FinanceAuthorityError, match="FINANCE_LOCAL_APPROVAL_DENIED"):
        service.execute(
            bound,
            preview=preview,
            approval_authority=approvals,
            lease_provider=revoke_before_final_boundary,
            clock=lambda: now,
        )
    snapshot = service.repository.load_snapshot(
        request_ref="request-ref:finance:fin002b-revoked-read"
    )
    assert snapshot.revision == 1
    assert not snapshot.import_commits


def test_cli_prepare_binds_current_preview_without_mutating(
    initialized_kernel,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    service, root, _now = initialized_kernel
    args = uaa_finance.parser().parse_args(
        [
            "prepare",
            "--repository-dir",
            str(root),
            "--helper-path",
            str(root / "unused-helper"),
            "--helper-sha256",
            "a" * 64,
            "--operation",
            "import_commit",
            "--expected-revision",
            "1",
            "--request-ref",
            "request-ref:finance:fin002b-cli-prepare",
            "--idempotency-ref",
            "idempotency-ref:finance:fin002b-cli-prepare",
            "--import-fixture-ref",
            IMPORT_FIXTURE_REF,
        ]
    )
    monkeypatch.setattr(uaa_finance, "_service", lambda _args: service)

    assert uaa_finance.command_prepare(args) == 0
    payload = json.loads(capsys.readouterr().out)
    preview = preview_synthetic_csv_fixture(IMPORT_FIXTURE_REF)
    assert payload["mutation_performed"] is False
    assert payload["operator_confirmation_required"] is True
    assert payload["request"]["import_preview_ref"] == preview.preview_ref
    assert payload["request"]["import_candidate_refs"] == [
        item.candidate_ref for item in preview.candidates
    ]
    snapshot = service.repository.load_snapshot(
        request_ref="request-ref:finance:fin002b-cli-read"
    )
    assert snapshot.revision == 1
    assert not snapshot.import_commits


def test_pending_generation_recovers_without_double_import(
    initialized_kernel, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, root, now = initialized_kernel
    request = _request(root, "import_commit", suffix="recovery", expected_revision=1)
    repository = service.repository
    original_recover = repository._recover_pending_commit

    def interrupt_after_pending_generation():
        if repository.pending_commit_path.exists():
            raise OSError("injected pending generation interruption")
        return original_recover()

    monkeypatch.setattr(
        repository, "_recover_pending_commit", interrupt_after_pending_generation
    )
    with pytest.raises(OSError, match="injected pending generation interruption"):
        _execute(service, request, now=now)
    assert (root / FINANCE_REPOSITORY_PENDING_COMMIT_FILE).is_file()

    monkeypatch.setattr(repository, "_recover_pending_commit", original_recover)
    proof, receipt = _execute(service, request, now=now)
    assert receipt.replayed is True
    assert proof.replayed is True
    snapshot = repository.load_snapshot(
        request_ref="request-ref:finance:fin002b-recovery-read"
    )
    assert snapshot.revision == 2
    assert len(snapshot.import_commits) == 1
    assert not (root / FINANCE_REPOSITORY_PENDING_COMMIT_FILE).exists()
