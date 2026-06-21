from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


NETWORK_BROWSER_OPENWEBUI_FREEZE_DOCS = [
    "docs/hardening/NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE.md",
    "docs/hardening/NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE_CONTRACTS.md",
    "docs/hardening/NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE_NON_GOALS.md",
    "docs/hardening/M80_TO_M81_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_M80_ACCEPTED_MILESTONE_REFS = tuple(
    f"milestone:M{index}" for index in range(71, 80)
)


class NetworkBrowserOpenWebUIFreezeStatus(str, Enum):
    frozen = "frozen"


class _NetworkBrowserOpenWebUIFreezeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class NetworkBrowserOpenWebUIFreezePolicy(_NetworkBrowserOpenWebUIFreezeModel):
    policy_ref: str = "network-browser-openwebui-freeze-policy:m80"
    freeze_only: bool = True
    review_only: bool = True
    network_browser_openwebui_only: bool = True
    deterministic: bool = True
    network_tool_expansion_enabled: bool = False
    unrestricted_network_enabled: bool = False
    authenticated_network_action_enabled: bool = False
    raw_network_response_enabled: bool = False
    browser_navigation_enabled: bool = False
    browser_click_enabled: bool = False
    browser_action_execution_enabled: bool = False
    browser_screenshot_enabled: bool = False
    raw_dom_enabled: bool = False
    authenticated_browser_profile_enabled: bool = False
    openwebui_model_authority_enabled: bool = False
    openwebui_tool_execution_enabled: bool = False
    openwebui_memory_write_enabled: bool = False
    openwebui_context_injection_enabled: bool = False
    raw_prompt_exposure_enabled: bool = False
    raw_provider_payload_exposure_enabled: bool = False
    plugin_install_enabled: bool = False
    plugin_enablement_enabled: bool = False
    plugin_execution_enabled: bool = False
    plugin_runtime_import_enabled: bool = False
    shell_execution_enabled: bool = False
    background_worker_enabled: bool = False
    remote_execution_enabled: bool = False
    credential_cookie_access_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_change_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class NetworkBrowserOpenWebUIFreezeRequest(_NetworkBrowserOpenWebUIFreezeModel):
    request_ref: str
    freeze_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_milestone_refs: list[str]
    checklist_refs: list[str]
    safe_summary: str
    freeze_only: bool = True
    review_only: bool = True
    network_browser_openwebui_only: bool = True
    deterministic: bool = True
    network_tool_expansion_requested: bool = False
    unrestricted_network_requested: bool = False
    authenticated_network_action_requested: bool = False
    raw_network_response_requested: bool = False
    browser_navigation_requested: bool = False
    browser_click_requested: bool = False
    browser_action_execution_requested: bool = False
    browser_screenshot_requested: bool = False
    raw_dom_requested: bool = False
    authenticated_browser_profile_requested: bool = False
    openwebui_model_authority_requested: bool = False
    openwebui_tool_execution_requested: bool = False
    openwebui_memory_write_requested: bool = False
    openwebui_context_injection_requested: bool = False
    raw_prompt_exposure_requested: bool = False
    raw_provider_payload_exposure_requested: bool = False
    plugin_install_requested: bool = False
    plugin_enablement_requested: bool = False
    plugin_execution_requested: bool = False
    plugin_runtime_import_requested: bool = False
    shell_execution_requested: bool = False
    background_worker_requested: bool = False
    remote_execution_requested: bool = False
    credential_cookie_access_requested: bool = False
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
            (self.freeze_ref, "freeze_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class NetworkBrowserOpenWebUIFreezeReport(_NetworkBrowserOpenWebUIFreezeModel):
    report_ref: str
    freeze_ref: str
    request_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_milestone_refs: list[str]
    checklist_refs: list[str]
    status: NetworkBrowserOpenWebUIFreezeStatus = NetworkBrowserOpenWebUIFreezeStatus.frozen
    freeze_only: bool = True
    review_only: bool = True
    network_browser_openwebui_only: bool = True
    deterministic: bool = True
    network_tool_expansion_performed: bool = False
    unrestricted_network_performed: bool = False
    authenticated_network_action_performed: bool = False
    raw_network_response_returned: bool = False
    browser_navigation_performed: bool = False
    browser_click_performed: bool = False
    browser_action_performed: bool = False
    browser_screenshot_performed: bool = False
    raw_dom_returned: bool = False
    authenticated_browser_profile_accessed: bool = False
    openwebui_model_authority_granted: bool = False
    openwebui_tool_execution_performed: bool = False
    openwebui_memory_write_performed: bool = False
    openwebui_context_injection_performed: bool = False
    raw_prompt_exposed: bool = False
    raw_provider_payload_exposed: bool = False
    plugin_install_performed: bool = False
    plugin_enablement_performed: bool = False
    plugin_execution_performed: bool = False
    plugin_runtime_import_performed: bool = False
    shell_execution_performed: bool = False
    background_worker_started: bool = False
    remote_execution_performed: bool = False
    credential_cookie_access_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.report_ref, "report_ref"),
            (self.freeze_ref, "freeze_ref"),
            (self.request_ref, "request_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        return self


def build_network_browser_openwebui_freeze_report(
    request: NetworkBrowserOpenWebUIFreezeRequest,
    policy: NetworkBrowserOpenWebUIFreezePolicy | None = None,
) -> NetworkBrowserOpenWebUIFreezeReport:
    active_policy = validate_network_browser_openwebui_freeze_policy(
        policy or NetworkBrowserOpenWebUIFreezePolicy()
    )
    validated_request = validate_network_browser_openwebui_freeze_request(request)
    report = NetworkBrowserOpenWebUIFreezeReport(
        report_ref=f"network-browser-openwebui-freeze-report:{_ref_suffix(validated_request.freeze_ref)}",
        freeze_ref=validated_request.freeze_ref,
        request_ref=validated_request.request_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        accepted_milestone_refs=list(validated_request.accepted_milestone_refs),
        checklist_refs=list(validated_request.checklist_refs),
        freeze_only=active_policy.freeze_only,
        review_only=active_policy.review_only,
        network_browser_openwebui_only=active_policy.network_browser_openwebui_only,
        deterministic=active_policy.deterministic,
        side_effects_performed=[],
        reason_codes=[
            "M80_NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE_REVIEW_ONLY",
            "M80_NO_NEW_RUNTIME_AUTHORITY",
            "M81_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M80 freezes the accepted M71-M79 network, browser, OpenWebUI, and plugin "
            "review boundaries. It adds no unrestricted network access, authenticated "
            "network action, raw network response, browser navigation or click, browser "
            "screenshot, raw DOM, authenticated browser profile access, OpenWebUI model "
            "authority, OpenWebUI tool execution, OpenWebUI memory write, OpenWebUI "
            "context injection, raw prompt exposure, raw provider payload exposure, "
            "plugin install, plugin enablement, plugin execution, plugin runtime import, "
            "shell execution, background worker, backend route, Control Center control, "
            "dependency, M81 work, or production authority."
        ),
    )
    return validate_network_browser_openwebui_freeze_report(report)


def validate_network_browser_openwebui_freeze_policy(
    policy: NetworkBrowserOpenWebUIFreezePolicy,
) -> NetworkBrowserOpenWebUIFreezePolicy:
    validated = NetworkBrowserOpenWebUIFreezePolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M80_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M80_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M80_FREEZE_CONTENT_DENIED") from exc
    return validated


def validate_network_browser_openwebui_freeze_request(
    request: NetworkBrowserOpenWebUIFreezeRequest,
) -> NetworkBrowserOpenWebUIFreezeRequest:
    payload = _model_payload(request)
    for field_name, reason in _M80_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, NetworkBrowserOpenWebUIFreezeRequest):
        raise ValueError("SECRET_LIKE_M80_FREEZE_CONTENT_DENIED")
    validated = NetworkBrowserOpenWebUIFreezeRequest.model_validate(payload)
    for field_name, reason in _M80_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M80_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M80_SIDE_EFFECTS_DENIED")
    _validate_accepted_milestones(validated.accepted_milestone_refs)
    _validate_checklist_refs(validated.checklist_refs)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M80_FREEZE_CONTENT_DENIED") from exc
    return validated


