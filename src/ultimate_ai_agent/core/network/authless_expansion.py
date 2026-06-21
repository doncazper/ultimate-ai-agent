from enum import Enum
import ipaddress
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


AUTHLESS_NETWORK_EXPANSION_DOCS = [
    "docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION.md",
    "docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_POLICY.md",
    "docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_AUTHORITY_BOUNDARY.md",
    "docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_RECEIPT_PLAN.md",
    "docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_NON_GOALS.md",
    "docs/network/M95_TO_M96_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]

M95_SECRET_LIKE_RE = re.compile(
    r"(api[_-]?key|authorization|bearer|cookie|password|secret|token|client[_-]?secret|oauth)",
    re.IGNORECASE,
)


class AuthlessNetworkExpansionStatus(str, Enum):
    authless_read_only_allowed = "authless_read_only_allowed"
    denied = "denied"


class _AuthlessNetworkExpansionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AuthlessNetworkExpansionPolicy(_AuthlessNetworkExpansionModel):
    policy_ref: str = "network-authless-expansion-policy:m95"
    capability_exists: bool = True
    disabled_by_default: bool = True
    authless_read_only_allowed: bool = True
    allowlist_required: bool = True
    https_only: bool = True
    get_only: bool = True
    redirect_controls_required: bool = True
    bounded_output_required: bool = True
    redaction_required: bool = True
    exact_scope_required: bool = True
    audit_required: bool = True
    revocation_required: bool = True
    transport_injection_required: bool = True
    unrestricted_network_allowed: bool = False
    authenticated_network_allowed: bool = False
    credential_headers_allowed: bool = False
    cookies_allowed: bool = False
    request_body_allowed: bool = False
    mutation_method_allowed: bool = False
    private_network_allowed: bool = False
    account_action_allowed: bool = False
    download_or_export_allowed: bool = False
    browser_form_allowed: bool = False
    provider_model_call_allowed: bool = False
    shell_execution_allowed: bool = False
    plugin_execution_allowed: bool = False
    memory_write_allowed: bool = False
    context_injection_allowed: bool = False
    backend_route_allowed: bool = False
    control_center_control_allowed: bool = False
    dependency_change_allowed: bool = False
    production_authority_allowed: bool = False
    max_response_bytes: int = Field(default=65536, ge=1, le=65536)
    max_preview_bytes: int = Field(default=4096, ge=1, le=4096)
    max_redirects: int = Field(default=1, ge=0, le=1)
    allowed_hosts: tuple[str, ...]
    allowed_redirect_hosts: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class AuthlessNetworkExpansionRequest(_AuthlessNetworkExpansionModel):
    request_ref: str
    actor_ref: str
    scoped_session_ref: str
    scope_ref: str
    network_tool_ref: str
    m72_fetch_tool_ref: str
    allowed_host_policy_ref: str
    target_host: str
    target_path: str = "/"
    method: str = "GET"
    exact_scope_approval_ref: str
    audit_ref: str
    revocation_ref: str
    safe_summary: str
    approval_ref: str | None = None
    approval_test_ref: str | None = None
    authority_refs: list[str] = Field(default_factory=list)
    redirect_target_host: str | None = None
    redirect_count: int = Field(default=0, ge=0)
    request_headers: dict[str, str] = Field(default_factory=dict)
    request_body: str | None = None
    query_string_present: bool = False
    raw_response_requested: bool = False
    raw_headers_requested: bool = False
    unrestricted_network_requested: bool = False
    authenticated_network_requested: bool = False
    credentials_or_cookies_requested: bool = False
    credential_headers_requested: bool = False
    mutation_method_requested: bool = False
    private_network_requested: bool = False
    account_action_requested: bool = False
    download_or_export_requested: bool = False
    browser_form_requested: bool = False
    provider_model_call_requested: bool = False
    shell_execution_requested: bool = False
    plugin_execution_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    production_authority_requested: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.actor_ref, "actor_ref"),
            (self.scoped_session_ref, "scoped_session_ref"),
            (self.scope_ref, "scope_ref"),
            (self.network_tool_ref, "network_tool_ref"),
            (self.m72_fetch_tool_ref, "m72_fetch_tool_ref"),
            (self.allowed_host_policy_ref, "allowed_host_policy_ref"),
            (self.exact_scope_approval_ref, "exact_scope_approval_ref"),
            (self.audit_ref, "audit_ref"),
            (self.revocation_ref, "revocation_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if self.approval_ref is not None:
            _validate_m61_ref(self.approval_ref, "approval_ref")
        if self.approval_test_ref is not None:
            if self.approval_test_ref.startswith("approval_test"):
                raise ValueError("APPROVAL_TEST_REF_DENIED")
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        for ref in self.authority_refs:
            _validate_m61_ref(ref, "authority_ref")
        _validate_safe_payload(self.safe_summary)
        return self


class AuthlessNetworkExpansionReceiptPlan(_AuthlessNetworkExpansionModel):
    receipt_ref: str
    request_ref: str
    scoped_session_ref: str
    scope_ref: str
    target_host_ref: str
    target_path_ref: str
    store_safe_refs_only: bool = True
    store_redacted_preview_only: bool = True
    raw_response_stored: bool = False
    raw_headers_stored: bool = False
    credential_headers_stored: bool = False
    cookies_stored: bool = False
    query_string_stored: bool = False
    account_action_stored: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.receipt_ref, "receipt_ref"),
            (self.request_ref, "request_ref"),
            (self.scoped_session_ref, "scoped_session_ref"),
            (self.scope_ref, "scope_ref"),
            (self.target_host_ref, "target_host_ref"),
            (self.target_path_ref, "target_path_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        return self


class AuthlessNetworkExpansionDecision(_AuthlessNetworkExpansionModel):
    decision_ref: str
    request_ref: str
    actor_ref: str
    scoped_session_ref: str
    scope_ref: str
    network_tool_ref: str
    m72_fetch_tool_ref: str
    allowed_host_policy_ref: str
    target_host_ref: str
    target_path_ref: str
    status: AuthlessNetworkExpansionStatus
    authless_read_only_allowed: bool
    capability_exists: bool = True
    disabled_by_default: bool = True
    exact_scope_bound: bool = True
    exact_approval_bound: bool = True
    allowlisted_domain_bound: bool = True
    redirect_policy_bound: bool = True
    bounded_output_bound: bool = True
    redaction_bound: bool = True
    audit_bound: bool = True
    revocation_bound: bool = True
    transport_injection_required: bool = True
    network_call_performed: bool = False
    unrestricted_network_allowed: bool = False
    authenticated_network_allowed: bool = False
    credential_headers_allowed: bool = False
    cookies_allowed: bool = False
    request_body_allowed: bool = False
    mutation_method_allowed: bool = False
    private_network_allowed: bool = False
    account_action_allowed: bool = False
    download_or_export_allowed: bool = False
    browser_form_allowed: bool = False
    provider_model_call_allowed: bool = False
    shell_execution_allowed: bool = False
    plugin_execution_allowed: bool = False
    memory_write_allowed: bool = False
    context_injection_allowed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    receipt_plan: AuthlessNetworkExpansionReceiptPlan
    reason_codes: list[str]
    safe_summary: str

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.request_ref, "request_ref"),
            (self.actor_ref, "actor_ref"),
            (self.scoped_session_ref, "scoped_session_ref"),
            (self.scope_ref, "scope_ref"),
            (self.network_tool_ref, "network_tool_ref"),
            (self.m72_fetch_tool_ref, "m72_fetch_tool_ref"),
            (self.allowed_host_policy_ref, "allowed_host_policy_ref"),
            (self.target_host_ref, "target_host_ref"),
            (self.target_path_ref, "target_path_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def validate_authless_network_expansion_policy(
    policy: AuthlessNetworkExpansionPolicy,
) -> AuthlessNetworkExpansionPolicy:
    payload = _model_payload(policy)
    for field_name, reason in _POLICY_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = AuthlessNetworkExpansionPolicy.model_validate(payload)
    for field_name, reason in _POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.max_preview_bytes > validated.max_response_bytes:
        raise ValueError("NETWORK_PREVIEW_LIMIT_EXCEEDS_RESPONSE_LIMIT")
    allowed_hosts = tuple(_normalize_public_host(host) for host in validated.allowed_hosts)
    redirect_hosts = tuple(_normalize_public_host(host) for host in validated.allowed_redirect_hosts)
    if len(set(allowed_hosts)) != len(allowed_hosts):
        raise ValueError("NETWORK_ALLOWLIST_DUPLICATE_DENIED")
    if not set(redirect_hosts).issubset(set(allowed_hosts)):
        raise ValueError("REDIRECT_HOST_NOT_ALLOWLISTED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_NETWORK_METADATA_DENIED") from exc
    object.__setattr__(validated, "allowed_hosts", allowed_hosts)
    object.__setattr__(validated, "allowed_redirect_hosts", redirect_hosts)
    return validated


