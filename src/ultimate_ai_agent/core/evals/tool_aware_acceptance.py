from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from enum import Enum
from typing import Literal, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ultimate_ai_agent.core.evals.tool_aware_baseline import (
    TAW00_MANDATORY_CANDIDATE_PATH_REFS,
    CandidateLock,
    SourceDependencyClosure,
    SourceProjection,
    canonical_digest,
    durable_payload_has_forbidden_fields,
    verify_candidate_lock,
    verify_source_dependency_closure,
)
from ultimate_ai_agent.core.execution.validation import validate_execution_ref


TAW08_CONTRACT_REF = "contract-ref:taw08:founder-private-acceptance:v1"
TAW08_EVALUATOR_REF = "evaluator-ref:taw08:deterministic-acceptance:v1"
TAW08_MAX_EVIDENCE_DELTA_ENTRIES = 32
TAW08_MAX_EVIDENCE_DELTA_ARTIFACT_BYTES = 4 * 1024 * 1024
TAW08_MAX_CANDIDATE_PATHS = 1024
TAW08_MAX_CANDIDATE_ARTIFACT_BYTES = 4 * 1024 * 1024
TAW08_MAX_REVISION_PATHS = 8192
# Founder-private acceptance authority. The matching private key is retained
# outside the repository and is never part of durable evaluation evidence.
TAW08_FOUNDER_DECISION_PUBLIC_KEY_HEX: str | None = (
    "9a1ed72c07a95aa395c72e8f3c92e4f5077aa2ab474d03c6b5655a267a7c469c"
)
TAW08_FOUNDATION_GATE_SOURCE_PREFIX = "repo-path-ref:src/ultimate_ai_agent/core/gate/"
TAW08_UNRESOLVED_DYNAMIC_IMPORT_PATH_REFS = (
    "repo-path-ref:src/ultimate_ai_agent/core/capabilities/__init__.py",
    "repo-path-ref:src/ultimate_ai_agent/core/capability_availability/__init__.py",
    "repo-path-ref:src/ultimate_ai_agent/core/extension_catalog/__init__.py",
    "repo-path-ref:src/ultimate_ai_agent/core/"
    "local_model_management/llama_cpp_supervisor.py",
)
TAW08_ACCEPTANCE_REPORT_PATH_REF = (
    "repo-path-ref:docs/evals/tool_aware_cognition_taw08_acceptance_report_v1.json"
)
TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF = (
    "repo-path-ref:docs/evals/"
    "tool_aware_cognition_taw08_final_acceptance_report_v1.json"
)
TAW08_ACTIVE_TRUTH_PATH_REFS = (
    "repo-path-ref:docs/kanban/current_board.md",
    "repo-path-ref:docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
)
TAW08_ALLOWED_EVIDENCE_ONLY_PATH_REFS = tuple(
    sorted(
        (
            TAW08_ACCEPTANCE_REPORT_PATH_REF,
            TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,
            *TAW08_ACTIVE_TRUTH_PATH_REFS,
            "repo-path-ref:docs/evals/tool_aware_cognition_taw08_board_reconciliation_v1.json",
            "repo-path-ref:docs/evals/tool_aware_cognition_taw08_release_truth_reconciliation_v1.json",
        )
    )
)
TAW08_REQUIRED_ENVIRONMENT_PATH_REFS = (
    "repo-path-ref:pyproject.toml",
    "repo-path-ref:uv.lock",
)
TAW08_RECONCILIATION_START = "[//]: # (TAW08-RECONCILIATION:START)"
TAW08_RECONCILIATION_JSON = "[//]: # (TAW08-RECONCILIATION:JSON)"
TAW08_RECONCILIATION_END = "[//]: # (TAW08-RECONCILIATION:END)"
TAW08_RECONCILIATION_NARRATIVES = {
    "repo-path-ref:docs/kanban/current_board.md": {
        "blocked": (
            "The bounded TAW-07 deterministic development contract recomputes the exact 24-case / 240-observation catalog-state and safe-disable matrix, latency and context budgets, paired founder-private quality deltas, catalog-injection census, and exact TAW-04 decision bindings without model/provider calls or real-hardware measurement. Its clean fixture report remains `blocked_missing_acceptance_evidence`: structural checks are not accepted metrics, and stale-cache recovery, routing confidence bounds, response-level injection scoring, exact live model/config/context/backend/hardware measurements, complete powered measurement strata, and independently verified holdout evidence are missing. The bounded TAW-08 contract binds the exact candidate lock, evaluator environment, complete post-lock history, three-kind evidence-only delta, founder evidence/decision refs, exact-head and post-merge Foundation receipts, both active-truth reconciliations, and a final content-addressed publication receipt. Actual founder-private acceptance evidence is not yet collected; the current report remains `blocked_missing_founder_evidence`, so Q22 completion, independent promotion, and public claims remain gated."
        ),
        "implemented": (
            "TAW-08 founder-private acceptance evidence is verified at the refs "
            "below. The founder-private report is accepted; independent promotion "
            "and public claims remain gated, and Q22 follows the canonical Queue V2 "
            "disposition."
        ),
    },
    "repo-path-ref:docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md": {
        "blocked": (
            "The TAW-07 deterministic development contract recomputes the fixed 24-case / 240-observation matrix, accepted TAW-04 bindings, budgets, quality gates, and persisted-report consistency without model/provider calls or runtime authority. Its clean fixture report remains `blocked_missing_acceptance_evidence`; structural results are not acceptance evidence, and stale-cache recovery, routing confidence, response-level injection scoring, exact live model/config/context/backend/hardware measurements, complete powered measurement strata, and independent holdout evidence remain missing. The TAW-08 contract reuses the TAW-00 exact candidate lock; locks the evaluator environment; verifies complete post-lock ancestry, commit, and path history; restricts the delta to the content-addressed acceptance report and both active-truth reconciliations; and binds the founder decision to exact measurements, exact-head/post-merge Foundation receipts, and a final content-addressed publication receipt. The founder remains the sole private-dogfood evaluator, which does not satisfy independent custodian/evaluator/baseline/sealed-holdout gates. Actual founder-private acceptance evidence is not yet collected; the report remains `blocked_missing_founder_evidence`, and Q22, independent promotion, public claims, broader authority, runtime/model/provider/connector calls, and production authority remain blocked."
        ),
        "implemented": (
            "TAW-08 founder-private acceptance evidence is verified at the refs "
            "below. The founder-private report is accepted; independent promotion, "
            "public claims, and broader authority remain blocked, and Q22 follows "
            "the canonical Queue V2 disposition."
        ),
    },
}
TAW08_RECONCILIATION_CLAIM_REFS = {
    "repo-path-ref:docs/kanban/current_board.md": (
        "claim-ref:queue-v2/Q22/taw08-current-board"
    ),
    "repo-path-ref:docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md": (
        "claim-ref:queue-v2/Q22/taw08-release-truth"
    ),
}
TAW08_REQUIRED_ACCEPTANCE_PATH_REFS = tuple(
    sorted(
        {
            *TAW00_MANDATORY_CANDIDATE_PATH_REFS,
            *TAW08_REQUIRED_ENVIRONMENT_PATH_REFS,
            *(
                f"repo-path-ref:{path}"
                for path in (
                    "src/ultimate_ai_agent/core/capabilities/awareness.py",
                    "src/ultimate_ai_agent/core/capabilities/chat_shadow.py",
                    "src/ultimate_ai_agent/core/capabilities/diagnostics.py",
                    "src/ultimate_ai_agent/core/capabilities/familiarity.py",
                    "src/ultimate_ai_agent/core/capabilities/outcomes.py",
                    "src/ultimate_ai_agent/core/capabilities/retrieval.py",
                    "src/ultimate_ai_agent/core/evals/tool_aware_acceptance.py",
                    "src/ultimate_ai_agent/core/evals/tool_aware_hardening.py",
                    "scripts/run_foundation_gate.py",
                    "scripts/verify_taw08_environment_preflight.py",
                    "scripts/verify_tool_aware_cognition_taw08.py",
                )
            ),
        }
    )
)
TAW08_FOUNDER_EVIDENCE_MISSING_REFS = (
    "evidence-missing-ref:taw08:candidate-lock-verification-receipt",
    "evidence-missing-ref:taw08:end-to-end-journey-receipt",
    "evidence-missing-ref:taw08:exact-head-foundation-receipt",
    "evidence-missing-ref:taw08:founder-acceptance-decision",
    "evidence-missing-ref:taw08:founder-decision-verification-authority",
    "evidence-missing-ref:taw08:live-model-hardware-measurements",
    "evidence-missing-ref:taw08:response-scoring",
    "evidence-missing-ref:taw08:routing-confidence-bounds",
    "evidence-missing-ref:taw08:stale-cache-recovery",
)
TAW08_POSTMERGE_EVIDENCE_MISSING_REF = (
    "evidence-missing-ref:taw08:postmerge-foundation-receipt"
)
TAW08_DELTA_VERIFICATION_MISSING_REF = (
    "evidence-missing-ref:taw08:verified-evidence-delta-receipt"
)
TAW08_FINAL_PUBLICATION_MISSING_REF = (
    "evidence-missing-ref:taw08:final-acceptance-publication-receipt"
)
TAW08_INDEPENDENT_PROMOTION_BLOCKER_REFS = (
    "blocker-ref:taw00:external-baseline-acceptance-authority-missing",
    "blocker-ref:taw00:independent-custodian-identity-authority-missing",
    "blocker-ref:taw00:independent-evaluator-identity-authority-missing",
    "blocker-ref:taw08:sealed-holdout-evidence-missing",
)
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_GIT_RE = re.compile(r"^git-sha:[0-9a-f]{40}$")
_LOCAL_MODEL_ARTIFACT_DIGEST_RE = re.compile(
    r"^model-artifact-digest-ref:sha256:[0-9a-f]{64}$"
)
_API_MODEL_ID_RE = re.compile(r"^model-id-ref:openai:[A-Za-z0-9][A-Za-z0-9._-]{1,127}$")
_HARDWARE_OBSERVATION_DIGEST_RE = re.compile(
    r"^hardware-observation-ref:sha256:[0-9a-f]{64}$"
)
_NON_EXACT_MODEL_ID_TOKENS = frozenset(
    {"any", "anything", "configured", "placeholder", "test", "unknown"}
)


class EvidenceOnlyArtifactKind(str, Enum):
    acceptance_report = "acceptance_report"
    immutable_evidence_refs = "immutable_evidence_refs"
    claim_reconciliation = "claim_reconciliation"


class ReconciledClaimStatus(str, Enum):
    implemented = "implemented"
    partial = "partial"
    blocked = "blocked"
    planned = "planned"


class TAW08AcceptanceStatus(str, Enum):
    blocked_missing_founder_evidence = "blocked_missing_founder_evidence"
    founder_private_accepted_postmerge_pending = (
        "founder_private_accepted_postmerge_pending"
    )
    founder_private_accepted_final_publication_pending = (
        "founder_private_accepted_final_publication_pending"
    )
    founder_private_accepted_promotion_blocked = (
        "founder_private_accepted_promotion_blocked"
    )
    failed = "failed"


class FounderMeasurementKind(str, Enum):
    stale_cache_recovery = "stale_cache_recovery"
    routing_confidence = "routing_confidence"
    response_scoring = "response_scoring"
    live_model_hardware = "live_model_hardware"
    end_to_end_journey = "end_to_end_journey"


TAW08_FOUNDER_MINIMUM_DENOMINATOR = 24
TAW08_FOUNDER_MEASUREMENT_STRATA = {
    FounderMeasurementKind.stale_cache_recovery: (
        "stratum-ref:taw08:cache-stale",
        "stratum-ref:taw08:cache-corrupt",
        "stratum-ref:taw08:cache-missing",
    ),
    FounderMeasurementKind.routing_confidence: (
        "stratum-ref:taw08:direct-chat",
        "stratum-ref:taw08:discovery",
        "stratum-ref:taw08:approval-required",
        "stratum-ref:taw08:unavailable",
        "stratum-ref:taw08:unsupported",
    ),
    FounderMeasurementKind.response_scoring: (
        "stratum-ref:taw08:direct-chat",
        "stratum-ref:taw08:discovery",
        "stratum-ref:taw08:proposal",
        "stratum-ref:taw08:approval-required",
        "stratum-ref:taw08:unavailable",
        "stratum-ref:taw08:unsupported",
        "stratum-ref:taw08:interrupted",
        "stratum-ref:taw08:recovery",
    ),
    FounderMeasurementKind.live_model_hardware: (
        "stratum-ref:taw08:live-model-response",
    ),
    FounderMeasurementKind.end_to_end_journey: (
        "stratum-ref:taw08:chat",
        "stratum-ref:taw08:discovery",
        "stratum-ref:taw08:proposal",
        "stratum-ref:taw08:approval-required",
        "stratum-ref:taw08:unavailable",
        "stratum-ref:taw08:unsupported",
        "stratum-ref:taw08:interrupted",
        "stratum-ref:taw08:recovery",
    ),
}
_TAW08_MEASUREMENT_PARAMETERS = {
    FounderMeasurementKind.stale_cache_recovery: (
        "metric-ref:taw08:stale-cache-recovery-success-rate",
        "threshold-ref:taw08:stale-cache-recovery-success-rate:v1",
        0.95,
    ),
    FounderMeasurementKind.routing_confidence: (
        "metric-ref:taw08:routing-confidence-accuracy",
        "threshold-ref:taw08:routing-confidence-accuracy:v1",
        0.95,
    ),
    FounderMeasurementKind.response_scoring: (
        "metric-ref:taw08:founder-response-score",
        "threshold-ref:taw08:founder-response-score:v1",
        0.80,
    ),
    FounderMeasurementKind.live_model_hardware: (
        "metric-ref:taw08:live-model-hardware-success-rate",
        "threshold-ref:taw08:live-model-hardware-success-rate:v1",
        0.95,
    ),
    FounderMeasurementKind.end_to_end_journey: (
        "metric-ref:taw08:end-to-end-journey-success-rate",
        "threshold-ref:taw08:end-to-end-journey-success-rate:v1",
        0.95,
    ),
}
TAW08_FOUNDER_MEASUREMENT_SPECS = {
    kind: tuple(
        (
            stratum_ref,
            parameters[0],
            parameters[1],
            "gte",
            parameters[2],
            "unit-ref:ratio",
            TAW08_FOUNDER_MINIMUM_DENOMINATOR,
        )
        for stratum_ref in TAW08_FOUNDER_MEASUREMENT_STRATA[kind]
    )
    for kind, parameters in _TAW08_MEASUREMENT_PARAMETERS.items()
}
TAW08_LANGUAGE_PROFILE_REF = "language-profile-ref:english-first"
TAW08_LOCAL_MODEL_PROFILE_REF = "model-profile-ref:qwen-3.8-27b-128k"
TAW08_CONTEXT_PROFILE_REF = "context-profile-ref:128k"
TAW08_FOUNDER_PROFILE_PATH_REF = (
    "repo-path-ref:docs/evals/tool_aware_cognition_q22_founder_dogfood_v1.json"
)
TAW08_REPOSITORY_VERIFIER_PATH_REF = (
    "repo-path-ref:scripts/verify_tool_aware_cognition_taw08.py"
)
TAW08_INFERENCE_PROFILE_REFS = (
    "inference-profile-ref:taw00:openai-chatgpt-api",
    "inference-profile-ref:taw00:openai-codex-api",
    "inference-profile-ref:taw00:qwen-3.8-27b-128k-local",
)
TAW08_LOCAL_INFERENCE_PROFILE_REF = (
    "inference-profile-ref:taw00:qwen-3.8-27b-128k-local"
)
TAW08_HARDWARE_FAMILY_REFS = (
    "hardware-family-ref:mac",
    "hardware-family-ref:windows",
)


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _validate_repo_path_refs(values: tuple[str, ...], field_name: str) -> None:
    if values != tuple(sorted(values)) or len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be unique and sorted")
    prefix = "repo-path-ref:"
    for value in values:
        if not value.startswith(prefix):
            raise ValueError(f"{field_name} must contain repository path refs")
        path = value.removeprefix(prefix)
        parts = path.split("/")
        if (
            not path
            or path.startswith("/")
            or len(path) > 512
            or any(part in ("", ".", "..") for part in parts)
            or any(character in path for character in ("\x00", "\n", "\r"))
        ):
            raise ValueError(f"{field_name} contains an unsafe repository path")


