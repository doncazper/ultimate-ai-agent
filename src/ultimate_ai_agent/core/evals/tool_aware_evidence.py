from __future__ import annotations

import math
import re
from collections import defaultdict
from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.evals.tool_aware_baseline import (
    TAW00_ACCEPTANCE_EVIDENCE_BLOCKER_REFS,
    AcceptanceEvidenceBinding,
    AdjudicationBundle,
    BaselineMetric,
    BaselineReceipt,
    BlindScoreBundle,
    CandidateLock,
    PairManifest,
    PowerAnalysisReceipt,
    RandomizationBundle,
    SourceDependencyClosure,
    SourceProjection,
    TAW00Protocol,
    durable_payload_has_forbidden_fields,
    protocol_configuration_digest,
    validate_acceptance_evidence_binding,
)
from ultimate_ai_agent.core.evals.tool_aware_corpus import (
    HoldoutCommitment,
    HoldoutOpeningReceipt,
    canonical_digest,
)
from ultimate_ai_agent.core.evals.tool_aware_statistics import (
    binomial_one_sided_upper_bound,
    binomial_lower_tail_probability,
    holm_adjusted_alpha,
    normal_approximation_minimum_denominator,
    paired_bootstrap_one_sided_bound,
    paired_bootstrap_p95_difference_upper_bound,
)
from ultimate_ai_agent.core.execution.validation import validate_execution_ref


_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
TAW00_REQUIRED_ARTIFACT_REFS = frozenset(
    {
        "artifact-ref:taw00:adjudications",
        "artifact-ref:taw00:candidate-lock",
        "artifact-ref:taw00:computed-power",
        "artifact-ref:taw00:familywise-bounds",
        "artifact-ref:taw00:holdout-commitment",
        "artifact-ref:taw00:holdout-opening",
        "artifact-ref:taw00:legacy-power",
        "artifact-ref:taw00:matrix-census",
        "artifact-ref:taw00:observation-census",
        "artifact-ref:taw00:pair-manifest",
        "artifact-ref:taw00:protocol",
        "artifact-ref:taw00:randomization",
        "artifact-ref:taw00:scores",
        "artifact-ref:taw00:source-closure",
        "artifact-ref:taw00:source-projection",
    }
)


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _digest(value: str, field_name: str) -> None:
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be an exact sha256 digest")


def _unique_sorted(values: tuple[str, ...], field_name: str) -> None:
    if values != tuple(sorted(values)) or len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be unique and sorted")
    for value in values:
        _ref(value, field_name)


class EvaluationMatrixCell(_FrozenModel):
    language_ref: str
    configuration_ref: str
    hardware_backend_ref: str
    stratum_ref: str
    pair_refs: tuple[str, ...] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_cell(self) -> "EvaluationMatrixCell":
        for value, field_name in (
            (self.language_ref, "language_ref"),
            (self.configuration_ref, "configuration_ref"),
            (self.hardware_backend_ref, "hardware_backend_ref"),
            (self.stratum_ref, "stratum_ref"),
        ):
            _ref(value, field_name)
        _unique_sorted(self.pair_refs, "pair_refs")
        return self


class EvaluationMatrixCensus(_FrozenModel):
    schema_version: Literal["uaa-taw00-evaluation-matrix.v1"] = (
        "uaa-taw00-evaluation-matrix.v1"
    )
    cycle_ref: str
    protocol_digest_ref: str
    pair_manifest_digest_ref: str
    cells: tuple[EvaluationMatrixCell, ...] = Field(..., min_length=1)
    census_digest_ref: str
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_census(self) -> "EvaluationMatrixCensus":
        _ref(self.cycle_ref, "cycle_ref")
        _digest(self.protocol_digest_ref, "protocol_digest_ref")
        _digest(self.pair_manifest_digest_ref, "pair_manifest_digest_ref")
        keys = [
            (
                cell.language_ref,
                cell.configuration_ref,
                cell.hardware_backend_ref,
                cell.stratum_ref,
            )
            for cell in self.cells
        ]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("evaluation matrix cells must be unique and sorted")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"census_digest_ref"})
        )
        if self.census_digest_ref != expected:
            raise ValueError("evaluation matrix census digest binding drift")
        return self


