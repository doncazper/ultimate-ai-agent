"""Declarative Browser Gateway Ladder contracts.

This module defines browser capability promotion posture only. It does not
perform web fetching, browser automation, provider calls, connector writes, or
runtime activation.
"""

from __future__ import annotations

from enum import Enum
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


class BrowserGatewayLadderState(str, Enum):
    DECLARED = "declared"
    DISCOVERED = "discovered"
    METADATA_ONLY = "metadata_only"
    OBSERVE_PLANNED = "observe_planned"
    OBSERVE_BLOCKED = "observe_blocked"
    ACTION_DRY_RUN_PLANNED = "action_dry_run_planned"
    ACTION_DRY_RUN_BLOCKED = "action_dry_run_blocked"
    EXACT_APPROVED_LOW_RISK_ACTION_PLANNED = (
        "exact_approved_low_risk_action_planned"
    )
    HIGH_RISK_ACTION_BLOCKED = "high_risk_action_blocked"
    AUTH_COOKIE_DOWNLOAD_UPLOAD_BLOCKED = "auth_cookie_download_upload_blocked"
    MUTATION_BLOCKED = "mutation_blocked"
    RUNTIME_DISABLED = "runtime_disabled"


class BrowserGatewayRiskClass(str, Enum):
    METADATA = "metadata"
    OBSERVE = "observe"
    ACTION_DRY_RUN = "action_dry_run"
    LOW_RISK_ACTION = "low_risk_action"
    HIGH_RISK_ACTION = "high_risk_action"
    AUTH_COOKIE_DOWNLOAD_UPLOAD = "auth_cookie_download_upload"
    MUTATION = "mutation"
    RUNTIME_DISABLED = "runtime_disabled"


class BrowserGatewayApprovalBindingStatus(str, Enum):
    APPROVAL_BOUND = "approval_bound"
    BLOCKED = "blocked"


BROWSER_GATEWAY_LADDER_STATES: tuple[str, ...] = tuple(
    state.value for state in BrowserGatewayLadderState
)
BROWSER_GATEWAY_DEFAULT_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-state-ref:browser:no-live-web-fetch",
    "blocked-state-ref:browser:no-live-browser-execution",
    "blocked-state-ref:browser:no-clicks",
    "blocked-state-ref:browser:no-forms",
    "blocked-state-ref:browser:no-auth-cookies",
    "blocked-state-ref:browser:no-download-upload",
    "blocked-state-ref:browser:no-public-web-mutation",
    "blocked-state-ref:browser:no-raw-page-payload",
    "blocked-state-ref:browser:no-model-provider-ui-authority",
)

_SAFE_REF_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]+$")
_RAW_OR_PRIVATE_MARKERS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "raw page",
    "raw_page",
    "raw dom",
    "raw_dom",
    "raw html",
    "raw_html",
    "raw payload",
    "raw_payload",
    "provider payload",
    "provider_payload",
    "provider exchange",
    "provider_exchange",
    "raw log",
    "raw_log",
    "/users/",
    "/home/",
    "c:\\users\\",
    "authorization: bearer",
    "api_key",
    "client_secret",
    "password:",
    "password=",
    "credential:",
    "credential=",
    "hostname:",
    "username:",
)
_RAW_URL_PREFIXES = ("http:", "https:", "file:", "data:", "javascript:")


class _BrowserGatewayModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=False,
    )

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