class RevisionPathCensus(_FrozenModel):
    schema_version: Literal["uaa-taw08-revision-path-census.v1"] = (
        "uaa-taw08-revision-path-census.v1"
    )
    revision_ref: str
    path_refs: tuple[str, ...] = Field(
        ..., min_length=1, max_length=TAW08_MAX_REVISION_PATHS
    )
    provenance_ref: Literal["provenance-ref:git-ls-tree"] = "provenance-ref:git-ls-tree"
    census_digest_ref: str

    @model_validator(mode="after")
    def validate_census(self) -> "RevisionPathCensus":
        _validate_git_ref(self.revision_ref, "revision_ref")
        _validate_repo_path_refs(self.path_refs, "path_refs")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"census_digest_ref"})
        )
        if self.census_digest_ref != expected:
            raise ValueError("revision path census digest binding drift")
        return self


class RevisionDeltaCensus(_FrozenModel):
    schema_version: Literal["uaa-taw08-revision-delta-census.v1"] = (
        "uaa-taw08-revision-delta-census.v1"
    )
    candidate_revision_ref: str
    delta_revision_ref: str
    path_refs: tuple[str, ...] = Field(
        ..., min_length=1, max_length=TAW08_MAX_EVIDENCE_DELTA_ENTRIES
    )
    history_path_refs: tuple[str, ...] = Field(
        ..., min_length=1, max_length=TAW08_MAX_REVISION_PATHS
    )
    commit_count: int = Field(..., ge=1, le=10_000)
    candidate_ancestor_verified: Literal[True] = True
    provenance_ref: Literal["provenance-ref:git-history-path-census"] = (
        "provenance-ref:git-history-path-census"
    )
    census_digest_ref: str

    @model_validator(mode="after")
    def validate_census(self) -> "RevisionDeltaCensus":
        _validate_git_ref(self.candidate_revision_ref, "candidate_revision_ref")
        _validate_git_ref(self.delta_revision_ref, "delta_revision_ref")
        _validate_repo_path_refs(self.path_refs, "path_refs")
        _validate_repo_path_refs(self.history_path_refs, "history_path_refs")
        if not set(self.path_refs) <= set(self.history_path_refs):
            raise ValueError(
                "revision endpoint paths must be present in history census"
            )
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"census_digest_ref"})
        )
        if self.census_digest_ref != expected:
            raise ValueError("revision delta census digest binding drift")
        return self


def _validate_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_digest(value: str, field_name: str) -> None:
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be an exact sha256 digest")


def _validate_git_ref(value: str, field_name: str) -> None:
    if not _GIT_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be an exact Git revision")


def _validate_sorted_refs(values: tuple[str, ...], field_name: str) -> None:
    if values != tuple(sorted(values)) or len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be unique and sorted")
    for value in values:
        _validate_ref(value, field_name)


def _validate_builder_keys(
    model_type: type[BaseModel], values: Mapping[str, object], generated_field: str
) -> None:
    allowed = set(model_type.model_fields) - {generated_field}
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(f"unknown builder fields: {tuple(sorted(unknown))}")


class ImmutableEvidenceRefsArtifact(_FrozenModel):
    schema_version: Literal["uaa-taw08-immutable-evidence-refs.v1"] = (
        "uaa-taw08-immutable-evidence-refs.v1"
    )
    evidence_refs: tuple[str, ...] = Field(..., min_length=1, max_length=64)
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_artifact(self) -> "ImmutableEvidenceRefsArtifact":
        _validate_sorted_refs(self.evidence_refs, "evidence_refs")
        return self


class ClaimReconciliationEntry(_FrozenModel):
    claim_ref: str
    status: ReconciledClaimStatus
    evidence_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_entry(self) -> "ClaimReconciliationEntry":
        _validate_ref(self.claim_ref, "claim_ref")
        _validate_sorted_refs(self.evidence_refs, "evidence_refs")
        return self


class ClaimReconciliationArtifact(_FrozenModel):
    schema_version: Literal["uaa-taw08-claim-reconciliation.v1"] = (
        "uaa-taw08-claim-reconciliation.v1"
    )
    entries: tuple[ClaimReconciliationEntry, ...] = Field(
        ..., min_length=1, max_length=64
    )
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_artifact(self) -> "ClaimReconciliationArtifact":
        refs = tuple(item.claim_ref for item in self.entries)
        if refs != tuple(sorted(refs)) or len(refs) != len(set(refs)):
            raise ValueError("claim reconciliation entries must be unique and sorted")
        return self


class RedactedAcceptanceReportArtifact(_FrozenModel):
    schema_version: Literal["uaa-taw08-redacted-acceptance-report.v1"] = (
        "uaa-taw08-redacted-acceptance-report.v1"
    )
    report_fingerprint_ref: str
    status: TAW08AcceptanceStatus
    candidate_revision_ref: str
    candidate_manifest_digest_ref: str
    founder_evidence_digest_ref: str | None
    independent_promotion_ready: Literal[False] = False
    public_quality_claims_allowed: Literal[False] = False
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_artifact(self) -> "RedactedAcceptanceReportArtifact":
        _validate_ref(self.report_fingerprint_ref, "report_fingerprint_ref")
        _validate_git_ref(self.candidate_revision_ref, "candidate_revision_ref")
        _validate_digest(
            self.candidate_manifest_digest_ref, "candidate_manifest_digest_ref"
        )
        if self.founder_evidence_digest_ref is not None:
            _validate_digest(
                self.founder_evidence_digest_ref, "founder_evidence_digest_ref"
            )
        return self


class EvidenceOnlyDeltaEntry(_FrozenModel):
    path_ref: str
    artifact_kind: EvidenceOnlyArtifactKind
    content_digest_ref: str

    @model_validator(mode="after")
    def validate_entry(self) -> "EvidenceOnlyDeltaEntry":
        _validate_ref(self.path_ref, "path_ref")
        _validate_digest(self.content_digest_ref, "content_digest_ref")
        return self


class EvidenceOnlyDeltaManifest(_FrozenModel):
    schema_version: Literal["uaa-taw08-evidence-only-delta.v1"] = (
        "uaa-taw08-evidence-only-delta.v1"
    )
    candidate_revision_ref: str
    candidate_manifest_digest_ref: str
    delta_revision_ref: str
    entries: tuple[EvidenceOnlyDeltaEntry, ...] = Field(
        ..., min_length=1, max_length=TAW08_MAX_EVIDENCE_DELTA_ENTRIES
    )
    manifest_digest_ref: str
    executable_changes_added: Literal[False] = False
    route_changes_added: Literal[False] = False
    prompt_changes_added: Literal[False] = False
    policy_changes_added: Literal[False] = False
    configuration_changes_added: Literal[False] = False
    dependency_changes_added: Literal[False] = False
    evaluator_changes_added: Literal[False] = False
    threshold_changes_added: Literal[False] = False
    corpus_or_holdout_changes_added: Literal[False] = False

    @model_validator(mode="after")
    def validate_manifest(self) -> "EvidenceOnlyDeltaManifest":
        _validate_git_ref(self.candidate_revision_ref, "candidate_revision_ref")
        _validate_git_ref(self.delta_revision_ref, "delta_revision_ref")
        _validate_digest(
            self.candidate_manifest_digest_ref, "candidate_manifest_digest_ref"
        )
        path_refs = tuple(item.path_ref for item in self.entries)
        if path_refs != tuple(sorted(path_refs)) or len(path_refs) != len(
            set(path_refs)
        ):
            raise ValueError("evidence-only delta entries must be unique and sorted")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"manifest_digest_ref"})
        )
        if self.manifest_digest_ref != expected:
            raise ValueError("evidence-only delta manifest digest binding drift")
        return self


class FoundationGateReceipt(_FrozenModel):
    schema_version: Literal["uaa-taw08-foundation-receipt.v1"] = (
        "uaa-taw08-foundation-receipt.v1"
    )
    stage: Literal["exact_head", "postmerge"]
    revision_ref: str
    report_digest_ref: str
    report_ref: str
    command_mode: Literal["report-only"] = "report-only"
    evaluator_environment_receipt: _EvaluatorEnvironmentReceipt
    evaluator_environment_digest_ref: str
    passed: Literal[True] = True
    redacted: Literal[True] = True
    raw_content_persisted: Literal[False] = False
    receipt_digest_ref: str

    @model_validator(mode="after")
    def validate_receipt(self) -> "FoundationGateReceipt":
        _validate_git_ref(self.revision_ref, "revision_ref")
        _validate_digest(self.report_digest_ref, "report_digest_ref")
        _validate_digest(
            self.evaluator_environment_digest_ref,
            "evaluator_environment_digest_ref",
        )
        _validate_ref(self.report_ref, "report_ref")
        if (
            self.evaluator_environment_digest_ref
            != self.evaluator_environment_receipt.receipt_digest_ref
        ):
            raise ValueError("Foundation receipt evaluator environment binding drift")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"receipt_digest_ref"})
        )
        if self.receipt_digest_ref != expected:
            raise ValueError("Foundation Gate receipt digest binding drift")
        return self


class _EvaluatorEnvironmentReceipt(_FrozenModel):
    schema_version: Literal["uaa-taw08-evaluator-environment.v1"] = (
        "uaa-taw08-evaluator-environment.v1"
    )
    python_implementation: Literal["cpython"] = "cpython"
    python_version: str = Field(..., pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    platform_system: str = Field(..., pattern=r"^[a-z0-9_-]{1,32}$")
    platform_machine: str = Field(..., pattern=r"^[a-z0-9_.-]{1,64}$")
    python_executable_digest_ref: str
    python_standard_library_file_count: int = Field(..., ge=1, le=100_000)
    python_standard_library_digest_ref: str
    git_executable_digest_ref: str
    git_provenance_ref: str
    installed_distribution_count: int = Field(..., ge=1, le=2048)
    installed_distributions_digest_ref: str
    pyproject_digest_ref: str
    uv_lock_digest_ref: str
    lock_check_command_ref: Literal[
        "command-ref:python-installed-distribution-lock-closure"
    ] = "command-ref:python-installed-distribution-lock-closure"
    independent_lock_closure_verified: Literal[True] = True
    locked_environment_verified: Literal[True] = True
    raw_content_persisted: Literal[False] = False
    receipt_digest_ref: str

    @model_validator(mode="after")
    def validate_receipt(self) -> "_EvaluatorEnvironmentReceipt":
        for field_name in (
            "python_executable_digest_ref",
            "python_standard_library_digest_ref",
            "git_executable_digest_ref",
            "installed_distributions_digest_ref",
            "pyproject_digest_ref",
            "uv_lock_digest_ref",
        ):
            _validate_digest(getattr(self, field_name), field_name)
        _validate_ref(self.git_provenance_ref, "git_provenance_ref")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"receipt_digest_ref"})
        )
        if self.receipt_digest_ref != expected:
            raise ValueError("evaluator environment receipt digest binding drift")
        return self


FoundationGateReceipt.model_rebuild()


class _CandidateLockVerificationReceipt(_FrozenModel):
    schema_version: Literal["uaa-taw08-candidate-lock-verification.v1"] = (
        "uaa-taw08-candidate-lock-verification.v1"
    )
    candidate_revision_ref: str
    candidate_manifest_digest_ref: str
    source_projection_digest_ref: str
    source_closure_digest_ref: str
    path_census_digest_ref: str
    repository_verifier_digest_ref: str
    executing_source_path_refs: tuple[str, ...] = Field(
        ..., min_length=1, max_length=TAW08_MAX_CANDIDATE_PATHS
    )
    executing_source_census_digest_ref: str
    evaluator_environment_receipt: _EvaluatorEnvironmentReceipt
    evaluator_environment_digest_ref: str
    verifier_ref: Literal["verifier-ref:taw08:candidate-lock:v1"] = (
        "verifier-ref:taw08:candidate-lock:v1"
    )
    verified: Literal[True] = True
    receipt_digest_ref: str

    @model_validator(mode="after")
    def validate_receipt(self) -> "_CandidateLockVerificationReceipt":
        _validate_git_ref(self.candidate_revision_ref, "candidate_revision_ref")
        for field_name in (
            "candidate_manifest_digest_ref",
            "source_projection_digest_ref",
            "source_closure_digest_ref",
            "path_census_digest_ref",
            "repository_verifier_digest_ref",
            "executing_source_census_digest_ref",
            "evaluator_environment_digest_ref",
        ):
            _validate_digest(getattr(self, field_name), field_name)
        _validate_repo_path_refs(
            self.executing_source_path_refs,
            "executing_source_path_refs",
        )
        if (
            self.evaluator_environment_digest_ref
            != self.evaluator_environment_receipt.receipt_digest_ref
        ):
            raise ValueError(
                "evaluator environment digest must bind the embedded receipt"
            )
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"receipt_digest_ref"})
        )
        if self.receipt_digest_ref != expected:
            raise ValueError("candidate verification receipt digest binding drift")
        return self


