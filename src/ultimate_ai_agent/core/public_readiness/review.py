import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.tools.v2.validation import validate_safe_tool_payload


M59_DOC_REFS = [
    "docs/public_readiness/PUBLIC_GITHUB_READINESS.md",
    "docs/public_readiness/PUBLIC_GITHUB_READINESS_POLICY.md",
    "docs/public_readiness/PUBLIC_GITHUB_READINESS_AUTHORITY_BOUNDARY.md",
    "docs/public_readiness/M59_TO_M60_BOUNDARY.md",
]
M59_REQUIRED_CHECKLIST_REFS = {
    "readiness:docs-current",
    "readiness:secret-hygiene",
    "readiness:artifact-hygiene",
    "readiness:route-boundary",
    "readiness:dependency-boundary",
}
M59_SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")
M59_SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|secret|token|password|private[_-]?key|authorization|cookie|oauth|bearer)",
    re.IGNORECASE,
)


class PublicGitHubReadinessStatus(str, Enum):
    reviewed = "reviewed"
    denied = "denied"


class _M59PublicReadinessModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class PublicGitHubReadinessPolicy(_M59PublicReadinessModel):
    policy_ref: str = "public-github-readiness-policy:m59"
    baseline_version: str = "0.63.0"
    review_only: bool = True
    contract_only: bool = True
    local_only: bool = True
    publication_enabled: bool = False
    github_push_enabled: bool = False
    github_release_enabled: bool = False
    wiki_automation_enabled: bool = False
    artifact_upload_enabled: bool = False
    external_service_enabled: bool = False
    credential_handling_enabled: bool = False
    network_access_enabled: bool = False
    production_authority_enabled: bool = False
    backend_routes_enabled: bool = False
    control_center_controls_enabled: bool = False
    dependencies_added: bool = False
    m60_beta_freeze_enabled: bool = False
    docs_refs: list[str] = Field(default_factory=lambda: list(M59_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M59", "version:v0.63.0"])
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy_shape(self) -> Any:
        _validate_m59_ref(self.policy_ref, "policy_ref")
        for ref in self.docs_refs:
            _require_nonempty(ref, "docs_ref")
        for ref in self.metadata_refs:
            _validate_m59_ref(ref, "metadata_ref")
        return self


class PublicGitHubReadinessRequest(_M59PublicReadinessModel):
    request_ref: str
    readiness_ref: str
    repository_ref: str
    baseline_ref: str
    actor_ref: str
    checklist_refs: list[str]
    artifact_refs: list[str] = Field(default_factory=list)
    safe_summary: str
    publication_requested: bool = False
    github_push_requested: bool = False
    github_release_requested: bool = False
    wiki_automation_requested: bool = False
    artifact_upload_requested: bool = False
    external_service_requested: bool = False
    credential_handling_requested: bool = False
    network_access_requested: bool = False
    production_authority_requested: bool = False
    m60_beta_freeze_requested: bool = False
    contains_secret: bool = False
    contains_private_user_data: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request_shape(self) -> Any:
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.readiness_ref, "readiness_ref"),
            (self.repository_ref, "repository_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m59_ref(value, field_name)
        if not self.checklist_refs:
            raise ValueError("PUBLIC_READINESS_CHECKLIST_REFS_REQUIRED")
        for ref in self.checklist_refs:
            _validate_m59_ref(ref, "checklist_ref")
        for ref in self.artifact_refs:
            _validate_m59_ref(ref, "artifact_ref")
        for ref in self.metadata_refs:
            _validate_m59_ref(ref, "metadata_ref")
        _require_nonempty(self.safe_summary, "safe_summary")
        return self


class PublicGitHubReadinessReceiptPlan(_M59PublicReadinessModel):
    receipt_plan_ref: str
    readiness_ref: str
    review_only: bool = True
    publication_performed: bool = False
    github_push_performed: bool = False
    github_release_performed: bool = False
    wiki_automation_performed: bool = False
    artifact_upload_performed: bool = False
    external_service_performed: bool = False
    credential_handling_performed: bool = False
    network_access_performed: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M59 public GitHub readiness receipt plan."

    @model_validator(mode="after")
    def validate_receipt_plan(self) -> Any:
        _validate_m59_ref(self.receipt_plan_ref, "receipt_plan_ref")
        _validate_m59_ref(self.readiness_ref, "readiness_ref")
        if not self.review_only:
            raise ValueError("PUBLIC_READINESS_REVIEW_ONLY_REQUIRED")
        for field_name, reason in _PERFORMED_DENIALS:
            if getattr(self, field_name):
                raise ValueError(reason)
        if self.side_effects_performed:
            raise ValueError("SIDE_EFFECTS_DENIED")
        _validate_safe_payload(self.safe_summary)
        return self


class PublicGitHubReadinessReport(_M59PublicReadinessModel):
    report_ref: str
    request_ref: str
    readiness_ref: str
    repository_ref: str
    baseline_ref: str
    actor_ref: str
    status: PublicGitHubReadinessStatus
    review_only: bool = True
    checklist_refs: list[str]
    missing_required_checklist_refs: list[str] = Field(default_factory=list)
    artifact_refs: list[str] = Field(default_factory=list)
    receipt_plan: PublicGitHubReadinessReceiptPlan | None = None
    publication_performed: bool = False
    github_push_performed: bool = False
    github_release_performed: bool = False
    wiki_automation_performed: bool = False
    artifact_upload_performed: bool = False
    external_service_performed: bool = False
    credential_handling_performed: bool = False
    network_access_performed: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    docs_refs: list[str] = Field(default_factory=lambda: list(M59_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M59", "version:v0.63.0"])

    @model_validator(mode="after")
    def validate_report(self) -> Any:
        for value, field_name in [
            (self.report_ref, "report_ref"),
            (self.request_ref, "request_ref"),
            (self.readiness_ref, "readiness_ref"),
            (self.repository_ref, "repository_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m59_ref(value, field_name)
        if not self.review_only:
            raise ValueError("PUBLIC_READINESS_REVIEW_ONLY_REQUIRED")
        for field_name, reason in _PERFORMED_DENIALS:
            if getattr(self, field_name):
                raise ValueError(reason)
        if self.side_effects_performed:
            raise ValueError("SIDE_EFFECTS_DENIED")
        _validate_safe_payload(self.safe_summary)
        return self


def validate_public_github_readiness_policy(
    policy: PublicGitHubReadinessPolicy,
) -> PublicGitHubReadinessPolicy:
    validated = PublicGitHubReadinessPolicy.model_validate(policy.model_dump())
    _validate_safe_payload(validated.metadata)
    if not validated.review_only or not validated.contract_only or not validated.local_only:
        raise ValueError("PUBLIC_READINESS_REVIEW_ONLY_REQUIRED")
    for field_name, reason in _ENABLED_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def validate_public_github_readiness_request(
    request: PublicGitHubReadinessRequest,
) -> PublicGitHubReadinessRequest:
    validated = PublicGitHubReadinessRequest.model_validate(request.model_dump())
    _validate_safe_payload(validated.safe_summary)
    _validate_safe_payload(validated.metadata)
    if len(set(validated.checklist_refs)) != len(validated.checklist_refs):
        raise ValueError("PUBLIC_READINESS_CHECKLIST_REF_DUPLICATE")
    for field_name, reason in _REQUESTED_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def build_public_github_readiness_report(
    request: PublicGitHubReadinessRequest,
    policy: PublicGitHubReadinessPolicy | None = None,
) -> PublicGitHubReadinessReport:
    validate_public_github_readiness_policy(policy or PublicGitHubReadinessPolicy())
    active_request = validate_public_github_readiness_request(request)
    missing = sorted(M59_REQUIRED_CHECKLIST_REFS.difference(active_request.checklist_refs))
    status = PublicGitHubReadinessStatus.denied if missing else PublicGitHubReadinessStatus.reviewed
    reason_codes = (
        ["M59_PUBLIC_READINESS_CHECKLIST_INCOMPLETE"]
        if missing
        else ["M59_PUBLIC_GITHUB_READINESS_REVIEW_ONLY"]
    )
    return PublicGitHubReadinessReport(
        report_ref=f"public-readiness-report:{_ref_suffix(active_request.readiness_ref)}",
        request_ref=active_request.request_ref,
        readiness_ref=active_request.readiness_ref,
        repository_ref=active_request.repository_ref,
        baseline_ref=active_request.baseline_ref,
        actor_ref=active_request.actor_ref,
        status=status,
        checklist_refs=list(active_request.checklist_refs),
        missing_required_checklist_refs=missing,
        artifact_refs=list(active_request.artifact_refs),
        receipt_plan=PublicGitHubReadinessReceiptPlan(
            receipt_plan_ref=f"public-readiness-receipt:{_ref_suffix(active_request.readiness_ref)}",
            readiness_ref=active_request.readiness_ref,
            safe_summary="M59 records public GitHub readiness review metadata only; no publication is performed.",
        ),
        reason_codes=reason_codes,
        safe_summary="Public GitHub readiness reviewed without publishing, uploading, or granting authority.",
        metadata_refs=[
            active_request.request_ref,
            active_request.readiness_ref,
            active_request.repository_ref,
            active_request.baseline_ref,
        ],
    )


_ENABLED_DENIALS = [
    ("publication_enabled", "PUBLICATION_DENIED"),
    ("github_push_enabled", "GITHUB_PUSH_DENIED"),
    ("github_release_enabled", "GITHUB_RELEASE_DENIED"),
    ("wiki_automation_enabled", "WIKI_AUTOMATION_DENIED"),
    ("artifact_upload_enabled", "ARTIFACT_UPLOAD_DENIED"),
    ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("backend_routes_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_controls_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependencies_added", "DEPENDENCY_ADDITION_DENIED"),
    ("m60_beta_freeze_enabled", "M60_BETA_FREEZE_DENIED"),
]

_REQUESTED_DENIALS = [
    ("publication_requested", "PUBLICATION_DENIED"),
    ("github_push_requested", "GITHUB_PUSH_DENIED"),
    ("github_release_requested", "GITHUB_RELEASE_DENIED"),
    ("wiki_automation_requested", "WIKI_AUTOMATION_DENIED"),
    ("artifact_upload_requested", "ARTIFACT_UPLOAD_DENIED"),
    ("external_service_requested", "EXTERNAL_SERVICE_DENIED"),
    ("credential_handling_requested", "CREDENTIAL_HANDLING_DENIED"),
    ("network_access_requested", "NETWORK_ACCESS_DENIED"),
    ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
    ("m60_beta_freeze_requested", "M60_BETA_FREEZE_DENIED"),
    ("contains_secret", "SECRET_LIKE_PUBLIC_READINESS_CONTENT_DENIED"),
    ("contains_private_user_data", "PRIVATE_DATA_PUBLIC_READINESS_CONTENT_DENIED"),
    ("contains_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
    ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
]

_PERFORMED_DENIALS = [
    ("publication_performed", "PUBLICATION_DENIED"),
    ("github_push_performed", "GITHUB_PUSH_DENIED"),
    ("github_release_performed", "GITHUB_RELEASE_DENIED"),
    ("wiki_automation_performed", "WIKI_AUTOMATION_DENIED"),
    ("artifact_upload_performed", "ARTIFACT_UPLOAD_DENIED"),
    ("external_service_performed", "EXTERNAL_SERVICE_DENIED"),
    ("credential_handling_performed", "CREDENTIAL_HANDLING_DENIED"),
    ("network_access_performed", "NETWORK_ACCESS_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]


def _validate_m59_ref(value: str, field_name: str) -> None:
    _require_nonempty(value, field_name)
    if not M59_SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name} must be a structured safe ref")


def _validate_safe_payload(value: Any) -> None:
    _deny_secret_like_keys(value)
    try:
        validate_safe_tool_payload(value, "public_readiness_content")
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_PUBLIC_READINESS_CONTENT_DENIED") from exc


def _deny_secret_like_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if M59_SECRET_KEY_RE.search(str(key)):
                raise ValueError("SECRET_LIKE_PUBLIC_READINESS_CONTENT_DENIED")
            _deny_secret_like_keys(item)
    elif isinstance(value, list):
        for item in value:
            _deny_secret_like_keys(item)


def _require_nonempty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[-1]
