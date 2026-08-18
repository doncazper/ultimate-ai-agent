from dataclasses import replace
from pathlib import Path
import stat
import threading
import zipfile

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.capabilities.enums import RiskLevel as CapabilityRiskLevel
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.knowledge_dump import (
    KnowledgeDumpStore,
    KnowledgeRightsBasis,
    KnowledgeSourceKind,
)
from ultimate_ai_agent.core.knowledge_dump.extractors import MAX_SOURCE_BYTES
from scripts.dev import uaa_knowledge


def _actor() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="knowledge_test_operator",
        authority_source=AuthoritySource.explicit_user_request,
    )


def _prepare(store: KnowledgeDumpStore, source: Path, **updates):  # type: ignore[no-untyped-def]
    values = {
        "title": "Synthetic Clinical Reference",
        "rights_basis": KnowledgeRightsBasis.operator_authored,
        "rights_evidence_ref": "rights-evidence-ref:operator-authored:test",
        "idempotency_key": "knowledge-ingest-test-001",
    }
    values.update(updates)
    return store.prepare_ingest(source, **values)


def _approve(
    store: KnowledgeDumpStore,
    prepared,  # type: ignore[no-untyped-def]
    *,
    approved_by_actor_id: str | None = None,
):  # type: ignore[no-untyped-def]
    actor = _actor()
    authority = LocalApprovalAuthority()
    request = store.approval_request_for_ingest(
        prepared, actor_context=actor, run_id="run:knowledge-dump:test"
    )
    authority.create_request(request)
    grant = authority.grant(
        request.approval_request_id,
        approved_by_actor_id=approved_by_actor_id or actor.actor_id,
        approved_actions=[request.requested_action],
        approved_resource_refs=request.resource_refs,
        approval_ref="approval:knowledge-dump:test",
    )
    return actor, authority, grant.approval_ref


def _approve_metadata(store: KnowledgeDumpStore, prepared):  # type: ignore[no-untyped-def]
    actor = _actor()
    authority = LocalApprovalAuthority()
    request = store.approval_request_for_metadata_update(
        prepared, actor_context=actor, run_id="run:knowledge-metadata:test"
    )
    authority.create_request(request)
    grant = authority.grant(
        request.approval_request_id,
        approved_by_actor_id=actor.actor_id,
        approved_actions=[request.requested_action],
        approved_resource_refs=request.resource_refs,
        approval_ref="approval:knowledge-metadata:test",
    )
    return actor, authority, grant.approval_ref


def test_plan_is_content_free_and_does_not_create_store(tmp_path: Path) -> None:
    source = tmp_path / "reference.md"
    source.write_text(
        "# Cardiovascular\n\nSynthetic atrial rhythm reference.", encoding="utf-8"
    )
    root = tmp_path / "dump"
    prepared = _prepare(KnowledgeDumpStore(root), source)

    assert not root.exists()
    assert prepared.plan.source_path_persistence_enabled is False
    assert prepared.plan.network_access_enabled is False
    assert prepared.plan.model_training_enabled is False
    serialized = str(prepared.plan.model_dump(mode="json"))
    assert str(source) not in serialized
    assert "Synthetic atrial rhythm reference" not in serialized


def test_oversized_source_is_rejected_before_read(tmp_path: Path) -> None:
    source = tmp_path / "oversized.txt"
    source.touch()
    with source.open("r+b") as handle:
        handle.truncate(MAX_SOURCE_BYTES + 1)
    store = KnowledgeDumpStore(tmp_path / "dump")

    with pytest.raises(ValueError, match="KNOWLEDGE_SOURCE_SIZE_OUT_OF_BOUNDS"):
        _prepare(store, source)

    assert not store.database_path.exists()


def test_pdf_parser_remains_blocked_without_dependency_authority(
    tmp_path: Path,
) -> None:
    source = tmp_path / "reference.pdf"
    source.write_bytes(b"%PDF-1.7 synthetic")
    store = KnowledgeDumpStore(tmp_path / "dump")

    with pytest.raises(ValueError, match="KNOWLEDGE_SOURCE_FORMAT_UNSUPPORTED"):
        _prepare(store, source)

    assert not store.database_path.exists()


