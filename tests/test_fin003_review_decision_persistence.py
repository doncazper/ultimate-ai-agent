from __future__ import annotations

from datetime import UTC, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError
from scripts.dev import uaa_finance

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityLeaseRevokeRequest
from ultimate_ai_agent.core.capabilities.enums import PolicyDecisionStatus
from ultimate_ai_agent.core.finance import repository as repository_module
from ultimate_ai_agent.core.finance.authority import (
    FinanceAuthorityError,
    FinanceMutationRequest,
    build_exact_finance_lease,
    build_finance_review_decision_capability_manifest,
)
from ultimate_ai_agent.core.finance.crypto import InMemoryFinanceCryptoBackend
from ultimate_ai_agent.core.finance.import_commit import FIN002_IMPORT_SAFE_DISABLE_REF
from ultimate_ai_agent.core.finance.import_preview import preview_synthetic_csv_fixture
from ultimate_ai_agent.core.finance.models import stable_finance_ref
from ultimate_ai_agent.core.finance.repository import (
    FinanceMutationPermit,
    FinanceMutationReceipt,
    FinanceRepository,
    FinanceRepositoryError,
)
from ultimate_ai_agent.core.finance.review_decision_commit import (
    FIN003_REVIEW_CAPABILITY_REF,
    FIN003_REVIEW_SAFE_DISABLE_REF,
    preview_finance_review_persistence,
)
from ultimate_ai_agent.core.finance.review_projection import (
    build_finance_review_projection,
)
from ultimate_ai_agent.core.finance.service import (
    FinanceKernelService,
    finance_repository_ref,
    finance_target_ref,
)


def _authorize(service, request, now):
    preview = service.prepare(request, now=now)
    approvals = LocalApprovalAuthority()
    approvals.create_request(preview.approval_request)
    approvals.grant(
        preview.approval_request.approval_request_id,
        approved_by_actor_id="actor-ref:finance:fin003-test-operator",
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
            "authority-lease-ref:finance:fin003-test",
            {"preview_ref": preview.preview_ref},
        ),
        issued_at=now - timedelta(seconds=1),
        expires_at=now + timedelta(minutes=10),
    )
    return bound, preview, approvals, lease


def _execute(service, request, now, **changes):
    bound, preview, approvals, lease = _authorize(service, request, now)
    return service.execute(
        bound,
        **{
            "preview": preview,
            "approval_authority": approvals,
            "lease_provider": lambda: [lease],
            "clock": lambda: now,
            **changes,
        },
    )


@pytest.fixture
def kernel(tmp_path: Path):
    root = tmp_path / "protected-book"
    crypto = InMemoryFinanceCryptoBackend()
    service = FinanceKernelService(FinanceRepository(root, crypto_backend=crypto))
    now = datetime.now(UTC)
    common = {"repository_ref": finance_repository_ref(root)}
    create = FinanceMutationRequest(
        **common,
        operation="create",
        fixture_ref="fixture-ref:finance/FIN-001:balanced-local-book:v1",
        expected_revision=0,
        request_ref="request-ref:finance:fin003-create",
        idempotency_ref="idempotency-ref:finance:fin003-create",
    )
    _execute(service, create, now)
    imported = preview_synthetic_csv_fixture(
        "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1"
    )
    commit = FinanceMutationRequest(
        **common,
        operation="import_commit",
        fixture_ref=imported.fixture_ref,
        import_preview_ref=imported.preview_ref,
        import_profile_ref=imported.profile_ref,
        import_fixture_manifest_ref=imported.import_fixture_manifest_ref,
        import_candidate_refs=tuple(item.candidate_ref for item in imported.candidates),
        import_source_fingerprint_refs=tuple(
            item.source_fingerprint_ref for item in imported.observations
        ),
        expected_revision=1,
        request_ref="request-ref:finance:fin003-import",
        idempotency_ref="idempotency-ref:finance:fin003-import",
        safe_disable_ref=FIN002_IMPORT_SAFE_DISABLE_REF,
    )
    _execute(service, commit, now)
    return service, crypto, now


def _snapshot(service):
    return service.repository.load_snapshot_read_only(
        request_ref="request-ref:finance:fin003-inspect"
    )


def _request(
    service,
    *,
    decision="confirm",
    compensates_event_ref=None,
    suffix="decision",
    item=0,
):
    snapshot = _snapshot(service)
    preview = preview_finance_review_persistence(
        snapshot,
        review_item_ref=build_finance_review_projection(snapshot)
        .review_items[item]
        .review_item_ref,
        request_ref=f"request-ref:finance:fin003-{suffix}",
        idempotency_ref=f"idempotency-ref:finance:fin003-{suffix}",
        decision=decision,
        compensates_event_ref=compensates_event_ref,
    )
    return FinanceMutationRequest(
        operation=preview.operation,
        repository_ref=preview.repository_ref,
        review_preview=preview,
        expected_revision=preview.source_revision,
        request_ref=preview.request_ref,
        idempotency_ref=preview.idempotency_ref,
        safe_disable_ref=FIN003_REVIEW_SAFE_DISABLE_REF,
    )


@pytest.mark.parametrize("decision", ["confirm", "reject", "defer"])
def test_approved_review_survives_reopen_replays_once_and_compensates(kernel, decision):
    service, crypto, now = kernel
    before = _snapshot(service)
    request = _request(service, decision=decision)
    preview = service.prepare(request, now=now)
    assert preview.capability_ref == FIN003_REVIEW_CAPABILITY_REF
    first = _execute(service, request, now)
    reopened = FinanceKernelService(
        FinanceRepository(service.repository.root, crypto_backend=crypto)
    )
    saved = _snapshot(reopened)
    assert saved.revision == 3
    assert saved.review_decisions[0].decision == decision
    assert saved.review_decisions[0].event_ref in first.proof_refs
    replay = _execute(reopened, request, now)
    assert replay.replayed is True
    assert replay.receipt_ref == first.receipt_ref
    assert _snapshot(reopened) == saved
    undo_request = _request(
        reopened,
        decision=None,
        compensates_event_ref=saved.review_decisions[0].event_ref,
        suffix="undo",
    )
    undo = _execute(reopened, undo_request, now)
    final = _snapshot(reopened)
    assert undo.operation == "review_undo"
    assert final.revision == 4
    assert len(final.review_decisions) == 2
    assert final.effective_review_decisions() == {}
    assert final.journal_entries == before.journal_entries
    assert final.account_balances() == before.account_balances()
    assert final.review_decisions[0] == saved.review_decisions[0]
    assert _execute(reopened, undo_request, now).receipt_ref == undo.receipt_ref


def test_current_approval_lease_and_safe_disable_are_required(kernel):
    service, _crypto, now = kernel
    request = _request(service)
    before = _snapshot(service)
    with pytest.raises(FinanceAuthorityError, match="LEASE_DENIED"):
        _execute(service, request, now, lease_provider=lambda: [])
    with pytest.raises(FinanceAuthorityError, match="SAFE_DISABLE_ENGAGED"):
        _execute(service, request, now, safe_disable_engaged=lambda: True)
    with pytest.raises(FinanceAuthorityError, match="PREVIEW_EXPIRED"):
        _execute(service, request, now, clock=lambda: now + timedelta(hours=1))
    assert _snapshot(service) == before


def test_stale_revision_and_changed_payload_replay_are_rejected(kernel):
    service, _crypto, now = kernel
    first = _request(service)
    competing = _request(service, decision="defer", suffix="competing")
    _execute(service, first, now)
    with pytest.raises(FinanceRepositoryError, match="STALE_REVISION"):
        _execute(service, competing, now)
    changed = _request(service, decision="reject")
    with pytest.raises(FinanceRepositoryError, match="IDEMPOTENCY_CONFLICT"):
        _execute(service, changed, now)
    assert len(_snapshot(service).review_decisions) == 1


@pytest.mark.parametrize("capacity", ["receipt", "generation"])
def test_capacity_is_checked_before_any_prepared_write(kernel, monkeypatch, capacity):
    service, _crypto, now = kernel
    request = _request(service)
    repo = service.repository
    before = {
        path.name: path.read_bytes() for path in repo.root.iterdir() if path.is_file()
    }
    if capacity == "receipt":
        monkeypatch.setattr(
            repository_module,
            "FINANCE_RECEIPT_LOG_MAX_BYTES",
            repo.receipts_path.stat().st_size + 1,
        )
    else:
        monkeypatch.setattr(repository_module, "FINANCE_GENERATION_MAX_BYTES", 1)
    with pytest.raises(FinanceRepositoryError, match="CAPACITY_EXHAUSTED"):
        _execute(service, request, now)
    after = {
        path.name: path.read_bytes() for path in repo.root.iterdir() if path.is_file()
    }
    assert after == before


