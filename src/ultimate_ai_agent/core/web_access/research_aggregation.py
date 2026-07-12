"""Pure, bounded aggregation of already-governed web evidence.

This module performs no retrieval.  It normalizes injected observations from
the exact WEB-HYBRID lanes into safe citations and provider posture.  The
result remains untrusted evidence and cannot grant context, memory, or action
authority.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret

from .firecrawl_cloud import FIRECRAWL_CLOUD_ADAPTER_REF
from .firecrawl_markdown import FIRECRAWL_MARKDOWN_ADAPTER_REF
from .hybrid_contracts import WebProviderTransportStatus, stable_web_hybrid_ref
from .hybrid_execution import HybridMarkdownExecutionResult
from .searxng_search import SearxngSearchExecutionResult


_SAFE_CODE = re.compile(r"^[A-Z][A-Z0-9_]{0,159}$")
_URL = re.compile(r"(?i)\b(?:https?|file)://\S+")
_LOCAL_PATH = re.compile(r"(?:^|\s)(?:/Users/|/home/|[A-Za-z]:\\)")
_IDENTITY_OR_HOST = re.compile(
    r"(?i)(?:\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|"
    r"\b(?:[A-Z0-9-]+\.)+(?:local|internal|invalid|com|net|org|io|dev)\b)"
)


class WebResearchProviderReadiness(StrEnum):
    ready = "ready"
    degraded = "degraded"
    unavailable = "unavailable"
    stale = "stale"
    blocked = "blocked"
    unknown = "unknown"


class WebResearchCostPosture(StrEnum):
    not_metered = "not_metered"
    free_plan_within_budget = "free_plan_within_budget"
    exhausted = "exhausted"
    blocked = "blocked"
    unknown = "unknown"


class WebResearchRedactionStatus(StrEnum):
    safe_summary_only = "safe_summary_only"
    content_redacted = "content_redacted"


class WebResearchSafeDisableStatus(StrEnum):
    inactive = "inactive"
    active = "active"
    unknown = "unknown"


class _ResearchModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


class WebResearchProviderObservation(_ResearchModel):
    observation_ref: str
    provider_ref: str
    adapter_ref: str
    readiness: WebResearchProviderReadiness
    cost_posture: WebResearchCostPosture
    safe_disable_status: WebResearchSafeDisableStatus
    metered: bool
    observed_at: datetime
    expires_at: datetime
    latency_posture_ref: str
    context_posture_ref: str
    routing_posture_ref: str
    budget_decision_ref: str
    budget_ref: str | None = None
    reason_codes: tuple[str, ...] = Field(default=(), max_length=20)
    blocker_codes: tuple[str, ...] = Field(default=(), max_length=20)

    @field_validator(
        "observation_ref",
        "provider_ref",
        "adapter_ref",
        "latency_posture_ref",
        "context_posture_ref",
        "routing_posture_ref",
        "budget_decision_ref",
        "budget_ref",
    )
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        if value is not None:
            _validate_safe_ref(value, "web_research_provider_ref")
        return value

    @field_validator("reason_codes", "blocker_codes")
    @classmethod
    def validate_codes(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _validated_codes(values)

    @field_validator("observed_at", "expires_at")
    @classmethod
    def validate_times(cls, value: datetime) -> datetime:
        return _aware(value)

    @model_validator(mode="after")
    def validate_observation(self) -> "WebResearchProviderObservation":
        if self.expires_at <= self.observed_at:
            raise ValueError("WEB_RESEARCH_PROVIDER_EXPIRY_INVALID")
        if self.metered and self.cost_posture == WebResearchCostPosture.not_metered:
            raise ValueError("WEB_RESEARCH_METERED_COST_POSTURE_INVALID")
        if not self.metered and self.cost_posture != WebResearchCostPosture.not_metered:
            raise ValueError("WEB_RESEARCH_UNMETERED_COST_POSTURE_INVALID")
        if (
            self.metered
            and self.cost_posture == WebResearchCostPosture.free_plan_within_budget
            and self.budget_ref is None
        ):
            raise ValueError("WEB_RESEARCH_METERED_BUDGET_REF_REQUIRED")
        return self


class WebResearchCitationObservation(_ResearchModel):
    citation_ref: str
    source_ref: str
    evidence_ref: str
    audit_ref: str
    provider_ref: str
    adapter_ref: str
    budget_decision_ref: str
    retrieval_ref: str
    provider_observation_ref: str
    safe_summary: str = Field(..., min_length=1, max_length=500)
    relevance_score: int = Field(..., ge=0, le=1000)
    redaction_status: WebResearchRedactionStatus
    summary_is_non_verbatim: Literal[True] = True
    content_untrusted: Literal[True] = True
    not_instruction_authority: Literal[True] = True

    @field_validator(
        "citation_ref",
        "source_ref",
        "evidence_ref",
        "audit_ref",
        "provider_ref",
        "adapter_ref",
        "budget_decision_ref",
        "retrieval_ref",
        "provider_observation_ref",
    )
    @classmethod
    def validate_refs(cls, value: str) -> str:
        _validate_safe_ref(value, "web_research_citation_ref")
        return value

    @field_validator("safe_summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        _validate_safe_summary(value)
        return value


class WebResearchExcludedSource(_ResearchModel):
    source_ref: str
    reason_code: str
    provider_observation_ref: str | None = None

    @field_validator("source_ref", "provider_observation_ref")
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        if value is not None:
            _validate_safe_ref(value, "web_research_excluded_ref")
        return value

    @field_validator("reason_code")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        if not _SAFE_CODE.fullmatch(value):
            raise ValueError("WEB_RESEARCH_EXCLUSION_CODE_UNSAFE")
        return value


class BoundedWebResearchAggregation(_ResearchModel):
    schema_version: Literal["uaa-web-research-aggregation.v1"] = (
        "uaa-web-research-aggregation.v1"
    )
    aggregation_ref: str
    research_task_ref: str
    query_ref: str
    status: Literal["observed", "empty", "blocked"]
    generated_at: datetime
    citations: tuple[WebResearchCitationObservation, ...] = Field(
        default=(), max_length=10
    )
    excluded_sources: tuple[WebResearchExcludedSource, ...] = Field(
        default=(), max_length=100
    )
    provider_observations: tuple[WebResearchProviderObservation, ...] = Field(
        default=(), max_length=10
    )
    citation_count: int = Field(..., ge=0, le=10)
    excluded_count: int = Field(..., ge=0, le=100)
    max_citations: int = Field(..., ge=1, le=10)
    max_summary_chars: int = Field(..., ge=100, le=4_000)
    total_summary_chars: int = Field(..., ge=0, le=4_000)
    reason_codes: tuple[str, ...] = Field(default=(), max_length=20)
    blocker_codes: tuple[str, ...] = Field(default=(), max_length=20)
    content_untrusted: Literal[True] = True
    not_instruction_authority: Literal[True] = True
    context_injection_authorized: Literal[False] = False
    memory_write_authorized: Literal[False] = False
    action_execution_authorized: Literal[False] = False
    provider_output_is_authority: Literal[False] = False
    raw_query_persisted: Literal[False] = False
    raw_page_content_persisted: Literal[False] = False
    raw_provider_payload_persisted: Literal[False] = False
    safe_refs_only: Literal[True] = True

    @field_validator("aggregation_ref", "research_task_ref", "query_ref")
    @classmethod
    def validate_refs(cls, value: str) -> str:
        _validate_safe_ref(value, "web_research_aggregation_ref")
        return value

    @field_validator("reason_codes", "blocker_codes")
    @classmethod
    def validate_codes(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _validated_codes(values)

    @model_validator(mode="after")
    def validate_counts(self) -> "BoundedWebResearchAggregation":
        if self.citation_count != len(self.citations):
            raise ValueError("WEB_RESEARCH_CITATION_COUNT_MISMATCH")
        if self.excluded_count != len(self.excluded_sources):
            raise ValueError("WEB_RESEARCH_EXCLUDED_COUNT_MISMATCH")
        if self.total_summary_chars != sum(
            len(item.safe_summary) for item in self.citations
        ):
            raise ValueError("WEB_RESEARCH_SUMMARY_BUDGET_MISMATCH")
        if self.total_summary_chars > self.max_summary_chars:
            raise ValueError("WEB_RESEARCH_SUMMARY_BUDGET_EXCEEDED")
        if self.status == "observed" and not self.citations:
            raise ValueError("WEB_RESEARCH_OBSERVED_CITATIONS_REQUIRED")
        if self.status != "observed" and self.citations:
            raise ValueError("WEB_RESEARCH_NON_OBSERVED_CITATIONS_DENIED")
        return self


def aggregate_web_research(
    *,
    research_task_ref: str,
    query_ref: str,
    citations: Sequence[WebResearchCitationObservation],
    provider_observations: Sequence[WebResearchProviderObservation],
    excluded_sources: Sequence[WebResearchExcludedSource] = (),
    evaluated_at: datetime | None = None,
    max_citations: int = 5,
    max_summary_chars: int = 2_000,
) -> BoundedWebResearchAggregation:
    """Aggregate deterministic injected observations without retrieving data."""

    _validate_safe_ref(research_task_ref, "web_research_task_ref")
    _validate_safe_ref(query_ref, "web_research_query_ref")
    if not 1 <= max_citations <= 10:
        raise ValueError("WEB_RESEARCH_CITATION_LIMIT_INVALID")
    if not 100 <= max_summary_chars <= 4_000:
        raise ValueError("WEB_RESEARCH_SUMMARY_LIMIT_INVALID")
    if len(citations) > 50:
        raise ValueError("WEB_RESEARCH_INPUT_CITATION_LIMIT_EXCEEDED")
    if len(provider_observations) > 10:
        raise ValueError("WEB_RESEARCH_INPUT_PROVIDER_LIMIT_EXCEEDED")
    if len(excluded_sources) > 100:
        raise ValueError("WEB_RESEARCH_INPUT_EXCLUSION_LIMIT_EXCEEDED")
    if len(excluded_sources) + len(citations) > 100:
        raise ValueError("WEB_RESEARCH_COMBINED_EXCLUSION_LIMIT_EXCEEDED")

    now = _aware(evaluated_at or datetime.now(timezone.utc))
    provider_refs = [item.observation_ref for item in provider_observations]
    if len(provider_refs) != len(set(provider_refs)):
        raise ValueError("WEB_RESEARCH_DUPLICATE_PROVIDER_OBSERVATION_REF")
    citation_refs = [item.citation_ref for item in citations]
    if len(citation_refs) != len(set(citation_refs)):
        raise ValueError("WEB_RESEARCH_DUPLICATE_CITATION_REF")
    normalized_providers = tuple(
        sorted(provider_observations, key=lambda item: item.observation_ref)
    )
    providers = {item.observation_ref: item for item in normalized_providers}
    normalized_exclusions = list(excluded_sources)
    eligible: list[WebResearchCitationObservation] = []
    seen_sources: set[str] = set()
    blockers: list[str] = []

    for citation in sorted(
        citations,
        key=lambda item: (-item.relevance_score, item.source_ref, item.citation_ref),
    ):
        provider = providers.get(citation.provider_observation_ref)
        exclusion = _provider_exclusion_reason(
            provider,
            now=now,
        )
        if provider is not None and citation.adapter_ref != provider.adapter_ref:
            exclusion = "CITATION_PROVIDER_ADAPTER_MISMATCH"
        if provider is not None and citation.provider_ref != provider.provider_ref:
            exclusion = "CITATION_PROVIDER_REF_MISMATCH"
        if (
            provider is not None
            and citation.budget_decision_ref != provider.budget_decision_ref
        ):
            exclusion = "CITATION_BUDGET_DECISION_MISMATCH"
        if citation.source_ref in seen_sources:
            exclusion = "DUPLICATE_SOURCE_REF"
        if exclusion is not None:
            normalized_exclusions.append(
                WebResearchExcludedSource(
                    source_ref=citation.source_ref,
                    reason_code=exclusion,
                    provider_observation_ref=citation.provider_observation_ref,
                )
            )
            blockers.append(exclusion)
            continue
        if len(eligible) >= max_citations:
            normalized_exclusions.append(
                WebResearchExcludedSource(
                    source_ref=citation.source_ref,
                    reason_code="CITATION_COUNT_BUDGET_EXCEEDED",
                    provider_observation_ref=citation.provider_observation_ref,
                )
            )
            continue
        if sum(len(item.safe_summary) for item in eligible) + len(
            citation.safe_summary
        ) > max_summary_chars:
            normalized_exclusions.append(
                WebResearchExcludedSource(
                    source_ref=citation.source_ref,
                    reason_code="SUMMARY_CHARACTER_BUDGET_EXCEEDED",
                    provider_observation_ref=citation.provider_observation_ref,
                )
            )
            continue
        seen_sources.add(citation.source_ref)
        eligible.append(citation)

    status: Literal["observed", "empty", "blocked"]
    status = "observed" if eligible else ("blocked" if blockers else "empty")
    reason_codes = (
        ("CITED_BOUNDED_RESEARCH_AGGREGATED",)
        if eligible
        else ("NO_ELIGIBLE_RESEARCH_CITATIONS",)
    )
    normalized_exclusions = sorted(
        normalized_exclusions,
        key=lambda item: (
            item.source_ref,
            item.reason_code,
            item.provider_observation_ref or "",
        ),
    )
    normalized_payload = {
        "research_task_ref": research_task_ref,
        "query_ref": query_ref,
        "generated_at": now.isoformat(),
        "citations": [item.model_dump(mode="json") for item in eligible],
        "excluded_sources": [
            item.model_dump(mode="json") for item in normalized_exclusions
        ],
        "provider_observations": [
            item.model_dump(mode="json") for item in normalized_providers
        ],
        "max_citations": max_citations,
        "max_summary_chars": max_summary_chars,
        "status": status,
        "reason_codes": reason_codes,
        "blocker_codes": tuple(dict.fromkeys(blockers)),
    }
    aggregation_ref = stable_web_hybrid_ref(
        "web-research-aggregation-ref", normalized_payload
    )
    return BoundedWebResearchAggregation(
        aggregation_ref=aggregation_ref,
        research_task_ref=research_task_ref,
        query_ref=query_ref,
        status=status,
        generated_at=now,
        citations=tuple(eligible),
        excluded_sources=tuple(normalized_exclusions),
        provider_observations=normalized_providers,
        citation_count=len(eligible),
        excluded_count=len(normalized_exclusions),
        max_citations=max_citations,
        max_summary_chars=max_summary_chars,
        total_summary_chars=sum(len(item.safe_summary) for item in eligible),
        reason_codes=reason_codes,
        blocker_codes=tuple(dict.fromkeys(blockers)),
    )


def citations_from_searxng_result(
    result: SearxngSearchExecutionResult,
    *,
    provider_observation_ref: str,
    retrieval_ref: str,
) -> tuple[WebResearchCitationObservation, ...]:
    """Map transient SearXNG evidence into bounded redacted citations."""

    if result.status not in {
        WebProviderTransportStatus.succeeded,
        WebProviderTransportStatus.simulated,
    }:
        return ()
    return tuple(
        WebResearchCitationObservation(
            citation_ref=stable_web_hybrid_ref(
                "web-research-citation-ref",
                {"request_ref": result.request_ref, "source_ref": item.source_ref},
            ),
            source_ref=item.source_ref,
            evidence_ref=stable_web_hybrid_ref(
                "web-research-evidence-ref",
                {
                    "request_ref": result.request_ref,
                    "source_ref": item.source_ref,
                    "response_receipt_hash_ref": (
                        result.transport_receipt.response_receipt_hash_ref
                    ),
                    "title": item.title,
                    "snippet": item.snippet,
                },
            ),
            audit_ref=result.gateway_audit_ref,
            provider_ref=(
                result.invocation_decision.provider_ref or "provider-ref:unknown"
            ),
            adapter_ref=result.invocation_decision.adapter_ref or "adapter-ref:unknown",
            budget_decision_ref=result.transport_receipt.budget_decision_ref,
            retrieval_ref=retrieval_ref,
            provider_observation_ref=provider_observation_ref,
            safe_summary=(
                "Bounded search-result citation; source content remains transient."
            ),
            relevance_score=max(0, 1000 - (index * 10)),
            redaction_status=WebResearchRedactionStatus.content_redacted,
        )
        for index, item in enumerate(result.evidence)
    )


def citation_from_hybrid_result(
    result: HybridMarkdownExecutionResult,
    *,
    provider_observation_ref: str,
    retrieval_ref: str,
) -> WebResearchCitationObservation | None:
    """Map transient hybrid markdown evidence without retaining raw markdown."""

    if result.evidence is None or result.status not in {
        WebProviderTransportStatus.succeeded,
        WebProviderTransportStatus.simulated,
    }:
        return None
    receipt = result.cloud_receipt or result.local_receipt
    if receipt is None:
        return None
    return WebResearchCitationObservation(
        citation_ref=stable_web_hybrid_ref(
            "web-research-citation-ref",
            {"request_ref": result.request_ref, "source_ref": result.evidence.source_ref},
        ),
        source_ref=result.evidence.source_ref,
        evidence_ref=result.evidence.content_hash_ref,
        audit_ref=stable_web_hybrid_ref(
            "web-research-audit-ref",
            {"transport_receipt_ref": receipt.receipt_ref},
        ),
        provider_ref=receipt.provider_ref,
        adapter_ref=(
            FIRECRAWL_CLOUD_ADAPTER_REF
            if result.cloud_receipt is not None
            else FIRECRAWL_MARKDOWN_ADAPTER_REF
        ),
        budget_decision_ref=receipt.budget_decision_ref,
        retrieval_ref=retrieval_ref,
        provider_observation_ref=provider_observation_ref,
        safe_summary=(
            "Bounded extracted-page citation; source content remains transient."
        ),
        relevance_score=1000,
        redaction_status=WebResearchRedactionStatus.content_redacted,
    )


def _provider_exclusion_reason(
    provider: WebResearchProviderObservation | None,
    *,
    now: datetime,
) -> str | None:
    if provider is None:
        return "PROVIDER_OBSERVATION_MISSING"
    if provider.observed_at > now:
        return "PROVIDER_OBSERVATION_FROM_FUTURE"
    if provider.safe_disable_status != WebResearchSafeDisableStatus.inactive:
        return "PROVIDER_SAFE_DISABLE_NOT_INACTIVE"
    if provider.expires_at <= now or provider.readiness == WebResearchProviderReadiness.stale:
        return "PROVIDER_OBSERVATION_STALE"
    if provider.readiness == WebResearchProviderReadiness.degraded:
        return "DEGRADED_USE_POLICY_DECISION_REQUIRED"
    if provider.readiness != WebResearchProviderReadiness.ready:
        return f"PROVIDER_{provider.readiness.value.upper()}"
    if provider.blocker_codes:
        return "PROVIDER_BLOCKER_PRESENT"
    if provider.metered and provider.cost_posture != WebResearchCostPosture.free_plan_within_budget:
        return "METERED_PROVIDER_BUDGET_UNAVAILABLE"
    return None


def _validate_safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)
    if "://" in value or "\\" in value or any(char.isspace() for char in value):
        raise ValueError("WEB_RESEARCH_SAFE_REF_REQUIRED")
    if contains_secret_like(value) or contains_obvious_secret(value):
        raise ValueError("WEB_RESEARCH_SAFE_REF_REQUIRED")


def _validate_safe_summary(value: str) -> None:
    if (
        value != " ".join(value.split())
        or _URL.search(value)
        or _LOCAL_PATH.search(value)
        or _IDENTITY_OR_HOST.search(value)
        or contains_secret_like(value)
        or contains_obvious_secret(value)
    ):
        raise ValueError("WEB_RESEARCH_SAFE_SUMMARY_REQUIRED")


def _validated_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if any(not _SAFE_CODE.fullmatch(value) for value in values):
        raise ValueError("WEB_RESEARCH_CODE_UNSAFE")
    return tuple(dict.fromkeys(values))


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("WEB_RESEARCH_TIMEZONE_REQUIRED")
    return value.astimezone(timezone.utc)
