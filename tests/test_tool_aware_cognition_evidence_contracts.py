from __future__ import annotations

import json

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from scripts import run_tool_aware_baseline as baseline_cli
from scripts import verify_tool_aware_cognition_taw00 as taw00_verifier

from ultimate_ai_agent.core.evals.tool_aware_baseline import (
    TAW00_ACCEPTANCE_SPECS,
    TAW00_DIMENSIONS,
    TAW00_MANDATORY_CANDIDATE_PATH_REFS,
    TAW00_REQUIRED_METRICS,
    AcceptanceEvidenceBinding,
    AdjudicationBundle,
    BaselineReceipt,
    BlindScore,
    BlindScoreBundle,
    CandidateLock,
    CandidateManifestEntry,
    MetricRequirement,
    PairManifest,
    PairManifestEntry,
    PowerAnalysisCell,
    PowerAnalysisReceipt,
    RandomizationBundle,
    RandomizationReceipt,
    SourceDependencyClosure,
    SourceDependencyEntry,
    SourceProjection,
    TAW00Protocol,
    protocol_configuration_digest,
)
from ultimate_ai_agent.core.evals.tool_aware_corpus import (
    build_holdout_commitment,
    build_holdout_opening_receipt,
    canonical_digest,
)
from ultimate_ai_agent.core.evals.tool_aware_evidence import (
    TAW00_REQUIRED_ARTIFACT_REFS,
    CompleteAcceptanceEvidenceBinding,
    ComputedPowerAnalysisReceipt,
    ComputedPowerCell,
    EvaluationMatrixCensus,
    EvaluationMatrixCell,
    FamilywiseBoundEntry,
    FamilywiseBoundReceipt,
    MetricObservation,
    ObservationCensus,
    build_artifact_census,
    derive_baseline_metrics,
    validate_artifact_census,
    validate_complete_acceptance_evidence,
    validate_computed_power_analysis,
    validate_evaluation_matrix,
    validate_familywise_bounds,
    validate_observation_census,
)
from ultimate_ai_agent.core.evals.tool_aware_statistics import (
    binomial_one_sided_upper_bound,
    binomial_lower_tail_probability,
    holm_adjusted_alpha,
    normal_approximation_minimum_denominator,
)


LANGUAGE = "language-ref:taw00:test"
CONFIGURATION = "configuration-ref:taw00:test"
HARDWARE = "hardware-ref:taw00:test"
STRATUM = "stratum-ref:taw00:test"
CYCLE = "cycle-ref:taw00:test"
PAIR = "pair-ref:taw00:test"
SOURCE_PATH = "repo-path-ref:a.py"
DIGEST_1 = "sha256:" + "1" * 64


def _requirements() -> tuple[MetricRequirement, ...]:
    requirements = []
    for metric_ref in TAW00_REQUIRED_METRICS:
        acceptance_bound, threshold, relative = TAW00_ACCEPTANCE_SPECS[metric_ref]
        if metric_ref.startswith("metric-ref:taw00:quality-"):
            estimand = "estimand-ref:taw00:paired-quality-one-sided-lower"
            estimator = "estimator-ref:taw00:paired-bootstrap"
        elif metric_ref == "metric-ref:taw00:p95-ttft-difference":
            estimand = "estimand-ref:taw00:paired-p95-ttft-one-sided-upper"
            estimator = "estimator-ref:taw00:request-clustered"
        else:
            estimand = "estimand-ref:taw00:binomial-one-sided-upper"
            estimator = "estimator-ref:taw00:clopper-pearson"
        requirements.append(
            MetricRequirement(
                metric_ref=metric_ref,
                stratum_ref=STRATUM,
                minimum_denominator=1,
                estimand_ref=estimand,
                estimator_ref=estimator,
                acceptance_bound=acceptance_bound,
                absolute_threshold=threshold,
                relative_to_baseline_fraction=relative,
            )
        )
    return tuple(sorted(requirements, key=lambda item: item.metric_ref))


