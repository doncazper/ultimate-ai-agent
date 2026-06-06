import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.tools.v2.validation import validate_safe_tool_payload


M60_DOC_REFS = [
    "docs/beta/LOCAL_DEVELOPER_BETA_FREEZE.md",
    "docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_POLICY.md",
    "docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_AUTHORITY_BOUNDARY.md",
    "docs/beta/POST_M60_AUTONOMY_BOUNDARY.md",
]
M60_REQUIRED_CHECKLIST_REFS = {
    "beta-freeze:validation-green",
    "beta-freeze:docs-current",
    "beta-freeze:route-stable",
    "beta-freeze:dependency-stable",
    "beta-freeze:artifact-clean",
    "beta-freeze:authority-frozen",
}
M60_SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")
M60_SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|secret|token|password|private[_-]?key|authorization|cookie|oauth|bearer)",
    re.IGNORECASE,
)


class LocalDeveloperBetaFreezeStatus(str, Enum):
    frozen = "frozen"
    denied = "denied"


class _M60BetaFreezeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class LocalDeveloperBetaFreezePolicy(_M60BetaFreezeModel):
    policy_ref: str = "local-developer-beta-freeze-policy:m60"
    baseline_version: str = "0.64.0"
    freeze_only: bool = True
    local_developer_beta_only: bool = True
    review_only: bool = True
    production_authority_enabled: bool = False
    public_release_enabled: bool = False
    external_distribution_enabled: bool = False
    post_m60_autonomy_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    network_tool_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    credential_handling_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    model_provider_call_enabled: bool = False
    backend_routes_enabled: bool = False
    control_center_controls_enabled: bool = False
    dependencies_added: bool = False
    docs_refs: list[str] = Field(default_factory=lambda: list(M60_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M60", "version:v0.64.0"])
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy_shape(self):
        _validate_m60_ref(self.policy_ref, "policy_ref")
        for ref in self.docs_refs:
            _require_nonempty(ref, "docs_ref")
        for ref in self.metadata_refs:
            _validate_m60_ref(ref, "metadata_ref")
        return self


class LocalDeveloperBetaFreezeRequest(_M60BetaFreezeModel):
    request_ref: str
    freeze_ref: str
    baseline_ref: str
    actor_ref: str
    checklist_refs: list[str]
    release_candidate_refs: list[str] = Field(default_factory=list)
    safe_summary: str
    public_release_requested: bool = False
    external_distribution_requested: bool = False
    post_m60_autonomy_requested: bool = False
    production_authority_requested: bool = False
    execution_requested: bool = False
    tool_execution_requested: bool = False
    shell_execution_requested: bool = False
    network_tool_requested: bool = False
    browser_automation_requested: bool = False
    plugin_execution_requested: bool = False
    mobile_sensor_requested: bool = False
    remote_execution_requested: bool = False
    credential_handling_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    model_provider_call_requested: bool = False
    contains_secret: bool = False
    contains_private_user_data: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request_shape(self):
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.freeze_ref, "freeze_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m60_ref(value, field_name)
        if not self.checklist_refs:
            raise ValueError("BETA_FREEZE_CHECKLIST_REFS_REQUIRED")
        for ref in self.checklist_refs:
            _validate_m60_ref(ref, "checklist_ref")
        for ref in self.release_candidate_refs:
            _validate_m60_ref(ref, "release_candidate_ref")
        for ref in self.metadata_refs:
            _validate_m60_ref(ref, "metadata_ref")
        _require_nonempty(self.safe_summary, "safe_summary")
        return self


class LocalDeveloperBetaFreezeReceiptPlan(_M60BetaFreezeModel):
    receipt_plan_ref: str
    freeze_ref: str
    freeze_only: bool = True
    local_developer_beta_only: bool = True
    production_authority_granted: bool = False
    public_release_performed: bool = False
    external_distribution_performed: bool = False
    execution_performed: bool = False
    post_m60_autonomy_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M60 local developer beta freeze receipt plan."

    @model_validator(mode="after")
    def validate_receipt_plan(self):
        _validate_m60_ref(self.receipt_plan_ref, "receipt_plan_ref")
        _validate_m60_ref(self.freeze_ref, "freeze_ref")
        if not self.freeze_only or not self.local_developer_beta_only:
            raise ValueError("LOCAL_DEVELOPER_BETA_FREEZE_ONLY_REQUIRED")
        for field_name, reason in _PERFORMED_DENIALS:
            if getattr(self, field_name):
                raise ValueError(reason)
        if self.side_effects_performed:
            raise ValueError("SIDE_EFFECTS_DENIED")
        _validate_safe_payload(self.safe_summary)
        return self


class LocalDeveloperBetaFreezeReport(_M60BetaFreezeModel):
    report_ref: str
    request_ref: str
    freeze_ref: str
    baseline_ref: str
    actor_ref: str
    status: LocalDeveloperBetaFreezeStatus
    freeze_only: bool = True
    local_developer_beta_only: bool = True
    checklist_refs: list[str]
    missing_required_checklist_refs: list[str] = Field(default_factory=list)
    release_candidate_refs: list[str] = Field(default_factory=list)
    receipt_plan: LocalDeveloperBetaFreezeReceiptPlan | None = None
    production_authority_granted: bool = False
    public_release_performed: bool = False
    external_distribution_performed: bool = False
    execution_performed: bool = False
    post_m60_autonomy_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    docs_refs: list[str] = Field(default_factory=lambda: list(M60_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M60", "version:v0.64.0"])

    @model_validator(mode="after")
    def validate_report(self):
        for value, field_name in [
            (self.report_ref, "report_ref"),
            (self.request_ref, "request_ref"),
            (self.freeze_ref, "freeze_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m60_ref(value, field_name)
        if not self.freeze_only or not self.local_developer_beta_only:
            raise ValueError("LOCAL_DEVELOPER_BETA_FREEZE_ONLY_REQUIRED")
        for field_name, reason in _PERFORMED_DENIALS:
            if getattr(self, field_name):
                raise ValueError(reason)
        if self.side_effects_performed:
            raise ValueError("SIDE_EFFECTS_DENIED")
        _validate_safe_payload(self.safe_summary)
        return self


def validate_local_developer_beta_freeze_policy(
    policy: LocalDeveloperBetaFreezePolicy,
) -> LocalDeveloperBetaFreezePolicy:
    validated = LocalDeveloperBetaFreezePolicy.model_validate(policy.model_dump())
    _validate_safe_payload(validated.metadata)
    if not validated.freeze_only or not validated.local_developer_beta_only or not validated.review_only:
        raise ValueError("LOCAL_DEVELOPER_BETA_FREEZE_ONLY_REQUIRED")
    for field_name, reason in _ENABLED_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def validate_local_developer_beta_freeze_request(
    request: LocalDeveloperBetaFreezeRequest,
) -> LocalDeveloperBetaFreezeRequest:
    validated = LocalDeveloperBetaFreezeRequest.model_validate(request.model_dump())
    _validate_safe_payload(validated.safe_summary)
    _validate_safe_payload(validated.metadata)
    if len(set(validated.checklist_refs)) != len(validated.checklist_refs):
        raise ValueError("BETA_FREEZE_CHECKLIST_REF_DUPLICATE")
    for field_name, reason in _REQUESTED_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def build_local_developer_beta_freeze_report(
    request: LocalDeveloperBetaFreezeRequest,
    policy: LocalDeveloperBetaFreezePolicy | None = None,
) -> LocalDeveloperBetaFreezeReport:
    validate_local_developer_beta_freeze_policy(policy or LocalDeveloperBetaFreezePolicy())
    active_request = validate_local_developer_beta_freeze_request(request)
    missing = sorted(M60_REQUIRED_CHECKLIST_REFS.difference(active_request.checklist_refs))
    status = LocalDeveloperBetaFreezeStatus.denied if missing else LocalDeveloperBetaFreezeStatus.frozen
    reason_codes = (
        ["M60_LOCAL_DEVELOPER_BETA_FREEZE_CHECKLIST_INCOMPLETE"]
        if missing
        else ["M60_LOCAL_DEVELOPER_BETA_FREEZE_REVIEW_ONLY"]
    )
    return LocalDeveloperBetaFreezeReport(
        report_ref=f"beta-freeze-report:{_ref_suffix(active_request.freeze_ref)}",
        request_ref=active_request.request_ref,
        freeze_ref=active_request.freeze_ref,
        baseline_ref=active_request.baseline_ref,
        actor_ref=active_request.actor_ref,
        status=status,
        checklist_refs=list(active_request.checklist_refs),
        missing_required_checklist_refs=missing,
        release_candidate_refs=list(active_request.release_candidate_refs),
        receipt_plan=LocalDeveloperBetaFreezeReceiptPlan(
            receipt_plan_ref=f"beta-freeze-receipt:{_ref_suffix(active_request.freeze_ref)}",
            freeze_ref=active_request.freeze_ref,
            safe_summary="M60 records local developer beta freeze metadata only; no authority is granted.",
        ),
        reason_codes=reason_codes,
        safe_summary="Local developer beta freeze reviewed without production authority or post-M60 autonomy.",
        metadata_refs=[
            active_request.request_ref,
            active_request.freeze_ref,
            active_request.baseline_ref,
        ],
    )


_ENABLED_DENIALS = [
    ("public_release_enabled", "PUBLIC_RELEASE_DENIED"),
    ("external_distribution_enabled", "EXTERNAL_DISTRIBUTION_DENIED"),
    ("post_m60_autonomy_enabled", "POST_M60_AUTONOMY_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("network_tool_enabled", "NETWORK_TOOL_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("model_provider_call_enabled", "MODEL_PROVIDER_CALL_DENIED"),
    ("backend_routes_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_controls_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependencies_added", "DEPENDENCY_ADDITION_DENIED"),
]

_REQUESTED_DENIALS = [
    ("public_release_requested", "PUBLIC_RELEASE_DENIED"),
    ("external_distribution_requested", "EXTERNAL_DISTRIBUTION_DENIED"),
    ("post_m60_autonomy_requested", "POST_M60_AUTONOMY_DENIED"),
    ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
    ("execution_requested", "EXECUTION_DENIED"),
    ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
    ("network_tool_requested", "NETWORK_TOOL_DENIED"),
    ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_requested", "MOBILE_SENSOR_DENIED"),
    ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
    ("credential_handling_requested", "CREDENTIAL_HANDLING_DENIED"),
    ("memory_write_requested", "MEMORY_WRITE_DENIED"),
    ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
    ("model_provider_call_requested", "MODEL_PROVIDER_CALL_DENIED"),
    ("contains_secret", "SECRET_LIKE_BETA_FREEZE_CONTENT_DENIED"),
    ("contains_private_user_data", "PRIVATE_DATA_BETA_FREEZE_CONTENT_DENIED"),
    ("contains_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
    ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
]

_PERFORMED_DENIALS = [
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
    ("public_release_performed", "PUBLIC_RELEASE_DENIED"),
    ("external_distribution_performed", "EXTERNAL_DISTRIBUTION_DENIED"),
    ("execution_performed", "EXECUTION_DENIED"),
    ("post_m60_autonomy_enabled", "POST_M60_AUTONOMY_DENIED"),
]


def _validate_m60_ref(value: str, field_name: str) -> None:
    _require_nonempty(value, field_name)
    if not M60_SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name} must be a structured safe ref")


def _validate_safe_payload(value: Any) -> None:
    _deny_secret_like_keys(value)
    try:
        validate_safe_tool_payload(value, "beta_freeze_content")
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_BETA_FREEZE_CONTENT_DENIED") from exc


def _deny_secret_like_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if M60_SECRET_KEY_RE.search(str(key)):
                raise ValueError("SECRET_LIKE_BETA_FREEZE_CONTENT_DENIED")
            _deny_secret_like_keys(item)
    elif isinstance(value, list):
        for item in value:
            _deny_secret_like_keys(item)


def _require_nonempty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[-1]
