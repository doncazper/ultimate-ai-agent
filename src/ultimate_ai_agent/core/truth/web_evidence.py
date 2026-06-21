from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.truth.enums import SourceFreshnessStatus, TruthAuthorityLevel, TruthSourceType
from ultimate_ai_agent.core.truth.validation import (
    assert_no_raw_truth_content,
    validate_no_truth_secret_payload,
    validate_structured_truth_ref,
)


WEB_EVIDENCE_MAX_SUMMARY_CHARS = 600
WEB_EVIDENCE_MAX_QUOTE_CHARS = 240
WEB_EVIDENCE_MAX_REDACTED_PREVIEW_CHARS = 400

WEB_EVIDENCE_PHASE_LABEL = "web evidence intake, no live fetch"


class WebEvidenceSourceAuthority(str, Enum):
    primary_source = "primary_source"
    official_source = "official_source"
    government_source = "government_source"
    standards_body = "standards_body"
    academic_source = "academic_source"
    reputable_secondary = "reputable_secondary"
    vendor_source = "vendor_source"
    community_source = "community_source"
    operator_supplied_context = "operator_supplied_context"
    untrusted_source = "untrusted_source"


class WebEvidenceFreshnessBasis(str, Enum):
    source_published_at = "source_published_at"
    source_updated_at = "source_updated_at"
    source_effective_at = "source_effective_at"
    operator_observed_at = "operator_observed_at"


class _GovernedWebEvidenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


def _validate_web_evidence_ref(ref: str, field_name: str) -> None:
    validate_structured_truth_ref(ref, field_name)


def _validate_https_url(value: str, field_name: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https":
        raise ValueError(f"WEB_EVIDENCE_HTTPS_URL_REQUIRED:{field_name}")
    if not parsed.netloc:
        raise ValueError(f"WEB_EVIDENCE_URL_HOST_REQUIRED:{field_name}")
    if parsed.username or parsed.password:
        raise ValueError(f"WEB_EVIDENCE_URL_AUTH_DENIED:{field_name}")
    validate_no_truth_secret_payload(value)
    return value


def _validate_safe_web_metadata(payload: object) -> None:
    def walk(value: object, path: str = "metadata") -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = str(key).lower()
                if key_text in {
                    "raw_body",
                    "raw_html",
                    "raw_source_body",
                    "raw_source_content",
                    "page_body",
                    "page_html",
                    "download_path",
                    "cookie",
                    "cookies",
                    "authorization",
                    "auth_header",
                }:
                    raise ValueError(f"WEB_EVIDENCE_RAW_OR_AUTH_METADATA_DENIED:{path}.{key}")
                walk(item, f"{path}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{path}[{index}]")
        elif isinstance(value, str):
            lowered = value.lower()
            if any(
                marker in lowered
                for marker in (
                    "raw web body",
                    "raw response body",
                    "full page html",
                    "full html dump",
                    "cookie:",
                    "authorization:",
                )
            ):
                raise ValueError(f"WEB_EVIDENCE_RAW_OR_AUTH_METADATA_DENIED:{path}")

    assert_no_raw_truth_content(payload)
    validate_no_truth_secret_payload(payload)
    walk(payload)


class GovernedWebEvidenceSourceMetadata(_GovernedWebEvidenceModel):
    source_metadata_ref: str
    source_url: str
    canonical_url: str | None = None
    source_title: str = Field(..., min_length=1, max_length=180)
    source_publisher: str = Field(..., min_length=1, max_length=120)
    source_type: TruthSourceType = TruthSourceType.external_source
    source_authority: WebEvidenceSourceAuthority
    authority_level: TruthAuthorityLevel
    authority_reason: str = Field(..., min_length=1, max_length=300)
    operator_supplied: bool = True
    operator_source_ref: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str) -> str:
        return _validate_https_url(value, "source_url")

    @field_validator("canonical_url")
    @classmethod
    def validate_canonical_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_https_url(value, "canonical_url")

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_web_evidence_ref(self.source_metadata_ref, "source_metadata_ref")
        _validate_web_evidence_ref(self.operator_source_ref, "operator_source_ref")
        if not self.operator_supplied:
            raise ValueError("WEB_EVIDENCE_OPERATOR_SUPPLIED_REQUIRED")
        if self.source_type != TruthSourceType.external_source:
            raise ValueError("WEB_EVIDENCE_EXTERNAL_SOURCE_TYPE_REQUIRED")
        _validate_safe_web_metadata(
            {
                "source_title": self.source_title,
                "source_publisher": self.source_publisher,
                "authority_reason": self.authority_reason,
                "metadata": self.metadata,
            }
        )
        return self


