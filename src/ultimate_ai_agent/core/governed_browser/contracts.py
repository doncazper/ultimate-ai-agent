"""Exact, content-free contracts for governed external actions.

The Queue 01 boundary is deliberately inactive for real external targets. The
contracts are useful now for deterministic local validation without granting
standing browser or external-mutation authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from enum import Enum
from typing import Any, Literal
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


def governed_receipt_identity_payload(receipt: BaseModel) -> dict[str, Any]:
    """Build a receipt identity payload without version-sensitive field metadata."""

    payload = receipt.model_dump(mode="json", exclude={"receipt_ref"})
    if payload.get("budget_release_ref") is None:
        payload.pop("budget_release_ref", None)
    return payload


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
    artifact_refs: tuple[str, ...] = Field(..., min_length=1, max_length=8)
    resource_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    action_count: StrictInt = Field(default=1, ge=1, le=1)
    page_snapshot_ref: str = Field(..., min_length=1, max_length=240)
    start_deadline: datetime
    human_presence_ref: str = Field(..., min_length=1, max_length=240)
    human_present: StrictBool

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_exact_binding(self) -> "ExternalActionAuthorityBinding":
        object.__setattr__(self, "origin", normalize_exact_origin(self.origin))
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

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

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
        if not re.fullmatch(
            r"idempotency-ref:[a-zA-Z0-9._:-]+:sha256:[0-9a-f]{64}",
            self.idempotency_ref,
        ):
            raise ValueError("GOVERNED_BROWSER_IDEMPOTENCY_REF_MISMATCH")
        return self


class ExternalActionAdversarialSignals(BaseModel):
    """Content-free hostile-site and race signals from one trusted adapter read."""

    schema_version: Literal["uaa-governed-external-action-adversarial-signals.v1"] = (
        "uaa-governed-external-action-adversarial-signals.v1"
    )
    cross_origin_redirect_detected: StrictBool
    dom_swap_detected: StrictBool
    hidden_field_detected: StrictBool
    changed_form_action_detected: StrictBool
    misleading_control_detected: StrictBool
    unexpected_popup_detected: StrictBool
    unexpected_download_detected: StrictBool
    page_mutation_after_approval_detected: StrictBool
    duplicate_submission_detected: StrictBool
    session_fixation_detected: StrictBool
    origin_confusion_detected: StrictBool
    upload_artifact_substitution_detected: StrictBool
    download_filename_attack_detected: StrictBool
    download_media_type_attack_detected: StrictBool
    download_signature_attack_detected: StrictBool
    recipient_substitution_detected: StrictBool
    content_substitution_detected: StrictBool
    amount_substitution_detected: StrictBool
    total_substitution_detected: StrictBool
    secret_canary_detected: StrictBool
    credential_canary_detected: StrictBool
    prompt_injection_detected: StrictBool
    raw_content_leak_detected: StrictBool
    raw_path_leak_detected: StrictBool
    cross_lane_interference_detected: StrictBool
    retry_requested: StrictBool
    resource_limit_exceeded: StrictBool
    active_resource_count: StrictInt = Field(..., ge=0, le=4)
    cleanup_verified: StrictBool

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @classmethod
    def clear_local_validation(cls) -> "ExternalActionAdversarialSignals":
        return cls(
            cross_origin_redirect_detected=False,
            dom_swap_detected=False,
            hidden_field_detected=False,
            changed_form_action_detected=False,
            misleading_control_detected=False,
            unexpected_popup_detected=False,
            unexpected_download_detected=False,
            page_mutation_after_approval_detected=False,
            duplicate_submission_detected=False,
            session_fixation_detected=False,
            origin_confusion_detected=False,
            upload_artifact_substitution_detected=False,
            download_filename_attack_detected=False,
            download_media_type_attack_detected=False,
            download_signature_attack_detected=False,
            recipient_substitution_detected=False,
            content_substitution_detected=False,
            amount_substitution_detected=False,
            total_substitution_detected=False,
            secret_canary_detected=False,
            credential_canary_detected=False,
            prompt_injection_detected=False,
            raw_content_leak_detected=False,
            raw_path_leak_detected=False,
            cross_lane_interference_detected=False,
            retry_requested=False,
            resource_limit_exceeded=False,
            active_resource_count=0,
            cleanup_verified=True,
        )

    def reason_refs(self) -> tuple[str, ...]:
        mapping = (
            ("cross_origin_redirect_detected", "cross-origin-redirect"),
            ("dom_swap_detected", "dom-swap"),
            ("hidden_field_detected", "hidden-field"),
            ("changed_form_action_detected", "changed-form-action"),
            ("misleading_control_detected", "misleading-control"),
            ("unexpected_popup_detected", "unexpected-popup"),
            ("unexpected_download_detected", "unexpected-download"),
            ("page_mutation_after_approval_detected", "page-mutation-after-approval"),
            ("duplicate_submission_detected", "duplicate-submission"),
            ("session_fixation_detected", "session-fixation"),
            ("origin_confusion_detected", "origin-confusion"),
            ("upload_artifact_substitution_detected", "upload-artifact-substitution"),
            ("download_filename_attack_detected", "download-filename-attack"),
            ("download_media_type_attack_detected", "download-media-type-attack"),
            ("download_signature_attack_detected", "download-signature-attack"),
            ("recipient_substitution_detected", "recipient-substitution"),
            ("content_substitution_detected", "content-substitution"),
            ("amount_substitution_detected", "amount-substitution"),
            ("total_substitution_detected", "total-substitution"),
            ("secret_canary_detected", "secret-canary"),
            ("credential_canary_detected", "credential-canary"),
            ("prompt_injection_detected", "prompt-injection-shaped-content"),
            ("raw_content_leak_detected", "raw-content-leak"),
            ("raw_path_leak_detected", "raw-path-leak"),
            ("cross_lane_interference_detected", "cross-lane-interference"),
            ("retry_requested", "automatic-retry-denied"),
            ("resource_limit_exceeded", "resource-limit-exceeded"),
        )
        reasons = [
            stable_governed_browser_ref(
                "reason-ref:governed-external-action:adversarial",
                {"signal": reason},
            )
            for field, reason in mapping
            if getattr(self, field)
        ]
        if not self.cleanup_verified:
            reasons.append(
                "reason-ref:governed-external-action:adversarial:cleanup-unverified"
            )
        return tuple(reasons)


class ExternalActionReadiness(BaseModel):
    schema_version: Literal["uaa-governed-external-action-readiness.v1"] = (
        "uaa-governed-external-action-readiness.v1"
    )
    readiness_ref: str
    binding_ref: str
    observed_origin_ref: str
    observed_recipient_ref: str
    observed_field_schema_ref: str
    observed_transaction_ref: str
    observed_artifact_refs: tuple[str, ...] = Field(..., min_length=1, max_length=8)
    observed_resource_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    page_snapshot_ref: str
    status: Literal["ready", "blocked"]
    observed_at: datetime
    expires_at: datetime
    broker_integrity_verified: StrictBool
    external_mutation_enabled: StrictBool
    safe_disable_active: StrictBool
    kill_switch_engaged: StrictBool
    adversarial_signals: ExternalActionAdversarialSignals

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_readiness(self) -> "ExternalActionReadiness":
        for value, label in [
            (self.readiness_ref, "readiness_ref"),
            (self.binding_ref, "binding_ref"),
            (self.observed_origin_ref, "observed_origin_ref"),
            (self.observed_recipient_ref, "observed_recipient_ref"),
            (self.observed_field_schema_ref, "observed_field_schema_ref"),
            (self.observed_transaction_ref, "observed_transaction_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            *[(ref, "observed_artifact_ref") for ref in self.observed_artifact_refs],
            *[(ref, "observed_resource_ref") for ref in self.observed_resource_refs],
        ]:
            validate_task_ref(value, label)
        if self.observed_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("GOVERNED_BROWSER_READINESS_TIMEZONE_REQUIRED")
        if self.expires_at <= self.observed_at:
            raise ValueError("GOVERNED_BROWSER_READINESS_WINDOW_INVALID")
        expected_ref = stable_governed_browser_ref(
            "readiness-ref:governed-external-action",
            self.model_dump(mode="json", exclude={"readiness_ref"}),
        )
        if self.readiness_ref != expected_ref:
            raise ValueError("GOVERNED_BROWSER_READINESS_REF_MISMATCH")
        return self


def build_external_action_readiness(
    request: ExternalActionExecutionRequest,
    *,
    status: Literal["ready", "blocked"],
    observed_at: datetime,
    expires_at: datetime,
    broker_integrity_verified: bool,
    external_mutation_enabled: bool,
    safe_disable_active: bool,
    kill_switch_engaged: bool,
    adversarial_signals: ExternalActionAdversarialSignals | None = None,
    binding_ref: str | None = None,
    observed_origin_ref: str | None = None,
    observed_recipient_ref: str | None = None,
    observed_field_schema_ref: str | None = None,
    observed_transaction_ref: str | None = None,
    observed_artifact_refs: tuple[str, ...] | None = None,
    observed_resource_refs: tuple[str, ...] | None = None,
    page_snapshot_ref: str | None = None,
) -> ExternalActionReadiness:
    binding = request.binding
    payload = {
        "binding_ref": (
            binding_ref if binding_ref is not None else binding.binding_ref
        ),
        "observed_origin_ref": (
            observed_origin_ref
            if observed_origin_ref is not None
            else binding.origin_ref
        ),
        "observed_recipient_ref": (
            observed_recipient_ref
            if observed_recipient_ref is not None
            else binding.recipient_ref
        ),
        "observed_field_schema_ref": (
            observed_field_schema_ref
            if observed_field_schema_ref is not None
            else binding.field_schema_ref
        ),
        "observed_transaction_ref": (
            observed_transaction_ref
            if observed_transaction_ref is not None
            else binding.transaction_ref
        ),
        "observed_artifact_refs": (
            tuple(observed_artifact_refs)
            if observed_artifact_refs is not None
            else tuple(binding.artifact_refs)
        ),
        "observed_resource_refs": (
            tuple(observed_resource_refs)
            if observed_resource_refs is not None
            else tuple(binding.resource_refs)
        ),
        "page_snapshot_ref": (
            page_snapshot_ref
            if page_snapshot_ref is not None
            else binding.page_snapshot_ref
        ),
        "status": status,
        "observed_at": observed_at,
        "expires_at": expires_at,
        "broker_integrity_verified": broker_integrity_verified,
        "external_mutation_enabled": external_mutation_enabled,
        "safe_disable_active": safe_disable_active,
        "kill_switch_engaged": kill_switch_engaged,
        "adversarial_signals": (
            adversarial_signals
            or ExternalActionAdversarialSignals.clear_local_validation()
        ),
    }
    draft = ExternalActionReadiness.model_construct(
        readiness_ref="readiness-ref:governed-external-action:unbound",
        **payload,
    )
    readiness_ref = stable_governed_browser_ref(
        "readiness-ref:governed-external-action",
        draft.model_dump(mode="json", exclude={"readiness_ref"}),
    )
    return ExternalActionReadiness(readiness_ref=readiness_ref, **payload)


class ExternalActionDispatchOutcome(str, Enum):
    succeeded = "succeeded"
    failed = "failed"
    outcome_ambiguous = "outcome_ambiguous"


class ExternalActionDispatchResult(BaseModel):
    outcome: ExternalActionDispatchOutcome
    evidence_refs: tuple[str, ...] = Field(..., min_length=1, max_length=12)
    operation_count: StrictInt = Field(default=1, ge=1, le=1)
    verified: StrictBool

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

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
    budget_release_ref: str | None = None
    budget_settlement_ref: str | None = None
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=12)
    reason_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=16)
    replayed: StrictBool = False
    content_free: Literal[True] = True
    automatic_retry_allowed: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

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
            (self.budget_release_ref, "budget_release_ref"),
            (self.budget_settlement_ref, "budget_settlement_ref"),
            *[(ref, "evidence_ref") for ref in self.evidence_refs],
            *[(ref, "reason_ref") for ref in self.reason_refs],
        ]:
            if value is not None:
                validate_task_ref(value, label)
        if (
            self.budget_release_ref is not None
            and self.budget_settlement_ref is not None
        ):
            raise ValueError("GOVERNED_BROWSER_BUDGET_ACCOUNTING_PROOF_CONFLICT")
        payload = {
            "transaction_ref": self.transaction_ref,
            "intent_ref": self.intent_ref,
            "binding_ref": self.binding_ref,
            "state": self.state,
            "approval_validation_ref": self.approval_validation_ref,
            "authority_decision_ref": self.authority_decision_ref,
            "budget_reservation_ref": self.budget_reservation_ref,
            "budget_settlement_ref": self.budget_settlement_ref,
            "evidence_refs": list(self.evidence_refs),
            "reason_refs": list(self.reason_refs),
        }
        if self.budget_release_ref is not None:
            payload["budget_release_ref"] = self.budget_release_ref
        expected_ref = stable_governed_browser_ref(
            "receipt-ref:governed-external-action",
            payload,
        )
        if self.receipt_ref != expected_ref:
            raise ValueError("GOVERNED_EXTERNAL_ACTION_RECEIPT_REF_MISMATCH")
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
