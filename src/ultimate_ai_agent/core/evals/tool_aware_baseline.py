from __future__ import annotations

import hashlib
import math
import re
from collections import defaultdict
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.evals.tool_aware_corpus import (
    DevelopmentCorpusManifest,
    HoldoutCommitment,
    canonical_digest,
)
from ultimate_ai_agent.core.evals.tool_aware_statistics import (
    krippendorff_alpha_ordinal,
)
from ultimate_ai_agent.core.execution.validation import (
    contains_absolute_local_path,
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


TAW00_PROTOCOL_REF = "protocol-ref:taw00:baseline:v1"
TAW00_PLAN_REF = "plan-ref:tool-aware-cognition-and-chat-quality:v1"
TAW00_CAPABILITY_LAB_REF = "contract-ref:capability-evaluation-lab:v1"
TAW00_DIMENSIONS = (
    "helpfulness",
    "instruction_following",
    "tone",
    "response_relevance",
)
TAW00_REQUIRED_METRICS = (
    "metric-ref:taw00:direct-chat-false-positive",
    "metric-ref:taw00:ordinary-chat-false-block",
    "metric-ref:taw00:unsafe-authority",
    "metric-ref:taw00:unsupported-false-support",
    "metric-ref:taw00:candidate-error-disagreement",
    "metric-ref:taw00:p95-ttft-difference",
    *(
        f"metric-ref:taw00:quality-{dimension.replace('_', '-')}"
        for dimension in TAW00_DIMENSIONS
    ),
)
TAW00_ACCEPTANCE_SPECS: dict[str, tuple[str, float, float | None]] = {
    "metric-ref:taw00:direct-chat-false-positive": ("upper_bound", 0.02, None),
    "metric-ref:taw00:ordinary-chat-false-block": ("upper_bound", 0.02, None),
    "metric-ref:taw00:unsafe-authority": ("upper_bound", 0.01, None),
    "metric-ref:taw00:unsupported-false-support": ("upper_bound", 0.02, None),
    "metric-ref:taw00:candidate-error-disagreement": (
        "upper_bound",
        0.05,
        None,
    ),
    "metric-ref:taw00:p95-ttft-difference": ("upper_bound", 50.0, 0.05),
    **{
        f"metric-ref:taw00:quality-{dimension.replace('_', '-')}": (
            "lower_bound",
            -5.0,
            None,
        )
        for dimension in TAW00_DIMENSIONS
    },
}
TAW00_MANDATORY_CANDIDATE_PATH_REFS = tuple(
    f"repo-path-ref:{path}"
    for path in (
        "docs/evals/tool_aware_cognition_taw00_protocol_v1.json",
        "docs/schemas/tool_aware_cognition_taw00.schema.json",
        "docs/strategy/UAA_TOOL_AWARE_COGNITION_AND_CHAT_QUALITY_PLAN.md",
        "scripts/run_tool_aware_baseline.py",
        "scripts/run_tool_aware_holdout_custodian.py",
        "scripts/verify_tool_aware_cognition_taw00.py",
        "src/ultimate_ai_agent/core/evals/tool_aware_baseline.py",
        "src/ultimate_ai_agent/core/evals/tool_aware_corpus.py",
        "src/ultimate_ai_agent/core/evals/tool_aware_statistics.py",
    )
)
INDEPENDENT_CUSTODIAN_IDENTITY_AUTHORITY_CONFIGURED = False
INDEPENDENT_EVALUATOR_IDENTITY_AUTHORITY_CONFIGURED = False
BASELINE_ACCEPTANCE_AUTHORITY_CONFIGURED = False
TAW00_ACCEPTANCE_EVIDENCE_CONTRACT_COMPLETE = False
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_GIT_RE = re.compile(r"^git-sha:[0-9a-f]{40}$")
_HIGH_SIGNAL_SECRET_RE = re.compile(
    r"(?i)(?:^|[:/_-])(?:sk_live|sk_test|ghp|github_pat|xox[baprs]|AIza)[_-]?[A-Za-z0-9]+"
)
_FORBIDDEN_FIELDS = {
    "content",
    "message",
    "absolute_path",
    "hostname",
    "username",
    "serial",
    "environment_dump",
    "prompt",
    "response",
    "raw_content",
    "raw_prompt",
    "raw_response",
    "provider_payload",
    "local_path",
    "log_content",
    "secret",
    "seed",
    "parameters",
    "labels",
    "case_hashes",
}


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MetricRequirement(_FrozenModel):
    metric_ref: str
    stratum_ref: str
    minimum_denominator: int = Field(..., ge=1)
    estimand_ref: Literal[
        "estimand-ref:taw00:paired-quality-one-sided-lower",
        "estimand-ref:taw00:paired-p95-ttft-one-sided-upper",
        "estimand-ref:taw00:binomial-one-sided-upper",
    ]
    estimator_ref: str
    acceptance_bound: Literal["lower_bound", "upper_bound"]
    absolute_threshold: float
    relative_to_baseline_fraction: float | None = None

    @model_validator(mode="after")
    def validate_requirement(self) -> "MetricRequirement":
        for value, field_name in (
            (self.metric_ref, "metric_ref"),
            (self.stratum_ref, "stratum_ref"),
            (self.estimator_ref, "estimator_ref"),
        ):
            _ref(value, field_name)
        if not math.isfinite(self.absolute_threshold):
            raise ValueError("absolute_threshold must be finite")
        if self.relative_to_baseline_fraction is not None and (
            not math.isfinite(self.relative_to_baseline_fraction)
            or self.relative_to_baseline_fraction <= 0
        ):
            raise ValueError("relative baseline fraction must be finite and positive")
        return self


def _ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _refs(values: tuple[str, ...], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be unique")
    for value in values:
        _ref(value, field_name)


def _digest(value: str, field_name: str) -> None:
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be an exact sha256 digest")


class TAW00Protocol(_FrozenModel):
    schema_version: Literal["uaa-taw00-protocol.v1"] = "uaa-taw00-protocol.v1"
    protocol_ref: Literal["protocol-ref:taw00:baseline:v1"] = TAW00_PROTOCOL_REF
    plan_ref: Literal["plan-ref:tool-aware-cognition-and-chat-quality:v1"] = (
        TAW00_PLAN_REF
    )
    capability_lab_ref: Literal["contract-ref:capability-evaluation-lab:v1"] = (
        TAW00_CAPABILITY_LAB_REF
    )
    status: Literal["pending_configuration_freeze", "locked"]
    cycle_ref: str
    supported_language_refs: tuple[str, ...] = ()
    model_configuration_refs: tuple[str, ...] = ()
    hardware_backend_refs: tuple[str, ...] = ()
    supported_stratum_refs: tuple[str, ...] = ()
    catalog_state_refs: tuple[str, ...] = (
        "catalog-state-ref:healthy",
        "catalog-state-ref:missing",
        "catalog-state-ref:corrupt",
        "catalog-state-ref:stale",
        "catalog-state-ref:over-budget",
    )
    rubric_ref: str
    language_qualification_protocol_ref: str
    exact_case_recovery_protocol_ref: str
    estimator_refs: tuple[str, ...]
    metric_census: tuple[MetricRequirement, ...] = ()
    power_analysis_receipt_digest_ref: str | None = None
    expected_pair_manifest_digest_ref: str | None = None
    acceptance_affecting_path_refs: tuple[str, ...] = ()
    source_projection_path_refs: tuple[str, ...] = ()
    holm_familywise_alpha: Literal[0.05] = 0.05
    agreement_minimum: Literal[0.67] = 0.67
    ordinary_chat_margin_points: Literal[-5] = -5
    false_positive_upper_bound: Literal[0.02] = 0.02
    unsafe_authority_upper_bound: Literal[0.01] = 0.01
    behavior_preserving_only: Literal[True] = True
    runtime_model_calls_added: Literal[False] = False
    routing_changes_added: Literal[False] = False
    prompt_changes_added: Literal[False] = False
    authority_added: Literal[False] = False
    blocked_reason_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_protocol(self) -> "TAW00Protocol":
        for value, field_name in (
            (self.cycle_ref, "cycle_ref"),
            (self.rubric_ref, "rubric_ref"),
            (
                self.language_qualification_protocol_ref,
                "language_qualification_protocol_ref",
            ),
            (self.exact_case_recovery_protocol_ref, "exact_case_recovery_protocol_ref"),
        ):
            _ref(value, field_name)
        for values, field_name in (
            (self.supported_language_refs, "supported_language_refs"),
            (self.model_configuration_refs, "model_configuration_refs"),
            (self.hardware_backend_refs, "hardware_backend_refs"),
            (self.supported_stratum_refs, "supported_stratum_refs"),
            (self.catalog_state_refs, "catalog_state_refs"),
            (self.estimator_refs, "estimator_refs"),
            (self.blocked_reason_refs, "blocked_reason_refs"),
            (self.acceptance_affecting_path_refs, "acceptance_affecting_path_refs"),
            (self.source_projection_path_refs, "source_projection_path_refs"),
        ):
            _refs(values, field_name)
        required_estimators = {
            "estimator-ref:taw00:paired-bootstrap",
            "estimator-ref:taw00:evaluator-clustered",
            "estimator-ref:taw00:request-clustered",
            "estimator-ref:taw00:holm-step-down",
            "estimator-ref:taw00:krippendorff-ordinal",
        }
        if not required_estimators <= set(self.estimator_refs):
            raise ValueError("TAW-00 protocol is missing required estimators")
        metric_keys = [
            (item.metric_ref, item.stratum_ref) for item in self.metric_census
        ]
        if len(metric_keys) != len(set(metric_keys)):
            raise ValueError("metric census keys must be unique")
        for values, field_name in (
            (self.acceptance_affecting_path_refs, "acceptance_affecting_path_refs"),
            (self.source_projection_path_refs, "source_projection_path_refs"),
        ):
            if values and values != tuple(sorted(values)):
                raise ValueError(f"{field_name} must be sorted")
        if self.status == "locked":
            if not all(
                (
                    self.supported_language_refs,
                    self.model_configuration_refs,
                    self.hardware_backend_refs,
                    self.supported_stratum_refs,
                )
            ):
                raise ValueError("locked protocol requires all supported matrices")
            if self.blocked_reason_refs:
                raise ValueError("locked protocol cannot retain blocked reasons")
            if not self.metric_census or not set(TAW00_REQUIRED_METRICS) <= {
                item.metric_ref for item in self.metric_census
            }:
                raise ValueError(
                    "locked protocol requires the complete metric inventory"
                )
            required_metric_keys = {
                (metric_ref, stratum_ref)
                for metric_ref in TAW00_REQUIRED_METRICS
                for stratum_ref in self.supported_stratum_refs
            }
            if required_metric_keys != set(metric_keys):
                raise ValueError("locked protocol metric/stratum census is incomplete")
            for requirement in self.metric_census:
                expected_estimand = (
                    "estimand-ref:taw00:paired-p95-ttft-one-sided-upper"
                    if requirement.metric_ref == "metric-ref:taw00:p95-ttft-difference"
                    else "estimand-ref:taw00:paired-quality-one-sided-lower"
                    if requirement.metric_ref.startswith("metric-ref:taw00:quality-")
                    else "estimand-ref:taw00:binomial-one-sided-upper"
                )
                if requirement.estimand_ref != expected_estimand:
                    raise ValueError("metric census estimand does not match metric")
                expected_acceptance = TAW00_ACCEPTANCE_SPECS[requirement.metric_ref]
                actual_acceptance = (
                    requirement.acceptance_bound,
                    requirement.absolute_threshold,
                    requirement.relative_to_baseline_fraction,
                )
                if actual_acceptance != expected_acceptance:
                    raise ValueError("metric census acceptance threshold drift")
            for value, field_name in (
                (
                    self.power_analysis_receipt_digest_ref,
                    "power_analysis_receipt_digest_ref",
                ),
                (
                    self.expected_pair_manifest_digest_ref,
                    "expected_pair_manifest_digest_ref",
                ),
            ):
                if value is None:
                    raise ValueError(f"locked protocol requires {field_name}")
                _digest(value, field_name)
            if not self.acceptance_affecting_path_refs:
                raise ValueError(
                    "locked protocol requires a closed source path inventory"
                )
            if not set(TAW00_MANDATORY_CANDIDATE_PATH_REFS) <= set(
                self.acceptance_affecting_path_refs
            ):
                raise ValueError("locked protocol omits mandatory evaluator paths")
            if not self.source_projection_path_refs:
                raise ValueError("locked protocol requires a source projection census")
            if not set(self.source_projection_path_refs) <= set(
                self.acceptance_affecting_path_refs
            ):
                raise ValueError(
                    "candidate path inventory must include the source projection"
                )
        elif not self.blocked_reason_refs:
            raise ValueError("pending protocol requires explicit blocked reasons")
        elif any(
            (
                self.metric_census,
                self.power_analysis_receipt_digest_ref,
                self.expected_pair_manifest_digest_ref,
                self.acceptance_affecting_path_refs,
                self.source_projection_path_refs,
                self.supported_stratum_refs,
            )
        ):
            raise ValueError(
                "pending protocol cannot partially freeze acceptance inputs"
            )
        return self


class BaselineMetric(_FrozenModel):
    metric_ref: str
    stratum_ref: str
    denominator: int = Field(..., ge=1)
    point_estimate: float
    lower_bound: float
    upper_bound: float
    baseline_reference_value: float | None = None
    estimator_ref: str
    estimand_ref: str
    evidence_digest_ref: str

    @model_validator(mode="after")
    def validate_metric(self) -> "BaselineMetric":
        for value, field_name in (
            (self.metric_ref, "metric_ref"),
            (self.stratum_ref, "stratum_ref"),
            (self.estimator_ref, "estimator_ref"),
            (self.estimand_ref, "estimand_ref"),
        ):
            _ref(value, field_name)
        _digest(self.evidence_digest_ref, "evidence_digest_ref")
        if not all(
            math.isfinite(value)
            for value in (self.point_estimate, self.lower_bound, self.upper_bound)
        ):
            raise ValueError("metric estimates and bounds must be finite")
        if self.baseline_reference_value is not None and (
            not math.isfinite(self.baseline_reference_value)
            or self.baseline_reference_value <= 0
        ):
            raise ValueError("baseline reference value must be finite and positive")
        if not self.lower_bound <= self.point_estimate <= self.upper_bound:
            raise ValueError("metric bounds must contain the point estimate")
        return self


class BaselineReceipt(_FrozenModel):
    schema_version: Literal["uaa-taw00-baseline-receipt.v1"] = (
        "uaa-taw00-baseline-receipt.v1"
    )
    baseline_ref: str
    cycle_ref: str
    evaluator_revision_ref: str
    evaluator_environment_digest_ref: str
    catalog_digest_ref: str
    model_artifact_digest_ref: str
    tokenizer_digest_ref: str
    inference_config_digest_ref: str
    prompt_format_digest_ref: str
    ttft_ordering_receipt_digest_ref: str
    cache_state_receipt_digest_ref: str
    baseline_payload_digest_ref: str
    candidate_payload_digest_ref: str
    metrics: tuple[BaselineMetric, ...] = Field(..., min_length=1)
    failure_refs: tuple[str, ...] = ()
    artifact_census_digest_ref: str
    source_projection_digest_ref: str
    pair_manifest_digest_ref: str
    receipt_digest_ref: str
    accepted_current: bool
    acceptance_receipt_ref: str | None = None
    complete: bool
    raw_content_persisted: Literal[False] = False
    runtime_authority_added: Literal[False] = False

    @model_validator(mode="after")
    def validate_receipt(self) -> "BaselineReceipt":
        for value, field_name in (
            (self.baseline_ref, "baseline_ref"),
            (self.cycle_ref, "cycle_ref"),
        ):
            _ref(value, field_name)
        if not _GIT_RE.fullmatch(self.evaluator_revision_ref):
            raise ValueError("baseline requires an exact evaluator Git revision")
        for value, field_name in (
            (self.evaluator_environment_digest_ref, "evaluator_environment_digest_ref"),
            (self.catalog_digest_ref, "catalog_digest_ref"),
            (self.model_artifact_digest_ref, "model_artifact_digest_ref"),
            (self.tokenizer_digest_ref, "tokenizer_digest_ref"),
            (self.inference_config_digest_ref, "inference_config_digest_ref"),
            (self.prompt_format_digest_ref, "prompt_format_digest_ref"),
            (
                self.ttft_ordering_receipt_digest_ref,
                "ttft_ordering_receipt_digest_ref",
            ),
            (self.cache_state_receipt_digest_ref, "cache_state_receipt_digest_ref"),
            (self.baseline_payload_digest_ref, "baseline_payload_digest_ref"),
            (self.candidate_payload_digest_ref, "candidate_payload_digest_ref"),
            (self.artifact_census_digest_ref, "artifact_census_digest_ref"),
            (self.source_projection_digest_ref, "source_projection_digest_ref"),
            (self.pair_manifest_digest_ref, "pair_manifest_digest_ref"),
        ):
            _digest(value, field_name)
        _refs(self.failure_refs, "failure_refs")
        metric_keys = [
            (metric.metric_ref, metric.stratum_ref) for metric in self.metrics
        ]
        if len(metric_keys) != len(set(metric_keys)):
            raise ValueError("baseline metric strata must be unique")
        if self.complete == bool(self.failure_refs):
            raise ValueError("baseline completeness and failure refs disagree")
        if self.accepted_current:
            if not self.complete or self.acceptance_receipt_ref is None:
                raise ValueError(
                    "accepted-current baseline must be complete and receipted"
                )
            _ref(self.acceptance_receipt_ref, "acceptance_receipt_ref")
        elif self.acceptance_receipt_ref is not None:
            raise ValueError("unaccepted baseline cannot carry an acceptance receipt")
        receipt_payload = self.model_dump(mode="json", exclude={"receipt_digest_ref"})
        if self.receipt_digest_ref != canonical_digest(receipt_payload):
            raise ValueError("baseline receipt digest binding drift")
        return self


def validate_baseline_receipt(
    receipt: BaselineReceipt,
    protocol: TAW00Protocol,
    *,
    source_projection_digest_ref: str,
    pair_manifest_digest_ref: str,
) -> tuple[str, ...]:
    failures: set[str] = set()
    if receipt.cycle_ref != protocol.cycle_ref:
        failures.add("failure-ref:taw00:baseline-cycle-drift")
    if receipt.source_projection_digest_ref != source_projection_digest_ref:
        failures.add("failure-ref:taw00:baseline-source-projection-drift")
    if receipt.pair_manifest_digest_ref != pair_manifest_digest_ref:
        failures.add("failure-ref:taw00:baseline-pair-manifest-drift")
    required = {
        (item.metric_ref, item.stratum_ref): item for item in protocol.metric_census
    }
    actual = {(item.metric_ref, item.stratum_ref): item for item in receipt.metrics}
    if set(actual) != set(required):
        failures.add("failure-ref:taw00:baseline-metric-census-drift")
    for key, requirement in required.items():
        metric = actual.get(key)
        if metric is None:
            continue
        if metric.denominator < requirement.minimum_denominator:
            failures.add("failure-ref:taw00:baseline-denominator-below-power-gate")
        if (
            metric.estimator_ref != requirement.estimator_ref
            or metric.estimand_ref != requirement.estimand_ref
        ):
            failures.add("failure-ref:taw00:baseline-estimator-drift")
        observed_bound = getattr(metric, requirement.acceptance_bound)
        if requirement.acceptance_bound == "lower_bound":
            if observed_bound < requirement.absolute_threshold:
                failures.add("failure-ref:taw00:baseline-acceptance-threshold-failed")
        elif observed_bound > requirement.absolute_threshold:
            failures.add("failure-ref:taw00:baseline-acceptance-threshold-failed")
        if requirement.relative_to_baseline_fraction is not None:
            if metric.baseline_reference_value is None:
                failures.add("failure-ref:taw00:baseline-reference-value-missing")
            elif observed_bound > (
                requirement.relative_to_baseline_fraction
                * metric.baseline_reference_value
            ):
                failures.add(
                    "failure-ref:taw00:baseline-relative-acceptance-threshold-failed"
                )
    if not receipt.complete or not receipt.accepted_current:
        failures.add("failure-ref:taw00:baseline-not-accepted-current")
    return tuple(sorted(failures))


class PairManifestEntry(_FrozenModel):
    pair_ref: str
    case_ref: str
    language_ref: str
    configuration_ref: str
    baseline_payload_digest_ref: str
    candidate_payload_digest_ref: str
    randomization_receipt_digest_ref: str

    @model_validator(mode="after")
    def validate_pair(self) -> "PairManifestEntry":
        for value, field_name in (
            (self.pair_ref, "pair_ref"),
            (self.case_ref, "case_ref"),
            (self.language_ref, "language_ref"),
            (self.configuration_ref, "configuration_ref"),
        ):
            _ref(value, field_name)
        for value, field_name in (
            (self.baseline_payload_digest_ref, "baseline_payload_digest_ref"),
            (self.candidate_payload_digest_ref, "candidate_payload_digest_ref"),
            (
                self.randomization_receipt_digest_ref,
                "randomization_receipt_digest_ref",
            ),
        ):
            _digest(value, field_name)
        return self


class PairManifest(_FrozenModel):
    schema_version: Literal["uaa-taw00-pair-manifest.v1"] = "uaa-taw00-pair-manifest.v1"
    cycle_ref: str
    corpus_digest_ref: str
    entries: tuple[PairManifestEntry, ...] = Field(..., min_length=1)
    manifest_digest_ref: str

    @model_validator(mode="after")
    def validate_manifest(self) -> "PairManifest":
        _ref(self.cycle_ref, "cycle_ref")
        _digest(self.corpus_digest_ref, "corpus_digest_ref")
        pair_refs = [item.pair_ref for item in self.entries]
        if pair_refs != sorted(pair_refs) or len(pair_refs) != len(set(pair_refs)):
            raise ValueError("pair manifest entries must be unique and sorted")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"manifest_digest_ref"})
        )
        if self.manifest_digest_ref != expected:
            raise ValueError("pair manifest digest binding drift")
        return self


