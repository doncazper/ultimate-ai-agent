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