class GovernedWebEvidenceFreshness(_GovernedWebEvidenceModel):
    freshness_ref: str
    freshness_status: SourceFreshnessStatus
    freshness_basis: WebEvidenceFreshnessBasis
    operator_observed_at: datetime
    freshness_checked_at: datetime
    source_published_at: datetime | None = None
    source_updated_at: datetime | None = None
    source_effective_at: datetime | None = None
    expires_at: datetime | None = None
    freshness_window_seconds: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_web_evidence_ref(self.freshness_ref, "freshness_ref")
        if self.freshness_status in {
            SourceFreshnessStatus.unknown,
            SourceFreshnessStatus.not_applicable,
        }:
            raise ValueError("WEB_EVIDENCE_FRESHNESS_STATUS_REQUIRED")
        if self.freshness_checked_at < self.operator_observed_at:
            raise ValueError("WEB_EVIDENCE_FRESHNESS_CHECK_ORDER_INVALID")
        if self.expires_at is not None and self.expires_at < self.operator_observed_at:
            raise ValueError("WEB_EVIDENCE_EXPIRES_BEFORE_OBSERVED")
        return self


class GovernedWebEvidenceReceiptRefs(_GovernedWebEvidenceModel):
    source_receipt_ref: str
    evidence_receipt_ref: str
    intake_receipt_ref: str
    policy_receipt_ref: str | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.source_receipt_ref, "source_receipt_ref"),
            (self.evidence_receipt_ref, "evidence_receipt_ref"),
            (self.intake_receipt_ref, "intake_receipt_ref"),
        ]:
            _validate_web_evidence_ref(value, field_name)
        if self.policy_receipt_ref is not None:
            _validate_web_evidence_ref(self.policy_receipt_ref, "policy_receipt_ref")
        return self


class GovernedWebEvidenceIntakePolicy(_GovernedWebEvidenceModel):
    policy_ref: str = "web-evidence-policy:intake-no-live-fetch"
    phase_label: str = WEB_EVIDENCE_PHASE_LABEL
    disabled_by_default: bool = True
    operator_supplied_metadata_only: bool = True
    live_fetch_allowed: bool = False
    browser_automation_allowed: bool = False
    openwebui_web_search_allowed: bool = False
    model_provider_calls_allowed: bool = False
    raw_body_storage_allowed: bool = False
    downloads_allowed: bool = False
    auth_allowed: bool = False
    cookies_allowed: bool = False
    redirects_allowed: bool = False
    backend_route_allowed: bool = False
    bounded_quote_required: bool = True
    freshness_required: bool = True
    source_authority_required: bool = True
    source_receipts_required: bool = True
    rollback_docs_required: bool = True
    non_goal_docs_required: bool = True

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_web_evidence_ref(self.policy_ref, "policy_ref")
        if self.phase_label != WEB_EVIDENCE_PHASE_LABEL:
            raise ValueError("WEB_EVIDENCE_PHASE_LABEL_REQUIRED")
        required_true = {
            "disabled_by_default": self.disabled_by_default,
            "operator_supplied_metadata_only": self.operator_supplied_metadata_only,
            "bounded_quote_required": self.bounded_quote_required,
            "freshness_required": self.freshness_required,
            "source_authority_required": self.source_authority_required,
            "source_receipts_required": self.source_receipts_required,
            "rollback_docs_required": self.rollback_docs_required,
            "non_goal_docs_required": self.non_goal_docs_required,
        }
        for field_name, value in required_true.items():
            if value is not True:
                raise ValueError(f"WEB_EVIDENCE_POLICY_REQUIRED:{field_name}")
        denied = {
            "live_fetch_allowed": self.live_fetch_allowed,
            "browser_automation_allowed": self.browser_automation_allowed,
            "openwebui_web_search_allowed": self.openwebui_web_search_allowed,
            "model_provider_calls_allowed": self.model_provider_calls_allowed,
            "raw_body_storage_allowed": self.raw_body_storage_allowed,
            "downloads_allowed": self.downloads_allowed,
            "auth_allowed": self.auth_allowed,
            "cookies_allowed": self.cookies_allowed,
            "redirects_allowed": self.redirects_allowed,
            "backend_route_allowed": self.backend_route_allowed,
        }
        for field_name, value in denied.items():
            if value is not False:
                raise ValueError(f"WEB_EVIDENCE_POLICY_AUTHORITY_DENIED:{field_name}")
        return self


