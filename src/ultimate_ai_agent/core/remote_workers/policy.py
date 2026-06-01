from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.remote_workers.enums import RemoteRiskLevel
from ultimate_ai_agent.core.remote_workers.jobs import RemoteJobEnvelope
from ultimate_ai_agent.core.remote_workers.registry import RemoteNodeRegistry, RemoteTransportRegistry
from ultimate_ai_agent.core.remote_workers.status import RemotePolicyDecision, allowed_decision, denied_decision
from ultimate_ai_agent.core.remote_workers.validation import assert_remote_secret_clean
from ultimate_ai_agent.core.time import utc_now


class RemoteExecutionPolicy(BaseModel):
    policy_id: str = Field(..., min_length=1)
    remote_workers_enabled: bool = False
    remote_transports_enabled: bool = False
    remote_tailnet_enabled: bool = False
    remote_accept_jobs: bool = False
    remote_dispatch_enabled: bool = False
    remote_subagents_enabled: bool = False
    remote_approvals_enabled: bool = False
    remote_personal_data_enabled: bool = False
    allow_network: bool = False
    allow_write_actions: bool = False
    allow_send_actions: bool = False
    allow_critical_actions: bool = False
    require_local_approval_for_high_risk: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def policy_must_be_safe(self):
        if self.remote_dispatch_enabled:
            raise ValueError("REMOTE_DISPATCH_CANNOT_BE_ENABLED")
        if self.remote_subagents_enabled:
            raise ValueError("REMOTE_SUBAGENTS_CANNOT_BE_ENABLED")
        if self.remote_approvals_enabled:
            raise ValueError("REMOTE_APPROVALS_CANNOT_BE_ENABLED")
        if self.allow_network:
            raise ValueError("REMOTE_NETWORK_CANNOT_BE_ENABLED")
        if self.allow_write_actions:
            raise ValueError("REMOTE_WRITE_CANNOT_BE_ENABLED")
        if self.allow_send_actions:
            raise ValueError("REMOTE_SEND_CANNOT_BE_ENABLED")
        if self.allow_critical_actions:
            raise ValueError("REMOTE_CRITICAL_CANNOT_BE_ENABLED")
        assert_remote_secret_clean(self.model_dump(mode="json"), "Remote execution policy")
        return self


def evaluate_remote_job_policy(
    envelope: RemoteJobEnvelope,
    node_registry: RemoteNodeRegistry,
    transport_registry: RemoteTransportRegistry,
    policy: RemoteExecutionPolicy,
) -> RemotePolicyDecision:
    reasons: list[str] = []
    if not policy.remote_workers_enabled:
        reasons.append("REMOTE_WORKERS_DISABLED")
    if not policy.remote_transports_enabled:
        reasons.append("REMOTE_TRANSPORTS_DISABLED")
    if not policy.remote_accept_jobs:
        reasons.append("REMOTE_ACCEPT_JOBS_DISABLED")
    reasons.extend(_risk_reasons(envelope))
    reasons.extend(_capability_reasons(envelope.requested_capabilities))

    node_decision = node_registry.validate_node(envelope.node_id)
    transport_decision = transport_registry.validate_transport(envelope.transport_id)
    if not node_decision.allowed:
        reasons.extend(node_decision.reason_codes)
    if not transport_decision.allowed:
        reasons.extend(transport_decision.reason_codes)

    node = node_registry.get_node(envelope.node_id)
    if node is not None and envelope.transport_id not in node.allowed_transport_ids:
        reasons.append("REMOTE_NODE_TRANSPORT_NOT_ALLOWED")

    if reasons:
        return denied_decision(reasons, "Remote job is blocked by foundation policy.", job_id=envelope.job_id)
    return allowed_decision(["REMOTE_DRY_RUN_ALLOWED"], "Remote job dry-run metadata is allowed.", job_id=envelope.job_id)


def _risk_reasons(envelope: RemoteJobEnvelope) -> list[str]:
    if envelope.risk_level in {RemoteRiskLevel.high, RemoteRiskLevel.critical, RemoteRiskLevel.forbidden}:
        if envelope.risk_level == RemoteRiskLevel.high:
            return ["REMOTE_HIGH_RISK_REQUIRES_LOCAL_APPROVAL"]
        if envelope.risk_level == RemoteRiskLevel.critical:
            return ["REMOTE_CRITICAL_DENIED"]
        return ["REMOTE_FORBIDDEN_DENIED"]
    return []


def _capability_reasons(capabilities: list[str]) -> list[str]:
    reasons = []
    normalized = {capability.lower().replace("-", "_") for capability in capabilities}
    denied = {
        "personal_data": "REMOTE_PERSONAL_DATA_DENIED",
        "write": "REMOTE_WRITE_DENIED",
        "write_files": "REMOTE_WRITE_DENIED",
        "send": "REMOTE_SEND_DENIED",
        "send_messages": "REMOTE_SEND_DENIED",
        "approve": "REMOTE_APPROVAL_DENIED",
        "approval": "REMOTE_APPROVAL_DENIED",
        "subagent": "REMOTE_SUBAGENT_DENIED",
        "call_tools": "REMOTE_TOOL_EXECUTION_DENIED",
        "tools": "REMOTE_TOOL_EXECUTION_DENIED",
        "network": "REMOTE_NETWORK_DENIED",
        "sandbox": "REMOTE_SANDBOX_DENIED",
    }
    for capability, reason in denied.items():
        if capability in normalized:
            reasons.append(reason)
    return reasons

