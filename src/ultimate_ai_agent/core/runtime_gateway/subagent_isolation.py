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


RUNTIME_SUBAGENT_ISOLATION_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-subagent-isolation:v1"
)
RUNTIME_SUBAGENT_ISOLATION_ROUTE_REF = "GET /api/runtime/subagent-isolation"
RUNTIME_SUBAGENT_ISOLATION_CLI_REF = "uaa runtime inspect-subagent-isolation"
RUNTIME_SUBAGENT_ISOLATION_SNAPSHOT_REF = (
    "subagent-isolation-snapshot-ref:runtime:roles"
)
RUNTIME_SUBAGENT_ISOLATION_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-32:subagent-isolation"
)
RUNTIME_SUBAGENT_ISOLATION_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-32:subagent-isolation"
)
RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_STATE_ROUTE_REF = (
    "GET /api/runtime/authority-state"
)
RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-subagent-isolation-live-dispatch"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_SUBAGENT_ISOLATION_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:subagent-isolation-no-live-dispatch",
    "blocked-authority:subagent-isolation-no-background-fanout",
    "blocked-authority:subagent-isolation-no-cross-agent-memory-transfer",
    "blocked-authority:subagent-isolation-no-tool-sharing",
    "blocked-authority:subagent-isolation-no-autonomous-delegation",
    "blocked-authority:subagent-isolation-no-provider-call",
    "blocked-authority:subagent-isolation-no-shell-execution",
    "blocked-authority:subagent-isolation-no-connector-write",
    "blocked-authority:subagent-isolation-no-control-center-authority-mint",
    "blocked-authority:subagent-isolation-no-raw-transcript-persistence",
)


class RuntimeSubagentRoleKind(str, Enum):
    implementer = "implementer"
    reviewer = "reviewer"
    verifier = "verifier"


class RuntimeSubagentReadinessStatus(str, Enum):
    contract_ready = "contract_ready"
    review_ready = "review_ready"
    blocked_dispatch = "blocked_dispatch"


class RuntimeSubagentArtifactKind(str, Enum):
    plan_comparison = "plan_comparison"
    review_packet = "review_packet"
    disagreement_summary = "disagreement_summary"