def validate_network_browser_openwebui_freeze_report(
    report: NetworkBrowserOpenWebUIFreezeReport,
) -> NetworkBrowserOpenWebUIFreezeReport:
    validated = NetworkBrowserOpenWebUIFreezeReport.model_validate(_model_payload(report))
    for field_name, reason in _M80_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M80_REPORT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != NetworkBrowserOpenWebUIFreezeStatus.frozen:
        raise ValueError("M80_FREEZE_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M80_SIDE_EFFECTS_DENIED")
    _validate_accepted_milestones(validated.accepted_milestone_refs)
    _validate_checklist_refs(validated.checklist_refs)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M80_FREEZE_CONTENT_DENIED") from exc
    return validated


def _validate_accepted_milestones(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M80_ACCEPTED_MILESTONES_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M80_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "accepted_milestone_ref")
    missing = [ref for ref in REQUIRED_M80_ACCEPTED_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M80_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M80_ACCEPTED_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M80_MILESTONE_REF_UNEXPECTED")


def _validate_checklist_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M80_CHECKLIST_REF_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M80_CHECKLIST_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "checklist_ref")


def _model_payload(model: BaseModel) -> dict[str, Any]:
    payload = model.model_dump()
    extra = getattr(model, "__pydantic_extra__", None)
    if extra:
        payload.update(extra)
    for key, value in getattr(model, "__dict__", {}).items():
        if key not in payload:
            payload[key] = value
    return payload


