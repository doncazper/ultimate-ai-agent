from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    AuthorityPolicyDecision,
    TrustMode,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.execution.validation import (
    SECRET_LIKE_RE,
    RAW_LOCAL_PATH_RE,
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS
from ultimate_ai_agent.core.time import utc_now


RUNTIME_INTERFACE_MODE_CONTRACT_REF = "contract-ref:runtime-interface-mode:v1"
RUNTIME_INTERFACE_MODE_ROUTE_REF = "GET /api/runtime/interface-mode"
RUNTIME_INTERFACE_MODE_CLI_REF = "uaa runtime inspect-interface-mode"
HERMES_CONTEXT_PACK_CONTRACT_REF = "contract-ref:hermes-context-pack:v1"
HERMES_CONTEXT_PACK_ROUTE_REF = "GET /api/runtime/hermes/context-pack"
HERMES_CONTEXT_PACK_CLI_REF = "uaa runtime inspect-hermes-context-pack"
HERMES_CHAT_ROUTE_REF = "POST /api/runtime/hermes/chat"
HERMES_CHAT_CLI_REF = "uaa runtime hermes-chat"
HERMES_CHAT_AUTHORITY_ACTION_REF = "authority-action-ref:hermes-interface-chat"
HERMES_CHAT_AUTHORITY_LANE_REF = "lane-ref:hermes-interface-chat-exact-cli"
HERMES_CHAT_AUTHORITY_DOMAIN_REF = "authority-domain-ref:workspace"
HERMES_CHAT_AUTHORITY_CAPABILITY_REF = "authority-capability-ref:execute"
HERMES_CHAT_AUTHORITY_REQUIRED_MODE_REF = (
    "authority-mode-ref:approved-safe-local-work-session"
)
HERMES_CHAT_AUTHORITY_REQUIRED_BLOCKED_REF = (
    "blocked-authority:hermes-workspace-execute-authority-required"
)
HERMES_CONTEXT_PACK_REF = "hermes-context-pack-ref:uaa-curated-runtime-interface-mode"
HERMES_CLI_ENV = "UAA_HERMES_CLI_PATH"
HERMES_INTERFACE_MODE_ENABLED_ENV = "UAA_HERMES_INTERFACE_MODE_ENABLED"
HERMES_EXACT_CHAT_ARGV_SHAPE_REF = (
    "argv-shape-ref:hermes-chat-query-quiet-source-uaa-control-center"
)
HERMES_EXACT_STATUS_ARGV_SHAPE_REF = "argv-shape-ref:hermes-status-all"
HERMES_OUTPUT_BYTE_LIMIT = 8_000
HERMES_DEFAULT_TIMEOUT_SECONDS = 8.0
HERMES_STATUS_TIMEOUT_SECONDS = 3.0
HERMES_FORBIDDEN_QUERY_FRAGMENTS = (
    "--yolo",
    "--oneshot",
    "--toolset",
    "--toolsets",
    "--tools",
    "--system",
    "--prompt-file",
    ";",
    "&&",
    "||",
    "|",
    "`",
    "$(",
)
HERMES_INTERFACE_MODE_BLOCKED_AUTHORITY_REFS = (
    "blocked-authority:hermes-unrestricted-command-execution",
    "blocked-authority:hermes-arbitrary-args",
    "blocked-authority:hermes-yolo-mode",
    "blocked-authority:hermes-oneshot-mode",
    "blocked-authority:hermes-toolset-passthrough",
    "blocked-authority:hermes-shell-string-execution",
    "blocked-authority:hermes-raw-prompt-persistence",
    "blocked-authority:hermes-raw-output-persistence",
    "blocked-authority:hermes-direct-memory-write",
    "blocked-authority:browser-automation",
    "blocked-authority:connector-write",
    "blocked-authority:production-authority",
)
HERMES_INTERFACE_MODE_REDACTIONS = (
    *GOVERNED_RUNTIME_REDACTIONS,
    "hermes_query_hashed_only",
    "hermes_output_summary_only",
    "hermes_cli_path_hashed_only",
    "uaa_memory_curated_summary_only",
    "hermes_memory_updates_candidate_only",
)


class RuntimeInterfaceMode(str, Enum):
    disabled = "disabled"
    shell_guarded = "shell_guarded"
    operator_override = "operator_override"
    pure_hermes_pass_through = "pure_hermes_pass_through"


class HermesCliStatus(str, Enum):
    ready = "ready"
    missing = "missing"
    unavailable = "unavailable"
    blocked = "blocked"


class HermesChatStatus(str, Enum):
    receipt_recorded = "receipt_recorded"
    blocked = "blocked"
    external_handoff_only = "external_handoff_only"
    unavailable = "unavailable"


@dataclass(frozen=True)
class HermesProcessResult:
    exit_code: int | None
    timed_out: bool
    duration_ms: int
    output_bytes: bytes
    error_category: str | None = None


class HermesProcessRunner(Protocol):
    def __call__(
        self,
        *,
        argv: tuple[str, ...],
        cwd: Path,
        env: dict[str, str],
        timeout_seconds: float,
        output_byte_limit: int,
    ) -> HermesProcessResult:
        ...


class HermesCliPostureReadModel(BaseModel):
    schema_version: str = "hermes_cli_posture.v1"
    cli_ref: str
    discovery_source: str
    status: HermesCliStatus
    readiness_command_shape_ref: str = HERMES_EXACT_STATUS_ARGV_SHAPE_REF
    chat_command_shape_ref: str = HERMES_EXACT_CHAT_ARGV_SHAPE_REF
    readiness_checked: bool = False
    readiness_exit_code: int | None = None
    readiness_timed_out: bool = False
    readiness_output_summary: str | None = None
    readiness_output_persisted: bool = False
    cli_path_persisted: bool = False
    exact_argv_only: bool = True
    shell_strings_allowed: bool = False
    yolo_allowed: bool = False
    oneshot_allowed: bool = False
    arbitrary_args_allowed: bool = False
    toolset_passthrough_allowed: bool = False
    safe_summary: str
    blocked_reason_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_posture(self) -> "HermesCliPostureReadModel":
        for ref in [
            self.cli_ref,
            self.readiness_command_shape_ref,
            self.chat_command_shape_ref,
            *self.blocked_reason_refs,
        ]:
            validate_execution_ref(ref, "hermes_cli_posture_ref")
        for value in [
            self.schema_version,
            self.discovery_source,
            self.safe_summary,
            self.readiness_output_summary or "readiness-summary-ref:not-checked",
        ]:
            validate_safe_execution_text(value, "hermes_cli_posture_text")
        if self.readiness_output_persisted or self.cli_path_persisted:
            raise ValueError("HERMES_CLI_RAW_PERSISTENCE_DENIED")
        if not self.exact_argv_only or self.shell_strings_allowed:
            raise ValueError("HERMES_CLI_EXACT_ARGV_REQUIRED")
        if self.yolo_allowed or self.oneshot_allowed:
            raise ValueError("HERMES_CLI_UNSAFE_MODE_DENIED")
        if self.arbitrary_args_allowed or self.toolset_passthrough_allowed:
            raise ValueError("HERMES_CLI_ARBITRARY_ARGS_DENIED")
        return self


class RuntimeInterfaceModeProfile(BaseModel):
    mode: RuntimeInterfaceMode
    status: str
    uaa_native_agent_enabled: bool = False
    uaa_planning_enabled: bool = False
    uaa_execution_enabled: bool = False
    uaa_redaction_receipts_enabled: bool
    hermes_cli_chat_enabled: bool
    external_handoff_only: bool = False
    operator_submission_required: bool
    safe_summary: str
    allowed_action_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_profile(self) -> "RuntimeInterfaceModeProfile":
        if self.uaa_native_agent_enabled or self.uaa_planning_enabled or self.uaa_execution_enabled:
            raise ValueError("RUNTIME_INTERFACE_UAA_NATIVE_AGENT_MUST_BE_OFF")
        for value in [
            self.status,
            self.safe_summary,
        ]:
            validate_safe_execution_text(value, "runtime_interface_profile_text")
        for ref in [*self.allowed_action_refs, *self.blocked_authority_refs]:
            validate_execution_ref(ref, "runtime_interface_profile_ref")
        if self.mode == RuntimeInterfaceMode.pure_hermes_pass_through.value:
            if self.hermes_cli_chat_enabled or not self.external_handoff_only:
                raise ValueError("RUNTIME_INTERFACE_PURE_HANDOFF_EXECUTION_DENIED")
        return self


class RuntimeInterfaceModeReadModel(BaseModel):
    schema_version: str = "runtime_interface_mode.v1"
    contract_ref: str = RUNTIME_INTERFACE_MODE_CONTRACT_REF
    route_ref: str = RUNTIME_INTERFACE_MODE_ROUTE_REF
    cli_ref: str = RUNTIME_INTERFACE_MODE_CLI_REF
    status: str = "active_shell_over_external_runtime"
    active_mode: RuntimeInterfaceMode = RuntimeInterfaceMode.disabled
    interface_enabled: bool = False
    mode_profiles: list[RuntimeInterfaceModeProfile]
    hermes_cli_posture: HermesCliPostureReadModel
    context_pack_ref: str = HERMES_CONTEXT_PACK_REF
    memory_update_policy: str = "candidate_only_review_required"
    control_center_mints_authority: bool = False
    python_core_owns_truth: bool = True
    uaa_native_agent_enabled: bool = False
    uaa_planning_enabled: bool = False
    uaa_execution_enabled: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_provider_payload_persisted: bool = False
    raw_log_persisted: bool = False
    raw_local_path_persisted: bool = False
    credential_material_persisted: bool = False
    safe_summary: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(HERMES_INTERFACE_MODE_REDACTIONS)
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeInterfaceModeReadModel":
        for ref in [
            self.contract_ref,
            self.context_pack_ref,
            *self.blocked_authority_refs,
            *self.evidence_refs,
            *self.proof_refs,
        ]:
            validate_execution_ref(ref, "runtime_interface_ref")
        for value in [
            self.schema_version,
            self.route_ref,
            self.cli_ref,
            self.status,
            self.memory_update_policy,
            self.safe_summary,
            *self.redactions_applied,
        ]:
            validate_safe_execution_text(value, "runtime_interface_text")
        if self.control_center_mints_authority:
            raise ValueError("CONTROL_CENTER_AUTHORITY_MINTING_DENIED")
        if self.uaa_native_agent_enabled or self.uaa_planning_enabled or self.uaa_execution_enabled:
            raise ValueError("RUNTIME_INTERFACE_UAA_NATIVE_AGENT_MUST_BE_OFF")
        if any(
            [
                self.raw_prompt_persisted,
                self.raw_response_persisted,
                self.raw_provider_payload_persisted,
                self.raw_log_persisted,
                self.raw_local_path_persisted,
                self.credential_material_persisted,
            ]
        ):
            raise ValueError("RUNTIME_INTERFACE_RAW_PERSISTENCE_DENIED")
        return self


class HermesContextSectionReadModel(BaseModel):
    section_ref: str
    source_surface: str
    projected_to_hermes: bool = True
    uaa_native_source_ref: str
    safe_summary: str
    provenance_refs: list[str] = Field(default_factory=list)
    why_shown_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    route_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_section(self) -> "HermesContextSectionReadModel":
        for ref in [
            self.section_ref,
            self.uaa_native_source_ref,
            *self.provenance_refs,
            *self.why_shown_refs,
            *self.evidence_refs,
            *self.proof_refs,
        ]:
            validate_execution_ref(ref, "hermes_context_section_ref")
        for value in [self.source_surface, self.safe_summary, *self.route_refs]:
            validate_safe_execution_text(value, "hermes_context_section_text")
        if not self.projected_to_hermes:
            raise ValueError("HERMES_CONTEXT_SECTION_PROJECTION_REQUIRED")
        return self


class HermesContextPackReadModel(BaseModel):
    schema_version: str = "hermes_context_pack.v1"
    contract_ref: str = HERMES_CONTEXT_PACK_CONTRACT_REF
    context_pack_ref: str = HERMES_CONTEXT_PACK_REF
    route_ref: str = HERMES_CONTEXT_PACK_ROUTE_REF
    cli_ref: str = HERMES_CONTEXT_PACK_CLI_REF
    status: str = "curated_redacted_context_ready"
    projection_enabled: bool = True
    built_at_ref: str = Field(default_factory=lambda: _hash_ref("time-ref", utc_now().isoformat()))
    source_count: int
    section_count: int
    sections: list[HermesContextSectionReadModel]
    token_budget_ref: str = "context-budget-ref:hermes-interface-mode-bounded"
    safe_summary: str
    memory_update_policy: str = "candidate_only_review_required"
    hermes_receives_raw_database_access: bool = False
    raw_memory_records_exposed: bool = False
    raw_crm_records_exposed: bool = False
    raw_chat_transcripts_exposed: bool = False
    raw_local_paths_exposed: bool = False
    raw_logs_exposed: bool = False
    credential_material_exposed: bool = False
    unbounded_private_content_exposed: bool = False
    direct_memory_write_enabled: bool = False
    projected_provenance_visible: bool = True
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(HERMES_INTERFACE_MODE_REDACTIONS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_context_pack(self) -> "HermesContextPackReadModel":
        for ref in [
            self.contract_ref,
            self.context_pack_ref,
            self.built_at_ref,
            self.token_budget_ref,
            *self.evidence_refs,
            *self.proof_refs,
        ]:
            validate_execution_ref(ref, "hermes_context_pack_ref")
        for value in [
            self.schema_version,
            self.route_ref,
            self.cli_ref,
            self.status,
            self.safe_summary,
            self.memory_update_policy,
            *self.redactions_applied,
        ]:
            validate_safe_execution_text(value, "hermes_context_pack_text")
        if self.section_count != len(self.sections) or self.source_count != len(self.sections):
            raise ValueError("HERMES_CONTEXT_PACK_COUNT_MISMATCH")
        if any(
            [
                self.hermes_receives_raw_database_access,
                self.raw_memory_records_exposed,
                self.raw_crm_records_exposed,
                self.raw_chat_transcripts_exposed,
                self.raw_local_paths_exposed,
                self.raw_logs_exposed,
                self.credential_material_exposed,
                self.unbounded_private_content_exposed,
                self.direct_memory_write_enabled,
            ]
        ):
            raise ValueError("HERMES_CONTEXT_PACK_RAW_ACCESS_DENIED")
        return self


class HermesChatRequest(BaseModel):
    schema_version: str = "hermes_chat_request.v1"
    mode: RuntimeInterfaceMode = RuntimeInterfaceMode.shell_guarded
    query: str = Field(..., min_length=1, max_length=4_000)
    context_pack_ref: str = HERMES_CONTEXT_PACK_REF
    mission_ref: str | None = None
    operator_submission_acknowledged: bool = False
    raw_prompt_persisted: bool = False
    raw_output_persisted: bool = False
    arbitrary_args_requested: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_chat_request(self) -> "HermesChatRequest":
        validate_safe_execution_text(self.schema_version, "schema_version")
        validate_execution_ref(self.context_pack_ref, "context_pack_ref")
        if self.mission_ref:
            validate_execution_ref(self.mission_ref, "mission_ref")
        _validate_hermes_query(self.query)
        if self.mode == RuntimeInterfaceMode.operator_override.value:
            if not self.operator_submission_acknowledged:
                raise ValueError("HERMES_OPERATOR_OVERRIDE_ACK_REQUIRED")
        if self.raw_prompt_persisted or self.raw_output_persisted:
            raise ValueError("HERMES_CHAT_RAW_PERSISTENCE_DENIED")
        if self.arbitrary_args_requested:
            raise ValueError("HERMES_CHAT_ARBITRARY_ARGS_DENIED")
        return self


class HermesChatReceiptReadModel(BaseModel):
    schema_version: str = "hermes_chat_receipt.v1"
    receipt_ref: str
    status: HermesChatStatus
    mode: RuntimeInterfaceMode
    query_ref: str
    context_pack_ref: str = HERMES_CONTEXT_PACK_REF
    hermes_cli_ref: str
    exact_argv_shape_ref: str = HERMES_EXACT_CHAT_ARGV_SHAPE_REF
    idempotency_ref: str
    execution_performed: bool
    external_handoff_only: bool = False
    operator_override_used: bool = False
    unsafe_arg_blocked: bool = False
    exit_code: int | None = None
    timed_out: bool = False
    duration_ms: int | None = None
    output_summary: str | None = None
    output_ref: str | None = None
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_output_persisted: bool = False
    raw_local_path_persisted: bool = False
    hidden_output_persistence_enabled: bool = False
    model_output_authority: str = "untrusted_external_proposal_only"
    memory_update_policy: str = "candidate_only_review_required"
    blocked_reason_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    authority_decision_ref: str | None = None
    authority_decision_outcome: str | None = None
    authority_lease_ref: str | None = None
    authority_domain_ref: str | None = None
    authority_capability_ref: str | None = None
    authority_required_mode_ref: str | None = None
    authority_audit_ref: str | None = None
    authority_policy_receipt_ref: str | None = None
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(HERMES_INTERFACE_MODE_REDACTIONS)
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> "HermesChatReceiptReadModel":
        for ref in [
            self.receipt_ref,
            self.query_ref,
            self.context_pack_ref,
            self.hermes_cli_ref,
            self.exact_argv_shape_ref,
            self.idempotency_ref,
        ]:
            validate_execution_ref(ref, "hermes_chat_receipt_ref")
        if self.output_ref:
            validate_execution_ref(self.output_ref, "hermes_output_ref")
        for ref in [*self.blocked_reason_refs, *self.evidence_refs, *self.proof_refs]:
            validate_execution_ref(ref, "hermes_chat_receipt_ref")
        for ref in [
            self.authority_decision_ref,
            self.authority_lease_ref,
            self.authority_domain_ref,
            self.authority_capability_ref,
            self.authority_required_mode_ref,
            self.authority_audit_ref,
            self.authority_policy_receipt_ref,
        ]:
            if ref:
                validate_execution_ref(ref, "hermes_chat_authority_ref")
        for value in [
            self.schema_version,
            self.model_output_authority,
            self.memory_update_policy,
            self.output_summary or "output-summary-ref:none",
            self.authority_decision_outcome or "authority-decision-outcome:none",
            *self.redactions_applied,
        ]:
            validate_safe_execution_text(value, "hermes_chat_receipt_text")
        if any(
            [
                self.raw_prompt_persisted,
                self.raw_response_persisted,
                self.raw_output_persisted,
                self.raw_local_path_persisted,
                self.hidden_output_persistence_enabled,
            ]
        ):
            raise ValueError("HERMES_CHAT_RAW_PERSISTENCE_DENIED")
        if self.external_handoff_only and self.execution_performed:
            raise ValueError("HERMES_PASS_THROUGH_EXECUTION_DENIED")
        if self.execution_performed:
            if self.authority_decision_outcome != AuthorityDecisionOutcome.allow.value:
                raise ValueError("HERMES_EXECUTION_REQUIRES_AUTHORITY_ALLOW")
            if not self.authority_lease_ref:
                raise ValueError("HERMES_EXECUTION_REQUIRES_AUTHORITY_LEASE")
        return self


class HermesCliAdapter:
    def __init__(
        self,
        *,
        runner: HermesProcessRunner | None = None,
        cwd: Path | None = None,
    ) -> None:
        self._runner = runner or _blocked_hermes_runner
        self._cwd = cwd or Path.cwd()

    def discover_cli(self) -> tuple[Path | None, str, str]:
        env_value = os.getenv(HERMES_CLI_ENV)
        if env_value:
            candidate = Path(env_value).expanduser()
            return (
                candidate if _is_executable_file(candidate) else None,
                "env",
                _hash_ref("hermes-cli-ref", {"source": "env", "value": str(candidate)}),
            )
        resolved = shutil.which("hermes")
        if resolved:
            return (
                Path(resolved),
                "path",
                _hash_ref("hermes-cli-ref", {"source": "path", "value": resolved}),
            )
        return None, "not_found", "hermes-cli-ref:not-found"

    def readiness(self) -> HermesCliPostureReadModel:
        if not is_hermes_interface_mode_enabled():
            return _disabled_hermes_cli_posture()
        cli_path, discovery_source, cli_ref = self.discover_cli()
        if cli_path is None:
            return HermesCliPostureReadModel(
                cli_ref=cli_ref,
                discovery_source=discovery_source,
                status=HermesCliStatus.missing,
                safe_summary=(
                    "Hermes CLI is not configured; interface mode can still show "
                    "external handoff posture without executing Hermes."
                ),
                blocked_reason_refs=["blocked-authority:hermes-cli-not-configured"],
            )
        result = self._runner(
            argv=(str(cli_path), "status", "--all"),
            cwd=self._cwd,
            env=_minimal_env(),
            timeout_seconds=HERMES_STATUS_TIMEOUT_SECONDS,
            output_byte_limit=HERMES_OUTPUT_BYTE_LIMIT,
        )
        status = (
            HermesCliStatus.ready
            if result.exit_code == 0 and not result.timed_out and result.error_category is None
            else HermesCliStatus.unavailable
        )
        return HermesCliPostureReadModel(
            cli_ref=cli_ref,
            discovery_source=discovery_source,
            status=status,
            readiness_checked=True,
            readiness_exit_code=result.exit_code,
            readiness_timed_out=result.timed_out,
            readiness_output_summary=_output_summary(result.output_bytes),
            safe_summary=(
                "Hermes CLI readiness was checked with exact status argv; output "
                "is summarized and not persisted."
            ),
            blocked_reason_refs=[] if status == HermesCliStatus.ready else [
                "blocked-authority:hermes-cli-readiness-unavailable"
            ],
        )

    def chat(
        self,
        request: HermesChatRequest,
        *,
        idempotency_ref: str,
        active_authority_leases: list[AuthorityLease] | None = None,
    ) -> HermesChatReceiptReadModel:
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        if not is_hermes_interface_mode_enabled():
            return _hermes_blocked_receipt(
                request,
                idempotency_ref,
                cli_ref="hermes-cli-ref:interface-mode-disabled",
                status=HermesChatStatus.blocked,
                blocked_reason_refs=["blocked-authority:hermes-interface-mode-disabled"],
                output_summary=(
                    "Hermes interface mode is disabled; UAA stayed UAA-native and "
                    "did not discover, probe, or execute Hermes."
                ),
            )
        if request.mode == RuntimeInterfaceMode.pure_hermes_pass_through.value:
            return _hermes_external_handoff_receipt(request, idempotency_ref)
        authority_decision = _hermes_chat_authority_decision(
            request,
            active_authority_leases or [],
        )
        if authority_decision.outcome != AuthorityDecisionOutcome.allow.value:
            return _hermes_blocked_receipt(
                request,
                idempotency_ref,
                cli_ref="hermes-cli-ref:authority-not-evaluated",
                status=HermesChatStatus.blocked,
                blocked_reason_refs=list(
                    dict.fromkeys(
                        [
                            HERMES_CHAT_AUTHORITY_REQUIRED_BLOCKED_REF,
                            *authority_decision.reason_refs,
                            *authority_decision.required_domain_refs,
                            *authority_decision.required_capability_refs,
                        ]
                    )
                ),
                output_summary=(
                    "Hermes CLI chat requires active Workspace execute "
                    "AuthorityLease scope before UAA discovers or executes Hermes."
                ),
                authority_decision=authority_decision,
            )
        cli_path, discovery_source, cli_ref = self.discover_cli()
        if cli_path is None:
            return _hermes_blocked_receipt(
                request,
                idempotency_ref,
                cli_ref=cli_ref,
                status=HermesChatStatus.unavailable,
                blocked_reason_refs=["blocked-authority:hermes-cli-not-configured"],
                output_summary=(
                    "Hermes CLI is not configured; no Hermes chat execution occurred."
                ),
                authority_decision=authority_decision,
            )
        del discovery_source
        try:
            _validate_hermes_query(request.query)
        except ValueError:
            return _hermes_blocked_receipt(
                request,
                idempotency_ref,
                cli_ref=cli_ref,
                status=HermesChatStatus.blocked,
                unsafe_arg_blocked=True,
                blocked_reason_refs=["blocked-authority:hermes-unsafe-query-fragment"],
                output_summary=(
                    "Hermes chat was blocked before execution because the transient "
                    "query included unsafe command-shaped content."
                ),
                authority_decision=authority_decision,
            )
        result = self._runner(
            argv=(
                str(cli_path),
                "chat",
                "--query",
                request.query,
                "--quiet",
                "--source",
                "uaa-control-center",
            ),
            cwd=self._cwd,
            env=_minimal_env(),
            timeout_seconds=HERMES_DEFAULT_TIMEOUT_SECONDS,
            output_byte_limit=HERMES_OUTPUT_BYTE_LIMIT,
        )
        output_summary = _output_summary(result.output_bytes)
        output_ref = _hash_ref(
            "hermes-output-ref",
            {
                "mode": request.mode,
                "exit_code": result.exit_code,
                "timed_out": result.timed_out,
                "bytes": len(result.output_bytes),
                "digest": hashlib.sha256(result.output_bytes).hexdigest(),
            },
        )
        status = (
            HermesChatStatus.receipt_recorded
            if result.error_category is None and not result.timed_out
            else HermesChatStatus.unavailable
        )
        blocked = []
        if status != HermesChatStatus.receipt_recorded:
            blocked.append("blocked-authority:hermes-chat-runner-unavailable")
        return HermesChatReceiptReadModel(
            receipt_ref=_chat_receipt_ref(request, idempotency_ref, status=status),
            status=status,
            mode=request.mode,
            query_ref=_query_ref(request.query),
            context_pack_ref=request.context_pack_ref,
            hermes_cli_ref=cli_ref,
            idempotency_ref=idempotency_ref,
            execution_performed=status == HermesChatStatus.receipt_recorded,
            operator_override_used=request.mode == RuntimeInterfaceMode.operator_override.value,
            exit_code=result.exit_code,
            timed_out=result.timed_out,
            duration_ms=result.duration_ms,
            output_summary=output_summary,
            output_ref=output_ref,
            blocked_reason_refs=blocked,
            evidence_refs=["evidence-ref:hermes-interface-mode-chat-receipt"],
            proof_refs=["proof-ref:hermes-interface-mode-exact-argv"],
            authority_decision_ref=authority_decision.decision_ref,
            authority_decision_outcome=authority_decision.outcome,
            authority_lease_ref=authority_decision.lease_ref,
            authority_domain_ref=HERMES_CHAT_AUTHORITY_DOMAIN_REF,
            authority_capability_ref=HERMES_CHAT_AUTHORITY_CAPABILITY_REF,
            authority_required_mode_ref=HERMES_CHAT_AUTHORITY_REQUIRED_MODE_REF,
            authority_audit_ref=authority_decision.audit_record_ref,
            authority_policy_receipt_ref=authority_decision.receipt_ref,
        )


def build_runtime_interface_mode_read_model(
    adapter: HermesCliAdapter | None = None,
) -> RuntimeInterfaceModeReadModel:
    hermes = adapter or HermesCliAdapter()
    interface_enabled = is_hermes_interface_mode_enabled()
    profiles = [
        RuntimeInterfaceModeProfile(
            mode=RuntimeInterfaceMode.disabled,
            status="disabled_uaa_native_only",
            uaa_redaction_receipts_enabled=False,
            hermes_cli_chat_enabled=False,
            operator_submission_required=True,
            safe_summary=(
                "Hermes interface mode is off by default; UAA remains UAA-native "
                "and does not discover, probe, or execute Hermes."
            ),
            allowed_action_refs=[],
            blocked_authority_refs=[
                "blocked-authority:hermes-interface-mode-disabled",
                *HERMES_INTERFACE_MODE_BLOCKED_AUTHORITY_REFS,
            ],
        ),
        RuntimeInterfaceModeProfile(
            mode=RuntimeInterfaceMode.shell_guarded,
            status="available_when_explicitly_enabled",
            uaa_redaction_receipts_enabled=True,
            hermes_cli_chat_enabled=interface_enabled,
            operator_submission_required=True,
            safe_summary=(
                "UAA native agent planning is off; UAA keeps redaction, receipts, "
                "status, stop posture, and exact scoped Hermes CLI chat."
            ),
            allowed_action_refs=["action-ref:hermes-cli-chat-exact-argv"],
            blocked_authority_refs=list(HERMES_INTERFACE_MODE_BLOCKED_AUTHORITY_REFS),
        ),
        RuntimeInterfaceModeProfile(
            mode=RuntimeInterfaceMode.operator_override,
            status="available_when_explicitly_enabled",
            uaa_redaction_receipts_enabled=True,
            hermes_cli_chat_enabled=interface_enabled,
            operator_submission_required=True,
            safe_summary=(
                "Operator override submits explicitly to Hermes with weaker UAA "
                "governance labeling; UAA still denies raw persistence and unsafe args."
            ),
            allowed_action_refs=["action-ref:hermes-cli-chat-operator-submission"],
            blocked_authority_refs=list(HERMES_INTERFACE_MODE_BLOCKED_AUTHORITY_REFS),
        ),
        RuntimeInterfaceModeProfile(
            mode=RuntimeInterfaceMode.pure_hermes_pass_through,
            status="external_handoff_only",
            uaa_redaction_receipts_enabled=False,
            hermes_cli_chat_enabled=False,
            external_handoff_only=True,
            operator_submission_required=True,
            safe_summary=(
                "Pure Hermes pass-through is visible external handoff only; UAA "
                "does not execute unrestricted Hermes commands."
            ),
            allowed_action_refs=["action-ref:external-hermes-handoff-visible-only"],
            blocked_authority_refs=list(HERMES_INTERFACE_MODE_BLOCKED_AUTHORITY_REFS),
        ),
    ]
    return RuntimeInterfaceModeReadModel(
        status=(
            "active_shell_over_external_runtime"
            if interface_enabled
            else "disabled_uaa_native_only"
        ),
        active_mode=(
            RuntimeInterfaceMode.shell_guarded
            if interface_enabled
            else RuntimeInterfaceMode.disabled
        ),
        interface_enabled=interface_enabled,
        mode_profiles=profiles,
        hermes_cli_posture=hermes.readiness(),
        safe_summary=(
            "Runtime interface mode is disabled; UAA remains UAA-native and Hermes "
            "is removable without changing the core operator loop."
            if not interface_enabled
            else "Runtime interface mode lets Control Center supervise Hermes as an "
            "external runtime while UAA-native agent planning and execution stay off."
        ),
        blocked_authority_refs=(
            [
                "blocked-authority:hermes-interface-mode-disabled",
                *HERMES_INTERFACE_MODE_BLOCKED_AUTHORITY_REFS,
            ]
            if not interface_enabled
            else list(HERMES_INTERFACE_MODE_BLOCKED_AUTHORITY_REFS)
        ),
        evidence_refs=["evidence-ref:runtime-interface-mode:python-core-contract"],
        proof_refs=["proof-ref:runtime-interface-mode:uaa-memory-bridge"],
    )


def build_hermes_context_pack_read_model() -> HermesContextPackReadModel:
    if not is_hermes_interface_mode_enabled():
        return HermesContextPackReadModel(
            status="disabled_uaa_native_only",
            projection_enabled=False,
            source_count=0,
            section_count=0,
            sections=[],
            safe_summary=(
                "Hermes context projection is disabled; UAA does not build a Hermes "
                "context pack and continues using UAA-native memory, evidence, and proof."
            ),
            projected_provenance_visible=False,
            evidence_refs=["evidence-ref:hermes-context-pack:disabled"],
            proof_refs=["proof-ref:hermes-context-pack:disabled"],
        )
    sections = [
        _context_section(
            "memory",
            "Memory Review and reviewed context",
            "Safe memory posture, candidate-review status, and retrieval refs only.",
            "GET /control-center/memory/review",
            "memory-source-ref:reviewed-context",
        ),
        _context_section(
            "crm",
            "CRM local command center",
            "Relationship and follow-up posture as redacted summaries; raw contact records stay out.",
            "GET /control-center/crm/summary",
            "crm-source-ref:local-command-center",
        ),
        _context_section(
            "chat",
            "Chat turns and handoffs",
            "Conversation continuity refs and receipt posture only; raw transcripts stay out.",
            "GET /control-center/chat/turns",
            "chat-source-ref:durable-turn-receipts",
        ),
        _context_section(
            "cowork-plans",
            "Cowork and Plans",
            "Current plan refs, handoff state, and operator intent summaries only.",
            "GET /control-center/agent-loop/thread",
            "plan-source-ref:founder-loop-thread",
        ),
        _context_section(
            "today",
            "Today",
            "Today loop priorities and current work posture as safe refs.",
            "GET /control-center/today/summary",
            "today-source-ref:founder-loop",
        ),
        _context_section(
            "action-inbox",
            "Action Inbox",
            "Action envelope refs, approval posture, and blocked states only.",
            "GET /control-center/actions/inbox",
            "action-source-ref:founder-actions-inbox",
        ),
        _context_section(
            "evidence",
            "Evidence",
            "Evidence timeline refs and receipt posture only.",
            "GET /control-center/evidence/timeline",
            "evidence-source-ref:founder-loop-timeline",
        ),
        _context_section(
            "proof",
            "Proof",
            "Proof index refs and verifier posture only.",
            "GET /control-center/proof/index",
            "proof-source-ref:control-center-proof-index",
        ),
        _context_section(
            "sources",
            "Sources",
            "Source readiness, why-shown refs, and connector-read posture only.",
            "GET /control-center/sources/readiness",
            "source-readiness-ref:founder-loop-sources",
        ),
    ]
    return HermesContextPackReadModel(
        source_count=len(sections),
        section_count=len(sections),
        sections=sections,
        safe_summary=(
            "Hermes receives a curated UAA context pack with redacted summaries, "
            "provenance refs, why-shown refs, evidence refs, and proof refs only."
        ),
        evidence_refs=["evidence-ref:hermes-context-pack:redacted-bridge"],
        proof_refs=["proof-ref:hermes-context-pack:no-raw-memory-access"],
    )


def verify_hermes_interface_mode_contract() -> dict[str, object]:
    previous_enabled = os.environ.get(HERMES_INTERFACE_MODE_ENABLED_ENV)
    try:
        os.environ.pop(HERMES_INTERFACE_MODE_ENABLED_ENV, None)
        disabled_interface = build_runtime_interface_mode_read_model(
            adapter=HermesCliAdapter(runner=_no_hermes_runner)
        )
        disabled_context_pack = build_hermes_context_pack_read_model()
        os.environ[HERMES_INTERFACE_MODE_ENABLED_ENV] = "1"
        interface = build_runtime_interface_mode_read_model(
            adapter=HermesCliAdapter(runner=_no_hermes_runner)
        )
        context_pack = build_hermes_context_pack_read_model()
        pass_through_receipt = HermesCliAdapter(runner=_no_hermes_runner).chat(
            HermesChatRequest(
                mode=RuntimeInterfaceMode.pure_hermes_pass_through,
                query="external handoff only",
                operator_submission_acknowledged=True,
            ),
            idempotency_ref="idempotency-ref:hermes-interface-verifier",
        )
    finally:
        if previous_enabled is None:
            os.environ.pop(HERMES_INTERFACE_MODE_ENABLED_ENV, None)
        else:
            os.environ[HERMES_INTERFACE_MODE_ENABLED_ENV] = previous_enabled
    return {
        "schema_version": "hermes_interface_mode_verifier.v1",
        "contract_ref": RUNTIME_INTERFACE_MODE_CONTRACT_REF,
        "default_disabled": (
            disabled_interface.active_mode == RuntimeInterfaceMode.disabled.value
            and not disabled_interface.interface_enabled
            and not disabled_context_pack.projection_enabled
        ),
        "uaa_native_agent_execution_off": not interface.uaa_execution_enabled,
        "uaa_native_agent_planning_off": not interface.uaa_planning_enabled,
        "context_curated_redacted": (
            not context_pack.raw_memory_records_exposed
            and not context_pack.raw_crm_records_exposed
            and not context_pack.raw_chat_transcripts_exposed
            and not context_pack.raw_local_paths_exposed
        ),
        "direct_memory_write_enabled": context_pack.direct_memory_write_enabled,
        "pass_through_external_only": (
            pass_through_receipt.external_handoff_only
            and not pass_through_receipt.execution_performed
        ),
        "unsafe_passthrough_blocked": (
            "blocked-authority:hermes-pass-through-execution"
            in pass_through_receipt.blocked_reason_refs
        ),
        "safe_refs_only": True,
        "raw_prompt_persisted": False,
        "raw_response_persisted": False,
        "raw_logs_persisted": False,
        "raw_local_paths_persisted": False,
    }


def _context_section(
    key: str,
    label: str,
    summary: str,
    route_ref: str,
    source_ref: str,
) -> HermesContextSectionReadModel:
    section_ref = f"hermes-context-section-ref:{key}"
    return HermesContextSectionReadModel(
        section_ref=section_ref,
        source_surface=label,
        uaa_native_source_ref=source_ref,
        safe_summary=summary,
        provenance_refs=[source_ref],
        why_shown_refs=[f"why-shown-ref:hermes-context:{key}:current-operator-loop"],
        evidence_refs=[f"evidence-ref:hermes-context:{key}"],
        proof_refs=[f"proof-ref:hermes-context:{key}:redacted"],
        route_refs=[route_ref],
    )


def _is_executable_file(candidate: Path) -> bool:
    try:
        return candidate.is_file() and os.access(candidate, os.X_OK)
    except OSError:
        return False


def is_hermes_interface_mode_enabled() -> bool:
    return os.getenv(HERMES_INTERFACE_MODE_ENABLED_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _disabled_hermes_cli_posture() -> HermesCliPostureReadModel:
    return HermesCliPostureReadModel(
        cli_ref="hermes-cli-ref:interface-mode-disabled",
        discovery_source="disabled",
        status=HermesCliStatus.blocked,
        readiness_checked=False,
        safe_summary=(
            "Hermes interface mode is disabled by default; no Hermes CLI discovery "
            "or readiness command was run."
        ),
        blocked_reason_refs=["blocked-authority:hermes-interface-mode-disabled"],
    )


def _validate_hermes_query(query: str) -> None:
    validate_safe_execution_text(query, "hermes_query")
    if SECRET_LIKE_RE.search(query) or RAW_LOCAL_PATH_RE.search(query):
        raise ValueError("HERMES_QUERY_PRIVATE_CONTENT_DENIED")
    lowered = query.lower()
    if any(fragment in lowered for fragment in HERMES_FORBIDDEN_QUERY_FRAGMENTS):
        raise ValueError("HERMES_QUERY_UNSAFE_FRAGMENT_DENIED")


def _minimal_env() -> dict[str, str]:
    env: dict[str, str] = {}
    for name in ("PATH", "HOME", "TMPDIR"):
        value = os.getenv(name)
        if value:
            env[name] = value
    env["UAA_RUNTIME_INTERFACE_MODE"] = "shell_guarded"
    return env


def _blocked_hermes_runner(
    *,
    argv: tuple[str, ...],
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: float,
    output_byte_limit: int,
) -> HermesProcessResult:
    del argv, cwd, env, timeout_seconds, output_byte_limit
    return HermesProcessResult(
        exit_code=None,
        timed_out=False,
        duration_ms=0,
        output_bytes=b"",
        error_category="HERMES_CLI_EXECUTION_BLOCKED_BY_DEFAULT",
    )


def _no_hermes_runner(
    *,
    argv: tuple[str, ...],
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: float,
    output_byte_limit: int,
) -> HermesProcessResult:
    del argv, cwd, env, timeout_seconds, output_byte_limit
    return HermesProcessResult(
        exit_code=None,
        timed_out=False,
        duration_ms=0,
        output_bytes=b"",
        error_category="HERMES_CLI_VERIFIER_NO_EXECUTION",
    )


def _output_summary(output: bytes) -> str:
    bounded = output[:HERMES_OUTPUT_BYTE_LIMIT]
    line_count = len([line for line in bounded.splitlines() if line.strip()])
    return (
        "Hermes output redacted; "
        f"{line_count} bounded lines and {len(bounded)} bytes observed."
    )


def _query_ref(query: str) -> str:
    return _hash_ref("hermes-query-ref", query)


def _chat_receipt_ref(
    request: HermesChatRequest,
    idempotency_ref: str,
    *,
    status: HermesChatStatus,
) -> str:
    return _hash_ref(
        "hermes-chat-receipt-ref",
        {
            "mode": request.mode,
            "query_ref": _query_ref(request.query),
            "context_pack_ref": request.context_pack_ref,
            "idempotency_ref": idempotency_ref,
            "status": status.value if isinstance(status, HermesChatStatus) else status,
        },
    )


def _hermes_chat_authority_decision(
    request: HermesChatRequest,
    active_authority_leases: list[AuthorityLease],
) -> AuthorityPolicyDecision:
    query_ref = _query_ref(request.query)
    resource_refs = [request.context_pack_ref, query_ref]
    if request.mission_ref:
        resource_refs.append(request.mission_ref)
    return evaluate_authority_request(
        AuthorityActionRequest(
            action_ref=f"{HERMES_CHAT_AUTHORITY_ACTION_REF}:{query_ref.split(':')[-1]}",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.execute,
            safe_summary=(
                "Evaluate Workspace execute authority for exact guarded Hermes "
                "CLI chat."
            ),
            resource_refs=resource_refs,
            route_ref=HERMES_CHAT_ROUTE_REF,
            lane_ref=HERMES_CHAT_AUTHORITY_LANE_REF,
            adapter_ref="adapter-ref:hermes-cli-exact-chat",
            requested_mode=TrustMode.approved_safe_local_work_session,
            constraints=(
                {"mission_ref": request.mission_ref} if request.mission_ref else {}
            )
            | {
                "context_pack_ref": request.context_pack_ref,
                "exact_argv_shape_ref": HERMES_EXACT_CHAT_ARGV_SHAPE_REF,
                "raw_prompt_persisted": False,
                "raw_output_persisted": False,
            },
            draft_fallback_available=False,
            rollback_ref="rollback-ref:hermes-interface-chat-disable-mode",
            safe_disable_ref="safe-disable-ref:hermes-interface-mode",
        ),
        active_authority_leases,
    )


def _hermes_external_handoff_receipt(
    request: HermesChatRequest,
    idempotency_ref: str,
) -> HermesChatReceiptReadModel:
    return HermesChatReceiptReadModel(
        receipt_ref=_chat_receipt_ref(
            request,
            idempotency_ref,
            status=HermesChatStatus.external_handoff_only,
        ),
        status=HermesChatStatus.external_handoff_only,
        mode=request.mode,
        query_ref=_query_ref(request.query),
        context_pack_ref=request.context_pack_ref,
        hermes_cli_ref="hermes-cli-ref:external-handoff-only",
        idempotency_ref=idempotency_ref,
        execution_performed=False,
        external_handoff_only=True,
        output_summary=(
            "Pure Hermes pass-through is an external handoff label only; UAA "
            "did not execute Hermes."
        ),
        blocked_reason_refs=["blocked-authority:hermes-pass-through-execution"],
        evidence_refs=["evidence-ref:hermes-interface-mode-external-handoff"],
        proof_refs=["proof-ref:hermes-interface-mode-no-passthrough-execution"],
    )


def _hermes_blocked_receipt(
    request: HermesChatRequest,
    idempotency_ref: str,
    *,
    cli_ref: str,
    status: HermesChatStatus,
    blocked_reason_refs: list[str],
    output_summary: str,
    unsafe_arg_blocked: bool = False,
    authority_decision: AuthorityPolicyDecision | None = None,
) -> HermesChatReceiptReadModel:
    return HermesChatReceiptReadModel(
        receipt_ref=_chat_receipt_ref(request, idempotency_ref, status=status),
        status=status,
        mode=request.mode,
        query_ref=_query_ref(request.query),
        context_pack_ref=request.context_pack_ref,
        hermes_cli_ref=cli_ref,
        idempotency_ref=idempotency_ref,
        execution_performed=False,
        unsafe_arg_blocked=unsafe_arg_blocked,
        output_summary=output_summary,
        blocked_reason_refs=blocked_reason_refs,
        evidence_refs=["evidence-ref:hermes-interface-mode-blocked-receipt"],
        proof_refs=["proof-ref:hermes-interface-mode-fail-closed"],
        authority_decision_ref=(
            authority_decision.decision_ref if authority_decision else None
        ),
        authority_decision_outcome=(
            authority_decision.outcome if authority_decision else None
        ),
        authority_lease_ref=authority_decision.lease_ref if authority_decision else None,
        authority_domain_ref=(
            HERMES_CHAT_AUTHORITY_DOMAIN_REF if authority_decision else None
        ),
        authority_capability_ref=(
            HERMES_CHAT_AUTHORITY_CAPABILITY_REF if authority_decision else None
        ),
        authority_required_mode_ref=(
            HERMES_CHAT_AUTHORITY_REQUIRED_MODE_REF if authority_decision else None
        ),
        authority_audit_ref=(
            authority_decision.audit_record_ref if authority_decision else None
        ),
        authority_policy_receipt_ref=(
            authority_decision.receipt_ref if authority_decision else None
        ),
    )


def _hash_ref(prefix: str, payload: object) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:sha256:{digest}"
