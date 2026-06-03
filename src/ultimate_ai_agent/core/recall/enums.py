from enum import Enum


class RecallSourceKind(str, Enum):
    canonical_document = "canonical_document"
    evidence_manifest = "evidence_manifest"
    receipt = "receipt"
    event_ledger = "event_ledger"
    user_reviewed_source = "user_reviewed_source"
    source_linked_memory = "source_linked_memory"
    reviewed_memory = "reviewed_memory"
    unreviewed_memory = "unreviewed_memory"
    model_output = "model_output"
    runtime_output = "runtime_output"
    openwebui_output = "openwebui_output"
    unknown = "unknown"


class RecallCandidateStatus(str, Enum):
    active = "active"
    stale = "stale"
    conflicted = "conflicted"
    revoked = "revoked"
    deleted = "deleted"
    superseded = "superseded"
    blocked = "blocked"


class RecallDecisionStatus(str, Enum):
    allowed = "allowed"
    excluded = "excluded"
    blocked = "blocked"
    empty = "empty"


class ContextPackBuildStatus(str, Enum):
    built = "built"
    empty = "empty"
    blocked = "blocked"