def test_durable_operator_metadata_rejects_raw_paths_and_unsafe_refs(
    tmp_path: Path,
) -> None:
    source = tmp_path / "reference.md"
    source.write_text("Synthetic safe-ref validation content.", encoding="utf-8")
    store = KnowledgeDumpStore(tmp_path / "dump")

    raw_rights_path = "/" + "Users/operator/license.pdf"
    with pytest.raises(ValueError, match="bounded safe reference"):
        _prepare(store, source, rights_evidence_ref=raw_rights_path)
    with pytest.raises(ValueError, match="bounded safe reference"):
        _prepare(store, source, idempotency_key="unsafe key")
    with pytest.raises(ValueError, match="KNOWLEDGE_IDEMPOTENCY_KEY_SECRET_LIKE"):
        _prepare(store, source, idempotency_key="token:" + "a" * 24)
    with pytest.raises(ValueError, match="must not contain a raw local path"):
        _prepare(
            store,
            source,
            title="Imported from " + "/" + "workspace/private/reference.md",
        )

    assert not store.database_path.exists()


def test_ingest_plan_binds_exact_chunks_and_persisted_metadata(tmp_path: Path) -> None:
    source = tmp_path / "reference.md"
    source.write_text("Synthetic exact-scope content for approval.", encoding="utf-8")
    store = KnowledgeDumpStore(tmp_path / "dump")
    prepared = _prepare(store, source)

    altered_chunk = replace(
        prepared.chunks[0], text="Different same-length scoped content."
    )
    altered_chunks = replace(prepared, chunks=(altered_chunk,))
    with pytest.raises(ValueError, match="KNOWLEDGE_INGEST_CHUNK_MANIFEST_MISMATCH"):
        store.approval_request_for_ingest(
            altered_chunks,
            actor_context=_actor(),
            run_id="run:knowledge-dump:tampered-chunk",
        )

    altered_plan = replace(
        prepared,
        plan=prepared.plan.model_copy(update={"title": "Unapproved replacement title"}),
    )
    with pytest.raises(ValueError, match="KNOWLEDGE_INGEST_PLAN_INTEGRITY_MISMATCH"):
        store.approval_request_for_ingest(
            altered_plan,
            actor_context=_actor(),
            run_id="run:knowledge-dump:tampered-plan",
        )

    authority_expanded = replace(
        prepared,
        plan=prepared.plan.model_copy(update={"network_access_enabled": True}),
    )
    with pytest.raises(ValueError, match="KNOWLEDGE_INGEST_PLAN_INTEGRITY_MISMATCH"):
        store.approval_request_for_ingest(
            authority_expanded,
            actor_context=_actor(),
            run_id="run:knowledge-dump:expanded-authority",
        )

    altered_contract = replace(
        prepared,
        plan=prepared.plan.model_copy(update={"contract_ref": "contract-ref:other"}),
    )
    with pytest.raises(ValueError, match="KNOWLEDGE_INGEST_PLAN_INTEGRITY_MISMATCH"):
        store.approval_request_for_ingest(
            altered_contract,
            actor_context=_actor(),
            run_id="run:knowledge-dump:altered-contract",
        )

    assert not store.database_path.exists()


def test_ingest_requires_exact_local_approval(tmp_path: Path) -> None:
    source = tmp_path / "reference.txt"
    source.write_text("A bounded synthetic knowledge statement.", encoding="utf-8")
    store = KnowledgeDumpStore(tmp_path / "dump")
    prepared = _prepare(store, source)

    with pytest.raises(
        PermissionError, match="KNOWLEDGE_INGEST_EXACT_APPROVAL_REQUIRED"
    ):
        store.ingest(
            prepared,
            approval_authority=LocalApprovalAuthority(),
            approval_ref="approval:unknown",
            actor_context=_actor(),
            run_id="run:knowledge-dump:test",
        )

    assert not store.database_path.exists()