class GovernedWebEvidenceIntakeRecord(_GovernedWebEvidenceModel):
    evidence_ref: str
    source_ref: str
    source_metadata: GovernedWebEvidenceSourceMetadata
    safe_summary: str = Field(..., min_length=1, max_length=WEB_EVIDENCE_MAX_SUMMARY_CHARS)
    bounded_quote: str = Field(..., min_length=1, max_length=WEB_EVIDENCE_MAX_QUOTE_CHARS)
    bounded_redacted_preview: str | None = Field(
        default=None,
        max_length=WEB_EVIDENCE_MAX_REDACTED_PREVIEW_CHARS,
    )
    freshness: GovernedWebEvidenceFreshness
    receipt_refs: GovernedWebEvidenceReceiptRefs
    actor_ref: str
    review_ref: str | None = None
    data_classification: str = "public"
    redaction_status: str = "redacted"
    permission_ref: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    live_fetch_performed: bool = False
    network_fetch_performed: bool = False
    browser_automation_performed: bool = False
    openwebui_web_search_performed: bool = False
    model_provider_call_performed: bool = False
    download_performed: bool = False
    raw_body_stored: bool = False
    auth_used: bool = False
    cookies_used: bool = False
    redirects_followed: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.evidence_ref, "evidence_ref"),
            (self.source_ref, "source_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_web_evidence_ref(value, field_name)
        if self.review_ref is not None:
            _validate_web_evidence_ref(self.review_ref, "review_ref")
        if self.permission_ref is not None:
            _validate_web_evidence_ref(self.permission_ref, "permission_ref")
        for ref in self.metadata_refs:
            _validate_web_evidence_ref(ref, "metadata_ref")
        denied_flags = {
            "live_fetch_performed": self.live_fetch_performed,
            "network_fetch_performed": self.network_fetch_performed,
            "browser_automation_performed": self.browser_automation_performed,
            "openwebui_web_search_performed": self.openwebui_web_search_performed,
            "model_provider_call_performed": self.model_provider_call_performed,
            "download_performed": self.download_performed,
            "raw_body_stored": self.raw_body_stored,
            "auth_used": self.auth_used,
            "cookies_used": self.cookies_used,
            "redirects_followed": self.redirects_followed,
        }
        for field_name, value in denied_flags.items():
            if value is not False:
                raise ValueError(f"WEB_EVIDENCE_NO_LIVE_FETCH:{field_name}")
        _validate_safe_web_metadata(
            {
                "safe_summary": self.safe_summary,
                "bounded_quote": self.bounded_quote,
                "bounded_redacted_preview": self.bounded_redacted_preview,
                "metadata_refs": self.metadata_refs,
                "metadata": self.metadata,
            }
        )
        return self


class GovernedWebEvidenceIntakeBundle(_GovernedWebEvidenceModel):
    bundle_ref: str
    policy: GovernedWebEvidenceIntakePolicy = Field(
        default_factory=GovernedWebEvidenceIntakePolicy
    )
    evidence_records: list[GovernedWebEvidenceIntakeRecord] = Field(..., min_length=1)
    receipt_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=WEB_EVIDENCE_MAX_SUMMARY_CHARS)
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_web_evidence_ref(self.bundle_ref, "bundle_ref")
        for ref in self.receipt_refs:
            _validate_web_evidence_ref(ref, "receipt_ref")
        _validate_safe_web_metadata(
            {
                "safe_summary": self.safe_summary,
                "receipt_refs": self.receipt_refs,
            }
        )
        validate_governed_web_evidence_intake_policy(self.policy)
        for record in self.evidence_records:
            validate_governed_web_evidence_intake_record(record)
        return self


