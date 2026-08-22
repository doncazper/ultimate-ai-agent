from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.knowledge_dump import (
    KnowledgeDumpStore,
    KnowledgeExtractionMethod,
    KnowledgeLifecycleState,
    KnowledgeOcrReviewStatus,
    KnowledgeRightsBasis,
    KnowledgeRightsStatus,
    KnowledgeSourceKind,
)
from ultimate_ai_agent.core.knowledge_dump.store import (
    _hash_ref,
    _legacy_ingest_scope_ref,
)
from scripts.dev import uaa_knowledge


def _actor() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="knowledge_hardening_operator",
        authority_source=AuthoritySource.explicit_user_request,
    )


def _grant(store: KnowledgeDumpStore, prepared, operation: str):  # type: ignore[no-untyped-def]
    actor = _actor()
    authority = LocalApprovalAuthority()
    request_factory = getattr(store, f"approval_request_for_{operation}")
    request = request_factory(
        prepared,
        actor_context=actor,
        run_id=f"run:knowledge-hardening:{operation}",
    )
    authority.create_request(request)
    grant = authority.grant(
        request.approval_request_id,
        approved_by_actor_id=actor.actor_id,
        approved_actions=[request.requested_action],
        approved_resource_refs=request.resource_refs,
        approval_ref=f"approval:knowledge-hardening:{operation}",
    )
    return actor, authority, grant.approval_ref


def _ingest(
    store: KnowledgeDumpStore,
    source: Path,
    *,
    idempotency_key: str,
    extraction_method: KnowledgeExtractionMethod = KnowledgeExtractionMethod.native_text,
    ocr_review_status: KnowledgeOcrReviewStatus = KnowledgeOcrReviewStatus.not_required,
    ocr_review_evidence_ref: str | None = None,
):
    prepared = store.prepare_ingest(
        source,
        title="Synthetic governed source",
        rights_basis=KnowledgeRightsBasis.operator_authored,
        rights_evidence_ref="rights-evidence-ref:q18-operator-authored",
        idempotency_key=idempotency_key,
        source_kind=KnowledgeSourceKind.reference,
        extraction_method=extraction_method,
        ocr_review_status=ocr_review_status,
        ocr_review_evidence_ref=ocr_review_evidence_ref,
    )
    actor, authority, approval_ref = _grant(store, prepared, "ingest")
    receipt = store.ingest(
        prepared,
        approval_authority=authority,
        approval_ref=approval_ref,
        actor_context=actor,
        run_id="run:knowledge-hardening:ingest",
    )
    return prepared, receipt


def _apply_governance(store: KnowledgeDumpStore, prepared):  # type: ignore[no-untyped-def]
    actor, authority, approval_ref = _grant(store, prepared, "governance_update")
    return store.update_governance(
        prepared,
        approval_authority=authority,
        approval_ref=approval_ref,
        actor_context=actor,
        run_id="run:knowledge-hardening:governance_update",
    )


def _apply_metadata(store: KnowledgeDumpStore, prepared):  # type: ignore[no-untyped-def]
    actor, authority, approval_ref = _grant(store, prepared, "metadata_update")
    return store.update_metadata(
        prepared,
        approval_authority=authority,
        approval_ref=approval_ref,
        actor_context=actor,
        run_id="run:knowledge-hardening:metadata_update",
    )


def test_encryption_posture_is_truthful_before_and_after_store_creation(
    tmp_path: Path,
) -> None:
    store = KnowledgeDumpStore(tmp_path / "dump")

    before = store.encryption_posture()
    assert before.owner_only_directory_permissions is False
    assert before.owner_only_database_permissions is False
    assert before.application_level_encryption_enabled is False
    assert before.keychain_bound_key_enabled is False
    assert before.plaintext_source_content_at_rest is True
    assert before.operator_controlled_encrypted_volume_required is True
    assert before.runtime_volume_encryption_verified is False

    source = tmp_path / "source.md"
    source.write_text("Synthetic local permission posture.", encoding="utf-8")
    _ingest(store, source, idempotency_key="knowledge-q18-posture-001")

    after = store.encryption_posture()
    assert after.owner_only_directory_permissions is True
    assert after.owner_only_database_permissions is True
    assert after.application_level_encryption_enabled is False


