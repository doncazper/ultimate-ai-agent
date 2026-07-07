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


RUNTIME_DOCTOR_DIAGNOSTICS_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-doctor-diagnostics:v1"
)
RUNTIME_DOCTOR_DIAGNOSTICS_ROUTE_REF = "GET /api/runtime/doctor-diagnostics"
RUNTIME_DOCTOR_DIAGNOSTICS_CLI_REF = "uaa runtime inspect-doctor-diagnostics"
RUNTIME_DOCTOR_DIAGNOSTICS_SNAPSHOT_REF = (
    "doctor-diagnostics-snapshot-ref:runtime:local-diagnostics"
)
RUNTIME_DOCTOR_DIAGNOSTICS_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-28:doctor-diagnostics"
)
RUNTIME_DOCTOR_DIAGNOSTICS_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-28:doctor-diagnostics"
)

RUNTIME_DOCTOR_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:runtime-doctor-no-installs",
    "blocked-authority:runtime-doctor-no-service-starts",
    "blocked-authority:runtime-doctor-no-protected-material-write",
    "blocked-authority:runtime-doctor-no-runtime-config-mutation",
    "blocked-authority:runtime-doctor-no-provider-payload-persistence",
    "blocked-authority:runtime-doctor-no-control-center-authority-mint",
)


class RuntimeDoctorDiagnosticDomain(str, Enum):
    setup = "setup"
    runtime_readiness = "runtime_readiness"
    providers = "providers"
    tools = "tools"
    protected_material = "protected_material"
    local_services = "local_services"
    authority = "authority"
    next_actions = "next_actions"


class RuntimeDoctorDiagnosticStatus(str, Enum):
    ok = "ok"
    review = "review"
    blocked = "blocked"
    unavailable = "unavailable"


