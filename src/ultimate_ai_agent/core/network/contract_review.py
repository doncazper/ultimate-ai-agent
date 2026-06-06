from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


NETWORK_TOOL_CONTRACT_REVIEW_DOCS = [
    "docs/network/NETWORK_TOOL_CONTRACT_REVIEW.md",
    "docs/network/NETWORK_TOOL_CONTRACT_REVIEW_POLICY.md",
    "docs/network/NETWORK_TOOL_CONTRACT_AUTHORITY_BOUNDARY.md",
    "docs/network/M71_TO_M72_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]


class NetworkToolCapabilityKind(str, Enum):
    allowlisted_read_only_http_fetch = "allowlisted_read_only_http_fetch"
    unrestricted_network_tool = "unrestricted_network_tool"
    authenticated_network_action = "authenticated_network_action"
    non_get_request = "non_get_request"
    request_body_upload = "request_body_upload"
    download_or_export = "download_or_export"
    browser_network_action = "browser_network_action"
    provider_model_call = "provider_model_call"
    webhook_or_callback = "webhook_or_callback"
    external_saas_sdk = "external_saas_sdk"
    unknown = "unknown"


class NetworkToolContractReviewStatus(str, Enum):
    review_ready = "review_ready"
    future_milestone = "future_milestone"
    denied = "denied"


class _NetworkToolContractReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class NetworkToolContractReviewPolicy(_NetworkToolContractReviewModel):
    policy_ref: str = "network-tool-contract-review-policy:m71"
    contract_only: bool = True
    review_only: bool = True
    disabled_by_default: bool = True
    deterministic: bool = True
    m72_candidate_only: bool = True
    network_call_enabled: bool = False
    http_fetch_enabled: bool = False
    unrestricted_network_enabled: bool = False
    authenticated_network_enabled: bool = False
    credentials_or_cookies_enabled: bool = False
    request_body_enabled: bool = False
    non_get_method_enabled: bool = False
    download_or_export_enabled: bool = False
    browser_automation_enabled: bool = False
    provider_model_call_enabled: bool = False
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


class NetworkToolContractReviewRequest(_NetworkToolContractReviewModel):
    review_ref: str
    candidate_ref: str
    actor_ref: str
    proposed_tool_ref: str
    safe_name: str
    capability_kind: NetworkToolCapabilityKind
    safe_summary: str
    allowed_host_policy_ref: str
    risk_ref: str
    approval_ref: str | None = None
    approval_test_ref: str | None = None
    contract_only: bool = True
    review_only: bool = True
    disabled_by_default: bool = True
    deterministic: bool = True
    m72_candidate_only: bool = True
    network_call_requested: bool = False
    http_fetch_requested: bool = False
    unrestricted_network_requested: bool = False
    authenticated_network_requested: bool = False
    credentials_or_cookies_requested: bool = False
    request_body_requested: bool = False
    non_get_method_requested: bool = False
    download_or_export_requested: bool = False
    browser_automation_requested: bool = False
    provider_model_call_requested: bool = False
    tool_execution_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    production_authority_requested: bool = False
    contains_raw_response_body: bool = False
    contains_raw_headers: bool = False
    contains_raw_url_with_query: bool = False
    contains_credentials_or_cookies: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.review_ref, "review_ref"),
            (self.candidate_ref, "candidate_ref"),
            (self.actor_ref, "actor_ref"),
            (self.proposed_tool_ref, "proposed_tool_ref"),
            (self.allowed_host_policy_ref, "allowed_host_policy_ref"),
            (self.risk_ref, "risk_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if self.approval_ref is not None:
            _validate_m61_ref(self.approval_ref, "approval_ref")
        if self.approval_test_ref is not None:
            if str(self.approval_test_ref).startswith("approval_test"):
                raise ValueError("APPROVAL_TEST_REF_DENIED")
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        _validate_safe_payload(self.safe_name)
        _validate_safe_payload(self.safe_summary)
        return self


class NetworkToolContractReviewReceiptPlan(_NetworkToolContractReviewModel):
    receipt_ref: str
    candidate_ref: str
    review_ref: str
    contract_only: bool = True
    review_only: bool = True
    network_call_performed: bool = False
    http_fetch_performed: bool = False
    tool_execution_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    raw_response_body_stored: bool = False
    raw_headers_stored: bool = False
    raw_url_with_query_stored: bool = False
    credentials_or_cookies_used: bool = False
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


class NetworkToolContractReviewDecision(_NetworkToolContractReviewModel):
    decision_ref: str
    review_ref: str
    candidate_ref: str
    proposed_tool_ref: str
    capability_kind: NetworkToolCapabilityKind
    status: NetworkToolContractReviewStatus
    review_allowed: bool
    contract_only: bool = True
    review_only: bool = True
    disabled_by_default: bool = True
    deterministic: bool = True
    m72_candidate_only: bool = True
    future_milestone_required: bool = True
    network_call_allowed: bool = False
    http_fetch_allowed: bool = False
    unrestricted_network_allowed: bool = False
    authenticated_network_allowed: bool = False
    credentials_or_cookies_allowed: bool = False
    request_body_allowed: bool = False
    non_get_method_allowed: bool = False
    download_or_export_allowed: bool = False
    browser_automation_allowed: bool = False
    provider_model_call_allowed: bool = False
    tool_execution_allowed: bool = False
    memory_write_allowed: bool = False
    context_injection_allowed: bool = False
    backend_route_allowed: bool = False
    control_center_control_allowed: bool = False
    dependency_change_allowed: bool = False
    production_authority_granted: bool = False
    receipt_plan: NetworkToolContractReviewReceiptPlan
    reason_codes: list[str]
    safe_summary: str

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.review_ref, "review_ref"),
            (self.candidate_ref, "candidate_ref"),
            (self.proposed_tool_ref, "proposed_tool_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def validate_network_tool_contract_review_policy(
    policy: NetworkToolContractReviewPolicy,
) -> NetworkToolContractReviewPolicy:
    payload = _model_payload(policy)
    for field_name, reason in _POLICY_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = NetworkToolContractReviewPolicy.model_validate(payload)
    for field_name, reason in _POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_NETWORK_TOOL_CONTENT_DENIED") from exc
    return validated


