from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _ref_suffix, _validate_m61_ref, _validate_safe_payload


SCOPED_RECURRING_LOW_RISK_AUTOMATION_DOCS = [
    "docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION.md",
    "docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_POLICY.md",
    "docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_AUTHORITY_BOUNDARY.md",
    "docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_RECEIPT_PLAN.md",
    "docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_NON_GOALS.md",
    "docs/automation/M98_TO_M99_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]


class ScopedRecurringLowRiskAutomationStatus(str, Enum):
    scoped_low_risk_ready_for_review = "scoped_low_risk_ready_for_review"
    denied = "denied"


class _ScopedRecurringLowRiskAutomationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ScopedRecurringLowRiskAutomationCadence(_ScopedRecurringLowRiskAutomationModel):
    cadence_ref: str
    cadence_label: str
    minimum_interval_seconds: int = Field(ge=0)
    max_occurrences: int = Field(ge=0)
    time_window_ref: str
    renewal_expiration_ref: str

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.cadence_ref, "cadence_ref"),
            (self.time_window_ref, "time_window_ref"),
            (self.renewal_expiration_ref, "renewal_expiration_ref"),
        ]:
            _validate_safe_ref(value, field_name)
        _validate_safe_payload(self.cadence_label)
        return self


class ScopedRecurringLowRiskAutomationPolicy(_ScopedRecurringLowRiskAutomationModel):
    policy_ref: str = "scoped-recurring-low-risk-automation-policy:m98"
    enabled_for_review: bool = True
    low_risk_only: bool = True
    read_only_only: bool = True
    strict_cadence_required: bool = True
    renewal_required: bool = True
    expiration_required: bool = True
    stop_conditions_required: bool = True
    audit_required: bool = True
    revocation_required: bool = True
    kill_switch_required: bool = True
    no_secret_access: bool = True
    safe_refs_only_required: bool = True
    runtime_allowed: bool = False
    scheduler_allowed: bool = False
    background_worker_allowed: bool = False
    recurring_execution_allowed: bool = False
    mutating_tasks_allowed: bool = False
    credential_access_allowed: bool = False
    secret_access_allowed: bool = False
    account_actions_allowed: bool = False
    shell_write_allowed: bool = False
    network_write_allowed: bool = False
    browser_write_allowed: bool = False
    silent_background_collection_allowed: bool = False
    memory_write_allowed: bool = False
    context_injection_allowed: bool = False
    export_allowed: bool = False
    backend_route_allowed: bool = False
    control_center_control_allowed: bool = False
    dependency_change_allowed: bool = False
    production_authority_allowed: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_safe_ref(self.policy_ref, "policy_ref")
        return self


class ScopedRecurringLowRiskAutomationRequest(_ScopedRecurringLowRiskAutomationModel):
    request_ref: str
    actor_ref: str
    scope_ref: str
    resource_ref: str
    workflow_ref: str
    action_ref: str
    cadence: ScopedRecurringLowRiskAutomationCadence
    approval_bundle_ref: str
    renewal_ref: str
    expiration_ref: str
    stop_condition_refs: list[str]
    audit_ref: str
    revocation_ref: str
    kill_switch_ref: str
    safe_purpose: str
    approval_ref: str | None = None
    approval_test_ref: str | None = None
    authority_refs: list[str] = Field(default_factory=list)
    renewal_expired: bool = False
    revoked: bool = False
    kill_switch_available: bool = True
    runtime_requested: bool = False
    scheduler_requested: bool = False
    background_worker_requested: bool = False
    recurring_execution_requested: bool = False
    mutating_task_requested: bool = False
    credential_access_requested: bool = False
    account_action_requested: bool = False
    shell_write_requested: bool = False
    network_write_requested: bool = False
    browser_write_requested: bool = False
    silent_background_collection_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    export_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    production_authority_requested: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.actor_ref, "actor_ref"),
            (self.scope_ref, "scope_ref"),
            (self.resource_ref, "resource_ref"),
            (self.workflow_ref, "workflow_ref"),
            (self.action_ref, "action_ref"),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.renewal_ref, "renewal_ref"),
            (self.expiration_ref, "expiration_ref"),
            (self.audit_ref, "audit_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.kill_switch_ref, "kill_switch_ref"),
        ]:
            _validate_safe_ref(value, field_name)
        for ref in self.stop_condition_refs:
            _validate_safe_ref(ref, "stop_condition_ref")
        if self.approval_ref is not None:
            _validate_safe_ref(self.approval_ref, "approval_ref")
        if self.approval_test_ref is not None:
            if self.approval_test_ref.startswith("approval_test"):
                raise ValueError("APPROVAL_TEST_REF_DENIED")
            _validate_safe_ref(self.approval_test_ref, "approval_test_ref")
        for ref in self.authority_refs:
            _validate_safe_ref(ref, "authority_ref")
        _validate_safe_payload(self.safe_purpose)
        return self