def test_pending_ocr_is_not_retrievable_until_exact_review(
    tmp_path: Path,
) -> None:
    source = tmp_path / "ocr.txt"
    source.write_text("Synthetic OCR review phrase alpha.", encoding="utf-8")
    store = KnowledgeDumpStore(tmp_path / "dump")
    prepared, receipt = _ingest(
        store,
        source,
        idempotency_key="knowledge-q18-ocr-001",
        extraction_method=KnowledgeExtractionMethod.operator_supplied_ocr,
        ocr_review_status=KnowledgeOcrReviewStatus.pending_review,
    )

    assert store.search("review phrase") == []
    with pytest.raises(ValueError, match="KNOWLEDGE_CONTEXT_SELECTION_INELIGIBLE"):
        store.prepare_selected_context([prepared.chunks[0].chunk_ref])

    governance = store.prepare_governance_update(
        receipt.document_ref,
        lifecycle_state=KnowledgeLifecycleState.active,
        rights_status=KnowledgeRightsStatus.current,
        rights_evidence_ref="rights-evidence-ref:q18-operator-authored",
        ocr_review_status=KnowledgeOcrReviewStatus.reviewed,
        ocr_review_evidence_ref="ocr-evidence-ref:q18-reviewed-001",
        idempotency_key="knowledge-q18-governance-ocr-001",
    )
    with pytest.raises(
        ValidationError, match="KNOWLEDGE_GOVERNANCE_UNSCOPED_AUTHORITY_DENIED"
    ):
        governance.plan.model_copy(update={"model_training_enabled": True})
    update = _apply_governance(store, governance)
    assert update.mutation_performed is True

    restarted_store = KnowledgeDumpStore(store.root)
    replay_plan = restarted_store.prepare_governance_update(
        receipt.document_ref,
        lifecycle_state=KnowledgeLifecycleState.active,
        rights_status=KnowledgeRightsStatus.current,
        rights_evidence_ref="rights-evidence-ref:q18-operator-authored",
        ocr_review_status=KnowledgeOcrReviewStatus.reviewed,
        ocr_review_evidence_ref="ocr-evidence-ref:q18-reviewed-001",
        idempotency_key="knowledge-q18-governance-ocr-001",
    )
    assert replay_plan.plan.exact_scope_ref == governance.plan.exact_scope_ref
    replay = _apply_governance(restarted_store, replay_plan)
    assert replay.mutation_performed is False
    with pytest.raises(ValueError, match="KNOWLEDGE_GOVERNANCE_IDEMPOTENCY_CONFLICT"):
        restarted_store.prepare_governance_update(
            receipt.document_ref,
            lifecycle_state=KnowledgeLifecycleState.archived,
            rights_status=KnowledgeRightsStatus.current,
            rights_evidence_ref="rights-evidence-ref:q18-operator-authored",
            ocr_review_status=KnowledgeOcrReviewStatus.reviewed,
            ocr_review_evidence_ref="ocr-evidence-ref:q18-reviewed-001",
            idempotency_key="knowledge-q18-governance-ocr-001",
        )

    pack = store.prepare_selected_context([prepared.chunks[0].chunk_ref])
    assert pack.selection_mode == "operator_selected"
    assert pack.selected_chunk_refs == (prepared.chunks[0].chunk_ref,)
    assert pack.hits[0].citation.chunk_ref == prepared.chunks[0].chunk_ref
    assert pack.uncited_content_included is False
    assert pack.model_training_authorized is False
    with pytest.raises(
        ValidationError, match="KNOWLEDGE_CONTEXT_AUTOMATIC_AUTHORITY_DENIED"
    ):
        pack.model_copy(update={"uncited_content_included": True})