class InterruptedWrite(RuntimeError):
    pass


@pytest.mark.parametrize(
    "boundary", ["prepared", "pending", "ciphertext", "metadata", "committed"]
)
@pytest.mark.parametrize("after_write", [False, True])
def test_atomic_generation_faults_recover_or_replay_exactly_once(
    kernel, monkeypatch, boundary, after_write
):
    service, crypto, now = kernel
    request = _request(service)
    repo = service.repository
    write = repo._atomic_write
    raised = False

    def interrupted(path, payload):
        nonlocal raised
        matched = (
            (boundary == "pending" and path == repo.pending_commit_path)
            or (boundary == "ciphertext" and path == repo.encrypted_path)
            or (boundary == "metadata" and path == repo.metadata_path)
            or (
                boundary == "prepared"
                and path == repo.receipts_path
                and b'"phase":"prepared","policy_decision_ref":"policy-decision-ref:finance/FIN-003'
                in payload
            )
            or (
                boundary == "committed"
                and path == repo.receipts_path
                and b'"phase":"committed","policy_decision_ref":"policy-decision-ref:finance/FIN-003'
                in payload
            )
        )
        if matched and not raised:
            raised = True
            if after_write:
                write(path, payload)
            raise InterruptedWrite("FIN003_TEST_INTERRUPTED_WRITE")
        return write(path, payload)

    # Metadata uses the classmethod JSON writer; intercept its actual common
    # atomic-write boundary as well as instance-dispatched binary writes.
    monkeypatch.setattr(FinanceRepository, "_atomic_write", staticmethod(interrupted))
    with pytest.raises(InterruptedWrite):
        _execute(service, request, now)
    assert raised
    reopened = FinanceKernelService(FinanceRepository(repo.root, crypto_backend=crypto))
    receipt = _execute(reopened, request, now)
    snapshot = _snapshot(reopened)
    assert snapshot.revision == 3
    assert len(snapshot.review_decisions) == 1
    assert snapshot.review_decisions[0].event_ref in receipt.proof_refs
    assert not reopened.repository.pending_commit_path.exists()
    assert _execute(reopened, request, now).receipt_ref == receipt.receipt_ref


def _cli_args(service, command, *options):
    return uaa_finance.parser().parse_args(
        [
            command,
            "--repository-dir",
            str(service.repository.root),
            "--helper-path",
            str(service.repository.root / "unused-helper"),
            "--helper-sha256",
            "a" * 64,
            *options,
        ]
    )


def test_cli_prepare_confirm_replay_review_and_undo_share_durable_truth(
    kernel, monkeypatch, capsys, tmp_path
):
    service, crypto, _now = kernel
    monkeypatch.setattr(uaa_finance, "_backend", lambda _args: crypto)
    before = _snapshot(service)
    item = build_finance_review_projection(before).review_items[0]
    prepared_args = _cli_args(
        service,
        "prepare",
        "--operation",
        "review_decision",
        "--expected-revision",
        "2",
        "--request-ref",
        "request-ref:finance:fin003-cli-save",
        "--idempotency-ref",
        "idempotency-ref:finance:fin003-cli-save",
        "--review-item-ref",
        item.review_item_ref,
        "--decision",
        "confirm",
    )
    assert uaa_finance.command_prepare(prepared_args) == 0
    bundle = json.loads(capsys.readouterr().out)
    assert bundle["mutation_performed"] is False
    assert bundle["operator_confirmation_required"] is True
    assert bundle["preview"]["capability_ref"] == FIN003_REVIEW_CAPABILITY_REF
    assert _snapshot(service) == before
    bundle_path = tmp_path / "review-bundle.json"
    bundle_path.write_text(json.dumps(bundle))
    unconfirmed = _cli_args(service, "run", "--bundle", str(bundle_path))
    with pytest.raises(ValueError, match="OPERATOR_CONFIRMATION_REQUIRED"):
        uaa_finance.command_run(unconfirmed)
    run_args = _cli_args(service, "run", "--bundle", str(bundle_path), "--confirmed")
    assert uaa_finance.command_run(run_args) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["receipt"]["phase"] == "committed"
    assert uaa_finance.command_run(run_args) == 0
    replay = json.loads(capsys.readouterr().out)
    assert replay["receipt"]["replayed"] is True
    assert replay["receipt"]["receipt_ref"] == first["receipt"]["receipt_ref"]
    read_args = _cli_args(
        service, "review", "--request-ref", "request-ref:finance:fin003-cli-review"
    )
    assert uaa_finance.command_read(read_args) == 0
    reviewed = json.loads(capsys.readouterr().out)
    assert reviewed["review_items"][0]["state"] == "confirmed"
    assert reviewed["review_items"][0]["lineage_ref"] == item.lineage_ref
    assert len(reviewed["decision_history"]) == 1
    undo_args = _cli_args(
        service,
        "prepare",
        "--operation",
        "review_undo",
        "--expected-revision",
        "3",
        "--request-ref",
        "request-ref:finance:fin003-cli-undo",
        "--idempotency-ref",
        "idempotency-ref:finance:fin003-cli-undo",
        "--review-item-ref",
        reviewed["review_items"][0]["review_item_ref"],
        "--compensates-event-ref",
        reviewed["decision_history"][0]["event_ref"],
    )
    assert uaa_finance.command_prepare(undo_args) == 0
    undo_bundle = json.loads(capsys.readouterr().out)
    undo_path = tmp_path / "undo-bundle.json"
    undo_path.write_text(json.dumps(undo_bundle))
    assert (
        uaa_finance.command_run(
            _cli_args(service, "run", "--bundle", str(undo_path), "--confirmed")
        )
        == 0
    )
    undone_result = json.loads(capsys.readouterr().out)
    assert undone_result["receipt"]["operation"] == "review_undo"
    assert uaa_finance.command_read(read_args) == 0
    undone = json.loads(capsys.readouterr().out)
    assert undone["review_items"][0]["state"] == "needs_review"
    assert len(undone["decision_history"]) == 2
    assert _snapshot(service).account_balances() == before.account_balances()
    for payload in (
        bundle,
        first,
        replay,
        reviewed,
        undo_bundle,
        undone_result,
        undone,
    ):
        encoded = json.dumps(payload)
        assert str(service.repository.root) not in encoded
        assert "amount_minor" not in encoded
        for imported in before.import_commits:
            assert all(ref not in encoded for ref in imported.source_fingerprint_refs)


@pytest.mark.parametrize("decision", ["confirm", "reject", "defer"])
def test_review_projection_preserves_open_deferrals_and_complete_review_posture(
    kernel, decision
):
    service, _crypto, now = kernel
    initial = build_finance_review_projection(_snapshot(service))
    _execute(service, _request(service, decision=decision), now)
    once = build_finance_review_projection(_snapshot(service))
    expected = {"confirm": "confirmed", "reject": "rejected", "defer": "deferred"}[
        decision
    ]
    assert once.review_items[0].state == expected
    assert once.review_items[0].lineage_ref == initial.review_items[0].lineage_ref
    assert (
        once.review_items[0].review_item_ref != initial.review_items[0].review_item_ref
    )
    assert once.review_batches[0].state == once.action_inbox[0].state == "needs_review"
    _execute(
        service, _request(service, decision=decision, suffix="second", item=1), now
    )
    twice = build_finance_review_projection(_snapshot(service))
    expected_batch = "needs_review" if decision == "defer" else "reviewed"
    assert (
        twice.review_batches[0].state == twice.action_inbox[0].state == expected_batch
    )
    assert len(twice.decision_history) == 2
    assert all(
        item.consequence_ref.endswith("posting-remains-in-suspense")
        for item in twice.review_items
    )


@pytest.mark.parametrize(
    "message",
    [
        "untrusted sample text",
        "FIN003_FAILED: sample detail",
        "FIN003_FAILED\nsample detail",
    ],
)
def test_cli_error_output_does_not_repeat_exception_text(message):
    assert (
        uaa_finance._safe_error_code(ValueError(message))
        == "FINANCE_CLI_REQUEST_FAILED"
    )
    assert (
        uaa_finance._safe_error_code(ValueError("FIN003_REVIEW_CLI_SCOPE_INVALID"))
        == "FIN003_REVIEW_CLI_SCOPE_INVALID"
    )


