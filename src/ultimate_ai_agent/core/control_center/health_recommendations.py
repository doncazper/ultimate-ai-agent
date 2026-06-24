from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.time import utc_now


FCC_HEALTH_RECOMMENDATION_CONTRACT_REF = (
    "contract-ref:fcc-health-001:self-healing-recommendations:v1"
)
FCC_HEALTH_RECOMMENDATION_BINDING_CONTRACT_REF = (
    "contract-ref:fcc-health-001:action-inbox-binding:v1"
)
FCC_HEALTH_RECOMMENDATION_ACTION_KIND = "self_heal_recommendation"

FCC_HEALTH_RECOMMENDATION_BLOCKED_AUTHORITY_REFS = [
    "blocked-state:no-auto-code",
    "blocked-state:no-auto-apply",
    "blocked-state:no-background-self-repair",
    "blocked-state:no-scheduler-authority",
    "blocked-state:no-provider-model-call",
    "blocked-state:no-hidden-context-injection",
    "blocked-state:no-connector-write",
    "blocked-state:no-shell-execution",
    "blocked-state:no-action-execution",
    "blocked-state:no-production-authority",
]

_UNSAFE_HUMAN_TEXT_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\braw\s+(?:prompt|response|provider\s+payload|log|logs|local\s+path|source\s+bod(?:y|ies)|content)\b",
        r"\b(?:prompt|response|provider\s+payload|log|logs|source\s+bod(?:y|ies))\s+content\b",
        r"(?<![A-Za-z0-9_.-])(?:/Users/|/home/|/private/var/|[A-Za-z]:\\Users\\)",
    ]
]


RecommendationKind = Literal[
    "verifier_failure",
    "documentation_currentness_drift",
    "route_manifest_mismatch",
    "api_contract_mismatch",
    "frontend_ui_friction",
    "blocked_state_confusion",
    "source_readiness_gap",
    "private_dogfood_feedback",
    "memory_quality_issue",
    "product_language_issue",
    "operational_maturity_gap",
    "release_truth_gap",
]
RecommendationSeverity = Literal["info", "low", "medium", "high"]
RecommendationLifecycleState = Literal[
    "detected",
    "queued_for_review",
    "reviewed_accepted",
    "reviewed_edited",
    "reviewed_rejected",
    "reviewed_deferred",
    "converted_to_task_candidate",
    "converted_to_patch_proposal_candidate",
    "stale",
    "resolved_by_external_evidence",
]