def validate_evaluation_matrix(
    census: EvaluationMatrixCensus,
    *,
    protocol: TAW00Protocol,
    pair_manifest: PairManifest,
) -> tuple[str, ...]:
    failures: set[str] = set()
    if census.cycle_ref != protocol.cycle_ref:
        failures.add("failure-ref:taw00:matrix-cycle-drift")
    if census.protocol_digest_ref != protocol_configuration_digest(protocol):
        failures.add("failure-ref:taw00:matrix-protocol-drift")
    if census.pair_manifest_digest_ref != pair_manifest.manifest_digest_ref:
        failures.add("failure-ref:taw00:matrix-pair-manifest-drift")
    expected_keys = {
        (language, configuration, hardware, stratum)
        for language in protocol.supported_language_refs
        for configuration in protocol.model_configuration_refs
        for hardware in protocol.hardware_backend_refs
        for stratum in protocol.supported_stratum_refs
    }
    actual_keys = {
        (
            cell.language_ref,
            cell.configuration_ref,
            cell.hardware_backend_ref,
            cell.stratum_ref,
        )
        for cell in census.cells
    }
    if actual_keys != expected_keys:
        failures.add("failure-ref:taw00:matrix-cross-product-census-drift")
    pair_by_ref = {entry.pair_ref: entry for entry in pair_manifest.entries}
    observed_pair_refs: list[str] = []
    for cell in census.cells:
        observed_pair_refs.extend(cell.pair_refs)
        for pair_ref in cell.pair_refs:
            pair = pair_by_ref.get(pair_ref)
            if pair is None or any(
                (
                    pair.language_ref != cell.language_ref,
                    pair.configuration_ref != cell.configuration_ref,
                    pair.stratum_ref != cell.stratum_ref,
                )
            ):
                failures.add("failure-ref:taw00:matrix-pair-cell-binding-drift")
    if sorted(observed_pair_refs) != sorted(pair_by_ref) or len(
        observed_pair_refs
    ) != len(set(observed_pair_refs)):
        failures.add("failure-ref:taw00:matrix-pair-census-drift")
    return tuple(sorted(failures))


class ComputedPowerCell(_FrozenModel):
    metric_ref: str
    stratum_ref: str
    target_effect_size: float = Field(..., gt=0)
    variance_bound: float = Field(..., gt=0)
    adjusted_one_sided_alpha: float = Field(..., gt=0, lt=1)
    target_power: float = Field(..., gt=0.5, lt=1)
    computed_minimum_denominator: int = Field(..., ge=1, le=10_000)
    method_ref: Literal["power-method-ref:taw00:normal-bound-v1"] = (
        "power-method-ref:taw00:normal-bound-v1"
    )

    @model_validator(mode="after")
    def validate_cell(self) -> "ComputedPowerCell":
        _ref(self.metric_ref, "metric_ref")
        _ref(self.stratum_ref, "stratum_ref")
        expected = normal_approximation_minimum_denominator(
            target_effect_size=self.target_effect_size,
            variance_bound=self.variance_bound,
            one_sided_alpha=self.adjusted_one_sided_alpha,
            target_power=self.target_power,
        )
        if self.computed_minimum_denominator != expected:
            raise ValueError(
                "power denominator disagrees with preregistered calculation"
            )
        return self


class ComputedPowerAnalysisReceipt(_FrozenModel):
    schema_version: Literal["uaa-taw00-computed-power-analysis.v1"] = (
        "uaa-taw00-computed-power-analysis.v1"
    )
    cycle_ref: str
    protocol_digest_ref: str
    matrix_census_digest_ref: str
    cells: tuple[ComputedPowerCell, ...] = Field(..., min_length=1)
    receipt_digest_ref: str
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_receipt(self) -> "ComputedPowerAnalysisReceipt":
        _ref(self.cycle_ref, "cycle_ref")
        _digest(self.protocol_digest_ref, "protocol_digest_ref")
        _digest(self.matrix_census_digest_ref, "matrix_census_digest_ref")
        keys = [(cell.metric_ref, cell.stratum_ref) for cell in self.cells]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("computed power cells must be unique and sorted")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"receipt_digest_ref"})
        )
        if self.receipt_digest_ref != expected:
            raise ValueError("computed power receipt digest binding drift")
        return self