class RuntimeSubagentIsolationRole(BaseModel):
    role_ref: str
    display_label: str
    role_kind: RuntimeSubagentRoleKind
    readiness_status: RuntimeSubagentReadinessStatus
    scope_envelope_ref: str
    context_pack_ref: str
    tool_grant_ref: str
    memory_grant_ref: str
    budget_ref: str
    kill_switch_ref: str
    receipt_plan_ref: str
    proof_ref: str
    safe_summary: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    live_dispatch_enabled: bool = False
    background_fanout_enabled: bool = False
    cross_agent_memory_transfer_enabled: bool = False
    tool_sharing_enabled: bool = False
    autonomous_delegation_enabled: bool = False
    provider_call_enabled: bool = False
    shell_execution_enabled: bool = False
    connector_write_enabled: bool = False
    raw_transcript_persisted: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_role(self) -> "RuntimeSubagentIsolationRole":
        for value, field_name in [
            (self.role_ref, "role_ref"),
            (self.scope_envelope_ref, "scope_envelope_ref"),
            (self.context_pack_ref, "context_pack_ref"),
            (self.tool_grant_ref, "tool_grant_ref"),
            (self.memory_grant_ref, "memory_grant_ref"),
            (self.budget_ref, "budget_ref"),
            (self.kill_switch_ref, "kill_switch_ref"),
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.proof_ref, "proof_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in ("blocked_authority_refs", "next_safe_action_refs"):
            for value in getattr(self, field_name):
                validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.display_label, "display_label"),
            (str(self.role_kind), "role_kind"),
            (str(self.readiness_status), "readiness_status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "live_dispatch_enabled": self.live_dispatch_enabled,
            "background_fanout_enabled": self.background_fanout_enabled,
            "cross_agent_memory_transfer_enabled": (
                self.cross_agent_memory_transfer_enabled
            ),
            "tool_sharing_enabled": self.tool_sharing_enabled,
            "autonomous_delegation_enabled": self.autonomous_delegation_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "raw_transcript_persisted": self.raw_transcript_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_SUBAGENT_ROLE_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_SUBAGENT_ROLE_BLOCKERS_REQUIRED")
        return self


class RuntimeSubagentReviewArtifact(BaseModel):
    artifact_ref: str
    artifact_kind: RuntimeSubagentArtifactKind
    display_label: str
    source_role_refs: list[str] = Field(default_factory=list)
    safe_summary: str
    proof_refs: list[str] = Field(default_factory=list)
    raw_agent_output_persisted: bool = False
    executable_authority: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_artifact(self) -> "RuntimeSubagentReviewArtifact":
        validate_execution_ref(self.artifact_ref, "artifact_ref")
        for field_name in ("source_role_refs", "proof_refs"):
            for value in getattr(self, field_name):
                validate_execution_ref(value, field_name)
        for value, field_name in [
            (str(self.artifact_kind), "artifact_kind"),
            (self.display_label, "display_label"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        if self.raw_agent_output_persisted or self.executable_authority:
            raise ValueError("RUNTIME_SUBAGENT_ARTIFACT_AUTHORITY_DENIED")
        return self


class RuntimeSubagentIsolationReadModel(BaseModel):
    schema_version: str = "runtime_subagent_isolation.v1"
    contract_ref: str = RUNTIME_SUBAGENT_ISOLATION_CONTRACT_REF
    status: str = "identity_isolation_readiness"
    snapshot_ref: str = RUNTIME_SUBAGENT_ISOLATION_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-subagent-isolation:pending"
    route_ref: str = RUNTIME_SUBAGENT_ISOLATION_ROUTE_REF
    cli_ref: str = RUNTIME_SUBAGENT_ISOLATION_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    authority_state_route_ref: str = RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_STATE_ROUTE_REF
    authority_state_cli_ref: str = RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_STATE_CLI_REF
    authority_state_mapping_ref: str
    authority_state_catalog_ref: str
    authority_state_decision_ref: str
    authority_state_decision_outcome: str
    authority_state_status: str
    authority_state_operator_message: str
    authority_state_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "Subagent isolation posture exposes role contracts, scope envelopes, "
        "review artifacts, and blocked dispatch labels only."
    )
    roles: list[RuntimeSubagentIsolationRole] = Field(default_factory=list)
    review_artifacts: list[RuntimeSubagentReviewArtifact] = Field(default_factory=list)
    role_count: int = 0
    review_artifact_count: int = 0
    contract_ready_count: int = 0
    review_ready_count: int = 0
    blocked_dispatch_count: int = 0
    identity_registry_visible: bool = True
    scope_envelopes_visible: bool = True
    context_pack_grants_visible: bool = True
    tool_grants_visible: bool = True
    memory_grants_visible: bool = True
    budget_visible: bool = True
    kill_switch_visible: bool = True
    receipt_plan_visible: bool = True
    proof_visible: bool = True
    live_dispatch_enabled: bool = False
    background_fanout_enabled: bool = False
    cross_agent_memory_transfer_enabled: bool = False
    tool_sharing_enabled: bool = False
    autonomous_delegation_enabled: bool = False
    provider_call_enabled: bool = False
    shell_execution_enabled: bool = False
    connector_write_enabled: bool = False
    control_center_mints_authority: bool = False
    raw_transcript_persisted: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "raw_agent_outputs_omitted",
            "raw_transcripts_omitted",
            "provider_payloads_omitted",
        ]
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeSubagentIsolationReadModel":
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
            != RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_MAPPING_UNKNOWN")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_OUTCOME_UNKNOWN")
        if self.role_count != len(self.roles):
            raise ValueError("RUNTIME_SUBAGENT_ROLE_COUNT_DRIFT")
        if self.review_artifact_count != len(self.review_artifacts):
            raise ValueError("RUNTIME_SUBAGENT_ARTIFACT_COUNT_DRIFT")
        status_counts = {
            RuntimeSubagentReadinessStatus.contract_ready.value: (
                self.contract_ready_count
            ),
            RuntimeSubagentReadinessStatus.review_ready.value: self.review_ready_count,
            RuntimeSubagentReadinessStatus.blocked_dispatch.value: (
                self.blocked_dispatch_count
            ),
        }
        for status, expected in status_counts.items():
            actual = sum(1 for role in self.roles if role.readiness_status == status)
            if actual != expected:
                raise ValueError("RUNTIME_SUBAGENT_STATUS_COUNT_DRIFT")
        visibility_flags = {
            "identity_registry_visible": self.identity_registry_visible,
            "scope_envelopes_visible": self.scope_envelopes_visible,
            "context_pack_grants_visible": self.context_pack_grants_visible,
            "tool_grants_visible": self.tool_grants_visible,
            "memory_grants_visible": self.memory_grants_visible,
            "budget_visible": self.budget_visible,
            "kill_switch_visible": self.kill_switch_visible,
            "receipt_plan_visible": self.receipt_plan_visible,
            "proof_visible": self.proof_visible,
        }
        missing = [name for name, value in visibility_flags.items() if not value]
        if missing:
            raise ValueError(
                "RUNTIME_SUBAGENT_ISOLATION_VISIBILITY_REQUIRED: "
                + ", ".join(missing)
            )
        denied_flags = {
            "live_dispatch_enabled": self.live_dispatch_enabled,
            "background_fanout_enabled": self.background_fanout_enabled,
            "cross_agent_memory_transfer_enabled": (
                self.cross_agent_memory_transfer_enabled
            ),
            "tool_sharing_enabled": self.tool_sharing_enabled,
            "autonomous_delegation_enabled": self.autonomous_delegation_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "control_center_mints_authority": self.control_center_mints_authority,
            "raw_transcript_persisted": self.raw_transcript_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        for ref in RUNTIME_SUBAGENT_ISOLATION_BLOCKED_AUTHORITY_REFS:
            if ref not in self.blocked_authority_refs:
                raise ValueError("RUNTIME_SUBAGENT_ISOLATION_BLOCKER_MISSING")
        if RUNTIME_SUBAGENT_ISOLATION_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_SUBAGENT_ISOLATION_PROOF_REF_REQUIRED")
        if RUNTIME_SUBAGENT_ISOLATION_VERIFIER_REF not in self.verifier_refs:
            raise ValueError("RUNTIME_SUBAGENT_ISOLATION_VERIFIER_REF_REQUIRED")
        return self


def _snapshot_hash_ref(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(encoded).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-subagent-isolation:{digest}"


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _role(
    slug: str,
    *,
    display_label: str,
    role_kind: RuntimeSubagentRoleKind,
    readiness_status: RuntimeSubagentReadinessStatus,
    safe_summary: str,
) -> RuntimeSubagentIsolationRole:
    return RuntimeSubagentIsolationRole(
        role_ref=f"subagent-role-ref:{slug}",
        display_label=display_label,
        role_kind=role_kind,
        readiness_status=readiness_status,
        scope_envelope_ref=f"scope-envelope-ref:subagent:{slug}",
        context_pack_ref=f"context-pack-ref:subagent:{slug}:safe-summary",
        tool_grant_ref=f"tool-grant-ref:subagent:{slug}:none-active",
        memory_grant_ref=f"memory-grant-ref:subagent:{slug}:read-none",
        budget_ref=f"budget-ref:subagent:{slug}:review-only",
        kill_switch_ref=f"kill-switch-ref:subagent:{slug}:required-before-dispatch",
        receipt_plan_ref=f"receipt-plan-ref:subagent:{slug}",
        proof_ref=RUNTIME_SUBAGENT_ISOLATION_PROOF_REF,
        safe_summary=safe_summary,
        blocked_authority_refs=list(RUNTIME_SUBAGENT_ISOLATION_BLOCKED_AUTHORITY_REFS),
        next_safe_action_refs=[f"next-safe-action-ref:subagent:{slug}:review"],
    )


def _artifact(
    slug: str,
    *,
    artifact_kind: RuntimeSubagentArtifactKind,
    display_label: str,
    source_role_refs: list[str],
    safe_summary: str,
) -> RuntimeSubagentReviewArtifact:
    return RuntimeSubagentReviewArtifact(
        artifact_ref=f"subagent-artifact-ref:{slug}",
        artifact_kind=artifact_kind,
        display_label=display_label,
        source_role_refs=source_role_refs,
        safe_summary=safe_summary,
        proof_refs=[RUNTIME_SUBAGENT_ISOLATION_PROOF_REF],
    )


def build_runtime_subagent_isolation_read_model(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
) -> RuntimeSubagentIsolationReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    roles = [
        _role(
            "implementer",
            display_label="Implementer",
            role_kind=RuntimeSubagentRoleKind.implementer,
            readiness_status=RuntimeSubagentReadinessStatus.contract_ready,
            safe_summary=(
                "Implementer identity contract is ready for review, but live "
                "dispatch and tool grants remain blocked."
            ),
        ),
        _role(
            "reviewer",
            display_label="Reviewer",
            role_kind=RuntimeSubagentRoleKind.reviewer,
            readiness_status=RuntimeSubagentReadinessStatus.review_ready,
            safe_summary=(
                "Reviewer role can be represented as proposal metadata; "
                "cross-agent memory transfer and tool sharing remain blocked."
            ),
        ),
        _role(
            "verifier",
            display_label="Verifier",
            role_kind=RuntimeSubagentRoleKind.verifier,
            readiness_status=RuntimeSubagentReadinessStatus.blocked_dispatch,
            safe_summary=(
                "Verifier role documents future proof duties; background fan-out "
                "and runtime invocation are not enabled."
            ),
        ),
    ]
    role_refs = [role.role_ref for role in roles]
    review_artifacts = [
        _artifact(
            "plan-comparison",
            artifact_kind=RuntimeSubagentArtifactKind.plan_comparison,
            display_label="Plan comparison",
            source_role_refs=role_refs[:2],
            safe_summary=(
                "Compares role-scoped plans by safe refs only; raw agent output "
                "is omitted."
            ),
        ),
        _artifact(
            "review-packet",
            artifact_kind=RuntimeSubagentArtifactKind.review_packet,
            display_label="Review packet",
            source_role_refs=role_refs,
            safe_summary=(
                "Bundles review posture, proof refs, and blockers without "
                "granting executable authority."
            ),
        ),
        _artifact(
            "disagreement-summary",
            artifact_kind=RuntimeSubagentArtifactKind.disagreement_summary,
            display_label="Disagreement summary",
            source_role_refs=role_refs[:2],
            safe_summary=(
                "Captures disagreement categories as safe metadata only."
            ),
        ),
    ]
    payload_for_hash: dict[str, object] = {
        "roles": [role.model_dump(mode="json") for role in roles],
        "review_artifacts": [
            artifact.model_dump(mode="json") for artifact in review_artifacts
        ],
        "blocked": list(RUNTIME_SUBAGENT_ISOLATION_BLOCKED_AUTHORITY_REFS),
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
    }
    return RuntimeSubagentIsolationReadModel(
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
        roles=roles,
        review_artifacts=review_artifacts,
        role_count=len(roles),
        review_artifact_count=len(review_artifacts),
        contract_ready_count=sum(
            1
            for role in roles
            if role.readiness_status
            == RuntimeSubagentReadinessStatus.contract_ready.value
        ),
        review_ready_count=sum(
            1
            for role in roles
            if role.readiness_status == RuntimeSubagentReadinessStatus.review_ready.value
        ),
        blocked_dispatch_count=sum(
            1
            for role in roles
            if role.readiness_status
            == RuntimeSubagentReadinessStatus.blocked_dispatch.value
        ),
        blocked_authority_refs=list(RUNTIME_SUBAGENT_ISOLATION_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            "promotion-path-ref:subagent-isolation:role-contract",
            "promotion-path-ref:subagent-isolation:context-pack",
            "promotion-path-ref:subagent-isolation:toolset-grant",
            "promotion-path-ref:subagent-isolation:approval",
            "promotion-path-ref:subagent-isolation:budget",
            "promotion-path-ref:subagent-isolation:kill-switch",
            "promotion-path-ref:subagent-isolation:receipt",
            "promotion-path-ref:subagent-isolation:proof",
        ],
        proof_refs=[
            RUNTIME_SUBAGENT_ISOLATION_PROOF_REF,
            "proof-ref:subagent-isolation:role-contracts",
            "proof-ref:subagent-isolation:blocked-dispatch",
        ],
        verifier_refs=[RUNTIME_SUBAGENT_ISOLATION_VERIFIER_REF],
        next_safe_action_refs=[
            "next-safe-action-ref:subagent-isolation:review-role-contracts",
            "next-safe-action-ref:subagent-isolation:define-context-pack-grants",
            "next-safe-action-ref:subagent-isolation:keep-dispatch-blocked",
        ],
    )


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None,
) -> AuthorityDecisionCatalogEntry:
    catalog = authority_decision_catalog or build_authority_decision_catalog()
    entries = {entry.lane_ref: entry for entry in catalog}
    if RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_MAPPING_REF not in entries:
        raise ValueError("RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_CATALOG_MISSING")
    return entries[RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_MAPPING_REF]