class RecommendationCandidate(BaseModel):
    schema_version: Literal["fcc_health_recommendation.v1"] = (
        "fcc_health_recommendation.v1"
    )
    contract_ref: Literal[
        "contract-ref:fcc-health-001:self-healing-recommendations:v1"
    ] = FCC_HEALTH_RECOMMENDATION_CONTRACT_REF
    recommendation_ref: str = Field(..., min_length=1)
    kind: RecommendationKind
    severity: RecommendationSeverity
    lifecycle_state: RecommendationLifecycleState = "queued_for_review"
    safe_title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=360)
    source_signal_refs: list[str]
    source_surface_refs: list[str]
    source_doc_refs: list[str]
    source_route_refs: list[str]
    source_test_refs: list[str]
    source_verifier_refs: list[str]
    evidence_refs: list[str]
    missing_proof_refs: list[str]
    blocked_authority_refs: list[str]
    owner_ref: str
    scope_ref: str
    impact_ref: str
    validation_plan_refs: list[str]
    rollback_or_safe_disable_refs: list[str]
    expected_receipt_refs: list[str]
    conversion_option_refs: list[str]
    next_safe_action: str = Field(..., min_length=1, max_length=240)
    created_at: str
    updated_at: str
    redaction_status: Literal["safe_refs_only"] = "safe_refs_only"
    auto_code_authorized: bool = False
    auto_apply_authorized: bool = False
    shell_execution_authorized: bool = False
    browser_automation_authorized: bool = False
    connector_write_authorized: bool = False
    connector_read_authorized: bool = False
    memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    provider_model_call_authorized: bool = False
    task_execution_authorized: bool = False
    external_side_effect_authorized: bool = False
    production_authority_enabled: bool = False
    public_release_claim_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _deny_authority_and_unsafe_content(self) -> "RecommendationCandidate":
        denied_flags = [
            "auto_code_authorized",
            "auto_apply_authorized",
            "shell_execution_authorized",
            "browser_automation_authorized",
            "connector_write_authorized",
            "connector_read_authorized",
            "memory_write_authorized",
            "context_injection_authorized",
            "provider_model_call_authorized",
            "task_execution_authorized",
            "external_side_effect_authorized",
            "production_authority_enabled",
            "public_release_claim_enabled",
        ]
        for flag in denied_flags:
            if getattr(self, flag):
                raise ValueError(f"FCC_HEALTH_RECOMMENDATION_AUTHORITY_DENIED:{flag}")
        payload = self.model_dump(mode="json")
        if contains_secret_like(payload):
            raise ValueError("FCC_HEALTH_RECOMMENDATION_SECRET_LIKE_VALUE_REJECTED")
        for field_name in ["safe_title", "safe_summary", "next_safe_action"]:
            value = getattr(self, field_name)
            if any(pattern.search(value) for pattern in _UNSAFE_HUMAN_TEXT_PATTERNS):
                raise ValueError(
                    "FCC_HEALTH_RECOMMENDATION_UNSAFE_HUMAN_TEXT_REJECTED:"
                    f"{field_name}"
                )
        for evidence_ref in self.evidence_refs:
            if "/" in evidence_ref or "\\" in evidence_ref:
                raise ValueError(
                    "FCC_HEALTH_RECOMMENDATION_UNSAFE_EVIDENCE_REF_REJECTED"
                )
        return self