def validate_computed_power_analysis(
    receipt: ComputedPowerAnalysisReceipt,
    *,
    protocol: TAW00Protocol,
    matrix: EvaluationMatrixCensus,
) -> tuple[str, ...]:
    failures: set[str] = set()
    if receipt.cycle_ref != protocol.cycle_ref:
        failures.add("failure-ref:taw00:computed-power-cycle-drift")
    if receipt.protocol_digest_ref != protocol_configuration_digest(protocol):
        failures.add("failure-ref:taw00:computed-power-protocol-drift")
    if receipt.matrix_census_digest_ref != matrix.census_digest_ref:
        failures.add("failure-ref:taw00:computed-power-matrix-drift")
    required = {
        (requirement.metric_ref, requirement.stratum_ref): requirement
        for requirement in protocol.metric_census
    }
    actual = {(cell.metric_ref, cell.stratum_ref): cell for cell in receipt.cells}
    if set(actual) != set(required):
        failures.add("failure-ref:taw00:computed-power-metric-census-drift")
    pair_counts: dict[str, int] = defaultdict(int)
    for cell in matrix.cells:
        pair_counts[cell.stratum_ref] += len(cell.pair_refs)
    for key, requirement in required.items():
        cell = actual.get(key)
        if cell is None:
            continue
        expected_alpha = protocol.holm_familywise_alpha / len(required)
        if not math.isclose(
            cell.adjusted_one_sided_alpha, expected_alpha, abs_tol=1e-15
        ):
            failures.add("failure-ref:taw00:computed-power-familywise-alpha-drift")
        if requirement.minimum_denominator != cell.computed_minimum_denominator:
            failures.add("failure-ref:taw00:computed-power-protocol-denominator-drift")
        if pair_counts[cell.stratum_ref] < cell.computed_minimum_denominator:
            failures.add("failure-ref:taw00:computed-power-pair-census-below-gate")
    return tuple(sorted(failures))


class MetricObservation(_FrozenModel):
    pair_ref: str
    metric_ref: str
    stratum_ref: str
    baseline_value: float | None = None
    candidate_value: float | None = None
    event_occurred: bool | None = None
    observation_digest_ref: str
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_observation(self) -> "MetricObservation":
        for value, field_name in (
            (self.pair_ref, "pair_ref"),
            (self.metric_ref, "metric_ref"),
            (self.stratum_ref, "stratum_ref"),
        ):
            _ref(value, field_name)
        if self.event_occurred is None:
            if self.baseline_value is None or self.candidate_value is None:
                raise ValueError(
                    "paired observation requires baseline and candidate values"
                )
            if not math.isfinite(self.baseline_value) or not math.isfinite(
                self.candidate_value
            ):
                raise ValueError("paired observation values must be finite")
        elif self.baseline_value is not None or self.candidate_value is not None:
            raise ValueError("binomial observation cannot carry paired values")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"observation_digest_ref"})
        )
        if self.observation_digest_ref != expected:
            raise ValueError("observation digest binding drift")
        return self


class ObservationCensus(_FrozenModel):
    schema_version: Literal["uaa-taw00-observation-census.v1"] = (
        "uaa-taw00-observation-census.v1"
    )
    cycle_ref: str
    pair_manifest_digest_ref: str
    matrix_census_digest_ref: str
    bootstrap_seed: int = Field(..., ge=0, le=2**31 - 1)
    bootstrap_resamples: int = Field(default=10_000, ge=10_000, le=50_000)
    observations: tuple[MetricObservation, ...] = Field(..., min_length=1)
    census_digest_ref: str
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_census(self) -> "ObservationCensus":
        _ref(self.cycle_ref, "cycle_ref")
        _digest(self.pair_manifest_digest_ref, "pair_manifest_digest_ref")
        _digest(self.matrix_census_digest_ref, "matrix_census_digest_ref")
        keys = [
            (item.pair_ref, item.metric_ref, item.stratum_ref)
            for item in self.observations
        ]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("observations must be unique and sorted")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"census_digest_ref"})
        )
        if self.census_digest_ref != expected:
            raise ValueError("observation census digest binding drift")
        return self


