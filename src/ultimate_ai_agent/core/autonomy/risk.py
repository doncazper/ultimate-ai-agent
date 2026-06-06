from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.approvals import (
    ScopedApprovalBundle,
    validate_scoped_approval_bundle,
)
from ultimate_ai_agent.core.autonomy.modes import (
    AutonomyRiskClass,
    _validate_m61_ref,
    _validate_safe_payload,
)
from ultimate_ai_agent.core.autonomy.revocation import (
    RevocationKillSwitchRecord,
    validate_revocation_kill_switch_record,
)


AUTONOMY_RISK_CLASSIFIER_DOCS = [
    "docs/autonomy/AUTONOMY_RISK_CLASSIFIER.md",
    "docs/autonomy/AUTONOMY_RISK_CLASSIFIER_CONTRACTS.md",
    "docs/autonomy/AUTONOMY_RISK_CLASSIFIER_NON_GOALS.md",
    "docs/autonomy/M68_TO_M69_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]


class AutonomyRiskSignalKind(str, Enum):
    redacted_review = "redacted_review"
    scoped_approval_bundle = "scoped_approval_bundle"
    revocation_intent = "revocation_intent"
    approval_ref = "approval_ref"
    dry_run_plan = "dry_run_plan"
    file_metadata_intent = "file_metadata_intent"
    context_proposal_intent = "context_proposal_intent"
    network_intent = "network_intent"
    browser_intent = "browser_intent"
    shell_intent = "shell_intent"
    plugin_intent = "plugin_intent"
    mobile_sensor_intent = "mobile_sensor_intent"
    remote_execution_intent = "remote_execution_intent"
    memory_write_intent = "memory_write_intent"
    context_injection_intent = "context_injection_intent"
    model_provider_intent = "model_provider_intent"
    production_authority_intent = "production_authority_intent"


_RISK_ORDER = {
    AutonomyRiskClass.low: 0,
    AutonomyRiskClass.medium: 1,
    AutonomyRiskClass.high: 2,
    AutonomyRiskClass.critical: 3,
}


class _AutonomyRiskClassifierModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AutonomyRiskSignal(_AutonomyRiskClassifierModel):
    signal_ref: str
    signal_kind: AutonomyRiskSignalKind
    risk_class: AutonomyRiskClass
    source_ref: str
    reason_code: str
    review_only: bool = True
    deterministic: bool = True
    authority_granted: bool = False
    execution_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.signal_ref, "signal_ref")
        _validate_m61_ref(self.source_ref, "source_ref")
        if not self.reason_code:
            raise ValueError("REASON_CODE_REQUIRED")
        return self


class AutonomyRiskClassificationRequest(_AutonomyRiskClassifierModel):
    classification_request_ref: str
    approval_bundle: ScopedApprovalBundle
    revocation_record: RevocationKillSwitchRecord
    declared_risk_class: AutonomyRiskClass
    risk_signals: list[AutonomyRiskSignal]
    actor_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    bundle_ref: str
    revocation_record_ref: str
    source_scope_ref: str
    audit_ref: str
    replay_ref: str
    review_only: bool = True
    deterministic: bool = True
    approval_refs_are_identifiers_only: bool = True
    authority_granted: bool = False
    policy_activation_requested: bool = False
    session_start_requested: bool = False
    session_active: bool = False
    autonomous_actions_enabled: bool = False
    background_worker_enabled: bool = False
    execution_requested: bool = False
    execution_performed: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    network_tool_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    model_provider_call_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    approval_test_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.classification_request_ref, "classification_request_ref"),
            (self.actor_ref, "actor_ref"),
            (self.bundle_ref, "bundle_ref"),
            (self.revocation_record_ref, "revocation_record_ref"),
            (self.source_scope_ref, "source_scope_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for refs, field_name, reason in [
            (self.resource_refs, "resource_ref", "RESOURCE_BINDING_REQUIRED"),
            (self.capability_refs, "capability_ref", "CAPABILITY_BINDING_REQUIRED"),
            (self.allowlist_refs, "allowlist_ref", "ALLOWLIST_REQUIRED"),
        ]:
            if not refs:
                raise ValueError(reason)
            for ref in refs:
                _validate_m61_ref(ref, field_name)
        if not self.risk_signals:
            raise ValueError("AUTONOMY_RISK_SIGNAL_REQUIRED")
        if self.approval_test_ref is not None:
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        return self