def _has_secret_like_extra(payload: dict[str, Any], model_type: type[BaseModel]) -> bool:
    allowed_fields = set(model_type.model_fields)
    extra_payload = {key: value for key, value in payload.items() if key not in allowed_fields}
    if not extra_payload:
        return False
    try:
        _validate_safe_payload(extra_payload)
    except ValueError:
        return True
    return False


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[1]


_M80_REQUIRED_TRUE = [
    ("freeze_only", "FREEZE_ONLY_REQUIRED"),
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("network_browser_openwebui_only", "NETWORK_BROWSER_OPENWEBUI_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_REVIEW_REQUIRED"),
]


_M80_POLICY_DENIALS = [
    ("network_tool_expansion_enabled", "NETWORK_TOOL_EXPANSION_DENIED"),
    ("unrestricted_network_enabled", "UNRESTRICTED_NETWORK_DENIED"),
    ("authenticated_network_action_enabled", "AUTHENTICATED_NETWORK_ACTION_DENIED"),
    ("raw_network_response_enabled", "RAW_NETWORK_RESPONSE_DENIED"),
    ("browser_navigation_enabled", "BROWSER_NAVIGATION_DENIED"),
    ("browser_click_enabled", "BROWSER_CLICK_DENIED"),
    ("browser_action_execution_enabled", "BROWSER_ACTION_EXECUTION_DENIED"),
    ("browser_screenshot_enabled", "BROWSER_SCREENSHOT_DENIED"),
    ("raw_dom_enabled", "RAW_DOM_DENIED"),
    ("authenticated_browser_profile_enabled", "AUTHENTICATED_BROWSER_PROFILE_DENIED"),
    ("openwebui_model_authority_enabled", "OPENWEBUI_MODEL_AUTHORITY_DENIED"),
    ("openwebui_tool_execution_enabled", "OPENWEBUI_TOOL_EXECUTION_DENIED"),
    ("openwebui_memory_write_enabled", "OPENWEBUI_MEMORY_WRITE_DENIED"),
    ("openwebui_context_injection_enabled", "OPENWEBUI_CONTEXT_INJECTION_DENIED"),
    ("raw_prompt_exposure_enabled", "RAW_PROMPT_EXPOSURE_DENIED"),
    ("raw_provider_payload_exposure_enabled", "RAW_PROVIDER_PAYLOAD_EXPOSURE_DENIED"),
    ("plugin_install_enabled", "PLUGIN_INSTALL_DENIED"),
    ("plugin_enablement_enabled", "PLUGIN_ENABLEMENT_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("plugin_runtime_import_enabled", "PLUGIN_RUNTIME_IMPORT_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("credential_cookie_access_enabled", "CREDENTIAL_COOKIE_ACCESS_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]


_M80_REQUEST_DENIALS = [
    ("network_tool_expansion_requested", "NETWORK_TOOL_EXPANSION_DENIED"),
    ("unrestricted_network_requested", "UNRESTRICTED_NETWORK_DENIED"),
    ("authenticated_network_action_requested", "AUTHENTICATED_NETWORK_ACTION_DENIED"),
    ("raw_network_response_requested", "RAW_NETWORK_RESPONSE_DENIED"),
    ("browser_navigation_requested", "BROWSER_NAVIGATION_DENIED"),
    ("browser_click_requested", "BROWSER_CLICK_DENIED"),
    ("browser_action_execution_requested", "BROWSER_ACTION_EXECUTION_DENIED"),
    ("browser_screenshot_requested", "BROWSER_SCREENSHOT_DENIED"),
    ("raw_dom_requested", "RAW_DOM_DENIED"),
    ("authenticated_browser_profile_requested", "AUTHENTICATED_BROWSER_PROFILE_DENIED"),
    ("openwebui_model_authority_requested", "OPENWEBUI_MODEL_AUTHORITY_DENIED"),
    ("openwebui_tool_execution_requested", "OPENWEBUI_TOOL_EXECUTION_DENIED"),
    ("openwebui_memory_write_requested", "OPENWEBUI_MEMORY_WRITE_DENIED"),
    ("openwebui_context_injection_requested", "OPENWEBUI_CONTEXT_INJECTION_DENIED"),
    ("raw_prompt_exposure_requested", "RAW_PROMPT_EXPOSURE_DENIED"),
    ("raw_provider_payload_exposure_requested", "RAW_PROVIDER_PAYLOAD_EXPOSURE_DENIED"),
    ("plugin_install_requested", "PLUGIN_INSTALL_DENIED"),
    ("plugin_enablement_requested", "PLUGIN_ENABLEMENT_DENIED"),
    ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
    ("plugin_runtime_import_requested", "PLUGIN_RUNTIME_IMPORT_DENIED"),
    ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
    ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
    ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
    ("credential_cookie_access_requested", "CREDENTIAL_COOKIE_ACCESS_DENIED"),
    ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
]


_M80_REPORT_DENIALS = [
    ("network_tool_expansion_performed", "NETWORK_TOOL_EXPANSION_DENIED"),
    ("unrestricted_network_performed", "UNRESTRICTED_NETWORK_DENIED"),
    ("authenticated_network_action_performed", "AUTHENTICATED_NETWORK_ACTION_DENIED"),
    ("raw_network_response_returned", "RAW_NETWORK_RESPONSE_DENIED"),
    ("browser_navigation_performed", "BROWSER_NAVIGATION_DENIED"),
    ("browser_click_performed", "BROWSER_CLICK_DENIED"),
    ("browser_action_performed", "BROWSER_ACTION_EXECUTION_DENIED"),
    ("browser_screenshot_performed", "BROWSER_SCREENSHOT_DENIED"),
    ("raw_dom_returned", "RAW_DOM_DENIED"),
    ("authenticated_browser_profile_accessed", "AUTHENTICATED_BROWSER_PROFILE_DENIED"),
    ("openwebui_model_authority_granted", "OPENWEBUI_MODEL_AUTHORITY_DENIED"),
    ("openwebui_tool_execution_performed", "OPENWEBUI_TOOL_EXECUTION_DENIED"),
    ("openwebui_memory_write_performed", "OPENWEBUI_MEMORY_WRITE_DENIED"),
    ("openwebui_context_injection_performed", "OPENWEBUI_CONTEXT_INJECTION_DENIED"),
    ("raw_prompt_exposed", "RAW_PROMPT_EXPOSURE_DENIED"),
    ("raw_provider_payload_exposed", "RAW_PROVIDER_PAYLOAD_EXPOSURE_DENIED"),
    ("plugin_install_performed", "PLUGIN_INSTALL_DENIED"),
    ("plugin_enablement_performed", "PLUGIN_ENABLEMENT_DENIED"),
    ("plugin_execution_performed", "PLUGIN_EXECUTION_DENIED"),
    ("plugin_runtime_import_performed", "PLUGIN_RUNTIME_IMPORT_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("background_worker_started", "BACKGROUND_WORKER_DENIED"),
    ("remote_execution_performed", "REMOTE_EXECUTION_DENIED"),
    ("credential_cookie_access_performed", "CREDENTIAL_COOKIE_ACCESS_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]
