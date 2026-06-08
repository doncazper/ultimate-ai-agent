from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.production_readiness.role_based_authority import (
    RoleBasedAuthorityModelRecord,
    validate_role_based_authority_model_record,
)


REMOTE_AGENT_COORDINATION_DOCS = [
    "docs/production/REMOTE_AGENT_COORDINATION_CONTRACT.md",
    "docs/production/REMOTE_AGENT_COORDINATION_BOUNDARY.md",
    "docs/production/REMOTE_AGENT_COORDINATION_RECEIPT_PLAN.md",
    "docs/production/REMOTE_AGENT_COORDINATION_NON_GOALS.md",
    "docs/production/M117_TO_M118_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class RemoteAgentCoordinationContractStatus(str, Enum):
    coordination_contract = "coordination_contract"


class _RemoteAgentCoordinationContract(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class RemoteAgentCoordinationContractPolicy(_RemoteAgentCoordinationContract):
    policy_ref: str = "remote-agent-coordination-policy:m117"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    baseline_binding_required: bool = True
    source_role_authority_model_binding_required: bool = True
    user_binding_required: bool = True
    workspace_binding_required: bool = True
    remote_agent_binding_required: bool = True
    coordination_scope_binding_required: bool = True
    trust_boundary_binding_required: bool = True
    handoff_protocol_binding_required: bool = True
    remote_agent_refs_required: bool = True
    coordination_scope_refs_required: bool = True
    trust_boundary_refs_required: bool = True
    handoff_protocol_refs_required: bool = True
    communication_channel_refs_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    production_authority_enabled: bool = False
    remote_agent_runtime_enabled: bool = False
    remote_dispatch_enabled: bool = False
    remote_execution_enabled: bool = False
    live_connection_enabled: bool = False
    network_access_enabled: bool = False
    agent_spawn_enabled: bool = False
    background_worker_enabled: bool = False
    credential_handling_enabled: bool = False
    account_action_enabled: bool = False
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


class RemoteAgentCoordinationContractRecord(_RemoteAgentCoordinationContract):
    remote_coordination_contract_ref: str
    source_record: RoleBasedAuthorityModelRecord
    source_role_authority_model_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    remote_agent_refs: list[str]
    coordination_scope_refs: list[str]
    trust_boundary_refs: list[str]
    handoff_protocol_refs: list[str]
    communication_channel_refs: list[str]
    revocation_boundary_ref: str
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: RemoteAgentCoordinationContractStatus = (
        RemoteAgentCoordinationContractStatus.coordination_contract
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    baseline_bound: bool = True
    source_role_authority_model_bound: bool = True
    user_bound: bool = True
    workspace_bound: bool = True
    remote_agent_bound: bool = True
    coordination_scope_bound: bool = True
    trust_boundary_bound: bool = True
    handoff_protocol_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    production_authority_enabled: bool = False
    remote_agent_runtime_enabled: bool = False
    remote_dispatch_enabled: bool = False
    remote_execution_enabled: bool = False
    live_connection_enabled: bool = False
    network_access_enabled: bool = False
    agent_spawn_enabled: bool = False
    background_worker_enabled: bool = False
    credential_handling_enabled: bool = False
    account_action_enabled: bool = False
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
            (self.remote_coordination_contract_ref, "remote_coordination_contract_ref"),
            (self.source_role_authority_model_ref, "source_role_authority_model_ref"),
            (self.source_baseline_ref, "source_baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.user_ref, "user_ref"),
            (self.workspace_ref, "workspace_ref"),
            (self.revocation_boundary_ref, "revocation_boundary_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.remote_agent_refs:
            _validate_m61_ref(ref, "remote_agent_ref")
        for ref in self.coordination_scope_refs:
            _validate_m61_ref(ref, "coordination_scope_ref")
        for ref in self.trust_boundary_refs:
            _validate_m61_ref(ref, "trust_boundary_ref")
        for ref in self.handoff_protocol_refs:
            _validate_m61_ref(ref, "handoff_protocol_ref")
        for ref in self.communication_channel_refs:
            _validate_m61_ref(ref, "communication_channel_ref")
        for ref in self.accepted_checkpoint_refs:
            _validate_m61_ref(ref, "accepted_checkpoint_ref")
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_remote_agent_coordination_contract_record(
    *,
    source_record: RoleBasedAuthorityModelRecord,
    policy: RemoteAgentCoordinationContractPolicy | None = None,
) -> RemoteAgentCoordinationContractRecord:
    active_policy = validate_remote_agent_coordination_contract_policy(
        policy or RemoteAgentCoordinationContractPolicy()
    )
    validated_source = _validate_source_role_authority_model_record(
        _coerce_source_role_authority_model_record(source_record)
    )
    record = RemoteAgentCoordinationContractRecord(
        remote_coordination_contract_ref="remote-agent-coordination:m117",
        source_record=validated_source,
        source_role_authority_model_ref=validated_source.role_authority_model_ref,
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        user_ref=validated_source.user_ref,
        workspace_ref=validated_source.workspace_ref,
        remote_agent_refs=[
            "remote-agent-ref:m117:reviewed-peer-agent",
            "remote-agent-ref:m117:coordination-placeholder",
        ],
        coordination_scope_refs=[
            "coordination-scope-ref:m117:review-only",
            "coordination-scope-ref:m117:no-live-dispatch",
        ],
        trust_boundary_refs=[
            "trust-boundary-ref:m117:no-runtime-trust",
            "trust-boundary-ref:m117:no-credential-transfer",
        ],
        handoff_protocol_refs=[
            "handoff-protocol-ref:m117:contract-only",
            "handoff-protocol-ref:m117:no-runtime-handoff",
        ],
        communication_channel_refs=[
            "communication-channel-ref:m117:declared-safe-ref-only",
            "communication-channel-ref:m117:no-live-connection",
        ],
        revocation_boundary_ref="revocation-boundary-ref:m117:review-only",
        audit_ref="audit-ref:m117:remote-agent-coordination-contract",
        replay_ref="replay-ref:m117:remote-agent-coordination-contract",
        accepted_checkpoint_refs=[
            *validated_source.accepted_checkpoint_refs,
            "checkpoint:m116",
        ],
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m117:remote-agent-coordination-contract:no-effect"
        ),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        baseline_bound=active_policy.baseline_binding_required,
        source_role_authority_model_bound=(
            active_policy.source_role_authority_model_binding_required
        ),
        user_bound=active_policy.user_binding_required,
        workspace_bound=active_policy.workspace_binding_required,
        remote_agent_bound=active_policy.remote_agent_binding_required,
        coordination_scope_bound=active_policy.coordination_scope_binding_required,
        trust_boundary_bound=active_policy.trust_boundary_binding_required,
        handoff_protocol_bound=active_policy.handoff_protocol_binding_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M117_REMOTE_AGENT_COORDINATION_CONTRACT",
            "M117_CONTRACT_ONLY",
            "M117_REVIEW_ONLY",
            "M117_NO_REMOTE_RUNTIME_OR_DISPATCH",
            "M118_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M117 records a contract-only and review-only remote agent "
            "coordination model using safe refs for peer agents, coordination "
            "scope, trust boundaries, handoff protocol, communication channel, "
            "revocation boundary, audit, replay, and a no-effect receipt plan. "
            "It starts no remote runtime, performs no dispatch, opens no live "
            "connection, uses no network, spawns no agents, handles no "
            "credentials, performs no account actions, calls no models, writes "
            "no memory, injects no context, executes nothing, adds no routes, "
            "adds no controls, adds no dependencies, and keeps M118 future."
        ),
    )
    return validate_remote_agent_coordination_contract_record(record)


def validate_remote_agent_coordination_contract_policy(
    policy: RemoteAgentCoordinationContractPolicy,
) -> RemoteAgentCoordinationContractPolicy:
    validated = RemoteAgentCoordinationContractPolicy.model_validate(
        _model_payload(policy)
    )
    for field_name, reason in _M117_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M117_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m117_metadata(validated.metadata)
    return validated


def validate_remote_agent_coordination_contract_record(
    record: RemoteAgentCoordinationContractRecord,
) -> RemoteAgentCoordinationContractRecord:
    payload = _model_payload(record)
    for field_name, reason in _M117_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, RemoteAgentCoordinationContractRecord):
        raise ValueError("SECRET_LIKE_M117_REMOTE_AGENT_COORDINATION_CONTENT_DENIED")
    for field_name, reason in [
        ("accepted_checkpoint_refs", "M117_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ("remote_agent_refs", "M117_REMOTE_AGENT_REF_REQUIRED"),
        ("coordination_scope_refs", "M117_COORDINATION_SCOPE_REF_REQUIRED"),
        ("trust_boundary_refs", "M117_TRUST_BOUNDARY_REF_REQUIRED"),
        ("handoff_protocol_refs", "M117_HANDOFF_PROTOCOL_REF_REQUIRED"),
        ("communication_channel_refs", "M117_COMMUNICATION_CHANNEL_REF_REQUIRED"),
        ("revocation_boundary_ref", "M117_REVOCATION_BOUNDARY_REF_REQUIRED"),
    ]:
        if not payload.get(field_name):
            raise ValueError(reason)
    source_record = _coerce_source_role_authority_model_record(
        payload.get("source_record")
    )
    validated_source = _validate_source_role_authority_model_record(source_record)
    validated = RemoteAgentCoordinationContractRecord.model_validate(payload)
    for field_name, reason in _M117_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if (
        validated.status
        != RemoteAgentCoordinationContractStatus.coordination_contract
    ):
        raise ValueError("M117_REMOTE_AGENT_COORDINATION_STATUS_REQUIRED")
    for field_name, reason in _M117_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m117_bindings(validated, validated_source)
    _validate_m117_metadata(validated.metadata)
    return validated


def _coerce_source_role_authority_model_record(
    value: Any,
) -> RoleBasedAuthorityModelRecord:
    if isinstance(value, RoleBasedAuthorityModelRecord):
        return value
    if isinstance(value, dict):
        return RoleBasedAuthorityModelRecord.model_validate(value)
    raise ValueError("M117_SOURCE_RECORD_REQUIRED")


def _validate_source_role_authority_model_record(
    source_record: RoleBasedAuthorityModelRecord,
) -> RoleBasedAuthorityModelRecord:
    source_payload = _model_payload(source_record)
    for field_name, reason in _M117_SOURCE_DENIALS:
        if source_payload.get(field_name):
            raise ValueError(reason)
    return validate_role_based_authority_model_record(source_record)


def _validate_m117_bindings(
    record: RemoteAgentCoordinationContractRecord,
    source_record: RoleBasedAuthorityModelRecord,
) -> None:
    if record.source_role_authority_model_ref != source_record.role_authority_model_ref:
        raise ValueError("M117_SOURCE_ROLE_AUTHORITY_MODEL_BINDING_MISMATCH")
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M117_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M117_ACTOR_BINDING_MISMATCH")
    if record.user_ref != source_record.user_ref:
        raise ValueError("M117_USER_BINDING_MISMATCH")
    if record.workspace_ref != source_record.workspace_ref:
        raise ValueError("M117_WORKSPACE_BINDING_MISMATCH")
    if record.remote_coordination_contract_ref != "remote-agent-coordination:m117":
        raise ValueError("M117_REMOTE_COORDINATION_CONTRACT_REF_REQUIRED")
    for ref in record.remote_agent_refs:
        if not ref.startswith("remote-agent-ref:"):
            raise ValueError("M117_REMOTE_AGENT_REF_REQUIRED")
    for ref in record.coordination_scope_refs:
        if not ref.startswith("coordination-scope-ref:"):
            raise ValueError("M117_COORDINATION_SCOPE_REF_REQUIRED")
    for ref in record.trust_boundary_refs:
        if not ref.startswith("trust-boundary-ref:"):
            raise ValueError("M117_TRUST_BOUNDARY_REF_REQUIRED")
    for ref in record.handoff_protocol_refs:
        if not ref.startswith("handoff-protocol-ref:"):
            raise ValueError("M117_HANDOFF_PROTOCOL_REF_REQUIRED")
    for ref in record.communication_channel_refs:
        if not ref.startswith("communication-channel-ref:"):
            raise ValueError("M117_COMMUNICATION_CHANNEL_REF_REQUIRED")
    if not record.revocation_boundary_ref.startswith("revocation-boundary-ref:"):
        raise ValueError("M117_REVOCATION_BOUNDARY_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M117_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    if "checkpoint:m116" not in record.accepted_checkpoint_refs:
        raise ValueError("M117_ACCEPTED_CHECKPOINT_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M117_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m117_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError(
            "SECRET_LIKE_M117_REMOTE_AGENT_COORDINATION_CONTENT_DENIED"
        ) from exc


_M117_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M117_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M117_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M117_ACTOR_BINDING_REQUIRED"),
    ("baseline_binding_required", "M117_BASELINE_BINDING_REQUIRED"),
    (
        "source_role_authority_model_binding_required",
        "M117_SOURCE_ROLE_AUTHORITY_MODEL_BINDING_REQUIRED",
    ),
    ("user_binding_required", "M117_USER_BINDING_REQUIRED"),
    ("workspace_binding_required", "M117_WORKSPACE_BINDING_REQUIRED"),
    ("remote_agent_binding_required", "M117_REMOTE_AGENT_BINDING_REQUIRED"),
    ("coordination_scope_binding_required", "M117_COORDINATION_SCOPE_BINDING_REQUIRED"),
    ("trust_boundary_binding_required", "M117_TRUST_BOUNDARY_BINDING_REQUIRED"),
    ("handoff_protocol_binding_required", "M117_HANDOFF_PROTOCOL_BINDING_REQUIRED"),
    ("remote_agent_refs_required", "M117_REMOTE_AGENT_REF_REQUIRED"),
    ("coordination_scope_refs_required", "M117_COORDINATION_SCOPE_REF_REQUIRED"),
    ("trust_boundary_refs_required", "M117_TRUST_BOUNDARY_REF_REQUIRED"),
    ("handoff_protocol_refs_required", "M117_HANDOFF_PROTOCOL_REF_REQUIRED"),
    ("communication_channel_refs_required", "M117_COMMUNICATION_CHANNEL_REF_REQUIRED"),
    ("audit_required", "M117_AUDIT_REQUIRED"),
    ("replay_required", "M117_REPLAY_REQUIRED"),
]

_M117_POLICY_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("remote_agent_runtime_enabled", "REMOTE_AGENT_RUNTIME_DENIED"),
    ("remote_dispatch_enabled", "REMOTE_DISPATCH_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("live_connection_enabled", "LIVE_CONNECTION_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("agent_spawn_enabled", "AGENT_SPAWN_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
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
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M117_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M117_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M117_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M117_ACTOR_BINDING_REQUIRED"),
    ("baseline_bound", "M117_BASELINE_BINDING_REQUIRED"),
    (
        "source_role_authority_model_bound",
        "M117_SOURCE_ROLE_AUTHORITY_MODEL_BINDING_REQUIRED",
    ),
    ("user_bound", "M117_USER_BINDING_REQUIRED"),
    ("workspace_bound", "M117_WORKSPACE_BINDING_REQUIRED"),
    ("remote_agent_bound", "M117_REMOTE_AGENT_BINDING_REQUIRED"),
    ("coordination_scope_bound", "M117_COORDINATION_SCOPE_BINDING_REQUIRED"),
    ("trust_boundary_bound", "M117_TRUST_BOUNDARY_BINDING_REQUIRED"),
    ("handoff_protocol_bound", "M117_HANDOFF_PROTOCOL_BINDING_REQUIRED"),
    ("audit_required", "M117_AUDIT_REQUIRED"),
    ("replay_safe", "M117_REPLAY_REQUIRED"),
]

_M117_RECORD_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("remote_agent_runtime_enabled", "REMOTE_AGENT_RUNTIME_DENIED"),
    ("remote_dispatch_enabled", "REMOTE_DISPATCH_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("live_connection_enabled", "LIVE_CONNECTION_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("agent_spawn_enabled", "AGENT_SPAWN_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
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

_M117_SOURCE_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("authority_runtime_enabled", "AUTHORITY_RUNTIME_DENIED"),
    ("role_enforcement_enabled", "ROLE_ENFORCEMENT_DENIED"),
    ("permission_enforcement_enabled", "PERMISSION_ENFORCEMENT_DENIED"),
    ("auth_runtime_enabled", "AUTH_RUNTIME_DENIED"),
    ("login_enabled", "LOGIN_DENIED"),
    ("session_cookie_handling_enabled", "SESSION_COOKIE_HANDLING_DENIED"),
    ("oauth_flow_enabled", "OAUTH_FLOW_DENIED"),
    ("token_exchange_enabled", "TOKEN_EXCHANGE_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
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
