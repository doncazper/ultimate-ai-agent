from ultimate_ai_agent.core.memory.enums import (
    MemoryDataClassification,
    MemoryLayer,
    MemoryProviderKind,
    MemoryRecordKind,
    MemoryRetentionState,
)
from ultimate_ai_agent.core.memory.local_store import LocalMemoryStore
from ultimate_ai_agent.core.memory.manifests import build_default_memory_provider_manifest
from ultimate_ai_agent.core.memory.provider import MemoryDeleteRequest, MemoryExportRequest, MemoryWriteRequest


def _request(request_id="mwr_m24_store", summary="Reviewed local memory summary."):
    return MemoryWriteRequest(
        request_id=request_id,
        provider_ref="local_dev_memory",
        memory_kind=MemoryRecordKind.project_fact,
        memory_layer=MemoryLayer.record,
        provider_kind=MemoryProviderKind.local_in_memory,
        safe_summary=summary,
        source_refs=["source:user-reviewed:m24-store"],
        evidence_refs=["evidence:m24-store"],
        event_refs=["event:m24-store"],
        receipt_refs=["receipt:m24-store"],
        user_reviewed=True,
        data_classification=MemoryDataClassification.internal,
        confidence_score=0.8,
        trust_score=0.7,
        dedup_key="m24-store-reviewed-summary",
        context_pack_eligible=True,
        injection_priority=1,
    )


def test_m24_default_manifest_is_local_only_and_non_operational():
    manifest = build_default_memory_provider_manifest(baseline_version="0.28.0")
    profile = manifest.providers[0]

    assert manifest.baseline_version == "0.28.0"
    assert manifest.local_store_enabled is True
    assert manifest.cloud_providers_enabled is False
    assert manifest.vector_search_enabled is False
    assert manifest.embeddings_enabled is False
    assert manifest.automatic_writes_enabled is False
    assert manifest.recall_injection_enabled is False
    assert manifest.context_pack_injection_enabled is False
    assert manifest.auto_decay_enabled is False
    assert manifest.background_workers_enabled is False
    assert profile.local_only is True
    assert profile.cloud_backed is False
    assert profile.production_ready is False


def test_m24_local_memory_store_put_get_list_delete_export_in_memory():
    store = LocalMemoryStore()

    write = store.put_record(_request())
    assert write.allowed is True
    assert write.memory_id is not None

    record = store.get_record(write.memory_id)
    assert record is not None
    assert record.safe_summary == "Reviewed local memory summary."
    assert record.authority_level == "recall_only"

    listed = store.list_records()
    assert [item.memory_id for item in listed] == [write.memory_id]

    export = store.export_records(
        MemoryExportRequest(
            request_id="mer_m24_store",
            provider_ref="local_dev_memory",
            include_deleted=False,
            include_raw_content=False,
            redacted_only=True,
        )
    )
    assert export.allowed is True
    assert export.records[0]["safe_summary"] == "Reviewed local memory summary."
    assert "content" not in export.records[0]

    deleted = store.mark_deleted(
        MemoryDeleteRequest(
            request_id="mdr_m24_store",
            memory_id=write.memory_id,
            reason="User-requested M24 deletion test.",
            user_requested=True,
        )
    )
    assert deleted.retention_state == MemoryRetentionState.deleted
    assert store.get_record(write.memory_id).retention_state == "deleted"


def test_m24_local_sqlite_store_uses_explicit_tmp_path_and_reopens(tmp_path):
    db_path = tmp_path / "m24_memory.sqlite3"
    first = LocalMemoryStore(storage_path=db_path)
    write = first.put_record(_request(request_id="mwr_m24_sqlite", summary="Reviewed SQLite summary."))
    assert write.allowed is True
    first.close()

    reopened = LocalMemoryStore(storage_path=db_path)
    record = reopened.get_record(write.memory_id)
    assert record is not None
    assert record.safe_summary == "Reviewed SQLite summary."
    assert reopened.manifest.providers[0].provider_kind == "local_sqlite"
    reopened.close()