def test_safe_disable_rejects_before_bundle_read_or_authority_side_effects(
    kernel, monkeypatch, tmp_path
):
    service, _crypto, _now = kernel

    def forbidden(*_args, **_kwargs):
        pytest.fail("Disabled execution must not read a bundle or issue authority")

    monkeypatch.setattr(uaa_finance, "_read_prepared_bundle", forbidden)
    monkeypatch.setattr(uaa_finance, "_authority_state_dir", forbidden)
    args = _cli_args(
        service,
        "run",
        "--bundle",
        str(tmp_path / "unused.json"),
        "--confirmed",
        "--safe-disable-engaged",
    )
    with pytest.raises(ValueError, match="SAFE_DISABLE_ENGAGED"):
        uaa_finance.command_run(args)


@pytest.mark.parametrize("field", ["extra", "posture", "approval", "preview"])
def test_refresh_rejects_rebound_bundle_without_mutation(
    kernel, monkeypatch, capsys, tmp_path, field
):
    service, crypto, now = kernel
    monkeypatch.setattr(uaa_finance, "_backend", lambda _args: crypto)
    request = _request(service)
    bound, preview, _approvals, _lease = _authorize(service, request, now)
    uaa_finance._emit_prepared_bundle(bound, preview)
    bundle = json.loads(capsys.readouterr().out)
    if field == "extra":
        bundle["unexpected"] = True
    elif field == "posture":
        bundle["operator_confirmation_required"] = False
    elif field == "approval":
        bundle["request"]["approval_ref"] = "approval-ref:finance:unreviewed"
    else:
        bundle["preview"]["prepared_at"] = (now - timedelta(seconds=1)).isoformat()
    path = tmp_path / "rebound.json"
    path.write_text(json.dumps(bundle))
    before = _snapshot(service)
    with pytest.raises(ValueError):
        uaa_finance.command_refresh_review(
            _cli_args(service, "refresh-review", "--bundle", str(path))
        )
    assert _snapshot(service) == before
    assert capsys.readouterr().out == ""


def test_persistence_contract_verifier():
    from scripts.verify_fin003_review_decision_persistence import verify

    assert verify() == []


def test_expired_cli_preparation_requires_fresh_review_and_confirmation(
    kernel, monkeypatch, capsys, tmp_path
):
    service, crypto, now = kernel
    monkeypatch.setattr(uaa_finance, "_backend", lambda _args: crypto)
    request = _request(service)
    old = service.prepare(request, now=now - timedelta(hours=1))
    uaa_finance._emit_prepared_bundle(request, old)
    bundle = json.loads(capsys.readouterr().out)
    path = tmp_path / "expired.json"
    path.write_text(json.dumps(bundle))
    before = _snapshot(service)
    with pytest.raises((ValueError, FinanceAuthorityError)):
        uaa_finance.command_run(
            _cli_args(service, "run", "--bundle", str(path), "--confirmed")
        )
    assert _snapshot(service) == before
    uaa_finance.command_refresh_review(
        _cli_args(service, "refresh-review", "--bundle", str(path))
    )
    refreshed = json.loads(capsys.readouterr().out)
    assert refreshed["request"] == bundle["request"]
    assert refreshed["preview"]["preview_ref"] != old.preview_ref
    assert _snapshot(service) == before
    fresh_path = tmp_path / "fresh.json"
    fresh_path.write_text(json.dumps(refreshed))
    with pytest.raises(ValueError, match="OPERATOR_CONFIRMATION_REQUIRED"):
        uaa_finance.command_run(_cli_args(service, "run", "--bundle", str(fresh_path)))
    assert (
        uaa_finance.command_run(
            _cli_args(service, "run", "--bundle", str(fresh_path), "--confirmed")
        )
        == 0
    )
    assert len(_snapshot(service).review_decisions) == 1


def test_refresh_cannot_make_a_changed_source_current(
    kernel, monkeypatch, capsys, tmp_path
):
    service, crypto, now = kernel
    monkeypatch.setattr(uaa_finance, "_backend", lambda _args: crypto)
    stale = _request(service, suffix="stale-refresh")
    uaa_finance._emit_prepared_bundle(stale, service.prepare(stale, now=now))
    path = tmp_path / "stale.json"
    path.write_text(capsys.readouterr().out)
    _execute(service, _request(service, suffix="current-winner"), now)
    before = _snapshot(service)
    uaa_finance.command_refresh_review(
        _cli_args(service, "refresh-review", "--bundle", str(path))
    )
    refreshed = json.loads(capsys.readouterr().out)
    assert refreshed["request"]["expected_revision"] == stale.expected_revision
    fresh_path = tmp_path / "still-stale.json"
    fresh_path.write_text(json.dumps(refreshed))
    with pytest.raises(FinanceRepositoryError, match="STALE_REVISION"):
        uaa_finance.command_run(
            _cli_args(service, "run", "--bundle", str(fresh_path), "--confirmed")
        )
    assert _snapshot(service) == before


def test_new_confirmed_review_preparation_can_retry_after_prior_lease_revocation(
    kernel, monkeypatch, capsys, tmp_path
):
    service, crypto, _now = kernel
    monkeypatch.setattr(uaa_finance, "_backend", lambda _args: crypto)
    item = build_finance_review_projection(_snapshot(service)).review_items[0]
    args = _cli_args(
        service,
        "prepare",
        "--operation",
        "review_decision",
        "--expected-revision",
        "2",
        "--request-ref",
        "request-ref:finance:fin003-cli-retry",
        "--idempotency-ref",
        "idempotency-ref:finance:fin003-cli-retry",
        "--review-item-ref",
        item.review_item_ref,
        "--decision",
        "confirm",
    )
    uaa_finance.command_prepare(args)
    original_bundle = json.loads(capsys.readouterr().out)
    original_path = tmp_path / "original-review.json"
    original_path.write_text(json.dumps(original_bundle))
    run = _cli_args(service, "run", "--bundle", str(original_path), "--confirmed")
    stage = FinanceRepository._stage_and_commit_generation

    def interrupt(*_args, **_kwargs):
        raise InterruptedWrite("FIN003_TEST_BEFORE_STAGE")

    monkeypatch.setattr(FinanceRepository, "_stage_and_commit_generation", interrupt)
    with pytest.raises(InterruptedWrite):
        uaa_finance.command_run(run)
    monkeypatch.setattr(FinanceRepository, "_stage_and_commit_generation", stage)
    store = uaa_finance.AuthorityLeaseStore(
        uaa_finance._authority_state_dir(service.repository.root)
    )
    issued = store.list_leases(active_only=True)
    assert len(issued) == 1
    store.revoke_lease(
        AuthorityLeaseRevokeRequest(
            lease_ref=issued[0].lease_ref,
            decision_reason_ref="reason-ref:finance:fin003-test-revoke",
            safe_summary="Revoke the exact synthetic test review lease.",
        ),
        idempotency_ref="idempotency-ref:finance:fin003-test-revoke",
    )
    with pytest.raises(FinanceAuthorityError, match="LEASE_DENIED"):
        uaa_finance.command_run(run)
    uaa_finance.command_prepare(args)
    refreshed = json.loads(capsys.readouterr().out)
    assert refreshed["request"] == original_bundle["request"]
    assert (
        refreshed["preview"]["preview_ref"] != original_bundle["preview"]["preview_ref"]
    )
    refreshed_path = tmp_path / "refreshed-review.json"
    refreshed_path.write_text(json.dumps(refreshed))
    assert (
        uaa_finance.command_run(
            _cli_args(service, "run", "--bundle", str(refreshed_path), "--confirmed")
        )
        == 0
    )
    capsys.readouterr()
    assert len(_snapshot(service).review_decisions) == 1


