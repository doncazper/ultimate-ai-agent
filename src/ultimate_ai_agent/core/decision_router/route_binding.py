from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core._compat import UTC
from ultimate_ai_agent.core.decision_router.turn_contracts import (
    InvocationPolicy,
    TurnContractKind,
    TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS,
)
from ultimate_ai_agent.core.planning.validation import validate_safe_task_text, validate_task_ref


ROUTE_DECISION_BINDING_CONTRACT_REF = "contract-ref:route-decision-binding:v1"
ROUTE_DECISION_BINDING_POLICY_VERSION_REF = "policy-version-ref:route-decision-binding:v1"
ROUTE_DECISION_BINDING_SOURCE_REF = "source-ref:route-decision-binding:core-contract"
ROUTE_DECISION_BINDING_REQUIRED_BLOCKED_AUTHORITY_REFS = (
    *TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS,
    "blocked-authority:no-route-decision-as-approval",
    "blocked-authority:no-stale-route-decision-mutation",
    "blocked-authority:no-route-decision-provider-authority",
)
ROUTE_DECISION_BINDING_ALLOWED_SIDE_EFFECT_CLASSES = (
    "none",
    "validation_only",
    "local_dev_workspace_only",
    "governed_network_read_only",
)


class RouteDecisionValidationStatus(str, Enum):
    valid = "valid"
    expired = "expired"
    scope_changed = "scope_changed"
    policy_changed = "policy_changed"
    replay_conflict = "replay_conflict"
    authority_blocked = "authority_blocked"
    unsafe_payload = "unsafe_payload"