class BrowserGatewayLadderStepContract(_BrowserGatewayModel):
    sequence: int = Field(..., ge=1)
    state: BrowserGatewayLadderState
    operator_posture: Literal["declared", "metadata_only", "planned", "blocked"]
    risk_class: BrowserGatewayRiskClass
    safe_mode: str = Field(..., min_length=1, max_length=200)
    blocked_authority_refs: tuple[str, ...] = Field(
        default_factory=lambda: BROWSER_GATEWAY_DEFAULT_BLOCKED_AUTHORITY_REFS
    )
    gateway_boundary_ref: str = "boundary-ref:web-access-gateway:required"
    policy_decision_ref: str = "policy-decision-ref:browser-gateway:required"
    future_exact_approval_ref: str = "approval-ref:browser-gateway:not-granted"
    audit_ref: str = "audit-ref:browser-gateway:required"
    replay_ref: str = "replay-ref:browser-gateway:required"
    evidence_ref: str = "evidence-ref:browser-gateway:redacted-only"
    revocation_ref: str = "revocation-ref:browser-gateway:required"
    safe_disable_ref: str = "safe-disable-ref:browser-gateway:required"
    redaction_ref: str = "redaction-ref:browser-gateway:no-raw-page-payload"
    web_access_gateway_required: Literal[True] = True
    exact_approval_required_before_execution: Literal[True] = True
    audit_required: Literal[True] = True
    replay_required: Literal[True] = True
    revocation_required: Literal[True] = True
    safe_disable_required: Literal[True] = True
    redaction_required: Literal[True] = True
    live_web_fetch_allowed: Literal[False] = False
    live_browser_observe_allowed: Literal[False] = False
    live_browser_execution_allowed: Literal[False] = False
    browser_click_allowed: Literal[False] = False
    browser_form_fill_allowed: Literal[False] = False
    browser_auth_cookie_allowed: Literal[False] = False
    browser_download_upload_allowed: Literal[False] = False
    browser_mutation_allowed: Literal[False] = False
    raw_page_payload_persistence_allowed: Literal[False] = False
    connector_write_allowed: Literal[False] = False
    provider_model_authority_allowed: Literal[False] = False
    control_center_authority_allowed: Literal[False] = False
    runtime_activation_allowed: Literal[False] = False
    public_beta_claim_allowed: Literal[False] = False

    @field_validator(
        "gateway_boundary_ref",
        "policy_decision_ref",
        "future_exact_approval_ref",
        "audit_ref",
        "replay_ref",
        "evidence_ref",
        "revocation_ref",
        "safe_disable_ref",
        "redaction_ref",
    )
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _safe_ref(value)

    @field_validator("blocked_authority_refs")
    @classmethod
    def validate_blocked_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if not values:
            raise ValueError("BROWSER_GATEWAY_BLOCKED_AUTHORITY_REFS_REQUIRED")
        return tuple(_safe_ref(value) for value in values)

    @model_validator(mode="after")
    def validate_step(self) -> "BrowserGatewayLadderStepContract":
        _safe_payload(self.safe_mode, "BROWSER_GATEWAY_UNSAFE_SAFE_MODE")
        return self


class BrowserGatewayLadderContract(_BrowserGatewayModel):
    contract_ref: str = "contract-ref:browser-gateway-ladder:v1"
    states: tuple[BrowserGatewayLadderState, ...] = tuple(BrowserGatewayLadderState)
    steps: tuple[BrowserGatewayLadderStepContract, ...] = Field(
        default_factory=lambda: _default_ladder_steps()
    )
    web_access_gateway_required: Literal[True] = True
    live_web_fetch_allowed: Literal[False] = False
    live_browser_execution_allowed: Literal[False] = False
    provider_model_calls_allowed: Literal[False] = False
    connector_writes_allowed: Literal[False] = False
    runtime_activation_allowed: Literal[False] = False

    @field_validator("contract_ref")
    @classmethod
    def validate_contract_ref(cls, value: str) -> str:
        return _safe_ref(value)

    @model_validator(mode="after")
    def validate_ladder(self) -> "BrowserGatewayLadderContract":
        if tuple(state.value for state in self.states) != BROWSER_GATEWAY_LADDER_STATES:
            raise ValueError("BROWSER_GATEWAY_LADDER_STATES_REQUIRED")
        actual_states = tuple(step.state for step in self.steps)
        if actual_states != self.states:
            raise ValueError("BROWSER_GATEWAY_LADDER_STEP_ORDER_REQUIRED")
        if tuple(step.sequence for step in self.steps) != tuple(
            range(1, len(self.steps) + 1)
        ):
            raise ValueError("BROWSER_GATEWAY_LADDER_SEQUENCE_REQUIRED")
        return self


