from ultimate_ai_agent.core.truth import (
    TruthSourceKind,
    TruthSourcePriority,
    TruthSourceRef,
    TruthSourceStatus,
    rank_truth_sources,
)


def source(ref: str, kind: TruthSourceKind, priority: TruthSourcePriority) -> TruthSourceRef:
    return TruthSourceRef(
        source_ref=ref,
        source_kind=kind,
        source_priority=priority,
        source_status=TruthSourceStatus.active,
        safe_label=ref,
    )


def test_primary_sources_rank_above_memory_and_blocked_output() -> None:
    ranked = rank_truth_sources(
        [
            source("memory:reviewed", TruthSourceKind.reviewed_memory, TruthSourcePriority.reviewed_memory),
            source("event:event-1", TruthSourceKind.event_ledger, TruthSourcePriority.event),
            source("canonical:roadmap", TruthSourceKind.canonical_document, TruthSourcePriority.canonical),
            source("receipt:receipt-1", TruthSourceKind.receipt, TruthSourcePriority.receipt),
            source("model:model-1", TruthSourceKind.model_output, TruthSourcePriority.model_output_blocked),
            source("evidence:evidence-1", TruthSourceKind.evidence_manifest, TruthSourcePriority.evidence),
            source("user-review:review-1", TruthSourceKind.user_reviewed_source, TruthSourcePriority.user_reviewed),
        ]
    )

    assert [item.source_ref for item in ranked] == [
        "canonical:roadmap",
        "evidence:evidence-1",
        "receipt:receipt-1",
        "event:event-1",
        "user-review:review-1",
        "memory:reviewed",
        "model:model-1",
    ]
