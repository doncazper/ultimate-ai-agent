from pathlib import Path
import json

import pytest

from ultimate_ai_agent.core.execution import (
    AppendFirstRunStorage,
    DurableRunRecord,
    DurableRunState,
    DurableRunStorageCorruptionError,
    DurableRunStorageDuplicateError,
    DurableRunStorageEntryKind,
    DurableRunStorageWriteError,
    build_receipt_summary_hash_ref,
    validate_receipt_summary_hash_ref,
)
from ultimate_ai_agent.core.files import FileKind, FileSensitivity, FileWriteProposal, LocalFileManager
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource


def _durable_record(run_id: str = "run:p1-025") -> DurableRunRecord:
    return DurableRunRecord(
        run_id=run_id,
        source_ref="canonical:p1-025-run-storage",
        state=DurableRunState.created,
        safe_summary="Durable run record for append-first storage verification.",
        audit_refs=["audit:p1-025"],
        receipt_refs=["receipt:p1-025"],
        replay_refs=["replay:p1-025"],
        rollback_refs=["rollback:p1-025"],
        evidence_refs=["evidence:p1-025"],
    )


def test_apply_write_uses_proposal_and_changes_file_content(tmp_path: Path):
    manager = LocalFileManager(workspace_root=tmp_path)
    proposal = FileWriteProposal(
        proposal_id="fwp_atomic",
        run_id="run_123",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="user_123",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        target_path="nested/out.txt",
        purpose="atomic write",
        new_content="hello",
        file_kind=FileKind.artifact,
        sensitivity=FileSensitivity.project_private,
        idempotency_key="idem_atomic",
    )

    decision = manager.propose_write(proposal)
    change = manager.apply_write(proposal)

    assert decision.allowed is True
    assert (tmp_path / "nested" / "out.txt").read_text(encoding="utf-8") == "hello"
    assert change.before_hash is None
    assert change.after_hash is not None
    assert change.rollback_ref is not None


