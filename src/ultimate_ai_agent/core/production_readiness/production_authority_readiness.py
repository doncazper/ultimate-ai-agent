from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.production_readiness.production_red_team_harness import (
    ProductionRedTeamHarnessRecord,
    validate_production_red_team_harness_record,
)


PRODUCTION_AUTHORITY_READINESS_REVIEW_DOCS = [
    "docs/production/PRODUCTION_AUTHORITY_READINESS_REVIEW.md",
    "docs/production/PRODUCTION_AUTHORITY_READINESS_BOUNDARY.md",
    "docs/production/PRODUCTION_AUTHORITY_READINESS_RECEIPT_PLAN.md",
    "docs/production/PRODUCTION_AUTHORITY_READINESS_NON_GOALS.md",
    "docs/production/M120_TO_M121_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class ProductionAuthorityReadinessReviewStatus(str, Enum):
    production_authority_readiness_review = "production_authority_readiness_review"


class _ProductionAuthorityReadinessReview(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ProductionAuthorityReadinessReviewPolicy(_ProductionAuthorityReadinessReview):
    policy_ref: str = "production-authority-readiness-policy:m120"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    baseline_binding_required: bool = True
    source_production_red_team_harness_binding_required: bool = True
    user_binding_required: bool = True
    workspace_binding_required: bool = True
    deployment_mode_binding_required: bool = True
    environment_binding_required: bool = True
    authority_tier_binding_required: bool = True
    readiness_check_binding_required: bool = True
    launch_blocker_binding_required: bool = True
    rollback_readiness_binding_required: bool = True
    readiness_check_refs_required: bool = True
    launch_blocker_refs_required: bool = True
    rollback_readiness_refs_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    production_authority_enabled: bool = False
    production_runtime_enabled: bool = False
    go_live_enabled: bool = False
    production_deployment_enabled: bool = False
    external_distribution_enabled: bool = False
    traffic_routing_enabled: bool = False
    account_action_enabled: bool = False
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
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class ProductionAuthorityReadinessReviewRecord(_ProductionAuthorityReadinessReview):
    production_authority_readiness_review_ref: str
    source_record: ProductionRedTeamHarnessRecord
    source_production_red_team_harness_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    deployment_mode_refs: list[str]
    environment_refs: list[str]
    authority_tier_refs: list[str]
    readiness_check_refs: list[str]
    launch_blocker_refs: list[str]
    rollback_readiness_refs: list[str]
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: ProductionAuthorityReadinessReviewStatus = (
        ProductionAuthorityReadinessReviewStatus.production_authority_readiness_review
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    baseline_bound: bool = True
    source_production_red_team_harness_bound: bool = True
    user_bound: bool = True
    workspace_bound: bool = True
    deployment_mode_bound: bool = True
    environment_bound: bool = True
    authority_tier_bound: bool = True
    readiness_check_bound: bool = True
    launch_blocker_bound: bool = True
    rollback_readiness_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    production_authority_enabled: bool = False
    production_runtime_enabled: bool = False
    go_live_enabled: bool = False
    production_deployment_enabled: bool = False
    external_distribution_enabled: bool = False
    traffic_routing_enabled: bool = False
    account_action_enabled: bool = False
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
            (
                self.production_authority_readiness_review_ref,
                "production_authority_readiness_review_ref",
            ),
            (
                self.source_production_red_team_harness_ref,
                "source_production_red_team_harness_ref",
            ),
            (self.source_baseline_ref, "source_baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.user_ref, "user_ref"),
            (self.workspace_ref, "workspace_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.deployment_mode_refs:
            _validate_m61_ref(ref, "deployment_mode_ref")
        for ref in self.environment_refs:
            _validate_m61_ref(ref, "environment_ref")
        for ref in self.authority_tier_refs:
            _validate_m61_ref(ref, "authority_tier_ref")
        for ref in self.readiness_check_refs:
            _validate_m61_ref(ref, "readiness_check_ref")
        for ref in self.launch_blocker_refs:
            _validate_m61_ref(ref, "launch_blocker_ref")
        for ref in self.rollback_readiness_refs:
            _validate_m61_ref(ref, "rollback_readiness_ref")
        for ref in self.accepted_checkpoint_refs:
            _validate_m61_ref(ref, "accepted_checkpoint_ref")
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_production_authority_readiness_review_record(
    *,
    source_record: ProductionRedTeamHarnessRecord,
    policy: ProductionAuthorityReadinessReviewPolicy | None = None,
) -> ProductionAuthorityReadinessReviewRecord:
    active_policy = validate_production_authority_readiness_review_policy(
        policy or ProductionAuthorityReadinessReviewPolicy()
    )
    validated_source = _validate_source_production_red_team_harness_record(
        _coerce_source_production_red_team_harness_record(source_record)
    )
    record = ProductionAuthorityReadinessReviewRecord(
        production_authority_readiness_review_ref=(
            "production-authority-readiness-review:m120"
        ),
        source_record=validated_source,
        source_production_red_team_harness_ref=(
            validated_source.production_red_team_harness_ref
        ),
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        user_ref=validated_source.user_ref,
        workspace_ref=validated_source.workspace_ref,
        deployment_mode_refs=validated_source.deployment_mode_refs,
        environment_refs=validated_source.environment_refs,
        authority_tier_refs=validated_source.authority_tier_refs,
        readiness_check_refs=[
            "readiness-check-ref:m120:authority-boundaries-reviewed",
            "readiness-check-ref:m120:launch-blockers-recorded",
            "readiness-check-ref:m120:rollback-readiness-reviewed",
        ],
        launch_blocker_refs=[
            "launch-blocker-ref:m120:no-production-authority",
            "launch-blocker-ref:m120:no-live-traffic",
            "launch-blocker-ref:m120:no-credential-runtime",
        ],
        rollback_readiness_refs=[
            "rollback-readiness-ref:m120:no-effect-plan",
            "rollback-readiness-ref:m120:manual-review-required",
        ],
        audit_ref="audit-ref:m120:production-authority-readiness",
        replay_ref="replay-ref:m120:production-authority-readiness",
        accepted_checkpoint_refs=[
            *validated_source.accepted_checkpoint_refs,
            "checkpoint:m119",
        ],
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m120:production-authority-readiness:no-effect"
        ),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        baseline_bound=active_policy.baseline_binding_required,
        source_production_red_team_harness_bound=(
            active_policy.source_production_red_team_harness_binding_required
        ),
        user_bound=active_policy.user_binding_required,
        workspace_bound=active_policy.workspace_binding_required,
        deployment_mode_bound=active_policy.deployment_mode_binding_required,
        environment_bound=active_policy.environment_binding_required,
        authority_tier_bound=active_policy.authority_tier_binding_required,
        readiness_check_bound=active_policy.readiness_check_binding_required,
        launch_blocker_bound=active_policy.launch_blocker_binding_required,
        rollback_readiness_bound=(
            active_policy.rollback_readiness_binding_required
        ),
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M120_PRODUCTION_AUTHORITY_READINESS_REVIEW",
            "M120_CONTRACT_ONLY",
            "M120_REVIEW_ONLY",
            "M120_NO_PRODUCTION_AUTHORITY_OR_GO_LIVE",
            "M121_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M120 records a contract-only and review-only production "
            "authority readiness review using safe refs for readiness checks, "
            "launch blockers, rollback readiness, audit, replay, and a "
            "no-effect receipt plan. It grants no production authority, "
            "starts no production runtime, performs no deployment, routes no "
            "traffic, handles no credentials, adds no routes, adds no "
            "controls, adds no dependencies, and keeps M121 future."
        ),
    )
    return validate_production_authority_readiness_review_record(record)


def validate_production_authority_readiness_review_policy(
    policy: ProductionAuthorityReadinessReviewPolicy,
) -> ProductionAuthorityReadinessReviewPolicy:
    validated = ProductionAuthorityReadinessReviewPolicy.model_validate(
        _model_payload(policy)
    )
    for field_name, reason in _M120_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M120_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m120_metadata(validated.metadata)
    return validated


def validate_production_authority_readiness_review_record(
    record: ProductionAuthorityReadinessReviewRecord,
) -> ProductionAuthorityReadinessReviewRecord:
    payload = _model_payload(record)
    for field_name, reason in _M120_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, ProductionAuthorityReadinessReviewRecord):
        raise ValueError("SECRET_LIKE_M120_PRODUCTION_AUTHORITY_READINESS_CONTENT_DENIED")
    for field_name, reason in [
        ("accepted_checkpoint_refs", "M120_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ("readiness_check_refs", "M120_READINESS_CHECK_REF_REQUIRED"),
        ("launch_blocker_refs", "M120_LAUNCH_BLOCKER_REF_REQUIRED"),
        ("rollback_readiness_refs", "M120_ROLLBACK_READINESS_REF_REQUIRED"),
    ]:
        if not payload.get(field_name):
            raise ValueError(reason)
    source_record = _coerce_source_production_red_team_harness_record(
        payload.get("source_record")
    )
    validated_source = _validate_source_production_red_team_harness_record(
        source_record
    )
    validated = ProductionAuthorityReadinessReviewRecord.model_validate(payload)
    for field_name, reason in _M120_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if (
        validated.status
        != ProductionAuthorityReadinessReviewStatus.production_authority_readiness_review
    ):
        raise ValueError("M120_PRODUCTION_AUTHORITY_READINESS_STATUS_REQUIRED")
    for field_name, reason in _M120_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m120_bindings(validated, validated_source)
    _validate_m120_metadata(validated.metadata)
    return validated


def _coerce_source_production_red_team_harness_record(
    value: Any,
) -> ProductionRedTeamHarnessRecord:
    if isinstance(value, ProductionRedTeamHarnessRecord):
        return value
    if isinstance(value, dict):
        return ProductionRedTeamHarnessRecord.model_validate(value)
    raise ValueError("M120_SOURCE_RECORD_REQUIRED")


def _validate_source_production_red_team_harness_record(
    source_record: ProductionRedTeamHarnessRecord,
) -> ProductionRedTeamHarnessRecord:
    source_payload = _model_payload(source_record)
    for field_name, reason in _M120_SOURCE_DENIALS:
        if source_payload.get(field_name):
            raise ValueError(reason)
    return validate_production_red_team_harness_record(source_record)


def _validate_m120_bindings(
    record: ProductionAuthorityReadinessReviewRecord,
    source_record: ProductionRedTeamHarnessRecord,
) -> None:
    if (
        record.source_production_red_team_harness_ref
        != source_record.production_red_team_harness_ref
    ):
        raise ValueError("M120_SOURCE_PRODUCTION_RED_TEAM_HARNESS_BINDING_MISMATCH")
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M120_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M120_ACTOR_BINDING_MISMATCH")
    if record.user_ref != source_record.user_ref:
        raise ValueError("M120_USER_BINDING_MISMATCH")
    if record.workspace_ref != source_record.workspace_ref:
        raise ValueError("M120_WORKSPACE_BINDING_MISMATCH")
    if record.deployment_mode_refs != source_record.deployment_mode_refs:
        raise ValueError("M120_DEPLOYMENT_MODE_BINDING_MISMATCH")
    if record.environment_refs != source_record.environment_refs:
        raise ValueError("M120_ENVIRONMENT_BINDING_MISMATCH")
    if record.authority_tier_refs != source_record.authority_tier_refs:
        raise ValueError("M120_AUTHORITY_TIER_BINDING_MISMATCH")
    if (
        record.production_authority_readiness_review_ref
        != "production-authority-readiness-review:m120"
    ):
        raise ValueError("M120_PRODUCTION_AUTHORITY_READINESS_REF_REQUIRED")
    for ref in record.readiness_check_refs:
        if not ref.startswith("readiness-check-ref:"):
            raise ValueError("M120_READINESS_CHECK_REF_REQUIRED")
    for ref in record.launch_blocker_refs:
        if not ref.startswith("launch-blocker-ref:"):
            raise ValueError("M120_LAUNCH_BLOCKER_REF_REQUIRED")
    for ref in record.rollback_readiness_refs:
        if not ref.startswith("rollback-readiness-ref:"):
            raise ValueError("M120_ROLLBACK_READINESS_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M120_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    if "checkpoint:m119" not in record.accepted_checkpoint_refs:
        raise ValueError("M120_ACCEPTED_CHECKPOINT_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M120_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m120_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError(
            "SECRET_LIKE_M120_PRODUCTION_AUTHORITY_READINESS_CONTENT_DENIED"
        ) from exc


_M120_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M120_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M120_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M120_ACTOR_BINDING_REQUIRED"),
    ("baseline_binding_required", "M120_BASELINE_BINDING_REQUIRED"),
    (
        "source_production_red_team_harness_binding_required",
        "M120_SOURCE_PRODUCTION_RED_TEAM_HARNESS_BINDING_REQUIRED",
    ),
    ("user_binding_required", "M120_USER_BINDING_REQUIRED"),
    ("workspace_binding_required", "M120_WORKSPACE_BINDING_REQUIRED"),
    ("deployment_mode_binding_required", "M120_DEPLOYMENT_MODE_BINDING_REQUIRED"),
    ("environment_binding_required", "M120_ENVIRONMENT_BINDING_REQUIRED"),
    ("authority_tier_binding_required", "M120_AUTHORITY_TIER_BINDING_REQUIRED"),
    ("readiness_check_binding_required", "M120_READINESS_CHECK_BINDING_REQUIRED"),
    ("launch_blocker_binding_required", "M120_LAUNCH_BLOCKER_BINDING_REQUIRED"),
    (
        "rollback_readiness_binding_required",
        "M120_ROLLBACK_READINESS_BINDING_REQUIRED",
    ),
    ("readiness_check_refs_required", "M120_READINESS_CHECK_REF_REQUIRED"),
    ("launch_blocker_refs_required", "M120_LAUNCH_BLOCKER_REF_REQUIRED"),
    ("rollback_readiness_refs_required", "M120_ROLLBACK_READINESS_REF_REQUIRED"),
    ("audit_required", "M120_AUDIT_REQUIRED"),
    ("replay_required", "M120_REPLAY_REQUIRED"),
]

_M120_POLICY_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("go_live_enabled", "GO_LIVE_DENIED"),
    ("production_deployment_enabled", "PRODUCTION_DEPLOYMENT_DENIED"),
    ("external_distribution_enabled", "EXTERNAL_DISTRIBUTION_DENIED"),
    ("traffic_routing_enabled", "TRAFFIC_ROUTING_DENIED"),
    ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
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
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M120_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M120_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M120_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M120_ACTOR_BINDING_REQUIRED"),
    ("baseline_bound", "M120_BASELINE_BINDING_REQUIRED"),
    (
        "source_production_red_team_harness_bound",
        "M120_SOURCE_PRODUCTION_RED_TEAM_HARNESS_BINDING_REQUIRED",
    ),
    ("user_bound", "M120_USER_BINDING_REQUIRED"),
    ("workspace_bound", "M120_WORKSPACE_BINDING_REQUIRED"),
    ("deployment_mode_bound", "M120_DEPLOYMENT_MODE_BINDING_REQUIRED"),
    ("environment_bound", "M120_ENVIRONMENT_BINDING_REQUIRED"),
    ("authority_tier_bound", "M120_AUTHORITY_TIER_BINDING_REQUIRED"),
    ("readiness_check_bound", "M120_READINESS_CHECK_BINDING_REQUIRED"),
    ("launch_blocker_bound", "M120_LAUNCH_BLOCKER_BINDING_REQUIRED"),
    ("rollback_readiness_bound", "M120_ROLLBACK_READINESS_BINDING_REQUIRED"),
    ("audit_required", "M120_AUDIT_REQUIRED"),
    ("replay_safe", "M120_REPLAY_REQUIRED"),
]

_M120_RECORD_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("go_live_enabled", "GO_LIVE_DENIED"),
    ("production_deployment_enabled", "PRODUCTION_DEPLOYMENT_DENIED"),
    ("external_distribution_enabled", "EXTERNAL_DISTRIBUTION_DENIED"),
    ("traffic_routing_enabled", "TRAFFIC_ROUTING_DENIED"),
    ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
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
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M120_SOURCE_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("red_team_execution_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("attack_automation_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("external_probe_enabled", "NETWORK_ACCESS_DENIED"),
    ("exploit_generation_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("security_scan_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]