def _candidate_lock() -> CandidateLock:
    entries = (
        CandidateManifestEntry(
            path_ref=SOURCE_PATH,
            content_digest_ref="sha256:" + "a" * 64,
        ),
    )
    payload = {
        "candidate_ref": "candidate-ref:taw00:test",
        "git_revision_ref": "git-sha:" + "a" * 40,
        "entries": [entry.model_dump(mode="json") for entry in entries],
        "evidence_only_delta_path_refs": (),
    }
    return CandidateLock(
        candidate_ref=payload["candidate_ref"],
        git_revision_ref=payload["git_revision_ref"],
        entries=entries,
        evidence_only_delta_path_refs=(),
        manifest_digest_ref=canonical_digest(payload),
    )


def _pair_manifest(lock: CandidateLock) -> PairManifest:
    baseline_digest = "sha256:" + "b" * 64
    candidate_digest = "sha256:" + "c" * 64
    randomization_payload = {
        "schema_version": "uaa-taw00-randomization-receipt.v1",
        "pair_ref": PAIR,
        "cycle_ref": CYCLE,
        "candidate_manifest_digest_ref": lock.manifest_digest_ref,
        "baseline_payload_digest_ref": baseline_digest,
        "candidate_payload_digest_ref": candidate_digest,
        "blinded_order": "a_then_b",
        "baseline_label": "a",
        "a_payload_digest_ref": baseline_digest,
        "b_payload_digest_ref": candidate_digest,
        "method_ref": "randomization-method-ref:taw00:balanced-v1",
        "raw_content_persisted": False,
    }
    entry = PairManifestEntry(
        pair_ref=PAIR,
        case_ref="case-ref:taw00:test",
        language_ref=LANGUAGE,
        configuration_ref=CONFIGURATION,
        stratum_ref=STRATUM,
        baseline_payload_digest_ref=baseline_digest,
        candidate_payload_digest_ref=candidate_digest,
        randomization_receipt_digest_ref=canonical_digest(randomization_payload),
    )
    payload = {
        "schema_version": "uaa-taw00-pair-manifest.v1",
        "cycle_ref": CYCLE,
        "corpus_digest_ref": "sha256:" + "d" * 64,
        "candidate_ref": lock.candidate_ref,
        "candidate_revision_ref": lock.git_revision_ref,
        "candidate_manifest_digest_ref": lock.manifest_digest_ref,
        "entries": [entry.model_dump(mode="json")],
    }
    return PairManifest(**payload, manifest_digest_ref=canonical_digest(payload))


def _protocol(
    pair_manifest: PairManifest,
) -> tuple[TAW00Protocol, PowerAnalysisReceipt]:
    base = {
        "status": "locked",
        "cycle_ref": CYCLE,
        "supported_language_refs": [LANGUAGE],
        "model_configuration_refs": [CONFIGURATION],
        "hardware_backend_refs": [HARDWARE],
        "supported_stratum_refs": [STRATUM],
        "rubric_ref": "rubric-ref:taw00:test",
        "language_qualification_protocol_ref": "qualification-ref:taw00:test",
        "exact_case_recovery_protocol_ref": "recovery-ref:taw00:test",
        "estimator_refs": [
            "estimator-ref:taw00:paired-bootstrap",
            "estimator-ref:taw00:evaluator-clustered",
            "estimator-ref:taw00:request-clustered",
            "estimator-ref:taw00:holm-step-down",
            "estimator-ref:taw00:krippendorff-ordinal",
            "estimator-ref:taw00:clopper-pearson",
        ],
        "metric_census": [item.model_dump(mode="json") for item in _requirements()],
        "power_analysis_receipt_digest_ref": DIGEST_1,
        "expected_pair_manifest_digest_ref": pair_manifest.manifest_digest_ref,
        "acceptance_affecting_path_refs": sorted(
            {*TAW00_MANDATORY_CANDIDATE_PATH_REFS, SOURCE_PATH}
        ),
        "source_projection_path_refs": [SOURCE_PATH],
        "blocked_reason_refs": [],
    }
    provisional = TAW00Protocol.model_validate(base)
    cells = tuple(
        PowerAnalysisCell(
            metric_ref=item.metric_ref,
            stratum_ref=item.stratum_ref,
            minimum_denominator=1,
            target_effect_size=100,
            familywise_alpha=0.05,
            target_power=0.8,
            method_ref="power-method-ref:taw00:pre-registered-v1",
        )
        for item in _requirements()
    )
    power_payload = {
        "schema_version": "uaa-taw00-power-analysis.v1",
        "cycle_ref": CYCLE,
        "protocol_digest_ref": protocol_configuration_digest(provisional),
        "cells": [cell.model_dump(mode="json") for cell in cells],
        "raw_content_persisted": False,
    }
    power = PowerAnalysisReceipt(
        **power_payload, receipt_digest_ref=canonical_digest(power_payload)
    )
    return (
        TAW00Protocol.model_validate(
            {**base, "power_analysis_receipt_digest_ref": power.receipt_digest_ref}
        ),
        power,
    )


