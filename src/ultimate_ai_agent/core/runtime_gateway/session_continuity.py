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


RUNTIME_SESSION_CONTINUITY_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-session-continuity:v1"
)
RUNTIME_SESSION_CONTINUITY_ROUTE_REF = "GET /api/runtime/session-continuity"
RUNTIME_SESSION_CONTINUITY_CLI_REF = "uaa runtime inspect-session-continuity"
RUNTIME_SESSION_CONTINUITY_SNAPSHOT_REF = (
    "session-continuity-snapshot-ref:runtime:multi-surface"
)
RUNTIME_SESSION_CONTINUITY_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-29:session-continuity"
)
RUNTIME_SESSION_CONTINUITY_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-29:session-continuity"
)
RUNTIME_SESSION_CONTINUITY_AUTHORITY_STATE_ROUTE_REF = "GET /api/runtime/authority-state"
RUNTIME_SESSION_CONTINUITY_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_SESSION_CONTINUITY_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-session-continuity-read-model"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_SESSION_CONTINUITY_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:session-continuity-no-external-message-gateway",
    "blocked-authority:session-continuity-no-account-sync",
    "blocked-authority:session-continuity-no-connector-write",
    "blocked-authority:session-continuity-no-remote-session",
    "blocked-authority:session-continuity-no-raw-transcript-persistence",
    "blocked-authority:session-continuity-no-raw-prompt-response-persistence",
    "blocked-authority:session-continuity-no-provider-payload-persistence",
    "blocked-authority:session-continuity-no-control-center-authority-mint",
)


class RuntimeSessionContinuitySource(str, Enum):
    control_center_desktop = "control_center_desktop"
    cli = "cli"
    delegated_runtime = "delegated_runtime"
    future_mobile = "future_mobile"
    coding_cockpit = "coding_cockpit"


class RuntimeSessionContinuityState(str, Enum):
    current = "current"
    stale = "stale"
    conflict_review = "conflict_review"
    blocked = "blocked"