def test_legacy_rows_are_quarantined_until_exact_extraction_classification(
    tmp_path: Path,
) -> None:
    root = tmp_path / "legacy-dump"
    root.mkdir(mode=0o700)
    database_path = root / "knowledge.sqlite3"
    text = "Synthetic legacy OCR provenance phrase."
    source = tmp_path / "legacy-source.txt"
    source.write_text(text, encoding="utf-8")
    store = KnowledgeDumpStore(root)
    prepared = store.prepare_ingest(
        source,
        title="Synthetic legacy source",
        rights_basis=KnowledgeRightsBasis.operator_authored,
        rights_evidence_ref="rights-evidence-ref:legacy-import",
        idempotency_key="knowledge-ingest-legacy-001",
    )
    document_ref = _hash_ref("knowledge-document-ref", prepared.plan.source_content_ref)
    chunk_ref = prepared.chunks[0].chunk_ref
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE documents (
                document_ref TEXT PRIMARY KEY,
                source_content_ref TEXT NOT NULL UNIQUE,
                exact_scope_ref TEXT NOT NULL,
                title TEXT NOT NULL,
                source_format TEXT NOT NULL,
                rights_basis TEXT NOT NULL,
                rights_evidence_ref TEXT NOT NULL,
                catalog_source_id TEXT,
                catalog_citation_locator_refs_json TEXT NOT NULL DEFAULT '[]',
                chunk_count INTEGER NOT NULL,
                character_count INTEGER NOT NULL,
                idempotency_key TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                source_kind TEXT NOT NULL DEFAULT 'reference',
                category TEXT NOT NULL DEFAULT 'uncategorized',
                collection TEXT,
                tags_json TEXT NOT NULL DEFAULT '[]'
            );
            CREATE TABLE chunks (
                chunk_ref TEXT PRIMARY KEY,
                document_ref TEXT NOT NULL REFERENCES documents(document_ref)
                    ON DELETE CASCADE,
                ordinal INTEGER NOT NULL,
                locator TEXT NOT NULL,
                text TEXT NOT NULL,
                text_ref TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE chunks_fts USING fts5(
                chunk_ref UNINDEXED, text,
                tokenize='unicode61 remove_diacritics 2'
            );
            """
        )
        connection.execute(
            """INSERT INTO documents VALUES
               (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                document_ref,
                prepared.plan.source_content_ref,
                _legacy_ingest_scope_ref(prepared.plan),
                prepared.plan.title,
                prepared.plan.source_format,
                prepared.plan.rights_basis,
                prepared.plan.rights_evidence_ref,
                None,
                "[]",
                1,
                len(text),
                "knowledge-ingest-legacy-001",
                "2026-08-22T00:00:00+00:00",
                prepared.plan.source_kind,
                prepared.plan.category,
                None,
                "[]",
            ),
        )
        connection.execute(
            "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?)",
            (
                chunk_ref,
                document_ref,
                0,
                prepared.chunks[0].locator,
                text,
                prepared.chunks[0].text_ref,
            ),
        )
        connection.execute("INSERT INTO chunks_fts VALUES (?, ?)", (chunk_ref, text))
    os.chmod(database_path, 0o600)

    legacy = store.list_documents()[0]
    assert legacy.extraction_method == KnowledgeExtractionMethod.legacy_unclassified
    assert legacy.rights_status == KnowledgeRightsStatus.review_required
    assert legacy.ocr_review_status == KnowledgeOcrReviewStatus.pending_review
    assert store.search("provenance phrase") == []
    with pytest.raises(ValueError, match="KNOWLEDGE_CONTEXT_SELECTION_INELIGIBLE"):
        store.prepare_selected_context([chunk_ref])
    actor, authority, approval_ref = _grant(store, prepared, "ingest")
    ingest_replay = store.ingest(
        prepared,
        approval_authority=authority,
        approval_ref=approval_ref,
        actor_context=actor,
        run_id="run:knowledge-hardening:ingest",
    )
    assert ingest_replay.mutation_performed is False
    assert (
        ingest_replay.extraction_method == KnowledgeExtractionMethod.legacy_unclassified
    )
    assert ingest_replay.rights_status == KnowledgeRightsStatus.review_required

    classification = store.prepare_governance_update(
        document_ref,
        lifecycle_state=KnowledgeLifecycleState.active,
        rights_status=KnowledgeRightsStatus.current,
        rights_evidence_ref="rights-evidence-ref:legacy-reviewed",
        extraction_method=KnowledgeExtractionMethod.native_text,
        ocr_review_status=KnowledgeOcrReviewStatus.not_required,
        ocr_review_evidence_ref=None,
        idempotency_key="knowledge-governance-legacy-classification",
    )
    receipt = _apply_governance(store, classification)
    assert receipt.extraction_method == KnowledgeExtractionMethod.native_text
    assert receipt.mutation_performed is True
    assert len(store.search("provenance phrase")) == 1


