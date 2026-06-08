from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.mobile_companion.mobile_sensor_hardening_freeze import (
    MobileSensorHardeningFreezeRecord,
    validate_mobile_sensor_hardening_freeze_record,
)


PRODUCTION_THREAT_MODEL_DOCS = [
    "docs/production/PRODUCTION_THREAT_MODEL.md",
    "docs/production/PRODUCTION_THREAT_MODEL_POLICY.md",
    "docs/production/PRODUCTION_THREAT_MODEL_AUTHORITY_BOUNDARY.md",
    "docs/production/PRODUCTION_THREAT_MODEL_RECEIPT_PLAN.md",
    "docs/production/PRODUCTION_THREAT_MODEL_NON_GOALS.md",
    "docs/production/M111_TO_M112_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class ProductionThreatModelStatus(str, Enum):
    threat_model_contract = "threat_model_contract"


class _ProductionThreatModelModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ProductionThreatModelPolicy(_ProductionThreatModelModel):
    policy_ref: str = "production-threat-model-policy:m111"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    baseline_binding_required: bool = True
    source_freeze_binding_required: bool = True
    threat_surface_refs_required: bool = True
    mitigation_plan_refs_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    production_authority_enabled: bool = False
    production_runtime_enabled: bool = False
    external_distribution_enabled: bool = False
    deployment_enabled: bool = False
    credential_handling_enabled: bool = False
    network_access_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    background_worker_enabled: bool = False
    remote_execution_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class ProductionThreatModelRecord(_ProductionThreatModelModel):
    threat_model_ref: str
    source_record: MobileSensorHardeningFreezeRecord
    source_freeze_ref: str
    source_baseline_ref: str
    actor_ref: str
    threat_surface_refs: list[str]
    mitigation_plan_refs: list[str]
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: ProductionThreatModelStatus = (
        ProductionThreatModelStatus.threat_model_contract
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    baseline_bound: bool = True
    source_freeze_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    production_authority_enabled: bool = False
    production_runtime_enabled: bool = False
    external_distribution_enabled: bool = False
    deployment_enabled: bool = False
    credential_handling_enabled: bool = False
    network_access_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    background_worker_enabled: bool = False
    remote_execution_enabled: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.threat_model_ref, "threat_model_ref"),
            (self.source_freeze_ref, "source_freeze_ref"),
            (self.source_baseline_ref, "source_baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.threat_surface_refs:
            _validate_m61_ref(ref, "threat_surface_ref")
        for ref in self.mitigation_plan_refs:
            _validate_m61_ref(ref, "mitigation_plan_ref")
        for ref in self.accepted_checkpoint_refs:
            _validate_m61_ref(ref, "accepted_checkpoint_ref")
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_production_threat_model_record(
    *,
    source_record: MobileSensorHardeningFreezeRecord,
    policy: ProductionThreatModelPolicy | None = None,
) -> ProductionThreatModelRecord:
    active_policy = validate_production_threat_model_policy(
        policy or ProductionThreatModelPolicy()
    )
    validated_source = _validate_source_freeze_record(source_record)
    record = ProductionThreatModelRecord(
        threat_model_ref="production-threat-model:m111",
        source_record=validated_source,
        source_freeze_ref=validated_source.freeze_ref,
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        threat_surface_refs=[
            "threat-surface-ref:m111:production-runtime",
            "threat-surface-ref:m111:credential-boundary",
            "threat-surface-ref:m111:deployment-boundary",
        ],
        mitigation_plan_refs=[
            "mitigation-plan-ref:m111:no-production-authority",
            "mitigation-plan-ref:m111:no-credential-handling",
            "mitigation-plan-ref:m111:no-deployment-runtime",
        ],
        audit_ref="audit-ref:m111:production-threat-model",
        replay_ref="replay-ref:m111:production-threat-model",
        accepted_checkpoint_refs=[
            "checkpoint:m101",
            "checkpoint:m102",
            "checkpoint:m103",
            "checkpoint:m104",
            "checkpoint:m105",
            "checkpoint:m106",
            "checkpoint:m107",
            "checkpoint:m108",
            "checkpoint:m109",
            "checkpoint:m110",
        ],
        no_effect_receipt_plan_ref="receipt-plan-ref:m111:production-threat-model:no-effect",
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        baseline_bound=active_policy.baseline_binding_required,
        source_freeze_bound=active_policy.source_freeze_binding_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M111_PRODUCTION_THREAT_MODEL",
            "M111_CONTRACT_ONLY",
            "M111_REVIEW_ONLY",
            "M111_NO_PRODUCTION_AUTHORITY",
            "M112_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M111 records a contract-only and review-only production threat "
            "model using safe threat surface refs, mitigation plan refs, audit "
            "refs, replay refs, and a no-effect receipt plan. It grants no "
            "production authority, enables no production runtime, handles no "
            "credentials, performs no deployment, accesses no network, calls no "
            "models, writes no memory, injects no context, executes nothing, "
            "adds no routes, adds no controls, adds no dependencies, and keeps "
            "M112 future."
        ),
    )
    return validate_production_threat_model_record(record)


def validate_production_threat_model_policy(
    policy: ProductionThreatModelPolicy,
) -> ProductionThreatModelPolicy:
    validated = ProductionThreatModelPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M111_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M111_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m111_metadata(validated.metadata)
    return validated


def validate_production_threat_model_record(
    record: ProductionThreatModelRecord,
) -> ProductionThreatModelRecord:
    payload = _model_payload(record)
    for field_name, reason in _M111_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, ProductionThreatModelRecord):
        raise ValueError("SECRET_LIKE_M111_PRODUCTION_THREAT_MODEL_CONTENT_DENIED")
    source_record = _coerce_source_freeze_record(payload.get("source_record"))
    validated_source = _validate_source_freeze_record(source_record)
    validated = ProductionThreatModelRecord.model_validate(payload)
    for field_name, reason in _M111_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != ProductionThreatModelStatus.threat_model_contract:
        raise ValueError("M111_THREAT_MODEL_STATUS_REQUIRED")
    if not validated.accepted_checkpoint_refs:
        raise ValueError("M111_ACCEPTED_CHECKPOINT_REF_REQUIRED")
    if not validated.threat_surface_refs:
        raise ValueError("M111_THREAT_SURFACE_REF_REQUIRED")
    if not validated.mitigation_plan_refs:
        raise ValueError("M111_MITIGATION_PLAN_REF_REQUIRED")
    for field_name, reason in _M111_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m111_bindings(validated, validated_source)
    _validate_m111_metadata(validated.metadata)
    return validated


