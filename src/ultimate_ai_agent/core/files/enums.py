from enum import Enum


class FileKind(str, Enum):
    canonical = "canonical"
    spec = "spec"
    adr = "adr"
    schema = "schema"
    prompt = "prompt"
    eval = "eval"
    source_code = "source_code"
    test = "test"
    artifact = "artifact"
    upload = "upload"
    research_source = "research_source"
    generated = "generated"
    temp = "temp"


class FileOperation(str, Enum):
    read = "read"
    preview = "preview"
    propose_write = "propose_write"
    apply_write = "apply_write"
    diff = "diff"
    snapshot = "snapshot"
    rollback = "rollback"
    delete_proposal = "delete_proposal"


class FileSensitivity(str, Enum):
    public = "public"
    project_private = "project_private"
    user_private = "user_private"
    sensitive_personal = "sensitive_personal"
    credential_secret = "credential_secret"
    regulated = "regulated"
    system_internal = "system_internal"
    tcb_protected = "tcb_protected"


class FileOperationStatus(str, Enum):
    proposed = "proposed"
    approved = "approved"
    applied = "applied"
    rejected = "rejected"
    blocked = "blocked"
    rolled_back = "rolled_back"
    failed = "failed"
