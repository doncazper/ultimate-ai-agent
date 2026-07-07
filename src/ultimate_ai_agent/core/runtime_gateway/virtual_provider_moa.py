from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityDecisionCatalogEntry,
    build_authority_decision_catalog,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)


RUNTIME_VIRTUAL_PROVIDER_MOA_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-virtual-provider-moa:v1"
)
RUNTIME_VIRTUAL_PROVIDER_MOA_ROUTE_REF = "GET /api/runtime/virtual-provider-moa"
RUNTIME_VIRTUAL_PROVIDER_MOA_CLI_REF = "uaa runtime inspect-virtual-provider-moa"
RUNTIME_VIRTUAL_PROVIDER_MOA_SNAPSHOT_REF = (
    "virtual-provider-moa-snapshot-ref:runtime:presets"
)
RUNTIME_VIRTUAL_PROVIDER_MOA_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-20:virtual-provider-moa"
)
RUNTIME_VIRTUAL_PROVIDER_MOA_AUTHORITY_STATE_ROUTE_REF = (
    "GET /api/runtime/authority-state"
)
RUNTIME_VIRTUAL_PROVIDER_MOA_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_VIRTUAL_PROVIDER_MOA_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-virtual-provider-moa-read-model"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_VIRTUAL_PROVIDER_MOA_BLOCKED_AUTHORITY_REFS = [
    "blocked-authority:virtual-provider-moa-no-live-model-fanout",
    "blocked-authority:virtual-provider-moa-no-provider-sdk-call",
    "blocked-authority:virtual-provider-moa-no-external-runtime-dispatch",
    "blocked-authority:virtual-provider-moa-no-hidden-advisor-prompts",
    "blocked-authority:virtual-provider-moa-no-raw-prompt-persistence",
    "blocked-authority:virtual-provider-moa-no-raw-response-persistence",
    "blocked-authority:virtual-provider-moa-no-output-authority",
    "blocked-authority:virtual-provider-moa-no-connector-write",
    "blocked-authority:virtual-provider-moa-no-shell-execution",
    "blocked-authority:virtual-provider-moa-no-browser-automation",
    "blocked-authority:virtual-provider-moa-no-production-authority",
]


class RuntimeVirtualAgentRole(str, Enum):
    codex_implementer = "codex_implementer"
    claude_reviewer = "claude_reviewer"
    hermes_researcher = "hermes_researcher"
    local_verifier = "local_verifier"
    uaa_supervisor = "uaa_supervisor"
    security_reviewer = "security_reviewer"


class RuntimeVirtualProviderPresetStatus(str, Enum):
    metadata_only = "metadata_only"
    readiness_only = "readiness_only"
    blocked_requires_authority = "blocked_requires_authority"


