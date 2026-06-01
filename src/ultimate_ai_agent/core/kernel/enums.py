from enum import Enum


class KernelTaskType(str, Enum):
    create_dev_file = "create_dev_file"
    update_dev_file = "update_dev_file"
    rollback_dev_file = "rollback_dev_file"
    validate_only = "validate_only"


class KernelTaskStatus(str, Enum):
    completed = "completed"
    denied = "denied"
    approval_required = "approval_required"
    blocked = "blocked"
    dry_run = "dry_run"
    failed = "failed"