class ScopedRecurringLowRiskAutomationReceiptPlan(_ScopedRecurringLowRiskAutomationModel):
    receipt_plan_ref: str
    request_ref: str
    actor_ref: str
    scope_ref: str
    resource_ref: str
    workflow_ref: str
    action_ref: str
    cadence_ref: str
    approval_bundle_ref: str
    renewal_ref: str
    expiration_ref: str
    audit_ref: str
    revocation_ref: str
    kill_switch_ref: str
    store_safe_refs_only: bool = True
    store_raw_payload: bool = False
    runtime_started: bool = False
    scheduler_started: bool = False
    background_worker_started: bool = False
    recurring_execution_performed: bool = False
    mutating_task_performed: bool = False
    secret_access_performed: bool = False
    account_action_performed: bool = False
    shell_write_performed: bool = False
    network_write_performed: bool = False
    browser_write_performed: bool = False
    background_collection_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    export_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "M98 scoped recurring low-risk automation receipt stores safe refs only."
    )

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.request_ref, "request_ref"),
            (self.actor_ref, "actor_ref"),
            (self.scope_ref, "scope_ref"),
            (self.resource_ref, "resource_ref"),
            (self.workflow_ref, "workflow_ref"),
            (self.action_ref, "action_ref"),
            (self.cadence_ref, "cadence_ref"),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.renewal_ref, "renewal_ref"),
            (self.expiration_ref, "expiration_ref"),
            (self.audit_ref, "audit_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.kill_switch_ref, "kill_switch_ref"),
        ]:
            _validate_safe_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class ScopedRecurringLowRiskAutomationDecision(_ScopedRecurringLowRiskAutomationModel):
    decision_ref: str
    request_ref: str
    actor_ref: str
    scope_ref: str
    resource_ref: str
    workflow_ref: str
    action_ref: str
    cadence_ref: str
    approval_bundle_ref: str
    renewal_ref: str
    expiration_ref: str
    stop_condition_refs: list[str]
    audit_ref: str
    revocation_ref: str
    kill_switch_ref: str
    status: ScopedRecurringLowRiskAutomationStatus
    enabled_for_review: bool = True
    low_risk_only: bool = True
    read_only_only: bool = True
    strict_cadence_required: bool = True
    renewal_required: bool = True
    renewal_not_expired: bool = True
    stop_conditions_required: bool = True
    audit_required: bool = True
    revocation_required: bool = True
    kill_switch_required: bool = True
    kill_switch_available: bool = True
    no_secret_access: bool = True
    safe_refs_only: bool = True
    runtime_started: bool = False
    scheduler_enabled: bool = False
    background_worker_enabled: bool = False
    recurring_execution_performed: bool = False
    mutating_task_allowed: bool = False
    secret_access_performed: bool = False
    account_action_performed: bool = False
    shell_write_performed: bool = False
    network_write_performed: bool = False
    browser_write_performed: bool = False
    background_collection_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    export_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    receipt_plan: ScopedRecurringLowRiskAutomationReceiptPlan
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.request_ref, "request_ref"),
            (self.actor_ref, "actor_ref"),
            (self.scope_ref, "scope_ref"),
            (self.resource_ref, "resource_ref"),
            (self.workflow_ref, "workflow_ref"),
            (self.action_ref, "action_ref"),
            (self.cadence_ref, "cadence_ref"),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.renewal_ref, "renewal_ref"),
            (self.expiration_ref, "expiration_ref"),
            (self.audit_ref, "audit_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.kill_switch_ref, "kill_switch_ref"),
        ]:
            _validate_safe_ref(value, field_name)
        for ref in self.stop_condition_refs:
            _validate_safe_ref(ref, "stop_condition_ref")
        if not self.reason_codes:
            raise ValueError("M98_REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def validate_scoped_recurring_low_risk_automation_policy(
    policy: ScopedRecurringLowRiskAutomationPolicy | None = None,
) -> ScopedRecurringLowRiskAutomationPolicy:
    validated = ScopedRecurringLowRiskAutomationPolicy.model_validate(
        (policy or ScopedRecurringLowRiskAutomationPolicy()).model_dump(
            mode="python", round_trip=True
        )
    )
    for field_name, reason in _POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_safe_payload(validated.metadata)
    return validated


