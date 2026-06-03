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
    "user": RecallSourceKind.user_reviewed_source,
    "user-review": RecallSourceKind.user_reviewed_source,
    "user_reviewed": RecallSourceKind.user_reviewed_source,
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

BLOCKED_RECALL_OUTPUT_KINDS = {
    RecallSourceKind.model_output,
    RecallSourceKind.runtime_output,
    RecallSourceKind.openwebui_output,
}

MEMORY_RECALL_SOURCE_KINDS = {
    RecallSourceKind.source_linked_memory,
    RecallSourceKind.reviewed_memory,
    RecallSourceKind.unreviewed_memory,
}


def recall_source_priority_rank(source_kind: RecallSourceKind) -> int:
    return RECALL_SOURCE_PRIORITY[source_kind]


def infer_recall_source_kind(source_ref: str) -> RecallSourceKind:
    prefix = source_ref.split(":", 1)[0]
    return RECOGNIZED_RECALL_SOURCE_REF_PREFIXES.get(prefix, RecallSourceKind.unknown)


def trusted_recall_source_kind(source_ref: str, declared_kind: RecallSourceKind) -> RecallSourceKind:
    inferred_kind = infer_recall_source_kind(source_ref)
    return inferred_kind if inferred_kind != RecallSourceKind.unknown else declared_kind


def recall_source_identity_reason_codes(source_ref: str, declared_kind: RecallSourceKind) -> list[str]:
    inferred_kind = infer_recall_source_kind(source_ref)
    reasons: list[str] = []

    if declared_kind == RecallSourceKind.unknown:
        reasons.append("UNKNOWN_SOURCE_KIND_DENIED")
    if inferred_kind == RecallSourceKind.unknown:
        reasons.append("ARBITRARY_SOURCE_REF_DENIED")
        if declared_kind != RecallSourceKind.unknown:
            reasons.append("SOURCE_REF_KIND_MISMATCH_DENIED")
        return list(dict.fromkeys(reasons))

    if inferred_kind != declared_kind:
        reasons.append("SOURCE_REF_KIND_MISMATCH_DENIED")
        if inferred_kind in MEMORY_RECALL_SOURCE_KINDS and declared_kind not in MEMORY_RECALL_SOURCE_KINDS:
            reasons.append("MEMORY_SOURCE_PRIORITY_UPGRADE_DENIED")
        elif recall_source_priority_rank(declared_kind) < recall_source_priority_rank(inferred_kind):
            reasons.append("SOURCE_PRIORITY_UPGRADE_DENIED")

    if inferred_kind == RecallSourceKind.model_output:
        reasons.append("MODEL_OUTPUT_RECALL_DENIED")
    if inferred_kind == RecallSourceKind.runtime_output:
        reasons.append("RUNTIME_OUTPUT_RECALL_DENIED")
    if inferred_kind == RecallSourceKind.openwebui_output:
        reasons.append("OPENWEBUI_OUTPUT_RECALL_DENIED")

    return list(dict.fromkeys(reasons))