class BrowserGatewayIntentMetadata(_BrowserGatewayModel):
    intent_ref: str
    requested_state: BrowserGatewayLadderState
    risk_class: BrowserGatewayRiskClass
    source_ref: str
    safe_url_ref: str | None = None
    action_plan_ref: str | None = None
    policy_decision_ref: str = "policy-decision-ref:browser-gateway:blocked"
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    safe_disable_ref: str
    blocked_authority_refs: tuple[str, ...] = Field(
        default_factory=lambda: BROWSER_GATEWAY_DEFAULT_BLOCKED_AUTHORITY_REFS
    )
    web_access_gateway_required: Literal[True] = True
    web_content_instruction_use_allowed: Literal[False] = False
    model_output_authority_allowed: Literal[False] = False
    provider_output_authority_allowed: Literal[False] = False
    control_center_state_authority_allowed: Literal[False] = False
    live_browser_execution_allowed: Literal[False] = False
    raw_page_payload_persistence_allowed: Literal[False] = False

    @field_validator(
        "intent_ref",
        "source_ref",
        "safe_url_ref",
        "action_plan_ref",
        "policy_decision_ref",
        "audit_ref",
        "replay_ref",
        "revocation_ref",
        "safe_disable_ref",
    )
    @classmethod
    def validate_optional_refs(cls, value: str | None) -> str | None:
        return _safe_ref(value) if value is not None else None

    @field_validator("blocked_authority_refs")
    @classmethod
    def validate_blocked_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if not values:
            raise ValueError("BROWSER_GATEWAY_BLOCKED_AUTHORITY_REFS_REQUIRED")
        return tuple(_safe_ref(value) for value in values)

    @model_validator(mode="after")
    def validate_state_risk(self) -> "BrowserGatewayIntentMetadata":
        if self.requested_state == BrowserGatewayLadderState.MUTATION_BLOCKED:
            _require_risk(self.risk_class, BrowserGatewayRiskClass.MUTATION)
        if self.requested_state == BrowserGatewayLadderState.HIGH_RISK_ACTION_BLOCKED:
            _require_risk(self.risk_class, BrowserGatewayRiskClass.HIGH_RISK_ACTION)
        if self.requested_state == (
            BrowserGatewayLadderState.AUTH_COOKIE_DOWNLOAD_UPLOAD_BLOCKED
        ):
            _require_risk(
                self.risk_class,
                BrowserGatewayRiskClass.AUTH_COOKIE_DOWNLOAD_UPLOAD,
            )
        return self


class BrowserGatewayExactApprovalBinding(_BrowserGatewayModel):
    approval_ref: str
    intent_ref: str
    allowed_state: BrowserGatewayLadderState = (
        BrowserGatewayLadderState.EXACT_APPROVED_LOW_RISK_ACTION_PLANNED
    )
    risk_class: BrowserGatewayRiskClass = BrowserGatewayRiskClass.LOW_RISK_ACTION
    action_plan_ref: str
    policy_decision_ref: str
    scope_ref: str
    expires_ref: str
    expected_receipt_ref: str
    revocation_ref: str
    approval_source_ref: str = "approval-source-ref:local-approval-authority"
    execution_authorized: Literal[False] = False
    live_browser_execution_allowed: Literal[False] = False
    model_output_authority_allowed: Literal[False] = False
    provider_output_authority_allowed: Literal[False] = False
    control_center_state_authority_allowed: Literal[False] = False

    @field_validator(
        "approval_ref",
        "intent_ref",
        "action_plan_ref",
        "policy_decision_ref",
        "scope_ref",
        "expires_ref",
        "expected_receipt_ref",
        "revocation_ref",
        "approval_source_ref",
    )
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _safe_ref(value)

    @model_validator(mode="after")
    def validate_low_risk_plan_only(self) -> "BrowserGatewayExactApprovalBinding":
        if self.allowed_state != (
            BrowserGatewayLadderState.EXACT_APPROVED_LOW_RISK_ACTION_PLANNED
        ):
            raise ValueError("BROWSER_GATEWAY_ONLY_LOW_RISK_ACTION_PLANNED_BINDING")
        if self.risk_class != BrowserGatewayRiskClass.LOW_RISK_ACTION:
            raise ValueError("BROWSER_GATEWAY_ONLY_LOW_RISK_ACTION_BINDING")
        return self