def validate_observation_census(
    census: ObservationCensus,
    *,
    protocol: TAW00Protocol,
    matrix: EvaluationMatrixCensus,
    pair_manifest: PairManifest,
) -> tuple[str, ...]:
    failures: set[str] = set()
    if census.cycle_ref != protocol.cycle_ref:
        failures.add("failure-ref:taw00:observation-cycle-drift")
    if census.pair_manifest_digest_ref != pair_manifest.manifest_digest_ref:
        failures.add("failure-ref:taw00:observation-pair-manifest-drift")
    if census.matrix_census_digest_ref != matrix.census_digest_ref:
        failures.add("failure-ref:taw00:observation-matrix-drift")
    required_metrics = {
        (requirement.metric_ref, requirement.stratum_ref): requirement
        for requirement in protocol.metric_census
    }
    pair_by_ref = {entry.pair_ref: entry for entry in pair_manifest.entries}
    expected_keys = {
        (pair.pair_ref, metric_ref, pair.stratum_ref)
        for pair in pair_manifest.entries
        for metric_ref, stratum_ref in required_metrics
        if stratum_ref == pair.stratum_ref
    }
    actual_keys = {
        (item.pair_ref, item.metric_ref, item.stratum_ref)
        for item in census.observations
    }
    if actual_keys != expected_keys:
        failures.add("failure-ref:taw00:observation-exhaustive-census-drift")
    for item in census.observations:
        pair = pair_by_ref.get(item.pair_ref)
        requirement = required_metrics.get((item.metric_ref, item.stratum_ref))
        if pair is None or pair.stratum_ref != item.stratum_ref or requirement is None:
            failures.add("failure-ref:taw00:observation-pair-metric-binding-drift")
            continue
        binomial = (
            requirement.estimand_ref == "estimand-ref:taw00:binomial-one-sided-upper"
        )
        if binomial != (item.event_occurred is not None):
            failures.add("failure-ref:taw00:observation-estimand-shape-drift")
    return tuple(sorted(failures))


class FamilywiseBoundEntry(_FrozenModel):
    metric_ref: str
    stratum_ref: str
    event_count: int = Field(..., ge=0, le=10_000)
    denominator: int = Field(..., ge=1, le=10_000)
    null_rate: float = Field(..., gt=0, lt=1)
    ordering_p_value: float = Field(..., ge=0, le=1)
    adjusted_one_sided_alpha: float = Field(..., gt=0, lt=1)
    upper_bound: float = Field(..., ge=0, le=1)

    @model_validator(mode="after")
    def validate_entry(self) -> "FamilywiseBoundEntry":
        _ref(self.metric_ref, "metric_ref")
        _ref(self.stratum_ref, "stratum_ref")
        if self.event_count > self.denominator:
            raise ValueError("familywise event count exceeds denominator")
        expected_p = binomial_lower_tail_probability(
            self.event_count, self.denominator, null_rate=self.null_rate
        )
        if not math.isclose(self.ordering_p_value, expected_p, abs_tol=1e-12):
            raise ValueError("familywise ordering p-value drift")
        expected_upper = binomial_one_sided_upper_bound(
            self.event_count,
            self.denominator,
            confidence=1 - self.adjusted_one_sided_alpha,
        )
        if not math.isclose(self.upper_bound, expected_upper, abs_tol=1e-12):
            raise ValueError("familywise upper bound drift")
        return self


class FamilywiseBoundReceipt(_FrozenModel):
    schema_version: Literal["uaa-taw00-familywise-bounds.v1"] = (
        "uaa-taw00-familywise-bounds.v1"
    )
    cycle_ref: str
    observation_census_digest_ref: str
    familywise_alpha: Literal[0.05] = 0.05
    entries: tuple[FamilywiseBoundEntry, ...] = Field(..., min_length=1)
    receipt_digest_ref: str
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_receipt(self) -> "FamilywiseBoundReceipt":
        _ref(self.cycle_ref, "cycle_ref")
        _digest(self.observation_census_digest_ref, "observation_census_digest_ref")
        keys = [(entry.metric_ref, entry.stratum_ref) for entry in self.entries]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("familywise entries must be unique and sorted")
        thresholds = holm_adjusted_alpha(
            {
                f"{entry.metric_ref}|{entry.stratum_ref}": entry.ordering_p_value
                for entry in self.entries
            },
            familywise_alpha=self.familywise_alpha,
        )
        for entry in self.entries:
            key = f"{entry.metric_ref}|{entry.stratum_ref}"
            if not math.isclose(
                entry.adjusted_one_sided_alpha, thresholds[key], abs_tol=1e-15
            ):
                raise ValueError("familywise Holm alpha drift")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"receipt_digest_ref"})
        )
        if self.receipt_digest_ref != expected:
            raise ValueError("familywise receipt digest binding drift")
        return self