def _matrix(
    protocol: TAW00Protocol, pair_manifest: PairManifest
) -> EvaluationMatrixCensus:
    cell = EvaluationMatrixCell(
        language_ref=LANGUAGE,
        configuration_ref=CONFIGURATION,
        hardware_backend_ref=HARDWARE,
        stratum_ref=STRATUM,
        pair_refs=(PAIR,),
    )
    payload = {
        "schema_version": "uaa-taw00-evaluation-matrix.v1",
        "cycle_ref": CYCLE,
        "protocol_digest_ref": protocol_configuration_digest(protocol),
        "pair_manifest_digest_ref": pair_manifest.manifest_digest_ref,
        "cells": [cell.model_dump(mode="json")],
        "raw_content_persisted": False,
    }
    return EvaluationMatrixCensus(
        **payload, census_digest_ref=canonical_digest(payload)
    )


def _computed_power(
    protocol: TAW00Protocol, matrix: EvaluationMatrixCensus
) -> ComputedPowerAnalysisReceipt:
    alpha = 0.05 / len(protocol.metric_census)
    cells = []
    for requirement in protocol.metric_census:
        denominator = normal_approximation_minimum_denominator(
            target_effect_size=100,
            variance_bound=1,
            one_sided_alpha=alpha,
            target_power=0.8,
        )
        cells.append(
            ComputedPowerCell(
                metric_ref=requirement.metric_ref,
                stratum_ref=requirement.stratum_ref,
                target_effect_size=100,
                variance_bound=1,
                adjusted_one_sided_alpha=alpha,
                target_power=0.8,
                computed_minimum_denominator=denominator,
            )
        )
    cells.sort(key=lambda item: item.metric_ref)
    payload = {
        "schema_version": "uaa-taw00-computed-power-analysis.v1",
        "cycle_ref": CYCLE,
        "protocol_digest_ref": protocol_configuration_digest(protocol),
        "matrix_census_digest_ref": matrix.census_digest_ref,
        "cells": [cell.model_dump(mode="json") for cell in cells],
        "raw_content_persisted": False,
    }
    return ComputedPowerAnalysisReceipt(
        **payload, receipt_digest_ref=canonical_digest(payload)
    )


def _observations(
    protocol: TAW00Protocol,
    matrix: EvaluationMatrixCensus,
    pair_manifest: PairManifest,
) -> ObservationCensus:
    rows = []
    for requirement in protocol.metric_census:
        payload = {
            "pair_ref": PAIR,
            "metric_ref": requirement.metric_ref,
            "stratum_ref": STRATUM,
            "baseline_value": None,
            "candidate_value": None,
            "event_occurred": False,
            "raw_content_persisted": False,
        }
        if requirement.estimand_ref != "estimand-ref:taw00:binomial-one-sided-upper":
            payload.update(
                baseline_value=100.0,
                candidate_value=100.0,
                event_occurred=None,
            )
        rows.append(
            MetricObservation(
                **payload,
                observation_digest_ref=canonical_digest(payload),
            )
        )
    rows.sort(key=lambda item: item.metric_ref)
    payload = {
        "schema_version": "uaa-taw00-observation-census.v1",
        "cycle_ref": CYCLE,
        "pair_manifest_digest_ref": pair_manifest.manifest_digest_ref,
        "matrix_census_digest_ref": matrix.census_digest_ref,
        "bootstrap_seed": 7,
        "bootstrap_resamples": 10_000,
        "observations": [row.model_dump(mode="json") for row in rows],
        "raw_content_persisted": False,
    }
    return ObservationCensus(**payload, census_digest_ref=canonical_digest(payload))


