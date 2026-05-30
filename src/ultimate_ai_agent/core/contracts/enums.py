from enum import Enum, IntEnum

class AgentMode(str, Enum):
    answer = "answer"
    research = "research"
    create = "create"
    execute = "execute"
    manage = "manage"
    spec = "spec"
    code = "code"
    review = "review"
    monitor = "monitor"
    notify = "notify"
    self_improve = "self_improve"

class TaskClass(str, Enum):
    factual = "factual"
    formatting = "formatting"
    code_generation = "code_generation"
    script_execution = "script_execution"
    file_modification = "file_modification"
    other = "other"

class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class AutonomyLevel(IntEnum):
    L0_answer_only = 0
    L1_draft_only = 1
    L2_recommend = 2
    L3_prepare_and_request_approval = 3
    L4_execute_reversible_trusted_action = 4
    L5_execute_approved_recurring_workflow = 5

class GroundingMode(str, Enum):
    none = "none"
    local_document = "local_document"
    web_search = "web_search"
    hybrid = "hybrid"
    strict = "strict"

class ContractStatus(str, Enum):
    draft = "draft"
    validated = "validated"
    context_bound = "context_bound"
    planned = "planned"
    executing = "executing"
    waiting_for_approval = "waiting_for_approval"
    verifying = "verifying"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    superseded = "superseded"
    archived = "archived"
    needs_clarification = "needs_clarification"
    blocked = "blocked"

class ContractMaturity(str, Enum):
    draft = "draft"
    provisional = "provisional"
    compatibility_protected = "compatibility_protected"
    deprecated = "deprecated"
    removed = "removed"

class DataSourceType(str, Enum):
    current_user_instruction = "current_user_instruction"
    canonical_file = "canonical_file"
    active_spec = "active_spec"
    project_memory = "project_memory"
    retrieved_file_snippet = "retrieved_file_snippet"
    provider_normalized_result = "provider_normalized_result"
    untrusted_external_content = "untrusted_external_content"
