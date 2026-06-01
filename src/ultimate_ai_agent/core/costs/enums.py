from enum import Enum


class BudgetScope(str, Enum):
    run = "run"
    user = "user"
    project = "project"
    workspace = "workspace"
    day = "day"
    month = "month"
    provider = "provider"
    model = "model"
    tool = "tool"


class BudgetStatus(str, Enum):
    allowed = "allowed"
    denied = "denied"
    warning = "warning"
    exhausted = "exhausted"
    approval_required = "approval_required"


class ResourceKind(str, Enum):
    tokens = "tokens"
    dollars = "dollars"
    cpu = "cpu"
    memory = "memory"
    vram = "vram"
    disk = "disk"
    network = "network"
    time = "time"