def validate_authless_network_expansion_request(
    request: AuthlessNetworkExpansionRequest,
    policy: AuthlessNetworkExpansionPolicy,
) -> AuthlessNetworkExpansionRequest:
    payload = _model_payload(request)
    for field_name, reason in _REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, AuthlessNetworkExpansionRequest):
        raise ValueError("SECRET_LIKE_NETWORK_METADATA_DENIED")
    validated = AuthlessNetworkExpansionRequest.model_validate(payload)
    if validated.method.upper() != "GET":
        raise ValueError("NON_GET_METHOD_DENIED")
    if validated.request_headers:
        raise ValueError("CREDENTIAL_HEADERS_DENIED")
    if validated.request_body is not None:
        raise ValueError("REQUEST_BODY_DENIED")
    target_host = _normalize_public_host(validated.target_host)
    if target_host not in set(policy.allowed_hosts):
        raise ValueError("HOST_NOT_ALLOWLISTED_DENIED")
    _validate_safe_path(validated.target_path)
    if validated.redirect_count > policy.max_redirects:
        raise ValueError("REDIRECT_LIMIT_DENIED")
    if validated.redirect_target_host:
        redirect_host = _normalize_public_host(validated.redirect_target_host)
        if redirect_host not in set(policy.allowed_redirect_hosts or policy.allowed_hosts):
            raise ValueError("REDIRECT_HOST_NOT_ALLOWLISTED")
    if validated.approval_ref:
        raise ValueError("APPROVAL_REF_NOT_AUTHORITY")
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    for ref in validated.authority_refs:
        if ref.startswith("approval_test"):
            raise ValueError("APPROVAL_TEST_REF_DENIED")
        if ref.split(":", 1)[0] in {
            "approval",
            "context-pack",
            "memory",
            "model",
            "openwebui",
            "tool-intent",
            "task-plan",
            "runtime",
        }:
            raise ValueError("AUTHORITY_REF_NOT_NETWORK_AUTHORITY")
    if validated.side_effects_performed:
        raise ValueError("NETWORK_SIDE_EFFECTS_DENIED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_NETWORK_METADATA_DENIED") from exc
    return validated


