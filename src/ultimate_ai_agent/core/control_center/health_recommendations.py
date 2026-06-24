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


def _bounded_refs(refs: Any, *, limit: int = 6) -> list[str]:
    if refs is None:
        return []
    if isinstance(refs, str):
        values = [refs]
    else:
        try:
            values = list(refs)
        except TypeError:
            values = [refs]
    return [str(ref) for ref in values if str(ref)][:limit]


def build_verifier_failure_recommendation(
    *,
    verifier_refs: list[str],
    test_refs: list[str] | None = None,
    doc_refs: list[str] | None = None,
) -> RecommendationCandidate:
    signal_refs = _bounded_refs(verifier_refs) or [
        "signal-ref:fcc-health-001:verifier-failure-review"
    ]
    return build_recommendation_candidate(
        kind="verifier_failure",
        severity="medium",
        safe_title="Review verifier failure refs",
        safe_summary=(
            "Verifier failure refs can become repair work only after an operator "
            "reviews the missing proof and scoped validation plan."
        ),
        source_signal_refs=signal_refs,
        source_surface_refs=["surface-ref:evidence", "surface-ref:settings"],
        source_doc_refs=_bounded_refs(doc_refs),
        source_route_refs=[],
        source_test_refs=_bounded_refs(test_refs),
        source_verifier_refs=signal_refs,
        evidence_refs=["evidence-ref:fcc-health-001:verifier-failure"],
        missing_proof_refs=[
            "missing-proof-ref:fcc-health-001:verifier-pass-after-review"
        ],
        owner_ref="owner-ref:verification-discipline",
        scope_ref="scope-ref:fcc-health-001:verifier-failure",
        impact_ref="impact-ref:regression-proof",
        validation_plan_refs=["validation-plan-ref:rerun-focused-verifier"],
        rollback_or_safe_disable_refs=[
            "safe-disable-ref:fcc-health-001:recommendation-review-only"
        ],
        next_safe_action=(
            "Inspect verifier refs and decide whether a scoped repair task is needed."
        ),
    )


def build_route_manifest_mismatch_recommendation(
    *,
    route_refs: list[str],
    verifier_refs: list[str] | None = None,
    doc_refs: list[str] | None = None,
) -> RecommendationCandidate:
    signal_refs = _bounded_refs(route_refs) or [
        "route-ref:fcc-health-001:manifest-review"
    ]
    return build_recommendation_candidate(
        kind="route_manifest_mismatch",
        severity="medium",
        safe_title="Review route manifest mismatch refs",
        safe_summary=(
            "Route manifest mismatch refs need contract review before API or "
            "Control Center surface changes."
        ),
        source_signal_refs=signal_refs,
        source_surface_refs=["surface-ref:settings", "surface-ref:evidence"],
        source_doc_refs=_bounded_refs(doc_refs)
        or ["docs/control_center/ROUTE_STATUS_MANIFEST.md"],
        source_route_refs=signal_refs,
        source_test_refs=["tests/test_control_center_api_routes.py"],
        source_verifier_refs=_bounded_refs(verifier_refs)
        or ["scripts/verify_control_center_route_status.py"],
        evidence_refs=["evidence-ref:fcc-health-001:route-manifest-mismatch"],
        missing_proof_refs=[
            "missing-proof-ref:fcc-health-001:route-manifest-contract-proof"
        ],
        owner_ref="owner-ref:control-center-api",
        scope_ref="scope-ref:fcc-health-001:route-manifest",
        impact_ref="impact-ref:route-contract-truth",
        validation_plan_refs=[
            "validation-plan-ref:verify-openapi-contract",
            "validation-plan-ref:test-control-center-api-routes",
        ],
        rollback_or_safe_disable_refs=[
            "safe-disable-ref:fcc-health-001:recommendation-review-only"
        ],
        next_safe_action=(
            "Compare route refs against OpenAPI and manifest docs before filing work."
        ),
    )


