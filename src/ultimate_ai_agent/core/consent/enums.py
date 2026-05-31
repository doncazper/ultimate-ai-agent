from enum import Enum

class ConsentStatus(str, Enum):
    active = "active"
    expired = "expired"
    revoked = "revoked"
    denied = "denied"
    pending = "pending"

class ConsentScopeType(str, Enum):
    user = "user"
    project = "project"
    workspace = "workspace"
    organization = "organization"
    global_scope = "global"

class ConsentSubjectType(str, Enum):
    user = "user"
    project = "project"
    workspace = "workspace"
    account = "account"
    provider = "provider"
    tool = "tool"
    scanner = "scanner"
    skill = "skill"
    model_route = "model_route"

class PermissionAction(str, Enum):
    any = "any"
    read = "read"
    write = "write"
    create = "create"
    update = "update"
    delete = "delete"
    execute = "execute"
    scan = "scan"
    notify = "notify"
    send = "send"
    publish = "publish"
    spend = "spend"
    approve = "approve"

class PermissionRisk(str, Enum):
    safe = "safe"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    forbidden = "forbidden"

class ApprovalRequirement(str, Enum):
    none = "none"
    per_action = "per_action"
    session = "session"
    standing = "standing"
    human_required = "human_required"
    forbidden = "forbidden"

class DataBoundary(str, Enum):
    public = "public"
    user_private = "user_private"
    project_private = "project_private"
    sensitive_personal = "sensitive_personal"
    credential_secret = "credential_secret"
    regulated = "regulated"
    third_party_confidential = "third_party_confidential"
    system_internal = "system_internal"
    tcb_protected = "tcb_protected"