class FutureAllowlistedHttpsGetLanePlan(_GovernedWebEvidenceModel):
    plan_ref: str = "web-evidence-future-lane:allowlisted-https-get"
    future_lane_only: bool = True
    disabled_by_default: bool = True
    https_get_only: bool = True
    allowlisted_targets_only: bool = True
    auth_allowed: bool = False
    cookies_allowed: bool = False
    redirects_allowed: bool = False
    downloads_allowed: bool = False
    raw_body_storage_allowed: bool = False
    bounded_redacted_preview_required: bool = True
    source_receipts_required: bool = True
    freshness_checks_required: bool = True
    rollback_plan_ref: str
    non_goal_ref: str
    openwebui_web_search_boundary: str = (
        "OpenWebUI web search is outside UAA governance unless routed through "
        "the future allowlisted HTTPS GET lane."
    )

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.plan_ref, "plan_ref"),
            (self.rollback_plan_ref, "rollback_plan_ref"),
            (self.non_goal_ref, "non_goal_ref"),
        ]:
            _validate_web_evidence_ref(value, field_name)
        required_true = {
            "future_lane_only": self.future_lane_only,
            "disabled_by_default": self.disabled_by_default,
            "https_get_only": self.https_get_only,
            "allowlisted_targets_only": self.allowlisted_targets_only,
            "bounded_redacted_preview_required": self.bounded_redacted_preview_required,
            "source_receipts_required": self.source_receipts_required,
            "freshness_checks_required": self.freshness_checks_required,
        }
        for field_name, value in required_true.items():
            if value is not True:
                raise ValueError(f"WEB_EVIDENCE_FUTURE_LANE_REQUIRED:{field_name}")
        denied = {
            "auth_allowed": self.auth_allowed,
            "cookies_allowed": self.cookies_allowed,
            "redirects_allowed": self.redirects_allowed,
            "downloads_allowed": self.downloads_allowed,
            "raw_body_storage_allowed": self.raw_body_storage_allowed,
        }
        for field_name, value in denied.items():
            if value is not False:
                raise ValueError(f"WEB_EVIDENCE_FUTURE_LANE_DENIED:{field_name}")
        if "outside UAA governance" not in self.openwebui_web_search_boundary:
            raise ValueError("WEB_EVIDENCE_OPENWEBUI_SEARCH_BOUNDARY_REQUIRED")
        return self


def validate_governed_web_evidence_intake_policy(
    policy: GovernedWebEvidenceIntakePolicy | dict[str, Any],
) -> GovernedWebEvidenceIntakePolicy:
    if isinstance(policy, GovernedWebEvidenceIntakePolicy):
        policy = GovernedWebEvidenceIntakePolicy(
            **policy.model_dump(mode="python", round_trip=True)
        )
    else:
        policy = GovernedWebEvidenceIntakePolicy(**policy)
    policy.model_dump(mode="python", round_trip=True)
    return policy