def build_api_contract_mismatch_recommendation(
    *,
    route_refs: list[str],
    test_refs: list[str] | None = None,
    verifier_refs: list[str] | None = None,
) -> RecommendationCandidate:
    signal_refs = _bounded_refs(route_refs) or [
        "api-contract-ref:fcc-health-001:openapi-review"
    ]
    return build_recommendation_candidate(
        kind="api_contract_mismatch",
        severity="high",
        safe_title="Review API contract mismatch refs",
        safe_summary=(
            "API contract mismatches must stay as recommendation refs until "
            "OpenAPI, route tests, and typed clients agree."
        ),
        source_signal_refs=signal_refs,
        source_surface_refs=["surface-ref:control-center", "surface-ref:cli"],
        source_doc_refs=["docs/control_center/founder_loop_api_perimeter_manifest.json"],
        source_route_refs=signal_refs,
        source_test_refs=_bounded_refs(test_refs)
        or ["tests/test_control_center_api_routes.py"],
        source_verifier_refs=_bounded_refs(verifier_refs)
        or ["scripts/verify_openapi_contract.py"],
        evidence_refs=["evidence-ref:fcc-health-001:api-contract-mismatch"],
        missing_proof_refs=[
            "missing-proof-ref:fcc-health-001:openapi-route-client-alignment"
        ],
        owner_ref="owner-ref:python-core-api",
        scope_ref="scope-ref:fcc-health-001:api-contract",
        impact_ref="impact-ref:contract-first-control-center",
        validation_plan_refs=[
            "validation-plan-ref:verify-openapi-contract",
            "validation-plan-ref:test-api-manifest",
        ],
        rollback_or_safe_disable_refs=[
            "safe-disable-ref:fcc-health-001:recommendation-review-only"
        ],
        next_safe_action=(
            "Review API contract refs before creating an exact route/client task."
        ),
    )


def build_blocked_state_confusion_recommendation(
    *,
    blocked_state_refs: list[str],
    surface_refs: list[str] | None = None,
) -> RecommendationCandidate:
    signal_refs = _bounded_refs(blocked_state_refs) or [
        "blocked-state:fcc-health-001:operator-confusion-review"
    ]
    return build_recommendation_candidate(
        kind="blocked_state_confusion",
        severity="medium",
        safe_title="Review blocked-state clarity refs",
        safe_summary=(
            "Blocked-state confusion should become wording or state-machine work "
            "only after safe review confirms the exact operator ambiguity."
        ),
        source_signal_refs=signal_refs,
        source_surface_refs=_bounded_refs(surface_refs)
        or ["surface-ref:actions", "surface-ref:evidence"],
        source_doc_refs=["docs/control_center/PRODUCT_LANGUAGE_RULES.md"],
        source_route_refs=[],
        source_test_refs=["apps/control-center/src/App.test.tsx"],
        source_verifier_refs=["scripts/verify_control_center_frontend.py"],
        evidence_refs=["evidence-ref:fcc-health-001:blocked-state-confusion"],
        missing_proof_refs=[
            "missing-proof-ref:fcc-health-001:operator-state-copy-review"
        ],
        owner_ref="owner-ref:operator-experience",
        scope_ref="scope-ref:fcc-health-001:blocked-state-clarity",
        impact_ref="impact-ref:operator-trust",
        validation_plan_refs=[
            "validation-plan-ref:frontend-copy-test",
            "validation-plan-ref:product-language-check",
        ],
        rollback_or_safe_disable_refs=[
            "safe-disable-ref:fcc-health-001:recommendation-review-only"
        ],
        next_safe_action=(
            "Review blocked-state refs before drafting a scoped UX or copy task."
        ),
    )


def build_memory_quality_issue_recommendation(
    *,
    memory_signal_refs: list[str],
    evidence_refs: list[str] | None = None,
) -> RecommendationCandidate:
    signal_refs = _bounded_refs(memory_signal_refs) or [
        "memory-quality-ref:fcc-health-001:review-needed"
    ]
    return build_recommendation_candidate(
        kind="memory_quality_issue",
        severity="medium",
        safe_title="Review memory quality and maintenance refs",
        safe_summary=(
            "Memory quality and maintenance refs can become review tasks only; "
            "they do not write memory, inject context, or treat recall as authority."
        ),
        source_signal_refs=signal_refs,
        source_surface_refs=[
            "surface-ref:memory",
            "surface-ref:actions",
            "surface-ref:evidence",
        ],
        source_doc_refs=[
            "docs/control_center/"
            "FCC_MEM_016_020_MEMORY_DIAGNOSTICS_CITATIONS_FEEDBACK_MAINTENANCE_CONTEXT.md",
            "docs/control_center/FCC_MEM_021_MEMORY_READ_MODELS_UI_ACTION_INBOX_BRIDGE.md",
        ],
        source_route_refs=[
            "GET /control-center/memory/quality-issues",
            "GET /control-center/memory/maintenance-runs",
            "GET /control-center/actions/inbox",
        ],
        source_test_refs=[
            "tests/test_fcc_mem_016_020_memory_diagnostics.py",
            "tests/test_fcc_mem_021_memory_ui_action_inbox_bridge.py",
        ],
        source_verifier_refs=[
            "scripts/verify_fcc_mem_021_memory_ui_action_inbox_bridge.py"
        ],
        evidence_refs=_bounded_refs(evidence_refs)
        or [
            "evidence-ref:fcc-health-001:memory-quality",
            "evidence-ref:fcc-mem-021:memory-proposal-bridge",
        ],
        missing_proof_refs=[
            "missing-proof-ref:fcc-mem-021:operator-quality-review",
            "missing-proof-ref:fcc-mem-021:no-auto-maintenance",
        ],
        owner_ref="owner-ref:memory-governance",
        scope_ref="scope-ref:fcc-health-001:memory-quality",
        impact_ref="impact-ref:memory-trust",
        validation_plan_refs=[
            "validation-plan-ref:fcc-mem-021-action-inbox-proposal-only",
            "validation-plan-ref:fcc-mem-021-context-use-remains-blocked",
        ],
        rollback_or_safe_disable_refs=[
            "safe-disable-ref:fcc-health-001:recommendation-review-only",
            "safe-disable-ref:fcc-mem-021:disable-memory-proposal-bridge",
        ],
        next_safe_action=(
            "Review memory quality and maintenance refs before creating a memory task."
        ),
    )


