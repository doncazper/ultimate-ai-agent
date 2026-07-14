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
from ultimate_ai_agent.core.runtime_gateway.skill_marketplace_catalog import (
    RuntimeSkillMarketplaceCatalogSnapshot,
    build_runtime_skill_marketplace_catalog_snapshot,
)


RUNTIME_SKILL_MARKETPLACE_POSTURE_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-skill-marketplace-posture:v1"
)
RUNTIME_SKILL_MARKETPLACE_POSTURE_ROUTE_REF = (
    "GET /api/runtime/skill-marketplace-posture"
)
RUNTIME_SKILL_MARKETPLACE_POSTURE_CLI_REF = (
    "uaa runtime inspect-skill-marketplace-posture"
)
RUNTIME_SKILL_MARKETPLACE_POSTURE_DOC_REF = (
    "docs/runtime/UAA_HERMES_RUNTIME_SKILL_MARKETPLACE_POSTURE.md"
)
RUNTIME_SKILL_MARKETPLACE_POSTURE_SNAPSHOT_REF = (
    "skill-marketplace-posture-snapshot-ref:runtime:phase-45"
)
RUNTIME_SKILL_MARKETPLACE_POSTURE_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-45:skill-marketplace-posture"
)
RUNTIME_SKILL_MARKETPLACE_POSTURE_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-45:skill-marketplace-posture"
)
RUNTIME_SKILL_MARKETPLACE_POSTURE_AUTHORITY_STATE_ROUTE_REF = (
    "GET /api/runtime/authority-state"
)
RUNTIME_SKILL_MARKETPLACE_POSTURE_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_SKILL_MARKETPLACE_POSTURE_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-skill-marketplace-posture-read-model"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_SKILL_MARKETPLACE_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:skill-marketplace-no-external-code-execution",
    "blocked-authority:skill-marketplace-no-direct-install",
    "blocked-authority:skill-marketplace-no-runtime-import",
    "blocked-authority:skill-marketplace-no-automatic-skill-write",
    "blocked-authority:skill-marketplace-no-provider-call",
    "blocked-authority:skill-marketplace-no-browser-automation",
    "blocked-authority:skill-marketplace-no-connector-write",
    "blocked-authority:skill-marketplace-no-raw-marketplace-persistence",
    "blocked-authority:skill-marketplace-no-control-center-authority-mint",
)


class RuntimeSkillMarketplaceStageKind(str, Enum):
    external_discovery_signal = "external_discovery_signal"
    quarantine = "quarantine"
    review = "review"
    adaptation_proposal = "adaptation_proposal"
    uaa_owned_adaptation = "uaa_owned_adaptation"
    activation_grant = "activation_grant"
    execution_block = "execution_block"


class RuntimeSkillMarketplaceStageStatus(str, Enum):
    signal_only = "signal_only"
    review_required = "review_required"
    blocked_until_owned_adaptation = "blocked_until_owned_adaptation"