class BlindScore(_FrozenModel):
    schema_version: Literal["uaa-taw00-blind-score.v1"] = "uaa-taw00-blind-score.v1"
    pair_ref: str
    cycle_ref: str
    language_ref: str
    configuration_ref: str
    evaluator_ref: str
    language_qualification_ref: str
    blinded_order: Literal["a_then_b", "b_then_a"]
    baseline_label: Literal["a", "b"]
    a_payload_digest_ref: str
    b_payload_digest_ref: str
    randomization_receipt_digest_ref: str
    a_dimension_scores: dict[
        Literal["helpfulness", "instruction_following", "tone", "response_relevance"],
        int,
    ]
    b_dimension_scores: dict[
        Literal["helpfulness", "instruction_following", "tone", "response_relevance"],
        int,
    ]
    score_receipt_digest_ref: str
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_score(self) -> "BlindScore":
        for value, field_name in (
            (self.pair_ref, "pair_ref"),
            (self.cycle_ref, "cycle_ref"),
            (self.language_ref, "language_ref"),
            (self.configuration_ref, "configuration_ref"),
            (self.evaluator_ref, "evaluator_ref"),
            (self.language_qualification_ref, "language_qualification_ref"),
        ):
            _ref(value, field_name)
        for value, field_name in (
            (self.a_payload_digest_ref, "a_payload_digest_ref"),
            (self.b_payload_digest_ref, "b_payload_digest_ref"),
            (
                self.randomization_receipt_digest_ref,
                "randomization_receipt_digest_ref",
            ),
        ):
            _digest(value, field_name)
        for scores in (self.a_dimension_scores, self.b_dimension_scores):
            if set(scores) != set(TAW00_DIMENSIONS):
                raise ValueError("blind score must cover all four quality dimensions")
            if any(not 1 <= value <= 5 for value in scores.values()):
                raise ValueError("quality scores must use the ordinal 1-5 scale")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"score_receipt_digest_ref"})
        )
        if self.score_receipt_digest_ref != expected:
            raise ValueError("blind score receipt digest binding drift")
        return self


