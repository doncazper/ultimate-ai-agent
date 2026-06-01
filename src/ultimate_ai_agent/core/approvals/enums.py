from enum import Enum


class ApprovalStatus(str, Enum):
    pending = "pending"
    granted = "granted"
    denied = "denied"
    expired = "expired"
    revoked = "revoked"
    invalid = "invalid"


class ApprovalSubjectType(str, Enum):
    model_route = "model_route"
    model_runtime_request = "model_runtime_request"
    tool_request = "tool_request"
    file_write = "file_write"
    external_action = "external_action"
    credential_access = "credential_access"
    kernel_task = "kernel_task"
    provider_route = "provider_route"
    unknown = "unknown"


class ApprovalRiskLevel(str, Enum):
    safe = "safe"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ApprovalDecisionStatus(str, Enum):
    approved = "approved"
    denied = "denied"
    approval_required = "approval_required"
    invalid = "invalid"
    expired = "expired"
    revoked = "revoked"
    out_of_scope = "out_of_scope"


class ApprovalMode(str, Enum):
    local_dev = "local_dev"
    test = "test"
    human_required = "human_required"
    disabled = "disabled"