def validate_network_tool_contract_review_request(
    request: NetworkToolContractReviewRequest,
) -> NetworkToolContractReviewRequest:
    payload = _model_payload(request)
    for field_name, reason in _REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, NetworkToolContractReviewRequest):
        raise ValueError("SECRET_LIKE_NETWORK_TOOL_CONTENT_DENIED")
    validated = NetworkToolContractReviewRequest.model_validate(payload)
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
    if validated.side_effects_performed:
        raise ValueError("NETWORK_TOOL_SIDE_EFFECTS_DENIED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_NETWORK_TOOL_CONTENT_DENIED") from exc
    return validated


def build_network_tool_contract_review_decision(
    request: NetworkToolContractReviewRequest,
    policy: NetworkToolContractReviewPolicy | None = None,
) -> NetworkToolContractReviewDecision:
    active_policy = validate_network_tool_contract_review_policy(
        policy or NetworkToolContractReviewPolicy()
    )
    validated_request = validate_network_tool_contract_review_request(request)
    receipt_plan = NetworkToolContractReviewReceiptPlan(
        receipt_ref=f"network-tool-contract-review-receipt:{_ref_suffix(validated_request.candidate_ref)}",
        candidate_ref=validated_request.candidate_ref,
        review_ref=validated_request.review_ref,
    )
    if validated_request.capability_kind == NetworkToolCapabilityKind.unknown:
        return validate_network_tool_contract_review_decision(
            NetworkToolContractReviewDecision(
                decision_ref=f"network-tool-contract-review-decision:{_ref_suffix(validated_request.candidate_ref)}",
                review_ref=validated_request.review_ref,
                candidate_ref=validated_request.candidate_ref,
                proposed_tool_ref=validated_request.proposed_tool_ref,
                capability_kind=validated_request.capability_kind,
                status=NetworkToolContractReviewStatus.denied,
                review_allowed=False,
                receipt_plan=receipt_plan,
                reason_codes=[
                    "UNKNOWN_NETWORK_TOOL_CAPABILITY_DENIED",
                    "M71_NETWORK_TOOL_CONTRACT_REVIEW_ONLY",
                ],
                safe_summary="Unknown network tool capability is denied for M71 review.",
            )
        )
    if validated_request.capability_kind == NetworkToolCapabilityKind.allowlisted_read_only_http_fetch:
        reason_codes = [
            "M71_NETWORK_TOOL_CONTRACT_REVIEW_ONLY",
            "M71_NO_NETWORK_CALL_AUTHORITY",
            "M72_REMAINS_FUTURE",
        ]
        status = NetworkToolContractReviewStatus.review_ready
    else:
        reason_codes = [
            "M71_NETWORK_TOOL_CONTRACT_REVIEW_ONLY",
            "FUTURE_NETWORK_MILESTONE_REQUIRED",
        ]
        status = NetworkToolContractReviewStatus.future_milestone

    return validate_network_tool_contract_review_decision(
        NetworkToolContractReviewDecision(
            decision_ref=f"network-tool-contract-review-decision:{_ref_suffix(validated_request.candidate_ref)}",
            review_ref=validated_request.review_ref,
            candidate_ref=validated_request.candidate_ref,
            proposed_tool_ref=validated_request.proposed_tool_ref,
            capability_kind=validated_request.capability_kind,
            status=status,
            review_allowed=True,
            contract_only=active_policy.contract_only,
            review_only=active_policy.review_only,
            disabled_by_default=active_policy.disabled_by_default,
            deterministic=active_policy.deterministic,
            m72_candidate_only=active_policy.m72_candidate_only,
            future_milestone_required=True,
            receipt_plan=receipt_plan,
            reason_codes=reason_codes,
            safe_summary=(
                "M71 reviews network tool contracts only. It performs no network call, "
                "allows no HTTP fetch, stores no raw response, uses no auth material, "
                "adds no backend route or Control Center control, and keeps M72 future."
            ),
        )
    )