def validate_familywise_bounds(
    receipt: FamilywiseBoundReceipt,
    *,
    protocol: TAW00Protocol,
    observations: ObservationCensus,
) -> tuple[str, ...]:
    failures: set[str] = set()
    if receipt.cycle_ref != protocol.cycle_ref:
        failures.add("failure-ref:taw00:familywise-cycle-drift")
    if receipt.observation_census_digest_ref != observations.census_digest_ref:
        failures.add("failure-ref:taw00:familywise-observation-census-drift")
    required = {
        (item.metric_ref, item.stratum_ref): item
        for item in protocol.metric_census
        if item.estimand_ref == "estimand-ref:taw00:binomial-one-sided-upper"
    }
    actual = {(item.metric_ref, item.stratum_ref): item for item in receipt.entries}
    if set(actual) != set(required):
        failures.add("failure-ref:taw00:familywise-metric-census-drift")
    by_key: dict[tuple[str, str], list[MetricObservation]] = defaultdict(list)
    for item in observations.observations:
        if item.event_occurred is not None:
            by_key[(item.metric_ref, item.stratum_ref)].append(item)
    for key, requirement in required.items():
        entry = actual.get(key)
        rows = by_key.get(key, [])
        if entry is None:
            continue
        if entry.denominator != len(rows) or entry.event_count != sum(
            item.event_occurred is True for item in rows
        ):
            failures.add("failure-ref:taw00:familywise-observation-count-drift")
        if not math.isclose(
            entry.null_rate, requirement.absolute_threshold, abs_tol=1e-15
        ):
            failures.add("failure-ref:taw00:familywise-null-rate-drift")
    return tuple(sorted(failures))


def derive_baseline_metrics(
    *,
    protocol: TAW00Protocol,
    observations: ObservationCensus,
    familywise_bounds: FamilywiseBoundReceipt,
) -> tuple[BaselineMetric, ...]:
    bounds = {
        (entry.metric_ref, entry.stratum_ref): entry
        for entry in familywise_bounds.entries
    }
    by_key: dict[tuple[str, str], list[MetricObservation]] = defaultdict(list)
    for observation in observations.observations:
        by_key[(observation.metric_ref, observation.stratum_ref)].append(observation)
    metrics: list[BaselineMetric] = []
    for requirement in sorted(
        protocol.metric_census, key=lambda item: (item.metric_ref, item.stratum_ref)
    ):
        key = (requirement.metric_ref, requirement.stratum_ref)
        rows = by_key[key]
        evidence_digest = canonical_digest([row.observation_digest_ref for row in rows])
        if requirement.estimand_ref == "estimand-ref:taw00:binomial-one-sided-upper":
            bound = bounds[key]
            metrics.append(
                BaselineMetric(
                    metric_ref=requirement.metric_ref,
                    stratum_ref=requirement.stratum_ref,
                    denominator=bound.denominator,
                    event_count=bound.event_count,
                    point_estimate=bound.event_count / bound.denominator,
                    lower_bound=0,
                    upper_bound=bound.upper_bound,
                    confidence_level=1 - bound.adjusted_one_sided_alpha,
                    estimator_ref=requirement.estimator_ref,
                    estimand_ref=requirement.estimand_ref,
                    evidence_digest_ref=evidence_digest,
                )
            )
            continue
        baseline = [float(row.baseline_value) for row in rows]
        candidate = [float(row.candidate_value) for row in rows]
        if (
            requirement.estimand_ref
            == "estimand-ref:taw00:paired-p95-ttft-one-sided-upper"
        ):
            point, upper = paired_bootstrap_p95_difference_upper_bound(
                baseline,
                candidate,
                resamples=observations.bootstrap_resamples,
                seed=observations.bootstrap_seed,
            )
            lower = min(point, 0.0)
            baseline_reference_value = sorted(baseline)[
                max(0, math.ceil(0.95 * len(baseline)) - 1)
            ]
        else:
            point, lower = paired_bootstrap_one_sided_bound(
                baseline,
                candidate,
                side="lower",
                resamples=observations.bootstrap_resamples,
                seed=observations.bootstrap_seed,
            )
            upper = max(point, 0.0)
            baseline_reference_value = None
        metrics.append(
            BaselineMetric(
                metric_ref=requirement.metric_ref,
                stratum_ref=requirement.stratum_ref,
                denominator=len(rows),
                point_estimate=point,
                lower_bound=lower,
                upper_bound=upper,
                baseline_reference_value=baseline_reference_value,
                estimator_ref=requirement.estimator_ref,
                estimand_ref=requirement.estimand_ref,
                evidence_digest_ref=evidence_digest,
            )
        )
    return tuple(metrics)


