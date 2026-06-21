from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _ref_suffix, _validate_m61_ref, _validate_safe_payload


RECURRING_AUTOMATION_CONTRACT_DOCS = [
    "docs/automation/RECURRING_AUTOMATION_CONTRACTS.md",
    "docs/automation/RECURRING_AUTOMATION_RENEWAL_POLICY.md",
    "docs/automation/RECURRING_AUTOMATION_STOP_CONDITIONS.md",
    "docs/automation/RECURRING_AUTOMATION_AUTHORITY_BOUNDARY.md",
    "docs/automation/RECURRING_AUTOMATION_RECEIPT_PLAN.md",
    "docs/automation/RECURRING_AUTOMATION_NON_GOALS.md",
    "docs/automation/M97_TO_M98_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]


class RecurringAutomationContractStatus(str, Enum):
    contract_ready_disabled = "contract_ready_disabled"
    denied = "denied"


class _RecurringAutomationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class RecurringAutomationCadence(_RecurringAutomationModel):
    cadence_ref: str
    cadence_label: str
    minimum_interval_seconds: int = Field(ge=0)
    max_occurrences: int = Field(ge=0)
    jitter_policy_ref: str
    time_window_ref: str

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.cadence_ref, "cadence_ref"),
            (self.jitter_policy_ref, "jitter_policy_ref"),
            (self.time_window_ref, "time_window_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.cadence_label)
        return self


class RecurringAutomationPolicy(_RecurringAutomationModel):
    policy_ref: str = "recurring-automation-policy:m97"
    capability_exists: bool = True
    disabled_by_default: bool = True
    contract_only: bool = True
    approval_renewal_required: bool = True
    expiration_required: bool = True
    stop_conditions_required: bool = True
    audit_required: bool = True
    revocation_required: bool = True
    safe_refs_only_required: bool = True
    recurrence_runtime_allowed: bool = False
    background_worker_allowed: bool = False
    cron_daemon_allowed: bool = False
    scheduler_allowed: bool = False
    actual_recurring_execution_allowed: bool = False
    side_effects_allowed: bool = False
    shell_execution_allowed: bool = False
    network_access_allowed: bool = False
    browser_automation_allowed: bool = False
    plugin_execution_allowed: bool = False
    memory_write_allowed: bool = False
    context_injection_allowed: bool = False
    backend_route_allowed: bool = False
    control_center_control_allowed: bool = False
    dependency_change_allowed: bool = False
    production_authority_allowed: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class RecurringAutomationContractRequest(_RecurringAutomationModel):
    request_ref: str
    actor_ref: str
    scope_ref: str
    resource_ref: str
    action_ref: str
    session_ref: str
    cadence: RecurringAutomationCadence
    approval_bundle_ref: str
    renewal_policy_ref: str
    expiration_ref: str
    stop_condition_refs: list[str]
    audit_ref: str
    revocation_ref: str
    safe_purpose: str
    approval_ref: str | None = None
    approval_test_ref: str | None = None
    authority_refs: list[str] = Field(default_factory=list)
    recurrence_runtime_requested: bool = False
    background_worker_requested: bool = False
    cron_daemon_requested: bool = False
    scheduler_requested: bool = False
    actual_recurring_execution_requested: bool = False
    side_effect_requested: bool = False
    shell_execution_requested: bool = False
    network_access_requested: bool = False
    browser_automation_requested: bool = False
    plugin_execution_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
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
            (self.action_ref, "action_ref"),
            (self.session_ref, "session_ref"),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.renewal_policy_ref, "renewal_policy_ref"),
            (self.expiration_ref, "expiration_ref"),
            (self.audit_ref, "audit_ref"),
            (self.revocation_ref, "revocation_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.stop_condition_refs:
            _validate_m61_ref(ref, "stop_condition_ref")
        if self.approval_ref is not None:
            _validate_m61_ref(self.approval_ref, "approval_ref")
        if self.approval_test_ref is not None:
            if self.approval_test_ref.startswith("approval_test"):
                raise ValueError("APPROVAL_TEST_REF_DENIED")
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        for ref in self.authority_refs:
            _validate_m61_ref(ref, "authority_ref")
        _validate_safe_payload(self.safe_purpose)
        return self


class RecurringAutomationContractReceiptPlan(_RecurringAutomationModel):
    receipt_plan_ref: str
    request_ref: str
    actor_ref: str
    scope_ref: str
    resource_ref: str
    action_ref: str
    cadence_ref: str
    approval_bundle_ref: str
    renewal_policy_ref: str
    expiration_ref: str
    audit_ref: str
    revocation_ref: str
    store_safe_refs_only: bool = True
    store_raw_payload: bool = False
    recurrence_runtime_started: bool = False
    background_worker_started: bool = False
    cron_daemon_started: bool = False
    scheduler_started: bool = False
    recurring_execution_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M97 recurring automation contract receipt stores safe refs only."

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.request_ref, "request_ref"),
            (self.actor_ref, "actor_ref"),
            (self.scope_ref, "scope_ref"),
            (self.resource_ref, "resource_ref"),
            (self.action_ref, "action_ref"),
            (self.cadence_ref, "cadence_ref"),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.renewal_policy_ref, "renewal_policy_ref"),
            (self.expiration_ref, "expiration_ref"),
            (self.audit_ref, "audit_ref"),
            (self.revocation_ref, "revocation_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class RecurringAutomationContractDecision(_RecurringAutomationModel):
    decision_ref: str
    request_ref: str
    actor_ref: str
    scope_ref: str
    resource_ref: str
    action_ref: str
    session_ref: str
    cadence_ref: str
    approval_bundle_ref: str
    renewal_policy_ref: str
    expiration_ref: str
    stop_condition_refs: list[str]
    audit_ref: str
    revocation_ref: str
    status: RecurringAutomationContractStatus
    capability_exists: bool = True
    disabled_by_default: bool = True
    contract_only: bool = True
    approval_renewal_required: bool = True
    expiration_required: bool = True
    stop_conditions_required: bool = True
    audit_required: bool = True
    revocation_required: bool = True
    safe_refs_only: bool = True
    recurrence_runtime_enabled: bool = False
    background_worker_enabled: bool = False
    cron_daemon_enabled: bool = False
    scheduler_enabled: bool = False
    recurring_execution_enabled: bool = False
    side_effects_allowed: bool = False
    shell_execution_allowed: bool = False
    network_access_allowed: bool = False
    browser_automation_allowed: bool = False
    plugin_execution_allowed: bool = False
    memory_write_allowed: bool = False
    context_injection_allowed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    receipt_plan: RecurringAutomationContractReceiptPlan
    reason_codes: list[str]
    safe_summary: str

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.request_ref, "request_ref"),
            (self.actor_ref, "actor_ref"),
            (self.scope_ref, "scope_ref"),
            (self.resource_ref, "resource_ref"),
            (self.action_ref, "action_ref"),
            (self.session_ref, "session_ref"),
            (self.cadence_ref, "cadence_ref"),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.renewal_policy_ref, "renewal_policy_ref"),
            (self.expiration_ref, "expiration_ref"),
            (self.audit_ref, "audit_ref"),
            (self.revocation_ref, "revocation_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.stop_condition_refs:
            _validate_m61_ref(ref, "stop_condition_ref")
        if not self.reason_codes:
            raise ValueError("M97_REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def validate_recurring_automation_policy(
    policy: RecurringAutomationPolicy | None = None,
) -> RecurringAutomationPolicy:
    validated = RecurringAutomationPolicy.model_validate(
        (policy or RecurringAutomationPolicy()).model_dump(mode="python", round_trip=True)
    )
    for field_name, reason in _POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_safe_payload(validated.metadata)
    return validated


def validate_recurring_automation_request(
    request: RecurringAutomationContractRequest,
    policy: RecurringAutomationPolicy | None = None,
) -> RecurringAutomationContractRequest:
    validate_recurring_automation_policy(policy)
    payload = request.model_dump(mode="python", round_trip=True)
    for field_name, reason in _REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = RecurringAutomationContractRequest.model_validate(payload)
    _validate_cadence(validated.cadence)
    if not validated.stop_condition_refs:
        raise ValueError("STOP_CONDITION_REQUIRED")
    if len(set(validated.stop_condition_refs)) != len(validated.stop_condition_refs):
        raise ValueError("STOP_CONDITION_DUPLICATE_DENIED")
    if validated.approval_ref:
        raise ValueError("APPROVAL_REF_NOT_RECURRING_AUTOMATION_AUTHORITY")
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
            raise ValueError("AUTHORITY_REF_NOT_RECURRING_AUTOMATION_AUTHORITY")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_safe_payload(validated.metadata)
    return validated


def build_recurring_automation_contract_decision(
    request: RecurringAutomationContractRequest,
    policy: RecurringAutomationPolicy | None = None,
) -> RecurringAutomationContractDecision:
    active_policy = validate_recurring_automation_policy(policy)
    validated_request = validate_recurring_automation_request(request, active_policy)
    receipt = RecurringAutomationContractReceiptPlan(
        receipt_plan_ref=f"recurring-automation-receipt-plan:{_ref_suffix(validated_request.request_ref)}",
        request_ref=validated_request.request_ref,
        actor_ref=validated_request.actor_ref,
        scope_ref=validated_request.scope_ref,
        resource_ref=validated_request.resource_ref,
        action_ref=validated_request.action_ref,
        cadence_ref=validated_request.cadence.cadence_ref,
        approval_bundle_ref=validated_request.approval_bundle_ref,
        renewal_policy_ref=validated_request.renewal_policy_ref,
        expiration_ref=validated_request.expiration_ref,
        audit_ref=validated_request.audit_ref,
        revocation_ref=validated_request.revocation_ref,
    )
    return validate_recurring_automation_contract_decision(
        RecurringAutomationContractDecision(
            decision_ref=f"recurring-automation-decision:{_ref_suffix(validated_request.request_ref)}",
            request_ref=validated_request.request_ref,
            actor_ref=validated_request.actor_ref,
            scope_ref=validated_request.scope_ref,
            resource_ref=validated_request.resource_ref,
            action_ref=validated_request.action_ref,
            session_ref=validated_request.session_ref,
            cadence_ref=validated_request.cadence.cadence_ref,
            approval_bundle_ref=validated_request.approval_bundle_ref,
            renewal_policy_ref=validated_request.renewal_policy_ref,
            expiration_ref=validated_request.expiration_ref,
            stop_condition_refs=list(validated_request.stop_condition_refs),
            audit_ref=validated_request.audit_ref,
            revocation_ref=validated_request.revocation_ref,
            status=RecurringAutomationContractStatus.contract_ready_disabled,
            capability_exists=active_policy.capability_exists,
            disabled_by_default=active_policy.disabled_by_default,
            contract_only=active_policy.contract_only,
            approval_renewal_required=active_policy.approval_renewal_required,
            expiration_required=active_policy.expiration_required,
            stop_conditions_required=active_policy.stop_conditions_required,
            audit_required=active_policy.audit_required,
            revocation_required=active_policy.revocation_required,
            safe_refs_only=active_policy.safe_refs_only_required,
            receipt_plan=receipt,
            reason_codes=[
                "M97_RECURRING_AUTOMATION_CONTRACT_READY_DISABLED",
                "CONTRACT_ONLY",
                "APPROVAL_RENEWAL_REQUIRED",
                "EXPIRATION_REQUIRED",
                "STOP_CONDITIONS_REQUIRED",
                "NO_RECURRENCE_RUNTIME",
                "NO_BACKGROUND_EXECUTION",
                "M98_REMAINS_FUTURE",
            ],
            safe_summary=(
                "M97 defines recurring automation contracts only. Renewal, expiration, "
                "stop conditions, audit, and revocation are required, while recurrence "
                "runtime, background workers, cron, schedulers, side effects, routes, "
                "dependencies, and production authority remain disabled."
            ),
        )
    )


def validate_recurring_automation_contract_decision(
    decision: RecurringAutomationContractDecision,
) -> RecurringAutomationContractDecision:
    validated = RecurringAutomationContractDecision.model_validate(
        decision.model_dump(mode="python", round_trip=True)
    )
    for field_name, reason in _DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_receipt_plan(validated.receipt_plan)
    if not validated.stop_condition_refs:
        raise ValueError("STOP_CONDITION_REQUIRED")
    return validated


def _validate_cadence(cadence: RecurringAutomationCadence) -> RecurringAutomationCadence:
    validated = RecurringAutomationCadence.model_validate(
        cadence.model_dump(mode="python", round_trip=True)
    )
    if validated.minimum_interval_seconds < 60:
        raise ValueError("CADENCE_INTERVAL_TOO_SHORT")
    if validated.max_occurrences < 1:
        raise ValueError("MAX_OCCURRENCES_REQUIRED")
    if validated.max_occurrences > 100:
        raise ValueError("MAX_OCCURRENCES_TOO_HIGH")
    return validated


def _validate_receipt_plan(
    receipt_plan: RecurringAutomationContractReceiptPlan,
) -> RecurringAutomationContractReceiptPlan:
    validated = RecurringAutomationContractReceiptPlan.model_validate(
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


_POLICY_REQUIRED_TRUE = [
    ("capability_exists", "CAPABILITY_EXISTS_REQUIRED"),
    ("disabled_by_default", "DISABLED_BY_DEFAULT_REQUIRED"),
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("approval_renewal_required", "APPROVAL_RENEWAL_REQUIRED"),
    ("expiration_required", "EXPIRATION_REQUIRED"),
    ("stop_conditions_required", "STOP_CONDITIONS_REQUIRED"),
    ("audit_required", "AUDIT_REQUIRED"),
    ("revocation_required", "REVOCATION_REQUIRED"),
    ("safe_refs_only_required", "SAFE_REFS_ONLY_REQUIRED"),
]

_POLICY_DENIALS = [
    ("recurrence_runtime_allowed", "RECURRENCE_RUNTIME_DENIED"),
    ("background_worker_allowed", "BACKGROUND_WORKER_DENIED"),
    ("cron_daemon_allowed", "CRON_DAEMON_DENIED"),
    ("scheduler_allowed", "SCHEDULER_DENIED"),
    ("actual_recurring_execution_allowed", "RECURRING_EXECUTION_DENIED"),
    ("side_effects_allowed", "SIDE_EFFECTS_DENIED"),
    ("shell_execution_allowed", "SHELL_EXECUTION_DENIED"),
    ("network_access_allowed", "NETWORK_ACCESS_DENIED"),
    ("browser_automation_allowed", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_allowed", "PLUGIN_EXECUTION_DENIED"),
    ("memory_write_allowed", "MEMORY_WRITE_DENIED"),
    ("context_injection_allowed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_allowed", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_allowed", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_allowed", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_allowed", "PRODUCTION_AUTHORITY_DENIED"),
]

_REQUEST_DENIALS = [
    ("recurrence_runtime_requested", "RECURRENCE_RUNTIME_DENIED"),
    ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
    ("cron_daemon_requested", "CRON_DAEMON_DENIED"),
    ("scheduler_requested", "SCHEDULER_DENIED"),
    ("actual_recurring_execution_requested", "RECURRING_EXECUTION_DENIED"),
    ("side_effect_requested", "SIDE_EFFECTS_DENIED"),
    ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
    ("network_access_requested", "NETWORK_ACCESS_DENIED"),
    ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
    ("memory_write_requested", "MEMORY_WRITE_DENIED"),
    ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
]

_DECISION_REQUIRED_TRUE = [
    ("capability_exists", "CAPABILITY_EXISTS_REQUIRED"),
    ("disabled_by_default", "DISABLED_BY_DEFAULT_REQUIRED"),
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("approval_renewal_required", "APPROVAL_RENEWAL_REQUIRED"),
    ("expiration_required", "EXPIRATION_REQUIRED"),
    ("stop_conditions_required", "STOP_CONDITIONS_REQUIRED"),
    ("audit_required", "AUDIT_REQUIRED"),
    ("revocation_required", "REVOCATION_REQUIRED"),
    ("safe_refs_only", "SAFE_REFS_ONLY_REQUIRED"),
]

_DECISION_DENIALS = [
    ("recurrence_runtime_enabled", "RECURRENCE_RUNTIME_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("cron_daemon_enabled", "CRON_DAEMON_DENIED"),
    ("scheduler_enabled", "SCHEDULER_DENIED"),
    ("recurring_execution_enabled", "RECURRING_EXECUTION_DENIED"),
    ("side_effects_allowed", "SIDE_EFFECTS_DENIED"),
    ("shell_execution_allowed", "SHELL_EXECUTION_DENIED"),
    ("network_access_allowed", "NETWORK_ACCESS_DENIED"),
    ("browser_automation_allowed", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_allowed", "PLUGIN_EXECUTION_DENIED"),
    ("memory_write_allowed", "MEMORY_WRITE_DENIED"),
    ("context_injection_allowed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]

_RECEIPT_DENIALS = [
    ("store_raw_payload", "RAW_PAYLOAD_DENIED"),
    ("recurrence_runtime_started", "RECURRENCE_RUNTIME_DENIED"),
    ("background_worker_started", "BACKGROUND_WORKER_DENIED"),
    ("cron_daemon_started", "CRON_DAEMON_DENIED"),
    ("scheduler_started", "SCHEDULER_DENIED"),
    ("recurring_execution_performed", "RECURRING_EXECUTION_DENIED"),
]
