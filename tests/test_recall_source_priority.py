from ultimate_ai_agent.core.recall import RecallSourceKind, recall_source_priority_rank


def test_recall_source_priority_keeps_memory_below_source_backed_refs():
    assert recall_source_priority_rank(RecallSourceKind.canonical_document) < recall_source_priority_rank(
        RecallSourceKind.evidence_manifest
    )
    assert recall_source_priority_rank(RecallSourceKind.evidence_manifest) < recall_source_priority_rank(
        RecallSourceKind.reviewed_memory
    )
    assert recall_source_priority_rank(RecallSourceKind.receipt) < recall_source_priority_rank(
        RecallSourceKind.source_linked_memory
    )
    assert recall_source_priority_rank(RecallSourceKind.event_ledger) < recall_source_priority_rank(
        RecallSourceKind.source_linked_memory
    )
    assert recall_source_priority_rank(RecallSourceKind.user_reviewed_source) < recall_source_priority_rank(
        RecallSourceKind.reviewed_memory
    )
    assert recall_source_priority_rank(RecallSourceKind.unreviewed_memory) > recall_source_priority_rank(
        RecallSourceKind.reviewed_memory
    )
