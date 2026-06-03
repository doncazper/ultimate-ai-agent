from ultimate_ai_agent.core.recall.enums import RecallSourceKind


RECALL_SOURCE_PRIORITY: dict[RecallSourceKind, int] = {
    RecallSourceKind.canonical_document: 0,
    RecallSourceKind.evidence_manifest: 1,
    RecallSourceKind.receipt: 2,
    RecallSourceKind.event_ledger: 3,
    RecallSourceKind.user_reviewed_source: 4,
    RecallSourceKind.source_linked_memory: 5,
    RecallSourceKind.reviewed_memory: 6,
    RecallSourceKind.unreviewed_memory: 7,
    RecallSourceKind.model_output: 90,
    RecallSourceKind.runtime_output: 91,
    RecallSourceKind.openwebui_output: 92,
    RecallSourceKind.unknown: 99,
}

RECOGNIZED_RECALL_SOURCE_REF_PREFIXES: dict[str, RecallSourceKind] = {
    "canonical": RecallSourceKind.canonical_document,
    "canonical_document": RecallSourceKind.canonical_document,
    "evidence": RecallSourceKind.evidence_manifest,
    "evidence_manifest": RecallSourceKind.evidence_manifest,
    "receipt": RecallSourceKind.receipt,
    "event": RecallSourceKind.event_ledger,
    "event_ledger": RecallSourceKind.event_ledger,
    "user-review": RecallSourceKind.user_reviewed_source,
    "user_reviewed_source": RecallSourceKind.user_reviewed_source,
    "memory": RecallSourceKind.reviewed_memory,
    "source_linked_memory": RecallSourceKind.source_linked_memory,
    "reviewed_memory": RecallSourceKind.reviewed_memory,
    "unreviewed_memory": RecallSourceKind.unreviewed_memory,
    "model": RecallSourceKind.model_output,
    "model_output": RecallSourceKind.model_output,
    "runtime": RecallSourceKind.runtime_output,
    "runtime_output": RecallSourceKind.runtime_output,
    "openwebui": RecallSourceKind.openwebui_output,
    "openwebui_output": RecallSourceKind.openwebui_output,
}


def recall_source_priority_rank(source_kind: RecallSourceKind) -> int:
    return RECALL_SOURCE_PRIORITY[source_kind]


def infer_recall_source_kind(source_ref: str) -> RecallSourceKind:
    prefix = source_ref.split(":", 1)[0]
    return RECOGNIZED_RECALL_SOURCE_REF_PREFIXES.get(prefix, RecallSourceKind.unknown)
