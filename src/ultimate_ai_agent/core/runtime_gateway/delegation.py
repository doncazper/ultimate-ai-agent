from __future__ import annotations

from enum import Enum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    GOVERNED_RUNTIME_REDACTIONS,
    GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
)


RUNTIME_DELEGATION_CONTRACT_REF = "contract-ref:runtime-delegation-adapter:v1"
RUNTIME_DELEGATION_ROUTE_REF = "GET /api/runtime/delegation-adapter"
RUNTIME_DELEGATION_CLI_REF = "uaa runtime inspect-delegation-adapter"
RUNTIME_DELEGATION_CONTROL_CENTER_REF = "control-center-route:runtime"


class RuntimeDelegationKind(str, Enum):
    hermes_agent = "hermes_agent"
    codex = "codex"
    claude = "claude"
    uaa_native = "uaa_native"
    local_agent = "local_agent"
    future_provider = "future_provider"


class RuntimeDelegationAuthorityMode(str, Enum):
    sealed = "sealed"
    read_only_readiness = "read_only_readiness"
    proposal_only = "proposal_only"
    approval_required = "approval_required"
    blocked = "blocked"


class RuntimeDelegationEndpointPosture(BaseModel):
    endpoint_ref: str = "endpoint-ref:runtime-delegation:operator-config-required"
    endpoint_configured: bool = False
    endpoint_loopback_or_approved_network_required: bool = True
    live_transport_enabled: bool = False
    credential_ref: str = "credential-ref:runtime-delegation:not-configured"
    credential_material_exposed: bool = False
    network_policy_ref: str = "network-policy-ref:runtime-delegation:blocked-by-default"
    safe_summary: str = (
        "Runtime endpoint posture is metadata only until an exact approved "
        "transport lane exists."
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_endpoint_posture(self) -> "RuntimeDelegationEndpointPosture":
        for value, field_name in [
            (self.endpoint_ref, "endpoint_ref"),
            (self.credential_ref, "credential_ref"),
            (self.network_policy_ref, "network_policy_ref"),
        ]:
            validate_execution_ref(value, field_name)
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.live_transport_enabled:
            raise ValueError("RUNTIME_DELEGATION_LIVE_TRANSPORT_DENIED")
        if self.credential_material_exposed:
            raise ValueError("RUNTIME_DELEGATION_CREDENTIAL_MATERIAL_DENIED")
        return self


class RuntimeDelegationAdapterReadModel(BaseModel):
    schema_version: str = "runtime_delegation_adapter.v1"
    contract_ref: str = RUNTIME_DELEGATION_CONTRACT_REF
    adapter_ref: str
    runtime_identity_ref: str
    runtime_label: str
    runtime_kind: RuntimeDelegationKind
    authority_mode: RuntimeDelegationAuthorityMode = (
        RuntimeDelegationAuthorityMode.read_only_readiness
    )
    status: str = "readiness_only"
    endpoint_posture: RuntimeDelegationEndpointPosture = Field(
        default_factory=RuntimeDelegationEndpointPosture
    )
    capability_refs: list[str] = Field(default_factory=list)
    health_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_reason_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    route_ref: str = RUNTIME_DELEGATION_ROUTE_REF
    cli_ref: str = RUNTIME_DELEGATION_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    uaa_controls_authority: bool = True
    runtime_provides_capability_only: bool = True
    control_center_talks_directly_to_runtime: bool = False
    live_run_submission_enabled: bool = False
    runtime_model_calls_enabled: bool = False
    provider_sdk_calls_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False
    safe_refs_only: bool = True
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_provider_payload_persisted: bool = False
    raw_log_persisted: bool = False
    raw_local_path_persisted: bool = False
    credential_material_persisted: bool = False
    safe_summary: str = (
        "UAA owns authority and receipts; delegated runtimes provide optional "
        "capability metadata until exact approved lanes graduate."
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeDelegationAdapterReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.adapter_ref, "adapter_ref"),
            (self.runtime_identity_ref, "runtime_identity_ref"),
            (self.control_center_ref, "control_center_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "capability_refs",
            "health_refs",
            "proof_refs",
            "blocked_reason_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.runtime_label, "runtime_label"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        for redaction in self.redactions_applied:
            validate_safe_execution_text(redaction, "redactions_applied")
        if not self.uaa_controls_authority:
            raise ValueError("RUNTIME_DELEGATION_UAA_AUTHORITY_REQUIRED")
        if not self.runtime_provides_capability_only:
            raise ValueError("RUNTIME_DELEGATION_CAPABILITY_ONLY_REQUIRED")
        if self.control_center_talks_directly_to_runtime:
            raise ValueError("RUNTIME_DELEGATION_CONTROL_CENTER_DIRECT_RUNTIME_DENIED")
        denied_flags = {
            "live_run_submission_enabled": self.live_run_submission_enabled,
            "runtime_model_calls_enabled": self.runtime_model_calls_enabled,
            "provider_sdk_calls_enabled": self.provider_sdk_calls_enabled,
            "tool_execution_enabled": self.tool_execution_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "background_autonomy_enabled": self.background_autonomy_enabled,
            "production_authority_enabled": self.production_authority_enabled,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "raw_provider_payload_persisted": self.raw_provider_payload_persisted,
            "raw_log_persisted": self.raw_log_persisted,
            "raw_local_path_persisted": self.raw_local_path_persisted,
            "credential_material_persisted": self.credential_material_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(f"RUNTIME_DELEGATION_AUTHORITY_DENIED: {', '.join(enabled)}")
        if not self.safe_refs_only:
            raise ValueError("RUNTIME_DELEGATION_SAFE_REFS_REQUIRED")
        return self


class RuntimeDelegationAdapter(Protocol):
    adapter_ref: str
    runtime_kind: RuntimeDelegationKind

    def readiness(self) -> RuntimeDelegationAdapterReadModel:
        ...


class HermesRuntimeDelegationAdapter:
    adapter_ref = "runtime-delegation-adapter:hermes-agent"
    runtime_kind = RuntimeDelegationKind.hermes_agent

    def readiness(self) -> RuntimeDelegationAdapterReadModel:
        return build_hermes_runtime_delegation_read_model()


def build_hermes_runtime_delegation_read_model() -> RuntimeDelegationAdapterReadModel:
    return RuntimeDelegationAdapterReadModel(
        adapter_ref="runtime-delegation-adapter:hermes-agent",
        runtime_identity_ref="runtime-identity-ref:hermes-agent:optional-target",
        runtime_label="Hermes Agent optional delegated runtime",
        runtime_kind=RuntimeDelegationKind.hermes_agent,
        capability_refs=[
            "capability-ref:runtime-delegation:run-supervision",
            "capability-ref:runtime-delegation:event-ingest",
            "capability-ref:runtime-delegation:approval-bridge",
            "capability-ref:runtime-delegation:stop-posture",
        ],
        health_refs=[
            "health-ref:runtime-delegation:hermes-config-missing",
            "health-ref:runtime-delegation:live-transport-disabled",
        ],
        proof_refs=[
            "proof-ref:runtime-delegation:adapter-contract",
            "proof-ref:runtime-delegation:uaa-authority-owner",
        ],
        blocked_reason_refs=[
            *GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
            "blocked-authority:runtime-delegation-live-run-submission",
            "blocked-authority:runtime-delegation-direct-control-center-runtime-access",
            "blocked-authority:runtime-delegation-credential-material-exposure",
        ],
        next_safe_action_refs=[
            "next-safe-action-ref:runtime-delegation:configure-endpoint-metadata",
            "next-safe-action-ref:runtime-delegation:add-capability-snapshot",
            "next-safe-action-ref:runtime-delegation:bind-approval-envelope",
            "next-safe-action-ref:runtime-delegation:add-redacted-run-receipts",
        ],
    )


def build_runtime_delegation_adapter_read_model(
    runtime_kind: RuntimeDelegationKind | str = RuntimeDelegationKind.hermes_agent,
) -> RuntimeDelegationAdapterReadModel:
    kind = RuntimeDelegationKind(runtime_kind)
    if kind is RuntimeDelegationKind.hermes_agent:
        return build_hermes_runtime_delegation_read_model()
    dashed = kind.value.replace("_", "-")
    return RuntimeDelegationAdapterReadModel(
        adapter_ref=f"runtime-delegation-adapter:{dashed}",
        runtime_identity_ref=f"runtime-identity-ref:{dashed}:future-target",
        runtime_label=f"{kind.value.replace('_', ' ').title()} future delegated runtime",
        runtime_kind=kind,
        status="blocked_future_target",
        capability_refs=["capability-ref:runtime-delegation:future-runtime-readiness"],
        health_refs=["health-ref:runtime-delegation:future-runtime-unconfigured"],
        proof_refs=["proof-ref:runtime-delegation:future-runtime-posture"],
        blocked_reason_refs=[
            *GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
            "blocked-authority:runtime-delegation-future-runtime-unconfigured",
        ],
        next_safe_action_refs=[
            "next-safe-action-ref:runtime-delegation:define-runtime-contract"
        ],
    )