class RuntimeDoctorDiagnosticItem(BaseModel):
    diagnostic_ref: str
    domain: RuntimeDoctorDiagnosticDomain
    status: RuntimeDoctorDiagnosticStatus
    display_label: str
    safe_summary: str
    signal_refs: list[str] = Field(default_factory=list)
    route_refs: list[str] = Field(default_factory=list)
    cli_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    install_performed: bool = False
    service_start_performed: bool = False
    credential_write_performed: bool = False
    runtime_config_mutation_performed: bool = False
    raw_log_persisted: bool = False
    raw_local_path_persisted: bool = False
    provider_payload_persisted: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_item(self) -> "RuntimeDoctorDiagnosticItem":
        validate_execution_ref(self.diagnostic_ref, "diagnostic_ref")
        for field_name in (
            "signal_refs",
            "route_refs",
            "cli_refs",
            "proof_refs",
            "blocked_authority_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (str(self.domain), "domain"),
            (str(self.status), "status"),
            (self.display_label, "display_label"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_DOCTOR_BLOCKED_AUTHORITY_REQUIRED")
        denied_flags = {
            "install_performed": self.install_performed,
            "service_start_performed": self.service_start_performed,
            "credential_write_performed": self.credential_write_performed,
            "runtime_config_mutation_performed": self.runtime_config_mutation_performed,
            "raw_log_persisted": self.raw_log_persisted,
            "raw_local_path_persisted": self.raw_local_path_persisted,
            "provider_payload_persisted": self.provider_payload_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_DOCTOR_DIAGNOSTIC_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        return self


class RuntimeDoctorDiagnosticsReadModel(BaseModel):
    schema_version: str = "runtime_doctor_diagnostics.v1"
    contract_ref: str = RUNTIME_DOCTOR_DIAGNOSTICS_CONTRACT_REF
    status: str = "read_only_diagnostics_posture"
    snapshot_ref: str = RUNTIME_DOCTOR_DIAGNOSTICS_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-doctor:pending"
    route_ref: str = RUNTIME_DOCTOR_DIAGNOSTICS_ROUTE_REF
    cli_ref: str = RUNTIME_DOCTOR_DIAGNOSTICS_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    safe_summary: str = (
        "Runtime doctor diagnostics explain local setup and readiness using "
        "redacted status refs only."
    )
    diagnostics: list[RuntimeDoctorDiagnosticItem] = Field(default_factory=list)
    diagnostic_count: int = 0
    ok_count: int = 0
    review_count: int = 0
    blocked_count: int = 0
    unavailable_count: int = 0
    setup_visible: bool = True
    runtime_readiness_visible: bool = True
    provider_posture_visible: bool = True
    tool_posture_visible: bool = True
    protected_material_posture_visible: bool = True
    service_posture_visible: bool = True
    authority_posture_visible: bool = True
    next_safe_actions_visible: bool = True
    install_enabled: bool = False
    service_start_enabled: bool = False
    credential_write_enabled: bool = False
    runtime_config_mutation_enabled: bool = False
    control_center_mints_authority: bool = False
    raw_log_persisted: bool = False
    raw_local_path_persisted: bool = False
    provider_payload_persisted: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "raw_logs_omitted",
            "raw_paths_omitted",
            "provider_payloads_omitted",
            "protected_material_omitted",
        ]
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeDoctorDiagnosticsReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
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
            "redactions_applied",
        ):
            for value in getattr(self, field_name):
                if field_name == "redactions_applied":
                    validate_safe_execution_text(value, field_name)
                else:
                    validate_execution_ref(value, field_name)
        if self.diagnostic_count != len(self.diagnostics):
            raise ValueError("RUNTIME_DOCTOR_DIAGNOSTIC_COUNT_DRIFT")
        status_counts = {
            RuntimeDoctorDiagnosticStatus.ok.value: self.ok_count,
            RuntimeDoctorDiagnosticStatus.review.value: self.review_count,
            RuntimeDoctorDiagnosticStatus.blocked.value: self.blocked_count,
            RuntimeDoctorDiagnosticStatus.unavailable.value: self.unavailable_count,
        }
        for status, expected in status_counts.items():
            actual = sum(1 for item in self.diagnostics if item.status == status)
            if actual != expected:
                raise ValueError("RUNTIME_DOCTOR_STATUS_COUNT_DRIFT")
        required_true = {
            "setup_visible": self.setup_visible,
            "runtime_readiness_visible": self.runtime_readiness_visible,
            "provider_posture_visible": self.provider_posture_visible,
            "tool_posture_visible": self.tool_posture_visible,
            "protected_material_posture_visible": (
                self.protected_material_posture_visible
            ),
            "service_posture_visible": self.service_posture_visible,
            "authority_posture_visible": self.authority_posture_visible,
            "next_safe_actions_visible": self.next_safe_actions_visible,
        }
        missing = [name for name, value in required_true.items() if not value]
        if missing:
            raise ValueError("RUNTIME_DOCTOR_VISIBILITY_REQUIRED: " + ", ".join(missing))
        denied_flags = {
            "install_enabled": self.install_enabled,
            "service_start_enabled": self.service_start_enabled,
            "credential_write_enabled": self.credential_write_enabled,
            "runtime_config_mutation_enabled": self.runtime_config_mutation_enabled,
            "control_center_mints_authority": self.control_center_mints_authority,
            "raw_log_persisted": self.raw_log_persisted,
            "raw_local_path_persisted": self.raw_local_path_persisted,
            "provider_payload_persisted": self.provider_payload_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError("RUNTIME_DOCTOR_AUTHORITY_DENIED: " + ", ".join(enabled))
        for ref in RUNTIME_DOCTOR_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS:
            if ref not in self.blocked_authority_refs:
                raise ValueError("RUNTIME_DOCTOR_BLOCKER_MISSING")
        if (
            not self.proof_refs
            or RUNTIME_DOCTOR_DIAGNOSTICS_PROOF_REF not in self.proof_refs
        ):
            raise ValueError("RUNTIME_DOCTOR_PROOF_REF_REQUIRED")
        if (
            not self.verifier_refs
            or RUNTIME_DOCTOR_DIAGNOSTICS_VERIFIER_REF not in self.verifier_refs
        ):
            raise ValueError("RUNTIME_DOCTOR_VERIFIER_REF_REQUIRED")
        return self


def _snapshot_hash_ref(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(encoded).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-doctor:{digest}"


def _diagnostic_item(
    slug: str,
    *,
    domain: RuntimeDoctorDiagnosticDomain,
    status: RuntimeDoctorDiagnosticStatus,
    display_label: str,
    safe_summary: str,
    signal_refs: list[str],
    route_refs: list[str] | None = None,
    cli_refs: list[str] | None = None,
    next_safe_action_refs: list[str] | None = None,
) -> RuntimeDoctorDiagnosticItem:
    return RuntimeDoctorDiagnosticItem(
        diagnostic_ref=f"runtime-doctor-diagnostic-ref:{slug}",
        domain=domain,
        status=status,
        display_label=display_label,
        safe_summary=safe_summary,
        signal_refs=signal_refs,
        route_refs=route_refs or [],
        cli_refs=cli_refs or [],
        proof_refs=[RUNTIME_DOCTOR_DIAGNOSTICS_PROOF_REF],
        blocked_authority_refs=list(RUNTIME_DOCTOR_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS),
        next_safe_action_refs=next_safe_action_refs or [],
    )


def build_runtime_doctor_diagnostics_read_model() -> RuntimeDoctorDiagnosticsReadModel:
    diagnostics = [
        _diagnostic_item(
            "setup",
            domain=RuntimeDoctorDiagnosticDomain.setup,
            status=RuntimeDoctorDiagnosticStatus.review,
            display_label="Setup",
            safe_summary=(
                "Setup posture is visible as local status; installs stay proposal-only."
            ),
            signal_refs=[
                "diagnostic-signal-ref:runtime-doctor:setup-assistant-status",
                "diagnostic-signal-ref:runtime-doctor:local-package-posture",
            ],
            route_refs=["route-ref:control-center-setup-assistant-summary"],
            cli_refs=["cli-ref:make-doctor"],
            next_safe_action_refs=["next-safe-action-ref:runtime-doctor:review-setup"],
        ),
        _diagnostic_item(
            "runtime-readiness",
            domain=RuntimeDoctorDiagnosticDomain.runtime_readiness,
            status=RuntimeDoctorDiagnosticStatus.ok,
            display_label="Runtime readiness",
            safe_summary=(
                "Runtime readiness uses existing backend status refs without launching services."
            ),
            signal_refs=[
                "diagnostic-signal-ref:runtime-doctor:runtime-readiness",
                "diagnostic-signal-ref:runtime-doctor:capability-matrix",
            ],
            route_refs=[
                "route-ref:runtime-readiness",
                "route-ref:runtime-capability-matrix",
            ],
            cli_refs=["cli-ref:uaa-runtime-status"],
        ),
        _diagnostic_item(
            "providers",
            domain=RuntimeDoctorDiagnosticDomain.providers,
            status=RuntimeDoctorDiagnosticStatus.review,
            display_label="Providers",
            safe_summary=(
                "Provider posture is readable metadata only; network adapter calls stay blocked."
            ),
            signal_refs=[
                "diagnostic-signal-ref:runtime-doctor:provider-catalog",
                "diagnostic-signal-ref:runtime-doctor:cost-posture",
            ],
            route_refs=["route-ref:control-center-providers-runtime-control-plane"],
            cli_refs=["cli-ref:uaa-runtime-authority-profile"],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-doctor:review-provider-posture"
            ],
        ),
        _diagnostic_item(
            "tools",
            domain=RuntimeDoctorDiagnosticDomain.tools,
            status=RuntimeDoctorDiagnosticStatus.ok,
            display_label="Tools",
            safe_summary=(
                "Tool catalog visibility is metadata-only; invocation authority is not added."
            ),
            signal_refs=[
                "diagnostic-signal-ref:runtime-doctor:tool-registry",
                "diagnostic-signal-ref:runtime-doctor:command-floor",
            ],
            route_refs=[
                "route-ref:runtime-tool-registry",
                "route-ref:runtime-hardline-command-blocklist",
            ],
            cli_refs=["cli-ref:uaa-runtime-inspect-tool-registry"],
        ),
        _diagnostic_item(
            "protected-material",
            domain=RuntimeDoctorDiagnosticDomain.protected_material,
            status=RuntimeDoctorDiagnosticStatus.blocked,
            display_label="Protected material",
            safe_summary=(
                "Protected material is represented by redacted refs only; writes remain blocked."
            ),
            signal_refs=[
                "diagnostic-signal-ref:runtime-doctor:protected-material-posture"
            ],
            cli_refs=["cli-ref:uaa-runtime-authority-profile"],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-doctor:bind-redacted-material-refs"
            ],
        ),
        _diagnostic_item(
            "local-services",
            domain=RuntimeDoctorDiagnosticDomain.local_services,
            status=RuntimeDoctorDiagnosticStatus.review,
            display_label="Local services",
            safe_summary=(
                "Local service status is readable; service starts and restarts stay blocked."
            ),
            signal_refs=[
                "diagnostic-signal-ref:runtime-doctor:local-service-status",
                "diagnostic-signal-ref:runtime-doctor:safe-disable-posture",
            ],
            route_refs=["route-ref:control-center-local-models-status"],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-doctor:propose-service-action"
            ],
        ),
        _diagnostic_item(
            "authority",
            domain=RuntimeDoctorDiagnosticDomain.authority,
            status=RuntimeDoctorDiagnosticStatus.ok,
            display_label="Authority",
            safe_summary=(
                "Authority posture points to AuthorityLease capabilities and "
                "blocked refs without minting power."
            ),
            signal_refs=[
                "diagnostic-signal-ref:runtime-doctor:trust-authority",
                "diagnostic-signal-ref:runtime-doctor:managed-scope-policy",
            ],
            route_refs=[
                "route-ref:control-center-trust-authority-matrix",
                "route-ref:api-runtime-managed-scope-policy",
            ],
            cli_refs=["cli-ref:uaa-runtime-inspect-managed-scope-policy"],
        ),
        _diagnostic_item(
            "next-actions",
            domain=RuntimeDoctorDiagnosticDomain.next_actions,
            status=RuntimeDoctorDiagnosticStatus.review,
            display_label="Next safe actions",
            safe_summary=(
                "Next actions are proposal refs until an approval envelope and receipt lane exists."
            ),
            signal_refs=["diagnostic-signal-ref:runtime-doctor:next-safe-actions"],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-doctor:setup-action-proposals",
                "next-safe-action-ref:runtime-doctor:approval-envelope",
                "next-safe-action-ref:runtime-doctor:receipt-and-proof",
            ],
        ),
    ]
    payload_for_hash: dict[str, object] = {
        "diagnostics": [item.model_dump(mode="json") for item in diagnostics],
        "blocked": list(RUNTIME_DOCTOR_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS),
    }
    return RuntimeDoctorDiagnosticsReadModel(
        snapshot_hash_ref=_snapshot_hash_ref(payload_for_hash),
        diagnostics=diagnostics,
        diagnostic_count=len(diagnostics),
        ok_count=sum(
            1
            for item in diagnostics
            if item.status == RuntimeDoctorDiagnosticStatus.ok.value
        ),
        review_count=sum(
            1
            for item in diagnostics
            if item.status == RuntimeDoctorDiagnosticStatus.review.value
        ),
        blocked_count=sum(
            1
            for item in diagnostics
            if item.status == RuntimeDoctorDiagnosticStatus.blocked.value
        ),
        unavailable_count=sum(
            1
            for item in diagnostics
            if item.status == RuntimeDoctorDiagnosticStatus.unavailable.value
        ),
        blocked_authority_refs=list(RUNTIME_DOCTOR_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            "promotion-path-ref:runtime-doctor:setup-action-proposals",
            "promotion-path-ref:runtime-doctor:approval-envelope",
            "promotion-path-ref:runtime-doctor:receipt",
            "promotion-path-ref:runtime-doctor:rollback-safe-disable",
            "promotion-path-ref:runtime-doctor:proof",
        ],
        proof_refs=[
            RUNTIME_DOCTOR_DIAGNOSTICS_PROOF_REF,
            "proof-ref:runtime-doctor:redacted-diagnostics",
            "proof-ref:runtime-doctor:blocked-mutation-posture",
        ],
        verifier_refs=[RUNTIME_DOCTOR_DIAGNOSTICS_VERIFIER_REF],
        next_safe_action_refs=[
            "next-safe-action-ref:runtime-doctor:review-diagnostics",
            "next-safe-action-ref:runtime-doctor:create-setup-proposal-lane",
            "next-safe-action-ref:runtime-doctor:bind-approval-and-receipt",
        ],
    )
