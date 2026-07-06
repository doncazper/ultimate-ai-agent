from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)


RUNTIME_LOGGING_PROFILE_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-logging-profile:v1"
)
RUNTIME_LOGGING_PROFILE_ROUTE_REF = "GET /api/runtime/logging-profile"
RUNTIME_LOGGING_PROFILE_CLI_REF = "uaa runtime inspect-logging-profile"
RUNTIME_LOGGING_PROFILE_SNAPSHOT_REF = "logging-profile-snapshot-ref:runtime:redacted"
RUNTIME_LOGGING_PROFILE_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-38:logging-profile"
)
RUNTIME_LOGGING_PROFILE_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-38:logging-profile"
)

RUNTIME_LOGGING_PROFILE_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:logging-profile-no-raw-log-persistence",
    "blocked-authority:logging-profile-no-raw-prompt-persistence",
    "blocked-authority:logging-profile-no-raw-response-persistence",
    "blocked-authority:logging-profile-no-provider-payload-persistence",
    "blocked-authority:logging-profile-no-local-path-persistence",
    "blocked-authority:logging-profile-no-credential-persistence",
    "blocked-authority:logging-profile-no-remote-telemetry-export",
    "blocked-authority:logging-profile-no-background-log-stream",
    "blocked-authority:logging-profile-no-control-center-authority-mint",
)


class RuntimeLoggingProfileKind(str, Enum):
    quiet_normal = "quiet_normal"
    redacted_troubleshooting = "redacted_troubleshooting"
    forensic_safe_refs = "forensic_safe_refs"


class RuntimeLoggingProfileStatus(str, Enum):
    active_default = "active_default"
    disabled_until_flagged = "disabled_until_flagged"
    blocked_raw_detail = "blocked_raw_detail"


class RuntimeLoggingRetentionClass(str, Enum):
    session_only = "session_only"
    bounded_local_receipt = "bounded_local_receipt"
    no_persistence = "no_persistence"