class RouteDecisionBinding(BaseModel):
    contract_ref: str = ROUTE_DECISION_BINDING_CONTRACT_REF
    binding_ref: str = Field(..., min_length=1)
    actor_ref: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    turn_ref: str = Field(..., min_length=1)
    decision_ref: str = Field(..., min_length=1)
    turn_contract: TurnContractKind
    route_ref: str = Field(..., min_length=1)
    side_effect_class: str = Field(..., min_length=1)
    policy_ref: str = Field(..., min_length=1)
    policy_version_ref: str = ROUTE_DECISION_BINDING_POLICY_VERSION_REF
    approval_ref: str | None = None
    approval_scope_ref: str | None = None
    provider_ref: str | None = None
    model_ref: str | None = None
    tool_refs: list[str] = Field(default_factory=list)
    action_refs: list[str] = Field(default_factory=list)
    resource_refs: list[str] = Field(default_factory=list)
    idempotency_key: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(UTC) + timedelta(minutes=5))
    content_fingerprint_ref: str = Field(..., min_length=1)
    context_fingerprint_ref: str | None = None
    binding_fingerprint_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    redaction_refs: list[str] = Field(default_factory=lambda: ["redaction-ref:route-decision-binding:safe-refs-only"])
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(ROUTE_DECISION_BINDING_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    safe_disable_ref: str | None = None
    safe_disable_active: bool = False
    safe_refs_only: bool = True
    raw_content_included: bool = False
    route_decision_is_approval: bool = False
    authority_granted: bool = False
    execution_performed: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_binding(self) -> "RouteDecisionBinding":
        if self.contract_ref != ROUTE_DECISION_BINDING_CONTRACT_REF:
            raise ValueError("unexpected route decision binding contract ref")
        for field_name in (
            "contract_ref",
            "binding_ref",
            "actor_ref",
            "session_ref",
            "turn_ref",
            "decision_ref",
            "policy_ref",
            "policy_version_ref",
            "idempotency_key",
            "content_fingerprint_ref",
        ):
            validate_task_ref(getattr(self, field_name), field_name)
        for field_name in (
            "approval_ref",
            "approval_scope_ref",
            "provider_ref",
            "model_ref",
            "context_fingerprint_ref",
            "binding_fingerprint_ref",
            "safe_disable_ref",
        ):
            _validate_optional_ref(getattr(self, field_name), field_name)
        for field_name in (
            "tool_refs",
            "action_refs",
            "resource_refs",
            "evidence_refs",
            "redaction_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        validate_safe_task_text(self.route_ref, "route_ref")
        validate_safe_task_text(self.side_effect_class, "side_effect_class")
        if self.side_effect_class not in ROUTE_DECISION_BINDING_ALLOWED_SIDE_EFFECT_CLASSES:
            raise ValueError("route decision binding side-effect class is not allowed")
        if self.expires_at <= self.created_at:
            raise ValueError("route decision binding expiry must be after creation")
        if self.safe_disable_active and self.safe_disable_ref is None:
            raise ValueError("active route decision safe-disable requires a safe-disable ref")
        if not self.safe_refs_only:
            raise ValueError("route decision binding must use safe refs only")
        if self.raw_content_included:
            raise ValueError("route decision binding must not include raw content")
        if self.route_decision_is_approval:
            raise ValueError("route decision binding must not be treated as approval")
        if self.authority_granted:
            raise ValueError("route decision binding must not grant authority")
        if self.execution_performed:
            raise ValueError("route decision binding must not perform execution")
        _validate_required_blocked_authorities(self.blocked_authority_refs)
        expected_fingerprint_ref = route_decision_binding_fingerprint_ref(self)
        if self.binding_fingerprint_ref is not None and self.binding_fingerprint_ref != expected_fingerprint_ref:
            raise ValueError("route decision binding fingerprint mismatch")
        return self


class RouteDecisionMutationContext(BaseModel):
    actor_ref: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    turn_ref: str = Field(..., min_length=1)
    turn_contract: TurnContractKind
    route_ref: str = Field(..., min_length=1)
    side_effect_class: str = Field(..., min_length=1)
    policy_ref: str = Field(..., min_length=1)
    policy_version_ref: str = ROUTE_DECISION_BINDING_POLICY_VERSION_REF
    approval_ref: str | None = None
    approval_scope_ref: str | None = None
    provider_ref: str | None = None
    model_ref: str | None = None
    tool_refs: list[str] = Field(default_factory=list)
    action_refs: list[str] = Field(default_factory=list)
    resource_refs: list[str] = Field(default_factory=list)
    idempotency_key: str = Field(..., min_length=1)
    content_fingerprint_ref: str = Field(..., min_length=1)
    context_fingerprint_ref: str | None = None
    safe_disable_active: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_context(self) -> "RouteDecisionMutationContext":
        for field_name in (
            "actor_ref",
            "session_ref",
            "turn_ref",
            "policy_ref",
            "policy_version_ref",
            "idempotency_key",
            "content_fingerprint_ref",
        ):
            validate_task_ref(getattr(self, field_name), field_name)
        for field_name in (
            "approval_ref",
            "approval_scope_ref",
            "provider_ref",
            "model_ref",
            "context_fingerprint_ref",
        ):
            _validate_optional_ref(getattr(self, field_name), field_name)
        for field_name in ("tool_refs", "action_refs", "resource_refs"):
            _validate_ref_list(getattr(self, field_name), field_name)
        validate_safe_task_text(self.route_ref, "route_ref")
        validate_safe_task_text(self.side_effect_class, "side_effect_class")
        if self.side_effect_class not in ROUTE_DECISION_BINDING_ALLOWED_SIDE_EFFECT_CLASSES:
            raise ValueError("route decision mutation context side-effect class is not allowed")
        return self


class RouteDecisionValidationResult(BaseModel):
    contract_ref: str = ROUTE_DECISION_BINDING_CONTRACT_REF
    binding_ref: str = Field(..., min_length=1)
    status: RouteDecisionValidationStatus
    allowed: bool = False
    safe_summary: str = Field(..., min_length=1, max_length=500)
    reason_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    binding_fingerprint_ref: str = Field(..., min_length=1)
    route_decision_is_approval: bool = False
    authority_granted: bool = False
    execution_performed: bool = False
    safe_refs_only: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_result(self) -> "RouteDecisionValidationResult":
        validate_task_ref(self.contract_ref, "contract_ref")
        validate_task_ref(self.binding_ref, "binding_ref")
        validate_task_ref(self.binding_fingerprint_ref, "binding_fingerprint_ref")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        _validate_ref_list(self.reason_refs, "reason_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        if self.allowed != (self.status == RouteDecisionValidationStatus.valid.value):
            raise ValueError("route decision validation allowed flag must match status")
        if self.route_decision_is_approval:
            raise ValueError("route decision validation result must not be approval")
        if self.authority_granted:
            raise ValueError("route decision validation result must not grant authority")
        if self.execution_performed:
            raise ValueError("route decision validation result must not perform execution")
        if not self.safe_refs_only:
            raise ValueError("route decision validation result must use safe refs only")
        return self


def build_route_decision_binding(
    policy: InvocationPolicy,
    *,
    actor_ref: str,
    session_ref: str,
    turn_ref: str,
    route_ref: str,
    side_effect_class: str,
    idempotency_key: str,
    content_fingerprint_ref: str,
    context_fingerprint_ref: str | None = None,
    provider_ref: str | None = None,
    model_ref: str | None = None,
    resource_refs: list[str] | None = None,
    approval_ref: str | None = None,
    approval_scope_ref: str | None = None,
    created_at: datetime | None = None,
    ttl_seconds: int = 300,
) -> RouteDecisionBinding:
    created = created_at or datetime.now(UTC)
    binding = RouteDecisionBinding(
        binding_ref=_hash_ref(
            "route-decision-binding",
            {
                "actor_ref": actor_ref,
                "session_ref": session_ref,
                "turn_ref": turn_ref,
                "decision_ref": policy.decision_ref,
                "route_ref": route_ref,
                "idempotency_key": idempotency_key,
            },
        ),
        actor_ref=actor_ref,
        session_ref=session_ref,
        turn_ref=turn_ref,
        decision_ref=policy.decision_ref,
        turn_contract=policy.turn_contract,
        route_ref=route_ref,
        side_effect_class=side_effect_class,
        policy_ref=policy.policy_ref,
        approval_ref=approval_ref,
        approval_scope_ref=approval_scope_ref or policy.approval_scope_ref,
        provider_ref=provider_ref,
        model_ref=model_ref,
        tool_refs=list(policy.tools),
        action_refs=[policy.action_scope_ref] if policy.action_scope_ref else [],
        resource_refs=resource_refs or [],
        idempotency_key=idempotency_key,
        created_at=created,
        expires_at=created + timedelta(seconds=ttl_seconds),
        content_fingerprint_ref=content_fingerprint_ref,
        context_fingerprint_ref=context_fingerprint_ref,
        evidence_refs=[ROUTE_DECISION_BINDING_SOURCE_REF],
        blocked_authority_refs=list(
            dict.fromkeys([*policy.blocked_authority_refs, *ROUTE_DECISION_BINDING_REQUIRED_BLOCKED_AUTHORITY_REFS])
        ),
    )
    payload = binding.model_dump(mode="python")
    payload["binding_fingerprint_ref"] = route_decision_binding_fingerprint_ref(binding)
    return RouteDecisionBinding(**payload)


def context_from_route_decision_binding(binding: RouteDecisionBinding) -> RouteDecisionMutationContext:
    return RouteDecisionMutationContext(
        actor_ref=binding.actor_ref,
        session_ref=binding.session_ref,
        turn_ref=binding.turn_ref,
        turn_contract=binding.turn_contract,
        route_ref=binding.route_ref,
        side_effect_class=binding.side_effect_class,
        policy_ref=binding.policy_ref,
        policy_version_ref=binding.policy_version_ref,
        approval_ref=binding.approval_ref,
        approval_scope_ref=binding.approval_scope_ref,
        provider_ref=binding.provider_ref,
        model_ref=binding.model_ref,
        tool_refs=list(binding.tool_refs),
        action_refs=list(binding.action_refs),
        resource_refs=list(binding.resource_refs),
        idempotency_key=binding.idempotency_key,
        content_fingerprint_ref=binding.content_fingerprint_ref,
        context_fingerprint_ref=binding.context_fingerprint_ref,
    )


def validate_route_decision_binding(
    binding: RouteDecisionBinding,
    context: RouteDecisionMutationContext,
    *,
    now: datetime | None = None,
    idempotency_ledger: Mapping[str, str] | None = None,
) -> RouteDecisionValidationResult:
    fingerprint_ref = route_decision_binding_fingerprint_ref(binding)
    evidence_refs = list(dict.fromkeys([*binding.evidence_refs, "evidence-ref:route-decision-binding:validation"]))
    if _has_unsafe_payload_flags(binding):
        return _validation_result(
            binding,
            RouteDecisionValidationStatus.unsafe_payload,
            "Route decision binding was rejected because it attempted to carry unsafe payload state.",
            ["reason-ref:route-decision-binding:unsafe-payload"],
            fingerprint_ref,
            evidence_refs,
        )
    if binding.safe_disable_active or context.safe_disable_active:
        return _validation_result(
            binding,
            RouteDecisionValidationStatus.authority_blocked,
            "Route decision binding was blocked by safe-disable posture.",
            ["reason-ref:route-decision-binding:safe-disable-active"],
            fingerprint_ref,
            evidence_refs,
        )
    checked_at = now or datetime.now(UTC)
    if checked_at > binding.expires_at:
        return _validation_result(
            binding,
            RouteDecisionValidationStatus.expired,
            "Route decision binding expired before mutation validation.",
            ["reason-ref:route-decision-binding:expired"],
            fingerprint_ref,
            evidence_refs,
        )
    if binding.binding_fingerprint_ref is not None and binding.binding_fingerprint_ref != fingerprint_ref:
        return _validation_result(
            binding,
            RouteDecisionValidationStatus.scope_changed,
            "Route decision binding fingerprint no longer matches its safe refs.",
            ["reason-ref:route-decision-binding:fingerprint-mismatch"],
            fingerprint_ref,
            evidence_refs,
        )
    replay_fingerprint = (idempotency_ledger or {}).get(binding.idempotency_key)
    if replay_fingerprint is not None and replay_fingerprint != fingerprint_ref:
        return _validation_result(
            binding,
            RouteDecisionValidationStatus.replay_conflict,
            "Route decision binding idempotency key conflicts with a prior binding fingerprint.",
            ["reason-ref:route-decision-binding:replay-conflict"],
            fingerprint_ref,
            evidence_refs,
        )
    if binding.policy_ref != context.policy_ref or binding.policy_version_ref != context.policy_version_ref:
        return _validation_result(
            binding,
            RouteDecisionValidationStatus.policy_changed,
            "Route decision binding policy version changed before mutation validation.",
            ["reason-ref:route-decision-binding:policy-changed"],
            fingerprint_ref,
            evidence_refs,
        )
    if _scope_changed(binding, context):
        return _validation_result(
            binding,
            RouteDecisionValidationStatus.scope_changed,
            "Route decision binding no longer matches actor, turn, route, approval, provider, model, or resource scope.",
            ["reason-ref:route-decision-binding:scope-changed"],
            fingerprint_ref,
            evidence_refs,
        )
    return _validation_result(
        binding,
        RouteDecisionValidationStatus.valid,
        "Route decision binding matched the requested mutation scope without granting authority.",
        ["reason-ref:route-decision-binding:valid"],
        fingerprint_ref,
        evidence_refs,
    )


def route_decision_binding_fingerprint_ref(binding: RouteDecisionBinding) -> str:
    payload = {
        "actor_ref": binding.actor_ref,
        "session_ref": binding.session_ref,
        "turn_ref": binding.turn_ref,
        "decision_ref": binding.decision_ref,
        "turn_contract": str(binding.turn_contract),
        "route_ref": binding.route_ref,
        "side_effect_class": binding.side_effect_class,
        "policy_ref": binding.policy_ref,
        "policy_version_ref": binding.policy_version_ref,
        "approval_ref": binding.approval_ref,
        "approval_scope_ref": binding.approval_scope_ref,
        "provider_ref": binding.provider_ref,
        "model_ref": binding.model_ref,
        "tool_refs": sorted(binding.tool_refs),
        "action_refs": sorted(binding.action_refs),
        "resource_refs": sorted(binding.resource_refs),
        "idempotency_key": binding.idempotency_key,
        "content_fingerprint_ref": binding.content_fingerprint_ref,
        "context_fingerprint_ref": binding.context_fingerprint_ref,
    }
    return _hash_ref("route-decision-binding-fingerprint", payload)


def safe_content_fingerprint_ref(value: str, *, namespace: str = "turn-content") -> str:
    return _hash_ref(f"{namespace}-fingerprint", {"sha256": hashlib.sha256(value.encode("utf-8")).hexdigest()})


def _scope_changed(binding: RouteDecisionBinding, context: RouteDecisionMutationContext) -> bool:
    scalar_fields = (
        "actor_ref",
        "session_ref",
        "turn_ref",
        "turn_contract",
        "route_ref",
        "side_effect_class",
        "approval_ref",
        "approval_scope_ref",
        "provider_ref",
        "model_ref",
        "idempotency_key",
        "content_fingerprint_ref",
        "context_fingerprint_ref",
    )
    if any(getattr(binding, field_name) != getattr(context, field_name) for field_name in scalar_fields):
        return True
    list_fields = ("tool_refs", "action_refs", "resource_refs")
    return any(sorted(getattr(binding, field_name)) != sorted(getattr(context, field_name)) for field_name in list_fields)


def _has_unsafe_payload_flags(binding: RouteDecisionBinding) -> bool:
    return bool(
        not binding.safe_refs_only
        or binding.raw_content_included
        or binding.route_decision_is_approval
        or binding.authority_granted
        or binding.execution_performed
    )


def _validation_result(
    binding: RouteDecisionBinding,
    status: RouteDecisionValidationStatus,
    safe_summary: str,
    reason_refs: list[str],
    fingerprint_ref: str,
    evidence_refs: list[str],
) -> RouteDecisionValidationResult:
    return RouteDecisionValidationResult(
        binding_ref=binding.binding_ref,
        status=status,
        allowed=status == RouteDecisionValidationStatus.valid,
        safe_summary=safe_summary,
        reason_refs=reason_refs,
        evidence_refs=evidence_refs,
        binding_fingerprint_ref=fingerprint_ref,
    )


def _hash_ref(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:safe-{digest}"


def _validate_optional_ref(value: str | None, field_name: str) -> None:
    if value is not None:
        validate_task_ref(value, field_name)


def _validate_ref_list(values: list[str], field_name: str) -> None:
    for value in values:
        validate_task_ref(value, field_name)


def _validate_required_blocked_authorities(values: list[str]) -> None:
    missing = set(ROUTE_DECISION_BINDING_REQUIRED_BLOCKED_AUTHORITY_REFS).difference(values)
    if missing:
        raise ValueError(f"route decision binding missing blocked authority ref: {sorted(missing)[0]}")
