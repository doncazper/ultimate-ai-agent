import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.tools.v2.validation import (
    validate_safe_tool_payload,
    validate_tool_ref,
)


M53_DOC_REFS = [
    "docs/tools/CONTROLLED_TOOL_EXPANSION_REVIEW.md",
    "docs/tools/CONTROLLED_TOOL_EXPANSION_POLICY.md",
    "docs/tools/CONTROLLED_TOOL_EXPANSION_AUTHORITY_BOUNDARY.md",
    "docs/tools/M53_TO_M54_BOUNDARY.md",
]
M53_SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")


class ToolExpansionCapabilityKind(str, Enum):
    safe_metadata_review = "safe_metadata_review"
    shell_execution = "shell_execution"
    subprocess_execution = "subprocess_execution"
    unrestricted_network_tool = "unrestricted_network_tool"
    provider_model_call = "provider_model_call"
    browser_automation_execution = "browser_automation_execution"
    plugin_enablement = "plugin_enablement"
    mobile_sensor_access = "mobile_sensor_access"
    remote_execution = "remote_execution"
    raw_file_browsing = "raw_file_browsing"
    raw_file_export = "raw_file_export"
    full_file_read = "full_file_read"
    file_mutation = "file_mutation"
    memory_write = "memory_write"
    context_injection = "context_injection"
    credentials_cookie_handling = "credentials_cookie_handling"
    external_saas_analytics_sdk = "external_saas_analytics_sdk"
    production_authority = "production_authority"
    unknown = "unknown"


class ControlledToolExpansionReviewStatus(str, Enum):
    review_ready = "review_ready"
    future_milestone = "future_milestone"
    denied = "denied"