class ArtifactCensusEntry(_FrozenModel):
    artifact_ref: str
    schema_ref: str
    artifact_digest_ref: str
    recursive_content_safety_verified: Literal[True] = True

    @model_validator(mode="after")
    def validate_entry(self) -> "ArtifactCensusEntry":
        _ref(self.artifact_ref, "artifact_ref")
        _ref(self.schema_ref, "schema_ref")
        _digest(self.artifact_digest_ref, "artifact_digest_ref")
        return self


class ArtifactCensus(_FrozenModel):
    schema_version: Literal["uaa-taw00-artifact-census.v1"] = (
        "uaa-taw00-artifact-census.v1"
    )
    cycle_ref: str
    entries: tuple[ArtifactCensusEntry, ...] = Field(..., min_length=1)
    census_digest_ref: str
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_census(self) -> "ArtifactCensus":
        _ref(self.cycle_ref, "cycle_ref")
        refs = [entry.artifact_ref for entry in self.entries]
        if refs != sorted(refs) or len(refs) != len(set(refs)):
            raise ValueError("artifact census entries must be unique and sorted")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"census_digest_ref"})
        )
        if self.census_digest_ref != expected:
            raise ValueError("artifact census digest binding drift")
        return self


def build_artifact_census(
    *,
    cycle_ref: str,
    artifacts: Mapping[str, tuple[str, object]],
) -> ArtifactCensus:
    entries = []
    for artifact_ref in sorted(artifacts):
        schema_ref, payload = artifacts[artifact_ref]
        if durable_payload_has_forbidden_fields(payload):
            raise ValueError("artifact census contains unsafe durable content")
        entries.append(
            ArtifactCensusEntry(
                artifact_ref=artifact_ref,
                schema_ref=schema_ref,
                artifact_digest_ref=canonical_digest(payload),
            )
        )
    payload = {
        "schema_version": "uaa-taw00-artifact-census.v1",
        "cycle_ref": cycle_ref,
        "entries": [entry.model_dump(mode="json") for entry in entries],
        "raw_content_persisted": False,
    }
    return ArtifactCensus(
        **payload,
        census_digest_ref=canonical_digest(payload),
    )


def validate_artifact_census(
    census: ArtifactCensus,
    *,
    artifacts: Mapping[str, tuple[str, object]],
) -> tuple[str, ...]:
    try:
        expected = build_artifact_census(
            cycle_ref=census.cycle_ref, artifacts=artifacts
        )
    except ValueError:
        return ("failure-ref:taw00:artifact-census-unsafe-content",)
    failures: set[str] = set()
    if set(artifacts) != TAW00_REQUIRED_ARTIFACT_REFS:
        failures.add("failure-ref:taw00:artifact-census-required-inventory-drift")
    if census.entries != expected.entries:
        failures.add("failure-ref:taw00:artifact-census-drift")
    return tuple(sorted(failures))


class CompleteAcceptanceEvidenceBinding(_FrozenModel):
    schema_version: Literal["uaa-taw00-complete-acceptance-binding.v1"] = (
        "uaa-taw00-complete-acceptance-binding.v1"
    )
    cycle_ref: str
    legacy_binding_digest_ref: str
    holdout_commitment_digest_ref: str
    holdout_opening_receipt_digest_ref: str
    matrix_census_digest_ref: str
    computed_power_receipt_digest_ref: str
    observation_census_digest_ref: str
    familywise_bound_receipt_digest_ref: str
    artifact_census_digest_ref: str
    baseline_receipt_digest_ref: str
    binding_digest_ref: str
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_binding(self) -> "CompleteAcceptanceEvidenceBinding":
        _ref(self.cycle_ref, "cycle_ref")
        for field_name in (
            "legacy_binding_digest_ref",
            "holdout_commitment_digest_ref",
            "holdout_opening_receipt_digest_ref",
            "matrix_census_digest_ref",
            "computed_power_receipt_digest_ref",
            "observation_census_digest_ref",
            "familywise_bound_receipt_digest_ref",
            "artifact_census_digest_ref",
            "baseline_receipt_digest_ref",
        ):
            _digest(getattr(self, field_name), field_name)
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"binding_digest_ref"})
        )
        if self.binding_digest_ref != expected:
            raise ValueError("complete acceptance binding digest drift")
        return self