def test_cli_refresh_review_preserves_pending_intent_and_requires_new_confirmation(
    kernel, monkeypatch, capsys, tmp_path
):
    service, crypto, now = kernel
    monkeypatch.setattr(uaa_finance, "_backend", lambda _args: crypto)
    request = _request(service, suffix="pending-cli")
    bound, preview, _approvals, _lease = _authorize(service, request, now)
    uaa_finance._emit_prepared_bundle(bound, preview)
    bundle = json.loads(capsys.readouterr().out)
    path = tmp_path / "pending-review.json"
    path.write_text(json.dumps(bundle))
    recover = FinanceRepository._recover_pending_commit

    def interrupted(repo, **kwargs):
        if repo.pending_commit_path.exists():
            raise InterruptedWrite("FIN003_TEST_PENDING_COMMIT")
        return recover(repo, **kwargs)

    monkeypatch.setattr(FinanceRepository, "_recover_pending_commit", interrupted)
    with pytest.raises(InterruptedWrite):
        uaa_finance.command_run(
            _cli_args(service, "run", "--bundle", str(path), "--confirmed")
        )
    monkeypatch.setattr(FinanceRepository, "_recover_pending_commit", recover)
    with pytest.raises(FinanceRepositoryError, match="REQUIRES_MUTATING_RECOVERY"):
        _snapshot(service)
    files_before = {
        p.name: p.read_bytes() for p in service.repository.root.iterdir() if p.is_file()
    }
    args = _cli_args(service, "refresh-review", "--bundle", str(path))
    assert uaa_finance.command_refresh_review(args) == 0
    refreshed = json.loads(capsys.readouterr().out)
    assert refreshed["request"] == bundle["request"]
    assert refreshed["operator_confirmation_required"] is True
    assert {
        p.name: p.read_bytes() for p in service.repository.root.iterdir() if p.is_file()
    } == files_before
    refreshed_path = tmp_path / "refreshed-pending-review.json"
    refreshed_path.write_text(json.dumps(refreshed))
    with pytest.raises(ValueError, match="CONFIRMATION_REQUIRED"):
        uaa_finance.command_run(
            _cli_args(service, "run", "--bundle", str(refreshed_path))
        )
    assert (
        uaa_finance.command_run(
            _cli_args(service, "run", "--bundle", str(refreshed_path), "--confirmed")
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["receipt"]["replayed"] is True
    assert _snapshot(service).revision == 3
    assert len(_snapshot(service).review_decisions) == 1


@pytest.mark.parametrize("revoke_at", [2, 3, 4])
def test_approval_revocation_at_each_locked_boundary_prevents_commit(kernel, revoke_at):
    service, _crypto, now = kernel
    request = _request(service)
    bound, preview, approvals, lease = _authorize(service, request, now)
    calls = 0

    def current_leases():
        nonlocal calls
        calls += 1
        if calls == revoke_at:
            approvals.revoke(
                preview.expected_approval_ref, "Synthetic review test revocation."
            )
        return [lease]

    with pytest.raises(FinanceAuthorityError, match="LOCAL_APPROVAL_DENIED"):
        service.execute(
            bound,
            preview=preview,
            approval_authority=approvals,
            lease_provider=current_leases,
            clock=lambda: now,
        )
    assert calls == revoke_at
    assert _snapshot(service).revision == 2
    assert not _snapshot(service).review_decisions
    assert not service.repository.pending_commit_path.exists()


def test_current_policy_denial_and_stale_policy_revision_fail_closed(kernel):
    service, _crypto, now = kernel
    request = _request(service)
    with pytest.raises(ValidationError):
        FinanceMutationRequest.model_validate(
            {
                **request.model_dump(mode="python"),
                "policy_revision_ref": "policy-revision-ref:finance:stale",
            }
        )
    service.gate.policy.can_execute = lambda *_args, **_kwargs: SimpleNamespace(
        status=PolicyDecisionStatus.denied, allowed=False
    )
    with pytest.raises(FinanceAuthorityError, match="POLICY_DENIED"):
        _execute(service, request, now)
    assert _snapshot(service).revision == 2


@pytest.mark.parametrize(
    "posture", ["revoked", "expired", "wrong_scope", "wrong_payload"]
)
def test_current_lease_posture_cannot_be_substituted(kernel, posture):
    service, _crypto, now = kernel
    request = _request(service)
    bound, preview, approvals, lease = _authorize(service, request, now)
    change = {
        "revoked": {"status": "revoked"},
        "expired": {"expires_at": now - timedelta(seconds=1)},
        "wrong_scope": {"scope": "persistent"},
        "wrong_payload": {
            "constraints": {
                **lease.constraints,
                "exact_request_fingerprint_ref": "payload-ref:finance:other",
            }
        },
    }[posture]
    invalid = lease.model_copy(update=change)
    with pytest.raises(FinanceAuthorityError, match="LEASE_DENIED"):
        service.execute(
            bound,
            preview=preview,
            approval_authority=approvals,
            lease_provider=lambda: [invalid],
            clock=lambda: now,
        )
    assert _snapshot(service).revision == 2


@pytest.mark.parametrize(
    "capability",
    [
        "capability-ref:finance/FIN-001/synthetic-book-mutation",
        "capability-ref:finance/FIN-002/synthetic-import-commit",
    ],
)
def test_generic_finance_permits_cannot_authorize_review_mutation(kernel, capability):
    service, _crypto, now = kernel
    bound, preview, approvals, lease = _authorize(service, _request(service), now)
    permit = service.gate.authorize(
        bound,
        preview=preview,
        approval_authority=approvals,
        active_authority_leases=[lease],
        now=now,
    )
    data = permit.model_dump(mode="json", exclude={"permit_ref"})
    data["capability_ref"] = capability
    data["permit_ref"] = stable_finance_ref("finance-mutation-permit-ref", data)
    with pytest.raises(ValidationError, match="REVIEW_PERMIT_SCOPE_INVALID"):
        FinanceMutationPermit.model_validate(data)
    assert _snapshot(service).revision == 2


def test_concurrent_review_writers_commit_one_current_revision(kernel):
    service, crypto, now = kernel
    requests = [
        _request(service, suffix=f"concurrent-{index}", decision=decision)
        for index, decision in enumerate(("confirm", "reject"))
    ]
    start = Barrier(2)

    def commit(request):
        independent = FinanceKernelService(
            FinanceRepository(service.repository.root, crypto_backend=crypto)
        )
        start.wait(timeout=10)
        try:
            return _execute(independent, request, now).phase
        except FinanceRepositoryError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(commit, requests))
    assert sorted(results) == ["FINANCE_STALE_REVISION", "committed"]
    assert _snapshot(service).revision == 3
    assert len(_snapshot(service).review_decisions) == 1


@pytest.mark.parametrize("after_unlink", [False, True])
def test_lost_response_at_pending_unlink_replays_without_another_event(
    kernel, monkeypatch, after_unlink
):
    service, crypto, now = kernel
    request = _request(service)
    repo = service.repository
    unlink = repo._unlink_private_file

    def interrupted(path, *, missing_ok):
        if path == repo.pending_commit_path:
            if after_unlink:
                unlink(path, missing_ok=missing_ok)
            raise InterruptedWrite("FIN003_TEST_PENDING_UNLINK")
        return unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(repo, "_unlink_private_file", interrupted)
    with pytest.raises(InterruptedWrite):
        _execute(service, request, now)
    reopened = FinanceKernelService(FinanceRepository(repo.root, crypto_backend=crypto))
    receipt = _execute(reopened, request, now)
    assert receipt.replayed is True
    assert _snapshot(reopened).revision == 3
    assert len(_snapshot(reopened).review_decisions) == 1


def test_review_retry_cannot_recover_a_different_pending_intent(kernel, monkeypatch):
    service, crypto, now = kernel
    first = _request(service, suffix="pending-first")
    other = _request(service, suffix="pending-other", decision="reject")
    repo = service.repository
    recover = repo._recover_pending_commit

    def interrupted(**kwargs):
        if repo.pending_commit_path.exists():
            raise InterruptedWrite("FIN003_TEST_PENDING_SCOPE")
        return recover(**kwargs)

    monkeypatch.setattr(repo, "_recover_pending_commit", interrupted)
    with pytest.raises(InterruptedWrite):
        _execute(service, first, now)
    before = {p.name: p.read_bytes() for p in repo.root.iterdir() if p.is_file()}
    reopened = FinanceKernelService(FinanceRepository(repo.root, crypto_backend=crypto))
    with pytest.raises(FinanceRepositoryError, match="PENDING_BINDING_INVALID"):
        _execute(reopened, other, now)
    assert {
        p.name: p.read_bytes() for p in repo.root.iterdir() if p.is_file()
    } == before
    assert _execute(reopened, first, now).replayed is True
    assert len(_snapshot(reopened).review_decisions) == 1


def test_saved_decision_survives_real_import_rank_movement_and_exact_undo(kernel):
    service, _crypto, now = kernel
    original_request = _request(service)
    receipt = _execute(service, original_request, now)
    saved = _snapshot(service)
    original_item = build_finance_review_projection(saved).review_items[0]
    imported = preview_synthetic_csv_fixture(
        "fixture-ref:finance/FIN-002:synthetic-csv-duplicate:v1",
        existing_fingerprint_refs=tuple(
            ref
            for record in saved.import_commits
            for ref in record.source_fingerprint_refs
        ),
    )
    request = FinanceMutationRequest(
        operation="import_commit",
        repository_ref=saved.repository_ref,
        fixture_ref=imported.fixture_ref,
        import_preview_ref=imported.preview_ref,
        import_profile_ref=imported.profile_ref,
        import_fixture_manifest_ref=imported.import_fixture_manifest_ref,
        import_candidate_refs=tuple(item.candidate_ref for item in imported.candidates),
        import_source_fingerprint_refs=tuple(
            item.source_fingerprint_ref for item in imported.observations
        ),
        expected_revision=saved.revision,
        request_ref="request-ref:finance:fin003-later-import",
        idempotency_ref="idempotency-ref:finance:fin003-later-import",
        safe_disable_ref=FIN002_IMPORT_SAFE_DISABLE_REF,
    )
    _execute(service, request, now)
    later = _snapshot(service)
    projection = build_finance_review_projection(later)
    index = next(
        i
        for i, item in enumerate(projection.review_items)
        if item.lineage_ref == original_item.lineage_ref
    )
    moved = projection.review_items[index]
    assert moved.rank > original_item.rank
    assert moved.review_item_ref != original_item.review_item_ref
    assert moved.state == "confirmed"
    assert moved.effective_decision_ref == original_item.effective_decision_ref
    assert _execute(service, original_request, now).receipt_ref == receipt.receipt_ref
    undo = _request(
        service,
        decision=None,
        compensates_event_ref=moved.effective_decision_ref,
        suffix="moved-undo",
        item=index,
    )
    _execute(service, undo, now)
    restored = _snapshot(service)
    assert (
        build_finance_review_projection(restored).review_items[index].state
        == "needs_review"
    )
    assert restored.journal_entries == later.journal_entries
    assert restored.account_balances() == later.account_balances()


@pytest.mark.parametrize("operation", ["review_decision", "review_undo"])
@pytest.mark.parametrize("boundary", ["pending", "ciphertext", "metadata", "committed"])
@pytest.mark.parametrize(
    "entrypoint",
    [
        "create",
        "import_commit",
        "direct_import",
        "backup",
        "restore",
        "delete",
        "legacy_load",
    ],
)
def test_pending_review_cannot_be_recovered_by_another_entrypoint(
    kernel, monkeypatch, operation, boundary, entrypoint
):
    service, crypto, now = kernel
    repo = service.repository
    if operation == "review_undo":
        _execute(service, _request(service), now)
        request = _request(
            service,
            decision=None,
            compensates_event_ref=_snapshot(service).review_decisions[0].event_ref,
            suffix="pending-undo",
        )
    else:
        request = _request(service)
    source = _snapshot(service)
    write = repo._atomic_write

    def interrupted(path, payload):
        write(path, payload)
        if (
            (boundary == "pending" and path == repo.pending_commit_path)
            or (boundary == "ciphertext" and path == repo.encrypted_path)
            or (boundary == "metadata" and path == repo.metadata_path)
            or (
                boundary == "committed"
                and path == repo.receipts_path
                and json.loads(payload.splitlines()[-1])["phase"] == "committed"
                and json.loads(payload.splitlines()[-1])["request_ref"]
                == request.request_ref
            )
        ):
            raise InterruptedWrite("FIN003_TEST_PENDING_REVIEW")

    with monkeypatch.context() as patch:
        patch.setattr(FinanceRepository, "_atomic_write", staticmethod(interrupted))
        with pytest.raises(InterruptedWrite):
            _execute(service, request, now)
    assert repo.pending_commit_path.exists()
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in repo.root.iterdir()
        if p.is_file()
    }
    reopened = FinanceKernelService(FinanceRepository(repo.root, crypto_backend=crypto))
    imported = preview_synthetic_csv_fixture(
        "fixture-ref:finance/FIN-002:synthetic-csv-duplicate:v1",
        existing_fingerprint_refs=tuple(
            ref
            for record in source.import_commits
            for ref in record.source_fingerprint_refs
        ),
    )
    fields = {}
    target = repo.root.parent / "other-operation-backup.enc"
    if entrypoint in {"import_commit", "direct_import"}:
        fields = {
            "fixture_ref": imported.fixture_ref,
            "import_preview_ref": imported.preview_ref,
            "import_profile_ref": imported.profile_ref,
            "import_fixture_manifest_ref": imported.import_fixture_manifest_ref,
            "import_candidate_refs": tuple(
                item.candidate_ref for item in imported.candidates
            ),
            "import_source_fingerprint_refs": tuple(
                item.source_fingerprint_ref for item in imported.observations
            ),
            "safe_disable_ref": FIN002_IMPORT_SAFE_DISABLE_REF,
        }
    elif entrypoint == "create":
        fields = {"fixture_ref": "fixture-ref:finance/FIN-001:balanced-local-book:v1"}
    elif entrypoint in {"backup", "restore"}:
        fields = {"target_ref": finance_target_ref(target)}
    # The old review permission has expired, while this unrelated operation
    # receives fresh, valid authority. It must not advance the pending review.
    later = now + timedelta(hours=1)
    error = None
    try:
        if entrypoint == "legacy_load":
            reopened.repository.load_snapshot(
                request_ref="request-ref:finance:other-load"
            )
        else:
            other = FinanceMutationRequest(
                operation="import_commit"
                if entrypoint == "direct_import"
                else entrypoint,
                repository_ref=request.repository_ref,
                expected_revision=0 if entrypoint == "create" else source.revision,
                request_ref="request-ref:finance:other-entrypoint",
                idempotency_ref="idempotency-ref:finance:other-entrypoint",
                **fields,
            )
            if entrypoint == "direct_import":
                bound, preview, approvals, lease = _authorize(reopened, other, later)

                def revalidate():
                    return reopened.gate.authorize(
                        bound,
                        preview=preview,
                        approval_authority=approvals,
                        active_authority_leases=[lease],
                        now=later,
                    )

                reopened.repository.commit_import(
                    imported, permit=revalidate(), revalidate=revalidate
                )
            else:
                _execute(
                    reopened,
                    other,
                    later,
                    **(
                        {"backup_path": target}
                        if entrypoint in {"backup", "restore"}
                        else {}
                    ),
                )
    except FinanceRepositoryError as exc:
        error = str(exc)
    assert {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in repo.root.iterdir()
        if p.is_file()
    } == before
    assert error == "FIN003_REVIEW_PENDING_AUTHORITY_REQUIRED"
    assert not target.exists()
    receipt = _execute(reopened, request, later)
    assert receipt.replayed is True
    assert not repo.pending_commit_path.exists()
    assert len(_snapshot(reopened).review_decisions) == (
        2 if operation == "review_undo" else 1
    )
    assert _snapshot(reopened).journal_entries == source.journal_entries