def _familywise(
    protocol: TAW00Protocol, observations: ObservationCensus
) -> FamilywiseBoundReceipt:
    binomial_requirements = [
        item
        for item in protocol.metric_census
        if item.estimand_ref == "estimand-ref:taw00:binomial-one-sided-upper"
    ]
    p_values = {
        f"{item.metric_ref}|{item.stratum_ref}": binomial_lower_tail_probability(
            0, 1, null_rate=item.absolute_threshold
        )
        for item in binomial_requirements
    }
    thresholds = holm_adjusted_alpha(p_values)
    entries = []
    for requirement in binomial_requirements:
        key = f"{requirement.metric_ref}|{requirement.stratum_ref}"
        alpha = thresholds[key]
        entries.append(
            FamilywiseBoundEntry(
                metric_ref=requirement.metric_ref,
                stratum_ref=requirement.stratum_ref,
                event_count=0,
                denominator=1,
                null_rate=requirement.absolute_threshold,
                ordering_p_value=p_values[key],
                adjusted_one_sided_alpha=alpha,
                upper_bound=binomial_one_sided_upper_bound(0, 1, confidence=1 - alpha),
            )
        )
    entries.sort(key=lambda item: item.metric_ref)
    payload = {
        "schema_version": "uaa-taw00-familywise-bounds.v1",
        "cycle_ref": CYCLE,
        "observation_census_digest_ref": observations.census_digest_ref,
        "familywise_alpha": 0.05,
        "entries": [entry.model_dump(mode="json") for entry in entries],
        "raw_content_persisted": False,
    }
    return FamilywiseBoundReceipt(
        **payload, receipt_digest_ref=canonical_digest(payload)
    )


def test_power_matrix_observation_and_familywise_contracts_are_computed() -> None:
    assert binomial_lower_tail_probability(0, 100, null_rate=0.01) == pytest.approx(
        0.99**100
    )

    lock = _candidate_lock()
    pairs = _pair_manifest(lock)
    protocol, _ = _protocol(pairs)
    matrix = _matrix(protocol, pairs)
    power = _computed_power(protocol, matrix)
    observations = _observations(protocol, matrix, pairs)
    familywise = _familywise(protocol, observations)

    assert (
        validate_evaluation_matrix(matrix, protocol=protocol, pair_manifest=pairs) == ()
    )
    assert (
        validate_computed_power_analysis(power, protocol=protocol, matrix=matrix) == ()
    )
    assert (
        validate_observation_census(
            observations, protocol=protocol, matrix=matrix, pair_manifest=pairs
        )
        == ()
    )
    assert (
        validate_familywise_bounds(
            familywise, protocol=protocol, observations=observations
        )
        == ()
    )
    assert len(
        derive_baseline_metrics(
            protocol=protocol,
            observations=observations,
            familywise_bounds=familywise,
        )
    ) == len(TAW00_REQUIRED_METRICS)


def test_computed_contracts_reject_tampering() -> None:
    with pytest.raises(ValidationError, match="power denominator disagrees"):
        ComputedPowerCell(
            metric_ref="metric-ref:taw00:test",
            stratum_ref=STRATUM,
            target_effect_size=100,
            variance_bound=1,
            adjusted_one_sided_alpha=0.01,
            target_power=0.8,
            computed_minimum_denominator=2,
        )
    payload = {
        "pair_ref": PAIR,
        "metric_ref": "metric-ref:taw00:test",
        "stratum_ref": STRATUM,
        "baseline_value": 1.0,
        "candidate_value": 1.0,
        "event_occurred": None,
        "raw_content_persisted": False,
    }
    with pytest.raises(ValidationError, match="observation digest binding drift"):
        MetricObservation(**payload, observation_digest_ref=DIGEST_1)