class _EvidenceOnlyDeltaVerificationReceipt(_FrozenModel):
    schema_version: Literal["uaa-taw08-evidence-delta-verification.v1"] = (
        "uaa-taw08-evidence-delta-verification.v1"
    )
    candidate_revision_ref: str
    candidate_manifest_digest_ref: str
    delta_revision_ref: str
    delta_manifest_digest_ref: str
    revision_delta_path_census_digest_ref: str
    history_path_refs: tuple[str, ...]
    commit_count: int = Field(..., ge=1, le=10_000)
    candidate_ancestor_verified: Literal[True] = True
    published_acceptance_report_fingerprint_ref: str
    artifact_count: int = Field(..., ge=1, le=TAW08_MAX_EVIDENCE_DELTA_ENTRIES)
    verifier_ref: Literal["verifier-ref:taw08:evidence-only-delta:v1"] = (
        "verifier-ref:taw08:evidence-only-delta:v1"
    )
    verified: Literal[True] = True
    receipt_digest_ref: str

    @model_validator(mode="after")
    def validate_receipt(self) -> "_EvidenceOnlyDeltaVerificationReceipt":
        _validate_git_ref(self.candidate_revision_ref, "candidate_revision_ref")
        _validate_git_ref(self.delta_revision_ref, "delta_revision_ref")
        for field_name in (
            "candidate_manifest_digest_ref",
            "delta_manifest_digest_ref",
            "revision_delta_path_census_digest_ref",
        ):
            _validate_digest(getattr(self, field_name), field_name)
        _validate_ref(
            self.published_acceptance_report_fingerprint_ref,
            "published_acceptance_report_fingerprint_ref",
        )
        _validate_repo_path_refs(self.history_path_refs, "history_path_refs")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"receipt_digest_ref"})
        )
        if self.receipt_digest_ref != expected:
            raise ValueError("delta verification receipt digest binding drift")
        return self


class FinalAcceptancePublicationArtifact(_FrozenModel):
    schema_version: Literal["uaa-taw08-final-acceptance-artifact.v1"] = (
        "uaa-taw08-final-acceptance-artifact.v1"
    )
    candidate_revision_ref: str
    candidate_manifest_digest_ref: str
    founder_evidence_digest_ref: str
    delta_revision_ref: str
    delta_manifest_digest_ref: str
    delta_verification_receipt_digest_ref: str
    postmerge_foundation_receipt_digest_ref: str
    final_status: Literal["founder_private_accepted_promotion_blocked"] = (
        "founder_private_accepted_promotion_blocked"
    )
    published_report_semantic_digest_ref: str
    independent_promotion_ready: Literal[False] = False
    public_quality_claims_allowed: Literal[False] = False
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_artifact(self) -> "FinalAcceptancePublicationArtifact":
        _validate_git_ref(self.candidate_revision_ref, "candidate_revision_ref")
        _validate_git_ref(self.delta_revision_ref, "delta_revision_ref")
        for field_name in (
            "candidate_manifest_digest_ref",
            "founder_evidence_digest_ref",
            "delta_manifest_digest_ref",
            "delta_verification_receipt_digest_ref",
            "postmerge_foundation_receipt_digest_ref",
            "published_report_semantic_digest_ref",
        ):
            _validate_digest(getattr(self, field_name), field_name)
        return self


class _PublicationHistoryCensus(_FrozenModel):
    schema_version: Literal["uaa-taw08-publication-history-census.v1"] = (
        "uaa-taw08-publication-history-census.v1"
    )
    delta_revision_ref: str
    publication_revision_ref: str
    path_refs: tuple[str, ...] = Field(..., min_length=1, max_length=1)
    history_path_refs: tuple[str, ...] = Field(..., min_length=1, max_length=1)
    commit_count: int = Field(..., ge=1, le=32)
    delta_ancestor_verified: Literal[True] = True
    provenance_ref: Literal["provenance-ref:git-history-path-census"] = (
        "provenance-ref:git-history-path-census"
    )
    census_digest_ref: str

    @model_validator(mode="after")
    def validate_census(self) -> "_PublicationHistoryCensus":
        _validate_git_ref(self.delta_revision_ref, "delta_revision_ref")
        _validate_git_ref(self.publication_revision_ref, "publication_revision_ref")
        if self.delta_revision_ref == self.publication_revision_ref:
            raise ValueError("publication history requires a later revision")
        expected_paths = (TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,)
        if self.path_refs != expected_paths or self.history_path_refs != expected_paths:
            raise ValueError("publication history contains non-publication paths")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"census_digest_ref"})
        )
        if self.census_digest_ref != expected:
            raise ValueError("publication history census digest binding drift")
        return self


class _FinalAcceptancePublicationReceipt(_FrozenModel):
    schema_version: Literal["uaa-taw08-final-acceptance-publication.v1"] = (
        "uaa-taw08-final-acceptance-publication.v1"
    )
    candidate_revision_ref: str
    candidate_manifest_digest_ref: str
    delta_revision_ref: str
    delta_manifest_digest_ref: str
    delta_verification_receipt_digest_ref: str
    postmerge_foundation_receipt_digest_ref: str
    publication_revision_ref: str
    publication_history_census: _PublicationHistoryCensus
    publication_history_census_digest_ref: str
    publication_path_ref: Literal[
        "repo-path-ref:docs/evals/"
        "tool_aware_cognition_taw08_final_acceptance_report_v1.json"
    ] = TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF
    publication_content_digest_ref: str
    final_status: Literal["founder_private_accepted_promotion_blocked"] = (
        "founder_private_accepted_promotion_blocked"
    )
    published_report_semantic_digest_ref: str
    publication_ref: str
    verified: Literal[True] = True
    raw_content_persisted: Literal[False] = False
    receipt_digest_ref: str

    @model_validator(mode="after")
    def validate_receipt(self) -> "_FinalAcceptancePublicationReceipt":
        _validate_git_ref(self.candidate_revision_ref, "candidate_revision_ref")
        _validate_git_ref(self.delta_revision_ref, "delta_revision_ref")
        _validate_git_ref(self.publication_revision_ref, "publication_revision_ref")
        for field_name in (
            "candidate_manifest_digest_ref",
            "delta_manifest_digest_ref",
            "delta_verification_receipt_digest_ref",
            "postmerge_foundation_receipt_digest_ref",
            "publication_history_census_digest_ref",
            "publication_content_digest_ref",
            "published_report_semantic_digest_ref",
        ):
            _validate_digest(getattr(self, field_name), field_name)
        _validate_ref(self.publication_ref, "publication_ref")
        if (
            self.publication_history_census_digest_ref
            != self.publication_history_census.census_digest_ref
            or self.publication_history_census.delta_revision_ref
            != self.delta_revision_ref
            or self.publication_history_census.publication_revision_ref
            != self.publication_revision_ref
        ):
            raise ValueError("publication history census binding drift")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"receipt_digest_ref"})
        )
        if self.receipt_digest_ref != expected:
            raise ValueError("final publication receipt digest binding drift")
        return self


class FounderSameHostBaselineEvidence(_FrozenModel):
    schema_version: Literal["uaa-taw08-same-host-baseline-evidence.v1"] = (
        "uaa-taw08-same-host-baseline-evidence.v1"
    )
    candidate_revision_ref: str
    candidate_manifest_digest_ref: str
    inference_profile_ref: str
    model_artifact_or_configuration_ref: str
    backend_ref: str
    observed_hardware_family_ref: str
    observed_hardware_ref: str
    evidence_ref: str
    metric_ref: Literal["metric-ref:taw08:live-model-hardware-success-rate"] = (
        "metric-ref:taw08:live-model-hardware-success-rate"
    )
    observed_value: float
    observation_count: int = Field(..., ge=TAW08_FOUNDER_MINIMUM_DENOMINATOR)
    successful_observation_count: int = Field(..., ge=0)
    unit_ref: Literal["unit-ref:ratio"] = "unit-ref:ratio"
    minimum_candidate_delta: Literal[0.0] = 0.0
    result_digest_ref: str
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_evidence(self) -> "FounderSameHostBaselineEvidence":
        _validate_git_ref(self.candidate_revision_ref, "candidate_revision_ref")
        _validate_digest(
            self.candidate_manifest_digest_ref,
            "candidate_manifest_digest_ref",
        )
        for field_name in (
            "inference_profile_ref",
            "model_artifact_or_configuration_ref",
            "backend_ref",
            "observed_hardware_family_ref",
            "observed_hardware_ref",
            "evidence_ref",
            "metric_ref",
            "unit_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        if not _HARDWARE_OBSERVATION_DIGEST_RE.fullmatch(self.observed_hardware_ref):
            raise ValueError("same-host hardware identity must be an opaque digest")
        if (
            not math.isfinite(self.observed_value)
            or not 0.0 <= self.observed_value <= 1.0
            or self.successful_observation_count > self.observation_count
            or not math.isclose(
                self.observed_value,
                self.successful_observation_count / self.observation_count,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
        ):
            raise ValueError("same-host baseline ratio census is invalid")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"result_digest_ref"})
        )
        if self.result_digest_ref != expected:
            raise ValueError("same-host baseline evidence digest binding drift")
        return self


class FounderMeasurementResult(_FrozenModel):
    schema_version: Literal["uaa-taw08-founder-measurement-result.v1"] = (
        "uaa-taw08-founder-measurement-result.v1"
    )
    measurement_kind: FounderMeasurementKind
    candidate_revision_ref: str
    candidate_manifest_digest_ref: str
    evidence_ref: str
    language_profile_ref: Literal["language-profile-ref:english-first"] = (
        TAW08_LANGUAGE_PROFILE_REF
    )
    inference_profile_ref: str | None = None
    model_profile_ref: str | None = None
    model_artifact_or_configuration_ref: str | None = None
    context_profile_ref: str | None = None
    backend_ref: str | None = None
    observed_hardware_family_ref: str | None = None
    observed_hardware_ref: str | None = None
    same_host_baseline: FounderSameHostBaselineEvidence | None = None
    observations: tuple["FounderMeasurementObservation", ...] = Field(
        ..., min_length=1, max_length=10_000
    )
    observation_count: int = Field(..., ge=1, le=1_000_000)
    threshold_decision: Literal["passed", "failed"]
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_result(self) -> "FounderMeasurementResult":
        _validate_git_ref(self.candidate_revision_ref, "candidate_revision_ref")
        _validate_digest(
            self.candidate_manifest_digest_ref, "candidate_manifest_digest_ref"
        )
        _validate_ref(self.evidence_ref, "evidence_ref")
        required_live_identity_values = (
            self.inference_profile_ref,
            self.model_profile_ref,
            self.model_artifact_or_configuration_ref,
            self.backend_ref,
            self.observed_hardware_family_ref,
            self.observed_hardware_ref,
        )
        all_live_identity_values = (
            *required_live_identity_values,
            self.context_profile_ref,
        )
        if self.measurement_kind is FounderMeasurementKind.live_model_hardware:
            if any(value is None for value in required_live_identity_values):
                raise ValueError("live-model measurement identity census is incomplete")
            if (
                self.inference_profile_ref not in TAW08_INFERENCE_PROFILE_REFS
                or self.observed_hardware_family_ref not in TAW08_HARDWARE_FAMILY_REFS
            ):
                raise ValueError("live-model measurement profile census drift")
            if self.inference_profile_ref == TAW08_LOCAL_INFERENCE_PROFILE_REF:
                if (
                    self.model_profile_ref != TAW08_LOCAL_MODEL_PROFILE_REF
                    or self.context_profile_ref != TAW08_CONTEXT_PROFILE_REF
                ):
                    raise ValueError("local live-model measurement profile drift")
                if not _LOCAL_MODEL_ARTIFACT_DIGEST_RE.fullmatch(
                    self.model_artifact_or_configuration_ref or ""
                ):
                    raise ValueError(
                        "local live-model measurement requires an artifact digest"
                    )
            elif self.context_profile_ref is not None:
                raise ValueError("API live-model measurement context profile drift")
            elif not _API_MODEL_ID_RE.fullmatch(
                self.model_artifact_or_configuration_ref or ""
            ) or any(
                token in _NON_EXACT_MODEL_ID_TOKENS
                for token in re.split(
                    r"[^a-z0-9]+",
                    (self.model_artifact_or_configuration_ref or "").lower(),
                )
                if token
            ):
                raise ValueError(
                    "API live-model measurement requires an exact model ID"
                )
            for index, value in enumerate(
                item for item in all_live_identity_values if item is not None
            ):
                _validate_ref(value, f"live_model_identity_{index}")
            if not _HARDWARE_OBSERVATION_DIGEST_RE.fullmatch(
                self.observed_hardware_ref or ""
            ):
                raise ValueError(
                    "live-model hardware identity must be an opaque digest"
                )
            baseline = self.same_host_baseline
            if baseline is None:
                raise ValueError("live-model measurement requires same-host baseline")
            if (
                baseline.candidate_revision_ref != self.candidate_revision_ref
                or baseline.candidate_manifest_digest_ref
                != self.candidate_manifest_digest_ref
                or baseline.inference_profile_ref != self.inference_profile_ref
                or baseline.model_artifact_or_configuration_ref
                != self.model_artifact_or_configuration_ref
                or baseline.backend_ref != self.backend_ref
                or baseline.observed_hardware_family_ref
                != self.observed_hardware_family_ref
                or baseline.observed_hardware_ref != self.observed_hardware_ref
            ):
                raise ValueError("live-model same-host baseline binding drift")
        elif any(value is not None for value in all_live_identity_values):
            raise ValueError("non-live measurement cannot bind a live-model identity")
        elif self.same_host_baseline is not None:
            raise ValueError("non-live measurement cannot bind same-host baseline")
        if self.observation_count != sum(
            item.observation_count for item in self.observations
        ):
            raise ValueError("founder measurement observation count drift")
        expected_spec = TAW08_FOUNDER_MEASUREMENT_SPECS[self.measurement_kind]
        actual_specs = tuple(
            (
                item.stratum_ref,
                item.metric_ref,
                item.threshold_ref,
                item.threshold_operator,
                item.threshold_value,
                item.unit_ref,
                item.minimum_denominator,
            )
            for item in self.observations
        )
        if actual_specs != expected_spec:
            raise ValueError("founder measurement metric threshold census drift")
        if any(
            item.observation_count < item.minimum_denominator
            for item in self.observations
        ):
            raise ValueError("founder measurement minimum denominator not met")
        if self.measurement_kind is FounderMeasurementKind.live_model_hardware:
            baseline = self.same_host_baseline
            live_observation = self.observations[0]
            if (
                baseline is None
                or baseline.metric_ref != live_observation.metric_ref
                or baseline.unit_ref != live_observation.unit_ref
                or live_observation.observed_value - baseline.observed_value
                < baseline.minimum_candidate_delta
            ):
                raise ValueError("live-model same-host baseline comparison failed")
        decisions = tuple(item.threshold_passed for item in self.observations)
        expected_decision = "passed" if all(decisions) else "failed"
        if self.threshold_decision != expected_decision:
            raise ValueError("founder measurement threshold decision drift")
        return self