@pytest.mark.parametrize("operation", ["review_decision", "review_undo"])
def test_manifest_accepts_an_executable_review_request(kernel, operation):
    service, _crypto, now = kernel
    if operation == "review_undo":
        _execute(service, _request(service), now)
        request = _request(
            service,
            decision=None,
            compensates_event_ref=_snapshot(service).review_decisions[0].event_ref,
            suffix="manifest-undo",
        )
    else:
        request = _request(service)
    manifest = build_finance_review_decision_capability_manifest()
    validator = Draft202012Validator(manifest.input_schema)
    payload = request.model_dump(
        mode="json",
        include={
            "operation",
            "repository_ref",
            "review_preview",
            "expected_revision",
            "request_ref",
            "idempotency_ref",
            "safe_disable_ref",
        },
    )
    validator.validate(payload)
    parsed = FinanceMutationRequest.model_validate(payload)
    receipt = _execute(service, parsed, now)
    assert receipt.phase == "committed"
    output_validator = Draft202012Validator(manifest.output_schema)
    output = receipt.model_dump(mode="json")
    output_validator.validate(output)
    assert not output_validator.is_valid({**output, "operation": "import_commit"})
    assert not output_validator.is_valid({**output, "phase": "prepared"})
    assert not output_validator.is_valid({**output, "unreviewed_output": True})
    for missing in ("expected_revision", "safe_disable_ref"):
        assert not validator.is_valid(
            {k: v for k, v in payload.items() if k != missing}
        )
    for revision in (None, -1, 0, 1, True, "2", 2.5):
        assert not validator.is_valid({**payload, "expected_revision": revision})
    for safe_disable in (None, "safe-disable-ref:finance/FIN-001:synthetic-mutations"):
        assert not validator.is_valid({**payload, "safe_disable_ref": safe_disable})


