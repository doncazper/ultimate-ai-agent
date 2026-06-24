"""Contract-first Web Runtime Authority hardening lane.

This module is intentionally declarative. It adds no live web fetching,
browser automation, provider SDK calls, or callable runtime authority.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


class WebRuntimeNoun(str, Enum):
    WEB_REQUEST = "web_request"
    WEB_OBSERVATION = "web_observation"
    WEB_EVIDENCE = "web_evidence"
    WEB_APPROVAL = "web_approval"
    WEB_ACTION_PLAN = "web_action_plan"
    WEB_AUDIT_RECORD = "web_audit_record"


class WebOperatorStateLabel(str, Enum):
    BLOCKED = "blocked"
    DEGRADED = "degraded"
    PARTIAL = "partial"


class WebSideEffectKind(str, Enum):
    POST = "POST"
    CLICK = "click"
    FORM = "form"
    DOWNLOAD = "download"
    UPLOAD = "upload"


class WebSideEffectLedgerState(str, Enum):
    BLOCKED_PENDING_DURABLE_AUDIT = "blocked_pending_durable_audit"


class WebPromotionStep(str, Enum):
    CANONICAL_NOUNS = "canonical_runtime_nouns"
    DURABLE_AUDIT_STORAGE = "durable_web_audit_storage"
    SIDE_EFFECT_LEDGER = "side_effect_ledger_states"
    APPROVAL_LINKAGE = "approval_linkage_fields"
    OPERATOR_LABELS = "operator_blocked_degraded_partial_labels"
    PROVIDER_DIAGNOSTICS = "provider_diagnostics"
    CATALOG_MANIFEST_VISIBILITY = "catalog_manifest_visibility"


WEB_RUNTIME_CANONICAL_NOUNS: tuple[str, ...] = tuple(noun.value for noun in WebRuntimeNoun)
WEB_RUNTIME_REQUIRED_SIDE_EFFECTS: tuple[str, ...] = tuple(
    side_effect.value for side_effect in WebSideEffectKind
)
WEB_RUNTIME_REQUIRED_OPERATOR_LABELS: tuple[str, ...] = tuple(
    label.value for label in WebOperatorStateLabel
)
WEB_RUNTIME_PROMOTION_STEPS: tuple[str, ...] = tuple(step.value for step in WebPromotionStep)

_FORBIDDEN_RAW_PRIVATE_MARKERS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "provider exchange",
    "provider_exchange",
    "raw provider",
    "raw_provider",
    "prompt body",
    "response body",
    "provider exchange body",
    "raw body",
    "raw_body",
    "raw header",
    "raw_header",
    "raw log",
    "raw_log",
    "/users/",
    "/home/",
    "c:\\users\\",
    "environment dump",
    "env dump",
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


class _WebRuntimeAuthorityModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=True,
    )

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


class WebRuntimeAuditRecordContract(_WebRuntimeAuthorityModel):
    noun: Literal["web_audit_record"] = "web_audit_record"
    audit_record_ref: str = Field(..., min_length=1)
    web_request_ref: str = Field(..., min_length=1)
    web_evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    policy_decision_ref: str = Field(..., min_length=1)
    scope_ref: str = Field(..., min_length=1)
    actor_ref: str = Field(..., min_length=1)
    provider_safe_ref: str = "provider-ref:not-configured"
    model_safe_ref: str = "model-ref:not-configured"
    redacted_summary: str = Field(..., min_length=1, max_length=500)
    content_untrusted: Literal[True] = True
    safe_refs_only: Literal[True] = True
    redacted_summary_only: Literal[True] = True
    raw_prompt_stored: Literal[False] = False
    raw_response_stored: Literal[False] = False
    raw_provider_exchange_stored: Literal[False] = False
    raw_path_stored: Literal[False] = False
    raw_log_stored: Literal[False] = False
    private_identifier_stored: Literal[False] = False
    credential_material_stored: Literal[False] = False

    @model_validator(mode="after")
    def validate_safe_refs_only(self) -> "WebRuntimeAuditRecordContract":
        _validate_safe_ref(self.audit_record_ref, "audit_record_ref")
        _validate_safe_ref(self.web_request_ref, "web_request_ref")
        _validate_safe_ref(self.policy_decision_ref, "policy_decision_ref")
        _validate_safe_ref(self.scope_ref, "scope_ref")
        _validate_safe_ref(self.actor_ref, "actor_ref")
        _validate_safe_ref(self.provider_safe_ref, "provider_safe_ref")
        _validate_safe_ref(self.model_safe_ref, "model_safe_ref")
        for evidence_ref in self.web_evidence_refs:
            _validate_safe_ref(evidence_ref, "web_evidence_ref")
        _validate_safe_payload(
            self.redacted_summary,
            "WEB_RUNTIME_AUDIT_RECORD_UNSAFE_SUMMARY",
        )
        return self


class WebDurableAuditStorageContract(_WebRuntimeAuthorityModel):
    storage_ref: str = "web-audit-storage-ref:runtime-authority:required-before-execution"
    status: Literal["required_before_browser_or_provider_execution"] = (
        "required_before_browser_or_provider_execution"
    )
    durable_storage_required_before_provider_or_browser_execution: Literal[True] = True
    append_only_required: Literal[True] = True
    safe_refs_only: Literal[True] = True
    redacted_summary_only: Literal[True] = True
    retention_policy_ref: str = "retention-policy-ref:web-runtime-audit:redacted-only"
    redaction_policy_ref: str = "redaction-policy-ref:web-runtime-audit:no-raw-content"
    storage_verification_lane_ref: str = (
        "verification-lane:web-runtime-authority:durable-audit-storage"
    )
    runtime_execution_allowed_without_storage: Literal[False] = False

    @model_validator(mode="after")
    def validate_storage_posture(self) -> "WebDurableAuditStorageContract":
        for value, field_name in [
            (self.storage_ref, "storage_ref"),
            (self.retention_policy_ref, "retention_policy_ref"),
            (self.redaction_policy_ref, "redaction_policy_ref"),
            (self.storage_verification_lane_ref, "storage_verification_lane_ref"),
        ]:
            _validate_safe_ref(value, field_name)
        _require_verification_lane(self.storage_verification_lane_ref)
        return self


class WebSideEffectLedgerContract(_WebRuntimeAuthorityModel):
    side_effect: WebSideEffectKind
    ledger_state: WebSideEffectLedgerState = (
        WebSideEffectLedgerState.BLOCKED_PENDING_DURABLE_AUDIT
    )
    ledger_state_ref: str
    verification_lane_ref: str
    blocked_before_execution: Literal[True] = True
    execution_allowed: Literal[False] = False
    action_plan_only: Literal[True] = True
    approval_required_before_promotion: Literal[True] = True
    durable_audit_required_before_promotion: Literal[True] = True

    @model_validator(mode="after")
    def validate_ledger_state(self) -> "WebSideEffectLedgerContract":
        _validate_safe_ref(self.ledger_state_ref, "ledger_state_ref")
        _validate_safe_ref(self.verification_lane_ref, "verification_lane_ref")
        _require_verification_lane(self.verification_lane_ref)
        return self


class WebApprovalLinkageContract(_WebRuntimeAuthorityModel):
    noun: Literal["web_approval"] = "web_approval"
    approval_ref: str = "approval-ref:web-runtime:not-granted"
    approval_scope_ref: str = "approval-scope-ref:web-runtime:not-validated"
    linked_web_request_ref: str = "web-request-ref:not-bound"
    linked_web_evidence_ref: str = "web-evidence-ref:not-bound"
    linked_web_audit_record_ref: str = "web-audit-record-ref:not-bound"
    policy_decision_ref: str = "policy-decision-ref:web-runtime:blocked"
    exact_scope_validation_required: Literal[True] = True
    local_approval_authority_required: Literal[True] = True
    approval_ref_authority: Literal[False] = False
    execution_authorized: Literal[False] = False
    scoped_execution_allowed: Literal[False] = False

    @model_validator(mode="after")
    def validate_approval_linkage(self) -> "WebApprovalLinkageContract":
        for value, field_name in [
            (self.approval_ref, "approval_ref"),
            (self.approval_scope_ref, "approval_scope_ref"),
            (self.linked_web_request_ref, "linked_web_request_ref"),
            (self.linked_web_evidence_ref, "linked_web_evidence_ref"),
            (self.linked_web_audit_record_ref, "linked_web_audit_record_ref"),
            (self.policy_decision_ref, "policy_decision_ref"),
        ]:
            _validate_safe_ref(value, field_name)
        return self


class WebOperatorStateContract(_WebRuntimeAuthorityModel):
    label: WebOperatorStateLabel
    display_text: str = Field(..., min_length=1, max_length=80)
    safe_summary: str = Field(..., min_length=1, max_length=240)
    runtime_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_operator_copy(self) -> "WebOperatorStateContract":
        _validate_safe_payload(
            self.display_text,
            "WEB_RUNTIME_OPERATOR_LABEL_UNSAFE_TEXT",
        )
        _validate_safe_payload(
            self.safe_summary,
            "WEB_RUNTIME_OPERATOR_LABEL_UNSAFE_SUMMARY",
        )
        return self


class WebPromotionStepContract(_WebRuntimeAuthorityModel):
    step: WebPromotionStep
    verification_lane_ref: str
    required_nouns: tuple[WebRuntimeNoun, ...] = Field(default_factory=tuple)
    operator_label: WebOperatorStateLabel
    promotion_allowed: Literal[False] = False
    runtime_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_promotion_step(self) -> "WebPromotionStepContract":
        _validate_safe_ref(self.verification_lane_ref, "verification_lane_ref")
        _require_verification_lane(self.verification_lane_ref)
        if not self.required_nouns:
            raise ValueError("WEB_RUNTIME_PROMOTION_STEP_NOUNS_REQUIRED")
        return self


class WebProviderDiagnosticContract(_WebRuntimeAuthorityModel):
    provider_diagnostic_ref: str = "provider-diagnostic-ref:web-runtime:metadata-only"
    provider_manifest_ref: str = "provider-manifest-ref:web-runtime:not-configured"
    diagnostic_status: Literal["diagnostic_only"] = "diagnostic_only"
    operator_label: WebOperatorStateLabel = WebOperatorStateLabel.BLOCKED
    safe_summary: str = (
        "Provider diagnostics are metadata-only health posture and do not grant runtime."
    )
    diagnostic_only: Literal[True] = True
    provider_authority_granted: Literal[False] = False
    provider_sdk_call_allowed: Literal[False] = False
    provider_network_call_allowed: Literal[False] = False
    callable_runtime_authority: Literal[False] = False
    execution_authorized: Literal[False] = False

    @model_validator(mode="after")
    def validate_diagnostic_only(self) -> "WebProviderDiagnosticContract":
        _validate_safe_ref(self.provider_diagnostic_ref, "provider_diagnostic_ref")
        _validate_safe_ref(self.provider_manifest_ref, "provider_manifest_ref")
        _validate_safe_payload(
            self.safe_summary,
            "WEB_RUNTIME_PROVIDER_DIAGNOSTIC_UNSAFE_SUMMARY",
        )
        return self


class WebCatalogManifestVisibilityContract(_WebRuntimeAuthorityModel):
    catalog_ref: str = "catalog-ref:web-runtime:metadata-only"
    manifest_ref: str = "manifest-ref:web-runtime:metadata-only"
    visibility_status: Literal["metadata_only"] = "metadata_only"
    catalog_visible: Literal[True] = True
    manifest_visible: Literal[True] = True
    catalog_manifest_visibility_only: Literal[True] = True
    callable_runtime: Literal[False] = False
    runtime_import_allowed: Literal[False] = False
    provider_authority_granted: Literal[False] = False
    execution_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_visibility_only(self) -> "WebCatalogManifestVisibilityContract":
        _validate_safe_ref(self.catalog_ref, "catalog_ref")
        _validate_safe_ref(self.manifest_ref, "manifest_ref")
        return self


class WebRuntimeAuthorityContract(_WebRuntimeAuthorityModel):
    contract_ref: str = "contract-ref:web-runtime-authority-hardening:v1"
    canonical_nouns: tuple[WebRuntimeNoun, ...] = tuple(WebRuntimeNoun)
    durable_audit_storage: WebDurableAuditStorageContract = Field(
        default_factory=WebDurableAuditStorageContract
    )
    side_effect_ledger: tuple[WebSideEffectLedgerContract, ...] = Field(
        default_factory=lambda: tuple(
            WebSideEffectLedgerContract(
                side_effect=side_effect,
                ledger_state_ref=f"ledger-state-ref:web-runtime:{side_effect.value.lower()}:blocked",
                verification_lane_ref=(
                    "verification-lane:web-runtime-authority:"
                    f"side-effect-ledger-{side_effect.value.lower()}"
                ),
            )
            for side_effect in WebSideEffectKind
        )
    )
    approval_linkage: WebApprovalLinkageContract = Field(
        default_factory=WebApprovalLinkageContract
    )
    operator_states: tuple[WebOperatorStateContract, ...] = Field(
        default_factory=lambda: (
            WebOperatorStateContract(
                label=WebOperatorStateLabel.BLOCKED,
                display_text="Blocked",
                safe_summary="Execution remains unavailable until required evidence gates pass.",
            ),
            WebOperatorStateContract(
                label=WebOperatorStateLabel.DEGRADED,
                display_text="Degraded",
                safe_summary="Metadata is inspectable but runtime authority is unavailable.",
            ),
            WebOperatorStateContract(
                label=WebOperatorStateLabel.PARTIAL,
                display_text="Partial",
                safe_summary="The boundary exists, but promotion gates are incomplete.",
            ),
        )
    )
    promotion_steps: tuple[WebPromotionStepContract, ...] = Field(
        default_factory=lambda: (
            WebPromotionStepContract(
                step=WebPromotionStep.CANONICAL_NOUNS,
                verification_lane_ref="verification-lane:web-runtime-authority:canonical-nouns",
                required_nouns=(WebRuntimeNoun.WEB_REQUEST, WebRuntimeNoun.WEB_EVIDENCE),
                operator_label=WebOperatorStateLabel.PARTIAL,
            ),
            WebPromotionStepContract(
                step=WebPromotionStep.DURABLE_AUDIT_STORAGE,
                verification_lane_ref="verification-lane:web-runtime-authority:durable-audit-storage",
                required_nouns=(WebRuntimeNoun.WEB_AUDIT_RECORD,),
                operator_label=WebOperatorStateLabel.BLOCKED,
            ),
            WebPromotionStepContract(
                step=WebPromotionStep.SIDE_EFFECT_LEDGER,
                verification_lane_ref="verification-lane:web-runtime-authority:side-effect-ledger",
                required_nouns=(WebRuntimeNoun.WEB_ACTION_PLAN, WebRuntimeNoun.WEB_AUDIT_RECORD),
                operator_label=WebOperatorStateLabel.BLOCKED,
            ),
            WebPromotionStepContract(
                step=WebPromotionStep.APPROVAL_LINKAGE,
                verification_lane_ref="verification-lane:web-runtime-authority:approval-linkage",
                required_nouns=(WebRuntimeNoun.WEB_APPROVAL, WebRuntimeNoun.WEB_EVIDENCE),
                operator_label=WebOperatorStateLabel.BLOCKED,
            ),
            WebPromotionStepContract(
                step=WebPromotionStep.OPERATOR_LABELS,
                verification_lane_ref="verification-lane:web-runtime-authority:operator-labels",
                required_nouns=(WebRuntimeNoun.WEB_OBSERVATION, WebRuntimeNoun.WEB_EVIDENCE),
                operator_label=WebOperatorStateLabel.DEGRADED,
            ),
            WebPromotionStepContract(
                step=WebPromotionStep.PROVIDER_DIAGNOSTICS,
                verification_lane_ref="verification-lane:web-runtime-authority:provider-diagnostics",
                required_nouns=(WebRuntimeNoun.WEB_OBSERVATION,),
                operator_label=WebOperatorStateLabel.DEGRADED,
            ),
            WebPromotionStepContract(
                step=WebPromotionStep.CATALOG_MANIFEST_VISIBILITY,
                verification_lane_ref=(
                    "verification-lane:web-runtime-authority:"
                    "catalog-manifest-visibility"
                ),
                required_nouns=(WebRuntimeNoun.WEB_REQUEST,),
                operator_label=WebOperatorStateLabel.PARTIAL,
            ),
        )
    )
    provider_diagnostics: tuple[WebProviderDiagnosticContract, ...] = Field(
        default_factory=lambda: (WebProviderDiagnosticContract(),)
    )
    catalog_manifest_visibility: WebCatalogManifestVisibilityContract = Field(
        default_factory=WebCatalogManifestVisibilityContract
    )
    live_web_fetching_allowed: Literal[False] = False
    browser_automation_allowed: Literal[False] = False
    provider_sdk_calls_allowed: Literal[False] = False
    post_click_form_download_upload_allowed: Literal[False] = False
    callable_runtime_authority: Literal[False] = False

    @model_validator(mode="after")
    def validate_authority_contract(self) -> "WebRuntimeAuthorityContract":
        _validate_safe_ref(self.contract_ref, "contract_ref")
        if tuple(_enum_value(noun) for noun in self.canonical_nouns) != WEB_RUNTIME_CANONICAL_NOUNS:
            raise ValueError("WEB_RUNTIME_CANONICAL_NOUNS_REQUIRED")
        side_effects = {_enum_value(entry.side_effect) for entry in self.side_effect_ledger}
        if side_effects != set(WEB_RUNTIME_REQUIRED_SIDE_EFFECTS):
            raise ValueError("WEB_RUNTIME_SIDE_EFFECT_LEDGER_INCOMPLETE")
        labels = {_enum_value(state.label) for state in self.operator_states}
        if not set(WEB_RUNTIME_REQUIRED_OPERATOR_LABELS).issubset(labels):
            raise ValueError("WEB_RUNTIME_OPERATOR_LABELS_REQUIRED")
        steps = {_enum_value(step.step) for step in self.promotion_steps}
        if steps != set(WEB_RUNTIME_PROMOTION_STEPS):
            raise ValueError("WEB_RUNTIME_PROMOTION_STEPS_REQUIRED")
        for step in self.promotion_steps:
            _require_verification_lane(step.verification_lane_ref)
        return self


def build_web_runtime_authority_contract() -> WebRuntimeAuthorityContract:
    return WebRuntimeAuthorityContract()


def _validate_safe_ref(value: str, field_name: str) -> None:
    if not value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name}:WEB_RUNTIME_SAFE_REF_REQUIRED")
    _validate_safe_payload(value, f"{field_name}:WEB_RUNTIME_UNSAFE_REF")


def _validate_safe_payload(value: object, error_code: str) -> None:
    if (
        contains_secret_like(value)
        or contains_obvious_secret(value)
        or _contains_forbidden_value_marker(value)
    ):
        raise ValueError(error_code)


def _contains_forbidden_value_marker(value: object) -> bool:
    if isinstance(value, str):
        normalized = value.lower()
        return any(marker in normalized for marker in _FORBIDDEN_RAW_PRIVATE_MARKERS)
    if isinstance(value, dict):
        return any(_contains_forbidden_value_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_value_marker(item) for item in value)
    return False


def _require_verification_lane(value: str) -> None:
    if not value.startswith("verification-lane:web-runtime-authority:"):
        raise ValueError("WEB_RUNTIME_VERIFICATION_LANE_REQUIRED")


def _enum_value(value: object) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)