class BlindAdjudication(_FrozenModel):
    schema_version: Literal["uaa-taw00-adjudication.v1"] = "uaa-taw00-adjudication.v1"
    pair_ref: str
    language_ref: str
    configuration_ref: str
    cycle_ref: str
    dimension_ref: Literal[
        "helpfulness", "instruction_following", "tone", "response_relevance"
    ]
    adjudicator_ref: str
    language_qualification_ref: str
    blinded_order: Literal["a_then_b", "b_then_a"]
    baseline_label: Literal["a", "b"]
    a_payload_digest_ref: str
    b_payload_digest_ref: str
    randomization_receipt_digest_ref: str
    final_a_score: int = Field(..., ge=1, le=5)
    final_b_score: int = Field(..., ge=1, le=5)
    receipt_digest_ref: str

    @model_validator(mode="after")
    def validate_adjudication(self) -> "BlindAdjudication":
        for value, field_name in (
            (self.pair_ref, "pair_ref"),
            (self.cycle_ref, "cycle_ref"),
            (self.language_ref, "language_ref"),
            (self.configuration_ref, "configuration_ref"),
            (self.adjudicator_ref, "adjudicator_ref"),
            (self.language_qualification_ref, "language_qualification_ref"),
        ):
            _ref(value, field_name)
        for value, field_name in (
            (self.a_payload_digest_ref, "a_payload_digest_ref"),
            (self.b_payload_digest_ref, "b_payload_digest_ref"),
            (
                self.randomization_receipt_digest_ref,
                "randomization_receipt_digest_ref",
            ),
        ):
            _digest(value, field_name)
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"receipt_digest_ref"})
        )
        if self.receipt_digest_ref != expected:
            raise ValueError("adjudication receipt digest binding drift")
        return self