def build_authless_network_expansion_decision(
    request: AuthlessNetworkExpansionRequest,
    policy: AuthlessNetworkExpansionPolicy | None = None,
) -> AuthlessNetworkExpansionDecision:
    if policy is None:
        raise ValueError("ALLOWLIST_POLICY_REQUIRED")
    active_policy = validate_authless_network_expansion_policy(
        policy
    )
    validated_request = validate_authless_network_expansion_request(request, active_policy)
    host = _normalize_public_host(validated_request.target_host)
    path_ref = _safe_path_ref(validated_request.target_path)
    receipt = AuthlessNetworkExpansionReceiptPlan(
        receipt_ref=f"network-authless-expansion-receipt:{_ref_suffix(validated_request.request_ref)}",
        request_ref=validated_request.request_ref,
        scoped_session_ref=validated_request.scoped_session_ref,
        scope_ref=validated_request.scope_ref,
        target_host_ref=f"network-host:{host.replace('.', '-')}",
        target_path_ref=path_ref,
    )
    return validate_authless_network_expansion_decision(
        AuthlessNetworkExpansionDecision(
            decision_ref=f"network-authless-expansion-decision:{_ref_suffix(validated_request.request_ref)}",
            request_ref=validated_request.request_ref,
            actor_ref=validated_request.actor_ref,
            scoped_session_ref=validated_request.scoped_session_ref,
            scope_ref=validated_request.scope_ref,
            network_tool_ref=validated_request.network_tool_ref,
            m72_fetch_tool_ref=validated_request.m72_fetch_tool_ref,
            allowed_host_policy_ref=validated_request.allowed_host_policy_ref,
            target_host_ref=f"network-host:{host.replace('.', '-')}",
            target_path_ref=path_ref,
            status=AuthlessNetworkExpansionStatus.authless_read_only_allowed,
            authless_read_only_allowed=True,
            receipt_plan=receipt,
            reason_codes=[
                "M95_AUTHLESS_READ_ONLY_NETWORK_EXPANSION_ALLOWED",
                "ALLOWLISTED_DOMAIN_BOUND",
                "NO_AUTH_MATERIAL",
                "GET_ONLY",
                "REDIRECT_POLICY_BOUND",
                "BOUNDED_REDACTED_OUTPUT_REQUIRED",
                "M96_REMAINS_FUTURE",
            ],
            safe_summary=(
                "M95 allows only exact-scope authless read-only network expansion proposals over "
                "allowlisted HTTPS GET targets with redirect controls, bounded redacted output, "
                "audit, revocation, and no auth material, mutations, routes, or production authority."
            ),
        )
    )