@pytest.mark.parametrize("revoked", ["approval", "lease", "safe_disable"])
def test_pending_review_revalidates_current_authority_at_shared_recovery(
    kernel, monkeypatch, revoked
):
    service, crypto, now = kernel
    request = _request(service)
    repo = service.repository
    write = repo._atomic_write

    def interrupted(path, payload):
        write(path, payload)
        if path == repo.pending_commit_path:
            raise InterruptedWrite("FIN003_TEST_PENDING_AUTHORITY")

    with monkeypatch.context() as patch:
        patch.setattr(FinanceRepository, "_atomic_write", staticmethod(interrupted))
        with pytest.raises(InterruptedWrite):
            _execute(service, request, now)
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in repo.root.iterdir()
        if p.is_file()
    }
    reopened = FinanceKernelService(FinanceRepository(repo.root, crypto_backend=crypto))
    bound, preview, approvals, lease = _authorize(reopened, request, now)
    calls = 0

    def current_leases():
        nonlocal calls
        calls += 1
        if calls == 3:
            if revoked == "approval":
                approvals.revoke(
                    preview.expected_approval_ref, "Synthetic recovery revocation."
                )
            if revoked == "lease":
                return []
        return [lease]

    with pytest.raises(FinanceAuthorityError):
        reopened.execute(
            bound,
            preview=preview,
            approval_authority=approvals,
            lease_provider=current_leases,
            clock=lambda: now,
            safe_disable_engaged=lambda: revoked == "safe_disable" and calls == 3,
        )
    assert calls == 3
    assert {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in repo.root.iterdir()
        if p.is_file()
    } == before
    assert _execute(reopened, request, now).replayed is True
    assert len(_snapshot(reopened).review_decisions) == 1


@pytest.mark.parametrize(
    "canonical",
    [
        "docs/kanban/current_board.md",
        "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
    ],
)
def test_canonical_persistence_status_is_verified(monkeypatch, canonical):
    from scripts import verify_fin003_review_decision_persistence as verifier

    assert verifier.verify() == []
    read = Path.read_text

    def stale_status(path, *args, **kwargs):
        if path == verifier.ROOT / canonical:
            return "FIN-003 preview only; no persistence."
        return read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", stale_status)
    assert (
        f"FIN003 canonical persistence status missing: {canonical}" in verifier.verify()
    )


@pytest.mark.parametrize("operation", ["review_decision", "review_undo"])
@pytest.mark.parametrize("permission_state", ["expired", "revoked"])
@pytest.mark.parametrize("boundary", ["pending", "ciphertext", "metadata", "committed"])
def test_fresh_recovery_retains_the_current_authority_audit(
    kernel, monkeypatch, operation, permission_state, boundary
):
    service, crypto, now = kernel
    repo = service.repository
    if operation == "review_undo":
        _execute(service, _request(service), now)
        request = _request(
            service,
            decision=None,
            compensates_event_ref=_snapshot(service).review_decisions[0].event_ref,
            suffix="reauthorized-undo",
        )
    else:
        request = _request(service, suffix="reauthorized-decision")
    source = _snapshot(service)
    bound, preview, approvals, lease = _authorize(service, request, now)
    write = repo._atomic_write

    def interrupted(path, payload):
        write(path, payload)
        if (
            (boundary == "pending" and path == repo.pending_commit_path)
            or (boundary == "ciphertext" and path == repo.encrypted_path)
            or (boundary == "metadata" and path == repo.metadata_path)
            or (
                boundary == "committed"
                and path == repo.receipts_path
                and json.loads(payload.splitlines()[-1])["phase"] == "committed"
                and json.loads(payload.splitlines()[-1])["request_ref"]
                == request.request_ref
            )
        ):
            raise InterruptedWrite("FIN003_TEST_RECOVERY_AUDIT")

    with monkeypatch.context() as patch:
        patch.setattr(FinanceRepository, "_atomic_write", staticmethod(interrupted))
        with pytest.raises(InterruptedWrite):
            service.execute(
                bound,
                preview=preview,
                approval_authority=approvals,
                lease_provider=lambda: [lease],
                clock=lambda: now,
            )
    original = FinanceMutationReceipt.model_validate(
        json.loads(repo.pending_commit_path.read_bytes().split(b"\n", 1)[0])["receipt"]
    )
    later = now + (
        timedelta(hours=1) if permission_state == "expired" else timedelta(seconds=1)
    )
    if permission_state == "revoked":
        approvals.revoke(preview.expected_approval_ref, "Synthetic recovery test.")
    with pytest.raises(FinanceAuthorityError):
        service.execute(
            bound,
            preview=preview,
            approval_authority=approvals,
            lease_provider=lambda: [lease],
            clock=lambda: later,
        )

    reopened = FinanceKernelService(FinanceRepository(repo.root, crypto_backend=crypto))
    fresh, fresh_preview, fresh_approvals, fresh_lease = _authorize(
        reopened, request, later
    )
    fresh_permit = reopened.gate.authorize(
        fresh,
        preview=fresh_preview,
        approval_authority=fresh_approvals,
        active_authority_leases=[fresh_lease],
        now=later,
    )
    receipt = reopened.execute(
        fresh,
        preview=fresh_preview,
        approval_authority=fresh_approvals,
        lease_provider=lambda: [fresh_lease],
        clock=lambda: later,
    )
    logged = [
        FinanceMutationReceipt.model_validate_json(line)
        for line in repo.receipts_path.read_bytes().splitlines()
    ]
    recovery = [
        item
        for item in logged
        if item.phase == "recovered" and original.receipt_ref in item.proof_refs
    ]
    assert len(recovery) == 1
    audit = recovery[0]
    assert audit.permit_ref == fresh_permit.permit_ref != original.permit_ref
    assert (
        audit.authority_lease_ref
        == fresh_lease.lease_ref
        != original.authority_lease_ref
    )
    assert audit.authority_decision_ref == fresh_permit.authority_decision_ref
    assert audit.approval_decision_ref == fresh_permit.approval_decision_ref
    assert audit.after_snapshot_ref == original.after_snapshot_ref
    preparations = [
        item
        for item in logged
        if item.phase == "prepared"
        and item.permit_ref == fresh_permit.permit_ref
        and original.receipt_ref in item.proof_refs
    ]
    assert len(preparations) == 1
    assert preparations[0].receipt_ref in audit.proof_refs
    assert original in logged
    assert receipt == original.model_copy(update={"replayed": True})
    assert len(_snapshot(reopened).review_decisions) == (
        2 if operation == "review_undo" else 1
    )
    assert _snapshot(reopened).journal_entries == source.journal_entries
    before_replay = repo.receipts_path.read_bytes()
    assert (
        reopened.execute(
            fresh,
            preview=fresh_preview,
            approval_authority=fresh_approvals,
            lease_provider=lambda: [fresh_lease],
            clock=lambda: later,
        ).replayed
        is True
    )
    assert repo.receipts_path.read_bytes() == before_replay


