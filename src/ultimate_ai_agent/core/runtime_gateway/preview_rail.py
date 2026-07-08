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


RUNTIME_PREVIEW_RAIL_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-preview-rail:v1"
)
RUNTIME_PREVIEW_RAIL_ROUTE_REF = "GET /api/runtime/preview-rail"
RUNTIME_PREVIEW_RAIL_CLI_REF = "uaa runtime inspect-preview-rail"
RUNTIME_PREVIEW_RAIL_SNAPSHOT_REF = "preview-rail-snapshot-ref:runtime:safe-refs"
RUNTIME_PREVIEW_RAIL_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-35:preview-rail"
)
RUNTIME_PREVIEW_RAIL_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-35:preview-rail"
)
RUNTIME_PREVIEW_RAIL_AUTHORITY_STATE_ROUTE_REF = "GET /api/runtime/authority-state"
RUNTIME_PREVIEW_RAIL_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_PREVIEW_RAIL_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-preview-rail-safe-ref-read-model"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_PREVIEW_RAIL_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:preview-rail-no-browser-automation",
    "blocked-authority:preview-rail-no-raw-sensitive-file-display",
    "blocked-authority:preview-rail-no-direct-runtime-payload-rendering",
    "blocked-authority:preview-rail-no-screenshot-capture",
    "blocked-authority:preview-rail-no-file-read",
    "blocked-authority:preview-rail-no-file-write",
    "blocked-authority:preview-rail-no-shell-execution",
    "blocked-authority:preview-rail-no-provider-call",
    "blocked-authority:preview-rail-no-control-center-authority-mint",
    "blocked-authority:preview-rail-no-raw-path-persistence",
    "blocked-authority:preview-rail-no-raw-file-content-persistence",
    "blocked-authority:preview-rail-no-raw-runtime-payload-persistence",
)


class RuntimePreviewRailSlotKind(str, Enum):
    file_ref = "file_ref"
    diff_ref = "diff_ref"
    artifact_ref = "artifact_ref"
    run_output_ref = "run_output_ref"
    proof_ref = "proof_ref"
    runtime_event_ref = "runtime_event_ref"


class RuntimePreviewRailSlotStatus(str, Enum):
    safe_ref_ready = "safe_ref_ready"
    bounded_preview_placeholder = "bounded_preview_placeholder"
    execution_blocked = "execution_blocked"