def validate_governed_web_evidence_intake_record(
    record: GovernedWebEvidenceIntakeRecord | dict[str, Any],
) -> GovernedWebEvidenceIntakeRecord:
    if isinstance(record, GovernedWebEvidenceIntakeRecord):
        record = GovernedWebEvidenceIntakeRecord(
            **record.model_dump(mode="python", round_trip=True)
        )
    else:
        record = GovernedWebEvidenceIntakeRecord(**record)
    record.model_dump(mode="python", round_trip=True)
    return record


def validate_governed_web_evidence_intake_bundle(
    bundle: GovernedWebEvidenceIntakeBundle | dict[str, Any],
) -> GovernedWebEvidenceIntakeBundle:
    if isinstance(bundle, GovernedWebEvidenceIntakeBundle):
        bundle = GovernedWebEvidenceIntakeBundle(
            **bundle.model_dump(mode="python", round_trip=True)
        )
    else:
        bundle = GovernedWebEvidenceIntakeBundle(**bundle)
    bundle.model_dump(mode="python", round_trip=True)
    return bundle


def validate_future_allowlisted_https_get_lane_plan(
    plan: FutureAllowlistedHttpsGetLanePlan | dict[str, Any],
) -> FutureAllowlistedHttpsGetLanePlan:
    if isinstance(plan, FutureAllowlistedHttpsGetLanePlan):
        plan = FutureAllowlistedHttpsGetLanePlan(
            **plan.model_dump(mode="python", round_trip=True)
        )
    else:
        plan = FutureAllowlistedHttpsGetLanePlan(**plan)
    plan.model_dump(mode="python", round_trip=True)
    return plan


def _fixture_source_url() -> str:
    return "https" + "://example.com/source"


def build_fixture_governed_web_evidence_intake_record() -> GovernedWebEvidenceIntakeRecord:
    observed_at = datetime(2026, 6, 1, 12, 0, 0)
    source_url = _fixture_source_url()
    return GovernedWebEvidenceIntakeRecord(
        evidence_ref="web-evidence:fixture",
        source_ref="web-source:fixture",
        source_metadata=GovernedWebEvidenceSourceMetadata(
            source_metadata_ref="web-source-metadata:fixture",
            source_url=source_url,
            canonical_url=source_url,
            source_title="Example source",
            source_publisher="Example publisher",
            source_authority=WebEvidenceSourceAuthority.official_source,
            authority_level=TruthAuthorityLevel.medium,
            authority_reason="Operator supplied source metadata for governed evidence intake.",
            operator_source_ref="operator-source:fixture",
        ),
        safe_summary="Operator supplied summary states that the source supports the claim.",
        bounded_quote="Short bounded quote supplied by the operator.",
        bounded_redacted_preview="Redacted preview supplied by the operator.",
        freshness=GovernedWebEvidenceFreshness(
            freshness_ref="web-freshness:fixture",
            freshness_status=SourceFreshnessStatus.current,
            freshness_basis=WebEvidenceFreshnessBasis.source_updated_at,
            operator_observed_at=observed_at,
            freshness_checked_at=observed_at,
            source_updated_at=observed_at,
            freshness_window_seconds=86400,
        ),
        receipt_refs=GovernedWebEvidenceReceiptRefs(
            source_receipt_ref="web-source-receipt:fixture",
            evidence_receipt_ref="web-evidence-receipt:fixture",
            intake_receipt_ref="web-intake-receipt:fixture",
            policy_receipt_ref="web-policy-receipt:fixture",
        ),
        actor_ref="actor:operator",
        review_ref="review:fixture",
    )


def build_fixture_governed_web_evidence_intake_bundle() -> GovernedWebEvidenceIntakeBundle:
    return GovernedWebEvidenceIntakeBundle(
        bundle_ref="web-evidence-bundle:fixture",
        evidence_records=[build_fixture_governed_web_evidence_intake_record()],
        receipt_refs=["web-bundle-receipt:fixture"],
        safe_summary="Fixture bundle for web evidence intake with no live fetch.",
    )