class RuntimeVirtualAgentSlot(BaseModel):
    slot_ref: str
    display_label: str
    role: RuntimeVirtualAgentRole
    runtime_ref: str
    provider_ref: str
    model_ref: str
    authority_profile_ref: str
    route_decision_trace_ref: str
    cost_estimate_ref: str
    output_envelope_ref: str
    comparison_proof_ref: str
    safe_disable_ref: str
    safe_summary: str
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    configured_for_live_call: bool = False
    provider_sdk_call_enabled: bool = False
    external_runtime_dispatch_enabled: bool = False
    hidden_advisor_prompt_enabled: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    output_authoritative: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_slot(self) -> "RuntimeVirtualAgentSlot":
        for value, field_name in [
            (self.slot_ref, "slot_ref"),
            (self.runtime_ref, "runtime_ref"),
            (self.provider_ref, "provider_ref"),
            (self.model_ref, "model_ref"),
            (self.authority_profile_ref, "authority_profile_ref"),
            (self.route_decision_trace_ref, "route_decision_trace_ref"),
            (self.cost_estimate_ref, "cost_estimate_ref"),
            (self.output_envelope_ref, "output_envelope_ref"),
            (self.comparison_proof_ref, "comparison_proof_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in ("proof_refs", "evidence_refs", "blocked_authority_refs"):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        validate_safe_execution_text(self.display_label, "display_label")
        validate_safe_execution_text(str(self.role), "role")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        denied_flags = {
            "configured_for_live_call": self.configured_for_live_call,
            "provider_sdk_call_enabled": self.provider_sdk_call_enabled,
            "external_runtime_dispatch_enabled": self.external_runtime_dispatch_enabled,
            "hidden_advisor_prompt_enabled": self.hidden_advisor_prompt_enabled,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "output_authoritative": self.output_authoritative,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_VIRTUAL_PROVIDER_SLOT_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_VIRTUAL_PROVIDER_SLOT_BLOCKERS_REQUIRED")
        return self


class RuntimeVirtualProviderPreset(BaseModel):
    preset_ref: str
    display_label: str
    status: RuntimeVirtualProviderPresetStatus
    safe_summary: str
    approval_mode_ref: str
    route_decision_trace_ref: str
    cost_estimate_ref: str
    comparison_proof_ref: str
    safe_disable_ref: str
    slots: list[RuntimeVirtualAgentSlot]
    slot_count: int = 0
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    per_agent_output_envelopes_required: bool = True
    comparison_proof_required: bool = True
    live_model_fanout_enabled: bool = False
    provider_sdk_enabled: bool = False
    external_runtime_dispatch_enabled: bool = False
    hidden_advisor_prompts_enabled: bool = False
    raw_prompt_persistence_enabled: bool = False
    raw_response_persistence_enabled: bool = False
    output_authority_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_preset(self) -> "RuntimeVirtualProviderPreset":
        for value, field_name in [
            (self.preset_ref, "preset_ref"),
            (self.approval_mode_ref, "approval_mode_ref"),
            (self.route_decision_trace_ref, "route_decision_trace_ref"),
            (self.cost_estimate_ref, "cost_estimate_ref"),
            (self.comparison_proof_ref, "comparison_proof_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "proof_refs",
            "evidence_refs",
            "verifier_refs",
            "blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        validate_safe_execution_text(self.display_label, "display_label")
        validate_safe_execution_text(str(self.status), "status")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.slot_count != len(self.slots):
            raise ValueError("RUNTIME_VIRTUAL_PROVIDER_SLOT_COUNT_MISMATCH")
        if not self.per_agent_output_envelopes_required:
            raise ValueError("RUNTIME_VIRTUAL_PROVIDER_OUTPUT_ENVELOPES_REQUIRED")
        if not self.comparison_proof_required:
            raise ValueError("RUNTIME_VIRTUAL_PROVIDER_COMPARISON_PROOF_REQUIRED")
        denied_flags = {
            "live_model_fanout_enabled": self.live_model_fanout_enabled,
            "provider_sdk_enabled": self.provider_sdk_enabled,
            "external_runtime_dispatch_enabled": self.external_runtime_dispatch_enabled,
            "hidden_advisor_prompts_enabled": self.hidden_advisor_prompts_enabled,
            "raw_prompt_persistence_enabled": self.raw_prompt_persistence_enabled,
            "raw_response_persistence_enabled": self.raw_response_persistence_enabled,
            "output_authority_enabled": self.output_authority_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_VIRTUAL_PROVIDER_PRESET_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_VIRTUAL_PROVIDER_PRESET_BLOCKERS_REQUIRED")
        return self


class RuntimeVirtualProviderMoaReadModel(BaseModel):
    schema_version: str = "runtime_virtual_provider_moa.v1"
    contract_ref: str = RUNTIME_VIRTUAL_PROVIDER_MOA_CONTRACT_REF
    status: str = "read_only_virtual_provider_preset_posture"
    snapshot_ref: str = RUNTIME_VIRTUAL_PROVIDER_MOA_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-virtual-provider-moa:pending"
    route_ref: str = RUNTIME_VIRTUAL_PROVIDER_MOA_ROUTE_REF
    cli_ref: str = RUNTIME_VIRTUAL_PROVIDER_MOA_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    authority_state_route_ref: str
    authority_state_cli_ref: str
    authority_state_mapping_ref: str
    authority_state_catalog_ref: str
    authority_state_decision_ref: str
    authority_state_decision_outcome: str
    authority_state_status: str
    authority_state_operator_message: str
    authority_state_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "Virtual provider presets show multi-agent collaboration posture only; "
        "no model fan-out, provider SDK call, or runtime dispatch is enabled."
    )
    presets: list[RuntimeVirtualProviderPreset]
    preset_count: int = 0
    agent_slot_count: int = 0
    ready_preset_count: int = 0
    blocked_preset_count: int = 0
    live_model_fanout_enabled: bool = False
    provider_sdk_enabled: bool = False
    external_runtime_dispatch_enabled: bool = False
    hidden_advisor_prompts_enabled: bool = False
    raw_prompt_persistence_enabled: bool = False
    raw_response_persistence_enabled: bool = False
    output_authority_enabled: bool = False
    production_authority_enabled: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: (
            list(GOVERNED_RUNTIME_REDACTIONS)
            + [
                "raw_prompts_omitted",
                "raw_responses_omitted",
                "provider_payloads_omitted",
                "advisor_prompts_omitted",
                "agent_outputs_omitted",
            ]
        )
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeVirtualProviderMoaReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.authority_state_mapping_ref, "authority_state_mapping_ref"),
            (self.authority_state_catalog_ref, "authority_state_catalog_ref"),
            (self.authority_state_decision_ref, "authority_state_decision_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "authority_state_reason_refs",
            "unsupported_adapter_refs",
            "blocked_authority_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.authority_state_route_ref, "authority_state_route_ref"),
            (self.authority_state_cli_ref, "authority_state_cli_ref"),
            (
                self.authority_state_decision_outcome,
                "authority_state_decision_outcome",
            ),
            (self.authority_state_status, "authority_state_status"),
            (
                self.authority_state_operator_message,
                "authority_state_operator_message",
            ),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        if self.preset_count != len(self.presets):
            raise ValueError("RUNTIME_VIRTUAL_PROVIDER_PRESET_COUNT_MISMATCH")
        if self.agent_slot_count != sum(preset.slot_count for preset in self.presets):
            raise ValueError("RUNTIME_VIRTUAL_PROVIDER_SLOT_TOTAL_MISMATCH")
        if self.ready_preset_count != len(
            [
                preset
                for preset in self.presets
                if preset.status == RuntimeVirtualProviderPresetStatus.readiness_only.value
            ]
        ):
            raise ValueError("RUNTIME_VIRTUAL_PROVIDER_READY_COUNT_MISMATCH")
        if self.blocked_preset_count != len(
            [
                preset
                for preset in self.presets
                if preset.status
                == RuntimeVirtualProviderPresetStatus.blocked_requires_authority.value
            ]
        ):
            raise ValueError("RUNTIME_VIRTUAL_PROVIDER_BLOCKED_COUNT_MISMATCH")
        if (
            self.authority_state_mapping_ref
            != RUNTIME_VIRTUAL_PROVIDER_MOA_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_VIRTUAL_PROVIDER_MOA_AUTHORITY_MAPPING_MISMATCH")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_VIRTUAL_PROVIDER_MOA_AUTHORITY_DECISION_INVALID")
        denied_flags = {
            "live_model_fanout_enabled": self.live_model_fanout_enabled,
            "provider_sdk_enabled": self.provider_sdk_enabled,
            "external_runtime_dispatch_enabled": self.external_runtime_dispatch_enabled,
            "hidden_advisor_prompts_enabled": self.hidden_advisor_prompts_enabled,
            "raw_prompt_persistence_enabled": self.raw_prompt_persistence_enabled,
            "raw_response_persistence_enabled": self.raw_response_persistence_enabled,
            "output_authority_enabled": self.output_authority_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_VIRTUAL_PROVIDER_MOA_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if RUNTIME_VIRTUAL_PROVIDER_MOA_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_VIRTUAL_PROVIDER_MOA_PROOF_REQUIRED")
        if set(RUNTIME_VIRTUAL_PROVIDER_MOA_BLOCKED_AUTHORITY_REFS) - set(
            self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_VIRTUAL_PROVIDER_MOA_BLOCKERS_REQUIRED")
        return self


def _hash_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-virtual-provider-moa:{digest}"


def _slot(
    *,
    slug: str,
    display_label: str,
    role: RuntimeVirtualAgentRole,
    runtime_ref: str,
    provider_ref: str,
    model_ref: str,
    safe_summary: str,
) -> RuntimeVirtualAgentSlot:
    return RuntimeVirtualAgentSlot(
        slot_ref=f"virtual-agent-slot-ref:{slug}",
        display_label=display_label,
        role=role,
        runtime_ref=runtime_ref,
        provider_ref=provider_ref,
        model_ref=model_ref,
        authority_profile_ref=f"authority-profile-ref:virtual-agent-slot:{slug}:blocked",
        route_decision_trace_ref=f"route-decision-trace-ref:virtual-provider-moa:{slug}",
        cost_estimate_ref=f"cost-estimate-ref:virtual-provider-moa:{slug}:not-executed",
        output_envelope_ref=f"agent-output-envelope-ref:virtual-provider-moa:{slug}:required",
        comparison_proof_ref=f"comparison-proof-ref:virtual-provider-moa:{slug}:required",
        safe_disable_ref=f"safe-disable-ref:virtual-provider-moa:{slug}",
        safe_summary=safe_summary,
        proof_refs=[RUNTIME_VIRTUAL_PROVIDER_MOA_PROOF_REF],
        evidence_refs=[f"evidence-ref:virtual-provider-moa:{slug}"],
        blocked_authority_refs=list(RUNTIME_VIRTUAL_PROVIDER_MOA_BLOCKED_AUTHORITY_REFS),
    )


def _preset(
    *,
    slug: str,
    display_label: str,
    status: RuntimeVirtualProviderPresetStatus,
    safe_summary: str,
    slots: list[RuntimeVirtualAgentSlot],
) -> RuntimeVirtualProviderPreset:
    return RuntimeVirtualProviderPreset(
        preset_ref=f"virtual-provider-preset-ref:{slug}",
        display_label=display_label,
        status=status,
        safe_summary=safe_summary,
        approval_mode_ref=f"approval-mode-ref:virtual-provider-moa:{slug}:future",
        route_decision_trace_ref=f"route-decision-trace-ref:virtual-provider-moa:{slug}",
        cost_estimate_ref=f"cost-estimate-ref:virtual-provider-moa:{slug}:aggregate",
        comparison_proof_ref=f"comparison-proof-ref:virtual-provider-moa:{slug}",
        safe_disable_ref=f"safe-disable-ref:virtual-provider-moa:{slug}",
        slots=slots,
        slot_count=len(slots),
        proof_refs=[RUNTIME_VIRTUAL_PROVIDER_MOA_PROOF_REF],
        evidence_refs=[f"evidence-ref:virtual-provider-moa:{slug}"],
        verifier_refs=["verifier-ref:hermes-runtime-adoption:phase-20"],
        blocked_authority_refs=list(RUNTIME_VIRTUAL_PROVIDER_MOA_BLOCKED_AUTHORITY_REFS),
    )


def _default_presets() -> list[RuntimeVirtualProviderPreset]:
    return [
        _preset(
            slug="codex-implement-claude-review",
            display_label="Codex implementer plus Claude reviewer",
            status=RuntimeVirtualProviderPresetStatus.readiness_only,
            safe_summary=(
                "Preset models a future Codex implementation branch with a "
                "Claude review branch and UAA supervision, but performs no calls."
            ),
            slots=[
                _slot(
                    slug="codex-implementer",
                    display_label="Codex implementer",
                    role=RuntimeVirtualAgentRole.codex_implementer,
                    runtime_ref="runtime-ref:codex:future-governed-adapter",
                    provider_ref="provider-ref:codex:external-future",
                    model_ref="model-ref:codex:implementation-role",
                    safe_summary="Codex slot is proposal metadata only.",
                ),
                _slot(
                    slug="claude-reviewer",
                    display_label="Claude reviewer",
                    role=RuntimeVirtualAgentRole.claude_reviewer,
                    runtime_ref="runtime-ref:claude:future-governed-adapter",
                    provider_ref="provider-ref:anthropic:external-future",
                    model_ref="model-ref:claude:review-role",
                    safe_summary="Claude slot is review metadata only.",
                ),
                _slot(
                    slug="uaa-supervisor-coding",
                    display_label="UAA supervisor",
                    role=RuntimeVirtualAgentRole.uaa_supervisor,
                    runtime_ref="runtime-ref:uaa:local-supervisor",
                    provider_ref="provider-ref:uaa:python-core",
                    model_ref="model-ref:uaa:policy-supervisor",
                    safe_summary="UAA supervisor slot owns policy refs only.",
                ),
            ],
        ),
        _preset(
            slug="hermes-research-local-verify",
            display_label="Hermes researcher plus local verifier",
            status=RuntimeVirtualProviderPresetStatus.metadata_only,
            safe_summary=(
                "Preset models a future Hermes research branch and local verifier "
                "branch without live web, provider, or command execution."
            ),
            slots=[
                _slot(
                    slug="hermes-researcher",
                    display_label="Hermes researcher",
                    role=RuntimeVirtualAgentRole.hermes_researcher,
                    runtime_ref="runtime-ref:hermes-agent:optional-target",
                    provider_ref="provider-ref:hermes:delegated-runtime",
                    model_ref="model-ref:hermes:research-role",
                    safe_summary="Hermes researcher slot is metadata only.",
                ),
                _slot(
                    slug="local-verifier",
                    display_label="Local verifier",
                    role=RuntimeVirtualAgentRole.local_verifier,
                    runtime_ref="runtime-ref:uaa:local-verifier",
                    provider_ref="provider-ref:uaa:python-core",
                    model_ref="model-ref:uaa:verifier-role",
                    safe_summary="Local verifier slot references verifier posture only.",
                ),
            ],
        ),
        _preset(
            slug="security-review-board",
            display_label="Security review board",
            status=RuntimeVirtualProviderPresetStatus.blocked_requires_authority,
            safe_summary=(
                "Preset is blocked until exact security-review runtime slots have "
                "approval, output envelopes, cost refs, and safe-disable coverage."
            ),
            slots=[
                _slot(
                    slug="security-reviewer",
                    display_label="Security reviewer",
                    role=RuntimeVirtualAgentRole.security_reviewer,
                    runtime_ref="runtime-ref:security-reviewer:future",
                    provider_ref="provider-ref:security-reviewer:future",
                    model_ref="model-ref:security-reviewer:future",
                    safe_summary="Security reviewer slot remains blocked.",
                ),
                _slot(
                    slug="uaa-supervisor-security",
                    display_label="UAA safety supervisor",
                    role=RuntimeVirtualAgentRole.uaa_supervisor,
                    runtime_ref="runtime-ref:uaa:safety-supervisor",
                    provider_ref="provider-ref:uaa:python-core",
                    model_ref="model-ref:uaa:safety-supervisor",
                    safe_summary="UAA safety supervisor owns blocked authority refs.",
                ),
            ],
        ),
    ]


def build_runtime_virtual_provider_moa_read_model() -> (
    RuntimeVirtualProviderMoaReadModel
):
    return build_runtime_virtual_provider_moa_read_model_from_authority_catalog(
        authority_decision_catalog=build_authority_decision_catalog()
    )


def build_runtime_virtual_provider_moa_read_model_from_authority_catalog(
    *,
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry],
) -> RuntimeVirtualProviderMoaReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    presets = _default_presets()
    model = RuntimeVirtualProviderMoaReadModel(
        authority_state_route_ref=(
            RUNTIME_VIRTUAL_PROVIDER_MOA_AUTHORITY_STATE_ROUTE_REF
        ),
        authority_state_cli_ref=RUNTIME_VIRTUAL_PROVIDER_MOA_AUTHORITY_STATE_CLI_REF,
        authority_state_mapping_ref=authority_entry.lane_ref,
        authority_state_catalog_ref=authority_entry.catalog_ref,
        authority_state_decision_ref=authority_entry.decision.decision_ref,
        authority_state_decision_outcome=_authority_value(
            authority_entry.decision.outcome
        ),
        authority_state_status=authority_entry.status,
        authority_state_operator_message=authority_entry.decision.operator_message,
        authority_state_reason_refs=list(authority_entry.decision.reason_refs),
        unsupported_adapter_refs=list(authority_entry.unsupported_adapter_refs),
        presets=presets,
        preset_count=len(presets),
        agent_slot_count=sum(preset.slot_count for preset in presets),
        ready_preset_count=len(
            [
                preset
                for preset in presets
                if preset.status == RuntimeVirtualProviderPresetStatus.readiness_only.value
            ]
        ),
        blocked_preset_count=len(
            [
                preset
                for preset in presets
                if preset.status
                == RuntimeVirtualProviderPresetStatus.blocked_requires_authority.value
            ]
        ),
        blocked_authority_refs=list(RUNTIME_VIRTUAL_PROVIDER_MOA_BLOCKED_AUTHORITY_REFS),
        proof_refs=[RUNTIME_VIRTUAL_PROVIDER_MOA_PROOF_REF],
        verifier_refs=["verifier-ref:hermes-runtime-adoption:phase-20"],
        next_safe_action_refs=[
            "next-safe-action-ref:virtual-provider-moa:inspect-presets",
            "next-safe-action-ref:virtual-provider-moa:bind-route-decision-trace",
            "next-safe-action-ref:virtual-provider-moa:keep-live-fanout-blocked",
        ],
    )
    payload = model.model_dump(mode="json", exclude={"snapshot_hash_ref"})
    return model.model_copy(update={"snapshot_hash_ref": _hash_payload(payload)})


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry],
) -> AuthorityDecisionCatalogEntry:
    for entry in authority_decision_catalog:
        if entry.lane_ref == RUNTIME_VIRTUAL_PROVIDER_MOA_AUTHORITY_MAPPING_REF:
            return entry
    raise ValueError("RUNTIME_VIRTUAL_PROVIDER_MOA_AUTHORITY_MAPPING_NOT_FOUND")


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))
