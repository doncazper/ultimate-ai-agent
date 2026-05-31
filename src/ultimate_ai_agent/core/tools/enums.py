from enum import Enum

class ToolCategory(str, Enum):
    memory = "memory"
    file = "file"
    code = "code"
    web = "web"
    provider = "provider"
    scanner = "scanner"
    messaging = "messaging"
    notification = "notification"
    external = "external"
    system = "system"
    sdk_adapter = "sdk_adapter"
    mcp = "mcp"
    a2a = "a2a"
    skill = "skill"
    mock = "mock"

class ToolExecutionMode(str, Enum):
    validate_only = "validate_only"
    dry_run = "dry_run"
    mock = "mock"
    local_dev = "local_dev"
    production = "production"

class ToolRiskLevel(str, Enum):
    safe = "safe"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    forbidden = "forbidden"

class ToolPermissionKind(str, Enum):
    filesystem_read = "filesystem_read"
    filesystem_write = "filesystem_write"
    network = "network"
    credential = "credential"
    memory_read = "memory_read"
    memory_write = "memory_write"
    notification = "notification"
    external_send = "external_send"
    external_publish = "external_publish"
    shell = "shell"
    code_execution = "code_execution"
    browser = "browser"
    tcb_access = "tcb_access"

class ToolDecisionStatus(str, Enum):
    allowed = "allowed"
    denied = "denied"
    approval_required = "approval_required"
    dry_run_only = "dry_run_only"
    blocked_by_foundation_gate = "blocked_by_foundation_gate"