class _M53ToolExpansionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ControlledToolExpansionPolicy(_M53ToolExpansionModel):
    policy_ref: str = "controlled-tool-expansion-policy:m53"
    baseline_version: str = "0.57.0"
    review_only: bool = True
    planning_only: bool = True
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    subprocess_execution_enabled: bool = False
    unrestricted_network_tools_enabled: bool = False
    provider_model_calls_enabled: bool = False
    model_authority_enabled: bool = False
    browser_automation_execution_enabled: bool = False
    plugin_enablement_enabled: bool = False
    mobile_sensor_access_enabled: bool = False
    remote_execution_enabled: bool = False
    raw_file_browsing_enabled: bool = False
    raw_file_export_enabled: bool = False
    full_file_read_enabled: bool = False
    file_mutation_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    credentials_cookie_handling_enabled: bool = False
    external_saas_analytics_sdk_enabled: bool = False
    backend_routes_enabled: bool = False
    control_center_controls_enabled: bool = False
    dependencies_added: bool = False
    production_authority_enabled: bool = False
    m54_implemented: bool = False
    docs_refs: list[str] = Field(default_factory=lambda: list(M53_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M53", "version:v0.57.0"])
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy(self) -> Any:
        validate_tool_ref(self.policy_ref, "policy_ref")
        for ref in self.docs_refs:
            _require_nonempty(ref, "docs_ref")
        for ref in self.metadata_refs:
            _validate_m53_ref(ref, "metadata_ref")
        validate_safe_tool_payload(self.metadata, "metadata")
        return self


class ControlledToolExpansionCandidate(_M53ToolExpansionModel):
    candidate_ref: str
    safe_name: str
    capability_kind: ToolExpansionCapabilityKind
    safe_summary: str
    approval_ref: str | None = None
    authority_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    execution_requested: bool = False
    tool_enablement_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_raw_tool_payload: bool = False
    contains_secret_like_content: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_candidate(self) -> Any:
        _validate_m53_ref(self.candidate_ref, "candidate_ref")
        _require_nonempty(self.safe_name, "safe_name")
        _require_nonempty(self.safe_summary, "safe_summary")
        for ref in [*self.authority_refs, *self.metadata_refs]:
            validate_tool_ref(ref, "metadata_ref")
        validate_safe_tool_payload(self.metadata, "metadata")
        if self.approval_ref:
            validate_tool_ref(self.approval_ref, "approval_ref")
        return self


class ControlledToolExpansionReceiptPlan(_M53ToolExpansionModel):
    receipt_plan_ref: str
    candidate_ref: str
    review_only: bool = True
    execution_performed: bool = False
    tool_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    raw_content_stored: bool = False
    network_call_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    safe_summary: str = "M53 review-only receipt plan."
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M53", "version:v0.57.0"])

    @model_validator(mode="after")
    def validate_receipt_plan(self) -> Any:
        _validate_m53_ref(self.receipt_plan_ref, "receipt_plan_ref")
        _validate_m53_ref(self.candidate_ref, "candidate_ref")
        _require_nonempty(self.safe_summary, "safe_summary")
        for ref in self.metadata_refs:
            _validate_m53_ref(ref, "metadata_ref")
        if not self.review_only:
            raise ValueError("M53_REVIEW_ONLY_REQUIRED")
        for field_name, reason in [
            ("execution_performed", "TOOL_EXPANSION_EXECUTION_DENIED"),
            ("tool_enabled", "TOOL_ENABLEMENT_DENIED"),
            ("raw_content_stored", "RAW_CONTENT_STORAGE_DENIED"),
            ("network_call_performed", "NETWORK_CALL_DENIED"),
            ("model_call_performed", "MODEL_CALL_DENIED"),
            ("memory_write_performed", "MEMORY_WRITE_DENIED"),
            ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
        ]:
            if getattr(self, field_name):
                raise ValueError(reason)
        if self.side_effects_performed:
            raise ValueError("SIDE_EFFECTS_DENIED")
        return self


class ControlledToolExpansionDecision(_M53ToolExpansionModel):
    decision_ref: str
    candidate_ref: str
    status: ControlledToolExpansionReviewStatus
    review_allowed: bool
    execution_allowed: bool = False
    tool_enablement_allowed: bool = False
    future_milestone_required: bool = False
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str = "M53 controlled tool expansion review is metadata-only."
    receipt_plan: ControlledToolExpansionReceiptPlan | None = None
    no_network_call_performed: bool = True
    no_model_call_performed: bool = True
    no_memory_write_performed: bool = True
    no_context_injection_performed: bool = True
    docs_refs: list[str] = Field(default_factory=lambda: list(M53_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M53", "version:v0.57.0"])

    @model_validator(mode="after")
    def validate_decision(self) -> Any:
        _validate_m53_ref(self.decision_ref, "decision_ref")
        _validate_m53_ref(self.candidate_ref, "candidate_ref")
        for ref in self.reason_codes:
            _require_nonempty(ref, "reason_code")
        for ref in self.docs_refs:
            _require_nonempty(ref, "docs_ref")
        for ref in self.metadata_refs:
            _validate_m53_ref(ref, "metadata_ref")
        _require_nonempty(self.safe_message, "safe_message")
        if self.execution_allowed:
            raise ValueError("TOOL_EXPANSION_EXECUTION_DENIED")
        if self.tool_enablement_allowed:
            raise ValueError("TOOL_ENABLEMENT_DENIED")
        if (
            not self.no_network_call_performed
            or not self.no_model_call_performed
            or not self.no_memory_write_performed
            or not self.no_context_injection_performed
        ):
            raise ValueError("SIDE_EFFECTS_DENIED")
        if self.status == ControlledToolExpansionReviewStatus.denied and self.review_allowed:
            raise ValueError("DENIED_REVIEW_MUST_NOT_BE_ALLOWED")
        if self.status != ControlledToolExpansionReviewStatus.denied and not self.review_allowed:
            raise ValueError("REVIEW_STATUS_MUST_BE_REVIEW_ALLOWED")
        return self


def validate_controlled_tool_expansion_policy(
    policy: ControlledToolExpansionPolicy,
) -> ControlledToolExpansionPolicy:
    validated = ControlledToolExpansionPolicy.model_validate(policy.model_dump())
    _assert_policy_runtime_flags_denied(validated)
    return validated


def validate_controlled_tool_expansion_candidate(
    candidate: ControlledToolExpansionCandidate,
) -> ControlledToolExpansionCandidate:
    validated = ControlledToolExpansionCandidate.model_validate(candidate.model_dump())
    _assert_candidate_authority_and_raw_fields_denied(validated)
    return validated


def evaluate_controlled_tool_expansion_candidate(
    candidate: ControlledToolExpansionCandidate,
    policy: ControlledToolExpansionPolicy | None = None,
) -> ControlledToolExpansionDecision:
    active_policy = validate_controlled_tool_expansion_policy(policy or ControlledToolExpansionPolicy())
    active_candidate = validate_controlled_tool_expansion_candidate(candidate)
    if active_candidate.capability_kind == ToolExpansionCapabilityKind.unknown:
        return ControlledToolExpansionDecision(
            decision_ref=f"controlled-tool-expansion-decision:{_ref_suffix(active_candidate.candidate_ref)}",
            candidate_ref=active_candidate.candidate_ref,
            status=ControlledToolExpansionReviewStatus.denied,
            review_allowed=False,
            reason_codes=["UNKNOWN_TOOL_EXPANSION_DENIED"],
            safe_message="Unknown tool expansion categories are denied.",
            receipt_plan=None,
            metadata_refs=[*active_policy.metadata_refs, active_candidate.candidate_ref],
        )

    receipt_plan = ControlledToolExpansionReceiptPlan(
        receipt_plan_ref=f"controlled-tool-expansion-receipt:{_ref_suffix(active_candidate.candidate_ref)}",
        candidate_ref=active_candidate.candidate_ref,
        safe_summary="M53 records metadata-only review with no enablement.",
        metadata_refs=[*active_policy.metadata_refs, active_candidate.candidate_ref],
    )
    if active_candidate.capability_kind == ToolExpansionCapabilityKind.safe_metadata_review:
        return ControlledToolExpansionDecision(
            decision_ref=f"controlled-tool-expansion-decision:{_ref_suffix(active_candidate.candidate_ref)}",
            candidate_ref=active_candidate.candidate_ref,
            status=ControlledToolExpansionReviewStatus.review_ready,
            review_allowed=True,
            future_milestone_required=False,
            reason_codes=["M53_REVIEW_ONLY"],
            safe_message="M53 metadata-only review is ready.",
            receipt_plan=receipt_plan,
            metadata_refs=[*active_policy.metadata_refs, active_candidate.candidate_ref],
        )

    return ControlledToolExpansionDecision(
        decision_ref=f"controlled-tool-expansion-decision:{_ref_suffix(active_candidate.candidate_ref)}",
        candidate_ref=active_candidate.candidate_ref,
        status=ControlledToolExpansionReviewStatus.future_milestone,
        review_allowed=True,
        future_milestone_required=True,
        reason_codes=["M53_REVIEW_ONLY", "FUTURE_MILESTONE_REQUIRED"],
        safe_message="Future capability requires a later reviewed milestone.",
        receipt_plan=receipt_plan,
        metadata_refs=[*active_policy.metadata_refs, active_candidate.candidate_ref],
    )


def _require_nonempty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")


def _validate_m53_ref(value: str, field_name: str) -> None:
    _require_nonempty(value, field_name)
    if value != "none" and not M53_SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name} must be a structured safe ref")


def _assert_policy_runtime_flags_denied(policy: ControlledToolExpansionPolicy) -> None:
    if not policy.review_only or not policy.planning_only:
        raise ValueError("M53_REVIEW_ONLY_REQUIRED")
    blocked_fields = [
        ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("subprocess_execution_enabled", "SUBPROCESS_EXECUTION_DENIED"),
        ("unrestricted_network_tools_enabled", "UNRESTRICTED_NETWORK_TOOL_DENIED"),
        ("provider_model_calls_enabled", "PROVIDER_MODEL_CALL_DENIED"),
        ("model_authority_enabled", "MODEL_AUTHORITY_DENIED"),
        ("browser_automation_execution_enabled", "BROWSER_AUTOMATION_EXECUTION_DENIED"),
        ("plugin_enablement_enabled", "PLUGIN_ENABLEMENT_DENIED"),
        ("mobile_sensor_access_enabled", "MOBILE_SENSOR_ACCESS_DENIED"),
        ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
        ("raw_file_browsing_enabled", "RAW_FILE_BROWSING_DENIED"),
        ("raw_file_export_enabled", "RAW_FILE_EXPORT_DENIED"),
        ("full_file_read_enabled", "FULL_FILE_READ_DENIED"),
        ("file_mutation_enabled", "FILE_MUTATION_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("credentials_cookie_handling_enabled", "CREDENTIALS_COOKIE_HANDLING_DENIED"),
        ("external_saas_analytics_sdk_enabled", "EXTERNAL_SAAS_ANALYTICS_SDK_DENIED"),
        ("backend_routes_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_controls_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependencies_added", "DEPENDENCY_ADDITION_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("m54_implemented", "M54_IMPLEMENTATION_DENIED"),
    ]
    for field_name, reason in blocked_fields:
        if getattr(policy, field_name):
            raise ValueError(reason)


def _assert_candidate_authority_and_raw_fields_denied(candidate: ControlledToolExpansionCandidate) -> None:
    if candidate.approval_ref:
        raise ValueError("APPROVAL_REF_NOT_AUTHORITY")
    for field_name, reason in [
        ("execution_requested", "TOOL_EXPANSION_EXECUTION_DENIED"),
        ("tool_enablement_requested", "TOOL_ENABLEMENT_DENIED"),
        ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
        ("contains_raw_prompt", "RAW_PROMPT_DENIED"),
        ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_DENIED"),
        ("contains_raw_tool_payload", "RAW_TOOL_PAYLOAD_DENIED"),
        ("contains_secret_like_content", "SECRET_LIKE_CONTENT_DENIED"),
    ]:
        if getattr(candidate, field_name):
            raise ValueError(reason)


def _ref_suffix(value: str) -> str:
    return value.split(":", 1)[1].replace("/", "-").replace("@", "-")
