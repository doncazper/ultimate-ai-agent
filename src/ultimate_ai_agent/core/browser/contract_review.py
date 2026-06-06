from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


BROWSER_AUTOMATION_CONTRACT_REVIEW_DOCS = [
    "docs/browser/BROWSER_AUTOMATION_CONTRACT_REVIEW.md",
    "docs/browser/BROWSER_AUTOMATION_CONTRACT_REVIEW_POLICY.md",
    "docs/browser/BROWSER_AUTOMATION_AUTHORITY_BOUNDARY.md",
    "docs/browser/BROWSER_AUTOMATION_RECEIPT_PLAN.md",
    "docs/browser/M73_TO_M74_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]


class BrowserAutomationCapabilityKind(str, Enum):
    observe_only_adapter = "observe_only_adapter"
    navigation = "navigation"
    click = "click"
    form_fill = "form_fill"
    screenshot_capture = "screenshot_capture"
    dom_read = "dom_read"
    download_or_upload = "download_or_upload"
    authenticated_profile_access = "authenticated_profile_access"
    remote_browser_control = "remote_browser_control"
    browser_network_interception = "browser_network_interception"
    unknown = "unknown"


class BrowserAutomationContractReviewStatus(str, Enum):
    review_ready = "review_ready"
    future_milestone = "future_milestone"
    denied = "denied"


class _BrowserAutomationContractReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class BrowserAutomationContractReviewPolicy(_BrowserAutomationContractReviewModel):
    policy_ref: str = "browser-automation-contract-review-policy:m73"
    contract_only: bool = True
    review_only: bool = True
    disabled_by_default: bool = True
    deterministic: bool = True
    m74_candidate_only: bool = True
    browser_automation_enabled: bool = False
    browser_observe_enabled: bool = False
    browser_navigation_enabled: bool = False
    browser_click_enabled: bool = False
    form_fill_enabled: bool = False
    screenshot_enabled: bool = False
    dom_read_enabled: bool = False
    authenticated_profile_enabled: bool = False
    download_or_upload_enabled: bool = False
    remote_browser_enabled: bool = False
    network_interception_enabled: bool = False
    network_call_enabled: bool = False
    model_call_enabled: bool = False
    tool_execution_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_change_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class BrowserAutomationContractReviewRequest(_BrowserAutomationContractReviewModel):
    review_ref: str
    candidate_ref: str
    actor_ref: str
    proposed_adapter_ref: str
    safe_name: str
    capability_kind: BrowserAutomationCapabilityKind
    safe_summary: str
    safe_browser_policy_ref: str
    risk_ref: str
    approval_ref: str | None = None
    approval_test_ref: str | None = None
    authority_refs: list[str] = Field(default_factory=list)
    contract_only: bool = True
    review_only: bool = True
    disabled_by_default: bool = True
    deterministic: bool = True
    m74_candidate_only: bool = True
    browser_automation_requested: bool = False
    browser_observe_requested: bool = False
    browser_navigation_requested: bool = False
    browser_click_requested: bool = False
    form_fill_requested: bool = False
    screenshot_requested: bool = False
    dom_read_requested: bool = False
    authenticated_profile_requested: bool = False
    download_or_upload_requested: bool = False
    remote_browser_requested: bool = False
    network_interception_requested: bool = False
    network_call_requested: bool = False
    model_call_requested: bool = False
    tool_execution_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    production_authority_requested: bool = False
    contains_raw_dom: bool = False
    contains_screenshot_bytes: bool = False
    contains_browser_profile_path: bool = False
    contains_cookies_or_credentials: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.review_ref, "review_ref"),
            (self.candidate_ref, "candidate_ref"),
            (self.actor_ref, "actor_ref"),
            (self.proposed_adapter_ref, "proposed_adapter_ref"),
            (self.safe_browser_policy_ref, "safe_browser_policy_ref"),
            (self.risk_ref, "risk_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if self.approval_ref is not None:
            _validate_m61_ref(self.approval_ref, "approval_ref")
        if self.approval_test_ref is not None:
            if str(self.approval_test_ref).startswith("approval_test"):
                raise ValueError("APPROVAL_TEST_REF_DENIED")
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        for ref in self.authority_refs:
            _validate_m61_ref(ref, "authority_ref")
        _validate_safe_payload(self.safe_name)
        _validate_safe_payload(self.safe_summary)
        return self


class BrowserAutomationContractReviewReceiptPlan(_BrowserAutomationContractReviewModel):
    receipt_ref: str
    candidate_ref: str
    review_ref: str
    contract_only: bool = True
    review_only: bool = True
    browser_automation_performed: bool = False
    browser_observe_performed: bool = False
    browser_navigation_performed: bool = False
    browser_click_performed: bool = False
    form_fill_performed: bool = False
    screenshot_stored: bool = False
    raw_dom_stored: bool = False
    authenticated_profile_used: bool = False
    cookies_or_credentials_used: bool = False
    network_call_performed: bool = False
    tool_execution_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.receipt_ref, "receipt_ref"),
            (self.candidate_ref, "candidate_ref"),
            (self.review_ref, "review_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        return self


class BrowserAutomationContractReviewDecision(_BrowserAutomationContractReviewModel):
    decision_ref: str
    review_ref: str
    candidate_ref: str
    proposed_adapter_ref: str
    capability_kind: BrowserAutomationCapabilityKind
    status: BrowserAutomationContractReviewStatus
    review_allowed: bool
    contract_only: bool = True
    review_only: bool = True
    disabled_by_default: bool = True
    deterministic: bool = True
    m74_candidate_only: bool = True
    future_milestone_required: bool = True
    browser_automation_allowed: bool = False
    browser_observe_allowed: bool = False
    browser_navigation_allowed: bool = False
    browser_click_allowed: bool = False
    form_fill_allowed: bool = False
    screenshot_allowed: bool = False
    dom_read_allowed: bool = False
    authenticated_profile_allowed: bool = False
    download_or_upload_allowed: bool = False
    remote_browser_allowed: bool = False
    network_interception_allowed: bool = False
    network_call_allowed: bool = False
    model_call_allowed: bool = False
    tool_execution_allowed: bool = False
    memory_write_allowed: bool = False
    context_injection_allowed: bool = False
    backend_route_allowed: bool = False
    control_center_control_allowed: bool = False
    dependency_change_allowed: bool = False
    production_authority_granted: bool = False
    receipt_plan: BrowserAutomationContractReviewReceiptPlan
    reason_codes: list[str]
    safe_summary: str

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.review_ref, "review_ref"),
            (self.candidate_ref, "candidate_ref"),
            (self.proposed_adapter_ref, "proposed_adapter_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def validate_browser_automation_contract_review_policy(
    policy: BrowserAutomationContractReviewPolicy,
) -> BrowserAutomationContractReviewPolicy:
    payload = _model_payload(policy)
    for field_name, reason in _POLICY_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = BrowserAutomationContractReviewPolicy.model_validate(payload)
    for field_name, reason in _POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_BROWSER_CONTENT_DENIED") from exc
    return validated