class RuntimeLoggingProfileRecord(BaseModel):
    profile_ref: str
    profile_kind: RuntimeLoggingProfileKind
    display_label: str
    profile_status: RuntimeLoggingProfileStatus
    retention_class: RuntimeLoggingRetentionClass
    flag_scope_ref: str
    ttl_policy_ref: str
    retention_policy_ref: str
    redaction_policy_ref: str
    redaction_verifier_ref: str
    proof_ref: str
    safe_summary: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    visible_in_control_center: bool = True
    operator_flag_required: bool = True
    safe_disable_available: bool = True
    raw_logs_persisted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    provider_payload_persisted: bool = False
    local_path_persisted: bool = False
    credential_material_persisted: bool = False
    remote_telemetry_export_enabled: bool = False
    background_log_stream_enabled: bool = False
    control_center_mints_authority: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_record(self) -> "RuntimeLoggingProfileRecord":
        for value, field_name in [
            (self.profile_ref, "profile_ref"),
            (self.flag_scope_ref, "flag_scope_ref"),
            (self.ttl_policy_ref, "ttl_policy_ref"),
            (self.retention_policy_ref, "retention_policy_ref"),
            (self.redaction_policy_ref, "redaction_policy_ref"),
            (self.redaction_verifier_ref, "redaction_verifier_ref"),
            (self.proof_ref, "proof_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "promotion_path_refs",
            "next_safe_action_refs",
        ):
            for value in getattr(self, field_name):
                validate_execution_ref(value, field_name)
        for value, field_name in [
            (str(self.profile_kind), "profile_kind"),
            (self.display_label, "display_label"),
            (str(self.profile_status), "profile_status"),
            (str(self.retention_class), "retention_class"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "raw_logs_persisted": self.raw_logs_persisted,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "provider_payload_persisted": self.provider_payload_persisted,
            "local_path_persisted": self.local_path_persisted,
            "credential_material_persisted": self.credential_material_persisted,
            "remote_telemetry_export_enabled": self.remote_telemetry_export_enabled,
            "background_log_stream_enabled": self.background_log_stream_enabled,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_LOGGING_PROFILE_RECORD_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.visible_in_control_center or not self.safe_disable_available:
            raise ValueError("RUNTIME_LOGGING_PROFILE_VISIBILITY_REQUIRED")
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_LOGGING_PROFILE_BLOCKERS_REQUIRED")
        return self


class RuntimeLoggingProfileReadModel(BaseModel):
    schema_version: str = "runtime_logging_profile.v1"
    contract_ref: str = RUNTIME_LOGGING_PROFILE_CONTRACT_REF
    status: str = "quiet_default_redacted_troubleshooting_available"
    snapshot_ref: str = RUNTIME_LOGGING_PROFILE_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:logging-profile:pending"
    route_ref: str = RUNTIME_LOGGING_PROFILE_ROUTE_REF
    cli_ref: str = RUNTIME_LOGGING_PROFILE_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    active_profile_ref: str = "logging-profile-ref:runtime:quiet-normal"
    safe_summary: str = (
        "Logging profile posture keeps UAA quiet by default and exposes a "
        "redacted troubleshooting profile proposal with TTL, retention, "
        "redaction verifier, proof, and safe-disable refs."
    )
    profiles: list[RuntimeLoggingProfileRecord] = Field(default_factory=list)
    profile_count: int = 0
    quiet_default_count: int = 0
    disabled_until_flagged_count: int = 0
    blocked_raw_detail_count: int = 0
    flag_scope_visible: bool = True
    ttl_policy_visible: bool = True
    redaction_rules_visible: bool = True
    retention_policy_visible: bool = True
    operator_proof_visible: bool = True
    safe_disable_visible: bool = True
    verbose_logging_enabled: bool = False
    raw_logs_persisted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    provider_payload_persisted: bool = False
    local_path_persisted: bool = False
    credential_material_persisted: bool = False
    remote_telemetry_export_enabled: bool = False
    background_log_stream_enabled: bool = False
    control_center_mints_authority: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "raw_logs_omitted",
            "raw_prompts_omitted",
            "raw_responses_omitted",
            "provider_payloads_omitted",
            "local_paths_omitted",
            "credential_material_omitted",
        ]
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeLoggingProfileReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.active_profile_ref, "active_profile_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "promotion_path_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
        ):
            for value in getattr(self, field_name):
                validate_execution_ref(value, field_name)
        for value in self.redactions_applied:
            validate_safe_execution_text(value, "redactions_applied")
        denied_flags = {
            "verbose_logging_enabled": self.verbose_logging_enabled,
            "raw_logs_persisted": self.raw_logs_persisted,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "provider_payload_persisted": self.provider_payload_persisted,
            "local_path_persisted": self.local_path_persisted,
            "credential_material_persisted": self.credential_material_persisted,
            "remote_telemetry_export_enabled": self.remote_telemetry_export_enabled,
            "background_log_stream_enabled": self.background_log_stream_enabled,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_LOGGING_PROFILE_READ_MODEL_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if set(RUNTIME_LOGGING_PROFILE_BLOCKED_AUTHORITY_REFS) - set(
            self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_LOGGING_PROFILE_BLOCKERS_REQUIRED")
        if self.profile_count != len(self.profiles):
            raise ValueError("RUNTIME_LOGGING_PROFILE_COUNT_MISMATCH")
        return self


def _profile(
    *,
    slug: str,
    profile_kind: RuntimeLoggingProfileKind,
    display_label: str,
    profile_status: RuntimeLoggingProfileStatus,
    retention_class: RuntimeLoggingRetentionClass,
    summary: str,
) -> RuntimeLoggingProfileRecord:
    return RuntimeLoggingProfileRecord(
        profile_ref=f"logging-profile-ref:runtime:{slug}",
        profile_kind=profile_kind,
        display_label=display_label,
        profile_status=profile_status,
        retention_class=retention_class,
        flag_scope_ref=f"logging-flag-scope-ref:runtime:{slug}",
        ttl_policy_ref=f"ttl-policy-ref:runtime-logging:{slug}",
        retention_policy_ref=f"retention-policy-ref:runtime-logging:{slug}",
        redaction_policy_ref=f"redaction-policy-ref:runtime-logging:{slug}",
        redaction_verifier_ref=f"redaction-verifier-ref:runtime-logging:{slug}",
        proof_ref=f"proof-ref:runtime-logging:{slug}",
        safe_summary=summary,
        blocked_authority_refs=list(RUNTIME_LOGGING_PROFILE_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            f"promotion-path-ref:runtime-logging:{slug}:flag-scope",
            f"promotion-path-ref:runtime-logging:{slug}:ttl",
            f"promotion-path-ref:runtime-logging:{slug}:redaction-verifier",
            f"promotion-path-ref:runtime-logging:{slug}:safe-disable",
        ],
        next_safe_action_refs=[
            f"next-safe-action-ref:runtime-logging:{slug}:operator-proof"
        ],
    )


def build_runtime_logging_profile_read_model() -> RuntimeLoggingProfileReadModel:
    profiles = [
        _profile(
            slug="quiet-normal",
            profile_kind=RuntimeLoggingProfileKind.quiet_normal,
            display_label="Quiet normal",
            profile_status=RuntimeLoggingProfileStatus.active_default,
            retention_class=RuntimeLoggingRetentionClass.no_persistence,
            summary=(
                "Default quiet profile keeps troubleshooting detail disabled "
                "and stores no raw logs."
            ),
        ),
        _profile(
            slug="redacted-troubleshooting",
            profile_kind=RuntimeLoggingProfileKind.redacted_troubleshooting,
            display_label="Redacted troubleshooting",
            profile_status=RuntimeLoggingProfileStatus.disabled_until_flagged,
            retention_class=RuntimeLoggingRetentionClass.session_only,
            summary=(
                "Verbose detail is proposed as an operator-flagged, TTL-bound, "
                "redacted troubleshooting profile."
            ),
        ),
        _profile(
            slug="forensic-safe-refs",
            profile_kind=RuntimeLoggingProfileKind.forensic_safe_refs,
            display_label="Forensic safe refs",
            profile_status=RuntimeLoggingProfileStatus.blocked_raw_detail,
            retention_class=RuntimeLoggingRetentionClass.bounded_local_receipt,
            summary=(
                "Forensic posture can retain safe refs and hashes only; raw "
                "logs, prompts, provider payloads, and paths remain blocked."
            ),
        ),
    ]
    payload = {
        "contract_ref": RUNTIME_LOGGING_PROFILE_CONTRACT_REF,
        "snapshot_ref": RUNTIME_LOGGING_PROFILE_SNAPSHOT_REF,
        "route_ref": RUNTIME_LOGGING_PROFILE_ROUTE_REF,
        "cli_ref": RUNTIME_LOGGING_PROFILE_CLI_REF,
        "profiles": profiles,
        "profile_count": len(profiles),
        "quiet_default_count": sum(
            profile.profile_status == RuntimeLoggingProfileStatus.active_default
            for profile in profiles
        ),
        "disabled_until_flagged_count": sum(
            profile.profile_status
            == RuntimeLoggingProfileStatus.disabled_until_flagged
            for profile in profiles
        ),
        "blocked_raw_detail_count": sum(
            profile.profile_status == RuntimeLoggingProfileStatus.blocked_raw_detail
            for profile in profiles
        ),
        "blocked_authority_refs": list(RUNTIME_LOGGING_PROFILE_BLOCKED_AUTHORITY_REFS),
        "promotion_path_refs": [
            "promotion-path-ref:logging-profile:flag-scope",
            "promotion-path-ref:logging-profile:ttl",
            "promotion-path-ref:logging-profile:redaction-verifier",
            "promotion-path-ref:logging-profile:retention-policy",
            "promotion-path-ref:logging-profile:operator-proof",
            "promotion-path-ref:logging-profile:safe-disable",
        ],
        "proof_refs": [RUNTIME_LOGGING_PROFILE_PROOF_REF],
        "verifier_refs": [RUNTIME_LOGGING_PROFILE_VERIFIER_REF],
        "next_safe_action_refs": [
            "next-safe-action-ref:logging-profile:operator-flag-contract",
            "next-safe-action-ref:logging-profile:redaction-regression-fixtures",
        ],
    }
    snapshot_material = {
        "contract_ref": payload["contract_ref"],
        "route_ref": payload["route_ref"],
        "profile_refs": [profile.profile_ref for profile in profiles],
        "blocked_authority_refs": payload["blocked_authority_refs"],
    }
    payload["snapshot_hash_ref"] = (
        "snapshot-hash-ref:logging-profile:"
        + hashlib.sha256(
            json.dumps(snapshot_material, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
    )
    return RuntimeLoggingProfileReadModel(**payload)