class AutonomyRiskClassificationDecision(_AutonomyRiskClassifierModel):
    decision_ref: str
    classification_request: AutonomyRiskClassificationRequest
    classification_request_ref: str
    actor_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    bundle_ref: str
    revocation_record_ref: str
    source_scope_ref: str
    audit_ref: str
    replay_ref: str
    declared_risk_class: AutonomyRiskClass
    derived_risk_class: AutonomyRiskClass
    classification_valid_for_review: bool = True
    review_only: bool = True
    deterministic: bool = True
    approval_refs_are_identifiers_only: bool = True
    authority_granted: bool = False
    risk_authority_granted: bool = False
    policy_activation_requested: bool = False
    session_start_requested: bool = False
    session_active: bool = False
    autonomous_actions_enabled: bool = False
    background_worker_enabled: bool = False
    execution_requested: bool = False
    execution_performed: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    network_tool_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    model_provider_call_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    approval_test_ref: str | None = None
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.classification_request_ref, "classification_request_ref"),
            (self.actor_ref, "actor_ref"),
            (self.bundle_ref, "bundle_ref"),
            (self.revocation_record_ref, "revocation_record_ref"),
            (self.source_scope_ref, "source_scope_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        if self.approval_test_ref is not None:
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        return self


def build_autonomy_risk_classification_decision(
    request: AutonomyRiskClassificationRequest,
) -> AutonomyRiskClassificationDecision:
    validated = validate_autonomy_risk_classification_request(request)
    derived = _derive_risk_class(validated)
    return validate_autonomy_risk_classification_decision(
        AutonomyRiskClassificationDecision(
            decision_ref=f"autonomy-risk-classification-decision:{_ref_suffix(validated.classification_request_ref)}",
            classification_request=validated,
            classification_request_ref=validated.classification_request_ref,
            actor_ref=validated.actor_ref,
            resource_refs=list(validated.resource_refs),
            capability_refs=list(validated.capability_refs),
            allowlist_refs=list(validated.allowlist_refs),
            bundle_ref=validated.bundle_ref,
            revocation_record_ref=validated.revocation_record_ref,
            source_scope_ref=validated.source_scope_ref,
            audit_ref=validated.audit_ref,
            replay_ref=validated.replay_ref,
            declared_risk_class=validated.declared_risk_class,
            derived_risk_class=derived,
            classification_valid_for_review=True,
            review_only=True,
            deterministic=True,
            approval_refs_are_identifiers_only=True,
            authority_granted=False,
            risk_authority_granted=False,
            execution_performed=False,
            side_effects_performed=[],
            reason_codes=[
                "M68_AUTONOMY_RISK_CLASSIFICATION_REVIEW_ONLY",
                f"M68_DERIVED_RISK_{derived.value.upper()}",
            ],
            safe_summary=(
                "M68 classifies autonomy risk for review only; it derives the highest risk from "
                "declared risk, scoped approval bundle risk, and explicit risk signals without "
                "granting authority, activating policy, starting sessions, or executing."
            ),
        )
    )


def validate_autonomy_risk_signal(signal: AutonomyRiskSignal) -> AutonomyRiskSignal:
    validated = AutonomyRiskSignal.model_validate(signal.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMY_RISK_CONTENT_DENIED") from exc
    if not validated.review_only:
        raise ValueError("REVIEW_ONLY_REQUIRED")
    if not validated.deterministic:
        raise ValueError("DETERMINISTIC_REPLAY_REQUIRED")
    if validated.authority_granted:
        raise ValueError("AUTONOMY_RISK_SIGNAL_AUTHORITY_DENIED")
    if validated.execution_performed:
        raise ValueError("EXECUTION_DENIED")
    if validated.side_effects_performed:
        raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")
    return validated


def validate_autonomy_risk_classification_request(
    request: AutonomyRiskClassificationRequest,
) -> AutonomyRiskClassificationRequest:
    validated = AutonomyRiskClassificationRequest.model_validate(request.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMY_RISK_CONTENT_DENIED") from exc
    try:
        bundle = validate_scoped_approval_bundle(validated.approval_bundle)
        revocation_record = validate_revocation_kill_switch_record(validated.revocation_record)
    except ValueError as exc:
        if "SECRET_LIKE" in str(exc):
            raise ValueError("SECRET_LIKE_AUTONOMY_RISK_CONTENT_DENIED") from exc
        raise
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    for field_name, reason in _RISK_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _RISK_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")
    for signal in validated.risk_signals:
        validate_autonomy_risk_signal(signal)
    _validate_request_bindings(validated, bundle, revocation_record)
    return validated


def validate_autonomy_risk_classification_decision(
    decision: AutonomyRiskClassificationDecision,
) -> AutonomyRiskClassificationDecision:
    validated = AutonomyRiskClassificationDecision.model_validate(decision.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMY_RISK_CONTENT_DENIED") from exc
    request = validate_autonomy_risk_classification_request(validated.classification_request)
    expected = _derive_risk_class(request)
    if _RISK_ORDER[validated.derived_risk_class] < _RISK_ORDER[expected]:
        raise ValueError("AUTONOMY_RISK_DOWNGRADE_DENIED")
    if validated.derived_risk_class != expected:
        raise ValueError("AUTONOMY_RISK_CLASSIFICATION_DRIFT_DENIED")
    _validate_decision_bindings(validated, request)
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    for field_name, reason in _RISK_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _RISK_DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")
    return validated


def _derive_risk_class(request: AutonomyRiskClassificationRequest) -> AutonomyRiskClass:
    risks = [request.declared_risk_class, request.approval_bundle.risk_class]
    risks.extend(signal.risk_class for signal in request.risk_signals)
    return max(risks, key=lambda risk: _RISK_ORDER[risk])


def _validate_request_bindings(
    request: AutonomyRiskClassificationRequest,
    bundle: ScopedApprovalBundle,
    revocation_record: RevocationKillSwitchRecord,
) -> None:
    if request.bundle_ref != bundle.bundle_ref:
        raise ValueError("AUTONOMY_RISK_BUNDLE_BINDING_MISMATCH_DENIED")
    if request.revocation_record_ref != revocation_record.revocation_record_ref:
        raise ValueError("AUTONOMY_RISK_REVOCATION_RECORD_BINDING_MISMATCH_DENIED")
    if request.source_scope_ref != bundle.source_scope_ref:
        raise ValueError("AUTONOMY_RISK_SCOPE_BINDING_MISMATCH_DENIED")
    if request.actor_ref != bundle.actor_ref:
        raise ValueError("AUTONOMY_RISK_ACTOR_BINDING_MISMATCH_DENIED")
    if request.resource_refs != bundle.resource_refs:
        raise ValueError("AUTONOMY_RISK_RESOURCE_BINDING_MISMATCH_DENIED")
    if request.capability_refs != bundle.capability_refs:
        raise ValueError("AUTONOMY_RISK_CAPABILITY_BINDING_MISMATCH_DENIED")
    if request.allowlist_refs != bundle.allowlist_refs:
        raise ValueError("AUTONOMY_RISK_ALLOWLIST_BINDING_MISMATCH_DENIED")
    if request.audit_ref != bundle.audit_ref:
        raise ValueError("AUTONOMY_RISK_AUDIT_BINDING_MISMATCH_DENIED")
    if request.replay_ref != bundle.replay_ref:
        raise ValueError("AUTONOMY_RISK_REPLAY_BINDING_MISMATCH_DENIED")


def _validate_decision_bindings(
    decision: AutonomyRiskClassificationDecision,
    request: AutonomyRiskClassificationRequest,
) -> None:
    if decision.classification_request_ref != request.classification_request_ref:
        raise ValueError("AUTONOMY_RISK_REQUEST_BINDING_MISMATCH_DENIED")
    if decision.actor_ref != request.actor_ref:
        raise ValueError("AUTONOMY_RISK_ACTOR_BINDING_MISMATCH_DENIED")
    if decision.resource_refs != request.resource_refs:
        raise ValueError("AUTONOMY_RISK_RESOURCE_BINDING_MISMATCH_DENIED")
    if decision.capability_refs != request.capability_refs:
        raise ValueError("AUTONOMY_RISK_CAPABILITY_BINDING_MISMATCH_DENIED")
    if decision.allowlist_refs != request.allowlist_refs:
        raise ValueError("AUTONOMY_RISK_ALLOWLIST_BINDING_MISMATCH_DENIED")
    if decision.bundle_ref != request.bundle_ref:
        raise ValueError("AUTONOMY_RISK_BUNDLE_BINDING_MISMATCH_DENIED")
    if decision.revocation_record_ref != request.revocation_record_ref:
        raise ValueError("AUTONOMY_RISK_REVOCATION_RECORD_BINDING_MISMATCH_DENIED")
    if decision.source_scope_ref != request.source_scope_ref:
        raise ValueError("AUTONOMY_RISK_SCOPE_BINDING_MISMATCH_DENIED")
    if decision.audit_ref != request.audit_ref:
        raise ValueError("AUTONOMY_RISK_AUDIT_BINDING_MISMATCH_DENIED")
    if decision.replay_ref != request.replay_ref:
        raise ValueError("AUTONOMY_RISK_REPLAY_BINDING_MISMATCH_DENIED")
    if decision.declared_risk_class != request.declared_risk_class:
        raise ValueError("AUTONOMY_RISK_DECLARATION_BINDING_MISMATCH_DENIED")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[1]


_RISK_REQUIRED_TRUE = [
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_REPLAY_REQUIRED"),
    ("approval_refs_are_identifiers_only", "APPROVAL_REF_IDENTIFIER_ONLY"),
]


_RISK_DENIALS = [
    ("authority_granted", "AUTONOMY_RISK_CLASSIFIER_AUTHORITY_DENIED"),
    ("policy_activation_requested", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
    ("session_start_requested", "AUTONOMY_SESSION_START_DENIED"),
    ("session_active", "AUTONOMY_SESSION_ACTIVATION_DENIED"),
    ("autonomous_actions_enabled", "AUTONOMOUS_ACTIONS_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("execution_requested", "EXECUTION_DENIED"),
    ("execution_performed", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("network_tool_enabled", "NETWORK_TOOL_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("model_provider_call_enabled", "MODEL_PROVIDER_CALL_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]


_RISK_DECISION_REQUIRED_TRUE = [
    ("classification_valid_for_review", "REVIEW_ONLY_REQUIRED"),
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_REPLAY_REQUIRED"),
    ("approval_refs_are_identifiers_only", "APPROVAL_REF_IDENTIFIER_ONLY"),
]


_RISK_DECISION_DENIALS = [
    ("authority_granted", "AUTONOMY_RISK_CLASSIFIER_AUTHORITY_DENIED"),
    ("risk_authority_granted", "AUTONOMY_RISK_CLASSIFIER_AUTHORITY_DENIED"),
    *_RISK_DENIALS[1:],
]