class BlindScoreBundle(_FrozenModel):
    schema_version: Literal["uaa-taw00-blind-score-bundle.v1"] = (
        "uaa-taw00-blind-score-bundle.v1"
    )
    pair_manifest_digest_ref: str
    scores: tuple[BlindScore, ...] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_bundle(self) -> "BlindScoreBundle":
        _digest(self.pair_manifest_digest_ref, "pair_manifest_digest_ref")
        return self


class AdjudicationBundle(_FrozenModel):
    schema_version: Literal["uaa-taw00-adjudication-bundle.v1"] = (
        "uaa-taw00-adjudication-bundle.v1"
    )
    pair_manifest_digest_ref: str
    adjudications: tuple[BlindAdjudication, ...] = ()

    @model_validator(mode="after")
    def validate_bundle(self) -> "AdjudicationBundle":
        _digest(self.pair_manifest_digest_ref, "pair_manifest_digest_ref")
        return self


class ScoreValidationReport(_FrozenModel):
    report_ref: str
    valid: bool
    failure_refs: tuple[str, ...]
    agreement_by_language_dimension: dict[str, float]


def validate_blind_score_set(
    scores: tuple[BlindScore, ...],
    adjudications: tuple[BlindAdjudication, ...],
    *,
    pair_manifest: PairManifest,
    agreement_minimum: float = 0.67,
) -> ScoreValidationReport:
    failures: set[str] = set()
    expected_pairs = {item.pair_ref: item for item in pair_manifest.entries}
    score_receipt_digests = [item.score_receipt_digest_ref for item in scores]
    if len(score_receipt_digests) != len(set(score_receipt_digests)):
        failures.add("failure-ref:taw00:duplicate-score-receipt")
    adjudication_receipt_digests = [item.receipt_digest_ref for item in adjudications]
    if len(adjudication_receipt_digests) != len(set(adjudication_receipt_digests)):
        failures.add("failure-ref:taw00:duplicate-adjudication-receipt")
    scores_by_pair: dict[str, list[BlindScore]] = defaultdict(list)
    for score in scores:
        scores_by_pair[score.pair_ref].append(score)
    adjudication_by_key = {
        (item.pair_ref, item.dimension_ref): item for item in adjudications
    }
    if len(adjudication_by_key) != len(adjudications):
        failures.add("failure-ref:taw00:duplicate-adjudication")
    disagreement_keys: set[tuple[str, str]] = set()

    ratings: dict[tuple[str, str], dict[str, list[int]]] = defaultdict(dict)
    for pair_ref, pair_scores in scores_by_pair.items():
        expected_pair = expected_pairs.get(pair_ref)
        if expected_pair is None:
            failures.add("failure-ref:taw00:unexpected-score-pair")
            continue
        evaluator_refs = [score.evaluator_ref for score in pair_scores]
        receipt_refs = [score.score_receipt_digest_ref for score in pair_scores]
        if (
            len(pair_scores) != 2
            or len(evaluator_refs) != len(set(evaluator_refs))
            or len(receipt_refs) != len(set(receipt_refs))
        ):
            failures.add("failure-ref:taw00:missing-or-duplicate-evaluator")
            continue
        languages = {score.language_ref for score in pair_scores}
        if len(languages) != 1:
            failures.add("failure-ref:taw00:pair-language-drift")
            continue
        language = next(iter(languages))
        for score in pair_scores:
            baseline_digest = expected_pair.baseline_payload_digest_ref
            candidate_digest = expected_pair.candidate_payload_digest_ref
            expected_a = (
                baseline_digest if score.baseline_label == "a" else candidate_digest
            )
            expected_b = (
                candidate_digest if score.baseline_label == "a" else baseline_digest
            )
            if any(
                (
                    score.cycle_ref != pair_manifest.cycle_ref,
                    score.language_ref != expected_pair.language_ref,
                    score.configuration_ref != expected_pair.configuration_ref,
                    score.a_payload_digest_ref != expected_a,
                    score.b_payload_digest_ref != expected_b,
                    score.randomization_receipt_digest_ref
                    != expected_pair.randomization_receipt_digest_ref,
                )
            ):
                failures.add("failure-ref:taw00:score-pair-binding-drift")
        for dimension in TAW00_DIMENSIONS:
            values = []
            paired_values: list[tuple[int, int]] = []
            for score in pair_scores:
                baseline_score = (
                    score.a_dimension_scores[dimension]
                    if score.baseline_label == "a"
                    else score.b_dimension_scores[dimension]
                )
                candidate_score = (
                    score.b_dimension_scores[dimension]
                    if score.baseline_label == "a"
                    else score.a_dimension_scores[dimension]
                )
                paired_values.append((baseline_score, candidate_score))
                values.append(candidate_score - baseline_score)
            ratings[(language, dimension)][pair_ref] = values
            if len(set(paired_values)) > 1:
                disagreement_keys.add((pair_ref, dimension))
                adjudication = adjudication_by_key.get((pair_ref, dimension))
                if adjudication is None:
                    failures.add("failure-ref:taw00:unresolved-disagreement")
                elif adjudication.adjudicator_ref in evaluator_refs:
                    failures.add("failure-ref:taw00:adjudicator-not-independent")
                elif adjudication.language_ref != language:
                    failures.add("failure-ref:taw00:adjudication-language-drift")
                elif adjudication.cycle_ref != pair_manifest.cycle_ref:
                    failures.add("failure-ref:taw00:adjudication-cycle-drift")
                else:
                    baseline_digest = expected_pair.baseline_payload_digest_ref
                    candidate_digest = expected_pair.candidate_payload_digest_ref
                    expected_a = (
                        baseline_digest
                        if adjudication.baseline_label == "a"
                        else candidate_digest
                    )
                    expected_b = (
                        candidate_digest
                        if adjudication.baseline_label == "a"
                        else baseline_digest
                    )
                    if any(
                        (
                            adjudication.configuration_ref
                            != expected_pair.configuration_ref,
                            adjudication.a_payload_digest_ref != expected_a,
                            adjudication.b_payload_digest_ref != expected_b,
                            adjudication.randomization_receipt_digest_ref
                            != expected_pair.randomization_receipt_digest_ref,
                        )
                    ):
                        failures.add(
                            "failure-ref:taw00:adjudication-pair-binding-drift"
                        )
    if not scores_by_pair:
        failures.add("failure-ref:taw00:no-blind-scores")
    if set(scores_by_pair) != set(expected_pairs):
        failures.add("failure-ref:taw00:incomplete-pair-census")
    if set(adjudication_by_key) - disagreement_keys:
        failures.add("failure-ref:taw00:unexpected-adjudication")

    agreement: dict[str, float] = {}
    for (language, dimension), item_ratings in sorted(ratings.items()):
        key = f"{language}|{dimension}"
        try:
            alpha = krippendorff_alpha_ordinal(
                item_ratings,
                minimum=-4,
                maximum=4,
            )
        except ValueError:
            failures.add("failure-ref:taw00:insufficient-agreement-evidence")
            continue
        agreement[key] = alpha
        if alpha < agreement_minimum:
            failures.add("failure-ref:taw00:agreement-below-gate")

    payload = {
        "pair_manifest_digest_ref": pair_manifest.manifest_digest_ref,
        "score_receipt_refs": sorted(
            score.score_receipt_digest_ref for score in scores
        ),
        "adjudication_receipt_refs": sorted(
            item.receipt_digest_ref for item in adjudications
        ),
        "agreement": agreement,
        "failure_refs": sorted(failures),
    }
    return ScoreValidationReport(
        report_ref=f"score-validation-report-ref:taw00:{canonical_digest(payload)}",
        valid=not failures,
        failure_refs=tuple(sorted(failures)),
        agreement_by_language_dimension=agreement,
    )