def validate_network_tool_contract_review_decision(
    decision: NetworkToolContractReviewDecision,
) -> NetworkToolContractReviewDecision:
    validated = NetworkToolContractReviewDecision.model_validate(_model_payload(decision))
    for field_name, reason in _DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status == NetworkToolContractReviewStatus.denied and validated.review_allowed:
        raise ValueError("DENIED_NETWORK_REVIEW_CANNOT_BE_ALLOWED")
    if validated.status != NetworkToolContractReviewStatus.denied and not validated.review_allowed:
        raise ValueError("NETWORK_REVIEW_ALLOWED_REQUIRED")
    _validate_network_tool_contract_review_receipt_plan(validated.receipt_plan)
    return validated


def _validate_network_tool_contract_review_receipt_plan(
    receipt_plan: NetworkToolContractReviewReceiptPlan,
) -> NetworkToolContractReviewReceiptPlan:
    validated = NetworkToolContractReviewReceiptPlan.model_validate(_model_payload(receipt_plan))
    for field_name, reason in _RECEIPT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _RECEIPT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("NETWORK_TOOL_SIDE_EFFECTS_DENIED")
    return validated


_POLICY_REQUIRED_TRUE = [
    ("contract_only", "NETWORK_TOOL_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "NETWORK_TOOL_REVIEW_ONLY_REQUIRED"),
    ("disabled_by_default", "NETWORK_TOOL_DISABLED_BY_DEFAULT_REQUIRED"),
    ("deterministic", "NETWORK_TOOL_DETERMINISTIC_REQUIRED"),
    ("m72_candidate_only", "M72_CANDIDATE_ONLY_REQUIRED"),
]

_POLICY_DENIALS = [
    ("network_call_enabled", "NETWORK_CALL_DENIED"),
    ("http_fetch_enabled", "HTTP_FETCH_DENIED"),
    ("unrestricted_network_enabled", "UNRESTRICTED_NETWORK_DENIED"),
    ("authenticated_network_enabled", "AUTHENTICATED_NETWORK_DENIED"),
    ("credentials_or_cookies_enabled", "CREDENTIAL_OR_COOKIE_HANDLING_DENIED"),
    ("request_body_enabled", "REQUEST_BODY_DENIED"),
    ("non_get_method_enabled", "NON_GET_METHOD_DENIED"),
    ("download_or_export_enabled", "DOWNLOAD_OR_EXPORT_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("provider_model_call_enabled", "PROVIDER_MODEL_CALL_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_REQUEST_REQUIRED_TRUE = [
    ("contract_only", "NETWORK_TOOL_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "NETWORK_TOOL_REVIEW_ONLY_REQUIRED"),
    ("disabled_by_default", "NETWORK_TOOL_DISABLED_BY_DEFAULT_REQUIRED"),
    ("deterministic", "NETWORK_TOOL_DETERMINISTIC_REQUIRED"),
    ("m72_candidate_only", "M72_CANDIDATE_ONLY_REQUIRED"),
]

_REQUEST_DENIALS = [
    ("network_call_requested", "NETWORK_CALL_DENIED"),
    ("http_fetch_requested", "HTTP_FETCH_DENIED"),
    ("unrestricted_network_requested", "UNRESTRICTED_NETWORK_DENIED"),
    ("authenticated_network_requested", "AUTHENTICATED_NETWORK_DENIED"),
    ("credentials_or_cookies_requested", "CREDENTIAL_OR_COOKIE_HANDLING_DENIED"),
    ("request_body_requested", "REQUEST_BODY_DENIED"),
    ("non_get_method_requested", "NON_GET_METHOD_DENIED"),
    ("download_or_export_requested", "DOWNLOAD_OR_EXPORT_DENIED"),
    ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
    ("provider_model_call_requested", "PROVIDER_MODEL_CALL_DENIED"),
    ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
    ("memory_write_requested", "MEMORY_WRITE_DENIED"),
    ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
    ("contains_raw_response_body", "RAW_RESPONSE_BODY_DENIED"),
    ("contains_raw_headers", "RAW_HEADERS_DENIED"),
    ("contains_raw_url_with_query", "RAW_URL_WITH_QUERY_DENIED"),
    ("contains_credentials_or_cookies", "CREDENTIAL_OR_COOKIE_HANDLING_DENIED"),
]

_DECISION_REQUIRED_TRUE = [
    ("contract_only", "NETWORK_TOOL_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "NETWORK_TOOL_REVIEW_ONLY_REQUIRED"),
    ("disabled_by_default", "NETWORK_TOOL_DISABLED_BY_DEFAULT_REQUIRED"),
    ("deterministic", "NETWORK_TOOL_DETERMINISTIC_REQUIRED"),
    ("m72_candidate_only", "M72_CANDIDATE_ONLY_REQUIRED"),
    ("future_milestone_required", "FUTURE_NETWORK_MILESTONE_REQUIRED"),
]

_DECISION_DENIALS = [
    ("network_call_allowed", "NETWORK_CALL_DENIED"),
    ("http_fetch_allowed", "HTTP_FETCH_DENIED"),
    ("unrestricted_network_allowed", "UNRESTRICTED_NETWORK_DENIED"),
    ("authenticated_network_allowed", "AUTHENTICATED_NETWORK_DENIED"),
    ("credentials_or_cookies_allowed", "CREDENTIAL_OR_COOKIE_HANDLING_DENIED"),
    ("request_body_allowed", "REQUEST_BODY_DENIED"),
    ("non_get_method_allowed", "NON_GET_METHOD_DENIED"),
    ("download_or_export_allowed", "DOWNLOAD_OR_EXPORT_DENIED"),
    ("browser_automation_allowed", "BROWSER_AUTOMATION_DENIED"),
    ("provider_model_call_allowed", "PROVIDER_MODEL_CALL_DENIED"),
    ("tool_execution_allowed", "TOOL_EXECUTION_DENIED"),
    ("memory_write_allowed", "MEMORY_WRITE_DENIED"),
    ("context_injection_allowed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_allowed", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_allowed", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_allowed", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]

_RECEIPT_REQUIRED_TRUE = [
    ("contract_only", "NETWORK_TOOL_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "NETWORK_TOOL_REVIEW_ONLY_REQUIRED"),
]

_RECEIPT_DENIALS = [
    ("network_call_performed", "NETWORK_CALL_DENIED"),
    ("http_fetch_performed", "HTTP_FETCH_DENIED"),
    ("tool_execution_performed", "TOOL_EXECUTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("raw_response_body_stored", "RAW_RESPONSE_BODY_DENIED"),
    ("raw_headers_stored", "RAW_HEADERS_DENIED"),
    ("raw_url_with_query_stored", "RAW_URL_WITH_QUERY_DENIED"),
    ("credentials_or_cookies_used", "CREDENTIAL_OR_COOKIE_HANDLING_DENIED"),
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