def _coerce_source_freeze_record(value: Any) -> MobileSensorHardeningFreezeRecord:
    if isinstance(value, MobileSensorHardeningFreezeRecord):
        return value
    if isinstance(value, dict):
        return MobileSensorHardeningFreezeRecord.model_validate(value)
    raise ValueError("M111_SOURCE_FREEZE_RECORD_REQUIRED")


def _validate_source_freeze_record(
    source_record: MobileSensorHardeningFreezeRecord,
) -> MobileSensorHardeningFreezeRecord:
    source_payload = _model_payload(source_record)
    for field_name, reason in _M111_SOURCE_DENIALS:
        if source_payload.get(field_name):
            raise ValueError(reason)
    return validate_mobile_sensor_hardening_freeze_record(source_record)


def _validate_m111_bindings(
    record: ProductionThreatModelRecord,
    source_record: MobileSensorHardeningFreezeRecord,
) -> None:
    if record.source_freeze_ref != source_record.freeze_ref:
        raise ValueError("M111_SOURCE_FREEZE_BINDING_MISMATCH")
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M111_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M111_ACTOR_BINDING_MISMATCH")
    if record.threat_model_ref != "production-threat-model:m111":
        raise ValueError("M111_THREAT_MODEL_REF_REQUIRED")
    for ref in record.threat_surface_refs:
        if not ref.startswith("threat-surface-ref:"):
            raise ValueError("M111_THREAT_SURFACE_REF_REQUIRED")
    for ref in record.mitigation_plan_refs:
        if not ref.startswith("mitigation-plan-ref:"):
            raise ValueError("M111_MITIGATION_PLAN_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M111_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M111_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m111_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError(
            "SECRET_LIKE_M111_PRODUCTION_THREAT_MODEL_CONTENT_DENIED"
        ) from exc


_M111_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M111_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M111_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M111_ACTOR_BINDING_REQUIRED"),
    ("baseline_binding_required", "M111_BASELINE_BINDING_REQUIRED"),
    ("source_freeze_binding_required", "M111_SOURCE_FREEZE_BINDING_REQUIRED"),
    ("threat_surface_refs_required", "M111_THREAT_SURFACE_REF_REQUIRED"),
    ("mitigation_plan_refs_required", "M111_MITIGATION_PLAN_REF_REQUIRED"),
    ("audit_required", "M111_AUDIT_REQUIRED"),
    ("replay_required", "M111_REPLAY_REQUIRED"),
]

_M111_POLICY_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("external_distribution_enabled", "EXTERNAL_DISTRIBUTION_DENIED"),
    ("deployment_enabled", "DEPLOYMENT_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M111_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M111_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M111_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M111_ACTOR_BINDING_REQUIRED"),
    ("baseline_bound", "M111_BASELINE_BINDING_REQUIRED"),
    ("source_freeze_bound", "M111_SOURCE_FREEZE_BINDING_REQUIRED"),
    ("audit_required", "M111_AUDIT_REQUIRED"),
    ("replay_safe", "M111_REPLAY_REQUIRED"),
]

_M111_RECORD_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("external_distribution_enabled", "EXTERNAL_DISTRIBUTION_DENIED"),
    ("deployment_enabled", "DEPLOYMENT_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M111_SOURCE_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("external_distribution_enabled", "EXTERNAL_DISTRIBUTION_DENIED"),
    ("deployment_enabled", "DEPLOYMENT_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
]