class BrowserGatewayApprovalBindingDecision(_BrowserGatewayModel):
    approval_binding_valid: bool
    status: BrowserGatewayApprovalBindingStatus
    reason_codes: tuple[str, ...]
    safe_message: str = Field(..., min_length=1, max_length=240)
    approval_ref: str | None = None
    intent_ref: str
    action_plan_ref: str | None = None
    execution_authorized: Literal[False] = False
    live_browser_execution_allowed: Literal[False] = False
    model_output_authority_allowed: Literal[False] = False
    provider_output_authority_allowed: Literal[False] = False
    control_center_state_authority_allowed: Literal[False] = False

    @field_validator("approval_ref", "intent_ref", "action_plan_ref")
    @classmethod
    def validate_optional_refs(cls, value: str | None) -> str | None:
        return _safe_ref(value) if value is not None else None

    @field_validator("reason_codes")
    @classmethod
    def validate_reason_codes(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if not values:
            raise ValueError("BROWSER_GATEWAY_REASON_CODES_REQUIRED")
        return tuple(_safe_ref(value) for value in values)

    @model_validator(mode="after")
    def validate_decision(self) -> "BrowserGatewayApprovalBindingDecision":
        _safe_payload(self.safe_message, "BROWSER_GATEWAY_UNSAFE_DECISION_MESSAGE")
        if (
            self.status == BrowserGatewayApprovalBindingStatus.APPROVAL_BOUND
            and not self.approval_binding_valid
        ):
            raise ValueError("BROWSER_GATEWAY_APPROVAL_BOUND_REQUIRES_VALID_BINDING")
        if (
            self.status == BrowserGatewayApprovalBindingStatus.BLOCKED
            and self.approval_binding_valid
        ):
            raise ValueError("BROWSER_GATEWAY_BLOCKED_CANNOT_BE_VALID_BINDING")
        return self


class BrowserGatewayBlockedReceipt(_BrowserGatewayModel):
    receipt_ref: str
    intent_ref: str
    requested_state: BrowserGatewayLadderState
    status: Literal["blocked"] = "blocked"
    reason_codes: tuple[str, ...]
    safe_summary: str = Field(..., min_length=1, max_length=320)
    approval_ref: str | None = None
    approval_missing_ref: str | None = None
    redacted_page_ref: str
    redacted_source_ref: str
    policy_decision_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    safe_disable_ref: str
    blocked_authority_refs: tuple[str, ...] = Field(
        default_factory=lambda: BROWSER_GATEWAY_DEFAULT_BLOCKED_AUTHORITY_REFS
    )
    observe_performed: Literal[False] = False
    dry_run_executed: Literal[False] = False
    click_performed: Literal[False] = False
    form_submitted: Literal[False] = False
    auth_cookie_accessed: Literal[False] = False
    download_upload_performed: Literal[False] = False
    mutation_performed: Literal[False] = False
    provider_model_called: Literal[False] = False
    connector_write_performed: Literal[False] = False
    raw_page_payload_persisted: Literal[False] = False

    @field_validator(
        "receipt_ref",
        "intent_ref",
        "approval_ref",
        "approval_missing_ref",
        "redacted_page_ref",
        "redacted_source_ref",
        "policy_decision_ref",
        "audit_ref",
        "replay_ref",
        "revocation_ref",
        "safe_disable_ref",
    )
    @classmethod
    def validate_optional_refs(cls, value: str | None) -> str | None:
        return _safe_ref(value) if value is not None else None

    @field_validator("reason_codes", "blocked_authority_refs")
    @classmethod
    def validate_ref_tuples(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if not values:
            raise ValueError("BROWSER_GATEWAY_REFS_REQUIRED")
        return tuple(_safe_ref(value) for value in values)

    @model_validator(mode="after")
    def validate_receipt(self) -> "BrowserGatewayBlockedReceipt":
        _safe_payload(self.safe_summary, "BROWSER_GATEWAY_UNSAFE_RECEIPT_SUMMARY")
        return self


class BrowserGatewayReplayAuditRecord(_BrowserGatewayModel):
    replay_ref: str
    intent_ref: str
    policy_decision_ref: str
    approval_decision_ref: str
    receipt_ref: str
    revocation_ref: str
    reason_codes: tuple[str, ...]
    reconstructable_from_safe_refs: Literal[True] = True
    reexecution_allowed: Literal[False] = False
    raw_page_payload_available: Literal[False] = False
    model_provider_ui_authority_allowed: Literal[False] = False

    @field_validator(
        "replay_ref",
        "intent_ref",
        "policy_decision_ref",
        "approval_decision_ref",
        "receipt_ref",
        "revocation_ref",
    )
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _safe_ref(value)

    @field_validator("reason_codes")
    @classmethod
    def validate_reason_codes(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if not values:
            raise ValueError("BROWSER_GATEWAY_REASON_CODES_REQUIRED")
        return tuple(_safe_ref(value) for value in values)


def build_browser_gateway_ladder_contract() -> BrowserGatewayLadderContract:
    return BrowserGatewayLadderContract()


def build_browser_gateway_intent_metadata(
    *,
    intent_ref: str,
    requested_state: BrowserGatewayLadderState,
    risk_class: BrowserGatewayRiskClass,
    source_ref: str,
    audit_ref: str,
    replay_ref: str,
    revocation_ref: str,
    safe_disable_ref: str,
    safe_url_ref: str | None = None,
    action_plan_ref: str | None = None,
    policy_decision_ref: str = "policy-decision-ref:browser-gateway:blocked",
) -> BrowserGatewayIntentMetadata:
    return BrowserGatewayIntentMetadata(
        intent_ref=intent_ref,
        requested_state=requested_state,
        risk_class=risk_class,
        source_ref=source_ref,
        safe_url_ref=safe_url_ref,
        action_plan_ref=action_plan_ref,
        policy_decision_ref=policy_decision_ref,
        audit_ref=audit_ref,
        replay_ref=replay_ref,
        revocation_ref=revocation_ref,
        safe_disable_ref=safe_disable_ref,
    )


def evaluate_browser_gateway_exact_approval_binding(
    binding: BrowserGatewayExactApprovalBinding,
    *,
    requested_intent_ref: str,
    requested_state: BrowserGatewayLadderState,
    requested_action_plan_ref: str,
    policy_decision_ref: str,
) -> BrowserGatewayApprovalBindingDecision:
    requested_intent_ref = _safe_ref(requested_intent_ref)
    requested_action_plan_ref = _safe_ref(requested_action_plan_ref)
    policy_decision_ref = _safe_ref(policy_decision_ref)
    mismatches: list[str] = []

    if binding.intent_ref != requested_intent_ref:
        mismatches.append("BROWSER_GATEWAY_INTENT_REF_MISMATCH")
    if binding.allowed_state != requested_state:
        mismatches.append("BROWSER_GATEWAY_STATE_MISMATCH")
    if binding.action_plan_ref != requested_action_plan_ref:
        mismatches.append("BROWSER_GATEWAY_ACTION_PLAN_REF_MISMATCH")
    if binding.policy_decision_ref != policy_decision_ref:
        mismatches.append("BROWSER_GATEWAY_POLICY_DECISION_REF_MISMATCH")

    if mismatches:
        return BrowserGatewayApprovalBindingDecision(
            approval_binding_valid=False,
            status=BrowserGatewayApprovalBindingStatus.BLOCKED,
            reason_codes=tuple(mismatches),
            safe_message="Browser approval binding is blocked because exact refs differ.",
            approval_ref=binding.approval_ref,
            intent_ref=requested_intent_ref,
            action_plan_ref=requested_action_plan_ref,
        )

    return BrowserGatewayApprovalBindingDecision(
        approval_binding_valid=True,
        status=BrowserGatewayApprovalBindingStatus.APPROVAL_BOUND,
        reason_codes=("BROWSER_GATEWAY_EXACT_APPROVAL_BINDING_MATCHED",),
        safe_message=(
            "Browser approval refs match, but this contract does not authorize "
            "live browser execution."
        ),
        approval_ref=binding.approval_ref,
        intent_ref=requested_intent_ref,
        action_plan_ref=requested_action_plan_ref,
    )


def build_browser_gateway_blocked_receipt(
    *,
    receipt_ref: str,
    intent_ref: str,
    requested_state: BrowserGatewayLadderState,
    reason_codes: tuple[str, ...],
    safe_summary: str,
    redacted_page_ref: str,
    redacted_source_ref: str,
    policy_decision_ref: str,
    audit_ref: str,
    replay_ref: str,
    revocation_ref: str,
    safe_disable_ref: str,
    approval_ref: str | None = None,
    approval_missing_ref: str | None = None,
) -> BrowserGatewayBlockedReceipt:
    return BrowserGatewayBlockedReceipt(
        receipt_ref=receipt_ref,
        intent_ref=intent_ref,
        requested_state=requested_state,
        reason_codes=reason_codes,
        safe_summary=safe_summary,
        approval_ref=approval_ref,
        approval_missing_ref=approval_missing_ref,
        redacted_page_ref=redacted_page_ref,
        redacted_source_ref=redacted_source_ref,
        policy_decision_ref=policy_decision_ref,
        audit_ref=audit_ref,
        replay_ref=replay_ref,
        revocation_ref=revocation_ref,
        safe_disable_ref=safe_disable_ref,
    )


def build_browser_gateway_replay_audit_record(
    *,
    replay_ref: str,
    intent_ref: str,
    policy_decision_ref: str,
    approval_decision_ref: str,
    receipt_ref: str,
    revocation_ref: str,
    reason_codes: tuple[str, ...],
) -> BrowserGatewayReplayAuditRecord:
    return BrowserGatewayReplayAuditRecord(
        replay_ref=replay_ref,
        intent_ref=intent_ref,
        policy_decision_ref=policy_decision_ref,
        approval_decision_ref=approval_decision_ref,
        receipt_ref=receipt_ref,
        revocation_ref=revocation_ref,
        reason_codes=reason_codes,
    )


def _default_ladder_steps() -> tuple[BrowserGatewayLadderStepContract, ...]:
    rows = (
        (
            BrowserGatewayLadderState.DECLARED,
            "declared",
            BrowserGatewayRiskClass.METADATA,
            "Browser capability is named as a future boundary only.",
        ),
        (
            BrowserGatewayLadderState.DISCOVERED,
            "metadata_only",
            BrowserGatewayRiskClass.METADATA,
            "Browser capability metadata can be inspected as untrusted data.",
        ),
        (
            BrowserGatewayLadderState.METADATA_ONLY,
            "metadata_only",
            BrowserGatewayRiskClass.METADATA,
            "Imported browser capability candidates remain metadata only.",
        ),
        (
            BrowserGatewayLadderState.OBSERVE_PLANNED,
            "planned",
            BrowserGatewayRiskClass.OBSERVE,
            "Observe posture is planned behind WebAccessGateway with redacted refs.",
        ),
        (
            BrowserGatewayLadderState.OBSERVE_BLOCKED,
            "blocked",
            BrowserGatewayRiskClass.OBSERVE,
            "Live observe remains blocked until a later accepted promotion.",
        ),
        (
            BrowserGatewayLadderState.ACTION_DRY_RUN_PLANNED,
            "planned",
            BrowserGatewayRiskClass.ACTION_DRY_RUN,
            "Action dry-run posture is a reviewable plan only.",
        ),
        (
            BrowserGatewayLadderState.ACTION_DRY_RUN_BLOCKED,
            "blocked",
            BrowserGatewayRiskClass.ACTION_DRY_RUN,
            "Dry-run cannot execute clicks, forms, auth, uploads, or downloads.",
        ),
        (
            BrowserGatewayLadderState.EXACT_APPROVED_LOW_RISK_ACTION_PLANNED,
            "planned",
            BrowserGatewayRiskClass.LOW_RISK_ACTION,
            "Low-risk action execution is future work after exact approval proof.",
        ),
        (
            BrowserGatewayLadderState.HIGH_RISK_ACTION_BLOCKED,
            "blocked",
            BrowserGatewayRiskClass.HIGH_RISK_ACTION,
            "High-risk browser actions remain blocked.",
        ),
        (
            BrowserGatewayLadderState.AUTH_COOKIE_DOWNLOAD_UPLOAD_BLOCKED,
            "blocked",
            BrowserGatewayRiskClass.AUTH_COOKIE_DOWNLOAD_UPLOAD,
            "Auth, cookies, downloads, and uploads remain blocked.",
        ),
        (
            BrowserGatewayLadderState.MUTATION_BLOCKED,
            "blocked",
            BrowserGatewayRiskClass.MUTATION,
            "Public-web mutations and non-GET style actions remain blocked.",
        ),
        (
            BrowserGatewayLadderState.RUNTIME_DISABLED,
            "blocked",
            BrowserGatewayRiskClass.RUNTIME_DISABLED,
            "Browser runtime activation is disabled by default.",
        ),
    )
    return tuple(
        BrowserGatewayLadderStepContract(
            sequence=index,
            state=state,
            operator_posture=posture,  # type: ignore[arg-type]
            risk_class=risk,
            safe_mode=safe_mode,
        )
        for index, (state, posture, risk, safe_mode) in enumerate(rows, start=1)
    )


def _require_risk(
    actual: BrowserGatewayRiskClass,
    expected: BrowserGatewayRiskClass,
) -> None:
    if actual != expected:
        raise ValueError("BROWSER_GATEWAY_RISK_CLASS_MISMATCH")


def _safe_ref(value: str) -> str:
    normalized = value.strip().lower()
    if not value or any(character.isspace() for character in value):
        raise ValueError("BROWSER_GATEWAY_SAFE_REF_REQUIRED")
    if not _SAFE_REF_PATTERN.fullmatch(value):
        raise ValueError("BROWSER_GATEWAY_SAFE_REF_REQUIRED")
    if normalized.startswith(_RAW_URL_PREFIXES):
        raise ValueError("BROWSER_GATEWAY_RAW_URL_REF_DENIED")
    _safe_payload(value, "BROWSER_GATEWAY_UNSAFE_REF")
    return value


def _safe_payload(value: object, error_code: str) -> None:
    if (
        contains_secret_like(value)
        or contains_obvious_secret(value)
        or _contains_forbidden_marker(value)
    ):
        raise ValueError(error_code)


def _contains_forbidden_marker(value: object) -> bool:
    if isinstance(value, str):
        normalized = value.lower()
        if ("https" + "://") in normalized or ("http" + "://") in normalized:
            return True
        return any(marker in normalized for marker in _RAW_OR_PRIVATE_MARKERS)
    if isinstance(value, dict):
        return any(_contains_forbidden_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_marker(item) for item in value)
    return False