def validate_complete_acceptance_evidence(
    binding: CompleteAcceptanceEvidenceBinding,
    *,
    legacy_binding: AcceptanceEvidenceBinding,
    protocol: TAW00Protocol,
    legacy_power_analysis: PowerAnalysisReceipt,
    source_projection: SourceProjection,
    source_closure: SourceDependencyClosure,
    candidate_lock: CandidateLock,
    pair_manifest: PairManifest,
    baseline_receipt: BaselineReceipt,
    randomization_bundle: RandomizationBundle,
    score_bundle: BlindScoreBundle,
    adjudication_bundle: AdjudicationBundle,
    commitment: HoldoutCommitment,
    opening: HoldoutOpeningReceipt,
    matrix: EvaluationMatrixCensus,
    computed_power: ComputedPowerAnalysisReceipt,
    observations: ObservationCensus,
    familywise_bounds: FamilywiseBoundReceipt,
    artifact_census: ArtifactCensus,
    artifact_payloads: Mapping[str, tuple[str, object]],
) -> tuple[str, ...]:
    failures = set(
        validate_acceptance_evidence_binding(
            legacy_binding,
            protocol=protocol,
            power_analysis=legacy_power_analysis,
            source_projection=source_projection,
            source_closure=source_closure,
            candidate_lock=candidate_lock,
            pair_manifest=pair_manifest,
            baseline_receipt=baseline_receipt,
            randomization_bundle=randomization_bundle,
            score_bundle=score_bundle,
            adjudication_bundle=adjudication_bundle,
        )
    )
    failures.difference_update(TAW00_ACCEPTANCE_EVIDENCE_BLOCKER_REFS)
    failures.update(
        validate_evaluation_matrix(
            matrix, protocol=protocol, pair_manifest=pair_manifest
        )
    )
    failures.update(
        validate_computed_power_analysis(
            computed_power, protocol=protocol, matrix=matrix
        )
    )
    failures.update(
        validate_observation_census(
            observations,
            protocol=protocol,
            matrix=matrix,
            pair_manifest=pair_manifest,
        )
    )
    failures.update(
        validate_familywise_bounds(
            familywise_bounds,
            protocol=protocol,
            observations=observations,
        )
    )
    failures.update(
        validate_artifact_census(artifact_census, artifacts=artifact_payloads)
    )
    if (
        opening.cycle_ref != commitment.cycle_ref
        or binding.cycle_ref != protocol.cycle_ref
    ):
        failures.add("failure-ref:taw00:complete-binding-cycle-drift")
    if opening.custodian_ref != commitment.custodian_ref:
        failures.add("failure-ref:taw00:holdout-opening-custodian-drift")
    if opening.commitment_digest_ref != commitment.commitment_digest:
        failures.add("failure-ref:taw00:holdout-opening-commitment-drift")
    expected_metrics = derive_baseline_metrics(
        protocol=protocol,
        observations=observations,
        familywise_bounds=familywise_bounds,
    )
    if baseline_receipt.metrics != expected_metrics:
        failures.add("failure-ref:taw00:baseline-observation-derivation-drift")
    if baseline_receipt.artifact_census_digest_ref != artifact_census.census_digest_ref:
        failures.add("failure-ref:taw00:baseline-artifact-census-drift")
    expected = {
        "legacy_binding_digest_ref": legacy_binding.binding_digest_ref,
        "holdout_commitment_digest_ref": commitment.commitment_digest,
        "holdout_opening_receipt_digest_ref": opening.receipt_digest_ref,
        "matrix_census_digest_ref": matrix.census_digest_ref,
        "computed_power_receipt_digest_ref": computed_power.receipt_digest_ref,
        "observation_census_digest_ref": observations.census_digest_ref,
        "familywise_bound_receipt_digest_ref": familywise_bounds.receipt_digest_ref,
        "artifact_census_digest_ref": artifact_census.census_digest_ref,
        "baseline_receipt_digest_ref": baseline_receipt.receipt_digest_ref,
    }
    for field_name, value in expected.items():
        if getattr(binding, field_name) != value:
            failures.add(
                "failure-ref:taw00:complete-binding-"
                + field_name.removesuffix("_ref").replace("_", "-")
                + "-drift"
            )
    return tuple(sorted(failures))