def validate_scoped_recurring_low_risk_automation_request(
    request: ScopedRecurringLowRiskAutomationRequest,
    policy: ScopedRecurringLowRiskAutomationPolicy | None = None,
) -> ScopedRecurringLowRiskAutomationRequest:
    validate_scoped_recurring_low_risk_automation_policy(policy)
    payload = request.model_dump(mode="python", round_trip=True)
    for field_name, reason in _REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = ScopedRecurringLowRiskAutomationRequest.model_validate(payload)
    _validate_cadence(validated.cadence)
    if not validated.stop_condition_refs:
        raise ValueError("STOP_CONDITION_REQUIRED")
    if len(set(validated.stop_condition_refs)) != len(validated.stop_condition_refs):
        raise ValueError("STOP_CONDITION_DUPLICATE_DENIED")
    if validated.approval_ref:
        raise ValueError("APPROVAL_REF_NOT_RECURRING_AUTONOMY_AUTHORITY")
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    for ref in validated.authority_refs:
        if ref.startswith("approval_test"):
            raise ValueError("APPROVAL_TEST_REF_DENIED")
        if ref.split(":", 1)[0] in {
            "approval",
            "context-pack",
            "memory",
            "model",
            "openwebui",
            "task-plan",
            "tool-intent",
            "runtime",
        }:
            raise ValueError("AUTHORITY_REF_NOT_RECURRING_AUTONOMY_AUTHORITY")
    if validated.renewal_expired:
        raise ValueError("RENEWAL_EXPIRED_DENIED")
    if validated.revoked:
        raise ValueError("REVOCATION_DENIED")
    if not validated.kill_switch_available:
        raise ValueError("KILL_SWITCH_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_safe_payload(validated.metadata)
    return validated


def build_scoped_recurring_low_risk_automation_decision(
    request: ScopedRecurringLowRiskAutomationRequest,
    policy: ScopedRecurringLowRiskAutomationPolicy | None = None,
) -> ScopedRecurringLowRiskAutomationDecision:
    active_policy = validate_scoped_recurring_low_risk_automation_policy(policy)
    validated_request = validate_scoped_recurring_low_risk_automation_request(
        request, active_policy
    )
    receipt = ScopedRecurringLowRiskAutomationReceiptPlan(
        receipt_plan_ref=(
            "scoped-recurring-low-risk-receipt-plan:"
            f"{_ref_suffix(validated_request.request_ref)}"
        ),
        request_ref=validated_request.request_ref,
        actor_ref=validated_request.actor_ref,
        scope_ref=validated_request.scope_ref,
        resource_ref=validated_request.resource_ref,
        workflow_ref=validated_request.workflow_ref,
        action_ref=validated_request.action_ref,
        cadence_ref=validated_request.cadence.cadence_ref,
        approval_bundle_ref=validated_request.approval_bundle_ref,
        renewal_ref=validated_request.renewal_ref,
        expiration_ref=validated_request.expiration_ref,
        audit_ref=validated_request.audit_ref,
        revocation_ref=validated_request.revocation_ref,
        kill_switch_ref=validated_request.kill_switch_ref,
    )
    return validate_scoped_recurring_low_risk_automation_decision(
        ScopedRecurringLowRiskAutomationDecision(
            decision_ref=(
                "scoped-recurring-low-risk-decision:"
                f"{_ref_suffix(validated_request.request_ref)}"
            ),
            request_ref=validated_request.request_ref,
            actor_ref=validated_request.actor_ref,
            scope_ref=validated_request.scope_ref,
            resource_ref=validated_request.resource_ref,
            workflow_ref=validated_request.workflow_ref,
            action_ref=validated_request.action_ref,
            cadence_ref=validated_request.cadence.cadence_ref,
            approval_bundle_ref=validated_request.approval_bundle_ref,
            renewal_ref=validated_request.renewal_ref,
            expiration_ref=validated_request.expiration_ref,
            stop_condition_refs=list(validated_request.stop_condition_refs),
            audit_ref=validated_request.audit_ref,
            revocation_ref=validated_request.revocation_ref,
            kill_switch_ref=validated_request.kill_switch_ref,
            status=ScopedRecurringLowRiskAutomationStatus.scoped_low_risk_ready_for_review,
            enabled_for_review=active_policy.enabled_for_review,
            low_risk_only=active_policy.low_risk_only,
            read_only_only=active_policy.read_only_only,
            strict_cadence_required=active_policy.strict_cadence_required,
            renewal_required=active_policy.renewal_required,
            renewal_not_expired=True,
            stop_conditions_required=active_policy.stop_conditions_required,
            audit_required=active_policy.audit_required,
            revocation_required=active_policy.revocation_required,
            kill_switch_required=active_policy.kill_switch_required,
            kill_switch_available=validated_request.kill_switch_available,
            no_secret_access=active_policy.no_secret_access,
            safe_refs_only=active_policy.safe_refs_only_required,
            receipt_plan=receipt,
            reason_codes=[
                "M98_SCOPED_RECURRING_LOW_RISK_READY_FOR_REVIEW",
                "LOW_RISK_READ_ONLY_ONLY",
                "STRICT_CADENCE_REQUIRED",
                "RENEWAL_ACTIVE",
                "STOP_CONDITIONS_REQUIRED",
                "KILL_SWITCH_READY",
                "AUDIT_TRAIL_REQUIRED",
                "NO_RUNTIME_SCHEDULER_OR_WORKER",
                "M99_REMAINS_FUTURE",
            ],
            safe_summary=(
                "M98 defines scoped low-risk read-only recurring automation review "
                "contracts with strict cadence, active renewal, stop conditions, audit, "
                "revocation, and kill switch refs. It starts no scheduler or worker, "
                "performs no recurring execution, accesses no sensitive material, and grants no "
                "production authority."
            ),
        )
    )


def validate_scoped_recurring_low_risk_automation_decision(
    decision: ScopedRecurringLowRiskAutomationDecision,
) -> ScopedRecurringLowRiskAutomationDecision:
    validated = ScopedRecurringLowRiskAutomationDecision.model_validate(
        decision.model_dump(mode="python", round_trip=True)
    )
    for field_name, reason in _DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if not validated.stop_condition_refs:
        raise ValueError("STOP_CONDITION_REQUIRED")
    _validate_receipt_plan(validated.receipt_plan)
    for field_name in [
        "request_ref",
        "actor_ref",
        "scope_ref",
        "resource_ref",
        "workflow_ref",
        "action_ref",
        "cadence_ref",
        "approval_bundle_ref",
        "renewal_ref",
        "expiration_ref",
        "audit_ref",
        "revocation_ref",
        "kill_switch_ref",
    ]:
        if getattr(validated.receipt_plan, field_name) != getattr(validated, field_name):
            raise ValueError("RECEIPT_PLAN_BINDING_MISMATCH")
    _validate_safe_payload(validated.metadata)
    return validated


def _validate_cadence(
    cadence: ScopedRecurringLowRiskAutomationCadence,
) -> ScopedRecurringLowRiskAutomationCadence:
    validated = ScopedRecurringLowRiskAutomationCadence.model_validate(
        cadence.model_dump(mode="python", round_trip=True)
    )
    if validated.minimum_interval_seconds < 300:
        raise ValueError("CADENCE_INTERVAL_TOO_SHORT")
    if validated.max_occurrences < 1:
        raise ValueError("MAX_OCCURRENCES_REQUIRED")
    if validated.max_occurrences > 31:
        raise ValueError("MAX_OCCURRENCES_TOO_HIGH")
    return validated


def _validate_receipt_plan(
    receipt_plan: ScopedRecurringLowRiskAutomationReceiptPlan,
) -> ScopedRecurringLowRiskAutomationReceiptPlan:
    validated = ScopedRecurringLowRiskAutomationReceiptPlan.model_validate(
        receipt_plan.model_dump(mode="python", round_trip=True)
    )
    if not validated.store_safe_refs_only:
        raise ValueError("SAFE_REFS_ONLY_REQUIRED")
    for field_name, reason in _RECEIPT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    return validated


def _validate_safe_ref(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError("SAFE_REF_REQUIRED")
    _validate_m61_ref(value, field_name)


_POLICY_REQUIRED_TRUE = [
    ("enabled_for_review", "ENABLED_FOR_REVIEW_REQUIRED"),
    ("low_risk_only", "LOW_RISK_ONLY_REQUIRED"),
    ("read_only_only", "READ_ONLY_ONLY_REQUIRED"),
    ("strict_cadence_required", "STRICT_CADENCE_REQUIRED"),
    ("renewal_required", "RENEWAL_REQUIRED"),
    ("expiration_required", "EXPIRATION_REQUIRED"),
    ("stop_conditions_required", "STOP_CONDITIONS_REQUIRED"),
    ("audit_required", "AUDIT_REQUIRED"),
    ("revocation_required", "REVOCATION_REQUIRED"),
    ("kill_switch_required", "KILL_SWITCH_REQUIRED"),
    ("no_secret_access", "SECRET_ACCESS_DENIED"),
    ("safe_refs_only_required", "SAFE_REFS_ONLY_REQUIRED"),
]

_POLICY_DENIALS = [
    ("runtime_allowed", "RUNTIME_DENIED"),
    ("scheduler_allowed", "SCHEDULER_DENIED"),
    ("background_worker_allowed", "BACKGROUND_WORKER_DENIED"),
    ("recurring_execution_allowed", "RECURRING_EXECUTION_DENIED"),
    ("mutating_tasks_allowed", "MUTATING_TASK_DENIED"),
    ("credential_access_allowed", "SECRET_ACCESS_DENIED"),
    ("secret_access_allowed", "SECRET_ACCESS_DENIED"),
    ("account_actions_allowed", "ACCOUNT_ACTION_DENIED"),
    ("shell_write_allowed", "SHELL_WRITE_DENIED"),
    ("network_write_allowed", "NETWORK_WRITE_DENIED"),
    ("browser_write_allowed", "BROWSER_WRITE_DENIED"),
    ("silent_background_collection_allowed", "BACKGROUND_COLLECTION_DENIED"),
    ("memory_write_allowed", "MEMORY_WRITE_DENIED"),
    ("context_injection_allowed", "CONTEXT_INJECTION_DENIED"),
    ("export_allowed", "EXPORT_DENIED"),
    ("backend_route_allowed", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_allowed", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_allowed", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_allowed", "PRODUCTION_AUTHORITY_DENIED"),
]

_REQUEST_DENIALS = [
    ("runtime_requested", "RUNTIME_DENIED"),
    ("scheduler_requested", "SCHEDULER_DENIED"),
    ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
    ("recurring_execution_requested", "RECURRING_EXECUTION_DENIED"),
    ("mutating_task_requested", "MUTATING_TASK_DENIED"),
    ("credential_access_requested", "SECRET_ACCESS_DENIED"),
    ("account_action_requested", "ACCOUNT_ACTION_DENIED"),
    ("shell_write_requested", "SHELL_WRITE_DENIED"),
    ("network_write_requested", "NETWORK_WRITE_DENIED"),
    ("browser_write_requested", "BROWSER_WRITE_DENIED"),
    ("silent_background_collection_requested", "BACKGROUND_COLLECTION_DENIED"),
    ("memory_write_requested", "MEMORY_WRITE_DENIED"),
    ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
    ("export_requested", "EXPORT_DENIED"),
    ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
]

_DECISION_REQUIRED_TRUE = [
    ("enabled_for_review", "ENABLED_FOR_REVIEW_REQUIRED"),
    ("low_risk_only", "LOW_RISK_ONLY_REQUIRED"),
    ("read_only_only", "READ_ONLY_ONLY_REQUIRED"),
    ("strict_cadence_required", "STRICT_CADENCE_REQUIRED"),
    ("renewal_required", "RENEWAL_REQUIRED"),
    ("renewal_not_expired", "RENEWAL_EXPIRED_DENIED"),
    ("stop_conditions_required", "STOP_CONDITIONS_REQUIRED"),
    ("audit_required", "AUDIT_REQUIRED"),
    ("revocation_required", "REVOCATION_REQUIRED"),
    ("kill_switch_required", "KILL_SWITCH_REQUIRED"),
    ("kill_switch_available", "KILL_SWITCH_REQUIRED"),
    ("no_secret_access", "SECRET_ACCESS_DENIED"),
    ("safe_refs_only", "SAFE_REFS_ONLY_REQUIRED"),
]

_DECISION_DENIALS = [
    ("runtime_started", "RUNTIME_DENIED"),
    ("scheduler_enabled", "SCHEDULER_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("recurring_execution_performed", "RECURRING_EXECUTION_DENIED"),
    ("mutating_task_allowed", "MUTATING_TASK_DENIED"),
    ("secret_access_performed", "SECRET_ACCESS_DENIED"),
    ("account_action_performed", "ACCOUNT_ACTION_DENIED"),
    ("shell_write_performed", "SHELL_WRITE_DENIED"),
    ("network_write_performed", "NETWORK_WRITE_DENIED"),
    ("browser_write_performed", "BROWSER_WRITE_DENIED"),
    ("background_collection_performed", "BACKGROUND_COLLECTION_DENIED"),
    ("memory_write_performed", "MEMORY_WRITE_DENIED"),
    ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
    ("export_performed", "EXPORT_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]

_RECEIPT_DENIALS = [
    ("store_raw_payload", "RAW_PAYLOAD_DENIED"),
    ("runtime_started", "RUNTIME_DENIED"),
    ("scheduler_started", "SCHEDULER_DENIED"),
    ("background_worker_started", "BACKGROUND_WORKER_DENIED"),
    ("recurring_execution_performed", "RECURRING_EXECUTION_DENIED"),
    ("mutating_task_performed", "MUTATING_TASK_DENIED"),
    ("secret_access_performed", "SECRET_ACCESS_DENIED"),
    ("account_action_performed", "ACCOUNT_ACTION_DENIED"),
    ("shell_write_performed", "SHELL_WRITE_DENIED"),
    ("network_write_performed", "NETWORK_WRITE_DENIED"),
    ("browser_write_performed", "BROWSER_WRITE_DENIED"),
    ("background_collection_performed", "BACKGROUND_COLLECTION_DENIED"),
    ("memory_write_performed", "MEMORY_WRITE_DENIED"),
    ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
    ("export_performed", "EXPORT_DENIED"),
]
