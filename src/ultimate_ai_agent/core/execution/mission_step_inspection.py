from __future__ import annotations

from datetime import datetime
from enum import Enum
import os
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.authority.contracts import authority_state_dir
from ultimate_ai_agent.core.authority.dispatch_contracts import AuthorityDispatchReceipt
from ultimate_ai_agent.core.authority.dispatcher import AuthorityDispatcher
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepCorruptionError,
    MissionStepStatus,
    MissionStepStore,
)
from ultimate_ai_agent.core.planning.validation import validate_task_ref
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.time import utc_now


MISSION_STEP_INSPECTION_SCHEMA_VERSION = "uaa-mission-step-inspection.v1"
MISSION_STEP_INSPECTION_API_REF = "GET /api/runtime/authority-state?mission_step_ref="
MISSION_STEP_INSPECTION_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-mission-step"
)
MISSION_STEP_INSPECTION_REDACTIONS = [
    "raw_content",
    "raw_paths",
    "raw_logs",
    "raw_provider_payloads",
    "state_directory",
    "persisted_summaries",
    "potential_identity_refs",
]


class MissionStepInspectionNotInitializedError(RuntimeError):
    pass


class MissionStepClaimFreshness(str, Enum):
    active = "active"
    expired = "expired"
    not_claimed = "not_claimed"
    unknown = "unknown"


class MissionStepInspectionReadModel(BaseModel):
    schema_version: Literal["uaa-mission-step-inspection.v1"] = (
        MISSION_STEP_INSPECTION_SCHEMA_VERSION
    )
    inspection_ref: str
    api_ref: str = MISSION_STEP_INSPECTION_API_REF
    cli_ref: str = MISSION_STEP_INSPECTION_CLI_REF
    durable_status: MissionStepStatus
    claim_freshness: MissionStepClaimFreshness
    mission_safe_ref: str
    run_safe_ref: str
    step_safe_ref: str
    capability_safe_ref: str
    adapter_safe_ref: str
    lease_safe_ref: str
    owner_safe_ref: str | None = None
    claim_safe_ref: str | None = None
    dispatch_safe_ref: str | None = None
    dispatch_receipt_safe_ref: str | None = None
    dispatch_binding_validated: bool
    dependency_count: int = Field(..., ge=0)
    generation: int = Field(..., ge=0)
    attempt_no: Literal[1] = 1
    deadline: datetime
    claim_expires_at: datetime | None = None
    checked_at: datetime
    observed_at: datetime
    reason_safe_refs: list[str] = Field(default_factory=list, max_length=64)
    evidence_safe_refs: list[str] = Field(default_factory=list, max_length=64)
    operator_summary: str
    execution_authority_granted: Literal[False] = False
    request_scoped_authority_required: Literal[True] = True
    adapter_invocation_performed: Literal[False] = False
    approval_or_lease_minted: Literal[False] = False
    autonomous_retry_performed: Literal[False] = False
    reconciliation_performed: Literal[False] = False
    inspection_only: Literal[True] = True
    raw_content_included: Literal[False] = False
    raw_paths_included: Literal[False] = False
    raw_logs_included: Literal[False] = False
    raw_provider_payload_included: Literal[False] = False
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(MISSION_STEP_INSPECTION_REDACTIONS)
    )

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


def _identity_safe_ref(prefix: str, value: str) -> str:
    return f"{prefix}:sha256:{hash_text(value)[:24]}"


def _bounded_safe_refs(prefix: str, values: list[str]) -> list[str]:
    return [
        _identity_safe_ref(prefix, value) for value in list(dict.fromkeys(values))[:64]
    ]


def _claim_freshness(
    source: Any,
    observed_at: datetime,
) -> MissionStepClaimFreshness:
    if source.status != MissionStepStatus.claimed.value:
        return MissionStepClaimFreshness.not_claimed
    if source.claim_expires_at is None or source.claim_expires_at.tzinfo is None:
        return MissionStepClaimFreshness.unknown
    if source.claim_expires_at <= observed_at:
        return MissionStepClaimFreshness.expired
    return MissionStepClaimFreshness.active


