from enum import Enum


class FoundationGateCategory(str, Enum):
    versioning = "versioning"
    tests = "tests"
    contracts = "contracts"
    security = "security"
    consent = "consent"
    tool_broker = "tool_broker"
    event_ledger = "event_ledger"
    memory = "memory"
    files = "files"
    truth = "truth"
    kernel = "kernel"
    rollback = "rollback"
    observability = "observability"
    blocked_modules = "blocked_modules"
    documentation = "documentation"


class FoundationGateStatus(str, Enum):
    passed = "passed"
    failed = "failed"
    warning = "warning"
    skipped = "skipped"
    blocked = "blocked"