class RuntimeSessionContinuitySurface(BaseModel):
    surface_ref: str
    source: RuntimeSessionContinuitySource
    source_label: str
    continuity_state: RuntimeSessionContinuityState
    session_ref: str
    run_ref: str | None = None
    route_ref: str
    cli_ref: str | None = None
    last_seen_ref: str
    staleness_state_ref: str
    conflict_state_ref: str
    safe_summary: str
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    external_message_gateway_enabled: bool = False
    account_sync_enabled: bool = False
    connector_write_enabled: bool = False
    remote_session_enabled: bool = False
    raw_transcript_persisted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_provider_payload_persisted: bool = False
    control_center_mints_authority: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_surface(self) -> "RuntimeSessionContinuitySurface":
        for value, field_name in [
            (self.surface_ref, "surface_ref"),
            (self.session_ref, "session_ref"),
            (self.last_seen_ref, "last_seen_ref"),
            (self.staleness_state_ref, "staleness_state_ref"),
            (self.conflict_state_ref, "conflict_state_ref"),
        ]:
            validate_execution_ref(value, field_name)
        if self.run_ref is not None:
            validate_execution_ref(self.run_ref, "run_ref")
        for field_name in (
            "evidence_refs",
            "proof_refs",
            "receipt_refs",
            "blocked_authority_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (str(self.source), "source"),
            (self.source_label, "source_label"),
            (str(self.continuity_state), "continuity_state"),
            (self.route_ref, "route_ref"),
            (self.cli_ref or "none", "cli_ref"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "external_message_gateway_enabled": self.external_message_gateway_enabled,
            "account_sync_enabled": self.account_sync_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "remote_session_enabled": self.remote_session_enabled,
            "raw_transcript_persisted": self.raw_transcript_persisted,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "raw_provider_payload_persisted": self.raw_provider_payload_persisted,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_SESSION_CONTINUITY_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_SESSION_CONTINUITY_BLOCKERS_REQUIRED")
        if not self.proof_refs:
            raise ValueError("RUNTIME_SESSION_CONTINUITY_PROOF_REQUIRED")
        return self


class RuntimeSessionContinuityReadModel(BaseModel):
    schema_version: str = "runtime_session_continuity.v1"
    contract_ref: str = RUNTIME_SESSION_CONTINUITY_CONTRACT_REF
    status: str = "read_only_multi_surface_session_continuity_posture"
    snapshot_ref: str = RUNTIME_SESSION_CONTINUITY_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-session-continuity:pending"
    route_ref: str = RUNTIME_SESSION_CONTINUITY_ROUTE_REF
    cli_ref: str = RUNTIME_SESSION_CONTINUITY_CLI_REF
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
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    primary_session_ref: str = "session-ref:runtime-continuity:operator-loop"
    safe_summary: str = (
        "Multi-surface session continuity is visible as safe refs, source "
        "labels, staleness states, and conflict states only."
    )
    surfaces: list[RuntimeSessionContinuitySurface] = Field(default_factory=list)
    surface_count: int = 0
    current_count: int = 0
    stale_count: int = 0
    conflict_count: int = 0
    blocked_count: int = 0
    source_labels_visible: bool = True
    staleness_states_visible: bool = True
    conflict_states_visible: bool = True
    delivery_receipts_required_for_promotion: bool = True
    revoke_required_for_promotion: bool = True
    audit_required_for_promotion: bool = True
    external_message_gateway_enabled: bool = False
    account_sync_enabled: bool = False
    connector_write_enabled: bool = False
    remote_session_enabled: bool = False
    raw_transcript_persisted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_provider_payload_persisted: bool = False
    control_center_mints_authority: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "raw_transcripts_omitted",
            "raw_prompts_omitted",
            "raw_responses_omitted",
            "provider_payloads_omitted",
            "account_material_omitted",
        ]
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeSessionContinuityReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.primary_session_ref, "primary_session_ref"),
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
            "authority_state_reason_refs",
            "unsupported_adapter_refs",
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
        if (
            self.authority_state_mapping_ref
            != RUNTIME_SESSION_CONTINUITY_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_SESSION_CONTINUITY_AUTHORITY_MAPPING_MISMATCH")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_SESSION_CONTINUITY_AUTHORITY_DECISION_INVALID")
        if self.surface_count != len(self.surfaces):
            raise ValueError("RUNTIME_SESSION_CONTINUITY_SURFACE_COUNT_DRIFT")
        expected_counts = {
            RuntimeSessionContinuityState.current.value: self.current_count,
            RuntimeSessionContinuityState.stale.value: self.stale_count,
            RuntimeSessionContinuityState.conflict_review.value: self.conflict_count,
            RuntimeSessionContinuityState.blocked.value: self.blocked_count,
        }
        for state, expected in expected_counts.items():
            actual = sum(1 for surface in self.surfaces if surface.continuity_state == state)
            if actual != expected:
                raise ValueError("RUNTIME_SESSION_CONTINUITY_STATE_COUNT_DRIFT")
        visibility_flags = {
            "source_labels_visible": self.source_labels_visible,
            "staleness_states_visible": self.staleness_states_visible,
            "conflict_states_visible": self.conflict_states_visible,
            "delivery_receipts_required_for_promotion": (
                self.delivery_receipts_required_for_promotion
            ),
            "revoke_required_for_promotion": self.revoke_required_for_promotion,
            "audit_required_for_promotion": self.audit_required_for_promotion,
        }
        missing = [name for name, value in visibility_flags.items() if not value]
        if missing:
            raise ValueError(
                "RUNTIME_SESSION_CONTINUITY_VISIBLE_PROMOTION_REQUIRED: "
                + ", ".join(missing)
            )
        denied_flags = {
            "external_message_gateway_enabled": self.external_message_gateway_enabled,
            "account_sync_enabled": self.account_sync_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "remote_session_enabled": self.remote_session_enabled,
            "raw_transcript_persisted": self.raw_transcript_persisted,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "raw_provider_payload_persisted": self.raw_provider_payload_persisted,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_SESSION_CONTINUITY_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        for ref in RUNTIME_SESSION_CONTINUITY_BLOCKED_AUTHORITY_REFS:
            if ref not in self.blocked_authority_refs:
                raise ValueError("RUNTIME_SESSION_CONTINUITY_BLOCKER_MISSING")
        if RUNTIME_SESSION_CONTINUITY_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_SESSION_CONTINUITY_PROOF_REF_REQUIRED")
        if RUNTIME_SESSION_CONTINUITY_VERIFIER_REF not in self.verifier_refs:
            raise ValueError("RUNTIME_SESSION_CONTINUITY_VERIFIER_REF_REQUIRED")
        return self


def _snapshot_hash_ref(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(encoded).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-session-continuity:{digest}"


def _surface(
    slug: str,
    *,
    source: RuntimeSessionContinuitySource,
    source_label: str,
    continuity_state: RuntimeSessionContinuityState,
    session_ref: str,
    route_ref: str,
    safe_summary: str,
    run_ref: str | None = None,
    cli_ref: str | None = None,
    receipt_refs: list[str] | None = None,
    next_safe_action_refs: list[str] | None = None,
) -> RuntimeSessionContinuitySurface:
    return RuntimeSessionContinuitySurface(
        surface_ref=f"session-continuity-surface-ref:{slug}",
        source=source,
        source_label=source_label,
        continuity_state=continuity_state,
        session_ref=session_ref,
        run_ref=run_ref,
        route_ref=route_ref,
        cli_ref=cli_ref,
        last_seen_ref=f"last-seen-ref:session-continuity:{slug}",
        staleness_state_ref=f"staleness-state-ref:session-continuity:{slug}",
        conflict_state_ref=f"conflict-state-ref:session-continuity:{slug}",
        safe_summary=safe_summary,
        evidence_refs=[f"evidence-ref:session-continuity:{slug}"],
        proof_refs=[RUNTIME_SESSION_CONTINUITY_PROOF_REF],
        receipt_refs=receipt_refs or [],
        blocked_authority_refs=list(RUNTIME_SESSION_CONTINUITY_BLOCKED_AUTHORITY_REFS),
        next_safe_action_refs=next_safe_action_refs or [],
    )


def build_runtime_session_continuity_read_model() -> RuntimeSessionContinuityReadModel:
    return build_runtime_session_continuity_read_model_from_authority_catalog(
        authority_decision_catalog=build_authority_decision_catalog()
    )


def build_runtime_session_continuity_read_model_from_authority_catalog(
    *,
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry],
) -> RuntimeSessionContinuityReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    surfaces = [
        _surface(
            "control-center-desktop",
            source=RuntimeSessionContinuitySource.control_center_desktop,
            source_label="Control Center desktop",
            continuity_state=RuntimeSessionContinuityState.current,
            session_ref="session-ref:runtime-continuity:operator-loop",
            run_ref="run-ref:runtime-continuity:operator-loop",
            route_ref="GET /runtime/readiness",
            safe_summary=(
                "Desktop Control Center is the current visible operator session."
            ),
            receipt_refs=["receipt-ref:session-continuity:desktop-read"],
        ),
        _surface(
            "cli",
            source=RuntimeSessionContinuitySource.cli,
            source_label="CLI",
            continuity_state=RuntimeSessionContinuityState.current,
            session_ref="session-ref:runtime-continuity:operator-loop",
            run_ref="run-ref:runtime-continuity:operator-loop",
            route_ref="repo-local-cli",
            cli_ref=RUNTIME_SESSION_CONTINUITY_CLI_REF,
            safe_summary=(
                "CLI inspection points at the same operator session safe refs."
            ),
            receipt_refs=["receipt-ref:session-continuity:cli-read"],
        ),
        _surface(
            "delegated-runtime",
            source=RuntimeSessionContinuitySource.delegated_runtime,
            source_label="Delegated runtime",
            continuity_state=RuntimeSessionContinuityState.stale,
            session_ref="session-ref:runtime-continuity:delegated-runtime",
            run_ref="run-ref:runtime-continuity:delegated-runtime",
            route_ref="GET /api/runtime/delegation-adapter",
            safe_summary=(
                "Delegated runtime visibility is stale until a delivery receipt "
                "and approval-binding chain exist."
            ),
            next_safe_action_refs=[
                "next-safe-action-ref:session-continuity:bind-delivery-receipt"
            ],
        ),
        _surface(
            "coding-cockpit",
            source=RuntimeSessionContinuitySource.coding_cockpit,
            source_label="Coding cockpit",
            continuity_state=RuntimeSessionContinuityState.conflict_review,
            session_ref="session-ref:runtime-continuity:coding-cockpit",
            route_ref="GET /control-center/coding/session",
            safe_summary=(
                "Coding cockpit session refs require operator review before "
                "being treated as the same runtime session."
            ),
            next_safe_action_refs=[
                "next-safe-action-ref:session-continuity:operator-review-conflict"
            ],
        ),
        _surface(
            "future-mobile",
            source=RuntimeSessionContinuitySource.future_mobile,
            source_label="Future mobile",
            continuity_state=RuntimeSessionContinuityState.blocked,
            session_ref="session-ref:runtime-continuity:future-mobile",
            route_ref="planned-route-ref:future-mobile-session-continuity",
            safe_summary=(
                "Future mobile continuity is represented as a blocked planned "
                "surface only; no account sync or remote session is active."
            ),
            next_safe_action_refs=[
                "next-safe-action-ref:session-continuity:define-channel-identity"
            ],
        ),
    ]
    payload_for_hash: dict[str, object] = {
        "surfaces": [surface.model_dump(mode="json") for surface in surfaces],
        "blocked": list(RUNTIME_SESSION_CONTINUITY_BLOCKED_AUTHORITY_REFS),
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
    }
    return RuntimeSessionContinuityReadModel(
        snapshot_hash_ref=_snapshot_hash_ref(payload_for_hash),
        authority_state_route_ref=RUNTIME_SESSION_CONTINUITY_AUTHORITY_STATE_ROUTE_REF,
        authority_state_cli_ref=RUNTIME_SESSION_CONTINUITY_AUTHORITY_STATE_CLI_REF,
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
        surfaces=surfaces,
        surface_count=len(surfaces),
        current_count=sum(
            1
            for surface in surfaces
            if surface.continuity_state == RuntimeSessionContinuityState.current.value
        ),
        stale_count=sum(
            1
            for surface in surfaces
            if surface.continuity_state == RuntimeSessionContinuityState.stale.value
        ),
        conflict_count=sum(
            1
            for surface in surfaces
            if surface.continuity_state
            == RuntimeSessionContinuityState.conflict_review.value
        ),
        blocked_count=sum(
            1
            for surface in surfaces
            if surface.continuity_state == RuntimeSessionContinuityState.blocked.value
        ),
        blocked_authority_refs=list(RUNTIME_SESSION_CONTINUITY_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            "promotion-path-ref:session-continuity:channel-identity",
            "promotion-path-ref:session-continuity:approval-binding",
            "promotion-path-ref:session-continuity:redaction",
            "promotion-path-ref:session-continuity:delivery-receipt",
            "promotion-path-ref:session-continuity:revoke",
            "promotion-path-ref:session-continuity:audit",
        ],
        proof_refs=[
            RUNTIME_SESSION_CONTINUITY_PROOF_REF,
            "proof-ref:session-continuity:source-labels",
            "proof-ref:session-continuity:staleness-conflict-states",
        ],
        verifier_refs=[RUNTIME_SESSION_CONTINUITY_VERIFIER_REF],
        next_safe_action_refs=[
            "next-safe-action-ref:session-continuity:review-source-labels",
            "next-safe-action-ref:session-continuity:resolve-conflict-ref",
            "next-safe-action-ref:session-continuity:design-delivery-receipts",
        ],
    )


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry],
) -> AuthorityDecisionCatalogEntry:
    for entry in authority_decision_catalog:
        if entry.lane_ref == RUNTIME_SESSION_CONTINUITY_AUTHORITY_MAPPING_REF:
            return entry
    raise ValueError("RUNTIME_SESSION_CONTINUITY_AUTHORITY_MAPPING_NOT_FOUND")


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))