class RuntimePreviewRailSlot(BaseModel):
    slot_ref: str
    display_label: str
    slot_kind: RuntimePreviewRailSlotKind
    slot_status: RuntimePreviewRailSlotStatus
    source_ref: str
    source_classification_ref: str
    bounded_preview_ref: str
    redaction_policy_ref: str
    attach_plan_ref: str
    receipt_plan_ref: str
    proof_ref: str
    safe_summary: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    browser_automation_enabled: bool = False
    raw_sensitive_file_display_enabled: bool = False
    direct_runtime_payload_rendering_enabled: bool = False
    screenshot_capture_enabled: bool = False
    file_read_enabled: bool = False
    file_write_enabled: bool = False
    shell_execution_enabled: bool = False
    provider_call_enabled: bool = False
    raw_path_persisted: bool = False
    raw_file_content_persisted: bool = False
    raw_runtime_payload_persisted: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_slot(self) -> "RuntimePreviewRailSlot":
        for value, field_name in [
            (self.slot_ref, "slot_ref"),
            (self.source_ref, "source_ref"),
            (self.source_classification_ref, "source_classification_ref"),
            (self.bounded_preview_ref, "bounded_preview_ref"),
            (self.redaction_policy_ref, "redaction_policy_ref"),
            (self.attach_plan_ref, "attach_plan_ref"),
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.proof_ref, "proof_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in ("blocked_authority_refs", "next_safe_action_refs"):
            for value in getattr(self, field_name):
                validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.display_label, "display_label"),
            (str(self.slot_kind), "slot_kind"),
            (str(self.slot_status), "slot_status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "browser_automation_enabled": self.browser_automation_enabled,
            "raw_sensitive_file_display_enabled": (
                self.raw_sensitive_file_display_enabled
            ),
            "direct_runtime_payload_rendering_enabled": (
                self.direct_runtime_payload_rendering_enabled
            ),
            "screenshot_capture_enabled": self.screenshot_capture_enabled,
            "file_read_enabled": self.file_read_enabled,
            "file_write_enabled": self.file_write_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "raw_path_persisted": self.raw_path_persisted,
            "raw_file_content_persisted": self.raw_file_content_persisted,
            "raw_runtime_payload_persisted": self.raw_runtime_payload_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_PREVIEW_RAIL_SLOT_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_PREVIEW_RAIL_SLOT_BLOCKERS_REQUIRED")
        return self


class RuntimePreviewRailReadModel(BaseModel):
    schema_version: str = "runtime_preview_rail.v1"
    contract_ref: str = RUNTIME_PREVIEW_RAIL_CONTRACT_REF
    status: str = "safe_ref_preview_rail_posture"
    snapshot_ref: str = RUNTIME_PREVIEW_RAIL_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-preview-rail:pending"
    route_ref: str = RUNTIME_PREVIEW_RAIL_ROUTE_REF
    cli_ref: str = RUNTIME_PREVIEW_RAIL_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    authority_state_route_ref: str = RUNTIME_PREVIEW_RAIL_AUTHORITY_STATE_ROUTE_REF
    authority_state_cli_ref: str = RUNTIME_PREVIEW_RAIL_AUTHORITY_STATE_CLI_REF
    authority_state_mapping_ref: str
    authority_state_catalog_ref: str
    authority_state_decision_ref: str
    authority_state_decision_outcome: str
    authority_state_status: str
    authority_state_operator_message: str
    authority_state_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "Operator preview rail exposes safe refs and bounded preview plans "
        "only; raw files, browser automation, and runtime payload rendering "
        "remain blocked."
    )
    slots: list[RuntimePreviewRailSlot] = Field(default_factory=list)
    slot_count: int = 0
    safe_ref_ready_count: int = 0
    bounded_preview_placeholder_count: int = 0
    execution_blocked_count: int = 0
    source_classification_visible: bool = True
    redaction_policy_visible: bool = True
    bounded_preview_visible: bool = True
    operator_attach_visible: bool = True
    receipt_plan_visible: bool = True
    proof_link_visible: bool = True
    browser_automation_enabled: bool = False
    raw_sensitive_file_display_enabled: bool = False
    direct_runtime_payload_rendering_enabled: bool = False
    screenshot_capture_enabled: bool = False
    file_read_enabled: bool = False
    file_write_enabled: bool = False
    shell_execution_enabled: bool = False
    provider_call_enabled: bool = False
    control_center_mints_authority: bool = False
    raw_path_persisted: bool = False
    raw_file_content_persisted: bool = False
    raw_runtime_payload_persisted: bool = False
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
            "raw_runtime_payloads_omitted",
            "raw_browser_state_omitted",
            "screenshot_pixels_omitted",
        ]
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimePreviewRailReadModel":
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
        if self.authority_state_mapping_ref != RUNTIME_PREVIEW_RAIL_AUTHORITY_MAPPING_REF:
            raise ValueError("RUNTIME_PREVIEW_RAIL_AUTHORITY_MAPPING_UNKNOWN")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_PREVIEW_RAIL_AUTHORITY_OUTCOME_UNKNOWN")
        if self.slot_count != len(self.slots):
            raise ValueError("RUNTIME_PREVIEW_RAIL_SLOT_COUNT_DRIFT")
        status_counts = {
            RuntimePreviewRailSlotStatus.safe_ref_ready.value: (
                self.safe_ref_ready_count
            ),
            RuntimePreviewRailSlotStatus.bounded_preview_placeholder.value: (
                self.bounded_preview_placeholder_count
            ),
            RuntimePreviewRailSlotStatus.execution_blocked.value: (
                self.execution_blocked_count
            ),
        }
        for status, expected in status_counts.items():
            actual = sum(1 for slot in self.slots if slot.slot_status == status)
            if actual != expected:
                raise ValueError("RUNTIME_PREVIEW_RAIL_SLOT_STATUS_COUNT_DRIFT")
        visible_flags = {
            "source_classification_visible": self.source_classification_visible,
            "redaction_policy_visible": self.redaction_policy_visible,
            "bounded_preview_visible": self.bounded_preview_visible,
            "operator_attach_visible": self.operator_attach_visible,
            "receipt_plan_visible": self.receipt_plan_visible,
            "proof_link_visible": self.proof_link_visible,
        }
        missing = [name for name, value in visible_flags.items() if not value]
        if missing:
            raise ValueError(
                "RUNTIME_PREVIEW_RAIL_VISIBILITY_REQUIRED: " + ", ".join(missing)
            )
        denied_flags = {
            "browser_automation_enabled": self.browser_automation_enabled,
            "raw_sensitive_file_display_enabled": (
                self.raw_sensitive_file_display_enabled
            ),
            "direct_runtime_payload_rendering_enabled": (
                self.direct_runtime_payload_rendering_enabled
            ),
            "screenshot_capture_enabled": self.screenshot_capture_enabled,
            "file_read_enabled": self.file_read_enabled,
            "file_write_enabled": self.file_write_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "control_center_mints_authority": self.control_center_mints_authority,
            "raw_path_persisted": self.raw_path_persisted,
            "raw_file_content_persisted": self.raw_file_content_persisted,
            "raw_runtime_payload_persisted": self.raw_runtime_payload_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_PREVIEW_RAIL_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        for ref in RUNTIME_PREVIEW_RAIL_BLOCKED_AUTHORITY_REFS:
            if ref not in self.blocked_authority_refs:
                raise ValueError("RUNTIME_PREVIEW_RAIL_BLOCKER_MISSING")
        if RUNTIME_PREVIEW_RAIL_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_PREVIEW_RAIL_PROOF_REF_REQUIRED")
        if RUNTIME_PREVIEW_RAIL_VERIFIER_REF not in self.verifier_refs:
            raise ValueError("RUNTIME_PREVIEW_RAIL_VERIFIER_REF_REQUIRED")
        return self


def _snapshot_hash_ref(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(encoded).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-preview-rail:{digest}"


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _slot(
    slug: str,
    *,
    display_label: str,
    slot_kind: RuntimePreviewRailSlotKind,
    slot_status: RuntimePreviewRailSlotStatus,
    safe_summary: str,
) -> RuntimePreviewRailSlot:
    return RuntimePreviewRailSlot(
        slot_ref=f"preview-rail-slot-ref:{slug}",
        display_label=display_label,
        slot_kind=slot_kind,
        slot_status=slot_status,
        source_ref=f"preview-source-ref:{slug}:safe-ref-only",
        source_classification_ref=f"source-classification-ref:preview-rail:{slug}",
        bounded_preview_ref=f"bounded-preview-ref:preview-rail:{slug}",
        redaction_policy_ref=f"redaction-policy-ref:preview-rail:{slug}",
        attach_plan_ref=f"attach-plan-ref:preview-rail:{slug}",
        receipt_plan_ref=f"receipt-plan-ref:preview-rail:{slug}",
        proof_ref=RUNTIME_PREVIEW_RAIL_PROOF_REF,
        safe_summary=safe_summary,
        blocked_authority_refs=list(RUNTIME_PREVIEW_RAIL_BLOCKED_AUTHORITY_REFS),
        next_safe_action_refs=[f"next-safe-action-ref:preview-rail:{slug}:review"],
    )


def build_runtime_preview_rail_read_model(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
) -> RuntimePreviewRailReadModel:
    return build_runtime_preview_rail_read_model_from_authority_catalog(
        authority_decision_catalog=authority_decision_catalog
        or build_authority_decision_catalog(),
    )


def build_runtime_preview_rail_read_model_from_authority_catalog(
    *,
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry],
) -> RuntimePreviewRailReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    slots = [
        _slot(
            "safe-file-ref",
            display_label="Safe file ref preview",
            slot_kind=RuntimePreviewRailSlotKind.file_ref,
            slot_status=RuntimePreviewRailSlotStatus.safe_ref_ready,
            safe_summary=(
                "File preview rail can show a safe file ref and bounded summary "
                "plan; raw sensitive content stays omitted."
            ),
        ),
        _slot(
            "diff-ref",
            display_label="Diff ref preview",
            slot_kind=RuntimePreviewRailSlotKind.diff_ref,
            slot_status=RuntimePreviewRailSlotStatus.safe_ref_ready,
            safe_summary=(
                "Diff preview rail can show safe diff refs and proof links "
                "without applying patches."
            ),
        ),
        _slot(
            "artifact-ref",
            display_label="Artifact ref preview",
            slot_kind=RuntimePreviewRailSlotKind.artifact_ref,
            slot_status=RuntimePreviewRailSlotStatus.bounded_preview_placeholder,
            safe_summary=(
                "Artifact preview is a bounded placeholder until source "
                "classification and receipt attachment are promoted."
            ),
        ),
        _slot(
            "run-output-ref",
            display_label="Run output summary preview",
            slot_kind=RuntimePreviewRailSlotKind.run_output_ref,
            slot_status=RuntimePreviewRailSlotStatus.bounded_preview_placeholder,
            safe_summary=(
                "Run output preview can point at redacted output summaries only; "
                "raw logs and command output stay omitted."
            ),
        ),
        _slot(
            "proof-ref",
            display_label="Proof detail preview",
            slot_kind=RuntimePreviewRailSlotKind.proof_ref,
            slot_status=RuntimePreviewRailSlotStatus.bounded_preview_placeholder,
            safe_summary=(
                "Proof preview can link proof refs beside chat without rendering "
                "raw payloads."
            ),
        ),
        _slot(
            "runtime-event-ref",
            display_label="Delegated runtime event preview",
            slot_kind=RuntimePreviewRailSlotKind.runtime_event_ref,
            slot_status=RuntimePreviewRailSlotStatus.execution_blocked,
            safe_summary=(
                "Delegated runtime event preview remains blocked for direct "
                "runtime payload rendering."
            ),
        ),
    ]
    payload_for_hash: dict[str, object] = {
        "slots": [slot.model_dump(mode="json") for slot in slots],
        "blocked": list(RUNTIME_PREVIEW_RAIL_BLOCKED_AUTHORITY_REFS),
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
    }
    return RuntimePreviewRailReadModel(
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
        slots=slots,
        slot_count=len(slots),
        safe_ref_ready_count=sum(
            1
            for slot in slots
            if slot.slot_status == RuntimePreviewRailSlotStatus.safe_ref_ready.value
        ),
        bounded_preview_placeholder_count=sum(
            1
            for slot in slots
            if slot.slot_status
            == RuntimePreviewRailSlotStatus.bounded_preview_placeholder.value
        ),
        execution_blocked_count=sum(
            1
            for slot in slots
            if slot.slot_status == RuntimePreviewRailSlotStatus.execution_blocked.value
        ),
        blocked_authority_refs=list(RUNTIME_PREVIEW_RAIL_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            "promotion-path-ref:preview-rail:source-classification",
            "promotion-path-ref:preview-rail:redaction",
            "promotion-path-ref:preview-rail:bounded-preview",
            "promotion-path-ref:preview-rail:operator-attach",
            "promotion-path-ref:preview-rail:receipt",
            "promotion-path-ref:preview-rail:visual-tests",
        ],
        proof_refs=[
            RUNTIME_PREVIEW_RAIL_PROOF_REF,
            "proof-ref:preview-rail:safe-ref-contracts",
            "proof-ref:preview-rail:raw-payload-rendering-blocked",
        ],
        verifier_refs=[RUNTIME_PREVIEW_RAIL_VERIFIER_REF],
        next_safe_action_refs=[
            "next-safe-action-ref:preview-rail:bind-source-classification",
            "next-safe-action-ref:preview-rail:define-bounded-preview",
            "next-safe-action-ref:preview-rail:keep-live-browser-blocked",
        ],
    )


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None,
) -> AuthorityDecisionCatalogEntry:
    catalog = authority_decision_catalog or build_authority_decision_catalog()
    entries = {entry.lane_ref: entry for entry in catalog}
    if RUNTIME_PREVIEW_RAIL_AUTHORITY_MAPPING_REF not in entries:
        raise ValueError("RUNTIME_PREVIEW_RAIL_AUTHORITY_CATALOG_MISSING")
    return entries[RUNTIME_PREVIEW_RAIL_AUTHORITY_MAPPING_REF]