def validate_authless_network_expansion_decision(
    decision: AuthlessNetworkExpansionDecision,
) -> AuthlessNetworkExpansionDecision:
    validated = AuthlessNetworkExpansionDecision.model_validate(_model_payload(decision))
    for field_name, reason in _DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_authless_network_expansion_receipt_plan(validated.receipt_plan)
    return validated


def _validate_authless_network_expansion_receipt_plan(
    receipt_plan: AuthlessNetworkExpansionReceiptPlan,
) -> AuthlessNetworkExpansionReceiptPlan:
    validated = AuthlessNetworkExpansionReceiptPlan.model_validate(_model_payload(receipt_plan))
    if not validated.store_safe_refs_only:
        raise ValueError("SAFE_REFS_ONLY_REQUIRED")
    if not validated.store_redacted_preview_only:
        raise ValueError("REDACTED_PREVIEW_ONLY_REQUIRED")
    for field_name, reason in _RECEIPT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("NETWORK_SIDE_EFFECTS_DENIED")
    return validated


_POLICY_REQUIRED_TRUE = [
    ("capability_exists", "CAPABILITY_EXISTS_REQUIRED"),
    ("disabled_by_default", "DISABLED_BY_DEFAULT_REQUIRED"),
    ("authless_read_only_allowed", "AUTHLESS_READ_ONLY_REQUIRED"),
    ("allowlist_required", "ALLOWLIST_REQUIRED"),
    ("https_only", "HTTPS_ONLY_REQUIRED"),
    ("get_only", "GET_ONLY_REQUIRED"),
    ("redirect_controls_required", "REDIRECT_CONTROLS_REQUIRED"),
    ("bounded_output_required", "BOUNDED_OUTPUT_REQUIRED"),
    ("redaction_required", "REDACTION_REQUIRED"),
    ("exact_scope_required", "EXACT_SCOPE_REQUIRED"),
    ("audit_required", "AUDIT_REQUIRED"),
    ("revocation_required", "REVOCATION_REQUIRED"),
    ("transport_injection_required", "TRANSPORT_INJECTION_REQUIRED"),
]