def _pending_review_for_audit(kernel, monkeypatch, operation):
    service, crypto, now = kernel
    repo = service.repository
    if operation == "review_undo":
        _execute(service, _request(service), now)
        request = _request(
            service,
            decision=None,
            compensates_event_ref=_snapshot(service).review_decisions[0].event_ref,
            suffix="audit-undo",
        )
    else:
        request = _request(service, suffix="audit-decision")
    recover = repo._recover_pending_commit

    def interrupted(**kwargs):
        if repo.pending_commit_path.exists():
            raise InterruptedWrite("FIN003_TEST_AUDIT_PENDING")
        return recover(**kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(repo, "_recover_pending_commit", interrupted)
        with pytest.raises(InterruptedWrite):
            _execute(service, request, now)
    original = FinanceMutationReceipt.model_validate(
        json.loads(repo.pending_commit_path.read_bytes().split(b"\n", 1)[0])["receipt"]
    )
    reopened = FinanceKernelService(FinanceRepository(repo.root, crypto_backend=crypto))
    later = now + timedelta(hours=1)
    fresh, preview, approvals, lease = _authorize(reopened, request, later)
    return (
        reopened,
        fresh,
        original,
        {
            "preview": preview,
            "approval_authority": approvals,
            "lease_provider": lambda: [lease],
            "clock": lambda: later,
        },
    )


@pytest.mark.parametrize("operation", ["review_decision", "review_undo"])
@pytest.mark.parametrize("phase", ["prepared", "recovered"])
@pytest.mark.parametrize("after_write", [False, True])
def test_recovery_audit_write_faults_preserve_exact_retry(
    kernel, monkeypatch, operation, phase, after_write
):
    service, request, original, options = _pending_review_for_audit(
        kernel, monkeypatch, operation
    )
    repo = service.repository
    prior = repo.receipts_path.read_bytes()
    generation_before = repo.encrypted_path.read_bytes()
    write = repo._atomic_write

    def interrupted(path, payload):
        is_target = (
            path == repo.receipts_path
            and json.loads(payload.splitlines()[-1])["phase"] == phase
            and original.receipt_ref
            in json.loads(payload.splitlines()[-1])["proof_refs"]
        )
        if is_target and not after_write:
            raise InterruptedWrite("FIN003_TEST_RECOVERY_AUDIT_WRITE")
        write(path, payload)
        if is_target and after_write:
            raise InterruptedWrite("FIN003_TEST_RECOVERY_AUDIT_WRITE")

    with monkeypatch.context() as patch:
        patch.setattr(FinanceRepository, "_atomic_write", staticmethod(interrupted))
        with pytest.raises(InterruptedWrite):
            service.execute(request, **options)
    assert repo.pending_commit_path.exists()
    assert repo.receipts_path.read_bytes().startswith(prior)
    if phase == "prepared":
        assert repo.encrypted_path.read_bytes() == generation_before
    assert service.execute(request, **options).replayed is True
    logged = [
        FinanceMutationReceipt.model_validate_json(line)
        for line in repo.receipts_path.read_bytes().splitlines()
    ]
    audit = [item for item in logged if original.receipt_ref in item.proof_refs]
    assert [item.phase for item in audit] == ["prepared", "recovered"]
    assert (
        len([item for item in logged if item.receipt_ref == original.receipt_ref]) == 1
    )
    assert audit[0].receipt_ref in audit[1].proof_refs
    assert len(_snapshot(service).review_decisions) == (
        2 if operation == "review_undo" else 1
    )
    completed = repo.receipts_path.read_bytes()
    assert service.execute(request, **options).replayed is True
    assert repo.receipts_path.read_bytes() == completed


@pytest.mark.parametrize("operation", ["review_decision", "review_undo"])
@pytest.mark.parametrize("available_for", ["original_only", "prepared_and_original"])
def test_recovery_reserves_completion_capacity_before_any_write(
    kernel, monkeypatch, operation, available_for
):
    from ultimate_ai_agent.core.finance import repository as repository_module

    service, request, original, options = _pending_review_for_audit(
        kernel, monkeypatch, operation
    )
    repo = service.repository
    permit = service.gate.authorize(
        request,
        preview=options["preview"],
        approval_authority=options["approval_authority"],
        active_authority_leases=options["lease_provider"](),
        now=options["clock"](),
    )
    preparation = repo._receipt(
        permit=permit,
        phase="prepared",
        before_revision=original.before_revision,
        after_revision=original.after_revision,
        before_snapshot_ref=original.before_snapshot_ref,
        after_snapshot_ref=None,
        proof_refs=(original.receipt_ref, *original.proof_refs),
    )
    additional = (
        (original,) if available_for == "original_only" else (original, preparation)
    )
    limited = len(repo.receipts_path.read_bytes()) + sum(
        len(
            (
                json.dumps(
                    item.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
                )
                + "\n"
            ).encode("utf-8")
        )
        for item in additional
    )
    before = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in repo.root.iterdir()
        if path.is_file()
    }
    with monkeypatch.context() as patch:
        patch.setattr(repository_module, "FINANCE_RECEIPT_LOG_MAX_BYTES", limited)
        with pytest.raises(FinanceRepositoryError, match="RECEIPT_CAPACITY_EXHAUSTED"):
            service.execute(request, **options)
    assert {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in repo.root.iterdir()
        if path.is_file()
    } == before
    assert service.execute(request, **options).replayed is True


@pytest.mark.parametrize("operation", ["review_decision", "review_undo"])
@pytest.mark.parametrize("revoked", ["approval", "lease", "safe_disable"])
def test_recovery_preparation_does_not_authorize_later_promotion(
    kernel, monkeypatch, operation, revoked
):
    service, request, original, options = _pending_review_for_audit(
        kernel, monkeypatch, operation
    )
    repo = service.repository
    ciphertext_before = repo.encrypted_path.read_bytes()
    metadata_before = repo.metadata_path.read_bytes()
    original_provider = options["lease_provider"]
    calls = 0

    def current_leases():
        nonlocal calls
        calls += 1
        if calls == 4:
            if revoked == "approval":
                options["approval_authority"].revoke(
                    options["preview"].expected_approval_ref,
                    "Synthetic post-preparation revocation.",
                )
            if revoked == "lease":
                return []
        return original_provider()

    with pytest.raises(FinanceAuthorityError):
        service.execute(
            request,
            **{**options, "lease_provider": current_leases},
            safe_disable_engaged=lambda: revoked == "safe_disable" and calls == 4,
        )
    assert calls == 4
    assert repo.pending_commit_path.exists()
    assert repo.encrypted_path.read_bytes() == ciphertext_before
    assert repo.metadata_path.read_bytes() == metadata_before
    logged = [
        FinanceMutationReceipt.model_validate_json(line)
        for line in repo.receipts_path.read_bytes().splitlines()
    ]
    audit = [item for item in logged if original.receipt_ref in item.proof_refs]
    assert [item.phase for item in audit] == ["prepared"]
    assert original not in logged
    assert (
        _execute(service, request, options["clock"]() + timedelta(seconds=1)).replayed
        is True
    )
    assert len(_snapshot(service).review_decisions) == (
        2 if operation == "review_undo" else 1
    )