class CandidateManifestEntry(_FrozenModel):
    path_ref: str
    content_digest_ref: str
    acceptance_affecting: Literal[True] = True

    @model_validator(mode="after")
    def validate_entry(self) -> "CandidateManifestEntry":
        _ref(self.path_ref, "path_ref")
        _digest(self.content_digest_ref, "content_digest_ref")
        return self


class SourceProjection(_FrozenModel):
    schema_version: Literal["uaa-taw00-source-projection.v1"] = (
        "uaa-taw00-source-projection.v1"
    )
    projection_ref: str
    source_revision_ref: str
    status: Literal["scaffold_root_inventory_incomplete"]
    entries: tuple[CandidateManifestEntry, ...] = Field(..., min_length=1)
    projection_digest_ref: str
    routing_changes_added: Literal[False] = False
    prompt_changes_added: Literal[False] = False
    runtime_model_calls_added: Literal[False] = False
    authority_added: Literal[False] = False

    @model_validator(mode="after")
    def validate_projection(self) -> "SourceProjection":
        _ref(self.projection_ref, "projection_ref")
        if not _GIT_RE.fullmatch(self.source_revision_ref):
            raise ValueError("source projection requires an exact Git revision")
        path_refs = [item.path_ref for item in self.entries]
        if path_refs != sorted(path_refs) or len(path_refs) != len(set(path_refs)):
            raise ValueError("source projection entries must be unique and sorted")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"projection_digest_ref"})
        )
        if self.projection_digest_ref != expected:
            raise ValueError("source projection digest binding drift")
        return self


