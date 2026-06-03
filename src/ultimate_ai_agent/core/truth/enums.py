from enum import Enum


class TruthSourceType(str, Enum):
    canonical_file = "canonical_file"
    approved_document = "approved_document"
    api = "api"
    database = "database"
    provider_result = "provider_result"
    event_ledger = "event_ledger"
    world_state = "world_state"
    memory = "memory"
    file = "file"
    user_instruction = "user_instruction"
    external_source = "external_source"
    model_output = "model_output"


class TruthAuthorityLevel(str, Enum):
    authoritative = "authoritative"
    high = "high"
    medium = "medium"
    low = "low"
    untrusted = "untrusted"
    not_authority = "not_authority"


class GroundingMode(str, Enum):
    none = "none"
    sources_preferred = "sources_preferred"
    sources_required = "sources_required"
    canonical_required = "canonical_required"
    api_or_database_required = "api_or_database_required"
    human_review_required = "human_review_required"


class ClaimVerificationStatus(str, Enum):
    supported = "supported"
    unsupported = "unsupported"
    contradicted = "contradicted"
    stale = "stale"
    insufficient_evidence = "insufficient_evidence"
    requires_human_review = "requires_human_review"


class SourceFreshnessStatus(str, Enum):
    current = "current"
    stale = "stale"
    expired = "expired"
    unknown = "unknown"
    not_applicable = "not_applicable"


class SourceConflictSeverity(str, Enum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TruthTaskClass(str, Enum):
    creative = "creative"
    general_answer = "general_answer"
    factual_answer = "factual_answer"
    research = "research"
    policy = "policy"
    legal = "legal"
    medical = "medical"
    financial = "financial"
    security = "security"
    live_status = "live_status"
    weather = "weather"
    news = "news"
    metrics = "metrics"
    code_status = "code_status"
    project_truth = "project_truth"


class TruthSourceKind(str, Enum):
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


class TruthSourcePriority(str, Enum):
    canonical = "canonical"
    evidence = "evidence"
    receipt = "receipt"
    event = "event"
    user_reviewed = "user_reviewed"
    source_linked_memory = "source_linked_memory"
    reviewed_memory = "reviewed_memory"
    unreviewed_memory = "unreviewed_memory"
    model_output_blocked = "model_output_blocked"
    blocked = "blocked"


class TruthSourceStatus(str, Enum):
    active = "active"
    stale = "stale"
    conflicted = "conflicted"
    revoked = "revoked"
    deleted = "deleted"
    superseded = "superseded"
    blocked = "blocked"


class EvidenceStrength(str, Enum):
    none = "none"
    ref_only = "ref_only"
    source_linked = "source_linked"
    evidence_supported = "evidence_supported"
    receipt_supported = "receipt_supported"
    event_supported = "event_supported"
    user_reviewed_supported = "user_reviewed_supported"
    conflicted = "conflicted"
    stale = "stale"
    revoked = "revoked"
    blocked = "blocked"


class ClaimStatus(str, Enum):
    unverified = "unverified"
    source_linked = "source_linked"
    evidence_supported = "evidence_supported"
    verified_by_primary_source = "verified_by_primary_source"
    conflicted = "conflicted"
    stale = "stale"
    revoked = "revoked"
    blocked = "blocked"
    rejected = "rejected"


class VerificationDecisionStatus(str, Enum):
    allowed = "allowed"
    denied = "denied"
    blocked = "blocked"
    requires_evidence = "requires_evidence"
    requires_user_review = "requires_user_review"
    conflicted = "conflicted"
    stale = "stale"
    revoked = "revoked"
    not_implemented = "not_implemented"


class ClaimRiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    forbidden = "forbidden"


class SourceTrustBoundary(str, Enum):
    primary = "primary"
    governed = "governed"
    user_reviewed = "user_reviewed"
    recall_only = "recall_only"
    blocked = "blocked"


class SourceStaleness(str, Enum):
    current = "current"
    stale = "stale"
    expired = "expired"
    unknown = "unknown"


class SourceRevocation(str, Enum):
    active = "active"
    revoked = "revoked"
    deleted = "deleted"
    superseded = "superseded"
