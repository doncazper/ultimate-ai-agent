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