def test_lifecycle_and_rights_updates_fail_closed_on_stale_revision(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.md"
    source.write_text("Synthetic lifecycle eligibility phrase.", encoding="utf-8")
    store = KnowledgeDumpStore(tmp_path / "dump")
    prepared, receipt = _ingest(
        store, source, idempotency_key="knowledge-q18-lifecycle-001"
    )
    stale_archive = store.prepare_governance_update(
        receipt.document_ref,
        lifecycle_state=KnowledgeLifecycleState.archived,
        rights_status=KnowledgeRightsStatus.current,
        rights_evidence_ref="rights-evidence-ref:q18-operator-authored",
        ocr_review_status=KnowledgeOcrReviewStatus.not_required,
        ocr_review_evidence_ref=None,
        idempotency_key="knowledge-q18-governance-archive-stale",
    )
    rights_review = store.prepare_governance_update(
        receipt.document_ref,
        lifecycle_state=KnowledgeLifecycleState.active,
        rights_status=KnowledgeRightsStatus.review_required,
        rights_evidence_ref="rights-evidence-ref:q18-review-required",
        ocr_review_status=KnowledgeOcrReviewStatus.not_required,
        ocr_review_evidence_ref=None,
        idempotency_key="knowledge-q18-governance-rights-001",
    )
    _apply_governance(store, rights_review)

    assert store.search("eligibility phrase") == []
    with pytest.raises(ValueError, match="KNOWLEDGE_CONTEXT_SELECTION_INELIGIBLE"):
        store.prepare_selected_context([prepared.chunks[0].chunk_ref])
    with pytest.raises(ValueError, match="KNOWLEDGE_GOVERNANCE_STALE_REVISION"):
        _apply_governance(store, stale_archive)


def test_selected_context_binds_order_deduplication_and_budget(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.md"
    source.write_text("A" * 1790 + " boundary " + "B" * 800, encoding="utf-8")
    store = KnowledgeDumpStore(tmp_path / "dump")
    prepared, _ = _ingest(store, source, idempotency_key="knowledge-q18-selection-001")
    assert len(prepared.chunks) >= 2
    refs = [prepared.chunks[1].chunk_ref, prepared.chunks[0].chunk_ref]

    pack = store.prepare_selected_context([*refs, refs[0]], max_characters=5000)
    assert pack.selected_chunk_refs == tuple(refs)
    assert tuple(hit.citation.chunk_ref for hit in pack.hits) == tuple(refs)
    assert pack.used_characters == sum(len(hit.text) for hit in pack.hits)

    with pytest.raises(ValueError, match="KNOWLEDGE_CONTEXT_CHARACTER_BUDGET_EXCEEDED"):
        store.prepare_selected_context(refs, max_characters=10)
    with pytest.raises(ValueError, match="KNOWLEDGE_CONTEXT_SELECTION_OUT_OF_BOUNDS"):
        store.prepare_selected_context(["unsafe-ref"])


def test_exact_removal_deletes_content_preserves_audit_and_blocks_resurrection(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.md"
    source.write_text("Synthetic exact removal phrase.", encoding="utf-8")
    store = KnowledgeDumpStore(tmp_path / "dump")
    _, receipt = _ingest(
        store, source, idempotency_key="knowledge-q18-removal-ingest-001"
    )
    removal = store.prepare_removal(
        receipt.document_ref,
        retention_decision_ref="retention-decision-ref:q18-remove-001",
        backup_disposition_ref="backup-disposition-ref:q18-reviewed-none",
        idempotency_key="knowledge-q18-removal-001",
    )
    with pytest.raises(
        ValidationError, match="KNOWLEDGE_REMOVAL_UNSCOPED_AUTHORITY_DENIED"
    ):
        removal.plan.model_copy(update={"automatic_restore_enabled": True})
    actor, authority, approval_ref = _grant(store, removal, "removal")
    first = store.remove(
        removal,
        approval_authority=authority,
        approval_ref=approval_ref,
        actor_context=actor,
        run_id="run:knowledge-hardening:removal",
    )
    replay = store.remove(
        removal,
        approval_authority=authority,
        approval_ref=approval_ref,
        actor_context=actor,
        run_id="run:knowledge-hardening:removal",
    )

    assert first.mutation_performed is True
    assert replay.mutation_performed is False
    assert first.deleted_chunk_count == 1
    assert store.list_documents() == []
    assert store.search("exact removal") == []
    assert store.inventory().document_count == 0
    with sqlite3.connect(store.database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0] == 0
        tombstone = connection.execute("SELECT * FROM document_removals").fetchone()
        assert tombstone is not None
    assert any(record.operation == "removal" for record in store.list_audit_records())
    serialized = str(first.model_dump(mode="json"))
    assert "Synthetic exact removal phrase" not in serialized
    assert b"Synthetic exact removal phrase" not in store.database_path.read_bytes()

    with pytest.raises(
        ValueError,
        match="KNOWLEDGE_REMOVED_CONTENT_REQUIRES_NEW_SOURCE_REVISION",
    ):
        _ingest(
            store,
            source,
            idempotency_key="knowledge-q18-removal-reingest-002",
        )


def test_removal_retains_metadata_and_governance_idempotency_bindings(
    tmp_path: Path,
) -> None:
    first_source = tmp_path / "first.md"
    second_source = tmp_path / "second.md"
    first_source.write_text("Synthetic first durable binding.", encoding="utf-8")
    second_source.write_text("Synthetic second durable binding.", encoding="utf-8")
    store = KnowledgeDumpStore(tmp_path / "dump")
    _, first = _ingest(
        store, first_source, idempotency_key="knowledge-q18-binding-first"
    )
    _, second = _ingest(
        store, second_source, idempotency_key="knowledge-q18-binding-second"
    )
    metadata_key = "knowledge-q18-binding-metadata"
    governance_key = "knowledge-q18-binding-governance"
    _apply_metadata(
        store,
        store.prepare_metadata_update(
            first.document_ref,
            source_kind=KnowledgeSourceKind.reference,
            category="reviewed",
            collection=None,
            tags=[],
            idempotency_key=metadata_key,
        ),
    )
    _apply_governance(
        store,
        store.prepare_governance_update(
            first.document_ref,
            lifecycle_state=KnowledgeLifecycleState.archived,
            rights_status=KnowledgeRightsStatus.current,
            rights_evidence_ref="rights-evidence-ref:q18-operator-authored",
            ocr_review_status=KnowledgeOcrReviewStatus.not_required,
            ocr_review_evidence_ref=None,
            idempotency_key=governance_key,
        ),
    )
    removal = store.prepare_removal(
        first.document_ref,
        retention_decision_ref="retention-decision-ref:q18-binding-remove",
        backup_disposition_ref="backup-disposition-ref:q18-binding-none",
        idempotency_key="knowledge-q18-binding-removal",
    )
    actor, authority, approval_ref = _grant(store, removal, "removal")
    store.remove(
        removal,
        approval_authority=authority,
        approval_ref=approval_ref,
        actor_context=actor,
        run_id="run:knowledge-hardening:removal",
    )

    with sqlite3.connect(store.database_path) as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM metadata_updates").fetchone()[0]
            == 1
        )
        assert (
            connection.execute("SELECT COUNT(*) FROM governance_updates").fetchone()[0]
            == 1
        )

    reused_metadata = store.prepare_metadata_update(
        second.document_ref,
        source_kind=KnowledgeSourceKind.reference,
        category="different",
        collection=None,
        tags=[],
        idempotency_key=metadata_key,
    )
    with pytest.raises(ValueError, match="KNOWLEDGE_METADATA_IDEMPOTENCY_CONFLICT"):
        _apply_metadata(store, reused_metadata)
    with pytest.raises(ValueError, match="KNOWLEDGE_GOVERNANCE_IDEMPOTENCY_CONFLICT"):
        store.prepare_governance_update(
            second.document_ref,
            lifecycle_state=KnowledgeLifecycleState.archived,
            rights_status=KnowledgeRightsStatus.current,
            rights_evidence_ref="rights-evidence-ref:q18-operator-authored",
            ocr_review_status=KnowledgeOcrReviewStatus.not_required,
            ocr_review_evidence_ref=None,
            idempotency_key=governance_key,
        )


def test_cli_requires_printed_exact_scope_for_removal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source.md"
    source.write_text("Synthetic CLI removal phrase.", encoding="utf-8")
    store_path = tmp_path / "dump"
    store = KnowledgeDumpStore(store_path)
    _, receipt = _ingest(
        store, source, idempotency_key="knowledge-q18-cli-removal-ingest"
    )
    common = [
        "--store",
        str(store_path),
        "remove",
        receipt.document_ref,
        "--retention-decision-ref",
        "retention-decision-ref:q18-cli",
        "--backup-disposition-ref",
        "backup-disposition-ref:q18-cli-none",
        "--idempotency-key",
        "knowledge-q18-cli-removal",
    ]

    with pytest.raises(SystemExit, match="Refusing mutation"):
        uaa_knowledge.main(common)
    plan = json.loads(capsys.readouterr().out)
    assert plan["automatic_restore_enabled"] is False

    assert (
        uaa_knowledge.main([*common, "--approve-exact-scope", plan["exact_scope_ref"]])
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["mutation_performed"] is True
    assert output["source_content_in_receipt"] is False
    assert (
        uaa_knowledge.main([*common, "--approve-exact-scope", plan["exact_scope_ref"]])
        == 0
    )
    replay = json.loads(capsys.readouterr().out)
    assert replay["mutation_performed"] is False
    with pytest.raises(ValueError, match="KNOWLEDGE_REMOVAL_IDEMPOTENCY_CONFLICT"):
        store.prepare_removal(
            receipt.document_ref,
            retention_decision_ref="retention-decision-ref:q18-cli",
            backup_disposition_ref="backup-disposition-ref:q18-different",
            idempotency_key="knowledge-q18-cli-removal",
        )
    assert store.list_documents() == []