def validate_browser_automation_contract_review_request(
    request: BrowserAutomationContractReviewRequest,
) -> BrowserAutomationContractReviewRequest:
    payload = _model_payload(request)
    for field_name, reason in _REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, BrowserAutomationContractReviewRequest):
        raise ValueError("SECRET_LIKE_BROWSER_CONTENT_DENIED")
    validated = BrowserAutomationContractReviewRequest.model_validate(payload)
    for field_name, reason in _REQUEST_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.approval_ref:
        raise ValueError("APPROVAL_REF_NOT_AUTHORITY")
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    if validated.authority_refs:
        raise ValueError("AUTHORITY_REF_NOT_BROWSER_AUTHORITY")
    if validated.side_effects_performed:
        raise ValueError("BROWSER_SIDE_EFFECTS_DENIED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_BROWSER_CONTENT_DENIED") from exc
    return validated


def build_browser_automation_contract_review_decision(
    request: BrowserAutomationContractReviewRequest,
    policy: BrowserAutomationContractReviewPolicy | None = None,
) -> BrowserAutomationContractReviewDecision:
    active_policy = validate_browser_automation_contract_review_policy(
        policy or BrowserAutomationContractReviewPolicy()
    )
    validated_request = validate_browser_automation_contract_review_request(request)
    receipt_plan = BrowserAutomationContractReviewReceiptPlan(
        receipt_ref=f"browser-contract-review-receipt:{_ref_suffix(validated_request.candidate_ref)}",
        candidate_ref=validated_request.candidate_ref,
        review_ref=validated_request.review_ref,
    )
    if validated_request.capability_kind == BrowserAutomationCapabilityKind.unknown:
        return validate_browser_automation_contract_review_decision(
            BrowserAutomationContractReviewDecision(
                decision_ref=f"browser-contract-review-decision:{_ref_suffix(validated_request.candidate_ref)}",
                review_ref=validated_request.review_ref,
                candidate_ref=validated_request.candidate_ref,
                proposed_adapter_ref=validated_request.proposed_adapter_ref,
                capability_kind=validated_request.capability_kind,
                status=BrowserAutomationContractReviewStatus.denied,
                review_allowed=False,
                receipt_plan=receipt_plan,
                reason_codes=[
                    "UNKNOWN_BROWSER_CAPABILITY_DENIED",
                    "M73_BROWSER_AUTOMATION_CONTRACT_REVIEW_ONLY",
                ],
                safe_summary="Unknown browser capability is denied for M73 contract review.",
            )
        )
    if validated_request.capability_kind == BrowserAutomationCapabilityKind.observe_only_adapter:
        reason_codes = [
            "M73_BROWSER_AUTOMATION_CONTRACT_REVIEW_ONLY",
            "M73_NO_BROWSER_AUTOMATION_AUTHORITY",
            "M74_REMAINS_FUTURE",
        ]
        status = BrowserAutomationContractReviewStatus.review_ready
    else:
        reason_codes = [
            "M73_BROWSER_AUTOMATION_CONTRACT_REVIEW_ONLY",
            "FUTURE_BROWSER_MILESTONE_REQUIRED",
        ]
        status = BrowserAutomationContractReviewStatus.future_milestone

    return validate_browser_automation_contract_review_decision(
        BrowserAutomationContractReviewDecision(
            decision_ref=f"browser-contract-review-decision:{_ref_suffix(validated_request.candidate_ref)}",
            review_ref=validated_request.review_ref,
            candidate_ref=validated_request.candidate_ref,
            proposed_adapter_ref=validated_request.proposed_adapter_ref,
            capability_kind=validated_request.capability_kind,
            status=status,
            review_allowed=True,
            contract_only=active_policy.contract_only,
            review_only=active_policy.review_only,
            disabled_by_default=active_policy.disabled_by_default,
            deterministic=active_policy.deterministic,
            m74_candidate_only=active_policy.m74_candidate_only,
            future_milestone_required=True,
            receipt_plan=receipt_plan,
            reason_codes=reason_codes,
            safe_summary=(
                "M73 reviews future browser automation contracts only. It performs no browser "
                "automation, navigation, click, form fill, screenshot capture, DOM read, "
                "network call, tool execution, backend route, Control Center control, or "
                "production authority, and keeps M74 future."
            ),
        )
    )