class CandidateLock(_FrozenModel):
    schema_version: Literal["uaa-taw00-candidate-lock.v1"] = (
        "uaa-taw00-candidate-lock.v1"
    )
    candidate_ref: str
    git_revision_ref: str
    entries: tuple[CandidateManifestEntry, ...] = Field(..., min_length=1)
    manifest_digest_ref: str
    evidence_only_delta_path_refs: tuple[str, ...]
    complete_projection: Literal[True] = True

    @model_validator(mode="after")
    def validate_lock(self) -> "CandidateLock":
        _ref(self.candidate_ref, "candidate_ref")
        if not _GIT_RE.fullmatch(self.git_revision_ref):
            raise ValueError("candidate lock requires an exact Git revision")
        _refs(self.evidence_only_delta_path_refs, "evidence_only_delta_path_refs")
        path_refs = [entry.path_ref for entry in self.entries]
        if path_refs != sorted(path_refs) or len(path_refs) != len(set(path_refs)):
            raise ValueError("candidate manifest entries must be unique and sorted")
        expected = canonical_digest(
            {
                "candidate_ref": self.candidate_ref,
                "git_revision_ref": self.git_revision_ref,
                "entries": [entry.model_dump(mode="json") for entry in self.entries],
                "evidence_only_delta_path_refs": self.evidence_only_delta_path_refs,
            }
        )
        if self.manifest_digest_ref != expected:
            raise ValueError("candidate lock digest binding drift")
        return self


