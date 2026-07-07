from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.authority import (
    AuthorityDecisionCatalogEntry,
    build_authority_decision_catalog,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)


RUNTIME_RESULT_CLASSIFICATION_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-result-classification:v1"
)
RUNTIME_RESULT_CLASSIFICATION_ROUTE_REF = "GET /api/runtime/result-classification"
RUNTIME_RESULT_CLASSIFICATION_CLI_REF = "uaa runtime inspect-result-classification"
RUNTIME_RESULT_CLASSIFICATION_SNAPSHOT_REF = (
    "result-classification-snapshot-ref:runtime:taxonomy"
)
RUNTIME_RESULT_CLASSIFICATION_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-39:result-classification"
)
RUNTIME_RESULT_CLASSIFICATION_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-39:result-classification"
)
RUNTIME_RESULT_CLASSIFICATION_AUTHORITY_STATE_ROUTE_REF = (
    "GET /api/runtime/authority-state"
)
RUNTIME_RESULT_CLASSIFICATION_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_RESULT_CLASSIFICATION_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-result-classification-taxonomy"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_RESULT_CLASSIFICATION_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:result-classification-no-tool-output-as-truth",
    "blocked-authority:result-classification-no-action-authority",
    "blocked-authority:result-classification-no-mutation-without-receipt",
    "blocked-authority:result-classification-no-unverified-evidence-promotion",
    "blocked-authority:result-classification-no-raw-output-persistence",
    "blocked-authority:result-classification-no-provider-payload-persistence",
    "blocked-authority:result-classification-no-control-center-authority-mint",
)


class RuntimeResultClassKind(str, Enum):
    evidence = "evidence"
    mutation = "mutation"
    warning = "warning"
    blocked = "blocked"
    proposal = "proposal"
    diagnostic = "diagnostic"
    untrusted_data = "untrusted_data"


class RuntimeResultVerificationStatus(str, Enum):
    verified_safe_ref = "verified_safe_ref"
    receipt_required = "receipt_required"
    review_required = "review_required"
    blocked_authority = "blocked_authority"
    untrusted_until_verified = "untrusted_until_verified"