def test_ingest_requires_policy_eligibility_before_approval(tmp_path: Path) -> None:
    source = tmp_path / "reference.txt"
    source.write_text("A bounded synthetic policy statement.", encoding="utf-8")
    store = KnowledgeDumpStore(
        tmp_path / "dump",
        policy_engine=PolicyEngine(default_max_risk=CapabilityRiskLevel.low),
    )
    prepared = _prepare(store, source)
    actor, authority, approval_ref = _approve(store, prepared)

    with pytest.raises(PermissionError, match="KNOWLEDGE_MUTATION_POLICY_DENIED"):
        store.ingest(
            prepared,
            approval_authority=authority,
            approval_ref=approval_ref,
            actor_context=actor,
            run_id="run:knowledge-dump:policy-denied",
        )

    assert not store.database_path.exists()


def test_store_enforces_private_directory_and_database_permissions(
    tmp_path: Path,
) -> None:
    source = tmp_path / "reference.txt"
    source.write_text("Synthetic private local content.", encoding="utf-8")
    root = tmp_path / "dump"
    root.mkdir(mode=0o755)
    store = KnowledgeDumpStore(root)
    prepared = _prepare(store, source)
    actor, authority, approval_ref = _approve(store, prepared)

    store.ingest(
        prepared,
        approval_authority=authority,
        approval_ref=approval_ref,
        actor_context=actor,
        run_id="run:knowledge-dump:test",
    )

    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    assert stat.S_IMODE(store.database_path.stat().st_mode) == 0o600