def test_holdout_opening_binds_commitment_without_persisting_private_material() -> None:
    private = json.dumps(
        {
            "schema_version": "uaa-taw00-private-holdout.v1",
            "cycle_ref": CYCLE,
            "corpus_ref": "corpus-ref:taw00:holdout",
            "deterministic_seed_ref": "seed-ref:taw00:holdout",
            "seed_material_hex": "22" * 32,
            "cases": [
                {
                    "case_ref": "case-ref:taw00:holdout",
                    "category_ref": "category-ref:taw00:ordinary-chat",
                    "rubric_ref": "rubric-ref:taw00:test",
                    "parameter_refs": ["parameter-ref:taw00:test"],
                    "variant_index": 1,
                }
            ],
            "synthetic_only": True,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    key = b"k" * 32
    commitment = build_holdout_commitment(
        cycle_ref=CYCLE,
        custodian_ref="custodian-ref:taw00:test",
        creation_order_evidence_ref="evidence-ref:taw00:created-before-candidate",
        custodian_attestation_ref="attestation-ref:taw00:test",
        secret_key=key,
        private_manifest=private,
    )
    opening = build_holdout_opening_receipt(
        commitment,
        opening_attestation_ref="attestation-ref:taw00:opening",
        secret_key=key,
        private_manifest=private,
    )

    assert opening.commitment_digest_ref == commitment.commitment_digest
    assert opening.private_key_persisted is False
    assert opening.private_manifest_persisted is False
    with pytest.raises(ValueError, match="does not open"):
        build_holdout_opening_receipt(
            commitment,
            opening_attestation_ref="attestation-ref:taw00:opening",
            secret_key=b"x" * 32,
            private_manifest=private,
        )


def test_artifact_census_is_exact_and_recursively_content_safe() -> None:
    artifacts = {
        ref: ("schema-ref:taw00:test", {"status_ref": "status-ref:taw00:safe"})
        for ref in TAW00_REQUIRED_ARTIFACT_REFS
    }
    census = build_artifact_census(cycle_ref=CYCLE, artifacts=artifacts)
    assert validate_artifact_census(census, artifacts=artifacts) == ()
    missing = dict(artifacts)
    missing.pop(next(iter(missing)))
    assert "failure-ref:taw00:artifact-census-required-inventory-drift" in (
        validate_artifact_census(census, artifacts=missing)
    )
    unsafe = dict(artifacts)
    unsafe[next(iter(unsafe))] = (
        "schema-ref:taw00:test",
        {"raw_prompt": "not durable"},
    )
    with pytest.raises(ValueError, match="unsafe durable content"):
        build_artifact_census(cycle_ref=CYCLE, artifacts=unsafe)


def _holdout_artifacts():
    private = json.dumps(
        {
            "schema_version": "uaa-taw00-private-holdout.v1",
            "cycle_ref": CYCLE,
            "corpus_ref": "corpus-ref:taw00:holdout",
            "deterministic_seed_ref": "seed-ref:taw00:holdout",
            "seed_material_hex": "33" * 32,
            "cases": [
                {
                    "case_ref": "case-ref:taw00:holdout",
                    "category_ref": "category-ref:taw00:ordinary-chat",
                    "rubric_ref": "rubric-ref:taw00:test",
                    "parameter_refs": ["parameter-ref:taw00:test"],
                    "variant_index": 2,
                }
            ],
            "synthetic_only": True,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    key = b"z" * 32
    commitment = build_holdout_commitment(
        cycle_ref=CYCLE,
        custodian_ref="custodian-ref:taw00:test",
        creation_order_evidence_ref="evidence-ref:taw00:created-before-candidate",
        custodian_attestation_ref="attestation-ref:taw00:test",
        secret_key=key,
        private_manifest=private,
    )
    opening = build_holdout_opening_receipt(
        commitment,
        opening_attestation_ref="attestation-ref:taw00:opening",
        secret_key=key,
        private_manifest=private,
    )
    return commitment, opening


def test_complete_binding_clears_only_the_six_code_owned_contract_failures(
    tmp_path, monkeypatch, capsys
) -> None:
    lock = _candidate_lock()
    pairs = _pair_manifest(lock)
    protocol, legacy_power = _protocol(pairs)
    matrix = _matrix(protocol, pairs)
    computed_power = _computed_power(protocol, matrix)
    observations = _observations(protocol, matrix, pairs)
    familywise = _familywise(protocol, observations)
    commitment, opening = _holdout_artifacts()

    source_entry = CandidateManifestEntry(
        path_ref=SOURCE_PATH,
        content_digest_ref="sha256:" + "a" * 64,
    )
    projection_payload = {
        "schema_version": "uaa-taw00-source-projection.v1",
        "projection_ref": "projection-ref:taw00:test",
        "source_revision_ref": lock.git_revision_ref,
        "status": "transitive_dependency_closed",
        "entries": [source_entry.model_dump(mode="json")],
        "routing_changes_added": False,
        "prompt_changes_added": False,
        "runtime_model_calls_added": False,
        "authority_added": False,
    }
    projection = SourceProjection(
        **projection_payload,
        projection_digest_ref=canonical_digest(projection_payload),
    )
    closure_entry = SourceDependencyEntry(
        path_ref=SOURCE_PATH,
        content_digest_ref=source_entry.content_digest_ref,
        dependency_path_refs=(),
    )
    closure_payload = {
        "schema_version": "uaa-taw00-source-dependency-closure.v1",
        "source_revision_ref": lock.git_revision_ref,
        "source_projection_digest_ref": projection.projection_digest_ref,
        "root_path_refs": [SOURCE_PATH],
        "entries": [closure_entry.model_dump(mode="json")],
    }
    closure = SourceDependencyClosure(
        **closure_payload,
        closure_digest_ref=canonical_digest(closure_payload),
    )
    pair = pairs.entries[0]
    randomization_payload = {
        "schema_version": "uaa-taw00-randomization-receipt.v1",
        "pair_ref": pair.pair_ref,
        "cycle_ref": CYCLE,
        "candidate_manifest_digest_ref": lock.manifest_digest_ref,
        "baseline_payload_digest_ref": pair.baseline_payload_digest_ref,
        "candidate_payload_digest_ref": pair.candidate_payload_digest_ref,
        "blinded_order": "a_then_b",
        "baseline_label": "a",
        "a_payload_digest_ref": pair.baseline_payload_digest_ref,
        "b_payload_digest_ref": pair.candidate_payload_digest_ref,
        "method_ref": "randomization-method-ref:taw00:balanced-v1",
        "raw_content_persisted": False,
    }
    randomization_receipt = RandomizationReceipt(
        **randomization_payload,
        receipt_digest_ref=canonical_digest(randomization_payload),
    )
    randomization_bundle_payload = {
        "schema_version": "uaa-taw00-randomization-bundle.v1",
        "pair_manifest_digest_ref": pairs.manifest_digest_ref,
        "candidate_manifest_digest_ref": lock.manifest_digest_ref,
        "receipts": [randomization_receipt.model_dump(mode="json")],
    }
    randomization = RandomizationBundle(
        **randomization_bundle_payload,
        bundle_digest_ref=canonical_digest(randomization_bundle_payload),
    )
    score_payload = {
        "schema_version": "uaa-taw00-blind-score.v1",
        "pair_ref": PAIR,
        "cycle_ref": CYCLE,
        "language_ref": LANGUAGE,
        "configuration_ref": CONFIGURATION,
        "evaluator_ref": "evaluator-ref:taw00:test",
        "language_qualification_ref": "qualification-ref:taw00:test",
        "blinded_order": "a_then_b",
        "baseline_label": "a",
        "a_payload_digest_ref": pair.baseline_payload_digest_ref,
        "b_payload_digest_ref": pair.candidate_payload_digest_ref,
        "randomization_receipt_digest_ref": randomization_receipt.receipt_digest_ref,
        "a_dimension_scores": {dimension: 3 for dimension in TAW00_DIMENSIONS},
        "b_dimension_scores": {dimension: 3 for dimension in TAW00_DIMENSIONS},
        "raw_content_persisted": False,
    }
    score = BlindScore(
        **score_payload,
        score_receipt_digest_ref=canonical_digest(score_payload),
    )
    scores = BlindScoreBundle(
        pair_manifest_digest_ref=pairs.manifest_digest_ref,
        scores=(score,),
    )
    adjudications = AdjudicationBundle(
        pair_manifest_digest_ref=pairs.manifest_digest_ref,
        adjudications=(),
    )
    artifact_models = {
        "artifact-ref:taw00:adjudications": adjudications,
        "artifact-ref:taw00:candidate-lock": lock,
        "artifact-ref:taw00:computed-power": computed_power,
        "artifact-ref:taw00:familywise-bounds": familywise,
        "artifact-ref:taw00:holdout-commitment": commitment,
        "artifact-ref:taw00:holdout-opening": opening,
        "artifact-ref:taw00:legacy-power": legacy_power,
        "artifact-ref:taw00:matrix-census": matrix,
        "artifact-ref:taw00:observation-census": observations,
        "artifact-ref:taw00:pair-manifest": pairs,
        "artifact-ref:taw00:protocol": protocol,
        "artifact-ref:taw00:randomization": randomization,
        "artifact-ref:taw00:scores": scores,
        "artifact-ref:taw00:source-closure": closure,
        "artifact-ref:taw00:source-projection": projection,
    }
    artifact_payloads = {
        ref: (
            "schema-ref:taw00:" + ref.removeprefix("artifact-ref:taw00:"),
            model.model_dump(mode="json"),
        )
        for ref, model in artifact_models.items()
    }
    artifact_census = build_artifact_census(
        cycle_ref=CYCLE,
        artifacts=artifact_payloads,
    )
    metrics = derive_baseline_metrics(
        protocol=protocol,
        observations=observations,
        familywise_bounds=familywise,
    )
    baseline_payload = {
        "schema_version": "uaa-taw00-baseline-receipt.v1",
        "baseline_ref": "baseline-ref:taw00:test",
        "cycle_ref": CYCLE,
        "evaluator_revision_ref": lock.git_revision_ref,
        "evaluator_environment_digest_ref": DIGEST_1,
        "catalog_digest_ref": "sha256:" + "2" * 64,
        "model_artifact_digest_ref": "sha256:" + "3" * 64,
        "tokenizer_digest_ref": "sha256:" + "4" * 64,
        "inference_config_digest_ref": "sha256:" + "5" * 64,
        "prompt_format_digest_ref": "sha256:" + "6" * 64,
        "ttft_ordering_receipt_digest_ref": "sha256:" + "7" * 64,
        "cache_state_receipt_digest_ref": "sha256:" + "8" * 64,
        "baseline_payload_digest_ref": pair.baseline_payload_digest_ref,
        "candidate_payload_digest_ref": pair.candidate_payload_digest_ref,
        "metrics": [metric.model_dump(mode="json") for metric in metrics],
        "failure_refs": [],
        "artifact_census_digest_ref": artifact_census.census_digest_ref,
        "source_projection_digest_ref": projection.projection_digest_ref,
        "pair_manifest_digest_ref": pairs.manifest_digest_ref,
        "accepted_current": True,
        "acceptance_receipt_ref": "acceptance-ref:taw00:test",
        "complete": True,
        "raw_content_persisted": False,
        "runtime_authority_added": False,
    }
    baseline = BaselineReceipt(
        **baseline_payload,
        receipt_digest_ref=canonical_digest(baseline_payload),
    )
    legacy_payload = {
        "schema_version": "uaa-taw00-acceptance-evidence-binding.v1",
        "cycle_ref": CYCLE,
        "protocol_digest_ref": protocol_configuration_digest(protocol),
        "power_analysis_receipt_digest_ref": legacy_power.receipt_digest_ref,
        "source_projection_digest_ref": projection.projection_digest_ref,
        "source_closure_digest_ref": closure.closure_digest_ref,
        "candidate_ref": lock.candidate_ref,
        "candidate_revision_ref": lock.git_revision_ref,
        "candidate_manifest_digest_ref": lock.manifest_digest_ref,
        "pair_manifest_digest_ref": pairs.manifest_digest_ref,
        "baseline_receipt_digest_ref": baseline.receipt_digest_ref,
        "randomization_bundle_digest_ref": randomization.bundle_digest_ref,
        "score_bundle_digest_ref": canonical_digest(scores.model_dump(mode="json")),
        "adjudication_bundle_digest_ref": canonical_digest(
            adjudications.model_dump(mode="json")
        ),
        "raw_content_persisted": False,
    }
    legacy_binding = AcceptanceEvidenceBinding(
        **legacy_payload,
        binding_digest_ref=canonical_digest(legacy_payload),
    )
    complete_payload = {
        "schema_version": "uaa-taw00-complete-acceptance-binding.v1",
        "cycle_ref": CYCLE,
        "legacy_binding_digest_ref": legacy_binding.binding_digest_ref,
        "holdout_commitment_digest_ref": commitment.commitment_digest,
        "holdout_opening_receipt_digest_ref": opening.receipt_digest_ref,
        "matrix_census_digest_ref": matrix.census_digest_ref,
        "computed_power_receipt_digest_ref": computed_power.receipt_digest_ref,
        "observation_census_digest_ref": observations.census_digest_ref,
        "familywise_bound_receipt_digest_ref": familywise.receipt_digest_ref,
        "artifact_census_digest_ref": artifact_census.census_digest_ref,
        "baseline_receipt_digest_ref": baseline.receipt_digest_ref,
        "raw_content_persisted": False,
    }
    complete_binding = CompleteAcceptanceEvidenceBinding(
        **complete_payload,
        binding_digest_ref=canonical_digest(complete_payload),
    )

    assert (
        validate_complete_acceptance_evidence(
            complete_binding,
            legacy_binding=legacy_binding,
            protocol=protocol,
            legacy_power_analysis=legacy_power,
            source_projection=projection,
            source_closure=closure,
            candidate_lock=lock,
            pair_manifest=pairs,
            baseline_receipt=baseline,
            randomization_bundle=randomization,
            score_bundle=scores,
            adjudication_bundle=adjudications,
            commitment=commitment,
            opening=opening,
            matrix=matrix,
            computed_power=computed_power,
            observations=observations,
            familywise_bounds=familywise,
            artifact_census=artifact_census,
            artifact_payloads=artifact_payloads,
        )
        == ()
    )

    schema = json.loads(taw00_verifier.SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    for model in (
        opening,
        matrix,
        computed_power,
        observations,
        familywise,
        artifact_census,
        complete_binding,
    ):
        assert not list(validator.iter_errors(model.model_dump(mode="json")))

    cli_payloads = {
        "binding": legacy_binding,
        "complete-binding": complete_binding,
        "protocol": protocol,
        "power-analysis": legacy_power,
        "source-projection": projection,
        "source-closure": closure,
        "candidate-lock": lock,
        "pair-manifest": pairs,
        "baseline-receipt": baseline,
        "randomization": randomization,
        "scores": scores,
        "adjudications": adjudications,
        "commitment": commitment,
        "holdout-opening": opening,
        "matrix-census": matrix,
        "computed-power": computed_power,
        "observations": observations,
        "familywise-bounds": familywise,
        "artifact-census": artifact_census,
    }
    argv = ["run_tool_aware_baseline.py", "verify-complete-evidence"]
    for option, model in cli_payloads.items():
        path = tmp_path / f"{option}.json"
        path.write_text(model.model_dump_json(), encoding="utf-8")
        argv.extend((f"--{option}", str(path)))
    monkeypatch.setattr(baseline_cli.sys, "argv", argv)
    assert baseline_cli.main() == 2
    output = capsys.readouterr().out
    assert "complete_contract_consistency_only_external_acceptance_blocked" in output
    assert '"failure_refs":[]' in output
