from enum import Enum


class ControlCenterSurface(str, Enum):
    dashboard = "dashboard"
    approvals = "approvals"
    runtime_readiness = "runtime_readiness"
    foundation_gate = "foundation_gate"
    api_routes = "api_routes"
    events = "events"
    receipts = "receipts"
    model_runtime = "model_runtime"
    remote_workers = "remote_workers"
    private_mesh = "private_mesh"
    mobile_planning = "mobile_planning"
    plugin_governance = "plugin_governance"


class ControlCenterCapabilityStatus(str, Enum):
    available_read_only = "available_read_only"
    preview_only = "preview_only"
    validation_only = "validation_only"
    planned_disabled = "planned_disabled"
    blocked = "blocked"
    not_implemented = "not_implemented"


class ControlCenterActionKind(str, Enum):
    view_status = "view_status"
    view_receipt = "view_receipt"
    view_event_summary = "view_event_summary"
    preview_action = "preview_action"
    preview_approval = "preview_approval"
    preview_runtime = "preview_runtime"
    preview_remote_worker = "preview_remote_worker"
    preview_mobile_capability = "preview_mobile_capability"
    disabled_execute = "disabled_execute"


class ControlCenterRiskLevel(str, Enum):
    safe = "safe"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    forbidden = "forbidden"


class ControlCenterActionDecisionStatus(str, Enum):
    allowed_preview = "allowed_preview"
    denied = "denied"
    blocked = "blocked"
    approval_required = "approval_required"
    not_implemented = "not_implemented"