class FounderMeasurementObservation(_FrozenModel):
    stratum_ref: str
    metric_ref: str
    observed_value: float
    observation_count: int = Field(..., ge=1, le=1_000_000)
    successful_observation_count: int = Field(..., ge=0, le=1_000_000)
    model_call_counts: tuple[int, ...] = Field(default=(), max_length=1_000_000)
    minimum_denominator: Literal[24] = TAW08_FOUNDER_MINIMUM_DENOMINATOR
    threshold_ref: str
    threshold_operator: Literal["gte", "lte"]
    threshold_value: float
    unit_ref: str

    @model_validator(mode="after")
    def validate_observation(self) -> "FounderMeasurementObservation":
        for value, field_name in (
            (self.stratum_ref, "stratum_ref"),
            (self.metric_ref, "metric_ref"),
            (self.threshold_ref, "threshold_ref"),
            (self.unit_ref, "unit_ref"),
        ):
            _validate_ref(value, field_name)
        if not math.isfinite(self.observed_value) or not math.isfinite(
            self.threshold_value
        ):
            raise ValueError("founder measurement values must be finite")
        if self.unit_ref == "unit-ref:ratio" and (
            not 0.0 <= self.observed_value <= 1.0
            or not 0.0 <= self.threshold_value <= 1.0
        ):
            raise ValueError("founder measurement ratios must be within zero and one")
        if (
            self.successful_observation_count > self.observation_count
            or not math.isclose(
                self.observed_value,
                self.successful_observation_count / self.observation_count,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
        ):
            raise ValueError("founder measurement ratio is inconsistent with counts")
        if self.stratum_ref == "stratum-ref:taw08:chat":
            if len(self.model_call_counts) != self.observation_count or any(
                count != 1 for count in self.model_call_counts
            ):
                raise ValueError(
                    "ordinary-chat observations require exactly one model call"
                )
        elif self.model_call_counts:
            raise ValueError("model-call census is only valid for ordinary chat")
        return self

    @property
    def threshold_passed(self) -> bool:
        if self.threshold_operator == "gte":
            return self.observed_value >= self.threshold_value
        return self.observed_value <= self.threshold_value


class FounderMeasurementReceipt(_FrozenModel):
    schema_version: Literal["uaa-taw08-founder-measurement-receipt.v1"] = (
        "uaa-taw08-founder-measurement-receipt.v1"
    )
    result: FounderMeasurementResult
    result_digest_ref: str
    verifier_ref: Literal["verifier-ref:taw08:founder-measurement:v1"] = (
        "verifier-ref:taw08:founder-measurement:v1"
    )
    verified: Literal[True] = True
    receipt_digest_ref: str

    @model_validator(mode="after")
    def validate_receipt(self) -> "FounderMeasurementReceipt":
        expected_result_digest = canonical_digest(self.result.model_dump(mode="json"))
        if self.result_digest_ref != expected_result_digest:
            raise ValueError("founder measurement result digest binding drift")
        if self.result.threshold_decision != "passed":
            raise ValueError(
                "founder measurement receipt requires a passed threshold decision"
            )
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"receipt_digest_ref"})
        )
        if self.receipt_digest_ref != expected:
            raise ValueError("founder measurement receipt digest binding drift")
        return self


def founder_decision_signature_payload(
    *,
    candidate_revision_ref: str,
    candidate_manifest_digest_ref: str,
    measurement_receipt_digest_refs: tuple[str, ...],
    exact_head_foundation_receipt_digest_ref: str,
    founder_decision_ref: str,
) -> bytes:
    """Return the canonical digest message that the founder must sign."""

    payload = {
        "schema_version": "uaa-taw08-founder-decision-signature.v1",
        "candidate_revision_ref": candidate_revision_ref,
        "candidate_manifest_digest_ref": candidate_manifest_digest_ref,
        "measurement_receipt_digest_refs": tuple(
            sorted(measurement_receipt_digest_refs)
        ),
        "exact_head_foundation_receipt_digest_ref": (
            exact_head_foundation_receipt_digest_ref
        ),
        "founder_decision_ref": founder_decision_ref,
        "founder_decision_outcome": "accepted",
    }
    return canonical_digest(payload).encode("ascii")


class FounderPrivateAcceptanceEvidence(_FrozenModel):
    schema_version: Literal["uaa-taw08-founder-acceptance-evidence.v1"] = (
        "uaa-taw08-founder-acceptance-evidence.v1"
    )
    candidate_revision_ref: str
    candidate_manifest_digest_ref: str
    founder_dogfood_profile_digest_ref: str
    stale_cache_recovery_receipt: FounderMeasurementReceipt
    routing_confidence_receipt: FounderMeasurementReceipt
    response_scoring_receipt: FounderMeasurementReceipt
    live_model_hardware_receipts: tuple[FounderMeasurementReceipt, ...] = Field(
        ..., min_length=1, max_length=32
    )
    end_to_end_journey_receipt: FounderMeasurementReceipt
    founder_decision_ref: str
    founder_decision_outcome: Literal["accepted"]
    founder_decision_signature_ref: str
    exact_head_foundation_receipt: FoundationGateReceipt
    evidence_digest_ref: str
    raw_content_persisted: Literal[False] = False
    runtime_model_calls_added: Literal[False] = False
    provider_calls_added: Literal[False] = False
    execution_authority_added: Literal[False] = False

    @model_validator(mode="after")
    def validate_evidence(self) -> "FounderPrivateAcceptanceEvidence":
        _validate_git_ref(self.candidate_revision_ref, "candidate_revision_ref")
        _validate_digest(
            self.candidate_manifest_digest_ref, "candidate_manifest_digest_ref"
        )
        _validate_digest(
            self.founder_dogfood_profile_digest_ref,
            "founder_dogfood_profile_digest_ref",
        )
        _validate_ref(self.founder_decision_ref, "founder_decision_ref")
        expected_kinds = (
            (
                self.stale_cache_recovery_receipt,
                FounderMeasurementKind.stale_cache_recovery,
            ),
            (
                self.routing_confidence_receipt,
                FounderMeasurementKind.routing_confidence,
            ),
            (self.response_scoring_receipt, FounderMeasurementKind.response_scoring),
            (
                self.end_to_end_journey_receipt,
                FounderMeasurementKind.end_to_end_journey,
            ),
        )
        all_receipts = [item[0] for item in expected_kinds]
        for receipt, expected_kind in expected_kinds:
            if receipt.result.measurement_kind is not expected_kind:
                raise ValueError("founder measurement receipt kind drift")
        if any(
            receipt.result.measurement_kind
            is not FounderMeasurementKind.live_model_hardware
            for receipt in self.live_model_hardware_receipts
        ):
            raise ValueError("live-model measurement receipt kind drift")
        live_receipt_digests = tuple(
            item.receipt_digest_ref for item in self.live_model_hardware_receipts
        )
        if live_receipt_digests != tuple(sorted(live_receipt_digests)):
            raise ValueError("live-model measurement receipts must be sorted")
        all_receipts.extend(self.live_model_hardware_receipts)
        receipt_digests = tuple(item.receipt_digest_ref for item in all_receipts)
        if len(receipt_digests) != len(set(receipt_digests)):
            raise ValueError("founder measurement receipts must be unique")
        if any(
            receipt.result.inference_profile_ref not in TAW08_INFERENCE_PROFILE_REFS
            or receipt.result.observed_hardware_family_ref
            not in TAW08_HARDWARE_FAMILY_REFS
            for receipt in self.live_model_hardware_receipts
        ):
            raise ValueError("live-model measurement profile census drift")
        if any(
            receipt.result.candidate_revision_ref != self.candidate_revision_ref
            or receipt.result.candidate_manifest_digest_ref
            != self.candidate_manifest_digest_ref
            for receipt in all_receipts
        ):
            raise ValueError("founder measurement receipt candidate binding drift")
        if (
            self.exact_head_foundation_receipt.stage != "exact_head"
            or self.exact_head_foundation_receipt.revision_ref
            != self.candidate_revision_ref
        ):
            raise ValueError(
                "exact-head Foundation receipt must bind the candidate revision"
            )
        if TAW08_FOUNDER_DECISION_PUBLIC_KEY_HEX is None:
            raise ValueError("founder decision verification authority is missing")
        if not re.fullmatch(
            r"ed25519-signature-ref:[0-9a-f]{128}",
            self.founder_decision_signature_ref,
        ):
            raise ValueError("founder decision signature ref is invalid")
        try:
            public_key_bytes = bytes.fromhex(TAW08_FOUNDER_DECISION_PUBLIC_KEY_HEX)
            if len(public_key_bytes) != 32:
                raise ValueError("founder decision public key is invalid")
            signature = bytes.fromhex(
                self.founder_decision_signature_ref.removeprefix(
                    "ed25519-signature-ref:"
                )
            )
            Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(
                signature,
                founder_decision_signature_payload(
                    candidate_revision_ref=self.candidate_revision_ref,
                    candidate_manifest_digest_ref=(self.candidate_manifest_digest_ref),
                    measurement_receipt_digest_refs=receipt_digests,
                    exact_head_foundation_receipt_digest_ref=(
                        self.exact_head_foundation_receipt.receipt_digest_ref
                    ),
                    founder_decision_ref=self.founder_decision_ref,
                ),
            )
        except (InvalidSignature, TypeError, ValueError) as exc:
            raise ValueError("founder decision signature verification failed") from exc
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"evidence_digest_ref"})
        )
        if self.evidence_digest_ref != expected:
            raise ValueError("founder acceptance evidence digest binding drift")
        return self