def test_cli_binds_operator_confirmation_to_printed_exact_scope(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "reference.txt"
    source.write_text("A bounded synthetic CLI approval statement.", encoding="utf-8")
    root = tmp_path / "dump"
    store = KnowledgeDumpStore(root)
    prepared = _prepare(store, source)
    shared = [
        "--store",
        str(root),
        "ingest",
        str(source),
        "--title",
        "Synthetic Clinical Reference",
        "--rights-basis",
        "operator_authored",
        "--rights-evidence-ref",
        "rights-evidence-ref:operator-authored:test",
        "--idempotency-key",
        "knowledge-ingest-test-001",
    ]

    with pytest.raises(SystemExit, match="provided exact scope does not match"):
        uaa_knowledge.main(
            [*shared, "--approve-exact-scope", "knowledge-ingest-scope-ref:stale"]
        )
    assert not store.database_path.exists()

    assert (
        uaa_knowledge.main(
            [*shared, "--approve-exact-scope", prepared.plan.exact_scope_ref]
        )
        == 0
    )
    assert len(store.list_documents()) == 1
    capsys.readouterr()
    assert uaa_knowledge.main(["--store", str(root), "audit"]) == 0
    audit_payload = capsys.readouterr().out
    assert '"operation": "ingest"' in audit_payload
    assert _actor().actor_id not in audit_payload


def test_cli_redacts_source_failures(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    missing = tmp_path / "private" / "missing.txt"
    result = uaa_knowledge.main(
        [
            "--store",
            str(tmp_path / "dump"),
            "plan-ingest",
            str(missing),
            "--title",
            "Missing source",
            "--rights-basis",
            "operator_authored",
            "--rights-evidence-ref",
            "rights-evidence-ref:operator-authored:test",
            "--idempotency-key",
            "knowledge-ingest-missing-001",
        ]
    )

    captured = capsys.readouterr()
    assert result == 2
    assert captured.err.strip() == "KNOWLEDGE_SOURCE_FILE_REQUIRED"
    assert str(missing) not in captured.err


def test_ingest_search_and_context_pack_are_cited_and_idempotent(
    tmp_path: Path,
) -> None:
    source = tmp_path / "reference.md"
    source.write_text(
        "Cardiology\n\nAtrial fibrillation is a synthetic example for lexical retrieval.\n\n"
        "Pediatrics\n\nA separate synthetic pediatric passage.",
        encoding="utf-8",
    )
    store = KnowledgeDumpStore(tmp_path / "dump")
    prepared = _prepare(store, source)
    approver_actor_id = "knowledge_test_approver"
    actor, authority, approval_ref = _approve(
        store, prepared, approved_by_actor_id=approver_actor_id
    )

    receipt = store.ingest(
        prepared,
        approval_authority=authority,
        approval_ref=approval_ref,
        actor_context=actor,
        run_id="run:knowledge-dump:test",
    )
    replay = store.ingest(
        prepared,
        approval_authority=authority,
        approval_ref=approval_ref,
        actor_context=actor,
        run_id="run:knowledge-dump:test",
    )

    assert receipt.mutation_performed is True
    assert replay.mutation_performed is False
    assert receipt.source_path_stored is False
    assert receipt.raw_content_in_receipt is False
    assert len(store.list_documents()) == 1
    hits = store.search("atrial fibrillation")
    assert hits
    assert hits[0].citation.locator.startswith("lines:")
    assert hits[0].citation.document_ref == receipt.document_ref
    assert hits[0].source_content_is_untrusted_data is True
    assert hits[0].source_content_is_instruction is False
    context = store.prepare_context("atrial rhythm", max_characters=4000)
    assert context.hits
    assert context.automatic_chat_injection_performed is False
    assert context.model_call_performed is False
    assert context.used_characters <= context.max_characters
    with pytest.raises(ValidationError):
        context.explicit_operator_use_required = False

    audit_records = store.list_audit_records()
    assert len(audit_records) == 1
    assert audit_records[0].operation == "ingest"
    assert audit_records[0].mutation_performed is True
    serialized_audit = str(audit_records[0].model_dump(mode="json"))
    assert audit_records[0].approver_ref.startswith("knowledge-approver-ref:sha256:")
    assert _actor().actor_id not in serialized_audit
    assert approver_actor_id not in serialized_audit


def test_filtered_search_ranks_only_within_allowed_documents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = KnowledgeDumpStore(tmp_path / "dump")
    dominant_source = tmp_path / "dominant.txt"
    dominant_source.write_text(("marker " * 10_000).strip(), encoding="utf-8")
    dominant = _prepare(
        store,
        dominant_source,
        title="Dominant excluded source",
        category="excluded",
        idempotency_key="knowledge-ingest-dominant-001",
    )
    actor1, authority1, approval_ref1 = _approve(store, dominant)
    store.ingest(
        dominant,
        approval_authority=authority1,
        approval_ref=approval_ref1,
        actor_context=actor1,
        run_id="run:knowledge-dump:test",
    )

    allowed_source = tmp_path / "allowed.txt"
    allowed_source.write_text("A single marker in an allowed source.", encoding="utf-8")
    allowed = _prepare(
        store,
        allowed_source,
        title="Allowed source",
        category="allowed",
        idempotency_key="knowledge-ingest-allowed-001",
    )
    actor2, authority2, approval_ref2 = _approve(store, allowed)
    allowed_receipt = store.ingest(
        allowed,
        approval_authority=authority2,
        approval_ref=approval_ref2,
        actor_context=actor2,
        run_id="run:knowledge-dump:test",
    )

    def separate_inventory_connection_is_forbidden(**_kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(
            "filtered search must resolve membership in its query transaction"
        )

    monkeypatch.setattr(
        store, "list_documents", separate_inventory_connection_is_forbidden
    )
    hits = store.search("marker", category="allowed", limit=1)

    assert [hit.citation.document_ref for hit in hits] == [allowed_receipt.document_ref]


def test_unicode_queries_follow_unicode_fts_tokenization(tmp_path: Path) -> None:
    source = tmp_path / "unicode.txt"
    source.write_text("Café reference. Привет reference.", encoding="utf-8")
    store = KnowledgeDumpStore(tmp_path / "dump")
    prepared = _prepare(store, source, idempotency_key="knowledge-ingest-unicode-001")
    actor, authority, approval_ref = _approve(store, prepared)
    store.ingest(
        prepared,
        approval_authority=authority,
        approval_ref=approval_ref,
        actor_context=actor,
        run_id="run:knowledge-dump:test",
    )

    assert store.search("café")
    assert store.search("Привет")


def test_approval_revocation_cannot_cross_durable_start_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "reference.txt"
    source.write_text("Synthetic serialized approval content.", encoding="utf-8")
    store = KnowledgeDumpStore(tmp_path / "dump")
    prepared = _prepare(store, source)
    actor, authority, approval_ref = _approve(store, prepared)
    entered = threading.Event()
    release = threading.Event()
    revoked = threading.Event()
    failures: list[BaseException] = []
    original = store._persist_approved_ingest

    def delayed_persist(*args, **kwargs):  # type: ignore[no-untyped-def]
        entered.set()
        if not release.wait(timeout=2):
            raise TimeoutError("test release signal missing")
        return original(*args, **kwargs)

    monkeypatch.setattr(store, "_persist_approved_ingest", delayed_persist)

    def ingest() -> None:
        try:
            store.ingest(
                prepared,
                approval_authority=authority,
                approval_ref=approval_ref,
                actor_context=actor,
                run_id="run:knowledge-dump:test",
            )
        except BaseException as exc:
            failures.append(exc)

    def revoke() -> None:
        authority.revoke(approval_ref, "test concurrent revocation")
        revoked.set()

    ingest_thread = threading.Thread(target=ingest)
    ingest_thread.start()
    assert entered.wait(timeout=1)
    revoke_thread = threading.Thread(target=revoke)
    revoke_thread.start()
    assert not revoked.wait(timeout=0.1)
    release.set()
    ingest_thread.join(timeout=2)
    revoke_thread.join(timeout=2)

    assert failures == []
    assert revoked.is_set()
    assert len(store.list_documents()) == 1


def test_proprietary_catalog_source_requires_retrieval_rights(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("Synthetic notes, not publisher content.", encoding="utf-8")
    store = KnowledgeDumpStore(tmp_path / "dump")

    with pytest.raises(
        ValueError,
        match="KNOWLEDGE_PROPRIETARY_SOURCE_REQUIRES_LICENSED_RETRIEVAL_RIGHTS",
    ):
        _prepare(store, source, catalog_source_id="apa_dsm_5_tr")

    prepared = _prepare(
        store,
        source,
        catalog_source_id="apa_dsm_5_tr",
        rights_basis=KnowledgeRightsBasis.licensed_for_local_retrieval,
    )
    assert prepared.plan.catalog_source_id == "apa_dsm_5_tr"


def test_epub_html_text_is_extracted_without_storing_archive_path(
    tmp_path: Path,
) -> None:
    source = tmp_path / "book.epub"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
            <container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
              <rootfiles><rootfile full-path="OPS/package.opf" /></rootfiles>
            </container>""",
        )
        archive.writestr(
            "OPS/package.opf",
            """<?xml version="1.0"?>
            <package xmlns="http://www.idpf.org/2007/opf">
              <manifest>
                <item id="chapter" href="chapter1.xhtml"
                      media-type="application/xhtml+xml" />
              </manifest>
              <spine><itemref idref="chapter" /></spine>
            </package>""",
        )
        archive.writestr(
            "OPS/chapter1.xhtml",
            "<html><body><h1>Chapter</h1><p>Renal physiology marker.</p></body></html>",
        )
        archive.writestr(
            "OPS/navigation.xhtml",
            "<html><body><p>Navigation text must not be indexed.</p></body></html>",
        )
    store = KnowledgeDumpStore(tmp_path / "dump")
    prepared = _prepare(store, source, idempotency_key="knowledge-ingest-epub-001")

    assert prepared.plan.planned_chunk_count == 1
    assert prepared.chunks[0].locator.startswith("epub-section:1")
    assert "Navigation text" not in prepared.chunks[0].text
    assert str(source) not in str(prepared.plan.model_dump(mode="json"))


def test_secret_like_source_and_idempotency_conflict_fail_closed(
    tmp_path: Path,
) -> None:
    secret_source = tmp_path / "secret.txt"
    secret_source.write_text("api_" + "key=" + "a" * 16 + "123456", encoding="utf-8")
    store = KnowledgeDumpStore(tmp_path / "dump")
    with pytest.raises(
        ValueError, match="KNOWLEDGE_SOURCE_CONTAINS_SECRET_LIKE_CONTENT"
    ):
        _prepare(store, secret_source)

    first = tmp_path / "first.txt"
    first.write_text("First synthetic content about oncology.", encoding="utf-8")
    prepared = _prepare(store, first)
    actor, authority, approval_ref = _approve(store, prepared)
    store.ingest(
        prepared,
        approval_authority=authority,
        approval_ref=approval_ref,
        actor_context=actor,
        run_id="run:knowledge-dump:test",
    )

    second = tmp_path / "second.txt"
    second.write_text("Different synthetic content about neurology.", encoding="utf-8")
    conflicting = _prepare(store, second)
    actor2, authority2, approval_ref2 = _approve(store, conflicting)
    with pytest.raises(ValueError, match="KNOWLEDGE_INGEST_IDEMPOTENCY_CONFLICT"):
        store.ingest(
            conflicting,
            approval_authority=authority2,
            approval_ref=approval_ref2,
            actor_context=actor2,
            run_id="run:knowledge-dump:test",
        )

    changed_scope = _prepare(store, first, title="Changed unpersisted title")
    actor3, authority3, approval_ref3 = _approve(store, changed_scope)
    with pytest.raises(ValueError, match="KNOWLEDGE_INGEST_IDEMPOTENCY_CONFLICT"):
        store.ingest(
            changed_scope,
            approval_authority=authority3,
            approval_ref=approval_ref3,
            actor_context=actor3,
            run_id="run:knowledge-dump:test",
        )

    duplicate_content = _prepare(
        store,
        first,
        idempotency_key="knowledge-ingest-different-key-001",
    )
    actor4, authority4, approval_ref4 = _approve(store, duplicate_content)
    with pytest.raises(ValueError, match="KNOWLEDGE_INGEST_CONTENT_ALREADY_BOUND"):
        store.ingest(
            duplicate_content,
            approval_authority=authority4,
            approval_ref=approval_ref4,
            actor_context=actor4,
            run_id="run:knowledge-dump:test",
        )


def test_inventory_filters_sorting_and_recategorization(tmp_path: Path) -> None:
    source = tmp_path / "medicine.md"
    source.write_text(
        "Synthetic cardiology source for library organization.", encoding="utf-8"
    )
    store = KnowledgeDumpStore(tmp_path / "dump")
    prepared = _prepare(
        store,
        source,
        source_kind=KnowledgeSourceKind.book,
        category="medicine",
        collection="clinical_library",
        tags=["cardiology", "reference"],
    )
    actor, authority, approval_ref = _approve(store, prepared)
    receipt = store.ingest(
        prepared,
        approval_authority=authority,
        approval_ref=approval_ref,
        actor_context=actor,
        run_id="run:knowledge-dump:test",
    )

    inventory = store.inventory()
    assert inventory.document_count == 1
    assert inventory.by_source_kind == {"book": 1}
    assert inventory.by_category == {"medicine": 1}
    assert inventory.by_collection == {"clinical_library": 1}
    assert inventory.by_tag == {"cardiology": 1, "reference": 1}
    assert len(store.list_documents(category="medicine", tag="cardiology")) == 1
    assert store.list_documents(category="business") == []
    assert store.search("cardiology", category="medicine")
    assert store.search("cardiology", category="business") == []

    update = store.prepare_metadata_update(
        receipt.document_ref,
        source_kind=KnowledgeSourceKind.manual,
        category="clinical_reference",
        collection="medical_core",
        tags=["cardiology", "diagnostics"],
        idempotency_key="knowledge-metadata-update-001",
    )
    actor2, authority2, approval_ref2 = _approve_metadata(store, update)
    updated = store.update_metadata(
        update,
        approval_authority=authority2,
        approval_ref=approval_ref2,
        actor_context=actor2,
        run_id="run:knowledge-metadata:test",
    )
    replay = store.update_metadata(
        update,
        approval_authority=authority2,
        approval_ref=approval_ref2,
        actor_context=actor2,
        run_id="run:knowledge-metadata:test",
    )

    assert updated.mutation_performed is True
    assert replay.mutation_performed is False
    document = store.list_documents(sort_by="category")[0]
    assert document.source_kind == "manual"
    assert document.category == "clinical_reference"
    assert document.collection == "medical_core"
    assert document.tags == ["cardiology", "diagnostics"]
    assert store.inventory().by_category == {"clinical_reference": 1}
    assert store.prepare_context("cardiology", collection="medical_core").hits
    assert store.prepare_context("cardiology", collection="clinical_library").hits == []
    assert [record.operation for record in store.list_audit_records()] == [
        "ingest",
        "metadata_update",
    ]


def test_metadata_update_requires_exact_approval_and_valid_slugs(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Synthetic source for metadata approval.", encoding="utf-8")
    store = KnowledgeDumpStore(tmp_path / "dump")
    prepared = _prepare(store, source)
    actor, authority, approval_ref = _approve(store, prepared)
    receipt = store.ingest(
        prepared,
        approval_authority=authority,
        approval_ref=approval_ref,
        actor_context=actor,
        run_id="run:knowledge-dump:test",
    )

    with pytest.raises(ValueError, match="category must be a bounded slug"):
        store.prepare_metadata_update(
            receipt.document_ref,
            source_kind=KnowledgeSourceKind.notes,
            category="Not A Slug",
            collection=None,
            tags=[],
            idempotency_key="metadata-invalid-slug-001",
        )
    with pytest.raises(ValueError, match="KNOWLEDGE_IDEMPOTENCY_KEY_SECRET_LIKE"):
        store.prepare_metadata_update(
            receipt.document_ref,
            source_kind=KnowledgeSourceKind.notes,
            category="research_notes",
            collection=None,
            tags=["reviewed"],
            idempotency_key="password:" + "a" * 24,
        )

    update = store.prepare_metadata_update(
        receipt.document_ref,
        source_kind=KnowledgeSourceKind.notes,
        category="research_notes",
        collection=None,
        tags=["reviewed"],
        idempotency_key="metadata-approval-required-001",
    )
    with pytest.raises(
        PermissionError, match="KNOWLEDGE_METADATA_EXACT_APPROVAL_REQUIRED"
    ):
        store.update_metadata(
            update,
            approval_authority=LocalApprovalAuthority(),
            approval_ref="approval:unknown",
            actor_context=_actor(),
            run_id="run:knowledge-metadata:test",
        )


def test_metadata_update_rejects_stale_prepared_revision(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Synthetic source for stale metadata checks.", encoding="utf-8")
    store = KnowledgeDumpStore(tmp_path / "dump")
    prepared = _prepare(store, source)
    actor, authority, approval_ref = _approve(store, prepared)
    receipt = store.ingest(
        prepared,
        approval_authority=authority,
        approval_ref=approval_ref,
        actor_context=actor,
        run_id="run:knowledge-dump:test",
    )

    first = store.prepare_metadata_update(
        receipt.document_ref,
        source_kind=KnowledgeSourceKind.notes,
        category="first_revision",
        collection=None,
        tags=["first"],
        idempotency_key="metadata-stale-first-001",
    )
    stale = store.prepare_metadata_update(
        receipt.document_ref,
        source_kind=KnowledgeSourceKind.manual,
        category="stale_revision",
        collection=None,
        tags=["stale"],
        idempotency_key="metadata-stale-second-001",
    )
    actor1, authority1, approval_ref1 = _approve_metadata(store, first)
    actor2, authority2, approval_ref2 = _approve_metadata(store, stale)
    store.update_metadata(
        first,
        approval_authority=authority1,
        approval_ref=approval_ref1,
        actor_context=actor1,
        run_id="run:knowledge-metadata:test",
    )

    with pytest.raises(ValueError, match="KNOWLEDGE_METADATA_STALE_REVISION"):
        store.update_metadata(
            stale,
            approval_authority=authority2,
            approval_ref=approval_ref2,
            actor_context=actor2,
            run_id="run:knowledge-metadata:test",
        )


@pytest.mark.parametrize("limit", [0, -1, 51])
def test_search_limit_is_strictly_bounded(tmp_path: Path, limit: int) -> None:
    store = KnowledgeDumpStore(tmp_path / "dump")
    with pytest.raises(ValueError, match="KNOWLEDGE_QUERY_OUT_OF_BOUNDS"):
        store.search("bounded query", limit=limit)