@pytest.mark.parametrize("operation", ["review_decision", "review_undo"])
@pytest.mark.parametrize("grant_change", ["created_at", "actor"])
def test_regranted_same_ref_and_lease_recovery_has_fresh_grant_audit(
    kernel, monkeypatch, operation, grant_change
):
    from ultimate_ai_agent.core.approvals import authority as approval_module

    service, _crypto, now = kernel
    if operation == "review_undo":
        _execute(service, _request(service), now)
        request = _request(
            service,
            decision=None,
            compensates_event_ref=_snapshot(service).review_decisions[0].event_ref,
            suffix="regrant-undo",
        )
    else:
        request = _request(service, suffix="regrant-decision")
    bound, preview, approvals, lease = _authorize(service, request, now)
    grant = approvals.get_grant(preview.expected_approval_ref)
    assert grant is not None
    options = dict(
        preview=preview,
        approval_authority=approvals,
        lease_provider=lambda: [lease],
        clock=lambda: now,
    )
    repo = service.repository
    recover = repo._recover_pending_commit

    def interrupted(**kwargs):
        if repo.pending_commit_path.exists():
            raise InterruptedWrite("FIN003_TEST_REGRANT_PENDING")
        return recover(**kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(repo, "_recover_pending_commit", interrupted)
        with pytest.raises(InterruptedWrite):
            service.execute(bound, **options)
    original = FinanceMutationReceipt.model_validate(
        json.loads(repo.pending_commit_path.read_bytes().split(b"\n", 1)[0])["receipt"]
    )
    approvals.revoke(preview.expected_approval_ref, "Synthetic same-ref regrant.")
    with pytest.raises(FinanceAuthorityError):
        service.execute(bound, **options)
    with monkeypatch.context() as patch:
        patch.setattr(
            approval_module,
            "utc_now",
            lambda: (
                grant.created_at
                + (
                    timedelta(seconds=1)
                    if grant_change == "created_at"
                    else timedelta(0)
                )
            ),
        )
        approvals.grant(
            preview.approval_request.approval_request_id,
            approved_by_actor_id=(
                grant.approved_by_actor_id
                if grant_change == "created_at"
                else "actor-ref:finance:replacement-test-operator"
            ),
            approval_ref=grant.approval_ref,
            expires_at=grant.expires_at,
        )
    assert service.execute(bound, **options).replayed is True
    logged = [
        FinanceMutationReceipt.model_validate_json(line)
        for line in repo.receipts_path.read_bytes().splitlines()
    ]
    recovered = [
        item
        for item in logged
        if item.phase == "recovered" and original.receipt_ref in item.proof_refs
    ]
    assert len(recovered) == 1
    assert recovered[0].approval_decision_ref != original.approval_decision_ref
    assert recovered[0].permit_ref != original.permit_ref
    assert recovered[0].authority_lease_ref == original.authority_lease_ref
    assert original in logged
    saved = repo.receipts_path.read_bytes()
    assert service.execute(bound, **options).replayed is True
    assert repo.receipts_path.read_bytes() == saved


def _review_backup(service, now, suffix):
    path = service.repository.root.parent / f"{suffix}-backup.enc"
    snapshot = _snapshot(service)
    request = FinanceMutationRequest(
        operation="backup",
        repository_ref=snapshot.repository_ref,
        expected_revision=snapshot.revision,
        target_ref=finance_target_ref(path),
        request_ref=f"request-ref:finance:{suffix}-backup",
        idempotency_ref=f"idempotency-ref:finance:{suffix}-backup",
    )
    _execute(service, request, now, backup_path=path)
    return path


def _review_restore(service, path, now, suffix):
    snapshot = _snapshot(service)
    request = FinanceMutationRequest(
        operation="restore",
        repository_ref=snapshot.repository_ref,
        expected_revision=snapshot.revision,
        target_ref=finance_target_ref(path),
        request_ref=f"request-ref:finance:{suffix}-restore",
        idempotency_ref=f"idempotency-ref:finance:{suffix}-restore",
    )
    return _execute(service, request, now, backup_path=path)


@pytest.mark.parametrize("history_change", ["decision", "undo", "fully_undone"])
def test_generic_restore_cannot_discard_review_history(kernel, history_change):
    service, _crypto, now = kernel
    if history_change == "undo":
        _execute(service, _request(service), now)
    backup = _review_backup(service, now, "history-before")
    if history_change != "undo":
        _execute(service, _request(service), now)
    if history_change != "decision":
        _execute(
            service,
            _request(
                service,
                decision=None,
                compensates_event_ref=_snapshot(service).review_decisions[-1].event_ref,
                suffix="history-undo",
            ),
            now,
        )
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in service.repository.root.iterdir()
        if p.is_file()
    }
    with pytest.raises(
        FinanceRepositoryError, match="FIN003_RESTORE_REVIEW_HISTORY_MISMATCH"
    ):
        _review_restore(service, backup, now, "older-history")
    assert {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in service.repository.root.iterdir()
        if p.is_file()
    } == before
    current = _snapshot(service)
    matching = _review_backup(service, now, "history-current")
    assert (
        _review_restore(service, matching, now, "matching-history").phase == "committed"
    )
    assert _snapshot(service).review_decisions == current.review_decisions
    assert _snapshot(service).journal_entries == current.journal_entries


@pytest.mark.parametrize("boundary", ["pending", "ciphertext", "metadata", "committed"])
@pytest.mark.parametrize("entrypoint", ["legacy_load", "delete"])
@pytest.mark.parametrize("history_change", ["decision", "undo"])
def test_legacy_pending_restore_cannot_drop_committed_review_audit(
    kernel, monkeypatch, boundary, entrypoint, history_change
):
    service, crypto, now = kernel
    if history_change == "undo":
        _execute(service, _request(service), now)
    backup = _review_backup(service, now, "legacy-before")
    if history_change == "decision":
        _execute(service, _request(service), now)
    else:
        _execute(
            service,
            _request(
                service,
                decision=None,
                compensates_event_ref=_snapshot(service).review_decisions[-1].event_ref,
                suffix="legacy-undo",
            ),
            now,
        )
    source = _snapshot(service)
    repo = service.repository
    write = repo._atomic_write
    append = repo._append_receipt_if_missing

    def interrupted_write(path, payload):
        write(path, payload)
        if (
            (boundary == "pending" and path == repo.pending_commit_path)
            or (boundary == "ciphertext" and path == repo.encrypted_path)
            or (boundary == "metadata" and path == repo.metadata_path)
        ):
            raise InterruptedWrite("FIN003_TEST_OLD_RESTORE_WRITE")

    def interrupted_receipt(receipt):
        append(receipt)
        if boundary == "committed" and receipt.operation == "restore":
            raise InterruptedWrite("FIN003_TEST_OLD_RESTORE_RECEIPT")

    with monkeypatch.context() as patch:
        # Build a legacy pending generation through the real old restore path;
        # only the new history guard is absent, including partial promotion.
        patch.setattr(repo, "_require_restore_review_history", lambda *a, **k: None)
        patch.setattr(
            FinanceRepository, "_atomic_write", staticmethod(interrupted_write)
        )
        patch.setattr(repo, "_append_receipt_if_missing", interrupted_receipt)
        with pytest.raises(InterruptedWrite):
            _review_restore(service, backup, now, "legacy-history")
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in repo.root.iterdir()
        if p.is_file()
    }
    reopened = FinanceKernelService(FinanceRepository(repo.root, crypto_backend=crypto))
    with pytest.raises(
        FinanceRepositoryError, match="FIN003_RESTORE_REVIEW_HISTORY_MISMATCH"
    ):
        if entrypoint == "legacy_load":
            reopened.repository.load_snapshot(
                request_ref="request-ref:finance:legacy-recover"
            )
        else:
            _execute(
                reopened,
                FinanceMutationRequest(
                    operation="delete",
                    repository_ref=source.repository_ref,
                    expected_revision=source.revision,
                    request_ref="request-ref:finance:legacy-delete",
                    idempotency_ref="idempotency-ref:finance:legacy-delete",
                ),
                now,
            )
    assert {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in repo.root.iterdir()
        if p.is_file()
    } == before
    assert repo.pending_commit_path.exists()


@pytest.mark.parametrize("boundary", ["pending", "ciphertext", "metadata", "committed"])
def test_matching_history_restore_recovers_at_every_promotion_boundary(
    kernel, monkeypatch, boundary
):
    service, crypto, now = kernel
    _execute(service, _request(service), now)
    source = _snapshot(service)
    backup = _review_backup(service, now, "matching-fault")
    repo = service.repository
    write = repo._atomic_write
    append = repo._append_receipt_if_missing

    def interrupted_write(path, payload):
        write(path, payload)
        if (
            (boundary == "pending" and path == repo.pending_commit_path)
            or (boundary == "ciphertext" and path == repo.encrypted_path)
            or (boundary == "metadata" and path == repo.metadata_path)
        ):
            raise InterruptedWrite("FIN003_TEST_MATCHING_RESTORE_WRITE")

    def interrupted_receipt(receipt):
        append(receipt)
        if boundary == "committed" and receipt.operation == "restore":
            raise InterruptedWrite("FIN003_TEST_MATCHING_RESTORE_RECEIPT")

    with monkeypatch.context() as patch:
        patch.setattr(
            FinanceRepository, "_atomic_write", staticmethod(interrupted_write)
        )
        patch.setattr(repo, "_append_receipt_if_missing", interrupted_receipt)
        with pytest.raises(InterruptedWrite):
            _review_restore(service, backup, now, "matching-fault")
    reopened = FinanceRepository(repo.root, crypto_backend=crypto)
    recovered = reopened.load_snapshot(
        request_ref="request-ref:finance:matching-recover"
    )
    assert recovered.review_decisions == source.review_decisions
    assert recovered.journal_entries == source.journal_entries
    assert not reopened.pending_commit_path.exists()


def test_restore_requires_exact_committed_history_not_just_matching_posture(kernel):
    from ultimate_ai_agent.core.finance.models import FinanceSnapshot
    from ultimate_ai_agent.core.finance.review_decision_commit import (
        build_finance_review_decision_record,
    )

    service, _crypto, now = kernel
    before = _snapshot(service)
    preview = _request(service).review_preview
    record = build_finance_review_decision_record(before, preview)
    unlogged = FinanceSnapshot.model_validate(
        {
            **before.model_dump(mode="python"),
            "revision": 3,
            "generation": 3,
            "review_decisions": (record,),
        }
    )
    with pytest.raises(
        FinanceRepositoryError, match="FIN003_RESTORE_REVIEW_HISTORY_MISMATCH"
    ):
        service.repository._require_restore_review_history(unlogged)
    _execute(service, _request(service), now)
    current = _snapshot(service)
    service.repository._require_restore_review_history(current)
    with pytest.raises(
        FinanceRepositoryError, match="FIN003_RESTORE_REVIEW_HISTORY_MISMATCH"
    ):
        service.repository._require_restore_review_history(before)
