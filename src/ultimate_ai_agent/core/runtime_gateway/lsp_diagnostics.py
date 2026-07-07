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


RUNTIME_LSP_DIAGNOSTICS_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-lsp-diagnostics:v1"
)
RUNTIME_LSP_DIAGNOSTICS_ROUTE_REF = "GET /api/runtime/lsp-diagnostics"
RUNTIME_LSP_DIAGNOSTICS_CLI_REF = "uaa runtime inspect-lsp-diagnostics"
RUNTIME_LSP_DIAGNOSTICS_SNAPSHOT_REF = "lsp-diagnostics-snapshot-ref:runtime:evidence"
RUNTIME_LSP_DIAGNOSTICS_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-34:lsp-diagnostics"
)
RUNTIME_LSP_DIAGNOSTICS_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-34:lsp-diagnostics"
)
RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_STATE_ROUTE_REF = "GET /api/runtime/authority-state"
RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-lsp-diagnostics-evidence"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_LSP_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:lsp-diagnostics-no-language-server-launch",
    "blocked-authority:lsp-diagnostics-no-dependency-install",
    "blocked-authority:lsp-diagnostics-no-shell-execution",
    "blocked-authority:lsp-diagnostics-no-file-read",
    "blocked-authority:lsp-diagnostics-no-file-write",
    "blocked-authority:lsp-diagnostics-no-provider-call",
    "blocked-authority:lsp-diagnostics-no-control-center-authority-mint",
    "blocked-authority:lsp-diagnostics-no-raw-path-persistence",
    "blocked-authority:lsp-diagnostics-no-raw-diagnostic-payload-persistence",
)


class RuntimeLspDiagnosticLanguage(str, Enum):
    python = "python"
    typescript = "typescript"
    docs = "docs"


class RuntimeLspDiagnosticStatus(str, Enum):
    evidence_placeholder = "evidence_placeholder"
    proof_ready = "proof_ready"
    execution_blocked = "execution_blocked"