class TAW08AcceptanceReport(_FrozenModel):
    schema_version: Literal["uaa-taw08-acceptance-report.v1"] = (
        "uaa-taw08-acceptance-report.v1"
    )
    contract_ref: Literal["contract-ref:taw08:founder-private-acceptance:v1"] = (
        TAW08_CONTRACT_REF
    )
    evaluator_ref: Literal["evaluator-ref:taw08:deterministic-acceptance:v1"] = (
        TAW08_EVALUATOR_REF
    )
    status: TAW08AcceptanceStatus
    candidate_revision_ref: str
    candidate_manifest_digest_ref: str
    candidate_verification_receipt: _CandidateLockVerificationReceipt | None
    candidate_verification_receipt_digest_ref: str | None
    founder_evidence: FounderPrivateAcceptanceEvidence | None
    founder_evidence_digest_ref: str | None
    evidence_only_delta: EvidenceOnlyDeltaManifest | None
    evidence_only_delta_manifest_digest_ref: str | None
    evidence_only_delta_verification_receipt: (
        _EvidenceOnlyDeltaVerificationReceipt | None
    )
    evidence_only_delta_verification_receipt_digest_ref: str | None
    postmerge_foundation_receipt: FoundationGateReceipt | None
    postmerge_foundation_receipt_digest_ref: str | None
    final_acceptance_publication_receipt: _FinalAcceptancePublicationReceipt | None
    final_acceptance_publication_receipt_digest_ref: str | None
    founder_private_accepted: bool
    founder_evidence_missing_refs: tuple[str, ...]
    failure_refs: tuple[str, ...]
    independent_promotion_blocker_refs: tuple[str, ...]
    independent_promotion_ready: Literal[False] = False
    sealed_holdout_evidence_verified: Literal[False] = False
    public_quality_claims_allowed: Literal[False] = False
    production_authority_added: Literal[False] = False
    runtime_model_calls_added: Literal[False] = False
    provider_calls_added: Literal[False] = False
    execution_authority_added: Literal[False] = False
    raw_content_persisted: Literal[False] = False
    report_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_report(self) -> "TAW08AcceptanceReport":
        _validate_git_ref(self.candidate_revision_ref, "candidate_revision_ref")
        _validate_digest(
            self.candidate_manifest_digest_ref, "candidate_manifest_digest_ref"
        )
        for value, field_name in (
            (self.founder_evidence_digest_ref, "founder_evidence_digest_ref"),
            (
                self.evidence_only_delta_manifest_digest_ref,
                "evidence_only_delta_manifest_digest_ref",
            ),
            (
                self.postmerge_foundation_receipt_digest_ref,
                "postmerge_foundation_receipt_digest_ref",
            ),
            (
                self.candidate_verification_receipt_digest_ref,
                "candidate_verification_receipt_digest_ref",
            ),
            (
                self.evidence_only_delta_verification_receipt_digest_ref,
                "evidence_only_delta_verification_receipt_digest_ref",
            ),
            (
                self.final_acceptance_publication_receipt_digest_ref,
                "final_acceptance_publication_receipt_digest_ref",
            ),
        ):
            if value is not None:
                _validate_digest(value, field_name)
        binding_failures: set[str] = set()
        expected_candidate_receipt_digest = (
            self.candidate_verification_receipt.receipt_digest_ref
            if self.candidate_verification_receipt is not None
            else None
        )
        if (
            self.candidate_verification_receipt_digest_ref
            != expected_candidate_receipt_digest
        ):
            raise ValueError(
                "candidate verification digest must bind the embedded receipt"
            )
        if self.candidate_verification_receipt is not None and (
            self.candidate_verification_receipt.candidate_revision_ref
            != self.candidate_revision_ref
            or self.candidate_verification_receipt.candidate_manifest_digest_ref
            != self.candidate_manifest_digest_ref
        ):
            binding_failures.add(
                "failure-ref:taw08:candidate-verification-binding-drift"
            )
        expected_founder_digest = (
            self.founder_evidence.evidence_digest_ref
            if self.founder_evidence is not None
            else None
        )
        if self.founder_evidence_digest_ref != expected_founder_digest:
            raise ValueError("founder evidence digest must bind the embedded evidence")
        if self.founder_evidence is not None and (
            self.founder_evidence.candidate_revision_ref != self.candidate_revision_ref
            or self.founder_evidence.candidate_manifest_digest_ref
            != self.candidate_manifest_digest_ref
        ):
            binding_failures.add(
                "failure-ref:taw08:founder-evidence-candidate-binding-drift"
            )
        expected_delta_digest = (
            self.evidence_only_delta.manifest_digest_ref
            if self.evidence_only_delta is not None
            else None
        )
        if self.evidence_only_delta_manifest_digest_ref != expected_delta_digest:
            raise ValueError("delta digest must bind the embedded delta manifest")
        if self.evidence_only_delta is not None and (
            self.evidence_only_delta.candidate_revision_ref
            != self.candidate_revision_ref
            or self.evidence_only_delta.candidate_manifest_digest_ref
            != self.candidate_manifest_digest_ref
        ):
            binding_failures.add(
                "failure-ref:taw08:evidence-delta-candidate-binding-drift"
            )
        expected_delta_receipt_digest = (
            self.evidence_only_delta_verification_receipt.receipt_digest_ref
            if self.evidence_only_delta_verification_receipt is not None
            else None
        )
        if (
            self.evidence_only_delta_verification_receipt_digest_ref
            != expected_delta_receipt_digest
        ):
            raise ValueError("delta verification digest must bind the embedded receipt")
        if self.evidence_only_delta_verification_receipt is not None:
            receipt = self.evidence_only_delta_verification_receipt
            expected_published_report_ref = (
                _pre_delta_acceptance_report_fingerprint_ref(
                    candidate_revision_ref=self.candidate_revision_ref,
                    candidate_manifest_digest_ref=(self.candidate_manifest_digest_ref),
                    candidate_verification_receipt=(
                        self.candidate_verification_receipt
                    ),
                    founder_evidence=self.founder_evidence,
                )
            )
            if (
                receipt.published_acceptance_report_fingerprint_ref
                != expected_published_report_ref
            ):
                binding_failures.add(
                    "failure-ref:taw08:published-acceptance-report-binding-drift"
                )
            if self.evidence_only_delta is None:
                binding_failures.add(
                    "failure-ref:taw08:delta-verification-without-manifest"
                )
            elif (
                receipt.candidate_revision_ref != self.candidate_revision_ref
                or receipt.candidate_manifest_digest_ref
                != self.candidate_manifest_digest_ref
                or receipt.delta_revision_ref
                != self.evidence_only_delta.delta_revision_ref
                or receipt.delta_manifest_digest_ref
                != self.evidence_only_delta.manifest_digest_ref
                or receipt.revision_delta_path_census_digest_ref
                != bind_revision_delta_census(
                    candidate_revision_ref=self.candidate_revision_ref,
                    delta_revision_ref=self.evidence_only_delta.delta_revision_ref,
                    path_refs=tuple(
                        item.path_ref for item in self.evidence_only_delta.entries
                    ),
                    history_path_refs=receipt.history_path_refs,
                    commit_count=receipt.commit_count,
                    candidate_ancestor_verified=True,
                    provenance_ref="provenance-ref:git-history-path-census",
                ).census_digest_ref
                or set(receipt.history_path_refs)
                - set(TAW08_ALLOWED_EVIDENCE_ONLY_PATH_REFS)
                or receipt.artifact_count != len(self.evidence_only_delta.entries)
            ):
                binding_failures.add(
                    "failure-ref:taw08:delta-verification-binding-drift"
                )
        expected_postmerge_digest = (
            self.postmerge_foundation_receipt.receipt_digest_ref
            if self.postmerge_foundation_receipt is not None
            else None
        )
        if self.postmerge_foundation_receipt_digest_ref != expected_postmerge_digest:
            raise ValueError(
                "postmerge digest must bind the embedded Foundation receipt"
            )
        if self.postmerge_foundation_receipt is not None:
            if self.postmerge_foundation_receipt.stage != "postmerge":
                binding_failures.add(
                    "failure-ref:taw08:postmerge-foundation-stage-drift"
                )
            if self.evidence_only_delta is None:
                binding_failures.add("failure-ref:taw08:postmerge-delta-missing")
            elif (
                self.postmerge_foundation_receipt.revision_ref
                != self.evidence_only_delta.delta_revision_ref
            ):
                binding_failures.add("failure-ref:taw08:postmerge-delta-revision-drift")
            if self.evidence_only_delta_verification_receipt is None:
                binding_failures.add(
                    "failure-ref:taw08:postmerge-delta-verification-missing"
                )
        expected_publication_digest = (
            self.final_acceptance_publication_receipt.receipt_digest_ref
            if self.final_acceptance_publication_receipt is not None
            else None
        )
        if (
            self.final_acceptance_publication_receipt_digest_ref
            != expected_publication_digest
        ):
            raise ValueError("final publication digest must bind the embedded receipt")
        if self.final_acceptance_publication_receipt is not None:
            publication = self.final_acceptance_publication_receipt
            if (
                self.evidence_only_delta is None
                or self.evidence_only_delta_verification_receipt is None
                or self.postmerge_foundation_receipt is None
            ):
                binding_failures.add(
                    "failure-ref:taw08:final-publication-prerequisite-missing"
                )
            elif (
                publication.candidate_revision_ref != self.candidate_revision_ref
                or publication.candidate_manifest_digest_ref
                != self.candidate_manifest_digest_ref
                or publication.delta_revision_ref
                != self.evidence_only_delta.delta_revision_ref
                or publication.delta_manifest_digest_ref
                != self.evidence_only_delta.manifest_digest_ref
                or publication.delta_verification_receipt_digest_ref
                != self.evidence_only_delta_verification_receipt.receipt_digest_ref
                or publication.postmerge_foundation_receipt_digest_ref
                != self.postmerge_foundation_receipt.receipt_digest_ref
                or publication.published_report_semantic_digest_ref
                != _final_acceptance_semantic_digest(
                    candidate_revision_ref=self.candidate_revision_ref,
                    candidate_manifest_digest_ref=(self.candidate_manifest_digest_ref),
                    founder_evidence_digest_ref=self.founder_evidence_digest_ref,
                    delta=self.evidence_only_delta,
                    delta_verification_receipt=(
                        self.evidence_only_delta_verification_receipt
                    ),
                    postmerge_foundation_receipt=(self.postmerge_foundation_receipt),
                )
            ):
                binding_failures.add(
                    "failure-ref:taw08:final-publication-binding-drift"
                )
        _validate_sorted_refs(
            self.founder_evidence_missing_refs, "founder_evidence_missing_refs"
        )
        _validate_sorted_refs(self.failure_refs, "failure_refs")
        if (
            self.independent_promotion_blocker_refs
            != TAW08_INDEPENDENT_PROMOTION_BLOCKER_REFS
        ):
            raise ValueError("independent promotion blocker census drift")
        known_binding_failure_refs = {
            "failure-ref:taw08:candidate-verification-binding-drift",
            "failure-ref:taw08:delta-verification-binding-drift",
            "failure-ref:taw08:delta-verification-without-manifest",
            "failure-ref:taw08:evidence-delta-candidate-binding-drift",
            "failure-ref:taw08:founder-evidence-candidate-binding-drift",
            "failure-ref:taw08:postmerge-delta-missing",
            "failure-ref:taw08:postmerge-delta-revision-drift",
            "failure-ref:taw08:postmerge-delta-verification-missing",
            "failure-ref:taw08:postmerge-foundation-stage-drift",
            "failure-ref:taw08:published-acceptance-report-binding-drift",
            "failure-ref:taw08:final-publication-binding-drift",
            "failure-ref:taw08:final-publication-prerequisite-missing",
        }
        if set(self.failure_refs) & known_binding_failure_refs != binding_failures:
            raise ValueError("TAW-08 binding failures must be recomputed exactly")
        if self.failure_refs:
            expected_status = TAW08AcceptanceStatus.failed
            expected_founder_accepted = False
        elif (
            self.founder_evidence is None or self.candidate_verification_receipt is None
        ):
            expected_status = TAW08AcceptanceStatus.blocked_missing_founder_evidence
            expected_founder_accepted = False
        elif (
            self.postmerge_foundation_receipt is None
            or self.evidence_only_delta is None
            or self.evidence_only_delta_verification_receipt is None
        ):
            expected_status = (
                TAW08AcceptanceStatus.founder_private_accepted_postmerge_pending
            )
            expected_founder_accepted = True
        elif self.final_acceptance_publication_receipt is None:
            expected_status = (
                TAW08AcceptanceStatus.founder_private_accepted_final_publication_pending
            )
            expected_founder_accepted = True
        else:
            expected_status = (
                TAW08AcceptanceStatus.founder_private_accepted_promotion_blocked
            )
            expected_founder_accepted = True
        if (
            self.status != expected_status
            or self.founder_private_accepted != expected_founder_accepted
        ):
            raise ValueError("TAW-08 acceptance status does not match bound evidence")
        expected_missing = set(TAW08_FOUNDER_EVIDENCE_MISSING_REFS)
        if self.candidate_verification_receipt is not None:
            expected_missing.discard(
                "evidence-missing-ref:taw08:candidate-lock-verification-receipt"
            )
        if self.founder_evidence is not None:
            expected_missing.difference_update(
                set(TAW08_FOUNDER_EVIDENCE_MISSING_REFS)
                - {"evidence-missing-ref:taw08:candidate-lock-verification-receipt"}
            )
        if self.postmerge_foundation_receipt is None:
            expected_missing.add(TAW08_POSTMERGE_EVIDENCE_MISSING_REF)
        if self.evidence_only_delta_verification_receipt is None:
            expected_missing.add(TAW08_DELTA_VERIFICATION_MISSING_REF)
        if self.final_acceptance_publication_receipt is None:
            expected_missing.add(TAW08_FINAL_PUBLICATION_MISSING_REF)
        expected_missing_tuple = tuple(sorted(expected_missing))
        if self.founder_evidence_missing_refs != expected_missing_tuple:
            raise ValueError("TAW-08 missing-evidence census drift")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"report_fingerprint_ref"})
        )
        expected_ref = f"taw08-acceptance-report-ref:{expected}"
        if self.report_fingerprint_ref != expected_ref:
            raise ValueError("TAW-08 acceptance report fingerprint binding drift")
        return self


def _pre_delta_acceptance_report_fingerprint_ref(
    *,
    candidate_revision_ref: str,
    candidate_manifest_digest_ref: str,
    candidate_verification_receipt: _CandidateLockVerificationReceipt | None,
    founder_evidence: FounderPrivateAcceptanceEvidence | None,
) -> str:
    """Rebuild the exact accepted-pending report eligible for publication."""
    missing = set(TAW08_FOUNDER_EVIDENCE_MISSING_REFS)
    failures: set[str] = set()
    if candidate_verification_receipt is not None:
        missing.discard(
            "evidence-missing-ref:taw08:candidate-lock-verification-receipt"
        )
        if (
            candidate_verification_receipt.candidate_revision_ref
            != candidate_revision_ref
            or candidate_verification_receipt.candidate_manifest_digest_ref
            != candidate_manifest_digest_ref
        ):
            failures.add("failure-ref:taw08:candidate-verification-binding-drift")
    if founder_evidence is not None:
        missing.difference_update(
            set(TAW08_FOUNDER_EVIDENCE_MISSING_REFS)
            - {"evidence-missing-ref:taw08:candidate-lock-verification-receipt"}
        )
        if (
            founder_evidence.candidate_revision_ref != candidate_revision_ref
            or founder_evidence.candidate_manifest_digest_ref
            != candidate_manifest_digest_ref
        ):
            failures.add("failure-ref:taw08:founder-evidence-candidate-binding-drift")
    missing.update(
        (
            TAW08_DELTA_VERIFICATION_MISSING_REF,
            TAW08_POSTMERGE_EVIDENCE_MISSING_REF,
            TAW08_FINAL_PUBLICATION_MISSING_REF,
        )
    )
    founder_accepted = (
        not failures
        and founder_evidence is not None
        and candidate_verification_receipt is not None
    )
    status = (
        TAW08AcceptanceStatus.failed
        if failures
        else TAW08AcceptanceStatus.founder_private_accepted_postmerge_pending
        if founder_accepted
        else TAW08AcceptanceStatus.blocked_missing_founder_evidence
    )
    payload = {
        "schema_version": "uaa-taw08-acceptance-report.v1",
        "contract_ref": TAW08_CONTRACT_REF,
        "evaluator_ref": TAW08_EVALUATOR_REF,
        "status": status.value,
        "candidate_revision_ref": candidate_revision_ref,
        "candidate_manifest_digest_ref": candidate_manifest_digest_ref,
        "candidate_verification_receipt": (
            candidate_verification_receipt.model_dump(mode="json")
            if candidate_verification_receipt
            else None
        ),
        "candidate_verification_receipt_digest_ref": (
            candidate_verification_receipt.receipt_digest_ref
            if candidate_verification_receipt
            else None
        ),
        "founder_evidence": (
            founder_evidence.model_dump(mode="json") if founder_evidence else None
        ),
        "founder_evidence_digest_ref": (
            founder_evidence.evidence_digest_ref if founder_evidence else None
        ),
        "evidence_only_delta": None,
        "evidence_only_delta_manifest_digest_ref": None,
        "evidence_only_delta_verification_receipt": None,
        "evidence_only_delta_verification_receipt_digest_ref": None,
        "postmerge_foundation_receipt": None,
        "postmerge_foundation_receipt_digest_ref": None,
        "final_acceptance_publication_receipt": None,
        "final_acceptance_publication_receipt_digest_ref": None,
        "founder_private_accepted": founder_accepted,
        "founder_evidence_missing_refs": tuple(sorted(missing)),
        "failure_refs": tuple(sorted(failures)),
        "independent_promotion_blocker_refs": TAW08_INDEPENDENT_PROMOTION_BLOCKER_REFS,
        "independent_promotion_ready": False,
        "sealed_holdout_evidence_verified": False,
        "public_quality_claims_allowed": False,
        "production_authority_added": False,
        "runtime_model_calls_added": False,
        "provider_calls_added": False,
        "execution_authority_added": False,
        "raw_content_persisted": False,
    }
    return f"taw08-acceptance-report-ref:{canonical_digest(payload)}"


def _final_acceptance_semantic_digest(
    *,
    candidate_revision_ref: str,
    candidate_manifest_digest_ref: str,
    founder_evidence_digest_ref: str | None,
    delta: EvidenceOnlyDeltaManifest,
    delta_verification_receipt: _EvidenceOnlyDeltaVerificationReceipt,
    postmerge_foundation_receipt: FoundationGateReceipt,
) -> str:
    return canonical_digest(
        {
            "schema_version": "uaa-taw08-final-acceptance-semantic.v1",
            "status": (
                TAW08AcceptanceStatus.founder_private_accepted_promotion_blocked.value
            ),
            "candidate_revision_ref": candidate_revision_ref,
            "candidate_manifest_digest_ref": candidate_manifest_digest_ref,
            "founder_evidence_digest_ref": founder_evidence_digest_ref,
            "delta_revision_ref": delta.delta_revision_ref,
            "delta_manifest_digest_ref": delta.manifest_digest_ref,
            "delta_verification_receipt_digest_ref": (
                delta_verification_receipt.receipt_digest_ref
            ),
            "postmerge_foundation_receipt_digest_ref": (
                postmerge_foundation_receipt.receipt_digest_ref
            ),
            "independent_promotion_ready": False,
            "public_quality_claims_allowed": False,
        }
    )


def build_final_acceptance_publication_artifact(
    *,
    candidate_revision_ref: str,
    candidate_manifest_digest_ref: str,
    founder_evidence_digest_ref: str,
    delta: EvidenceOnlyDeltaManifest,
    delta_verification_receipt: _EvidenceOnlyDeltaVerificationReceipt,
    postmerge_foundation_receipt: FoundationGateReceipt,
) -> FinalAcceptancePublicationArtifact:
    semantic_digest = _final_acceptance_semantic_digest(
        candidate_revision_ref=candidate_revision_ref,
        candidate_manifest_digest_ref=candidate_manifest_digest_ref,
        founder_evidence_digest_ref=founder_evidence_digest_ref,
        delta=delta,
        delta_verification_receipt=delta_verification_receipt,
        postmerge_foundation_receipt=postmerge_foundation_receipt,
    )
    return FinalAcceptancePublicationArtifact(
        candidate_revision_ref=candidate_revision_ref,
        candidate_manifest_digest_ref=candidate_manifest_digest_ref,
        founder_evidence_digest_ref=founder_evidence_digest_ref,
        delta_revision_ref=delta.delta_revision_ref,
        delta_manifest_digest_ref=delta.manifest_digest_ref,
        delta_verification_receipt_digest_ref=(
            delta_verification_receipt.receipt_digest_ref
        ),
        postmerge_foundation_receipt_digest_ref=(
            postmerge_foundation_receipt.receipt_digest_ref
        ),
        final_status=(
            TAW08AcceptanceStatus.founder_private_accepted_promotion_blocked.value
        ),
        published_report_semantic_digest_ref=semantic_digest,
        independent_promotion_ready=False,
        public_quality_claims_allowed=False,
        raw_content_persisted=False,
    )