def test_apply_write_records_pre_write_diff_summary(tmp_path: Path):
    target = tmp_path / "out.txt"
    secret_like_old_content = "token=should-not-appear\n"
    target.write_text(secret_like_old_content, encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    proposal = FileWriteProposal(
        proposal_id="fwp_atomic_diff",
        run_id="run_123",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="user_123",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        target_path="out.txt",
        purpose="atomic write diff",
        new_content="new\n",
        expected_existing_hash=manager.build_file_ref("out.txt").content_hash,
        file_kind=FileKind.artifact,
        sensitivity=FileSensitivity.project_private,
        idempotency_key="idem_atomic_diff",
    )

    change = manager.apply_write(proposal)

    assert "removed_lines=1" in change.diff_summary
    assert "added_lines=1" in change.diff_summary
    assert "raw_diff_omitted=True" in change.diff_summary
    assert "should-not-appear" not in change.diff_summary
    assert secret_like_old_content not in change.diff_summary
    assert "new" not in change.diff_summary


def test_apply_write_cleans_temp_file_when_replace_fails(tmp_path: Path, monkeypatch):
    target = tmp_path / "out.txt"
    target.write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    proposal = FileWriteProposal(
        proposal_id="fwp_atomic_failure",
        run_id="run_123",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="user_123",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        target_path="out.txt",
        purpose="atomic write failure",
        new_content="new",
        file_kind=FileKind.artifact,
        sensitivity=FileSensitivity.project_private,
        idempotency_key="idem_atomic_failure",
    )

    def fail_replace(_source, _target):
        raise OSError("replace failed")

    monkeypatch.setattr("ultimate_ai_agent.core.files.manager.os.replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        manager.apply_write(proposal)

    assert target.read_text(encoding="utf-8") == "old"
    assert list(tmp_path.glob(".out.txt.*.tmp")) == []


def test_append_first_run_storage_writes_run_and_receipt_atomically(tmp_path: Path):
    store = AppendFirstRunStorage(tmp_path / "runs.jsonl")

    run_entry = store.append_run_record(
        _durable_record(),
        idempotency_key="idempotency:p1-025-run",
        audit_ref="audit:p1-025-run",
        receipt_ref="receipt:p1-025-run",
        rollback_ref="rollback:p1-025-run",
        safe_summary="Append-first durable run record persisted.",
        evidence_refs=["evidence:p1-025-run"],
    )
    receipt_entry = store.append_receipt_summary(
        run_id="run:p1-025",
        receipt_ref="receipt:p1-025-summary",
        idempotency_key="idempotency:p1-025-receipt",
        audit_ref="audit:p1-025-receipt",
        rollback_ref="rollback:p1-025-receipt",
        safe_summary="Append-first durable receipt summary persisted.",
        receipt_summary={
            "status": "persisted",
            "safe_summary": "Receipt summary stores redacted status only.",
            "audit_ref": "audit:p1-025-receipt",
            "rollback_ref": "rollback:p1-025-receipt",
        },
        evidence_refs=["evidence:p1-025-receipt"],
    )

    reloaded = AppendFirstRunStorage(tmp_path / "runs.jsonl")

    assert [entry.kind for entry in reloaded.list_entries("run:p1-025")] == [
        DurableRunStorageEntryKind.run_record,
        DurableRunStorageEntryKind.receipt,
    ]
    assert receipt_entry.previous_entry_hash_ref == run_entry.entry_hash_ref
    assert receipt_entry.receipt_hash_schema_version == "durable_receipt_hash.v1"
    assert receipt_entry.receipt_hash_ref.startswith("sha256:")
    assert receipt_entry.replay_validation_ref.startswith("sha256:")
    assert (
        validate_receipt_summary_hash_ref(receipt_entry.receipt_summary, receipt_entry.receipt_hash_ref)
        is True
    )
    assert reloaded.latest_run_record("run:p1-025").run_id == "run:p1-025"
    assert reloaded.list_receipt_summaries("run:p1-025")[0]["status"] == "persisted"
    assert reloaded.validate_receipt_replay("run:p1-025", "receipt:p1-025-summary").receipt_hash_ref == (
        receipt_entry.receipt_hash_ref
    )


def test_append_first_run_storage_receipt_hash_is_stable_and_redacted():
    summary_a = {
        "status": "persisted",
        "safe_summary": "Receipt summary stores safe refs only.",
        "audit_ref": "audit:p1-029-receipt",
        "receipt_ref": "receipt:p1-029-receipt",
        "rollback_ref": "rollback:p1-029-receipt",
        "mutation_ref": "mutation:p1-029-receipt",
        "after_hash_ref": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    }
    summary_b = {
        "after_hash_ref": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "mutation_ref": "mutation:p1-029-receipt",
        "rollback_ref": "rollback:p1-029-receipt",
        "receipt_ref": "receipt:p1-029-receipt",
        "audit_ref": "audit:p1-029-receipt",
        "safe_summary": "Receipt summary stores safe refs only.",
        "status": "persisted",
    }

    hash_a = build_receipt_summary_hash_ref(summary_a)
    hash_b = build_receipt_summary_hash_ref(summary_b)

    assert hash_a == hash_b
    assert hash_a.startswith("sha256:")
    assert "p1-029-receipt" not in hash_a


def test_append_first_run_storage_validates_receipt_replay(tmp_path: Path):
    store = AppendFirstRunStorage(tmp_path / "runs.jsonl")
    store.append_run_record(
        _durable_record(run_id="run:p1-029"),
        idempotency_key="idempotency:p1-029-run",
        audit_ref="audit:p1-029-run",
        receipt_ref="receipt:p1-029-run",
        rollback_ref="rollback:p1-029-run",
        safe_summary="Replay hash durable run record persists.",
    )
    receipt_entry = store.append_receipt_summary(
        run_id="run:p1-029",
        receipt_ref="receipt:p1-029-replay",
        idempotency_key="idempotency:p1-029-replay",
        audit_ref="audit:p1-029-replay",
        rollback_ref="rollback:p1-029-replay",
        safe_summary="Replay hash durable receipt summary persists.",
        receipt_summary={
            "status": "persisted",
            "safe_summary": "Replay validation uses redacted receipt summary.",
            "audit_ref": "audit:p1-029-replay",
            "receipt_ref": "receipt:p1-029-replay",
            "rollback_ref": "rollback:p1-029-replay",
        },
    )

    reloaded = AppendFirstRunStorage(tmp_path / "runs.jsonl")
    replay_entry = reloaded.validate_receipt_replay("run:p1-029", "receipt:p1-029-replay")

    assert replay_entry.receipt_hash_ref == receipt_entry.receipt_hash_ref
    assert replay_entry.replay_validation_ref == receipt_entry.replay_validation_ref


def test_append_first_run_storage_receipt_hash_detects_summary_mismatch():
    summary = {
        "status": "persisted",
        "safe_summary": "Receipt summary stores safe refs only.",
        "audit_ref": "audit:p1-029-mismatch",
        "receipt_ref": "receipt:p1-029-mismatch",
        "rollback_ref": "rollback:p1-029-mismatch",
    }
    receipt_hash_ref = build_receipt_summary_hash_ref(summary)
    changed_summary = dict(summary)
    changed_summary["status"] = "blocked"

    with pytest.raises(DurableRunStorageCorruptionError, match="DURABLE_RUN_STORAGE_RECEIPT_HASH_MISMATCH"):
        validate_receipt_summary_hash_ref(changed_summary, receipt_hash_ref)


def test_append_first_run_storage_rejects_private_data_shaped_receipt_hash_keys(tmp_path: Path):
    store = AppendFirstRunStorage(tmp_path / "runs.jsonl")

    with pytest.raises(ValueError, match="unsafe durable receipt hash key"):
        store.append_receipt_summary(
            run_id="run:p1-029",
            receipt_ref="receipt:p1-029-private-key",
            idempotency_key="idempotency:p1-029-private-key",
            audit_ref="audit:p1-029-private-key",
            rollback_ref="rollback:p1-029-private-key",
            safe_summary="Private-data-shaped receipt summary key is rejected.",
            receipt_summary={"target_path": "safe-ref:p1-029-private-key"},
        )

    assert not (tmp_path / "runs.jsonl").exists()


def test_append_first_run_storage_preserves_prior_file_when_replace_fails(tmp_path: Path, monkeypatch):
    store = AppendFirstRunStorage(tmp_path / "runs.jsonl")
    store.append_run_record(
        _durable_record(),
        idempotency_key="idempotency:p1-025-original",
        audit_ref="audit:p1-025-original",
        receipt_ref="receipt:p1-025-original",
        rollback_ref="rollback:p1-025-original",
        safe_summary="Original durable run record persisted.",
    )
    before = (tmp_path / "runs.jsonl").read_text(encoding="utf-8")

    def fail_replace(_temp_path, _target_path):
        raise OSError("replace failed")

    monkeypatch.setattr(store, "_replace_temp_file", fail_replace)

    with pytest.raises(DurableRunStorageWriteError, match="DURABLE_RUN_STORAGE_ATOMIC_WRITE_FAILED"):
        store.append_receipt_summary(
            run_id="run:p1-025",
            receipt_ref="receipt:p1-025-failed",
            idempotency_key="idempotency:p1-025-failed",
            audit_ref="audit:p1-025-failed",
            rollback_ref="rollback:p1-025-failed",
            safe_summary="Failed durable receipt summary is not committed.",
            receipt_summary={"status": "blocked", "safe_summary": "Atomic replace failed before commit."},
        )

    assert (tmp_path / "runs.jsonl").read_text(encoding="utf-8") == before
    assert len(store.list_entries("run:p1-025")) == 1
    assert list(tmp_path.glob(".runs.jsonl.*.tmp")) == []


def test_append_first_run_storage_rejects_corrupted_hash_chain(tmp_path: Path):
    store_path = tmp_path / "runs.jsonl"
    store = AppendFirstRunStorage(store_path)
    store.append_run_record(
        _durable_record(),
        idempotency_key="idempotency:p1-025-corruption",
        audit_ref="audit:p1-025-corruption",
        receipt_ref="receipt:p1-025-corruption",
        rollback_ref="rollback:p1-025-corruption",
        safe_summary="Durable run record before corruption verification.",
    )

    line = json.loads(store_path.read_text(encoding="utf-8").splitlines()[0])
    line["safe_summary"] = "Tampered durable run record summary."
    store_path.write_text(json.dumps(line) + "\n", encoding="utf-8")

    with pytest.raises(DurableRunStorageCorruptionError, match="DURABLE_RUN_STORAGE_ENTRY_HASH_MISMATCH"):
        AppendFirstRunStorage(store_path)


def test_append_first_run_storage_blocks_duplicate_idempotency_keys(tmp_path: Path):
    store = AppendFirstRunStorage(tmp_path / "runs.jsonl")
    store.append_run_record(
        _durable_record(),
        idempotency_key="idempotency:p1-025-duplicate",
        audit_ref="audit:p1-025-duplicate",
        receipt_ref="receipt:p1-025-duplicate",
        rollback_ref="rollback:p1-025-duplicate",
        safe_summary="First durable run record persists.",
    )

    with pytest.raises(DurableRunStorageDuplicateError, match="DURABLE_RUN_STORAGE_IDEMPOTENCY_REPLAY_DENIED"):
        store.append_receipt_summary(
            run_id="run:p1-025",
            receipt_ref="receipt:p1-025-duplicate",
            idempotency_key="idempotency:p1-025-duplicate",
            audit_ref="audit:p1-025-duplicate",
            rollback_ref="rollback:p1-025-duplicate",
            safe_summary="Duplicate durable receipt summary is denied.",
            receipt_summary={"status": "blocked", "safe_summary": "Duplicate idempotency key denied."},
        )


def test_append_first_run_storage_recovers_restart_visibility(tmp_path: Path):
    restarted = _durable_record().model_copy(
        update={
            "state": DurableRunState.restart_recovery,
            "generation": 2,
            "restart_refs": ["restart:p1-025"],
        }
    )
    restarted = DurableRunRecord.model_validate(restarted.model_dump())
    store = AppendFirstRunStorage(tmp_path / "runs.jsonl")
    store.append_run_record(
        restarted,
        idempotency_key="idempotency:p1-025-restart",
        audit_ref="audit:p1-025-restart",
        receipt_ref="receipt:p1-025-restart",
        rollback_ref="rollback:p1-025-restart",
        safe_summary="Restart recovery durable run record persisted.",
        evidence_refs=["evidence:p1-025-restart"],
    )

    recovered = AppendFirstRunStorage(tmp_path / "runs.jsonl").latest_run_record("run:p1-025")

    assert recovered.state == DurableRunState.restart_recovery
    assert recovered.restart_refs == ["restart:p1-025"]
    assert recovered.generation == 2


def test_append_first_run_storage_rejects_unredacted_receipt_summary(tmp_path: Path):
    store = AppendFirstRunStorage(tmp_path / "runs.jsonl")

    with pytest.raises(ValueError, match="unsafe durable storage language"):
        store.append_receipt_summary(
            run_id="run:p1-025",
            receipt_ref="receipt:p1-025-unsafe",
            idempotency_key="idempotency:p1-025-unsafe",
            audit_ref="audit:p1-025-unsafe",
            rollback_ref="rollback:p1-025-unsafe",
            safe_summary="Unsafe durable receipt summary is rejected.",
            receipt_summary={"note": "unredacted transcript requested"},
        )

    assert not (tmp_path / "runs.jsonl").exists()