def validate_browser_automation_contract_review_decision(
    decision: BrowserAutomationContractReviewDecision,
) -> BrowserAutomationContractReviewDecision:
    validated = BrowserAutomationContractReviewDecision.model_validate(_model_payload(decision))
    for field_name, reason in _DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status == BrowserAutomationContractReviewStatus.denied and validated.review_allowed:
        raise ValueError("DENIED_BROWSER_REVIEW_CANNOT_BE_ALLOWED")
    if validated.status != BrowserAutomationContractReviewStatus.denied and not validated.review_allowed:
        raise ValueError("BROWSER_REVIEW_ALLOWED_REQUIRED")
    _validate_browser_automation_contract_review_receipt_plan(validated.receipt_plan)
    return validated


def _validate_browser_automation_contract_review_receipt_plan(
    receipt_plan: BrowserAutomationContractReviewReceiptPlan,
) -> BrowserAutomationContractReviewReceiptPlan:
    validated = BrowserAutomationContractReviewReceiptPlan.model_validate(_model_payload(receipt_plan))
    for field_name, reason in _RECEIPT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _RECEIPT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("BROWSER_SIDE_EFFECTS_DENIED")
    return validated


_POLICY_REQUIRED_TRUE = [
    ("contract_only", "BROWSER_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "BROWSER_REVIEW_ONLY_REQUIRED"),
    ("disabled_by_default", "BROWSER_DISABLED_BY_DEFAULT_REQUIRED"),
    ("deterministic", "BROWSER_DETERMINISTIC_REQUIRED"),
    ("m74_candidate_only", "M74_CANDIDATE_ONLY_REQUIRED"),
]

_POLICY_DENIALS = [
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("browser_observe_enabled", "BROWSER_OBSERVE_DENIED"),
    ("browser_navigation_enabled", "BROWSER_NAVIGATION_DENIED"),
    ("browser_click_enabled", "BROWSER_CLICK_DENIED"),
    ("form_fill_enabled", "FORM_FILL_DENIED"),
    ("screenshot_enabled", "SCREENSHOT_DENIED"),
    ("dom_read_enabled", "DOM_READ_DENIED"),
    ("authenticated_profile_enabled", "AUTHENTICATED_PROFILE_DENIED"),
    ("download_or_upload_enabled", "DOWNLOAD_OR_UPLOAD_DENIED"),
    ("remote_browser_enabled", "REMOTE_BROWSER_DENIED"),
    ("network_interception_enabled", "NETWORK_INTERCEPTION_DENIED"),
    ("network_call_enabled", "NETWORK_CALL_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_REQUEST_REQUIRED_TRUE = [
    ("contract_only", "BROWSER_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "BROWSER_REVIEW_ONLY_REQUIRED"),
    ("disabled_by_default", "BROWSER_DISABLED_BY_DEFAULT_REQUIRED"),
    ("deterministic", "BROWSER_DETERMINISTIC_REQUIRED"),
    ("m74_candidate_only", "M74_CANDIDATE_ONLY_REQUIRED"),
]

_REQUEST_DENIALS = [
    ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
    ("browser_observe_requested", "BROWSER_OBSERVE_DENIED"),
    ("browser_navigation_requested", "BROWSER_NAVIGATION_DENIED"),
    ("browser_click_requested", "BROWSER_CLICK_DENIED"),
    ("form_fill_requested", "FORM_FILL_DENIED"),
    ("screenshot_requested", "SCREENSHOT_DENIED"),
    ("dom_read_requested", "DOM_READ_DENIED"),
    ("authenticated_profile_requested", "AUTHENTICATED_PROFILE_DENIED"),
    ("download_or_upload_requested", "DOWNLOAD_OR_UPLOAD_DENIED"),
    ("remote_browser_requested", "REMOTE_BROWSER_DENIED"),
    ("network_interception_requested", "NETWORK_INTERCEPTION_DENIED"),
    ("network_call_requested", "NETWORK_CALL_DENIED"),
    ("model_call_requested", "MODEL_CALL_DENIED"),
    ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
    ("memory_write_requested", "MEMORY_WRITE_DENIED"),
    ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
    ("contains_raw_dom", "RAW_DOM_DENIED"),
    ("contains_screenshot_bytes", "SCREENSHOT_BYTES_DENIED"),
    ("contains_browser_profile_path", "BROWSER_PROFILE_PATH_DENIED"),
    ("contains_cookies_or_credentials", "COOKIES_OR_CREDENTIALS_DENIED"),
]

_DECISION_REQUIRED_TRUE = [
    ("contract_only", "BROWSER_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "BROWSER_REVIEW_ONLY_REQUIRED"),
    ("disabled_by_default", "BROWSER_DISABLED_BY_DEFAULT_REQUIRED"),
    ("deterministic", "BROWSER_DETERMINISTIC_REQUIRED"),
    ("m74_candidate_only", "M74_CANDIDATE_ONLY_REQUIRED"),
    ("future_milestone_required", "FUTURE_BROWSER_MILESTONE_REQUIRED"),
]

_DECISION_DENIALS = [
    ("browser_automation_allowed", "BROWSER_AUTOMATION_DENIED"),
    ("browser_observe_allowed", "BROWSER_OBSERVE_DENIED"),
    ("browser_navigation_allowed", "BROWSER_NAVIGATION_DENIED"),
    ("browser_click_allowed", "BROWSER_CLICK_DENIED"),
    ("form_fill_allowed", "FORM_FILL_DENIED"),
    ("screenshot_allowed", "SCREENSHOT_DENIED"),
    ("dom_read_allowed", "DOM_READ_DENIED"),
    ("authenticated_profile_allowed", "AUTHENTICATED_PROFILE_DENIED"),
    ("download_or_upload_allowed", "DOWNLOAD_OR_UPLOAD_DENIED"),
    ("remote_browser_allowed", "REMOTE_BROWSER_DENIED"),
    ("network_interception_allowed", "NETWORK_INTERCEPTION_DENIED"),
    ("network_call_allowed", "NETWORK_CALL_DENIED"),
    ("model_call_allowed", "MODEL_CALL_DENIED"),
    ("tool_execution_allowed", "TOOL_EXECUTION_DENIED"),
    ("memory_write_allowed", "MEMORY_WRITE_DENIED"),
    ("context_injection_allowed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_allowed", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_allowed", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_allowed", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]

_RECEIPT_REQUIRED_TRUE = [
    ("contract_only", "BROWSER_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "BROWSER_REVIEW_ONLY_REQUIRED"),
]

_RECEIPT_DENIALS = [
    ("browser_automation_performed", "BROWSER_AUTOMATION_DENIED"),
    ("browser_observe_performed", "BROWSER_OBSERVE_DENIED"),
    ("browser_navigation_performed", "BROWSER_NAVIGATION_DENIED"),
    ("browser_click_performed", "BROWSER_CLICK_DENIED"),
    ("form_fill_performed", "FORM_FILL_DENIED"),
    ("screenshot_stored", "SCREENSHOT_DENIED"),
    ("raw_dom_stored", "RAW_DOM_DENIED"),
    ("authenticated_profile_used", "AUTHENTICATED_PROFILE_DENIED"),
    ("cookies_or_credentials_used", "COOKIES_OR_CREDENTIALS_DENIED"),
    ("network_call_performed", "NETWORK_CALL_DENIED"),
    ("tool_execution_performed", "TOOL_EXECUTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
]


def _model_payload(model: BaseModel) -> dict[str, Any]:
    payload = model.model_dump(mode="python", round_trip=True)
    extra = getattr(model, "__pydantic_extra__", None)
    if extra:
        payload.update(extra)
    return payload


def _has_secret_like_extra(payload: dict[str, Any], model_type: type[BaseModel]) -> bool:
    allowed = set(model_type.model_fields)
    for key, value in payload.items():
        if key in allowed:
            continue
        try:
            _validate_safe_payload({key: value})
        except ValueError:
            return True
    return False


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[-1].replace("/", "-")
