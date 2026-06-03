from enum import Enum


class MemoryType(str, Enum):
    episodic = "episodic"
    semantic = "semantic"
    preference = "preference"
    project = "project"
    procedural = "procedural"
    relationship = "relationship"
    artifact_summary = "artifact_summary"
    decision = "decision"
    constraint = "constraint"
    open_question = "open_question"
    workflow_playbook = "workflow_playbook"


class MemoryScope(str, Enum):
    user = "user"
    project = "project"
    workspace = "workspace"
    organization = "organization"
    global_scope = "global_scope"


class MemoryStatus(str, Enum):
    active = "active"
    superseded = "superseded"
    corrected = "corrected"
    deleted = "deleted"
    revoked = "revoked"
    quarantined = "quarantined"
    pending_review = "pending_review"


class MemoryAuthority(str, Enum):
    user_provided = "user_provided"
    canonical_file_derived = "canonical_file_derived"
    event_ledger_derived = "event_ledger_derived"
    tool_result_derived = "tool_result_derived"
    assistant_inferred = "assistant_inferred"
    imported = "imported"


class MemorySensitivity(str, Enum):
    public = "public"
    user_private = "user_private"
    project_private = "project_private"
    sensitive_personal = "sensitive_personal"
    credential_secret = "credential_secret"
    regulated = "regulated"
    third_party_confidential = "third_party_confidential"
    system_internal = "system_internal"
    tcb_protected = "tcb_protected"


class MemoryWriteDisposition(str, Enum):
    retain = "retain"
    reject = "reject"
    quarantine = "quarantine"
    needs_review = "needs_review"
    supersede_existing = "supersede_existing"


class MemoryRetrievalMode(str, Enum):
    keyword = "keyword"
    metadata = "metadata"
    hybrid_contract_only = "hybrid_contract_only"
    source_ref = "source_ref"
    recent = "recent"


class MemoryProviderKind(str, Enum):
    local_in_memory = "local_in_memory"
    local_sqlite = "local_sqlite"
    planned_external = "planned_external"
    blocked_cloud = "blocked_cloud"
    unknown = "unknown"


class MemoryProviderStatus(str, Enum):
    contract_only = "contract_only"
    local_dev_only = "local_dev_only"
    validation_only = "validation_only"
    planned_disabled = "planned_disabled"
    blocked = "blocked"
    not_implemented = "not_implemented"


class MemoryLayer(str, Enum):
    source = "source"
    record = "record"
    recall = "recall"
    review = "review"
    evidence = "evidence"
    governance = "governance"
    blocked = "blocked"


class MemoryRecordKind(str, Enum):
    workspace_note = "workspace_note"
    session_summary = "session_summary"
    structured_fact = "structured_fact"
    project_fact = "project_fact"
    user_preference = "user_preference"
    decision_record = "decision_record"
    procedural_note = "procedural_note"
    evidence_link = "evidence_link"
    correction = "correction"
    interaction_summary = "interaction_summary"
    task_context = "task_context"
    identity_note = "identity_note"
    blocked = "blocked"


class MemoryReviewState(str, Enum):
    draft = "draft"
    user_review_required = "user_review_required"
    user_reviewed = "user_reviewed"
    stale = "stale"
    conflicted = "conflicted"
    superseded = "superseded"
    revoked = "revoked"
    deleted = "deleted"
    blocked = "blocked"


class MemoryAuthorityLevel(str, Enum):
    recall_only = "recall_only"
    non_authoritative = "non_authoritative"
    source_linked = "source_linked"
    evidence_supported = "evidence_supported"
    blocked_authority = "blocked_authority"


class MemorySourcePriority(str, Enum):
    canonical_source = "canonical_source"
    evidence_manifest = "evidence_manifest"
    receipt = "receipt"
    event_ledger = "event_ledger"
    user_reviewed_source = "user_reviewed_source"
    source_linked_memory = "source_linked_memory"
    unreviewed_memory = "unreviewed_memory"
    blocked = "blocked"


class MemoryWriteDecisionStatus(str, Enum):
    allowed_for_local_store = "allowed_for_local_store"
    denied = "denied"
    blocked = "blocked"
    requires_user_review = "requires_user_review"
    requires_evidence = "requires_evidence"
    not_implemented = "not_implemented"


class MemoryDataClassification(str, Enum):
    public = "public"
    internal = "internal"
    personal = "personal"
    sensitive = "sensitive"
    regulated = "regulated"
    forbidden = "forbidden"


class MemoryRetentionState(str, Enum):
    active = "active"
    expired = "expired"
    deletion_requested = "deletion_requested"
    deleted = "deleted"
    export_only = "export_only"
    archived = "archived"
    blocked = "blocked"


class MemoryConflictState(str, Enum):
    none = "none"
    possible_conflict = "possible_conflict"
    confirmed_conflict = "confirmed_conflict"
    stale = "stale"
    superseded = "superseded"


class MemoryDecayState(str, Enum):
    none = "none"
    active = "active"
    decay_candidate = "decay_candidate"
    archive_candidate = "archive_candidate"
    archived = "archived"
    blocked = "blocked"


class MemoryRecallEligibility(str, Enum):
    ineligible = "ineligible"
    eligible_metadata_only = "eligible_metadata_only"
    context_pack_candidate = "context_pack_candidate"
    blocked = "blocked"