def build_mission_step_inspection_read_model(
    step_ref: str,
    *,
    state_dir: Path | None = None,
    clock: Callable[[], datetime] = utc_now,
) -> MissionStepInspectionReadModel:
    validate_task_ref(step_ref, "mission_step_inspection_ref")
    owned_state_dir = state_dir or authority_state_dir()
    mission_store = MissionStepStore(owned_state_dir, clock=clock)
    try:
        os.lstat(mission_store.receipts_path)
    except FileNotFoundError:
        raise MissionStepInspectionNotInitializedError(
            "MISSION_STEP_INSPECTION_NOT_INITIALIZED"
        ) from None
    dispatcher = AuthorityDispatcher(owned_state_dir, adapters=[])
    dispatch_receipts = dispatcher.list_receipts()
    latest_by_dispatch: dict[str, AuthorityDispatchReceipt] = {}
    for receipt in dispatch_receipts:
        latest_by_dispatch[receipt.dispatch_ref] = receipt
    mission_store._bind_dispatch_receipt_resolver(  # noqa: SLF001
        latest_by_dispatch.get
    )
    source = mission_store._read_inspection_source(step_ref)  # noqa: SLF001
    dispatch_binding_validated = False
    if source.dispatch_ref is not None:
        durable_dispatch = latest_by_dispatch.get(source.dispatch_ref)
        if (
            durable_dispatch is None
            or durable_dispatch.request_fingerprint_ref
            != source.dispatch_request_fingerprint_ref
            or durable_dispatch.run_ref != source.run_ref
            or durable_dispatch.lease_ref != source.lease_ref
            or durable_dispatch.adapter_ref != source.adapter_ref
            or durable_dispatch.capability_ref != source.capability_ref
        ):
            raise MissionStepCorruptionError("MISSION_STEP_DISPATCH_BINDING_INVALID")
        dispatch_binding_validated = True
    observed_at = clock()
    if observed_at.tzinfo is None:
        raise ValueError("MISSION_STEP_INSPECTION_CLOCK_TIMEZONE_REQUIRED")
    return MissionStepInspectionReadModel(
        inspection_ref=_identity_safe_ref(
            "mission-step-inspection-ref",
            f"{source.step_ref}:{source.receipt_ref}:{source.checked_at.isoformat()}",
        ),
        durable_status=source.status,
        claim_freshness=_claim_freshness(source, observed_at),
        mission_safe_ref=_identity_safe_ref("mission-safe-ref", source.mission_ref),
        run_safe_ref=_identity_safe_ref("run-safe-ref", source.run_ref),
        step_safe_ref=_identity_safe_ref("step-safe-ref", source.step_ref),
        capability_safe_ref=_identity_safe_ref(
            "capability-safe-ref", source.capability_ref
        ),
        adapter_safe_ref=_identity_safe_ref("adapter-safe-ref", source.adapter_ref),
        lease_safe_ref=_identity_safe_ref("lease-safe-ref", source.lease_ref),
        owner_safe_ref=(
            _identity_safe_ref("owner-safe-ref", source.owner_ref)
            if source.owner_ref is not None
            else None
        ),
        claim_safe_ref=(
            _identity_safe_ref("claim-safe-ref", source.claim_ref)
            if source.claim_ref is not None
            else None
        ),
        dispatch_safe_ref=(
            _identity_safe_ref("dispatch-safe-ref", source.dispatch_ref)
            if source.dispatch_ref is not None
            else None
        ),
        dispatch_receipt_safe_ref=(
            _identity_safe_ref("dispatch-receipt-safe-ref", source.dispatch_receipt_ref)
            if source.dispatch_receipt_ref is not None
            else None
        ),
        dispatch_binding_validated=dispatch_binding_validated,
        dependency_count=len(source.dependency_step_refs),
        generation=source.generation,
        deadline=source.deadline,
        claim_expires_at=source.claim_expires_at,
        checked_at=source.checked_at,
        observed_at=observed_at,
        reason_safe_refs=_bounded_safe_refs(
            "mission-reason-safe-ref", source.reason_refs
        ),
        evidence_safe_refs=_bounded_safe_refs(
            "mission-evidence-safe-ref", source.evidence_refs
        ),
        operator_summary=(
            "Mission step inspection is read-only; durable status and claim "
            "freshness do not grant request execution authority."
        ),
    )