def recommendation_ref_for(
    *,
    kind: str,
    scope_ref: str,
    owner_ref: str,
    source_signal_refs: list[str],
) -> str:
    stable_payload = json.dumps(
        {
            "kind": kind,
            "scope_ref": scope_ref,
            "owner_ref": owner_ref,
            "source_signal_refs": sorted(source_signal_refs),
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(stable_payload.encode("utf-8")).hexdigest()[:16]
    safe_kind = re.sub(r"[^a-z0-9_]+", "-", kind.lower()).strip("-")
    return f"recommendation:fcc-health-001:{safe_kind}:{digest}"


def build_recommendation_candidate(
    *,
    kind: RecommendationKind,
    severity: RecommendationSeverity,
    safe_title: str,
    safe_summary: str,
    source_signal_refs: list[str],
    source_surface_refs: list[str],
    source_doc_refs: list[str],
    source_route_refs: list[str],
    source_test_refs: list[str],
    source_verifier_refs: list[str],
    evidence_refs: list[str],
    missing_proof_refs: list[str],
    owner_ref: str,
    scope_ref: str,
    impact_ref: str,
    validation_plan_refs: list[str],
    rollback_or_safe_disable_refs: list[str],
    next_safe_action: str,
    lifecycle_state: RecommendationLifecycleState = "queued_for_review",
) -> RecommendationCandidate:
    blocked_authority_refs = sorted(set(FCC_HEALTH_RECOMMENDATION_BLOCKED_AUTHORITY_REFS))
    now = utc_now().replace(microsecond=0).isoformat()
    return RecommendationCandidate(
        recommendation_ref=recommendation_ref_for(
            kind=kind,
            scope_ref=scope_ref,
            owner_ref=owner_ref,
            source_signal_refs=source_signal_refs,
        ),
        kind=kind,
        severity=severity,
        lifecycle_state=lifecycle_state,
        safe_title=safe_title,
        safe_summary=safe_summary,
        source_signal_refs=source_signal_refs,
        source_surface_refs=source_surface_refs,
        source_doc_refs=source_doc_refs,
        source_route_refs=source_route_refs,
        source_test_refs=source_test_refs,
        source_verifier_refs=source_verifier_refs,
        evidence_refs=evidence_refs,
        missing_proof_refs=missing_proof_refs,
        blocked_authority_refs=blocked_authority_refs,
        owner_ref=owner_ref,
        scope_ref=scope_ref,
        impact_ref=impact_ref,
        validation_plan_refs=validation_plan_refs,
        rollback_or_safe_disable_refs=rollback_or_safe_disable_refs,
        expected_receipt_refs=[
            "expected-receipt-ref:fcc-health-001:recommendation-review-decision"
        ],
        conversion_option_refs=[
            "conversion-option:fcc-health-001:task-candidate-after-review",
            "conversion-option:fcc-health-001:patch-proposal-candidate-after-review",
        ],
        next_safe_action=next_safe_action,
        created_at=now,
        updated_at=now,
    )


def build_fcc_health_recommendations(
    *,
    source_readiness: dict[str, Any] | None = None,
    dogfood_capture: dict[str, Any] | None = None,
) -> list[RecommendationCandidate]:
    recommendations: list[RecommendationCandidate] = []
    source_readiness = source_readiness or {}
    missing_contract_refs = list(source_readiness.get("missing_contract_refs") or [])
    blocked_authority_refs = list(source_readiness.get("blocked_authority_refs") or [])

    if missing_contract_refs or blocked_authority_refs:
        recommendations.append(
            build_recommendation_candidate(
                kind="source_readiness_gap",
                severity="medium",
                safe_title="Review source readiness gaps",
                safe_summary=(
                    "Source readiness has missing contracts or blocked authority "
                    "refs that should be reviewed before any connector work."
                ),
                source_signal_refs=[*missing_contract_refs[:5], *blocked_authority_refs[:5]],
                source_surface_refs=["surface-ref:inbox", "surface-ref:briefing"],
                source_doc_refs=[
                    "docs/control_center/"
                    "FCC_SOURCES_001_SOURCE_READINESS_DRAFT_ONLY_INPUTS.md"
                ],
                source_route_refs=["GET /control-center/sources/readiness"],
                source_test_refs=["tests/test_control_center_api_routes.py"],
                source_verifier_refs=[
                    "scripts/verify_fcc_sources_001_source_readiness_draft_only_inputs.py"
                ],
                evidence_refs=["evidence-ref:fcc-health-001:source-readiness-gap"],
                missing_proof_refs=missing_contract_refs[:5],
                owner_ref="owner-ref:founder-command-center",
                scope_ref="scope-ref:fcc-health-001:source-readiness",
                impact_ref="impact-ref:operator-trust",
                validation_plan_refs=[
                    "validation-plan-ref:verify-source-readiness",
                    "validation-plan-ref:verify-operational-maturity",
                ],
                rollback_or_safe_disable_refs=[
                    "safe-disable-ref:fcc-health-001:recommendation-review-only"
                ],
                next_safe_action=(
                    "Review source readiness refs before creating connector "
                    "contract work."
                ),
            )
        )

    recommendations.append(
        build_recommendation_candidate(
            kind="documentation_currentness_drift",
            severity="low",
            safe_title="Review documentation currentness refs",
            safe_summary=(
                "Planning and truth docs should be reviewed for currentness "
                "before any active-path wording changes."
            ),
            source_signal_refs=[
                "signal-ref:documentation-integrity:currentness-review",
            ],
            source_surface_refs=["surface-ref:evidence", "surface-ref:settings"],
            source_doc_refs=[
                "README.md",
                "docs/README.md",
                "docs/DOCUMENTATION_INDEX.md",
                "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
            ],
            source_route_refs=[],
            source_test_refs=[],
            source_verifier_refs=["scripts/verify_documentation_integrity.py"],
            evidence_refs=["evidence-ref:fcc-health-001:docs-currentness"],
            missing_proof_refs=[
                "missing-proof-ref:fcc-health-001:human-currentness-review"
            ],
            owner_ref="owner-ref:docs-discipline",
            scope_ref="scope-ref:fcc-health-001:documentation-currentness",
            impact_ref="impact-ref:portfolio-truth",
            validation_plan_refs=[
                "validation-plan-ref:verify-documentation-integrity"
            ],
            rollback_or_safe_disable_refs=[
                "safe-disable-ref:fcc-health-001:recommendation-review-only"
            ],
            next_safe_action=(
                "Review active-path docs and decide whether a scoped docs task "
                "is needed."
            ),
        )
    )

    dogfood_capture = dogfood_capture or {}
    friction_refs = list(dogfood_capture.get("friction_refs") or [])
    if friction_refs:
        recommendations.append(
            build_recommendation_candidate(
                kind="frontend_ui_friction",
                severity="low",
                safe_title="Review private UI friction refs",
                safe_summary=(
                    "Private dogfood friction refs can become UI polish tasks "
                    "only after operator review."
                ),
                source_signal_refs=friction_refs[:6],
                source_surface_refs=["surface-ref:control-center"],
                source_doc_refs=[
                    "docs/control_center/"
                    "FCC_REVIEW_001_EVIDENCE_NARRATIVE_WEEKLY_REVIEW.md"
                ],
                source_route_refs=[],
                source_test_refs=["apps/control-center/src/App.test.tsx"],
                source_verifier_refs=["scripts/verify_control_center_frontend.py"],
                evidence_refs=["evidence-ref:fcc-health-001:ui-friction"],
                missing_proof_refs=[
                    "missing-proof-ref:fcc-health-001:visual-review-before-polish"
                ],
                owner_ref="owner-ref:control-center",
                scope_ref="scope-ref:fcc-health-001:ui-friction",
                impact_ref="impact-ref:operator-usability",
                validation_plan_refs=[
                    "validation-plan-ref:frontend-check",
                    "validation-plan-ref:visual-regression-if-ui-changes",
                ],
                rollback_or_safe_disable_refs=[
                    "safe-disable-ref:fcc-health-001:recommendation-review-only"
                ],
                next_safe_action=(
                    "Review private friction refs before creating a scoped UI "
                    "task candidate."
                ),
            )
        )

    recommendations.append(
        build_recommendation_candidate(
            kind="operational_maturity_gap",
            severity="info",
            safe_title="Review operational maturity proof gaps",
            safe_summary=(
                "Operational maturity gaps should remain recommendation refs until "
                "the missing proof and receipts exist."
            ),
            source_signal_refs=["signal-ref:operational-maturity:proof-gap-review"],
            source_surface_refs=["surface-ref:settings", "surface-ref:evidence"],
            source_doc_refs=["docs/control_center/operational_maturity_manifest.json"],
            source_route_refs=[],
            source_test_refs=["tests/test_operational_maturity_manifest.py"],
            source_verifier_refs=["scripts/verify_operational_maturity.py"],
            evidence_refs=["evidence-ref:fcc-health-001:operational-maturity-gap"],
            missing_proof_refs=[
                "missing-proof-ref:fcc-health-001:rank-promotion-proof"
            ],
            owner_ref="owner-ref:control-center",
            scope_ref="scope-ref:fcc-health-001:operational-maturity",
            impact_ref="impact-ref:authority-ramp-truth",
            validation_plan_refs=["validation-plan-ref:verify-operational-maturity"],
            rollback_or_safe_disable_refs=[
                "safe-disable-ref:fcc-health-001:recommendation-review-only"
            ],
            next_safe_action=(
                "Review maturity proof gaps before changing any rank or authority "
                "claim."
            ),
        )
    )
    return recommendations