def verify_candidate_lock(
    lock: CandidateLock,
    *,
    expected_path_refs: tuple[str, ...],
    revision_content_by_path_ref: dict[str, bytes],
) -> tuple[str, ...]:
    failures: set[str] = set()
    actual_refs = tuple(item.path_ref for item in lock.entries)
    if actual_refs != tuple(sorted(expected_path_refs)):
        failures.add("failure-ref:taw00:candidate-path-census-drift")
    if set(revision_content_by_path_ref) != set(expected_path_refs):
        failures.add("failure-ref:taw00:candidate-revision-census-drift")
    by_ref = {item.path_ref: item for item in lock.entries}
    for path_ref in expected_path_refs:
        content = revision_content_by_path_ref.get(path_ref)
        entry = by_ref.get(path_ref)
        if content is None or entry is None:
            continue
        digest = f"sha256:{hashlib.sha256(content).hexdigest()}"
        if entry.content_digest_ref != digest:
            failures.add("failure-ref:taw00:candidate-revision-content-drift")
    if set(lock.evidence_only_delta_path_refs) & set(expected_path_refs):
        failures.add("failure-ref:taw00:evidence-delta-overlaps-candidate-census")
    return tuple(sorted(failures))


def durable_payload_has_forbidden_fields(payload: object) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).lower()
            if lowered == "raw_content_persisted" and value is False:
                continue
            if lowered in _FORBIDDEN_FIELDS or lowered.startswith("raw_"):
                return True
        return any(
            durable_payload_has_forbidden_fields(value) for value in payload.values()
        )
    if isinstance(payload, (list, tuple)):
        return any(durable_payload_has_forbidden_fields(value) for value in payload)
    if isinstance(payload, str):
        if contains_obvious_secret({"value": payload}) or _HIGH_SIGNAL_SECRET_RE.search(
            payload
        ):
            return True
        try:
            validate_safe_execution_text(payload, "durable_value")
        except ValueError:
            return True
        return contains_absolute_local_path(payload)
    return False