def _verify_and_bind_final_acceptance_publication(
    *,
    publication_revision_ref: str,
    publication_path_ref: str,
    publication_content: bytes,
    publication_history_census: _PublicationHistoryCensus,
    candidate_revision_ref: str,
    candidate_manifest_digest_ref: str,
    founder_evidence_digest_ref: str,
    delta: EvidenceOnlyDeltaManifest,
    delta_verification_receipt: _EvidenceOnlyDeltaVerificationReceipt,
    postmerge_foundation_receipt: FoundationGateReceipt,
) -> _FinalAcceptancePublicationReceipt:
    _validate_git_ref(publication_revision_ref, "publication_revision_ref")
    if (
        publication_history_census.delta_revision_ref != delta.delta_revision_ref
        or publication_history_census.publication_revision_ref
        != publication_revision_ref
    ):
        raise ValueError("final publication history binding drift")
    if publication_path_ref != TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF:
        raise ValueError("final publication path is not canonical")
    if (
        not isinstance(publication_content, bytes)
        or len(publication_content) > TAW08_MAX_EVIDENCE_DELTA_ARTIFACT_BYTES
    ):
        raise ValueError("final publication content shape or size is invalid")
    expected_artifact = build_final_acceptance_publication_artifact(
        candidate_revision_ref=candidate_revision_ref,
        candidate_manifest_digest_ref=candidate_manifest_digest_ref,
        founder_evidence_digest_ref=founder_evidence_digest_ref,
        delta=delta,
        delta_verification_receipt=delta_verification_receipt,
        postmerge_foundation_receipt=postmerge_foundation_receipt,
    )
    try:
        raw_payload = json.loads(publication_content)
        if durable_payload_has_forbidden_fields(raw_payload):
            raise ValueError("final publication contains forbidden durable fields")
        published_artifact = FinalAcceptancePublicationArtifact.model_validate(
            raw_payload
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, RecursionError):
        raise ValueError("final publication artifact schema is invalid") from None
    if published_artifact != expected_artifact:
        raise ValueError("final publication artifact binding drift")
    content_digest = f"sha256:{hashlib.sha256(publication_content).hexdigest()}"
    payload = {
        "schema_version": "uaa-taw08-final-acceptance-publication.v1",
        "candidate_revision_ref": candidate_revision_ref,
        "candidate_manifest_digest_ref": candidate_manifest_digest_ref,
        "delta_revision_ref": delta.delta_revision_ref,
        "delta_manifest_digest_ref": delta.manifest_digest_ref,
        "delta_verification_receipt_digest_ref": (
            delta_verification_receipt.receipt_digest_ref
        ),
        "postmerge_foundation_receipt_digest_ref": (
            postmerge_foundation_receipt.receipt_digest_ref
        ),
        "publication_revision_ref": publication_revision_ref,
        "publication_history_census": publication_history_census.model_dump(
            mode="json"
        ),
        "publication_history_census_digest_ref": (
            publication_history_census.census_digest_ref
        ),
        "publication_path_ref": publication_path_ref,
        "publication_content_digest_ref": content_digest,
        "final_status": expected_artifact.final_status,
        "published_report_semantic_digest_ref": (
            expected_artifact.published_report_semantic_digest_ref
        ),
        "publication_ref": f"publication-ref:taw08:final:{content_digest}",
        "verified": True,
        "raw_content_persisted": False,
    }
    return _FinalAcceptancePublicationReceipt.model_validate(
        {**payload, "receipt_digest_ref": canonical_digest(payload)}
    )


def bind_evidence_only_delta(**values: object) -> EvidenceOnlyDeltaManifest:
    _validate_builder_keys(EvidenceOnlyDeltaManifest, values, "manifest_digest_ref")
    normalized = dict(values)
    entries = normalized.get("entries")
    if isinstance(entries, (list, tuple)):
        normalized["entries"] = tuple(
            item
            if isinstance(item, EvidenceOnlyDeltaEntry)
            else EvidenceOnlyDeltaEntry.model_validate(item)
            for item in entries
        )
    payload = EvidenceOnlyDeltaManifest.model_construct(
        **normalized,
        manifest_digest_ref="sha256:" + "0" * 64,
    ).model_dump(mode="json", exclude={"manifest_digest_ref"})
    return EvidenceOnlyDeltaManifest.model_validate(
        {**payload, "manifest_digest_ref": canonical_digest(payload)}
    )


def bind_revision_path_census(**values: object) -> RevisionPathCensus:
    _validate_builder_keys(RevisionPathCensus, values, "census_digest_ref")
    payload = RevisionPathCensus.model_construct(
        **values,
        census_digest_ref="sha256:" + "0" * 64,
    ).model_dump(mode="json", exclude={"census_digest_ref"})
    return RevisionPathCensus.model_validate(
        {**payload, "census_digest_ref": canonical_digest(payload)}
    )


def bind_revision_delta_census(**values: object) -> RevisionDeltaCensus:
    _validate_builder_keys(RevisionDeltaCensus, values, "census_digest_ref")
    payload = RevisionDeltaCensus.model_construct(
        **values,
        census_digest_ref="sha256:" + "0" * 64,
    ).model_dump(mode="json", exclude={"census_digest_ref"})
    return RevisionDeltaCensus.model_validate(
        {**payload, "census_digest_ref": canonical_digest(payload)}
    )


def _bind_publication_history_census(
    **values: object,
) -> _PublicationHistoryCensus:
    _validate_builder_keys(_PublicationHistoryCensus, values, "census_digest_ref")
    payload = _PublicationHistoryCensus.model_construct(
        **values,
        census_digest_ref="sha256:" + "0" * 64,
    ).model_dump(mode="json", exclude={"census_digest_ref"})
    return _PublicationHistoryCensus.model_validate(
        {**payload, "census_digest_ref": canonical_digest(payload)}
    )


def _bind_foundation_gate_receipt(**values: object) -> FoundationGateReceipt:
    _validate_builder_keys(FoundationGateReceipt, values, "receipt_digest_ref")
    payload = FoundationGateReceipt.model_construct(
        **values,
        receipt_digest_ref="sha256:" + "0" * 64,
    ).model_dump(mode="json", exclude={"receipt_digest_ref"})
    return FoundationGateReceipt.model_validate(
        {**payload, "receipt_digest_ref": canonical_digest(payload)}
    )


def _bind_evaluator_environment_receipt(
    **values: object,
) -> _EvaluatorEnvironmentReceipt:
    _validate_builder_keys(
        _EvaluatorEnvironmentReceipt,
        values,
        "receipt_digest_ref",
    )
    payload = _EvaluatorEnvironmentReceipt.model_construct(
        **values,
        receipt_digest_ref="sha256:" + "0" * 64,
    ).model_dump(mode="json", exclude={"receipt_digest_ref"})
    return _EvaluatorEnvironmentReceipt.model_validate(
        {**payload, "receipt_digest_ref": canonical_digest(payload)}
    )


def _verify_and_bind_foundation_gate_report(
    *,
    report: object,
    stage: Literal["exact_head", "postmerge"],
    revision_ref: str,
    evaluator_environment_receipt: _EvaluatorEnvironmentReceipt,
) -> FoundationGateReceipt:
    _validate_git_ref(revision_ref, "revision_ref")
    reports_module = sys.modules.get("ultimate_ai_agent.core.gate.reports")
    criteria_module = sys.modules.get("ultimate_ai_agent.core.gate.criteria")
    foundation_report_type = (
        getattr(reports_module, "FoundationGateReport", None)
        if reports_module is not None
        else None
    )
    if foundation_report_type is None or type(report) is not foundation_report_type:
        raise ValueError("Foundation receipt requires a typed gate report")
    default_criteria = (
        getattr(criteria_module, "default_foundation_gate_criteria", None)
        if criteria_module is not None
        else None
    )
    if not callable(default_criteria):
        raise ValueError("Foundation receipt requires the canonical gate census")
    report_payload = report.model_dump(mode="json")
    expected_fields = {
        "report_id",
        "version",
        "generated_at",
        "overall_status",
        "results",
        "passed_count",
        "failed_count",
        "warning_count",
        "blocked_count",
        "summary",
        "next_recommended_action",
        "evaluated_revision_ref",
        "evaluation_provenance_digest_ref",
        "event_ref",
        "trace_id",
        "command_mode",
        "command_receipts",
        "latency_gate",
        "release_verification_lanes",
    }
    if set(report_payload) != expected_fields:
        raise ValueError("Foundation receipt requires a validated gate report")
    results = report_payload["results"]
    if not isinstance(results, list) or any(
        not isinstance(item, dict) or not isinstance(item.get("status"), str)
        for item in results
    ):
        raise ValueError("Foundation receipt requires a validated gate report")
    statuses = ("passed", "failed", "warning", "blocked")
    criterion_ids = tuple(item.get("criterion_id") for item in results)
    expected_criterion_ids = tuple(
        sorted(item.criterion_id for item in default_criteria())
    )
    counts = {
        status: sum(item["status"] == status for item in results) for status in statuses
    }
    expected_status = (
        "failed"
        if counts["failed"]
        else "blocked"
        if counts["blocked"]
        else "warning"
        if counts["warning"]
        else "passed"
    )
    reports_digest_builder = getattr(
        reports_module,
        "foundation_gate_evaluation_provenance_digest",
        None,
    )
    if (
        report_payload["evaluated_revision_ref"] != revision_ref
        or not callable(reports_digest_builder)
        or report_payload["evaluation_provenance_digest_ref"]
        != reports_digest_builder(report)
    ):
        raise ValueError("Foundation report revision provenance drift")
    if (
        not results
        or criterion_ids != expected_criterion_ids
        or len(criterion_ids) != len(set(criterion_ids))
        or report_payload["overall_status"] != "passed"
        or report_payload["overall_status"] != expected_status
        or report_payload["passed_count"] != counts["passed"]
        or report_payload["failed_count"] != counts["failed"]
        or report_payload["warning_count"] != counts["warning"]
        or report_payload["blocked_count"] != counts["blocked"]
        or report_payload["command_mode"] != "report-only"
    ):
        raise ValueError("Foundation receipt requires a passing report-only gate")
    command_receipts = report_payload["command_receipts"]
    if (
        not isinstance(command_receipts, list)
        or len(command_receipts) != 1
        or command_receipts[0].get("command_ref")
        != "command:foundation_gate.typed_report"
        or command_receipts[0].get("command_mode") != "report-only"
        or command_receipts[0].get("status") != "report_only"
        or command_receipts[0].get("satisfied_by") != "typed-foundation-gate-evaluator"
        or "local read/probe code" not in command_receipts[0].get("safe_summary", "")
    ):
        raise ValueError("Foundation receipt requires report-only command provenance")
    safety_payload = {
        **report_payload,
        "results": [
            {key: value for key, value in item.items() if key != "criterion_id"}
            for item in results
        ],
    }
    if durable_payload_has_forbidden_fields(safety_payload):
        raise ValueError("Foundation report contains unsafe durable evidence")
    report_id = report_payload["report_id"]
    if not isinstance(report_id, str):
        raise ValueError("Foundation receipt requires a validated gate report")
    return _bind_foundation_gate_receipt(
        stage=stage,
        revision_ref=revision_ref,
        report_digest_ref=canonical_digest(report_payload),
        report_ref=f"foundation-report-ref:{report_id.replace('_', '-')}",
        evaluator_environment_receipt=evaluator_environment_receipt,
        evaluator_environment_digest_ref=(
            evaluator_environment_receipt.receipt_digest_ref
        ),
    )


def verify_and_bind_founder_measurement_result(
    result: FounderMeasurementResult,
) -> FounderMeasurementReceipt:
    if result.threshold_decision != "passed":
        raise ValueError("founder measurement threshold decision did not pass")
    result_digest_ref = canonical_digest(result.model_dump(mode="json"))
    payload = FounderMeasurementReceipt.model_construct(
        result=result,
        result_digest_ref=result_digest_ref,
        verifier_ref="verifier-ref:taw08:founder-measurement:v1",
        verified=True,
        receipt_digest_ref="sha256:" + "0" * 64,
    ).model_dump(mode="json", exclude={"receipt_digest_ref"})
    return FounderMeasurementReceipt.model_validate(
        {**payload, "receipt_digest_ref": canonical_digest(payload)}
    )


def bind_founder_private_acceptance_evidence(
    **values: object,
) -> FounderPrivateAcceptanceEvidence:
    _validate_builder_keys(
        FounderPrivateAcceptanceEvidence, values, "evidence_digest_ref"
    )
    normalized = dict(values)
    receipt = normalized.get("exact_head_foundation_receipt")
    if isinstance(receipt, dict):
        normalized["exact_head_foundation_receipt"] = (
            FoundationGateReceipt.model_validate(receipt)
        )
    for field_name in (
        "stale_cache_recovery_receipt",
        "routing_confidence_receipt",
        "response_scoring_receipt",
        "end_to_end_journey_receipt",
    ):
        measurement = normalized.get(field_name)
        if isinstance(measurement, dict):
            normalized[field_name] = FounderMeasurementReceipt.model_validate(
                measurement
            )
    live_measurements = normalized.get("live_model_hardware_receipts")
    if isinstance(live_measurements, (list, tuple)):
        normalized["live_model_hardware_receipts"] = tuple(
            item
            if isinstance(item, FounderMeasurementReceipt)
            else FounderMeasurementReceipt.model_validate(item)
            for item in live_measurements
        )
    payload = FounderPrivateAcceptanceEvidence.model_construct(
        **normalized,
        evidence_digest_ref="sha256:" + "0" * 64,
    ).model_dump(mode="json", exclude={"evidence_digest_ref"})
    return FounderPrivateAcceptanceEvidence.model_validate(
        {**payload, "evidence_digest_ref": canonical_digest(payload)}
    )


