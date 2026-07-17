from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import validate_execution_ref


def stable_matrix_hardening_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


class MatrixHardeningCheckStatus(str, Enum):
    passed = "passed"
    partial = "partial"
    blocked = "blocked"
    external_facility_required = "external_facility_required"


class MatrixHardeningCheckCategory(str, Enum):
    large_room_backpressure = "large_room_backpressure"
    cache_queue_bounds = "cache_queue_bounds"
    migration_multi_device = "migration_multi_device"
    rate_limit_malicious_events = "rate_limit_malicious_events"
    retention_deletion_low_disk = "retention_deletion_low_disk"
    restart_offline_recovery = "restart_offline_recovery"
    accessibility_keyboard_focus = "accessibility_keyboard_focus"
    localization_readiness = "localization_readiness"
    telemetry_redaction = "telemetry_redaction"
    dependency_sbom = "dependency_sbom"
    rollback_safe_disable = "rollback_safe_disable"
    element_interoperability = "element_interoperability"


class _MatrixHardeningModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class MatrixHardeningBudget(_MatrixHardeningModel):
    budget_ref: str
    unit: Literal["bytes", "events", "rooms", "records", "relations"]
    limit: int = Field(..., ge=1, le=64 * 1024 * 1024)
    evidence_ref: str

    @model_validator(mode="after")
    def validate_budget(self) -> "MatrixHardeningBudget":
        validate_execution_ref(self.budget_ref, "matrix_hardening_budget_ref")
        validate_execution_ref(self.evidence_ref, "matrix_hardening_evidence_ref")
        return self


class MatrixHardeningCheck(_MatrixHardeningModel):
    check_ref: str
    category: MatrixHardeningCheckCategory
    status: MatrixHardeningCheckStatus
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=16)
    blocker_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=16)
    safe_summary: str = Field(..., min_length=1, max_length=320)
    raw_content_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_check(self) -> "MatrixHardeningCheck":
        for value in (self.check_ref, *self.evidence_refs, *self.blocker_refs):
            validate_execution_ref(value, "matrix_hardening_check_ref")
        if self.status == MatrixHardeningCheckStatus.passed:
            if not self.evidence_refs or self.blocker_refs:
                raise ValueError("MATRIX_HARDENING_PASSED_CHECK_INVALID")
        elif not self.blocker_refs:
            raise ValueError("MATRIX_HARDENING_BLOCKER_REQUIRED")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise ValueError("MATRIX_HARDENING_DUPLICATE_EVIDENCE_REF")
        if len(set(self.blocker_refs)) != len(self.blocker_refs):
            raise ValueError("MATRIX_HARDENING_DUPLICATE_BLOCKER_REF")
        return self


class MatrixHardeningPosture(_MatrixHardeningModel):
    schema_version: Literal["uaa-matrix-hardening-posture.v1"] = (
        "uaa-matrix-hardening-posture.v1"
    )
    posture_ref: str
    runtime_status: Literal["partial_hardening_evidence"] = (
        "partial_hardening_evidence"
    )
    checks: tuple[MatrixHardeningCheck, ...] = Field(min_length=12, max_length=12)
    budgets: tuple[MatrixHardeningBudget, ...] = Field(min_length=8, max_length=8)
    blocked_later_lane_refs: tuple[str, ...] = Field(min_length=5, max_length=8)
    request_scoped_runtime_evaluation_required: Literal[True] = True
    new_runtime_authority_granted: Literal[False] = False
    calls_enabled: Literal[False] = False
    agent_participants_enabled: Literal[False] = False
    hosted_infrastructure_enabled: Literal[False] = False
    public_federation_enabled: Literal[False] = False
    production_deployment_enabled: Literal[False] = False
    element_interoperability_status: Literal["external_facility_required"] = (
        "external_facility_required"
    )
    raw_content_included: Literal[False] = False
    local_paths_included: Literal[False] = False
    desktop_only: Literal[True] = True
    safe_summary: str = Field(..., min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_posture(self) -> "MatrixHardeningPosture":
        validate_execution_ref(self.posture_ref, "matrix_hardening_posture_ref")
        for value in self.blocked_later_lane_refs:
            validate_execution_ref(value, "matrix_hardening_blocked_lane_ref")
        if len(set(self.blocked_later_lane_refs)) != len(
            self.blocked_later_lane_refs
        ):
            raise ValueError("MATRIX_HARDENING_DUPLICATE_LATER_LANE_REF")
        categories = {check.category for check in self.checks}
        if categories != set(MatrixHardeningCheckCategory):
            raise ValueError("MATRIX_HARDENING_CHECK_COVERAGE_MISMATCH")
        statuses = {check.status for check in self.checks}
        if MatrixHardeningCheckStatus.blocked not in statuses:
            raise ValueError("MATRIX_HARDENING_BLOCKED_TRUTH_REQUIRED")
        if MatrixHardeningCheckStatus.external_facility_required not in statuses:
            raise ValueError("MATRIX_HARDENING_EXTERNAL_FACILITY_TRUTH_REQUIRED")
        expected = stable_matrix_hardening_ref(
            "posture-ref:matrix-hardening",
            self.model_dump(mode="json", exclude={"posture_ref"}),
        )
        if self.posture_ref != expected:
            raise ValueError("MATRIX_HARDENING_POSTURE_REF_MISMATCH")
        return self


__all__ = [
    "MatrixHardeningBudget",
    "MatrixHardeningCheck",
    "MatrixHardeningCheckCategory",
    "MatrixHardeningCheckStatus",
    "MatrixHardeningPosture",
    "stable_matrix_hardening_ref",
]
