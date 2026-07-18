"""Exact, content-free contracts for governed external actions.

The Queue 01 boundary is deliberately inactive for real external targets. The
contracts are useful now for deterministic local validation without granting
standing browser or external-mutation authority.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Literal
from urllib.parse import urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    model_validator,
)

from ultimate_ai_agent.core.approvals import ApprovalRiskLevel, ApprovalSubjectType
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
    AuthorityDomain,
)
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityAuthorityLevel,
    CapabilityCostClass,
    CapabilityKind,
    CapabilityLatencyClass,
    CapabilityPrivacyLevel,
    CoordinationMode,
    RiskLevel,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.models import (
    CapabilityManifest,
    ContextPolicy,
    QualitySignals,
    RuntimePolicy,
    SafetyPolicy,
)
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.planning.validation import validate_task_ref


GOVERNED_EXTERNAL_ACTION_LANE_REF = "authority-lane-ref:governed-external-action-v1"
GOVERNED_EXTERNAL_ACTION_CAPABILITY_REF = (
    "capability-ref:governed-external-action-transaction-v1"
)
GOVERNED_EXTERNAL_ACTION_ADAPTER_REF = (
    "adapter-ref:governed-external-action-inactive-v1"
)
GOVERNED_EXTERNAL_ACTION_TOOL_REF = "tool-ref:governed-external-action-v1"
GOVERNED_EXTERNAL_ACTION_SAFE_DISABLE_REF = (
    "safe-disable-ref:governed-external-actions:inactive"
)
GOVERNED_EXTERNAL_ACTION_ROLLBACK_REF = (
    "rollback-ref:governed-external-action-manual-review"
)


def stable_governed_browser_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


def normalize_exact_origin(value: str) -> str:
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("GOVERNED_BROWSER_ORIGIN_INVALID") from exc
    host = (parsed.hostname or "").lower().rstrip(".")
    loopback = host in {"localhost", "127.0.0.1", "::1"}
    if (
        not host
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or parsed.scheme not in {"https", "http"}
        or (parsed.scheme == "http" and not loopback)
    ):
        raise ValueError("GOVERNED_BROWSER_ORIGIN_INVALID")
    default_port = 443 if parsed.scheme == "https" else 80
    suffix = "" if port in {None, default_port} else f":{port}"
    host_text = f"[{host}]" if ":" in host else host
    return f"{parsed.scheme}://{host_text}{suffix}"


class ExternalActionTargetKind(str, Enum):
    local_validation = "local_validation"
    external = "external"


class ExternalActionState(str, Enum):
    prepared = "prepared"
    started = "started"
    blocked = "blocked"
    succeeded = "succeeded"
    failed = "failed"
    outcome_ambiguous = "outcome_ambiguous"


class ExternalActionAuthorityBinding(BaseModel):
    """One exact external-action scope; no field grants broader authority."""

    schema_version: Literal["uaa-governed-external-action-binding.v1"] = (
        "uaa-governed-external-action-binding.v1"
    )
    target_kind: ExternalActionTargetKind
    authority_capability: AuthorityCapability = Field(
        default=AuthorityCapability.execute,
        validate_default=True,
    )
    origin: str = Field(..., min_length=1, max_length=240)
    origin_ref: str = Field(..., min_length=1, max_length=240)
    recipient_ref: str = Field(..., min_length=1, max_length=240)
    field_schema_ref: str = Field(..., min_length=1, max_length=240)
    transaction_ref: str = Field(..., min_length=1, max_length=240)
    artifact_refs: list[str] = Field(..., min_length=1, max_length=8)
    resource_refs: list[str] = Field(..., min_length=1, max_length=16)
    action_count: StrictInt = Field(default=1, ge=1, le=1)
    page_snapshot_ref: str = Field(..., min_length=1, max_length=240)
    start_deadline: datetime
    human_presence_ref: str = Field(..., min_length=1, max_length=240)
    human_present: StrictBool

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_exact_binding(self) -> "ExternalActionAuthorityBinding":
        self.origin = normalize_exact_origin(self.origin)
        expected_origin_ref = stable_governed_browser_ref(
            "origin-ref:governed-browser", {"origin": self.origin}
        )
        if self.origin_ref != expected_origin_ref:
            raise ValueError("GOVERNED_BROWSER_ORIGIN_REF_MISMATCH")
        if self.start_deadline.tzinfo is None:
            raise ValueError("GOVERNED_BROWSER_DEADLINE_TIMEZONE_REQUIRED")
        for value, label in [
            (self.origin_ref, "origin_ref"),
            (self.recipient_ref, "recipient_ref"),
            (self.field_schema_ref, "field_schema_ref"),
            (self.transaction_ref, "transaction_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            (self.human_presence_ref, "human_presence_ref"),
            *[(ref, "artifact_ref") for ref in self.artifact_refs],
            *[(ref, "resource_ref") for ref in self.resource_refs],
        ]:
            validate_task_ref(value, label)
        if len(set(self.artifact_refs)) != len(self.artifact_refs):
            raise ValueError("GOVERNED_BROWSER_DUPLICATE_ARTIFACT_REF")
        if len(set(self.resource_refs)) != len(self.resource_refs):
            raise ValueError("GOVERNED_BROWSER_DUPLICATE_RESOURCE_REF")
        return self

    @property
    def binding_ref(self) -> str:
        return stable_governed_browser_ref(
            "authority-binding-ref:governed-external-action",
            self.model_dump(mode="json"),
        )

    def exact_resource_refs(self) -> list[str]:
        return [
            self.origin_ref,
            self.recipient_ref,
            self.field_schema_ref,
            self.transaction_ref,
            *self.artifact_refs,
            *self.resource_refs,
            self.page_snapshot_ref,
            self.human_presence_ref,
        ]


class ExternalActionExecutionRequest(BaseModel):
    schema_version: Literal["uaa-governed-external-action-request.v1"] = (
        "uaa-governed-external-action-request.v1"
    )
    binding: ExternalActionAuthorityBinding
    run_ref: str = Field(..., min_length=1, max_length=240)
    task_ref: str = Field(..., min_length=1, max_length=240)
    intent_ref: str = Field(..., min_length=1, max_length=240)
    idempotency_ref: str = Field(..., min_length=1, max_length=240)
    lease_ref: str = Field(..., min_length=1, max_length=240)
    approval_ref: str = Field(..., min_length=1, max_length=240)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_execution_request(self) -> "ExternalActionExecutionRequest":
        for value, label in [
            (self.run_ref, "run_ref"),
            (self.task_ref, "task_ref"),
            (self.intent_ref, "intent_ref"),
            (self.idempotency_ref, "idempotency_ref"),
            (self.lease_ref, "lease_ref"),
            (self.approval_ref, "approval_ref"),
        ]:
            validate_task_ref(value, label)
        expected = stable_governed_browser_ref(
            "intent-ref:governed-external-action",
            {
                "binding_ref": self.binding.binding_ref,
                "run_ref": self.run_ref,
                "task_ref": self.task_ref,
                "lease_ref": self.lease_ref,
            },
        )
        if self.intent_ref != expected:
            raise ValueError("GOVERNED_BROWSER_INTENT_REF_MISMATCH")
        return self


class ExternalActionReadiness(BaseModel):
    schema_version: Literal["uaa-governed-external-action-readiness.v1"] = (
        "uaa-governed-external-action-readiness.v1"
    )
    readiness_ref: str
    binding_ref: str
    page_snapshot_ref: str
    status: Literal["ready", "blocked"]
    observed_at: datetime
    expires_at: datetime
    broker_integrity_verified: StrictBool
    external_mutation_enabled: StrictBool
    safe_disable_active: StrictBool
    kill_switch_engaged: StrictBool

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_readiness(self) -> "ExternalActionReadiness":
        for value, label in [
            (self.readiness_ref, "readiness_ref"),
            (self.binding_ref, "binding_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
        ]:
            validate_task_ref(value, label)
        if self.observed_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("GOVERNED_BROWSER_READINESS_TIMEZONE_REQUIRED")
        if self.expires_at <= self.observed_at:
            raise ValueError("GOVERNED_BROWSER_READINESS_WINDOW_INVALID")
        return self


class ExternalActionDispatchOutcome(str, Enum):
    succeeded = "succeeded"
    failed = "failed"
    outcome_ambiguous = "outcome_ambiguous"


class ExternalActionDispatchResult(BaseModel):
    outcome: ExternalActionDispatchOutcome
    evidence_refs: list[str] = Field(..., min_length=1, max_length=12)
    operation_count: StrictInt = Field(default=1, ge=1, le=1)
    verified: StrictBool

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_dispatch_result(self) -> "ExternalActionDispatchResult":
        for ref in self.evidence_refs:
            validate_task_ref(ref, "external_action_evidence_ref")
        if (
            self.outcome == ExternalActionDispatchOutcome.succeeded.value
            and not self.verified
        ):
            raise ValueError("GOVERNED_BROWSER_SUCCESS_REQUIRES_VERIFICATION")
        return self


class ExternalActionReceipt(BaseModel):
    schema_version: Literal["uaa-governed-external-action-receipt.v1"] = (
        "uaa-governed-external-action-receipt.v1"
    )
    receipt_ref: str
    transaction_ref: str
    intent_ref: str
    binding_ref: str
    state: ExternalActionState
    approval_validation_ref: str | None = None
    authority_decision_ref: str | None = None
    budget_reservation_ref: str | None = None
    budget_settlement_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list, max_length=12)
    reason_refs: list[str] = Field(default_factory=list, max_length=16)
    replayed: StrictBool = False
    content_free: Literal[True] = True
    automatic_retry_allowed: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> "ExternalActionReceipt":
        for value, label in [
            (self.receipt_ref, "receipt_ref"),
            (self.transaction_ref, "transaction_ref"),
            (self.intent_ref, "intent_ref"),
            (self.binding_ref, "binding_ref"),
            (self.approval_validation_ref, "approval_validation_ref"),
            (self.authority_decision_ref, "authority_decision_ref"),
            (self.budget_reservation_ref, "budget_reservation_ref"),
            (self.budget_settlement_ref, "budget_settlement_ref"),
            *[(ref, "evidence_ref") for ref in self.evidence_refs],
            *[(ref, "reason_ref") for ref in self.reason_refs],
        ]:
            if value is not None:
                validate_task_ref(value, label)
        return self


def build_external_action_authority_request(
    request: ExternalActionExecutionRequest,
) -> AuthorityActionRequest:
    binding = request.binding
    return AuthorityActionRequest(
        action_ref=stable_governed_browser_ref(
            "authority-action-ref:governed-external-action",
            {"intent_ref": request.intent_ref, "binding_ref": binding.binding_ref},
        ),
        domain=AuthorityDomain.browser,
        capability=AuthorityCapability(binding.authority_capability),
        safe_summary="Evaluate one exact governed external-action transaction.",
        resource_refs=binding.exact_resource_refs(),
        route_ref="core/governed-browser/external-action-transaction",
        capability_ref=GOVERNED_EXTERNAL_ACTION_CAPABILITY_REF,
        lane_ref=GOVERNED_EXTERNAL_ACTION_LANE_REF,
        adapter_ref=GOVERNED_EXTERNAL_ACTION_ADAPTER_REF,
        constraint_claims=[
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.operation_budget,
                value=binding.action_count,
            ),
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.cost_budget_microusd,
                value=0,
            ),
        ],
        constraints={
            "tool_ref": GOVERNED_EXTERNAL_ACTION_TOOL_REF,
            "binding_ref": binding.binding_ref,
            "request_fingerprint_ref": request.intent_ref,
            "start_deadline_ref": stable_governed_browser_ref(
                "start-deadline-ref:governed-external-action",
                {"deadline": binding.start_deadline.isoformat()},
            ),
            "human_presence_ref": binding.human_presence_ref,
            "human_present": binding.human_present,
            "external_target": binding.target_kind
            == ExternalActionTargetKind.external.value,
        },
        rollback_ref=GOVERNED_EXTERNAL_ACTION_ROLLBACK_REF,
        safe_disable_ref=GOVERNED_EXTERNAL_ACTION_SAFE_DISABLE_REF,
    )


def build_external_action_approval_request(
    request: ExternalActionExecutionRequest,
) -> ApprovalRequest:
    action = build_external_action_authority_request(request)
    return ApprovalRequest(
        approval_request_id=stable_governed_browser_ref(
            "approval-request-ref:governed-external-action",
            {"intent_ref": request.intent_ref},
        ),
        run_id=request.run_ref,
        subject_type=ApprovalSubjectType.tool_request,
        subject_id=action.action_ref,
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="operator-ref:local-user",
            authority_source=AuthoritySource.explicit_user_request,
            created_at=request.binding.start_deadline,
        ),
        requested_action=action.action_ref,
        purpose="Approve one exact governed external-action transaction.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="governed_external_action_exact_scope",
            requires_redaction=True,
            requires_consent=True,
        ),
        resource_refs=[
            request.lease_ref,
            GOVERNED_EXTERNAL_ACTION_ADAPTER_REF,
            *request.binding.exact_resource_refs(),
        ],
        expires_at=request.binding.start_deadline,
    )


def build_external_action_capability_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id=GOVERNED_EXTERNAL_ACTION_CAPABILITY_REF,
        version="1.0.0",
        kind=CapabilityKind.deterministic,
        name="Governed external-action transaction",
        description=(
            "Validate one exact external-action envelope; real targets remain inactive."
        ),
        examples=["Run one injected local-validation transaction."],
        anti_examples=[
            "Grant standing browser authority or execute against a real external target."
        ],
        input_schema={"type": "object", "required": ["intent_ref"]},
        output_schema={"type": "object", "required": ["receipt_ref", "state"]},
        input_modes=["safe_refs_only"],
        output_modes=["content_free_receipt"],
        side_effects=SideEffectLevel.external,
        risk_level=RiskLevel.high,
        authority_level=CapabilityAuthorityLevel.external,
        approval_required=True,
        deterministic=True,
        rollback_supported=True,
        receipt_required=True,
        privacy_level=CapabilityPrivacyLevel.local_private,
        estimated_latency_class=CapabilityLatencyClass.interactive,
        estimated_cost_class=CapabilityCostClass.none,
        evidence_required=True,
        memory_write_allowed=False,
        context_injection_allowed=False,
        provider_runtime_allowed=False,
        browser_runtime_allowed=False,
        connector_write_allowed=False,
        sandbox_profile="governed-browser-injected-local-validation-v1",
        allowed_coordination_modes=[CoordinationMode.workflow_node],
        concurrency_safe=False,
        single_writer_required=True,
        context_policy=ContextPolicy(
            required_context_keys=["binding_ref", "idempotency_key"],
            allow_memory_refs=False,
            allow_raw_content=False,
        ),
        runtime_policy=RuntimePolicy(
            timeout_seconds=30,
            max_retries=0,
            max_concurrency=1,
            deterministic=True,
        ),
        safety=SafetyPolicy(
            allow_parallel=False,
            require_single_writer=True,
            approval_required=True,
            max_risk_level=RiskLevel.high,
            max_side_effect_level=SideEffectLevel.external,
        ),
        quality=QualitySignals(
            test_coverage_refs=["test-ref:governed-browser-queue-01-group-01"],
            owner_reviewed=True,
        ),
        metadata={
            "status": "implemented_inactive",
            "real_external_targets_enabled": False,
            "approval_refs_are_identifiers_only": True,
            "automatic_retry_allowed": False,
        },
    )