def _bind_candidate_lock_verification_receipt(
    *,
    candidate_lock: CandidateLock,
    expected_path_refs: tuple[str, ...],
    revision_content_by_path_ref: Mapping[str, bytes],
    source_projection: SourceProjection,
    source_closure: SourceDependencyClosure,
    closure_content_by_path_ref: Mapping[str, bytes],
    revision_path_census: RevisionPathCensus,
    evaluator_environment_receipt: _EvaluatorEnvironmentReceipt,
    executing_source_path_refs: tuple[str, ...],
    executing_source_census_digest_ref: str,
) -> _CandidateLockVerificationReceipt:
    if len(expected_path_refs) > TAW08_MAX_CANDIDATE_PATHS:
        raise ValueError("candidate verification path bound exceeded")
    if expected_path_refs != tuple(sorted(expected_path_refs)) or len(
        expected_path_refs
    ) != len(set(expected_path_refs)):
        raise ValueError("candidate verification path census must be unique and sorted")
    if not set(TAW08_REQUIRED_ACCEPTANCE_PATH_REFS) <= set(expected_path_refs):
        raise ValueError("candidate verification path census is incomplete")
    for content_by_path_ref in (
        revision_content_by_path_ref,
        closure_content_by_path_ref,
    ):
        if len(content_by_path_ref) > TAW08_MAX_CANDIDATE_PATHS:
            raise ValueError("candidate verification content path bound exceeded")
        if any(
            not isinstance(content, bytes)
            or len(content) > TAW08_MAX_CANDIDATE_ARTIFACT_BYTES
            for content in content_by_path_ref.values()
        ):
            raise ValueError("candidate verification content shape or size is invalid")
    if (
        len(source_projection.entries) > TAW08_MAX_CANDIDATE_PATHS
        or len(source_closure.entries) > TAW08_MAX_CANDIDATE_PATHS
    ):
        raise ValueError("candidate verification source path bound exceeded")
    if revision_path_census.revision_ref != candidate_lock.git_revision_ref:
        raise ValueError("revision path census must bind the candidate revision")
    available_path_refs = set(revision_path_census.path_refs)
    revision_gate_paths = {
        path_ref
        for path_ref in revision_path_census.path_refs
        if path_ref.startswith(TAW08_FOUNDATION_GATE_SOURCE_PREFIX)
        and path_ref.endswith(".py")
    }
    failures = set(
        verify_candidate_lock(
            candidate_lock,
            expected_path_refs=expected_path_refs,
            revision_content_by_path_ref=dict(revision_content_by_path_ref),
        )
    )
    failures.update(
        verify_source_dependency_closure(
            source_closure,
            source_projection=source_projection,
            content_by_path_ref=closure_content_by_path_ref,
            available_path_refs=available_path_refs,
            allow_unresolved_dynamic_import_path_refs=set(
                TAW08_UNRESOLVED_DYNAMIC_IMPORT_PATH_REFS
            ),
        )
    )
    if (
        source_projection.source_revision_ref != candidate_lock.git_revision_ref
        or source_closure.source_revision_ref != candidate_lock.git_revision_ref
    ):
        failures.add("failure-ref:taw08:candidate-source-revision-drift")
    candidate_source_entries = {
        item.path_ref: item
        for item in candidate_lock.entries
        if item.path_ref.startswith("repo-path-ref:src/")
        and item.path_ref.endswith(".py")
    }
    candidate_gate_entries = {
        item.path_ref
        for item in candidate_lock.entries
        if item.path_ref.startswith(TAW08_FOUNDATION_GATE_SOURCE_PREFIX)
        and item.path_ref.endswith(".py")
    }
    if candidate_gate_entries != revision_gate_paths:
        failures.add("failure-ref:taw08:foundation-gate-source-census-drift")
    projection_entries = {item.path_ref: item for item in source_projection.entries}
    closure_entries = {item.path_ref: item for item in source_closure.entries}
    if set(candidate_source_entries) != set(projection_entries):
        failures.add("failure-ref:taw08:candidate-source-projection-census-drift")
    for path_ref, candidate_entry in candidate_source_entries.items():
        projection_entry = projection_entries.get(path_ref)
        closure_entry = closure_entries.get(path_ref)
        if (
            projection_entry is not None
            and projection_entry.content_digest_ref
            != candidate_entry.content_digest_ref
        ):
            failures.add("failure-ref:taw08:candidate-source-projection-content-drift")
        if closure_entry is None:
            failures.add("failure-ref:taw08:candidate-source-closure-incomplete")
        elif closure_entry.content_digest_ref != candidate_entry.content_digest_ref:
            failures.add("failure-ref:taw08:candidate-source-closure-content-drift")
    environment_entries = {
        item.path_ref: item
        for item in candidate_lock.entries
        if item.path_ref in TAW08_REQUIRED_ENVIRONMENT_PATH_REFS
    }
    if set(environment_entries) != set(TAW08_REQUIRED_ENVIRONMENT_PATH_REFS):
        failures.add("failure-ref:taw08:evaluator-environment-census-drift")
    else:
        if (
            evaluator_environment_receipt.pyproject_digest_ref
            != environment_entries["repo-path-ref:pyproject.toml"].content_digest_ref
            or evaluator_environment_receipt.uv_lock_digest_ref
            != environment_entries["repo-path-ref:uv.lock"].content_digest_ref
        ):
            failures.add("failure-ref:taw08:evaluator-environment-lock-drift")
    repository_verifier_entries = {
        item.path_ref: item
        for item in candidate_lock.entries
        if item.path_ref == TAW08_REPOSITORY_VERIFIER_PATH_REF
    }
    if set(repository_verifier_entries) != {TAW08_REPOSITORY_VERIFIER_PATH_REF}:
        failures.add("failure-ref:taw08:repository-verifier-census-drift")
    if failures:
        raise ValueError(
            f"candidate lock verification failed: {tuple(sorted(failures))}"
        )
    payload = {
        "schema_version": "uaa-taw08-candidate-lock-verification.v1",
        "candidate_revision_ref": candidate_lock.git_revision_ref,
        "candidate_manifest_digest_ref": candidate_lock.manifest_digest_ref,
        "source_projection_digest_ref": source_projection.projection_digest_ref,
        "source_closure_digest_ref": source_closure.closure_digest_ref,
        "path_census_digest_ref": revision_path_census.census_digest_ref,
        "repository_verifier_digest_ref": repository_verifier_entries[
            TAW08_REPOSITORY_VERIFIER_PATH_REF
        ].content_digest_ref,
        "executing_source_path_refs": executing_source_path_refs,
        "executing_source_census_digest_ref": executing_source_census_digest_ref,
        "evaluator_environment_receipt": evaluator_environment_receipt.model_dump(
            mode="json"
        ),
        "evaluator_environment_digest_ref": (
            evaluator_environment_receipt.receipt_digest_ref
        ),
        "verifier_ref": "verifier-ref:taw08:candidate-lock:v1",
        "verified": True,
    }
    return _CandidateLockVerificationReceipt.model_validate(
        {**payload, "receipt_digest_ref": canonical_digest(payload)}
    )


def redacted_acceptance_report_artifact(
    report: TAW08AcceptanceReport,
) -> RedactedAcceptanceReportArtifact:
    return RedactedAcceptanceReportArtifact(
        report_fingerprint_ref=report.report_fingerprint_ref,
        status=report.status,
        candidate_revision_ref=report.candidate_revision_ref,
        candidate_manifest_digest_ref=report.candidate_manifest_digest_ref,
        founder_evidence_digest_ref=report.founder_evidence_digest_ref,
    )


def _parse_bounded_claim_reconciliation_markdown(
    path_ref: str,
    content: bytes,
    candidate_content: bytes | None,
) -> ClaimReconciliationArtifact | None:
    if path_ref not in TAW08_ACTIVE_TRUTH_PATH_REFS or candidate_content is None:
        return None
    try:
        rendered = content.decode("utf-8")
        candidate_rendered = candidate_content.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if any(
        text.count(marker) != 1
        for text in (rendered, candidate_rendered)
        for marker in (
            TAW08_RECONCILIATION_START,
            TAW08_RECONCILIATION_JSON,
            TAW08_RECONCILIATION_END,
        )
    ):
        return None

    def split(text: str) -> tuple[str, str, str, str] | None:
        prefix, marker, remainder = text.partition(TAW08_RECONCILIATION_START)
        narrative, json_marker, json_and_suffix = remainder.partition(
            TAW08_RECONCILIATION_JSON
        )
        body, end_marker, suffix = json_and_suffix.partition(TAW08_RECONCILIATION_END)
        if not marker or not json_marker or not end_marker:
            return None
        return prefix, narrative.strip(), body.strip(), suffix

    changed_parts = split(rendered)
    candidate_parts = split(candidate_rendered)
    if (
        changed_parts is None
        or candidate_parts is None
        or changed_parts[0] != candidate_parts[0]
        or changed_parts[3] != candidate_parts[3]
    ):
        return None
    try:
        payload = json.loads(changed_parts[2])
        if durable_payload_has_forbidden_fields(payload):
            return None
        artifact = ClaimReconciliationArtifact.model_validate(payload)
        if (
            len(artifact.entries) != 1
            or artifact.entries[0].claim_ref
            != TAW08_RECONCILIATION_CLAIM_REFS[path_ref]
        ):
            return None
        expected_narrative = TAW08_RECONCILIATION_NARRATIVES[path_ref].get(
            artifact.entries[0].status.value
        )
        if expected_narrative is None or changed_parts[1] != expected_narrative:
            return None
        return artifact
    except (json.JSONDecodeError, ValidationError, ValueError, RecursionError):
        return None


def _parse_evidence_delta_artifact(
    entry: EvidenceOnlyDeltaEntry,
    content: bytes,
    candidate_content: bytes | None,
) -> _FrozenModel | None:
    if (
        entry.artifact_kind is EvidenceOnlyArtifactKind.claim_reconciliation
        and entry.path_ref in TAW08_ACTIVE_TRUTH_PATH_REFS
    ):
        return _parse_bounded_claim_reconciliation_markdown(
            entry.path_ref,
            content,
            candidate_content,
        )
    try:
        payload = json.loads(content)
        if durable_payload_has_forbidden_fields(payload):
            return None
        if entry.artifact_kind is EvidenceOnlyArtifactKind.acceptance_report:
            artifact: _FrozenModel = RedactedAcceptanceReportArtifact.model_validate(
                payload
            )
        elif entry.artifact_kind is EvidenceOnlyArtifactKind.immutable_evidence_refs:
            artifact = ImmutableEvidenceRefsArtifact.model_validate(payload)
        else:
            artifact = ClaimReconciliationArtifact.model_validate(payload)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValidationError,
        ValueError,
        RecursionError,
    ):
        return None
    return artifact


def verify_evidence_only_delta(
    *,
    candidate_lock: CandidateLock,
    delta: EvidenceOnlyDeltaManifest,
    changed_content_by_path_ref: Mapping[str, bytes],
    revision_delta_census: RevisionDeltaCensus,
    candidate_content_by_path_ref: Mapping[str, bytes] | None = None,
    validated_acceptance_reports_by_path_ref: Mapping[str, TAW08AcceptanceReport]
    | None = None,
) -> tuple[str, ...]:
    failures: set[str] = set()
    validated_acceptance_reports_by_path_ref = (
        validated_acceptance_reports_by_path_ref or {}
    )
    candidate_content_by_path_ref = candidate_content_by_path_ref or {}
    revision_delta_path_refs = revision_delta_census.path_refs
    if (
        len(changed_content_by_path_ref) > TAW08_MAX_EVIDENCE_DELTA_ENTRIES
        or len(revision_delta_path_refs) > TAW08_MAX_EVIDENCE_DELTA_ENTRIES
    ):
        return ("failure-ref:taw08:evidence-delta-path-bound-exceeded",)
    if revision_delta_path_refs != tuple(sorted(revision_delta_path_refs)) or len(
        revision_delta_path_refs
    ) != len(set(revision_delta_path_refs)):
        return ("failure-ref:taw08:revision-delta-path-census-invalid",)
    allowed_refs = set(candidate_lock.evidence_only_delta_path_refs)
    candidate_refs = {item.path_ref for item in candidate_lock.entries}
    actual_refs = set(changed_content_by_path_ref)
    entry_by_ref = {item.path_ref: item for item in delta.entries}
    acceptance_entry = entry_by_ref.get(TAW08_ACCEPTANCE_REPORT_PATH_REF)
    if (
        acceptance_entry is None
        or acceptance_entry.artifact_kind
        is not EvidenceOnlyArtifactKind.acceptance_report
    ):
        failures.add("failure-ref:taw08:evidence-delta-acceptance-report-missing")
    for truth_path_ref in TAW08_ACTIVE_TRUTH_PATH_REFS:
        truth_entry = entry_by_ref.get(truth_path_ref)
        if (
            truth_entry is None
            or truth_entry.artifact_kind
            is not EvidenceOnlyArtifactKind.claim_reconciliation
        ):
            failures.add("failure-ref:taw08:active-truth-reconciliation-missing")
    if (
        revision_delta_census.candidate_revision_ref != candidate_lock.git_revision_ref
        or revision_delta_census.delta_revision_ref != delta.delta_revision_ref
    ):
        failures.add("failure-ref:taw08:revision-delta-binding-drift")
    if (
        delta.candidate_revision_ref != candidate_lock.git_revision_ref
        or delta.candidate_manifest_digest_ref != candidate_lock.manifest_digest_ref
    ):
        failures.add("failure-ref:taw08:evidence-delta-candidate-binding-drift")
    if set(entry_by_ref) != actual_refs:
        failures.add("failure-ref:taw08:evidence-delta-path-census-drift")
    if set(revision_delta_path_refs) != actual_refs:
        failures.add("failure-ref:taw08:revision-delta-path-census-drift")
    if set(revision_delta_census.history_path_refs) - allowed_refs:
        failures.add("failure-ref:taw08:revision-history-unapproved-path")
    if actual_refs - allowed_refs:
        failures.add("failure-ref:taw08:evidence-delta-unapproved-path")
    if actual_refs & candidate_refs:
        failures.add("failure-ref:taw08:evidence-delta-acceptance-path-overlap")
    for path_ref, content in changed_content_by_path_ref.items():
        entry = entry_by_ref.get(path_ref)
        if entry is None:
            continue
        if not isinstance(content, bytes):
            failures.add("failure-ref:taw08:evidence-delta-content-shape-invalid")
            continue
        if len(content) > TAW08_MAX_EVIDENCE_DELTA_ARTIFACT_BYTES:
            failures.add("failure-ref:taw08:evidence-delta-content-bound-exceeded")
            continue
        artifact = _parse_evidence_delta_artifact(
            entry,
            content,
            candidate_content_by_path_ref.get(path_ref),
        )
        if artifact is None:
            failures.add("failure-ref:taw08:evidence-delta-artifact-schema-invalid")
            continue
        if entry.artifact_kind is EvidenceOnlyArtifactKind.acceptance_report:
            validated_report = validated_acceptance_reports_by_path_ref.get(path_ref)
            if (
                validated_report is None
                or validated_report.candidate_revision_ref
                != candidate_lock.git_revision_ref
                or validated_report.candidate_manifest_digest_ref
                != candidate_lock.manifest_digest_ref
                or validated_report.status
                is not TAW08AcceptanceStatus.founder_private_accepted_postmerge_pending
                or artifact != redacted_acceptance_report_artifact(validated_report)
            ):
                failures.add(
                    "failure-ref:taw08:evidence-delta-acceptance-report-binding-drift"
                )
        elif entry.path_ref in TAW08_ACTIVE_TRUTH_PATH_REFS:
            if (
                not isinstance(artifact, ClaimReconciliationArtifact)
                or artifact.entries[0].status is not ReconciledClaimStatus.implemented
            ):
                failures.add("failure-ref:taw08:active-truth-status-not-implemented")
            else:
                accepted_report = validated_acceptance_reports_by_path_ref.get(
                    TAW08_ACCEPTANCE_REPORT_PATH_REF
                )
                expected_evidence_refs = (
                    tuple(
                        sorted(
                            (
                                accepted_report.report_fingerprint_ref,
                                accepted_report.founder_evidence_digest_ref,
                            )
                        )
                    )
                    if accepted_report is not None
                    and accepted_report.founder_evidence_digest_ref is not None
                    else None
                )
                if (
                    expected_evidence_refs is not None
                    and artifact.entries[0].evidence_refs != expected_evidence_refs
                ):
                    failures.add(
                        "failure-ref:taw08:active-truth-evidence-binding-drift"
                    )
        digest = f"sha256:{hashlib.sha256(content).hexdigest()}"
        if entry.content_digest_ref != digest:
            failures.add("failure-ref:taw08:evidence-delta-content-drift")
    return tuple(sorted(failures))