_POLICY_DENIALS = [
    ("unrestricted_network_allowed", "UNRESTRICTED_NETWORK_DENIED"),
    ("authenticated_network_allowed", "AUTHENTICATED_NETWORK_DENIED"),
    ("credential_headers_allowed", "CREDENTIAL_HEADERS_DENIED"),
    ("cookies_allowed", "COOKIES_DENIED"),
    ("request_body_allowed", "REQUEST_BODY_DENIED"),
    ("mutation_method_allowed", "MUTATION_METHOD_DENIED"),
    ("private_network_allowed", "PRIVATE_NETWORK_DENIED"),
    ("account_action_allowed", "ACCOUNT_ACTION_DENIED"),
    ("download_or_export_allowed", "DOWNLOAD_OR_EXPORT_DENIED"),
    ("browser_form_allowed", "BROWSER_FORM_DENIED"),
    ("provider_model_call_allowed", "PROVIDER_MODEL_CALL_DENIED"),
    ("shell_execution_allowed", "SHELL_EXECUTION_DENIED"),
    ("plugin_execution_allowed", "PLUGIN_EXECUTION_DENIED"),
    ("memory_write_allowed", "MEMORY_WRITE_DENIED"),
    ("context_injection_allowed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_allowed", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_allowed", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_allowed", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_allowed", "PRODUCTION_AUTHORITY_DENIED"),
]

_REQUEST_DENIALS = [
    ("query_string_present", "QUERY_STRING_DENIED"),
    ("raw_response_requested", "RAW_RESPONSE_DENIED"),
    ("raw_headers_requested", "RAW_HEADERS_DENIED"),
    ("unrestricted_network_requested", "UNRESTRICTED_NETWORK_DENIED"),
    ("authenticated_network_requested", "AUTHENTICATED_NETWORK_DENIED"),
    ("credentials_or_cookies_requested", "CREDENTIAL_OR_COOKIE_DENIED"),
    ("credential_headers_requested", "CREDENTIAL_HEADERS_DENIED"),
    ("mutation_method_requested", "MUTATION_METHOD_DENIED"),
    ("private_network_requested", "PRIVATE_NETWORK_DENIED"),
    ("account_action_requested", "ACCOUNT_ACTION_DENIED"),
    ("download_or_export_requested", "DOWNLOAD_OR_EXPORT_DENIED"),
    ("browser_form_requested", "BROWSER_FORM_DENIED"),
    ("provider_model_call_requested", "PROVIDER_MODEL_CALL_DENIED"),
    ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
    ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
    ("memory_write_requested", "MEMORY_WRITE_DENIED"),
    ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
]

_DECISION_REQUIRED_TRUE = [
    ("capability_exists", "CAPABILITY_EXISTS_REQUIRED"),
    ("disabled_by_default", "DISABLED_BY_DEFAULT_REQUIRED"),
    ("authless_read_only_allowed", "AUTHLESS_READ_ONLY_REQUIRED"),
    ("exact_scope_bound", "EXACT_SCOPE_REQUIRED"),
    ("exact_approval_bound", "EXACT_APPROVAL_REQUIRED"),
    ("allowlisted_domain_bound", "ALLOWLIST_REQUIRED"),
    ("redirect_policy_bound", "REDIRECT_CONTROLS_REQUIRED"),
    ("bounded_output_bound", "BOUNDED_OUTPUT_REQUIRED"),
    ("redaction_bound", "REDACTION_REQUIRED"),
    ("audit_bound", "AUDIT_REQUIRED"),
    ("revocation_bound", "REVOCATION_REQUIRED"),
    ("transport_injection_required", "TRANSPORT_INJECTION_REQUIRED"),
]

_DECISION_DENIALS = [
    ("network_call_performed", "NETWORK_CALL_PERFORMED_DENIED_IN_DECISION"),
    ("unrestricted_network_allowed", "UNRESTRICTED_NETWORK_DENIED"),
    ("authenticated_network_allowed", "AUTHENTICATED_NETWORK_DENIED"),
    ("credential_headers_allowed", "CREDENTIAL_HEADERS_DENIED"),
    ("cookies_allowed", "COOKIES_DENIED"),
    ("request_body_allowed", "REQUEST_BODY_DENIED"),
    ("mutation_method_allowed", "MUTATION_METHOD_DENIED"),
    ("private_network_allowed", "PRIVATE_NETWORK_DENIED"),
    ("account_action_allowed", "ACCOUNT_ACTION_DENIED"),
    ("download_or_export_allowed", "DOWNLOAD_OR_EXPORT_DENIED"),
    ("browser_form_allowed", "BROWSER_FORM_DENIED"),
    ("provider_model_call_allowed", "PROVIDER_MODEL_CALL_DENIED"),
    ("shell_execution_allowed", "SHELL_EXECUTION_DENIED"),
    ("plugin_execution_allowed", "PLUGIN_EXECUTION_DENIED"),
    ("memory_write_allowed", "MEMORY_WRITE_DENIED"),
    ("context_injection_allowed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]

_RECEIPT_DENIALS = [
    ("raw_response_stored", "RAW_RESPONSE_DENIED"),
    ("raw_headers_stored", "RAW_HEADERS_DENIED"),
    ("credential_headers_stored", "CREDENTIAL_HEADERS_DENIED"),
    ("cookies_stored", "COOKIES_DENIED"),
    ("query_string_stored", "QUERY_STRING_DENIED"),
    ("account_action_stored", "ACCOUNT_ACTION_DENIED"),
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


def _normalize_public_host(value: str) -> str:
    host = value.strip().lower().rstrip(".")
    if not host or "/" in host or ":" in host or "@" in host or "*" in host:
        raise ValueError("HOST_INVALID")
    if M95_SECRET_LIKE_RE.search(host):
        raise ValueError("SECRET_LIKE_HOST_DENIED")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None or host in {"localhost"} or host.endswith(".local"):
        raise ValueError("PRIVATE_NETWORK_DENIED")
    _validate_safe_payload(host)
    return host


def _validate_safe_path(path: str) -> None:
    if not path.startswith("/"):
        raise ValueError("TARGET_PATH_INVALID")
    if ".." in path.split("/"):
        raise ValueError("PATH_TRAVERSAL_DENIED")
    if "?" in path or "#" in path:
        raise ValueError("QUERY_STRING_DENIED")
    if M95_SECRET_LIKE_RE.search(path):
        raise ValueError("SECRET_LIKE_PATH_DENIED")
    _validate_safe_payload(path)


def _safe_path_ref(path: str) -> str:
    safe = path.strip("/").replace("/", "-") or "root"
    safe = re.sub(r"[^a-zA-Z0-9_.-]", "-", safe)[:80]
    return f"network-path:{safe}"


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[-1].replace("/", "-")
