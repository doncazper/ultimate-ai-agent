import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.memory.enums import (
    MemoryAuthorityLevel,
    MemoryDataClassification,
    MemoryDecayState,
    MemoryLayer,
    MemoryProviderKind,
    MemoryProviderStatus,
    MemoryRecallEligibility,
    MemoryRecordKind,
    MemoryRetentionState,
    MemoryReviewState,
    MemorySourcePriority,
)
from ultimate_ai_agent.core.memory.records import (
    MemoryLifecycleMetadata,
    MemoryProvenance,
    MemoryRecallMetadata,
    MemoryRecord,
    MemorySourceRef,
)
from ultimate_ai_agent.core.memory.validation import (
    assert_memory_recall_not_authority,
    assert_source_priority_does_not_make_memory_authority,
    validate_memory_record,
)


def test_m24_memory_taxonomy_contains_reviewed_recall_metadata() -> None:
    assert MemoryProviderKind.local_in_memory.value == "local_in_memory"
    assert MemoryProviderKind.local_sqlite.value == "local_sqlite"
    assert MemoryProviderKind.blocked_cloud.value == "blocked_cloud"
    assert MemoryProviderStatus.local_dev_only.value == "local_dev_only"
    assert MemoryLayer.record.value == "record"
    assert MemoryRecordKind.workspace_note.value == "workspace_note"
    assert MemoryRecordKind.session_summary.value == "session_summary"
    assert MemoryRecordKind.structured_fact.value == "structured_fact"
    assert MemoryRecordKind.project_fact.value == "project_fact"
    assert MemoryRecordKind.user_preference.value == "user_preference"
    assert MemoryRecordKind.decision_record.value == "decision_record"
    assert MemoryRecordKind.procedural_note.value == "procedural_note"
    assert MemoryRecordKind.evidence_link.value == "evidence_link"
    assert MemoryRecordKind.correction.value == "correction"
    assert MemoryReviewState.user_reviewed.value == "user_reviewed"
    assert MemoryAuthorityLevel.recall_only.value == "recall_only"
    assert MemorySourcePriority.canonical_source.value == "canonical_source"
    assert MemoryDataClassification.forbidden.value == "forbidden"
    assert MemoryRetentionState.deleted.value == "deleted"
    assert MemoryDecayState.archive_candidate.value == "archive_candidate"
    assert MemoryRecallEligibility.context_pack_candidate.value == "context_pack_candidate"


def test_m24_memory_record_is_recall_only_and_forbids_extra_fields() -> None:
    record = MemoryRecord(
        memory_id="mem_m24_001",
        memory_kind=MemoryRecordKind.structured_fact,
        memory_layer=MemoryLayer.record,
        provider_kind=MemoryProviderKind.local_in_memory,
        review_state=MemoryReviewState.user_reviewed,
        authority_level=MemoryAuthorityLevel.recall_only,
        source_priority=MemorySourcePriority.user_reviewed_source,
        data_classification=MemoryDataClassification.internal,
        safe_summary="User-reviewed project preference: prefer local-only memory tests.",
        provenance=MemoryProvenance(
            provenance_id="prov_m24_001",
            source_refs=[
                MemorySourceRef(
                    source_ref="src_m24_001",
                    source_kind="user_reviewed_note",
                    source_priority=MemorySourcePriority.user_reviewed_source,
                    event_refs=["evt_m24_001"],
                    receipt_refs=["receipt_m24_001"],
                )
            ],
            reviewed_by_ref="user_review_m24_001",
            review_state=MemoryReviewState.user_reviewed,
            source_priority=MemorySourcePriority.user_reviewed_source,
        ),
        source_refs=[
            MemorySourceRef(
                source_ref="src_m24_001",
                source_kind="user_reviewed_note",
                source_priority=MemorySourcePriority.user_reviewed_source,
            )
        ],
        event_refs=["evt_m24_001"],
        receipt_refs=["receipt_m24_001"],
        confidence_score=0.72,
        trust_score=0.64,
        recall_metadata=MemoryRecallMetadata(
            recall_id="recall_m24_001",
            context_pack_eligible=True,
            injection_priority=3,
            retrieval_hint="local-only reviewed memory",
        ),
        lifecycle=MemoryLifecycleMetadata(
            dedup_key="project-pref-local-tests",
            decay_state=MemoryDecayState.decay_candidate,
            archive_candidate=True,
        ),
    )

    assert validate_memory_record(record) is True
    assert assert_memory_recall_not_authority(record) is True
    assert assert_source_priority_does_not_make_memory_authority(record) is True
    assert record.provenance.source_refs[0].source_ref == "src_m24_001"
    assert record.recall_metadata.context_pack_eligible is True
    assert record.lifecycle.archive_candidate is True

    with pytest.raises(ValidationError):
        MemorySourceRef(
            source_ref="src_m24_extra",
            source_kind="user_reviewed_note",
            source_priority=MemorySourcePriority.user_reviewed_source,
            raw_payload="not allowed",
        )


def test_m24_authoritative_or_secret_memory_is_rejected() -> None:
    base = {
        "memory_id": "mem_m24_blocked",
        "memory_kind": MemoryRecordKind.structured_fact,
        "memory_layer": MemoryLayer.record,
        "provider_kind": MemoryProviderKind.local_in_memory,
        "review_state": MemoryReviewState.user_reviewed,
        "source_priority": MemorySourcePriority.user_reviewed_source,
        "data_classification": MemoryDataClassification.internal,
        "safe_summary": "Reviewed recall summary only.",
        "source_refs": [
            MemorySourceRef(
                source_ref="src_m24_blocked",
                source_kind="user_reviewed_note",
                source_priority=MemorySourcePriority.user_reviewed_source,
            )
        ],
    }

    with pytest.raises(ValueError, match="authority"):
        validate_memory_record(MemoryRecord(**base, authority_level=MemoryAuthorityLevel.blocked_authority))

    with pytest.raises(ValueError, match="secret"):
        secret_payload = {
            **base,
            "memory_id": "mem_m24_secret",
            "authority_level": MemoryAuthorityLevel.recall_only,
            "safe_summary": "password=super-secret-value",
        }
        validate_memory_record(
            MemoryRecord(**secret_payload)
        )