def _verify_and_bind_evidence_only_delta(
    *,
    candidate_lock: CandidateLock,
    delta: EvidenceOnlyDeltaManifest,
    changed_content_by_path_ref: Mapping[str, bytes],
    revision_delta_census: RevisionDeltaCensus,
    candidate_content_by_path_ref: Mapping[str, bytes] | None = None,
    validated_acceptance_reports_by_path_ref: Mapping[str, TAW08AcceptanceReport]
    | None = None,
) -> _EvidenceOnlyDeltaVerificationReceipt:
    failures = verify_evidence_only_delta(
        candidate_lock=candidate_lock,
        delta=delta,
        changed_content_by_path_ref=changed_content_by_path_ref,
        revision_delta_census=revision_delta_census,
        candidate_content_by_path_ref=candidate_content_by_path_ref,
        validated_acceptance_reports_by_path_ref=(
            validated_acceptance_reports_by_path_ref
        ),
    )
    if failures:
        raise ValueError(f"evidence-only delta verification failed: {failures}")
    published_report = validated_acceptance_reports_by_path_ref[
        TAW08_ACCEPTANCE_REPORT_PATH_REF
    ]
    payload = {
        "schema_version": "uaa-taw08-evidence-delta-verification.v1",
        "candidate_revision_ref": candidate_lock.git_revision_ref,
        "candidate_manifest_digest_ref": candidate_lock.manifest_digest_ref,
        "delta_revision_ref": delta.delta_revision_ref,
        "delta_manifest_digest_ref": delta.manifest_digest_ref,
        "revision_delta_path_census_digest_ref": (
            revision_delta_census.census_digest_ref
        ),
        "history_path_refs": revision_delta_census.history_path_refs,
        "commit_count": revision_delta_census.commit_count,
        "candidate_ancestor_verified": True,
        "published_acceptance_report_fingerprint_ref": (
            published_report.report_fingerprint_ref
        ),
        "artifact_count": len(delta.entries),
        "verifier_ref": "verifier-ref:taw08:evidence-only-delta:v1",
        "verified": True,
    }
    return _EvidenceOnlyDeltaVerificationReceipt.model_validate(
        {**payload, "receipt_digest_ref": canonical_digest(payload)}
    )


def evaluate_taw08_acceptance(
    *,
    candidate_lock: CandidateLock,
    candidate_verification_receipt: _CandidateLockVerificationReceipt | None = None,
    founder_evidence: FounderPrivateAcceptanceEvidence | None = None,
    evidence_only_delta: EvidenceOnlyDeltaManifest | None = None,
    evidence_only_delta_verification_receipt: (
        _EvidenceOnlyDeltaVerificationReceipt | None
    ) = None,
    postmerge_foundation_receipt: FoundationGateReceipt | None = None,
    final_acceptance_publication_receipt: (
        _FinalAcceptancePublicationReceipt | None
    ) = None,
    failure_refs: tuple[str, ...] = (),
) -> TAW08AcceptanceReport:
    _validate_sorted_refs(failure_refs, "failure_refs")
    missing = set(TAW08_FOUNDER_EVIDENCE_MISSING_REFS)
    derived_failures = set(failure_refs)
    if candidate_verification_receipt is not None:
        missing.discard(
            "evidence-missing-ref:taw08:candidate-lock-verification-receipt"
        )
        if (
            candidate_verification_receipt.candidate_revision_ref
            != candidate_lock.git_revision_ref
            or candidate_verification_receipt.candidate_manifest_digest_ref
            != candidate_lock.manifest_digest_ref
        ):
            derived_failures.add(
                "failure-ref:taw08:candidate-verification-binding-drift"
            )
        repository_verifier_digest_ref = next(
            (
                item.content_digest_ref
                for item in candidate_lock.entries
                if item.path_ref == TAW08_REPOSITORY_VERIFIER_PATH_REF
            ),
            None,
        )
        if candidate_verification_receipt.repository_verifier_digest_ref != (
            repository_verifier_digest_ref
        ):
            derived_failures.add("failure-ref:taw08:repository-verifier-binding-drift")
    if founder_evidence is not None:
        missing.difference_update(
            set(TAW08_FOUNDER_EVIDENCE_MISSING_REFS)
            - {"evidence-missing-ref:taw08:candidate-lock-verification-receipt"}
        )
        if (
            founder_evidence.candidate_revision_ref != candidate_lock.git_revision_ref
            or founder_evidence.candidate_manifest_digest_ref
            != candidate_lock.manifest_digest_ref
        ):
            derived_failures.add(
                "failure-ref:taw08:founder-evidence-candidate-binding-drift"
            )
        founder_profile_entries = {
            item.path_ref: item.content_digest_ref
            for item in candidate_lock.entries
            if item.path_ref == TAW08_FOUNDER_PROFILE_PATH_REF
        }
        if founder_profile_entries.get(TAW08_FOUNDER_PROFILE_PATH_REF) != (
            founder_evidence.founder_dogfood_profile_digest_ref
        ):
            derived_failures.add("failure-ref:taw08:founder-profile-binding-drift")
    if evidence_only_delta is not None and (
        evidence_only_delta.candidate_revision_ref != candidate_lock.git_revision_ref
        or evidence_only_delta.candidate_manifest_digest_ref
        != candidate_lock.manifest_digest_ref
    ):
        derived_failures.add("failure-ref:taw08:evidence-delta-candidate-binding-drift")
    if evidence_only_delta_verification_receipt is None:
        missing.add(TAW08_DELTA_VERIFICATION_MISSING_REF)
    else:
        missing.discard(TAW08_DELTA_VERIFICATION_MISSING_REF)
        if (
            evidence_only_delta_verification_receipt.published_acceptance_report_fingerprint_ref
            != _pre_delta_acceptance_report_fingerprint_ref(
                candidate_revision_ref=candidate_lock.git_revision_ref,
                candidate_manifest_digest_ref=candidate_lock.manifest_digest_ref,
                candidate_verification_receipt=candidate_verification_receipt,
                founder_evidence=founder_evidence,
            )
        ):
            derived_failures.add(
                "failure-ref:taw08:published-acceptance-report-binding-drift"
            )
        if evidence_only_delta is None:
            derived_failures.add(
                "failure-ref:taw08:delta-verification-without-manifest"
            )
        elif (
            evidence_only_delta_verification_receipt.candidate_revision_ref
            != candidate_lock.git_revision_ref
            or evidence_only_delta_verification_receipt.candidate_manifest_digest_ref
            != candidate_lock.manifest_digest_ref
            or evidence_only_delta_verification_receipt.delta_revision_ref
            != evidence_only_delta.delta_revision_ref
            or evidence_only_delta_verification_receipt.delta_manifest_digest_ref
            != evidence_only_delta.manifest_digest_ref
            or evidence_only_delta_verification_receipt.revision_delta_path_census_digest_ref
            != bind_revision_delta_census(
                candidate_revision_ref=candidate_lock.git_revision_ref,
                delta_revision_ref=evidence_only_delta.delta_revision_ref,
                path_refs=tuple(item.path_ref for item in evidence_only_delta.entries),
                history_path_refs=(
                    evidence_only_delta_verification_receipt.history_path_refs
                ),
                commit_count=evidence_only_delta_verification_receipt.commit_count,
                candidate_ancestor_verified=True,
                provenance_ref="provenance-ref:git-history-path-census",
            ).census_digest_ref
            or set(evidence_only_delta_verification_receipt.history_path_refs)
            - set(candidate_lock.evidence_only_delta_path_refs)
            or evidence_only_delta_verification_receipt.artifact_count
            != len(evidence_only_delta.entries)
        ):
            derived_failures.add("failure-ref:taw08:delta-verification-binding-drift")
    if postmerge_foundation_receipt is None:
        missing.add(TAW08_POSTMERGE_EVIDENCE_MISSING_REF)
    else:
        missing.discard(TAW08_POSTMERGE_EVIDENCE_MISSING_REF)
        if postmerge_foundation_receipt.stage != "postmerge":
            derived_failures.add("failure-ref:taw08:postmerge-foundation-stage-drift")
        if evidence_only_delta is None:
            derived_failures.add("failure-ref:taw08:postmerge-delta-missing")
        elif (
            postmerge_foundation_receipt.revision_ref
            != evidence_only_delta.delta_revision_ref
        ):
            derived_failures.add("failure-ref:taw08:postmerge-delta-revision-drift")
        if evidence_only_delta_verification_receipt is None:
            derived_failures.add(
                "failure-ref:taw08:postmerge-delta-verification-missing"
            )
    if final_acceptance_publication_receipt is None:
        missing.add(TAW08_FINAL_PUBLICATION_MISSING_REF)
    else:
        missing.discard(TAW08_FINAL_PUBLICATION_MISSING_REF)
        if (
            evidence_only_delta is None
            or evidence_only_delta_verification_receipt is None
            or postmerge_foundation_receipt is None
        ):
            derived_failures.add(
                "failure-ref:taw08:final-publication-prerequisite-missing"
            )
        elif (
            final_acceptance_publication_receipt.candidate_revision_ref
            != candidate_lock.git_revision_ref
            or final_acceptance_publication_receipt.candidate_manifest_digest_ref
            != candidate_lock.manifest_digest_ref
            or final_acceptance_publication_receipt.delta_revision_ref
            != evidence_only_delta.delta_revision_ref
            or final_acceptance_publication_receipt.delta_manifest_digest_ref
            != evidence_only_delta.manifest_digest_ref
            or final_acceptance_publication_receipt.delta_verification_receipt_digest_ref
            != evidence_only_delta_verification_receipt.receipt_digest_ref
            or final_acceptance_publication_receipt.postmerge_foundation_receipt_digest_ref
            != postmerge_foundation_receipt.receipt_digest_ref
            or final_acceptance_publication_receipt.published_report_semantic_digest_ref
            != _final_acceptance_semantic_digest(
                candidate_revision_ref=candidate_lock.git_revision_ref,
                candidate_manifest_digest_ref=candidate_lock.manifest_digest_ref,
                founder_evidence_digest_ref=(
                    founder_evidence.evidence_digest_ref if founder_evidence else None
                ),
                delta=evidence_only_delta,
                delta_verification_receipt=(evidence_only_delta_verification_receipt),
                postmerge_foundation_receipt=postmerge_foundation_receipt,
            )
        ):
            derived_failures.add("failure-ref:taw08:final-publication-binding-drift")
    founder_accepted = (
        founder_evidence is not None and candidate_verification_receipt is not None
    )
    if derived_failures:
        status = TAW08AcceptanceStatus.failed
        founder_accepted = False
    elif not founder_accepted:
        status = TAW08AcceptanceStatus.blocked_missing_founder_evidence
    elif (
        postmerge_foundation_receipt is None
        or evidence_only_delta is None
        or evidence_only_delta_verification_receipt is None
    ):
        status = TAW08AcceptanceStatus.founder_private_accepted_postmerge_pending
    elif final_acceptance_publication_receipt is None:
        status = (
            TAW08AcceptanceStatus.founder_private_accepted_final_publication_pending
        )
    else:
        status = TAW08AcceptanceStatus.founder_private_accepted_promotion_blocked
    payload = {
        "schema_version": "uaa-taw08-acceptance-report.v1",
        "contract_ref": TAW08_CONTRACT_REF,
        "evaluator_ref": TAW08_EVALUATOR_REF,
        "status": status.value,
        "candidate_revision_ref": candidate_lock.git_revision_ref,
        "candidate_manifest_digest_ref": candidate_lock.manifest_digest_ref,
        "candidate_verification_receipt": (
            candidate_verification_receipt.model_dump(mode="json")
            if candidate_verification_receipt
            else None
        ),
        "candidate_verification_receipt_digest_ref": (
            candidate_verification_receipt.receipt_digest_ref
            if candidate_verification_receipt
            else None
        ),
        "founder_evidence": (
            founder_evidence.model_dump(mode="json") if founder_evidence else None
        ),
        "founder_evidence_digest_ref": (
            founder_evidence.evidence_digest_ref if founder_evidence else None
        ),
        "evidence_only_delta": (
            evidence_only_delta.model_dump(mode="json") if evidence_only_delta else None
        ),
        "evidence_only_delta_manifest_digest_ref": (
            evidence_only_delta.manifest_digest_ref if evidence_only_delta else None
        ),
        "evidence_only_delta_verification_receipt": (
            evidence_only_delta_verification_receipt.model_dump(mode="json")
            if evidence_only_delta_verification_receipt
            else None
        ),
        "evidence_only_delta_verification_receipt_digest_ref": (
            evidence_only_delta_verification_receipt.receipt_digest_ref
            if evidence_only_delta_verification_receipt
            else None
        ),
        "postmerge_foundation_receipt": (
            postmerge_foundation_receipt.model_dump(mode="json")
            if postmerge_foundation_receipt
            else None
        ),
        "postmerge_foundation_receipt_digest_ref": (
            postmerge_foundation_receipt.receipt_digest_ref
            if postmerge_foundation_receipt
            else None
        ),
        "final_acceptance_publication_receipt": (
            final_acceptance_publication_receipt.model_dump(mode="json")
            if final_acceptance_publication_receipt
            else None
        ),
        "final_acceptance_publication_receipt_digest_ref": (
            final_acceptance_publication_receipt.receipt_digest_ref
            if final_acceptance_publication_receipt
            else None
        ),
        "founder_private_accepted": founder_accepted,
        "founder_evidence_missing_refs": tuple(sorted(missing)),
        "failure_refs": tuple(sorted(derived_failures)),
        "independent_promotion_blocker_refs": (
            TAW08_INDEPENDENT_PROMOTION_BLOCKER_REFS
        ),
        "independent_promotion_ready": False,
        "sealed_holdout_evidence_verified": False,
        "public_quality_claims_allowed": False,
        "production_authority_added": False,
        "runtime_model_calls_added": False,
        "provider_calls_added": False,
        "execution_authority_added": False,
        "raw_content_persisted": False,
    }
    return TAW08AcceptanceReport.model_validate(
        {
            **payload,
            "report_fingerprint_ref": (
                f"taw08-acceptance-report-ref:{canonical_digest(payload)}"
            ),
        }
    )