def build_release_truth_gap_recommendation(
    *,
    signal_refs: list[str],
    doc_refs: list[str] | None = None,
) -> RecommendationCandidate:
    bounded_signal_refs = _bounded_refs(signal_refs) or [
        "release-truth-ref:fcc-health-001:proof-gap"
    ]
    return build_recommendation_candidate(
        kind="release_truth_gap",
        severity="medium",
        safe_title="Review release truth gap refs",
        safe_summary=(
            "Release truth gaps must stay review-only until implemented, partial, "
            "blocked, and missing states are reconciled with evidence."
        ),
        source_signal_refs=bounded_signal_refs,
        source_surface_refs=["surface-ref:evidence", "surface-ref:settings"],
        source_doc_refs=_bounded_refs(doc_refs)
        or ["docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"],
        source_route_refs=[],
        source_test_refs=[],
        source_verifier_refs=["scripts/verify_documentation_integrity.py"],
        evidence_refs=["evidence-ref:fcc-health-001:release-truth-gap"],
        missing_proof_refs=[
            "missing-proof-ref:fcc-health-001:release-truth-evidence-review"
        ],
        owner_ref="owner-ref:release-truth",
        scope_ref="scope-ref:fcc-health-001:release-truth",
        impact_ref="impact-ref:portfolio-truth",
        validation_plan_refs=[
            "validation-plan-ref:verify-documentation-integrity",
            "validation-plan-ref:product-language-check",
        ],
        rollback_or_safe_disable_refs=[
            "safe-disable-ref:fcc-health-001:recommendation-review-only"
        ],
        next_safe_action=(
            "Review release truth refs before changing product-readiness claims."
        ),
    )


def build_fcc_health_recommendations(
    *,
    source_readiness: dict[str, Any] | None = None,
    dogfood_capture: dict[str, Any] | None = None,
    verifier_failure_refs: list[str] | None = None,
    route_manifest_mismatch_refs: list[str] | None = None,
    api_contract_mismatch_refs: list[str] | None = None,
    blocked_state_confusion_refs: list[str] | None = None,
    memory_quality_issue_refs: list[str] | None = None,
    release_truth_gap_refs: list[str] | None = None,
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

    if verifier_failure_refs:
        recommendations.append(
            build_verifier_failure_recommendation(
                verifier_refs=verifier_failure_refs,
            )
        )

    if route_manifest_mismatch_refs:
        recommendations.append(
            build_route_manifest_mismatch_recommendation(
                route_refs=route_manifest_mismatch_refs,
            )
        )

    if api_contract_mismatch_refs:
        recommendations.append(
            build_api_contract_mismatch_recommendation(
                route_refs=api_contract_mismatch_refs,
            )
        )

    if blocked_state_confusion_refs:
        recommendations.append(
            build_blocked_state_confusion_recommendation(
                blocked_state_refs=blocked_state_confusion_refs,
            )
        )

    if memory_quality_issue_refs:
        recommendations.append(
            build_memory_quality_issue_recommendation(
                memory_signal_refs=memory_quality_issue_refs,
            )
        )

    if release_truth_gap_refs:
        recommendations.append(
            build_release_truth_gap_recommendation(signal_refs=release_truth_gap_refs)
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