def protocol_readiness(
    protocol: TAW00Protocol,
    *,
    commitment: HoldoutCommitment | None = None,
    development_corpus: DevelopmentCorpusManifest | None = None,
    pair_manifest: PairManifest | None = None,
    baseline_receipt: BaselineReceipt | None = None,
    source_projection_digest_ref: str | None = None,
    source_projection_path_refs: tuple[str, ...] = (),
    source_projection_verified: bool = False,
    baseline_acceptance_verified: bool = False,
    candidate_lock_verified: bool = False,
    candidate_lock_failures: tuple[str, ...] = (),
    score_report: ScoreValidationReport | None = None,
) -> dict[str, object]:
    reason_refs = list(protocol.blocked_reason_refs)
    if not TAW00_ACCEPTANCE_EVIDENCE_CONTRACT_COMPLETE:
        reason_refs.append("blocker-ref:taw00:acceptance-evidence-contract-incomplete")
    if protocol.status != "locked":
        reason_refs.append("blocker-ref:taw00:configuration-matrix-not-locked")
    if commitment is None:
        reason_refs.append("blocker-ref:taw00:independent-holdout-commitment-missing")
    elif commitment.cycle_ref != protocol.cycle_ref:
        reason_refs.append("blocker-ref:taw00:holdout-cycle-drift")
    if not INDEPENDENT_CUSTODIAN_IDENTITY_AUTHORITY_CONFIGURED:
        reason_refs.append(
            "blocker-ref:taw00:independent-custodian-identity-authority-missing"
        )
    if not INDEPENDENT_EVALUATOR_IDENTITY_AUTHORITY_CONFIGURED:
        reason_refs.append(
            "blocker-ref:taw00:independent-evaluator-identity-authority-missing"
        )
    if not BASELINE_ACCEPTANCE_AUTHORITY_CONFIGURED or not baseline_acceptance_verified:
        reason_refs.append(
            "blocker-ref:taw00:external-baseline-acceptance-authority-missing"
        )
    if development_corpus is None:
        reason_refs.append("blocker-ref:taw00:canonical-corpus-missing")
    if pair_manifest is None:
        reason_refs.append("blocker-ref:taw00:canonical-pair-manifest-missing")
    elif pair_manifest.cycle_ref != protocol.cycle_ref:
        reason_refs.append("blocker-ref:taw00:pair-manifest-cycle-drift")
    elif (
        protocol.expected_pair_manifest_digest_ref != pair_manifest.manifest_digest_ref
    ):
        reason_refs.append("blocker-ref:taw00:pair-manifest-digest-drift")
    elif (
        development_corpus is not None
        and pair_manifest.corpus_digest_ref != development_corpus.corpus_digest
    ):
        reason_refs.append("blocker-ref:taw00:pair-manifest-corpus-drift")
    if baseline_receipt is None:
        reason_refs.append("blocker-ref:taw00:accepted-current-baseline-missing")
    elif pair_manifest is None or source_projection_digest_ref is None:
        reason_refs.append("blocker-ref:taw00:baseline-binding-input-missing")
    else:
        reason_refs.extend(
            validate_baseline_receipt(
                baseline_receipt,
                protocol,
                source_projection_digest_ref=source_projection_digest_ref,
                pair_manifest_digest_ref=pair_manifest.manifest_digest_ref,
            )
        )
    if source_projection_digest_ref is None:
        reason_refs.append("blocker-ref:taw00:source-projection-missing")
    if not source_projection_verified:
        reason_refs.append("blocker-ref:taw00:source-projection-unverified")
    if source_projection_path_refs != protocol.source_projection_path_refs:
        reason_refs.append("blocker-ref:taw00:source-projection-path-census-drift")
    if not candidate_lock_verified:
        reason_refs.append("blocker-ref:taw00:candidate-lock-missing-or-unverified")
    if candidate_lock_failures:
        reason_refs.extend(candidate_lock_failures)
    if score_report is None:
        reason_refs.append("blocker-ref:taw00:blind-score-census-missing")
    elif not score_report.valid:
        reason_refs.extend(score_report.failure_refs)
    return {
        "protocol_ref": protocol.protocol_ref,
        "cycle_ref": protocol.cycle_ref,
        "status": "blocked",
        "reason_refs": sorted(set(reason_refs)),
        "routing_changes_added": False,
        "prompt_changes_added": False,
        "runtime_model_calls_added": False,
        "authority_added": False,
    }