class RuntimeResultClassificationRecord(BaseModel):
    classification_ref: str
    result_kind: RuntimeResultClassKind
    display_label: str
    verification_status: RuntimeResultVerificationStatus
    provenance_policy_ref: str
    redaction_policy_ref: str
    receipt_requirement_ref: str
    proof_binding_ref: str
    safe_summary: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    visible_in_control_center: bool = True
    result_label_required: bool = True
    provenance_required: bool = True
    redaction_required: bool = True
    proof_binding_required: bool = True
    tool_output_as_truth_enabled: bool = False
    action_authority_enabled: bool = False
    mutation_without_receipt_enabled: bool = False
    unverified_evidence_promotion_enabled: bool = False
    raw_output_persisted: bool = False
    provider_payload_persisted: bool = False
    control_center_mints_authority: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_record(self) -> "RuntimeResultClassificationRecord":
        for value, field_name in [
            (self.classification_ref, "classification_ref"),
            (self.provenance_policy_ref, "provenance_policy_ref"),
            (self.redaction_policy_ref, "redaction_policy_ref"),
            (self.receipt_requirement_ref, "receipt_requirement_ref"),
            (self.proof_binding_ref, "proof_binding_ref"),
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
            (str(self.result_kind), "result_kind"),
            (self.display_label, "display_label"),
            (str(self.verification_status), "verification_status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "tool_output_as_truth_enabled": self.tool_output_as_truth_enabled,
            "action_authority_enabled": self.action_authority_enabled,
            "mutation_without_receipt_enabled": self.mutation_without_receipt_enabled,
            "unverified_evidence_promotion_enabled": (
                self.unverified_evidence_promotion_enabled
            ),
            "raw_output_persisted": self.raw_output_persisted,
            "provider_payload_persisted": self.provider_payload_persisted,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_RESULT_CLASSIFICATION_RECORD_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not (
            self.visible_in_control_center
            and self.result_label_required
            and self.provenance_required
            and self.redaction_required
            and self.proof_binding_required
        ):
            raise ValueError("RUNTIME_RESULT_CLASSIFICATION_LABELS_REQUIRED")
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_RESULT_CLASSIFICATION_BLOCKERS_REQUIRED")
        return self


class RuntimeResultClassificationReadModel(BaseModel):
    schema_version: str = "runtime_result_classification.v1"
    contract_ref: str = RUNTIME_RESULT_CLASSIFICATION_CONTRACT_REF
    status: str = "taxonomy_read_model_only"
    snapshot_ref: str = RUNTIME_RESULT_CLASSIFICATION_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:result-classification:pending"
    route_ref: str = RUNTIME_RESULT_CLASSIFICATION_ROUTE_REF
    cli_ref: str = RUNTIME_RESULT_CLASSIFICATION_CLI_REF
    authority_state_route_ref: str = (
        RUNTIME_RESULT_CLASSIFICATION_AUTHORITY_STATE_ROUTE_REF
    )
    authority_state_cli_ref: str = (
        RUNTIME_RESULT_CLASSIFICATION_AUTHORITY_STATE_CLI_REF
    )
    authority_state_mapping_ref: str
    authority_state_catalog_ref: str
    authority_state_decision_ref: str
    authority_state_decision_outcome: str
    authority_state_status: str
    authority_state_operator_message: str
    authority_state_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    safe_summary: str = (
        "Runtime and tool results are classified as evidence, mutation, warning, "
        "blocked, proposal, diagnostic, or untrusted data; classification labels "
        "do not make output truth or action authority."
    )
    classifications: list[RuntimeResultClassificationRecord] = Field(default_factory=list)
    classification_count: int = 0
    evidence_count: int = 0
    mutation_count: int = 0
    warning_count: int = 0
    blocked_count: int = 0
    proposal_count: int = 0
    diagnostic_count: int = 0
    untrusted_data_count: int = 0
    labels_visible: bool = True
    provenance_visible: bool = True
    redaction_visible: bool = True
    verification_status_visible: bool = True
    proof_binding_visible: bool = True
    receipt_requirement_visible: bool = True
    tool_output_as_truth_enabled: bool = False
    action_authority_enabled: bool = False
    mutation_without_receipt_enabled: bool = False
    unverified_evidence_promotion_enabled: bool = False
    raw_output_persisted: bool = False
    provider_payload_persisted: bool = False
    control_center_mints_authority: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "raw_outputs_omitted",
            "provider_payloads_omitted",
            "untrusted_data_bounded",
        ]
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeResultClassificationReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.authority_state_mapping_ref, "authority_state_mapping_ref"),
            (self.authority_state_catalog_ref, "authority_state_catalog_ref"),
            (self.authority_state_decision_ref, "authority_state_decision_ref"),
            (self.control_center_ref, "control_center_ref"),
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
            "authority_state_reason_refs",
            "unsupported_adapter_refs",
            "blocked_authority_refs",
            "promotion_path_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
        ):
            for value in getattr(self, field_name):
                validate_execution_ref(value, field_name)
        if (
            self.authority_state_mapping_ref
            != RUNTIME_RESULT_CLASSIFICATION_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_RESULT_CLASSIFICATION_AUTHORITY_MAPPING_STALE")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_RESULT_CLASSIFICATION_AUTHORITY_OUTCOME_UNKNOWN")
        for value in self.redactions_applied:
            validate_safe_execution_text(value, "redactions_applied")
        denied_flags = {
            "tool_output_as_truth_enabled": self.tool_output_as_truth_enabled,
            "action_authority_enabled": self.action_authority_enabled,
            "mutation_without_receipt_enabled": self.mutation_without_receipt_enabled,
            "unverified_evidence_promotion_enabled": (
                self.unverified_evidence_promotion_enabled
            ),
            "raw_output_persisted": self.raw_output_persisted,
            "provider_payload_persisted": self.provider_payload_persisted,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_RESULT_CLASSIFICATION_READ_MODEL_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if set(RUNTIME_RESULT_CLASSIFICATION_BLOCKED_AUTHORITY_REFS) - set(
            self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_RESULT_CLASSIFICATION_BLOCKERS_REQUIRED")
        if self.classification_count != len(self.classifications):
            raise ValueError("RUNTIME_RESULT_CLASSIFICATION_COUNT_MISMATCH")
        return self


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _classification(
    kind: RuntimeResultClassKind,
    verification_status: RuntimeResultVerificationStatus,
    summary: str,
) -> RuntimeResultClassificationRecord:
    token = kind.value.replace("_", "-")
    return RuntimeResultClassificationRecord(
        classification_ref=f"result-classification-ref:runtime:{token}",
        result_kind=kind,
        display_label=kind.value.replace("_", " ").title(),
        verification_status=verification_status,
        provenance_policy_ref=f"provenance-policy-ref:runtime-result:{token}",
        redaction_policy_ref=f"redaction-policy-ref:runtime-result:{token}",
        receipt_requirement_ref=f"receipt-requirement-ref:runtime-result:{token}",
        proof_binding_ref=f"proof-binding-ref:runtime-result:{token}",
        safe_summary=summary,
        blocked_authority_refs=list(
            RUNTIME_RESULT_CLASSIFICATION_BLOCKED_AUTHORITY_REFS
        ),
        promotion_path_refs=[
            f"promotion-path-ref:runtime-result:{token}:envelope",
            f"promotion-path-ref:runtime-result:{token}:proof-binding",
        ],
        next_safe_action_refs=[
            f"next-safe-action-ref:runtime-result:{token}:classification-tests"
        ],
    )


def build_runtime_result_classification_read_model(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
) -> (
    RuntimeResultClassificationReadModel
):
    return build_runtime_result_classification_read_model_from_authority_catalog(
        authority_decision_catalog=authority_decision_catalog
    )


def build_runtime_result_classification_read_model_from_authority_catalog(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
) -> RuntimeResultClassificationReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    classifications = [
        _classification(
            RuntimeResultClassKind.evidence,
            RuntimeResultVerificationStatus.verified_safe_ref,
            "Evidence results require source refs, redaction, and proof binding.",
        ),
        _classification(
            RuntimeResultClassKind.mutation,
            RuntimeResultVerificationStatus.receipt_required,
            "Mutation results require exact receipt refs before any claim.",
        ),
        _classification(
            RuntimeResultClassKind.warning,
            RuntimeResultVerificationStatus.review_required,
            "Warning results are operator-visible and require review posture.",
        ),
        _classification(
            RuntimeResultClassKind.blocked,
            RuntimeResultVerificationStatus.blocked_authority,
            "Blocked results explain missing authority and next safe actions.",
        ),
        _classification(
            RuntimeResultClassKind.proposal,
            RuntimeResultVerificationStatus.review_required,
            "Proposal results remain untrusted drafts until separately approved.",
        ),
        _classification(
            RuntimeResultClassKind.diagnostic,
            RuntimeResultVerificationStatus.review_required,
            "Diagnostic results are troubleshooting evidence, not authority.",
        ),
        _classification(
            RuntimeResultClassKind.untrusted_data,
            RuntimeResultVerificationStatus.untrusted_until_verified,
            "Untrusted data is bounded and cannot act as instructions or truth.",
        ),
    ]
    payload = {
        "contract_ref": RUNTIME_RESULT_CLASSIFICATION_CONTRACT_REF,
        "snapshot_ref": RUNTIME_RESULT_CLASSIFICATION_SNAPSHOT_REF,
        "route_ref": RUNTIME_RESULT_CLASSIFICATION_ROUTE_REF,
        "cli_ref": RUNTIME_RESULT_CLASSIFICATION_CLI_REF,
        "authority_state_mapping_ref": authority_entry.lane_ref,
        "authority_state_catalog_ref": authority_entry.catalog_ref,
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
        "authority_state_status": authority_entry.status,
        "authority_state_operator_message": authority_entry.decision.operator_message,
        "authority_state_reason_refs": list(authority_entry.decision.reason_refs),
        "unsupported_adapter_refs": list(authority_entry.unsupported_adapter_refs),
        "classifications": classifications,
        "classification_count": len(classifications),
        "evidence_count": sum(
            item.result_kind == RuntimeResultClassKind.evidence
            for item in classifications
        ),
        "mutation_count": sum(
            item.result_kind == RuntimeResultClassKind.mutation
            for item in classifications
        ),
        "warning_count": sum(
            item.result_kind == RuntimeResultClassKind.warning
            for item in classifications
        ),
        "blocked_count": sum(
            item.result_kind == RuntimeResultClassKind.blocked
            for item in classifications
        ),
        "proposal_count": sum(
            item.result_kind == RuntimeResultClassKind.proposal
            for item in classifications
        ),
        "diagnostic_count": sum(
            item.result_kind == RuntimeResultClassKind.diagnostic
            for item in classifications
        ),
        "untrusted_data_count": sum(
            item.result_kind == RuntimeResultClassKind.untrusted_data
            for item in classifications
        ),
        "blocked_authority_refs": list(
            RUNTIME_RESULT_CLASSIFICATION_BLOCKED_AUTHORITY_REFS
        ),
        "promotion_path_refs": [
            "promotion-path-ref:result-classification:result-envelope",
            "promotion-path-ref:result-classification:provenance",
            "promotion-path-ref:result-classification:redaction",
            "promotion-path-ref:result-classification:verification-status",
            "promotion-path-ref:result-classification:proof-binding",
        ],
        "proof_refs": [RUNTIME_RESULT_CLASSIFICATION_PROOF_REF],
        "verifier_refs": [RUNTIME_RESULT_CLASSIFICATION_VERIFIER_REF],
        "next_safe_action_refs": [
            "next-safe-action-ref:result-classification:envelope-contract",
            "next-safe-action-ref:result-classification:ui-label-regression",
        ],
    }
    snapshot_material = {
        "contract_ref": payload["contract_ref"],
        "route_ref": payload["route_ref"],
        "classification_refs": [
            item.classification_ref for item in classifications
        ],
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
        "blocked_authority_refs": payload["blocked_authority_refs"],
    }
    payload["snapshot_hash_ref"] = (
        "snapshot-hash-ref:result-classification:"
        + hashlib.sha256(
            json.dumps(snapshot_material, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
    )
    return RuntimeResultClassificationReadModel(**payload)


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None,
) -> AuthorityDecisionCatalogEntry:
    catalog = authority_decision_catalog or build_authority_decision_catalog()
    for entry in catalog:
        if entry.lane_ref == RUNTIME_RESULT_CLASSIFICATION_AUTHORITY_MAPPING_REF:
            return entry
    raise ValueError("RUNTIME_RESULT_CLASSIFICATION_AUTHORITY_MAPPING_MISSING")
