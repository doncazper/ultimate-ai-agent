from enum import Enum


class OrchestrationPreviewStatus(str, Enum):
    selected = "selected"
    denied = "denied"
    no_candidate = "no_candidate"
    approval_required = "approval_required"
    budget_exceeded = "budget_exceeded"
    privacy_blocked = "privacy_blocked"
    capability_missing = "capability_missing"
    context_too_small = "context_too_small"