class RuntimeSkillMarketplaceStage(BaseModel):
    stage_ref: str
    stage_kind: RuntimeSkillMarketplaceStageKind
    display_label: str
    status: RuntimeSkillMarketplaceStageStatus
    safe_summary: str
    signal_policy_ref: str
    quarantine_ref: str
    review_ref: str
    adaptation_ref: str
    activation_grant_ref: str
    safe_disable_ref: str
    receipt_plan_ref: str
    proof_ref: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    external_popularity_is_trust: bool = False
    external_code_execution_enabled: bool = False
    direct_marketplace_install_enabled: bool = False
    runtime_import_enabled: bool = False
    automatic_skill_write_enabled: bool = False
    provider_call_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    raw_marketplace_payload_persisted: bool = False
    control_center_mints_authority: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_stage(self) -> "RuntimeSkillMarketplaceStage":
        for value, field_name in [
            (self.stage_ref, "stage_ref"),
            (self.signal_policy_ref, "signal_policy_ref"),
            (self.quarantine_ref, "quarantine_ref"),
            (self.review_ref, "review_ref"),
            (self.adaptation_ref, "adaptation_ref"),
            (self.activation_grant_ref, "activation_grant_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.receipt_plan_ref, "receipt_plan_ref"),
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
            (str(self.stage_kind), "stage_kind"),
            (self.display_label, "display_label"),
            (str(self.status), "status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "external_popularity_is_trust": self.external_popularity_is_trust,
            "external_code_execution_enabled": self.external_code_execution_enabled,
            "direct_marketplace_install_enabled": (
                self.direct_marketplace_install_enabled
            ),
            "runtime_import_enabled": self.runtime_import_enabled,
            "automatic_skill_write_enabled": self.automatic_skill_write_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "raw_marketplace_payload_persisted": (
                self.raw_marketplace_payload_persisted
            ),
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_SKILL_MARKETPLACE_STAGE_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_STAGE_BLOCKERS_REQUIRED")
        return self


class RuntimeSkillMarketplacePostureReadModel(BaseModel):
    schema_version: str = "runtime_skill_marketplace_posture.v1"
    contract_ref: str = RUNTIME_SKILL_MARKETPLACE_POSTURE_CONTRACT_REF
    status: str = "signal_review_adaptation_only"
    snapshot_ref: str = RUNTIME_SKILL_MARKETPLACE_POSTURE_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:skill-marketplace-posture:pending"
    route_ref: str = RUNTIME_SKILL_MARKETPLACE_POSTURE_ROUTE_REF
    cli_ref: str = RUNTIME_SKILL_MARKETPLACE_POSTURE_CLI_REF
    doc_ref: str = RUNTIME_SKILL_MARKETPLACE_POSTURE_DOC_REF
    authority_state_route_ref: str = (
        RUNTIME_SKILL_MARKETPLACE_POSTURE_AUTHORITY_STATE_ROUTE_REF
    )
    authority_state_cli_ref: str = (
        RUNTIME_SKILL_MARKETPLACE_POSTURE_AUTHORITY_STATE_CLI_REF
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
        "External and agent-created skills are discovery signals only until "
        "quarantined, reviewed, converted into UAA-owned adaptations, and "
        "separately granted activation authority."
    )
    catalog: RuntimeSkillMarketplaceCatalogSnapshot = Field(
        default_factory=build_runtime_skill_marketplace_catalog_snapshot
    )
    stages: list[RuntimeSkillMarketplaceStage] = Field(default_factory=list)
    stage_count: int = 0
    review_required_count: int = 0
    blocked_execution_count: int = 0
    external_popularity_is_trust: bool = False
    external_code_execution_enabled: bool = False
    direct_marketplace_install_enabled: bool = False
    runtime_import_enabled: bool = False
    automatic_skill_write_enabled: bool = False
    provider_call_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    raw_marketplace_payload_persisted: bool = False
    control_center_mints_authority: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: (
            list(GOVERNED_RUNTIME_REDACTIONS)
            + [
                "raw_marketplace_payloads_omitted",
                "external_code_omitted",
                "publisher_material_omitted",
            ]
        )
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeSkillMarketplacePostureReadModel":
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
            (self.doc_ref, "doc_ref"),
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
        for value in self.redactions_applied:
            validate_safe_execution_text(value, "redactions_applied")
        if (
            self.authority_state_mapping_ref
            != RUNTIME_SKILL_MARKETPLACE_POSTURE_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_AUTHORITY_MAPPING_MISMATCH")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_AUTHORITY_DECISION_INVALID")
        denied_flags = {
            "external_popularity_is_trust": self.external_popularity_is_trust,
            "external_code_execution_enabled": self.external_code_execution_enabled,
            "direct_marketplace_install_enabled": (
                self.direct_marketplace_install_enabled
            ),
            "runtime_import_enabled": self.runtime_import_enabled,
            "automatic_skill_write_enabled": self.automatic_skill_write_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "raw_marketplace_payload_persisted": (
                self.raw_marketplace_payload_persisted
            ),
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_SKILL_MARKETPLACE_READ_MODEL_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if set(RUNTIME_SKILL_MARKETPLACE_BLOCKED_AUTHORITY_REFS) - set(
            self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_BLOCKERS_REQUIRED")
        if self.stage_count != len(self.stages):
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_COUNT_MISMATCH")
        if self.review_required_count != len(
            [
                stage
                for stage in self.stages
                if stage.status == RuntimeSkillMarketplaceStageStatus.review_required
            ]
        ):
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_REVIEW_COUNT_MISMATCH")
        if self.blocked_execution_count != len(
            [
                stage
                for stage in self.stages
                if stage.stage_kind == RuntimeSkillMarketplaceStageKind.execution_block
            ]
        ):
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_BLOCKED_COUNT_MISMATCH")
        if self.snapshot_hash_ref != _snapshot_hash_ref(self):
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_SNAPSHOT_HASH_MISMATCH")
        return self


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _stage(
    stage_kind: RuntimeSkillMarketplaceStageKind,
    display_label: str,
    status: RuntimeSkillMarketplaceStageStatus,
    summary: str,
) -> RuntimeSkillMarketplaceStage:
    token = stage_kind.value.replace("_", "-")
    return RuntimeSkillMarketplaceStage(
        stage_ref=f"skill-marketplace-stage-ref:runtime:{token}",
        stage_kind=stage_kind,
        display_label=display_label,
        status=status,
        safe_summary=summary,
        signal_policy_ref=f"signal-policy-ref:skill-marketplace:{token}",
        quarantine_ref=f"quarantine-ref:skill-marketplace:{token}",
        review_ref=f"review-ref:skill-marketplace:{token}",
        adaptation_ref=f"adaptation-ref:skill-marketplace:{token}",
        activation_grant_ref=f"activation-grant-ref:skill-marketplace:{token}",
        safe_disable_ref=f"safe-disable-ref:skill-marketplace:{token}",
        receipt_plan_ref=f"receipt-plan-ref:skill-marketplace:{token}",
        proof_ref=f"proof-ref:skill-marketplace:{token}",
        blocked_authority_refs=list(RUNTIME_SKILL_MARKETPLACE_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            f"promotion-path-ref:skill-marketplace:{token}:quarantine",
            f"promotion-path-ref:skill-marketplace:{token}:review",
            f"promotion-path-ref:skill-marketplace:{token}:uaa-owned-adaptation",
            f"promotion-path-ref:skill-marketplace:{token}:activation-grant",
        ],
        next_safe_action_refs=[
            f"next-safe-action-ref:skill-marketplace:{token}:review-contract"
        ],
    )


def build_runtime_skill_marketplace_posture_read_model(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
) -> RuntimeSkillMarketplacePostureReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    catalog = build_runtime_skill_marketplace_catalog_snapshot()
    stages = [
        _stage(
            RuntimeSkillMarketplaceStageKind.external_discovery_signal,
            "External discovery signals",
            RuntimeSkillMarketplaceStageStatus.signal_only,
            "Stars, downloads, reviews, screenshots, and publisher claims are "
            "discovery signals only, never trust.",
        ),
        _stage(
            RuntimeSkillMarketplaceStageKind.quarantine,
            "Quarantine",
            RuntimeSkillMarketplaceStageStatus.review_required,
            "External or agent-created skill ideas are quarantined before review.",
        ),
        _stage(
            RuntimeSkillMarketplaceStageKind.review,
            "Review",
            RuntimeSkillMarketplaceStageStatus.review_required,
            "Review captures source, safety, license, product fit, and blocked "
            "authority posture without running external code.",
        ),
        _stage(
            RuntimeSkillMarketplaceStageKind.adaptation_proposal,
            "Adaptation proposal",
            RuntimeSkillMarketplaceStageStatus.review_required,
            "Adaptation proposals are diffs or plans for UAA-owned work, not "
            "automatic skill writes.",
        ),
        _stage(
            RuntimeSkillMarketplaceStageKind.uaa_owned_adaptation,
            "UAA-owned adaptation",
            RuntimeSkillMarketplaceStageStatus.review_required,
            "Only reviewed UAA-owned adaptations can later request activation grants.",
        ),
        _stage(
            RuntimeSkillMarketplaceStageKind.activation_grant,
            "Activation grant",
            RuntimeSkillMarketplaceStageStatus.blocked_until_owned_adaptation,
            "Activation remains blocked until manifest, scan, approval, receipts, "
            "rollback, and safe-disable posture are proven.",
        ),
        _stage(
            RuntimeSkillMarketplaceStageKind.execution_block,
            "Execution block",
            RuntimeSkillMarketplaceStageStatus.blocked_until_owned_adaptation,
            "External skill execution, direct marketplace install, and runtime "
            "import remain blocked.",
        ),
    ]
    payload = {
        "route_ref": RUNTIME_SKILL_MARKETPLACE_POSTURE_ROUTE_REF,
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
        "catalog": catalog,
        "stages": stages,
        "stage_count": len(stages),
        "review_required_count": len(
            [
                stage
                for stage in stages
                if stage.status == RuntimeSkillMarketplaceStageStatus.review_required
            ]
        ),
        "blocked_execution_count": len(
            [
                stage
                for stage in stages
                if stage.stage_kind == RuntimeSkillMarketplaceStageKind.execution_block
            ]
        ),
        "blocked_authority_refs": list(
            RUNTIME_SKILL_MARKETPLACE_BLOCKED_AUTHORITY_REFS
        ),
        "promotion_path_refs": [
            "promotion-path-ref:skill-marketplace:reviewed-uaa-owned-adaptation",
            "promotion-path-ref:skill-marketplace:local-registry-entry",
            "promotion-path-ref:skill-marketplace:static-product-review",
            "promotion-path-ref:skill-marketplace:approval-safe-disable",
            "promotion-path-ref:skill-marketplace:rollback-receipt-proof",
        ],
        "proof_refs": [RUNTIME_SKILL_MARKETPLACE_POSTURE_PROOF_REF],
        "verifier_refs": [RUNTIME_SKILL_MARKETPLACE_POSTURE_VERIFIER_REF],
        "next_safe_action_refs": [
            "next-safe-action-ref:skill-marketplace:adaptation-review-schema",
            "next-safe-action-ref:skill-marketplace:local-registry-contract",
        ],
    }
    unvalidated = RuntimeSkillMarketplacePostureReadModel.model_construct(**payload)
    payload["snapshot_hash_ref"] = _snapshot_hash_ref(unvalidated)
    return RuntimeSkillMarketplacePostureReadModel(**payload)


def _snapshot_hash_ref(read_model: RuntimeSkillMarketplacePostureReadModel) -> str:
    material = read_model.model_dump(
        mode="json",
        exclude={"snapshot_hash_ref"},
    )
    digest = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"snapshot-hash-ref:skill-marketplace-posture:{digest}"


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None,
) -> AuthorityDecisionCatalogEntry:
    catalog = authority_decision_catalog or build_authority_decision_catalog()
    for entry in catalog:
        if entry.lane_ref == RUNTIME_SKILL_MARKETPLACE_POSTURE_AUTHORITY_MAPPING_REF:
            return entry
    raise ValueError("RUNTIME_SKILL_MARKETPLACE_AUTHORITY_MAPPING_MISSING")