class RuntimeLspDiagnosticEvidenceContract(BaseModel):
    diagnostic_ref: str
    display_label: str
    language: RuntimeLspDiagnosticLanguage
    status: RuntimeLspDiagnosticStatus
    source_scope_ref: str
    evidence_ref: str
    receipt_plan_ref: str
    proof_ref: str
    safe_summary: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    language_server_started: bool = False
    dependency_install_enabled: bool = False
    shell_execution_enabled: bool = False
    file_read_enabled: bool = False
    file_write_enabled: bool = False
    provider_call_enabled: bool = False
    raw_path_persisted: bool = False
    raw_diagnostic_payload_persisted: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_contract(self) -> "RuntimeLspDiagnosticEvidenceContract":
        for value, field_name in [
            (self.diagnostic_ref, "diagnostic_ref"),
            (self.source_scope_ref, "source_scope_ref"),
            (self.evidence_ref, "evidence_ref"),
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.proof_ref, "proof_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in ("blocked_authority_refs", "next_safe_action_refs"):
            for value in getattr(self, field_name):
                validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.display_label, "display_label"),
            (str(self.language), "language"),
            (str(self.status), "status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "language_server_started": self.language_server_started,
            "dependency_install_enabled": self.dependency_install_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "file_read_enabled": self.file_read_enabled,
            "file_write_enabled": self.file_write_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "raw_path_persisted": self.raw_path_persisted,
            "raw_diagnostic_payload_persisted": (
                self.raw_diagnostic_payload_persisted
            ),
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_LSP_DIAGNOSTIC_CONTRACT_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_LSP_DIAGNOSTIC_BLOCKERS_REQUIRED")
        return self


class RuntimeLspDiagnosticsReadModel(BaseModel):
    schema_version: str = "runtime_lsp_diagnostics.v1"
    contract_ref: str = RUNTIME_LSP_DIAGNOSTICS_CONTRACT_REF
    status: str = "diagnostic_evidence_placeholder_posture"
    snapshot_ref: str = RUNTIME_LSP_DIAGNOSTICS_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-lsp-diagnostics:pending"
    route_ref: str = RUNTIME_LSP_DIAGNOSTICS_ROUTE_REF
    cli_ref: str = RUNTIME_LSP_DIAGNOSTICS_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    authority_state_route_ref: str = RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_STATE_ROUTE_REF
    authority_state_cli_ref: str = RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_STATE_CLI_REF
    authority_state_mapping_ref: str
    authority_state_catalog_ref: str
    authority_state_decision_ref: str
    authority_state_decision_outcome: str
    authority_state_status: str
    authority_state_operator_message: str
    authority_state_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "Semantic diagnostics posture exposes diagnostic evidence contracts "
        "only; no language server or shell command is launched."
    )
    diagnostics: list[RuntimeLspDiagnosticEvidenceContract] = Field(default_factory=list)
    diagnostic_count: int = 0
    evidence_placeholder_count: int = 0
    proof_ready_count: int = 0
    execution_blocked_count: int = 0
    diagnostic_evidence_contract_visible: bool = True
    receipt_plan_visible: bool = True
    proof_link_visible: bool = True
    redaction_policy_visible: bool = True
    allowlisted_server_required_for_promotion: bool = True
    cwd_jail_required_for_promotion: bool = True
    timeout_required_for_promotion: bool = True
    language_server_started: bool = False
    dependency_install_enabled: bool = False
    shell_execution_enabled: bool = False
    file_read_enabled: bool = False
    file_write_enabled: bool = False
    provider_call_enabled: bool = False
    control_center_mints_authority: bool = False
    raw_path_persisted: bool = False
    raw_diagnostic_payload_persisted: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "raw_paths_omitted",
            "raw_file_content_omitted",
            "raw_diagnostic_payloads_omitted",
            "language_server_logs_omitted",
        ]
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeLspDiagnosticsReadModel":
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
        for field_name in (
            "blocked_authority_refs",
            "promotion_path_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
            "authority_state_reason_refs",
            "unsupported_adapter_refs",
            "redactions_applied",
        ):
            for value in getattr(self, field_name):
                if field_name == "redactions_applied":
                    validate_safe_execution_text(value, field_name)
                else:
                    validate_execution_ref(value, field_name)
        if (
            self.authority_state_mapping_ref
            != RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_MAPPING_UNKNOWN")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_OUTCOME_UNKNOWN")
        if self.diagnostic_count != len(self.diagnostics):
            raise ValueError("RUNTIME_LSP_DIAGNOSTIC_COUNT_DRIFT")
        status_counts = {
            RuntimeLspDiagnosticStatus.evidence_placeholder.value: (
                self.evidence_placeholder_count
            ),
            RuntimeLspDiagnosticStatus.proof_ready.value: self.proof_ready_count,
            RuntimeLspDiagnosticStatus.execution_blocked.value: (
                self.execution_blocked_count
            ),
        }
        for status, expected in status_counts.items():
            actual = sum(1 for item in self.diagnostics if item.status == status)
            if actual != expected:
                raise ValueError("RUNTIME_LSP_DIAGNOSTIC_STATUS_COUNT_DRIFT")
        visibility_flags = {
            "diagnostic_evidence_contract_visible": (
                self.diagnostic_evidence_contract_visible
            ),
            "receipt_plan_visible": self.receipt_plan_visible,
            "proof_link_visible": self.proof_link_visible,
            "redaction_policy_visible": self.redaction_policy_visible,
            "allowlisted_server_required_for_promotion": (
                self.allowlisted_server_required_for_promotion
            ),
            "cwd_jail_required_for_promotion": self.cwd_jail_required_for_promotion,
            "timeout_required_for_promotion": self.timeout_required_for_promotion,
        }
        missing = [name for name, value in visibility_flags.items() if not value]
        if missing:
            raise ValueError(
                "RUNTIME_LSP_DIAGNOSTIC_VISIBILITY_REQUIRED: " + ", ".join(missing)
            )
        denied_flags = {
            "language_server_started": self.language_server_started,
            "dependency_install_enabled": self.dependency_install_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "file_read_enabled": self.file_read_enabled,
            "file_write_enabled": self.file_write_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "control_center_mints_authority": self.control_center_mints_authority,
            "raw_path_persisted": self.raw_path_persisted,
            "raw_diagnostic_payload_persisted": (
                self.raw_diagnostic_payload_persisted
            ),
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        for ref in RUNTIME_LSP_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS:
            if ref not in self.blocked_authority_refs:
                raise ValueError("RUNTIME_LSP_DIAGNOSTIC_BLOCKER_MISSING")
        if RUNTIME_LSP_DIAGNOSTICS_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_LSP_DIAGNOSTIC_PROOF_REF_REQUIRED")
        if RUNTIME_LSP_DIAGNOSTICS_VERIFIER_REF not in self.verifier_refs:
            raise ValueError("RUNTIME_LSP_DIAGNOSTIC_VERIFIER_REF_REQUIRED")
        return self


def _snapshot_hash_ref(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(encoded).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-lsp-diagnostics:{digest}"


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _diagnostic(
    slug: str,
    *,
    display_label: str,
    language: RuntimeLspDiagnosticLanguage,
    status: RuntimeLspDiagnosticStatus,
    safe_summary: str,
) -> RuntimeLspDiagnosticEvidenceContract:
    return RuntimeLspDiagnosticEvidenceContract(
        diagnostic_ref=f"lsp-diagnostic-ref:{slug}",
        display_label=display_label,
        language=language,
        status=status,
        source_scope_ref=f"source-scope-ref:lsp-diagnostic:{slug}:safe-ref-only",
        evidence_ref=f"evidence-ref:lsp-diagnostic:{slug}",
        receipt_plan_ref=f"receipt-plan-ref:lsp-diagnostic:{slug}",
        proof_ref=RUNTIME_LSP_DIAGNOSTICS_PROOF_REF,
        safe_summary=safe_summary,
        blocked_authority_refs=list(RUNTIME_LSP_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS),
        next_safe_action_refs=[f"next-safe-action-ref:lsp-diagnostic:{slug}:review"],
    )


def build_runtime_lsp_diagnostics_read_model(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
) -> RuntimeLspDiagnosticsReadModel:
    return build_runtime_lsp_diagnostics_read_model_from_authority_catalog(
        authority_decision_catalog=authority_decision_catalog
        or build_authority_decision_catalog(),
    )


def build_runtime_lsp_diagnostics_read_model_from_authority_catalog(
    *,
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry],
) -> RuntimeLspDiagnosticsReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    diagnostics = [
        _diagnostic(
            "python-semantic-proof",
            display_label="Python semantic proof",
            language=RuntimeLspDiagnosticLanguage.python,
            status=RuntimeLspDiagnosticStatus.proof_ready,
            safe_summary=(
                "Python diagnostic proof contract is ready, but no language "
                "server is launched."
            ),
        ),
        _diagnostic(
            "typescript-diagnostic-placeholder",
            display_label="TypeScript diagnostic placeholder",
            language=RuntimeLspDiagnosticLanguage.typescript,
            status=RuntimeLspDiagnosticStatus.evidence_placeholder,
            safe_summary=(
                "TypeScript diagnostics are represented as safe evidence "
                "placeholders until an allowlisted server lane exists."
            ),
        ),
        _diagnostic(
            "docs-diagnostic-blocked",
            display_label="Docs diagnostic blocked lane",
            language=RuntimeLspDiagnosticLanguage.docs,
            status=RuntimeLspDiagnosticStatus.execution_blocked,
            safe_summary=(
                "Docs diagnostic lane documents future proof linkage while "
                "shell execution and file reads stay blocked."
            ),
        ),
    ]
    payload_for_hash: dict[str, object] = {
        "diagnostics": [item.model_dump(mode="json") for item in diagnostics],
        "blocked": list(RUNTIME_LSP_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS),
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
    }
    return RuntimeLspDiagnosticsReadModel(
        snapshot_hash_ref=_snapshot_hash_ref(payload_for_hash),
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
        diagnostics=diagnostics,
        diagnostic_count=len(diagnostics),
        evidence_placeholder_count=sum(
            1
            for item in diagnostics
            if item.status == RuntimeLspDiagnosticStatus.evidence_placeholder.value
        ),
        proof_ready_count=sum(
            1
            for item in diagnostics
            if item.status == RuntimeLspDiagnosticStatus.proof_ready.value
        ),
        execution_blocked_count=sum(
            1
            for item in diagnostics
            if item.status == RuntimeLspDiagnosticStatus.execution_blocked.value
        ),
        blocked_authority_refs=list(RUNTIME_LSP_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            "promotion-path-ref:lsp-diagnostics:allowlisted-server",
            "promotion-path-ref:lsp-diagnostics:cwd-jail",
            "promotion-path-ref:lsp-diagnostics:timeout",
            "promotion-path-ref:lsp-diagnostics:redaction",
            "promotion-path-ref:lsp-diagnostics:diagnostic-receipt",
            "promotion-path-ref:lsp-diagnostics:proof-link",
        ],
        proof_refs=[
            RUNTIME_LSP_DIAGNOSTICS_PROOF_REF,
            "proof-ref:lsp-diagnostics:evidence-contracts",
            "proof-ref:lsp-diagnostics:server-launch-blocked",
        ],
        verifier_refs=[RUNTIME_LSP_DIAGNOSTICS_VERIFIER_REF],
        next_safe_action_refs=[
            "next-safe-action-ref:lsp-diagnostics:define-allowlisted-server",
            "next-safe-action-ref:lsp-diagnostics:bind-diagnostic-receipt",
            "next-safe-action-ref:lsp-diagnostics:keep-launch-blocked",
        ],
    )


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None,
) -> AuthorityDecisionCatalogEntry:
    catalog = authority_decision_catalog or build_authority_decision_catalog()
    entries = {entry.lane_ref: entry for entry in catalog}
    if RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_MAPPING_REF not in entries:
        raise ValueError("RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_CATALOG_MISSING")
    return entries[RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_MAPPING_REF]
