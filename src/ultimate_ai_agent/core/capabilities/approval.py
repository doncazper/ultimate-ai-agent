from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.capabilities.enums import PolicyDecisionStatus, RiskLevel, SideEffectLevel
from ultimate_ai_agent.core.capabilities.models import (
    CAPABILITY_SCOPE_PATTERN,
    CapabilityManifest,
    PolicyDecision,
    TaskEnvelope,
    _assert_secret_clean,
)
from ultimate_ai_agent.core.time import utc_now


class CapabilityApprovalGrant(BaseModel):
    approval_ref: str = Field(..., min_length=1)
    capability_id: str = Field(..., min_length=1)
    granted_by: str = Field(..., min_length=1)
    task_id: str | None = None
    trace_id: str | None = None
    max_risk_level: RiskLevel = RiskLevel.critical
    max_side_effect_level: SideEffectLevel = SideEffectLevel.destructive
    expires_at: datetime | None = None
    revoked: bool = False
    reason: str = Field(default="Human approval captured for exact capability execution.", min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    @field_validator("approval_ref")
    @classmethod
    def validate_approval_ref(cls, value: str) -> str:
        if not CAPABILITY_SCOPE_PATTERN.fullmatch(value):
            raise ValueError("approval_ref must be a safe ref.")
        return value

    @model_validator(mode="after")
    def validate_secret_free(self):
        _assert_secret_clean(self.model_dump(mode="json"), "capability_approval_grant")
        return self


class ApprovalAuthority(Protocol):
    def validate_approval(
        self,
        capability: CapabilityManifest,
        task: TaskEnvelope,
        context: dict[str, Any],
    ) -> PolicyDecision:
        ...


class LocalApprovalAuthority:
    def __init__(self, grants: list[CapabilityApprovalGrant] | None = None):
        self._grants: dict[str, CapabilityApprovalGrant] = {}
        for grant in grants or []:
            self.add_grant(grant)

    def add_grant(self, grant: CapabilityApprovalGrant) -> CapabilityApprovalGrant:
        self._grants[grant.approval_ref] = grant
        return grant

    def revoke(self, approval_ref: str) -> CapabilityApprovalGrant:
        grant = self._grants[approval_ref]
        revoked = grant.model_copy(update={"revoked": True})
        self._grants[approval_ref] = revoked
        return revoked

    def list_grants(self) -> list[CapabilityApprovalGrant]:
        return list(self._grants.values())

    def validate_approval(
        self,
        capability: CapabilityManifest,
        task: TaskEnvelope,
        context: dict[str, Any],
    ) -> PolicyDecision:
        approval_ref = context.get("approval_ref") or task.context.get("approval_ref")
        if not approval_ref:
            return _approval_denied(capability, task, ["APPROVAL_REF_MISSING"])
        grant = self._grant_from_context(str(approval_ref), context)
        if grant is None:
            return _approval_denied(capability, task, ["APPROVAL_GRANT_NOT_FOUND"])
        reason_codes: list[str] = []
        if grant.revoked:
            reason_codes.append("APPROVAL_REVOKED")
        if grant.capability_id != capability.id:
            reason_codes.append("APPROVAL_CAPABILITY_MISMATCH")
        if grant.task_id is not None and grant.task_id != task.task_id:
            reason_codes.append("APPROVAL_TASK_MISMATCH")
        if grant.expires_at is not None and grant.expires_at <= utc_now():
            reason_codes.append("APPROVAL_EXPIRED")
        if _rank_risk(capability.risk_level) > _rank_risk(grant.max_risk_level):
            reason_codes.append("APPROVAL_RISK_SCOPE_EXCEEDED")
        if _rank_side_effect(capability.side_effects) > _rank_side_effect(grant.max_side_effect_level):
            reason_codes.append("APPROVAL_SIDE_EFFECT_SCOPE_EXCEEDED")
        if reason_codes:
            return _approval_denied(capability, task, reason_codes)
        return PolicyDecision(
            status=PolicyDecisionStatus.allowed,
            allowed=True,
            requires_approval=False,
            reason_codes=["APPROVAL_GRANT_VALID"],
            safe_message="Approval grant is valid for exact capability execution.",
            capability_id=capability.id,
            task_id=task.task_id,
        )

    def _grant_from_context(self, approval_ref: str, context: dict[str, Any]) -> CapabilityApprovalGrant | None:
        if approval_ref in self._grants:
            return self._grants[approval_ref]
        for item in context.get("approval_grants", []):
            grant = item if isinstance(item, CapabilityApprovalGrant) else CapabilityApprovalGrant.model_validate(item)
            if grant.approval_ref == approval_ref:
                self.add_grant(grant)
                return grant
        return None


def _approval_denied(capability: CapabilityManifest, task: TaskEnvelope, reason_codes: list[str]) -> PolicyDecision:
    return PolicyDecision(
        status=PolicyDecisionStatus.denied,
        allowed=False,
        requires_approval=True,
        reason_codes=list(dict.fromkeys(reason_codes)),
        safe_message="Approval grant did not satisfy the capability execution gate.",
        capability_id=capability.id,
        task_id=task.task_id,
    )


_RISK_RANK = {
    RiskLevel.safe: 0,
    RiskLevel.low: 1,
    RiskLevel.medium: 2,
    RiskLevel.high: 3,
    RiskLevel.critical: 4,
    RiskLevel.forbidden: 5,
}

_SIDE_EFFECT_RANK = {
    SideEffectLevel.none: 0,
    SideEffectLevel.read: 1,
    SideEffectLevel.write: 2,
    SideEffectLevel.external: 3,
    SideEffectLevel.destructive: 4,
}


def _rank_risk(level: RiskLevel) -> int:
    return _RISK_RANK[level]


def _rank_side_effect(level: SideEffectLevel) -> int:
    return _SIDE_EFFECT_RANK[level]
