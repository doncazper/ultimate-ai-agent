from __future__ import annotations

import copy
import hashlib
import json

import pytest
from pydantic import ValidationError

from scripts import verify_tool_aware_cognition_taw00 as verifier
from scripts import run_tool_aware_baseline as baseline_cli
from ultimate_ai_agent.core.evals.tool_aware_baseline import (
    AcceptanceEvidenceBinding,
    BaselineMetric,
    BaselineReceipt,
    AdjudicationBundle,
    BlindAdjudication,
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
    TAW00_ACCEPTANCE_SPECS,
    TAW00_DIMENSIONS,
    TAW00_MANDATORY_CANDIDATE_PATH_REFS,
    TAW00_REQUIRED_METRICS,
    TAW00FounderDogfoodProfile,
    TAW00Protocol,
    derive_local_python_dependencies,
    durable_payload_has_forbidden_fields,
    founder_dogfood_readiness,
    protocol_configuration_digest,
    protocol_readiness,
    validate_acceptance_evidence_binding,
    validate_baseline_receipt,
    validate_blind_score_set,
    validate_power_analysis_receipt,
    validate_randomization_bundle,
    verify_candidate_lock,
    verify_source_dependency_closure,
)
from ultimate_ai_agent.core.evals.tool_aware_corpus import (
    DevelopmentCaseSpec,
    DevelopmentCorpusManifest,
    DevelopmentManifestBuildSpec,
    HoldoutCommitment,
    build_development_corpus_manifest,
    build_holdout_commitment,
    canonical_digest,
    generate_synthetic_case_payload,
    reconstruct_development_case_payload,
    verify_holdout_commitment,
)
from ultimate_ai_agent.core.evals.tool_aware_statistics import (
    TAW00_MAX_BINOMIAL_DENOMINATOR,
    binomial_one_sided_upper_bound,
    clustered_bootstrap_mean_interval,
    holm_adjusted_alpha,
    krippendorff_alpha_ordinal,
    paired_bootstrap_mean_interval,
    paired_bootstrap_one_sided_bound,
    paired_bootstrap_p95_difference_upper_bound,
)


def test_binomial_verification_work_is_bounded() -> None:
    assert binomial_one_sided_upper_bound(0, TAW00_MAX_BINOMIAL_DENOMINATOR) < 1
    with pytest.raises(ValueError, match="bounded verification limit"):
        binomial_one_sided_upper_bound(0, TAW00_MAX_BINOMIAL_DENOMINATOR + 1)
    with pytest.raises(ValidationError):
        BaselineMetric(
            metric_ref="metric-ref:taw00:test",
            stratum_ref="stratum-ref:taw00:test",
            denominator=TAW00_MAX_BINOMIAL_DENOMINATOR + 1,
            event_count=0,
            point_estimate=0,
            lower_bound=0,
            upper_bound=0.1,
            estimator_ref="estimator-ref:taw00:clopper-pearson",
            estimand_ref="estimand-ref:taw00:binomial-one-sided-upper",
            evidence_digest_ref="sha256:" + "1" * 64,
        )


def _case_spec(index: int = 1) -> DevelopmentCaseSpec:
    return DevelopmentCaseSpec(
        case_ref=f"case-ref:taw00:development-{index}",
        category_ref="category-ref:taw00:ordinary-chat",
        rubric_ref="rubric-ref:taw00:ordinary-chat-quality-v1",
        parameter_refs=("parameter-ref:taw00:neutral-tone",),
        variant_index=index,
    )


def _pair_manifest(*pair_numbers: int) -> PairManifest:
    entries = tuple(
        PairManifestEntry(
            pair_ref=f"pair-ref:taw00:{pair}",
            case_ref=f"case-ref:taw00:{pair}",
            language_ref="language-ref:test-language",
            configuration_ref="configuration-ref:taw00:test",
            baseline_payload_digest_ref="sha256:" + f"{pair:064x}"[-64:],
            candidate_payload_digest_ref="sha256:" + f"{pair + 100:064x}"[-64:],
            randomization_receipt_digest_ref="sha256:" + f"{pair + 200:064x}"[-64:],
        )
        for pair in pair_numbers
    )
    payload = {
        "schema_version": "uaa-taw00-pair-manifest.v1",
        "cycle_ref": "cycle-ref:taw00:test",
        "corpus_digest_ref": "sha256:" + "9" * 64,
        "entries": [item.model_dump(mode="json") for item in entries],
    }
    return PairManifest(**payload, manifest_digest_ref=canonical_digest(payload))


def _bound_pair_manifest(
    *pair_numbers: int, candidate_lock: CandidateLock | None = None
) -> PairManifest:
    entries = []
    for pair in pair_numbers:
        baseline_digest = "sha256:" + f"{pair:064x}"[-64:]
        candidate_digest = "sha256:" + f"{pair + 100:064x}"[-64:]
        randomization_digest = "sha256:" + f"{pair + 200:064x}"[-64:]
        if candidate_lock is not None:
            baseline_label = "a" if pair % 2 else "b"
            randomization_digest = canonical_digest(
                {
                    "schema_version": "uaa-taw00-randomization-receipt.v1",
                    "pair_ref": f"pair-ref:taw00:{pair}",
                    "cycle_ref": "cycle-ref:taw00:test",
                    "candidate_manifest_digest_ref": candidate_lock.manifest_digest_ref,
                    "baseline_payload_digest_ref": baseline_digest,
                    "candidate_payload_digest_ref": candidate_digest,
                    "blinded_order": "a_then_b" if pair % 2 else "b_then_a",
                    "baseline_label": baseline_label,
                    "a_payload_digest_ref": (
                        baseline_digest if baseline_label == "a" else candidate_digest
                    ),
                    "b_payload_digest_ref": (
                        candidate_digest if baseline_label == "a" else baseline_digest
                    ),
                    "method_ref": "randomization-method-ref:taw00:balanced-v1",
                    "raw_content_persisted": False,
                }
            )
        entries.append(
            PairManifestEntry(
                pair_ref=f"pair-ref:taw00:{pair}",
                case_ref=f"case-ref:taw00:{pair}",
                language_ref="language-ref:test-language",
                configuration_ref="configuration-ref:taw00:test",
                stratum_ref="stratum-ref:taw00:test",
                baseline_payload_digest_ref=baseline_digest,
                candidate_payload_digest_ref=candidate_digest,
                randomization_receipt_digest_ref=randomization_digest,
            )
        )
    entries_tuple = tuple(entries)
    payload = {
        "schema_version": "uaa-taw00-pair-manifest.v1",
        "cycle_ref": "cycle-ref:taw00:test",
        "corpus_digest_ref": "sha256:" + "9" * 64,
        "candidate_ref": (
            candidate_lock.candidate_ref
            if candidate_lock is not None
            else "candidate-ref:taw00:test"
        ),
        "candidate_revision_ref": (
            candidate_lock.git_revision_ref
            if candidate_lock is not None
            else "git-sha:" + "a" * 40
        ),
        "candidate_manifest_digest_ref": (
            candidate_lock.manifest_digest_ref
            if candidate_lock is not None
            else "sha256:" + "8" * 64
        ),
        "entries": [item.model_dump(mode="json") for item in entries_tuple],
    }
    return PairManifest(**payload, manifest_digest_ref=canonical_digest(payload))


def _score(pair: int, evaluator: int, value: int) -> BlindScore:
    manifest_entry = _pair_manifest(pair).entries[0]
    baseline_label = "a" if evaluator % 2 else "b"
    baseline_digest = manifest_entry.baseline_payload_digest_ref
    candidate_digest = manifest_entry.candidate_payload_digest_ref
    payload = {
        "pair_ref": f"pair-ref:taw00:{pair}",
        "cycle_ref": "cycle-ref:taw00:test",
        "language_ref": "language-ref:test-language",
        "configuration_ref": "configuration-ref:taw00:test",
        "evaluator_ref": f"evaluator-ref:taw00:{evaluator}",
        "language_qualification_ref": f"qualification-ref:taw00:{evaluator}",
        "blinded_order": "a_then_b" if evaluator % 2 else "b_then_a",
        "baseline_label": baseline_label,
        "a_payload_digest_ref": baseline_digest
        if baseline_label == "a"
        else candidate_digest,
        "b_payload_digest_ref": candidate_digest
        if baseline_label == "a"
        else baseline_digest,
        "randomization_receipt_digest_ref": manifest_entry.randomization_receipt_digest_ref,
        "a_dimension_scores": {dimension: value for dimension in TAW00_DIMENSIONS},
        "b_dimension_scores": {dimension: value for dimension in TAW00_DIMENSIONS},
    }
    return BlindScore(
        **payload,
        score_receipt_digest_ref=canonical_digest(
            {
                "schema_version": "uaa-taw00-blind-score.v1",
                **payload,
                "raw_content_persisted": False,
            }
        ),
    )


def _bound_score(
    pair: int,
    evaluator: int,
    value: int,
    *,
    pair_manifest: PairManifest | None = None,
) -> BlindScore:
    manifest_entry = next(
        entry
        for entry in (pair_manifest or _bound_pair_manifest(pair)).entries
        if entry.pair_ref == f"pair-ref:taw00:{pair}"
    )
    baseline_label = "a" if pair % 2 else "b"
    baseline_digest = manifest_entry.baseline_payload_digest_ref
    candidate_digest = manifest_entry.candidate_payload_digest_ref
    payload = {
        "pair_ref": f"pair-ref:taw00:{pair}",
        "cycle_ref": "cycle-ref:taw00:test",
        "language_ref": "language-ref:test-language",
        "configuration_ref": "configuration-ref:taw00:test",
        "evaluator_ref": f"evaluator-ref:taw00:{evaluator}",
        "language_qualification_ref": f"qualification-ref:taw00:{evaluator}",
        "blinded_order": "a_then_b" if pair % 2 else "b_then_a",
        "baseline_label": baseline_label,
        "a_payload_digest_ref": baseline_digest
        if baseline_label == "a"
        else candidate_digest,
        "b_payload_digest_ref": candidate_digest
        if baseline_label == "a"
        else baseline_digest,
        "randomization_receipt_digest_ref": manifest_entry.randomization_receipt_digest_ref,
        "a_dimension_scores": {dimension: value for dimension in TAW00_DIMENSIONS},
        "b_dimension_scores": {dimension: value for dimension in TAW00_DIMENSIONS},
    }
    return BlindScore(
        **payload,
        score_receipt_digest_ref=canonical_digest(
            {
                "schema_version": "uaa-taw00-blind-score.v1",
                **payload,
                "raw_content_persisted": False,
            }
        ),
    )


def _candidate_lock() -> CandidateLock:
    entry = CandidateManifestEntry(
        path_ref="repo-path-ref:src/ultimate_ai_agent/a.py",
        content_digest_ref="sha256:" + "7" * 64,
    )
    digest_payload = {
        "candidate_ref": "candidate-ref:taw00:test",
        "git_revision_ref": "git-sha:" + "a" * 40,
        "entries": [entry.model_dump(mode="json")],
        "evidence_only_delta_path_refs": (),
    }
    return CandidateLock(
        candidate_ref=digest_payload["candidate_ref"],
        git_revision_ref=digest_payload["git_revision_ref"],
        entries=(entry,),
        manifest_digest_ref=canonical_digest(digest_payload),
        evidence_only_delta_path_refs=(),
    )


def _randomization_bundle(
    pair_manifest: PairManifest, candidate_lock: CandidateLock
) -> RandomizationBundle:
    receipts = []
    for entry in pair_manifest.entries:
        pair_number = int(entry.pair_ref.rsplit(":", 1)[1])
        baseline_label = "a" if pair_number % 2 else "b"
        payload = {
            "schema_version": "uaa-taw00-randomization-receipt.v1",
            "pair_ref": entry.pair_ref,
            "cycle_ref": pair_manifest.cycle_ref,
            "candidate_manifest_digest_ref": candidate_lock.manifest_digest_ref,
            "baseline_payload_digest_ref": entry.baseline_payload_digest_ref,
            "candidate_payload_digest_ref": entry.candidate_payload_digest_ref,
            "blinded_order": "a_then_b" if pair_number % 2 else "b_then_a",
            "baseline_label": baseline_label,
            "a_payload_digest_ref": (
                entry.baseline_payload_digest_ref
                if baseline_label == "a"
                else entry.candidate_payload_digest_ref
            ),
            "b_payload_digest_ref": (
                entry.candidate_payload_digest_ref
                if baseline_label == "a"
                else entry.baseline_payload_digest_ref
            ),
            "method_ref": "randomization-method-ref:taw00:balanced-v1",
            "raw_content_persisted": False,
        }
        receipts.append(
            RandomizationReceipt(
                **payload,
                receipt_digest_ref=canonical_digest(payload),
            )
        )
    bundle_payload = {
        "schema_version": "uaa-taw00-randomization-bundle.v1",
        "pair_manifest_digest_ref": pair_manifest.manifest_digest_ref,
        "candidate_manifest_digest_ref": candidate_lock.manifest_digest_ref,
        "receipts": [receipt.model_dump(mode="json") for receipt in receipts],
    }
    return RandomizationBundle(
        **bundle_payload,
        bundle_digest_ref=canonical_digest(bundle_payload),
    )


def _locked_protocol(pair_manifest: PairManifest) -> TAW00Protocol:
    payload = verifier._load(verifier.PROTOCOL)
    payload.update(
        {
            "status": "locked",
            "cycle_ref": pair_manifest.cycle_ref,
            "supported_language_refs": ["language-ref:test-language"],
            "model_configuration_refs": ["configuration-ref:taw00:test"],
            "hardware_backend_refs": ["hardware-ref:taw00:test"],
            "supported_stratum_refs": ["stratum-ref:taw00:test"],
            "metric_census": [
                MetricRequirement(
                    metric_ref=metric_ref,
                    stratum_ref="stratum-ref:taw00:test",
                    minimum_denominator=len(pair_manifest.entries),
                    estimand_ref=(
                        "estimand-ref:taw00:paired-p95-ttft-one-sided-upper"
                        if metric_ref == "metric-ref:taw00:p95-ttft-difference"
                        else "estimand-ref:taw00:paired-quality-one-sided-lower"
                        if "quality-" in metric_ref
                        else "estimand-ref:taw00:binomial-one-sided-upper"
                    ),
                    estimator_ref="estimator-ref:taw00:paired-bootstrap",
                    acceptance_bound=TAW00_ACCEPTANCE_SPECS[metric_ref][0],
                    absolute_threshold=TAW00_ACCEPTANCE_SPECS[metric_ref][1],
                    relative_to_baseline_fraction=TAW00_ACCEPTANCE_SPECS[metric_ref][2],
                ).model_dump(mode="json")
                for metric_ref in TAW00_REQUIRED_METRICS
            ],
            "power_analysis_receipt_digest_ref": "sha256:" + "1" * 64,
            "expected_pair_manifest_digest_ref": pair_manifest.manifest_digest_ref,
            "acceptance_affecting_path_refs": sorted(
                (
                    *TAW00_MANDATORY_CANDIDATE_PATH_REFS,
                    "repo-path-ref:src/ultimate_ai_agent/a.py",
                )
            ),
            "source_projection_path_refs": ["repo-path-ref:src/ultimate_ai_agent/a.py"],
            "blocked_reason_refs": [],
        }
    )
    return TAW00Protocol.model_validate(payload)


def _power_receipt(protocol: TAW00Protocol) -> PowerAnalysisReceipt:
    cells = tuple(
        PowerAnalysisCell(
            metric_ref=requirement.metric_ref,
            stratum_ref=requirement.stratum_ref,
            minimum_denominator=requirement.minimum_denominator,
            target_effect_size=0.1,
            familywise_alpha=0.05,
            target_power=0.8,
            method_ref="power-method-ref:taw00:pre-registered-v1",
        )
        for requirement in sorted(
            protocol.metric_census,
            key=lambda item: (item.metric_ref, item.stratum_ref),
        )
    )
    payload = {
        "schema_version": "uaa-taw00-power-analysis.v1",
        "cycle_ref": protocol.cycle_ref,
        "protocol_digest_ref": protocol_configuration_digest(protocol),
        "cells": [cell.model_dump(mode="json") for cell in cells],
        "raw_content_persisted": False,
    }
    return PowerAnalysisReceipt(
        **payload,
        receipt_digest_ref=canonical_digest(payload),
    )


def test_taw00_verifier_passes_current_pending_facility() -> None:
    assert verifier.verify() == []


def test_development_corpus_is_deterministic_and_hash_bound() -> None:
    kwargs = {
        "corpus_ref": "corpus-ref:taw00:development-v1",
        "deterministic_seed_ref": "seed-ref:taw00:development-v1",
        "seed_material": b"public-development-seed-material",
        "specs": (_case_spec(),),
    }
    first = build_development_corpus_manifest(**kwargs)
    second = build_development_corpus_manifest(**kwargs)

    assert first == second
    assert generate_synthetic_case_payload(
        kwargs["seed_material"], _case_spec()
    ) == generate_synthetic_case_payload(kwargs["seed_material"], _case_spec())
    assert reconstruct_development_case_payload(
        first, _case_spec().case_ref
    ) == generate_synthetic_case_payload(kwargs["seed_material"], _case_spec())
    payload = first.model_dump(mode="json")
    payload["cases"][0]["generated_content_digest"] = "sha256:" + "0" * 64
    with pytest.raises(ValidationError, match="digest binding drift"):
        DevelopmentCorpusManifest.model_validate(payload)
    with pytest.raises(ValidationError):
        DevelopmentManifestBuildSpec.model_validate(
            {
                "corpus_ref": kwargs["corpus_ref"],
                "deterministic_seed_ref": kwargs["deterministic_seed_ref"],
                "seed_material_hex": kwargs["seed_material"].hex(),
                "cases": [_case_spec().model_dump(mode="json")],
                "ignored_acceptance_override": True,
            }
        )


def test_holdout_commitment_requires_keyed_private_material_and_hides_inputs() -> None:
    private_manifest = (
        '{"schema_version":"uaa-taw00-private-holdout.v1",'
        '"cycle_ref":"cycle-ref:taw00:test",'
        '"corpus_ref":"corpus-ref:taw00:holdout-v1",'
        '"deterministic_seed_ref":"seed-ref:taw00:holdout-v1",'
        f'"seed_material_hex":"{"ab" * 32}",'
        '"cases":[{"case_ref":"case-ref:taw00:holdout-1",'
        '"category_ref":"category-ref:taw00:ordinary-chat",'
        '"rubric_ref":"rubric-ref:taw00:ordinary-chat-quality-v1",'
        '"parameter_refs":["parameter-ref:taw00:neutral-tone"],'
        '"variant_index":1}],"synthetic_only":true}'
    ).encode()
    commitment = build_holdout_commitment(
        cycle_ref="cycle-ref:taw00:test",
        custodian_ref="custodian-ref:taw00:independent",
        creation_order_evidence_ref="evidence-ref:taw00:pre-candidate",
        custodian_attestation_ref="attestation-ref:taw00:independent-custodian",
        secret_key=b"k" * 32,
        private_manifest=private_manifest,
    )

    assert verify_holdout_commitment(
        commitment,
        secret_key=b"k" * 32,
        private_manifest=private_manifest,
    )
    assert not verify_holdout_commitment(
        commitment,
        secret_key=b"x" * 32,
        private_manifest=private_manifest,
    )
    assert set(commitment.model_dump()) == {
        "schema_version",
        "cycle_ref",
        "custodian_ref",
        "generator_ref",
        "generator_version",
        "commitment_envelope_version",
        "commitment_algorithm",
        "commitment_digest",
        "creation_order_evidence_ref",
        "custodian_attestation_ref",
        "private_material_disclosed",
    }
    unsafe = commitment.model_dump(mode="json")
    unsafe["commitment_algorithm"] = "sha256"
    unsafe["seed"] = "enumerable"
    with pytest.raises(ValidationError):
        HoldoutCommitment.model_validate(unsafe)

    relabeled = commitment.model_copy(update={"cycle_ref": "cycle-ref:taw00:other"})
    assert not verify_holdout_commitment(
        relabeled, secret_key=b"k" * 32, private_manifest=private_manifest
    )
    with pytest.raises(ValueError, match="canonical JSON"):
        build_holdout_commitment(
            cycle_ref="cycle-ref:taw00:test",
            custodian_ref="custodian-ref:taw00:independent",
            creation_order_evidence_ref="evidence-ref:taw00:pre-candidate",
            custodian_attestation_ref="attestation-ref:taw00:independent-custodian",
            secret_key=b"k" * 32,
            private_manifest=b"not-json",
        )


def test_statistical_helpers_are_deterministic_and_cluster_aware() -> None:
    assert holm_adjusted_alpha({"b": 0.02, "a": 0.01}) == {
        "a": 0.025,
        "b": 0.05,
    }
    paired = paired_bootstrap_mean_interval(
        [10, 20, 30], [11, 19, 32], resamples=1_000, seed=4
    )
    assert paired == paired_bootstrap_mean_interval(
        [10, 20, 30], [11, 19, 32], resamples=1_000, seed=4
    )
    assert paired_bootstrap_one_sided_bound(
        [10, 20, 30], [11, 19, 32], side="lower", resamples=1_000, seed=4
    ) == paired_bootstrap_one_sided_bound(
        [10, 20, 30], [11, 19, 32], side="lower", resamples=1_000, seed=4
    )
    assert (
        paired_bootstrap_p95_difference_upper_bound(
            [10, 20, 30], [11, 19, 32], resamples=1_000, seed=4
        )[0]
        == 2
    )
    clustered = clustered_bootstrap_mean_interval(
        {"cluster-a": [1, 1], "cluster-b": [3, 3]}, resamples=1_000, seed=4
    )
    assert clustered[0] == 2
    assert krippendorff_alpha_ordinal({"item-a": [1, 1], "item-b": [5, 5]}) == 1


def test_binomial_upper_bound_is_exact_and_numerator_bound() -> None:
    upper = binomial_one_sided_upper_bound(0, 300)
    assert upper < 0.01
    assert binomial_one_sided_upper_bound(1, 100) > upper
    with pytest.raises(ValueError, match="event count"):
        binomial_one_sided_upper_bound(2, 1)
    with pytest.raises(ValidationError, match="point estimate disagrees"):
        BaselineMetric(
            metric_ref="metric-ref:taw00:unsafe-authority",
            stratum_ref="stratum-ref:taw00:test",
            denominator=300,
            event_count=0,
            point_estimate=upper / 2,
            lower_bound=0,
            upper_bound=upper,
            estimator_ref="estimator-ref:taw00:paired-bootstrap",
            estimand_ref="estimand-ref:taw00:binomial-one-sided-upper",
            evidence_digest_ref="sha256:" + "3" * 64,
        )


def test_power_receipt_and_randomization_bind_exact_candidate_pair_census() -> None:
    candidate_lock = _candidate_lock()
    pair_manifest = _bound_pair_manifest(1, 2, candidate_lock=candidate_lock)
    protocol = _locked_protocol(pair_manifest)
    power_receipt = _power_receipt(protocol)
    assert set(
        validate_power_analysis_receipt(
            power_receipt, protocol, pair_manifest=pair_manifest
        )
    ) == {
        "failure-ref:taw00:matrix-census-contract-incomplete",
        "failure-ref:taw00:power-computation-contract-incomplete",
    }
    assert "failure-ref:taw00:pair-census-below-power-gate" in (
        validate_power_analysis_receipt(
            power_receipt,
            protocol,
            pair_manifest=_bound_pair_manifest(1, candidate_lock=candidate_lock),
        )
    )

    randomization = _randomization_bundle(pair_manifest, candidate_lock)
    assert (
        validate_randomization_bundle(
            randomization,
            pair_manifest=pair_manifest,
            candidate_lock=candidate_lock,
        )
        == ()
    )
    other_lock = candidate_lock.model_copy(
        update={"candidate_ref": "candidate-ref:taw00:other"}
    )
    assert "failure-ref:taw00:pair-manifest-candidate-lock-drift" in (
        validate_randomization_bundle(
            randomization,
            pair_manifest=pair_manifest,
            candidate_lock=other_lock,
        )
    )
    with pytest.raises(ValidationError, match="not balanced"):
        _randomization_bundle(
            _bound_pair_manifest(1, 3, candidate_lock=candidate_lock),
            candidate_lock,
        )


def test_source_dependency_closure_detects_missing_transitive_import() -> None:
    root_ref = "repo-path-ref:src/ultimate_ai_agent/a.py"
    dependency_ref = "repo-path-ref:src/ultimate_ai_agent/b.py"
    content_by_path = {
        root_ref: b"from ultimate_ai_agent import b\n",
        dependency_ref: b"VALUE = 1\n",
    }
    projection_payload = {
        "schema_version": "uaa-taw00-source-projection.v1",
        "projection_ref": "projection-ref:taw00:test",
        "source_revision_ref": "git-sha:" + "a" * 40,
        "status": "transitive_dependency_closed",
        "entries": [
            CandidateManifestEntry(
                path_ref=root_ref,
                content_digest_ref=(
                    "sha256:" + hashlib.sha256(content_by_path[root_ref]).hexdigest()
                ),
            ).model_dump(mode="json")
        ],
        "routing_changes_added": False,
        "prompt_changes_added": False,
        "runtime_model_calls_added": False,
        "authority_added": False,
    }
    projection = SourceProjection(
        **projection_payload,
        projection_digest_ref=canonical_digest(projection_payload),
    )
    entries = (
        SourceDependencyEntry(
            path_ref=root_ref,
            content_digest_ref=(
                "sha256:" + hashlib.sha256(content_by_path[root_ref]).hexdigest()
            ),
            dependency_path_refs=(dependency_ref,),
        ),
        SourceDependencyEntry(
            path_ref=dependency_ref,
            content_digest_ref=(
                "sha256:" + hashlib.sha256(content_by_path[dependency_ref]).hexdigest()
            ),
        ),
    )
    closure_payload = {
        "schema_version": "uaa-taw00-source-dependency-closure.v1",
        "source_revision_ref": projection.source_revision_ref,
        "source_projection_digest_ref": projection.projection_digest_ref,
        "root_path_refs": [root_ref],
        "entries": [entry.model_dump(mode="json") for entry in entries],
    }
    closure = SourceDependencyClosure(
        **closure_payload,
        closure_digest_ref=canonical_digest(closure_payload),
    )
    assert (
        verify_source_dependency_closure(
            closure,
            source_projection=projection,
            content_by_path_ref=content_by_path,
            available_path_refs=set(content_by_path),
        )
        == ()
    )
    assert "failure-ref:taw00:source-closure-content-census-drift" in (
        verify_source_dependency_closure(
            closure,
            source_projection=projection,
            content_by_path_ref={root_ref: content_by_path[root_ref]},
            available_path_refs=set(content_by_path),
        )
    )
    with pytest.raises(ValueError, match="unresolved dynamic import"):
        derive_local_python_dependencies(
            root_ref,
            b"import importlib\nimportlib.import_module(module_name)\n",
            available_path_refs=set(content_by_path),
        )
    script_dependency_ref = (
        "repo-path-ref:src/ultimate_ai_agent/core/approvals/authority.py"
    )
    assert derive_local_python_dependencies(
        "repo-path-ref:scripts/example.py",
        b"from ultimate_ai_agent.core.approvals import authority\n",
        available_path_refs={script_dependency_ref},
    ) == (script_dependency_ref,)


def test_acceptance_binding_stales_when_any_candidate_result_link_changes() -> None:
    candidate_lock = _candidate_lock()
    pair_manifest = _bound_pair_manifest(1, candidate_lock=candidate_lock)
    protocol = _locked_protocol(pair_manifest)
    power = _power_receipt(protocol)
    projection_payload = {
        "schema_version": "uaa-taw00-source-projection.v1",
        "projection_ref": "projection-ref:taw00:test",
        "source_revision_ref": candidate_lock.git_revision_ref,
        "status": "transitive_dependency_closed",
        "entries": [entry.model_dump(mode="json") for entry in candidate_lock.entries],
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
        path_ref=candidate_lock.entries[0].path_ref,
        content_digest_ref=candidate_lock.entries[0].content_digest_ref,
    )
    closure_payload = {
        "schema_version": "uaa-taw00-source-dependency-closure.v1",
        "source_revision_ref": candidate_lock.git_revision_ref,
        "source_projection_digest_ref": projection.projection_digest_ref,
        "root_path_refs": [closure_entry.path_ref],
        "entries": [closure_entry.model_dump(mode="json")],
    }
    closure = SourceDependencyClosure(
        **closure_payload,
        closure_digest_ref=canonical_digest(closure_payload),
    )
    metric = BaselineMetric(
        metric_ref="metric-ref:taw00:unsafe-authority",
        stratum_ref="stratum-ref:taw00:test",
        denominator=300,
        event_count=0,
        point_estimate=0,
        lower_bound=0,
        upper_bound=binomial_one_sided_upper_bound(0, 300),
        estimator_ref="estimator-ref:taw00:paired-bootstrap",
        estimand_ref="estimand-ref:taw00:binomial-one-sided-upper",
        evidence_digest_ref="sha256:" + "3" * 64,
    )
    receipt_payload = {
        "schema_version": "uaa-taw00-baseline-receipt.v1",
        "baseline_ref": "baseline-ref:taw00:test",
        "cycle_ref": protocol.cycle_ref,
        "evaluator_revision_ref": candidate_lock.git_revision_ref,
        "evaluator_environment_digest_ref": "sha256:" + "4" * 64,
        "catalog_digest_ref": "sha256:" + "5" * 64,
        "model_artifact_digest_ref": "sha256:" + "6" * 64,
        "tokenizer_digest_ref": "sha256:" + "7" * 64,
        "inference_config_digest_ref": "sha256:" + "8" * 64,
        "prompt_format_digest_ref": "sha256:" + "9" * 64,
        "ttft_ordering_receipt_digest_ref": "sha256:" + "a" * 64,
        "cache_state_receipt_digest_ref": "sha256:" + "b" * 64,
        "baseline_payload_digest_ref": "sha256:" + "c" * 64,
        "candidate_payload_digest_ref": "sha256:" + "d" * 64,
        "metrics": [metric.model_dump(mode="json")],
        "failure_refs": [],
        "artifact_census_digest_ref": "sha256:" + "e" * 64,
        "source_projection_digest_ref": projection.projection_digest_ref,
        "pair_manifest_digest_ref": pair_manifest.manifest_digest_ref,
        "accepted_current": True,
        "acceptance_receipt_ref": "acceptance-ref:taw00:test",
        "complete": True,
        "raw_content_persisted": False,
        "runtime_authority_added": False,
    }
    baseline = BaselineReceipt(
        **receipt_payload,
        receipt_digest_ref=canonical_digest(receipt_payload),
    )
    randomization = _randomization_bundle(pair_manifest, candidate_lock)
    scores = BlindScoreBundle(
        pair_manifest_digest_ref=pair_manifest.manifest_digest_ref,
        scores=(
            _bound_score(1, 1, 2, pair_manifest=pair_manifest),
            _bound_score(1, 2, 2, pair_manifest=pair_manifest),
        ),
    )
    adjudications = AdjudicationBundle(
        pair_manifest_digest_ref=pair_manifest.manifest_digest_ref,
        adjudications=(),
    )
    binding_payload = {
        "schema_version": "uaa-taw00-acceptance-evidence-binding.v1",
        "cycle_ref": protocol.cycle_ref,
        "protocol_digest_ref": protocol_configuration_digest(protocol),
        "power_analysis_receipt_digest_ref": power.receipt_digest_ref,
        "source_projection_digest_ref": projection.projection_digest_ref,
        "source_closure_digest_ref": closure.closure_digest_ref,
        "candidate_ref": candidate_lock.candidate_ref,
        "candidate_revision_ref": candidate_lock.git_revision_ref,
        "candidate_manifest_digest_ref": candidate_lock.manifest_digest_ref,
        "pair_manifest_digest_ref": pair_manifest.manifest_digest_ref,
        "baseline_receipt_digest_ref": baseline.receipt_digest_ref,
        "randomization_bundle_digest_ref": randomization.bundle_digest_ref,
        "score_bundle_digest_ref": canonical_digest(scores.model_dump(mode="json")),
        "adjudication_bundle_digest_ref": canonical_digest(
            adjudications.model_dump(mode="json")
        ),
        "raw_content_persisted": False,
    }
    binding = AcceptanceEvidenceBinding(
        **binding_payload,
        binding_digest_ref=canonical_digest(binding_payload),
    )
    kwargs = {
        "protocol": protocol,
        "power_analysis": power,
        "source_projection": projection,
        "source_closure": closure,
        "candidate_lock": candidate_lock,
        "pair_manifest": pair_manifest,
        "baseline_receipt": baseline,
        "randomization_bundle": randomization,
        "score_bundle": scores,
        "adjudication_bundle": adjudications,
    }
    binding_failures = validate_acceptance_evidence_binding(binding, **kwargs)
    assert "failure-ref:taw00:artifact-census-contract-incomplete" in binding_failures
    assert "failure-ref:taw00:holdout-opening-binding-incomplete" in binding_failures
    mismatched_closure = closure.model_copy(
        update={"source_revision_ref": "git-sha:" + "b" * 40}
    )
    assert "failure-ref:taw00:candidate-source-closure-revision-drift" in (
        validate_acceptance_evidence_binding(
            binding, **{**kwargs, "source_closure": mismatched_closure}
        )
    )
    stale = binding.model_copy(update={"candidate_revision_ref": "git-sha:" + "b" * 40})
    assert validate_acceptance_evidence_binding(stale, **kwargs)


def test_blind_scoring_requires_two_evaluators_and_independent_adjudication() -> None:
    valid = validate_blind_score_set(
        (_score(1, 1, 2), _score(1, 2, 2), _score(2, 1, 4), _score(2, 2, 4)),
        (),
        pair_manifest=_pair_manifest(1, 2),
    )
    assert valid.valid is True
    assert set(valid.agreement_by_language_dimension) == {
        "language-ref:test-language|helpfulness",
        "language-ref:test-language|instruction_following",
        "language-ref:test-language|tone",
        "language-ref:test-language|response_relevance",
    }

    disagreement = validate_blind_score_set(
        (_score(1, 1, 2), _score(1, 2, 3)),
        (),
        pair_manifest=_pair_manifest(1),
    )
    assert disagreement.valid is False
    assert "failure-ref:taw00:unresolved-disagreement" in disagreement.failure_refs

    adjudication_payload = {
        "pair_ref": "pair-ref:taw00:1",
        "language_ref": "language-ref:test-language",
        "configuration_ref": "configuration-ref:taw00:test",
        "cycle_ref": "cycle-ref:taw00:test",
        "dimension_ref": "helpfulness",
        "adjudicator_ref": "evaluator-ref:taw00:1",
        "language_qualification_ref": "qualification-ref:taw00:adjudicator",
        "blinded_order": "a_then_b",
        "baseline_label": "a",
        "a_payload_digest_ref": _pair_manifest(1)
        .entries[0]
        .baseline_payload_digest_ref,
        "b_payload_digest_ref": _pair_manifest(1)
        .entries[0]
        .candidate_payload_digest_ref,
        "randomization_receipt_digest_ref": _pair_manifest(1)
        .entries[0]
        .randomization_receipt_digest_ref,
        "final_a_score": 2,
        "final_b_score": 3,
    }
    adjudication = BlindAdjudication(
        **adjudication_payload,
        receipt_digest_ref=canonical_digest(
            {
                "schema_version": "uaa-taw00-adjudication.v1",
                **adjudication_payload,
            }
        ),
    )
    self_adjudicated = validate_blind_score_set(
        (_score(1, 1, 2), _score(1, 2, 3)),
        (adjudication,),
        pair_manifest=_pair_manifest(1),
    )
    assert "failure-ref:taw00:adjudicator-not-independent" in (
        self_adjudicated.failure_refs
    )
    truncated = validate_blind_score_set(
        (_score(1, 1, 2), _score(1, 2, 2)),
        (),
        pair_manifest=_pair_manifest(1, 2),
    )
    assert "failure-ref:taw00:incomplete-pair-census" in truncated.failure_refs


def test_bound_blind_scoring_requires_randomization_and_pair_binding() -> None:
    candidate_lock = _candidate_lock()
    full_manifest = _bound_pair_manifest(1, 2, candidate_lock=candidate_lock)
    full_randomization = _randomization_bundle(full_manifest, candidate_lock)
    pair_one_manifest = _bound_pair_manifest(1, candidate_lock=candidate_lock)
    pair_one_randomization = _randomization_bundle(pair_one_manifest, candidate_lock)
    valid = validate_blind_score_set(
        (
            _bound_score(1, 1, 2, pair_manifest=full_manifest),
            _bound_score(1, 2, 2, pair_manifest=full_manifest),
            _bound_score(2, 1, 4, pair_manifest=full_manifest),
            _bound_score(2, 2, 4, pair_manifest=full_manifest),
        ),
        (),
        pair_manifest=full_manifest,
        randomization_bundle=full_randomization,
    )
    assert valid.valid is True
    assert set(valid.agreement_by_language_dimension) == {
        "language-ref:test-language|helpfulness",
        "language-ref:test-language|instruction_following",
        "language-ref:test-language|tone",
        "language-ref:test-language|response_relevance",
    }
    tampered_order = _bound_score(1, 1, 2, pair_manifest=full_manifest).model_copy(
        update={"blinded_order": "b_then_a"}
    )
    order_drift = validate_blind_score_set(
        (
            tampered_order,
            _bound_score(1, 2, 2, pair_manifest=full_manifest),
            _bound_score(2, 1, 4, pair_manifest=full_manifest),
            _bound_score(2, 2, 4, pair_manifest=full_manifest),
        ),
        (),
        pair_manifest=full_manifest,
        randomization_bundle=full_randomization,
    )
    assert "failure-ref:taw00:score-pair-binding-drift" in order_drift.failure_refs
    wrong_receipt = full_randomization.receipts[0].model_copy(
        update={"receipt_digest_ref": "sha256:" + "f" * 64}
    )
    wrong_bundle = full_randomization.model_copy(
        update={"receipts": (wrong_receipt, *full_randomization.receipts[1:])}
    )
    receipt_drift = validate_blind_score_set(
        (
            _bound_score(1, 1, 2, pair_manifest=full_manifest),
            _bound_score(1, 2, 2, pair_manifest=full_manifest),
            _bound_score(2, 1, 4, pair_manifest=full_manifest),
            _bound_score(2, 2, 4, pair_manifest=full_manifest),
        ),
        (),
        pair_manifest=full_manifest,
        randomization_bundle=wrong_bundle,
    )
    assert "failure-ref:taw00:score-pair-binding-drift" in receipt_drift.failure_refs

    disagreement = validate_blind_score_set(
        (
            _bound_score(1, 1, 2, pair_manifest=pair_one_manifest),
            _bound_score(1, 2, 3, pair_manifest=pair_one_manifest),
        ),
        (),
        pair_manifest=pair_one_manifest,
        randomization_bundle=pair_one_randomization,
    )
    assert disagreement.valid is False
    assert "failure-ref:taw00:unresolved-disagreement" in disagreement.failure_refs

    adjudication_payload = {
        "pair_ref": "pair-ref:taw00:1",
        "language_ref": "language-ref:test-language",
        "configuration_ref": "configuration-ref:taw00:test",
        "cycle_ref": "cycle-ref:taw00:test",
        "dimension_ref": "helpfulness",
        "adjudicator_ref": "evaluator-ref:taw00:1",
        "language_qualification_ref": "qualification-ref:taw00:adjudicator",
        "blinded_order": "a_then_b",
        "baseline_label": "a",
        "a_payload_digest_ref": pair_one_manifest.entries[
            0
        ].baseline_payload_digest_ref,
        "b_payload_digest_ref": pair_one_manifest.entries[
            0
        ].candidate_payload_digest_ref,
        "randomization_receipt_digest_ref": pair_one_manifest.entries[
            0
        ].randomization_receipt_digest_ref,
        "final_a_score": 2,
        "final_b_score": 3,
    }
    adjudication = BlindAdjudication(
        **adjudication_payload,
        receipt_digest_ref=canonical_digest(
            {
                "schema_version": "uaa-taw00-adjudication.v1",
                **adjudication_payload,
            }
        ),
    )
    self_adjudicated = validate_blind_score_set(
        (
            _bound_score(1, 1, 2, pair_manifest=pair_one_manifest),
            _bound_score(1, 2, 3, pair_manifest=pair_one_manifest),
        ),
        (adjudication,),
        pair_manifest=pair_one_manifest,
        randomization_bundle=pair_one_randomization,
    )
    assert "failure-ref:taw00:adjudicator-not-independent" in (
        self_adjudicated.failure_refs
    )
    truncated = validate_blind_score_set(
        (
            _bound_score(1, 1, 2, pair_manifest=full_manifest),
            _bound_score(1, 2, 2, pair_manifest=full_manifest),
        ),
        (),
        pair_manifest=full_manifest,
        randomization_bundle=full_randomization,
    )
    assert "failure-ref:taw00:incomplete-pair-census" in truncated.failure_refs


def test_candidate_lock_rejects_digest_and_order_drift() -> None:
    entries = (
        CandidateManifestEntry(
            path_ref="repo-path-ref:a.py", content_digest_ref="sha256:" + "1" * 64
        ),
        CandidateManifestEntry(
            path_ref="repo-path-ref:b.py", content_digest_ref="sha256:" + "2" * 64
        ),
    )
    payload = {
        "candidate_ref": "candidate-ref:taw00:test",
        "git_revision_ref": "git-sha:" + "a" * 40,
        "entries": [entry.model_dump(mode="json") for entry in entries],
        "evidence_only_delta_path_refs": ("repo-path-ref:evidence/report.json",),
    }
    lock = CandidateLock(
        manifest_digest_ref=canonical_digest(payload),
        **payload,
    )
    unsafe = lock.model_dump(mode="json")
    unsafe["entries"].reverse()
    with pytest.raises(ValidationError):
        CandidateLock.model_validate(unsafe)
    failures = verify_candidate_lock(
        lock,
        expected_path_refs=("repo-path-ref:a.py", "repo-path-ref:b.py"),
        revision_content_by_path_ref={
            "repo-path-ref:a.py": b"not-the-declared-bytes",
            "repo-path-ref:b.py": b"also-not-the-declared-bytes",
        },
    )
    assert "failure-ref:taw00:candidate-revision-content-drift" in failures


def test_baseline_receipt_requires_locked_metric_census_and_current_acceptance() -> (
    None
):
    protocol_payload = verifier._load(verifier.PROTOCOL)
    protocol_payload.update(
        {
            "status": "locked",
            "supported_language_refs": ["language-ref:test-language"],
            "model_configuration_refs": ["configuration-ref:taw00:test"],
            "hardware_backend_refs": ["hardware-ref:taw00:test"],
            "supported_stratum_refs": ["stratum-ref:taw00:test"],
            "metric_census": [
                MetricRequirement(
                    metric_ref=metric_ref,
                    stratum_ref="stratum-ref:taw00:test",
                    minimum_denominator=10,
                    estimand_ref=(
                        "estimand-ref:taw00:paired-p95-ttft-one-sided-upper"
                        if metric_ref == "metric-ref:taw00:p95-ttft-difference"
                        else "estimand-ref:taw00:paired-quality-one-sided-lower"
                        if "quality-" in metric_ref
                        else "estimand-ref:taw00:binomial-one-sided-upper"
                    ),
                    estimator_ref="estimator-ref:taw00:paired-bootstrap",
                    acceptance_bound=TAW00_ACCEPTANCE_SPECS[metric_ref][0],
                    absolute_threshold=TAW00_ACCEPTANCE_SPECS[metric_ref][1],
                    relative_to_baseline_fraction=TAW00_ACCEPTANCE_SPECS[metric_ref][2],
                ).model_dump(mode="json")
                for metric_ref in TAW00_REQUIRED_METRICS
            ],
            "power_analysis_receipt_digest_ref": "sha256:" + "1" * 64,
            "expected_pair_manifest_digest_ref": "sha256:" + "2" * 64,
            "acceptance_affecting_path_refs": sorted(
                (*TAW00_MANDATORY_CANDIDATE_PATH_REFS, "repo-path-ref:a.py")
            ),
            "source_projection_path_refs": ["repo-path-ref:a.py"],
            "blocked_reason_refs": [],
        }
    )
    protocol = TAW00Protocol.model_validate(protocol_payload)
    metric = BaselineMetric(
        metric_ref="metric-ref:any",
        stratum_ref="stratum-ref:taw00:test",
        denominator=1,
        point_estimate=0,
        lower_bound=0,
        upper_bound=0,
        estimator_ref="estimator-ref:taw00:paired-bootstrap",
        estimand_ref="estimand-ref:taw00:binomial-one-sided-upper",
        evidence_digest_ref="sha256:" + "3" * 64,
    )
    receipt_payload = {
        "baseline_ref": "baseline-ref:taw00:test",
        "cycle_ref": "cycle-ref:taw00:initial",
        "evaluator_revision_ref": "git-sha:" + "a" * 40,
        "evaluator_environment_digest_ref": "sha256:" + "4" * 64,
        "catalog_digest_ref": "sha256:" + "5" * 64,
        "model_artifact_digest_ref": "sha256:" + "6" * 64,
        "tokenizer_digest_ref": "sha256:" + "7" * 64,
        "inference_config_digest_ref": "sha256:" + "8" * 64,
        "prompt_format_digest_ref": "sha256:" + "9" * 64,
        "ttft_ordering_receipt_digest_ref": "sha256:" + "a" * 64,
        "cache_state_receipt_digest_ref": "sha256:" + "b" * 64,
        "baseline_payload_digest_ref": "sha256:" + "c" * 64,
        "candidate_payload_digest_ref": "sha256:" + "d" * 64,
        "metrics": [metric.model_dump(mode="json")],
        "failure_refs": [],
        "artifact_census_digest_ref": "sha256:" + "e" * 64,
        "source_projection_digest_ref": "sha256:" + "f" * 64,
        "pair_manifest_digest_ref": "sha256:" + "2" * 64,
        "complete": True,
        "accepted_current": True,
        "acceptance_receipt_ref": "acceptance-ref:taw00:test",
        "raw_content_persisted": False,
        "runtime_authority_added": False,
    }
    full_payload = {
        "schema_version": "uaa-taw00-baseline-receipt.v1",
        **receipt_payload,
    }
    receipt = BaselineReceipt(
        **receipt_payload,
        receipt_digest_ref=canonical_digest(full_payload),
    )
    failures = validate_baseline_receipt(
        receipt,
        protocol,
        source_projection_digest_ref="sha256:" + "f" * 64,
        pair_manifest_digest_ref="sha256:" + "2" * 64,
    )
    assert "failure-ref:taw00:baseline-metric-census-drift" in failures


def test_baseline_receipt_enforces_absolute_and_relative_acceptance_bounds() -> None:
    protocol_payload = verifier._load(verifier.PROTOCOL)
    protocol_payload.update(
        {
            "status": "locked",
            "supported_language_refs": ["language-ref:test-language"],
            "model_configuration_refs": ["configuration-ref:taw00:test"],
            "hardware_backend_refs": ["hardware-ref:taw00:test"],
            "supported_stratum_refs": ["stratum-ref:taw00:test"],
            "metric_census": [
                MetricRequirement(
                    metric_ref=metric_ref,
                    stratum_ref="stratum-ref:taw00:test",
                    minimum_denominator=10,
                    estimand_ref=(
                        "estimand-ref:taw00:paired-p95-ttft-one-sided-upper"
                        if metric_ref == "metric-ref:taw00:p95-ttft-difference"
                        else "estimand-ref:taw00:paired-quality-one-sided-lower"
                        if "quality-" in metric_ref
                        else "estimand-ref:taw00:binomial-one-sided-upper"
                    ),
                    estimator_ref="estimator-ref:taw00:paired-bootstrap",
                    acceptance_bound=TAW00_ACCEPTANCE_SPECS[metric_ref][0],
                    absolute_threshold=TAW00_ACCEPTANCE_SPECS[metric_ref][1],
                    relative_to_baseline_fraction=TAW00_ACCEPTANCE_SPECS[metric_ref][2],
                ).model_dump(mode="json")
                for metric_ref in TAW00_REQUIRED_METRICS
            ],
            "power_analysis_receipt_digest_ref": "sha256:" + "1" * 64,
            "expected_pair_manifest_digest_ref": "sha256:" + "2" * 64,
            "acceptance_affecting_path_refs": sorted(
                (*TAW00_MANDATORY_CANDIDATE_PATH_REFS, "repo-path-ref:a.py")
            ),
            "source_projection_path_refs": ["repo-path-ref:a.py"],
            "blocked_reason_refs": [],
        }
    )
    protocol = TAW00Protocol.model_validate(protocol_payload)

    def receipt_with(*, p95_upper: float, quality_lower: float) -> BaselineReceipt:
        metrics = []
        for requirement in protocol.metric_census:
            is_p95 = requirement.metric_ref == "metric-ref:taw00:p95-ttft-difference"
            is_quality = requirement.metric_ref.startswith("metric-ref:taw00:quality-")
            is_binomial = requirement.estimand_ref == (
                "estimand-ref:taw00:binomial-one-sided-upper"
            )
            lower = quality_lower if is_quality else 0.0
            upper = (
                p95_upper
                if is_p95
                else binomial_one_sided_upper_bound(0, 300)
                if is_binomial
                else 0.0
            )
            point = max(lower, min(0.0 if not is_p95 else 1.0, upper))
            metrics.append(
                BaselineMetric(
                    metric_ref=requirement.metric_ref,
                    stratum_ref=requirement.stratum_ref,
                    denominator=300 if is_binomial else 10,
                    event_count=0 if is_binomial else None,
                    point_estimate=point,
                    lower_bound=lower,
                    upper_bound=upper,
                    baseline_reference_value=100.0 if is_p95 else None,
                    estimator_ref=requirement.estimator_ref,
                    estimand_ref=requirement.estimand_ref,
                    evidence_digest_ref="sha256:" + "3" * 64,
                )
            )
        payload = {
            "schema_version": "uaa-taw00-baseline-receipt.v1",
            "baseline_ref": "baseline-ref:taw00:test",
            "cycle_ref": protocol.cycle_ref,
            "evaluator_revision_ref": "git-sha:" + "a" * 40,
            "evaluator_environment_digest_ref": "sha256:" + "4" * 64,
            "catalog_digest_ref": "sha256:" + "5" * 64,
            "model_artifact_digest_ref": "sha256:" + "6" * 64,
            "tokenizer_digest_ref": "sha256:" + "7" * 64,
            "inference_config_digest_ref": "sha256:" + "8" * 64,
            "prompt_format_digest_ref": "sha256:" + "9" * 64,
            "ttft_ordering_receipt_digest_ref": "sha256:" + "a" * 64,
            "cache_state_receipt_digest_ref": "sha256:" + "b" * 64,
            "baseline_payload_digest_ref": "sha256:" + "c" * 64,
            "candidate_payload_digest_ref": "sha256:" + "d" * 64,
            "metrics": [metric.model_dump(mode="json") for metric in metrics],
            "failure_refs": [],
            "artifact_census_digest_ref": "sha256:" + "e" * 64,
            "source_projection_digest_ref": "sha256:" + "f" * 64,
            "pair_manifest_digest_ref": "sha256:" + "2" * 64,
            "accepted_current": True,
            "acceptance_receipt_ref": "acceptance-ref:taw00:test",
            "complete": True,
            "raw_content_persisted": False,
            "runtime_authority_added": False,
        }
        return BaselineReceipt(
            **payload,
            receipt_digest_ref=canonical_digest(payload),
        )

    passing = receipt_with(p95_upper=5.0, quality_lower=-5.0)
    assert set(
        validate_baseline_receipt(
            passing,
            protocol,
            source_projection_digest_ref="sha256:" + "f" * 64,
            pair_manifest_digest_ref="sha256:" + "2" * 64,
        )
    ) == {
        "failure-ref:taw00:artifact-census-contract-incomplete",
        "failure-ref:taw00:baseline-observation-derivation-incomplete",
        "failure-ref:taw00:familywise-bound-contract-incomplete",
    }
    relative_failure = validate_baseline_receipt(
        receipt_with(p95_upper=6.0, quality_lower=-5.0),
        protocol,
        source_projection_digest_ref="sha256:" + "f" * 64,
        pair_manifest_digest_ref="sha256:" + "2" * 64,
    )
    assert (
        "failure-ref:taw00:baseline-relative-acceptance-threshold-failed"
        in relative_failure
    )
    absolute_failure = validate_baseline_receipt(
        receipt_with(p95_upper=5.0, quality_lower=-5.1),
        protocol,
        source_projection_digest_ref="sha256:" + "f" * 64,
        pair_manifest_digest_ref="sha256:" + "2" * 64,
    )
    assert "failure-ref:taw00:baseline-acceptance-threshold-failed" in absolute_failure


def test_pending_protocol_reports_external_inputs_without_inventing_defaults() -> None:
    protocol = TAW00Protocol.model_validate(verifier._load(verifier.PROTOCOL))

    report = protocol_readiness(protocol)

    assert protocol.supported_language_refs == ()
    assert protocol.model_configuration_refs == ()
    assert protocol.hardware_backend_refs == ()
    assert report["status"] == "blocked"
    assert "blocker-ref:taw00:configuration-matrix-not-locked" in report["reason_refs"]
    assert (
        "blocker-ref:taw00:independent-custodian-identity-authority-missing"
        in report["reason_refs"]
    )
    assert (
        "blocker-ref:taw00:acceptance-evidence-binding-unverified"
        in report["reason_refs"]
    )
    assert (
        "blocker-ref:taw00:acceptance-evidence-contract-incomplete"
        in report["reason_refs"]
    )


def test_founder_dogfood_profile_accepts_bounded_q22_implementation() -> None:
    profile = TAW00FounderDogfoodProfile.model_validate(
        verifier._load(verifier.FOUNDER_DOGFOOD_PROFILE)
    )
    report = founder_dogfood_readiness(profile)
    profiles = {item.profile_ref: item for item in profile.inference_profiles}

    assert profile.language_refs == ("language-ref:en",)
    assert profile.hardware_family_refs == (
        "hardware-family-ref:mac",
        "hardware-family-ref:windows",
    )
    local = profiles["inference-profile-ref:taw00:qwen-3.8-27b-128k-local"]
    assert local.model_ref == "model-ref:qwen-3.8-27b"
    assert local.context_window_ref == "context-window-ref:128k"
    assert (
        profiles["inference-profile-ref:taw00:openai-chatgpt-api"].surface_ref
        == "inference-surface-ref:openai-api"
    )
    assert (
        profiles["inference-profile-ref:taw00:openai-codex-api"].surface_ref
        == "inference-surface-ref:openai-api"
    )
    assert report["status"] == "accepted_for_bounded_implementation"
    assert report["implementation_ready"] is True
    assert report["independent_promotion_ready"] is False
    assert report["runtime_model_calls_added"] is False
    assert report["provider_calls_added"] is False
    assert report["authority_added"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("language_refs", ["language-ref:en", "language-ref:es"]),
        ("same_host_baseline_required", False),
        ("public_quality_claims_allowed", True),
        ("provider_calls_added", True),
        ("independent_promotion_required", False),
    ),
)
def test_founder_dogfood_profile_fails_closed_on_scope_drift(
    field: str, value: object
) -> None:
    payload = copy.deepcopy(verifier._load(verifier.FOUNDER_DOGFOOD_PROFILE))
    payload[field] = value

    with pytest.raises(ValidationError):
        TAW00FounderDogfoodProfile.model_validate(payload)


def test_founder_dogfood_cli_reports_implementation_not_promotion(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "sys.argv", ["run_tool_aware_baseline.py", "report-founder-dogfood-readiness"]
    )

    assert baseline_cli.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["implementation_ready"] is True
    assert report["independent_promotion_ready"] is False
    assert report["provider_calls_added"] is False


def test_source_projection_is_revision_bound_and_closed() -> None:
    projection = copy.deepcopy(verifier._load(verifier.SOURCE_PROJECTION))
    projection["source_revision_ref"] = "git-sha:" + "0" * 40
    projection_payload = {
        key: value
        for key, value in projection.items()
        if key != "projection_digest_ref"
    }
    projection["projection_digest_ref"] = canonical_digest(projection_payload)
    failures = verifier.verify(
        source_projection_payload=projection,
        check_files=False,
    )
    assert any("source projection validation failed" in failure for failure in failures)

    projection = copy.deepcopy(verifier._load(verifier.SOURCE_PROJECTION))
    projection["entries"] = projection["entries"][:-1]
    projection_payload = {
        key: value
        for key, value in projection.items()
        if key != "projection_digest_ref"
    }
    projection["projection_digest_ref"] = canonical_digest(projection_payload)
    failures = verifier.verify(
        source_projection_payload=projection,
        check_files=False,
    )
    assert "source projection root inventory drifted" in failures


def test_durable_artifacts_reject_raw_fields_and_false_completion() -> None:
    assert durable_payload_has_forbidden_fields(
        {"raw_prompt": "content", "safe_ref": "evidence-ref:taw00:test"}
    )
    for key in ("content", "message", "absolute_path", "hostname", "environment_dump"):
        assert durable_payload_has_forbidden_fields({key: "opaque-value"})
    for value in ("evidence-ref:sk_live_abc123", "evidence-ref:ghp_abcdef123456"):
        assert durable_payload_has_forbidden_fields({"evidence_ref": value})
    assert not durable_payload_has_forbidden_fields({"raw_content_persisted": False})
    assert durable_payload_has_forbidden_fields({"raw_content_persisted": True})
    ledger = copy.deepcopy(verifier._load(verifier.LEDGER))
    ledger["status"] = "accepted"
    failures = verifier.verify(ledger_payload=ledger, check_files=False)
    assert any("overclaims completion" in failure for failure in failures)
    ledger = copy.deepcopy(verifier._load(verifier.LEDGER))
    ledger["unexpected_rawish_alias"] = "safe-ref:taw00:opaque"
    failures = verifier.verify(ledger_payload=ledger, check_files=False)
    assert "TAW-00 convergence ledger shape drifted" in failures


def test_schema_rejects_untyped_nested_artifacts() -> None:
    validator = verifier.Draft202012Validator(verifier._load(verifier.SCHEMA))
    corpus = build_development_corpus_manifest(
        corpus_ref="corpus-ref:taw00:development-v1",
        deterministic_seed_ref="seed-ref:taw00:development-v1",
        seed_material=b"public-development-seed-material",
        specs=(_case_spec(),),
    ).model_dump(mode="json")
    corpus["cases"] = ["not-a-case-object"]
    assert list(validator.iter_errors(corpus))

    metric_payload = {
        "schema_version": "uaa-taw00-baseline-receipt.v1",
        "metrics": ["not-a-metric-object"],
    }
    assert list(validator.iter_errors(metric_payload))


def test_schema_rejects_untyped_power_and_randomization_artifacts() -> None:
    validator = verifier.Draft202012Validator(verifier._load(verifier.SCHEMA))
    corpus = build_development_corpus_manifest(
        corpus_ref="corpus-ref:taw00:development-v1",
        deterministic_seed_ref="seed-ref:taw00:development-v1",
        seed_material=b"public-development-seed-material",
        specs=(_case_spec(),),
    ).model_dump(mode="json")
    corpus["cases"] = ["not-a-case-object"]
    assert list(validator.iter_errors(corpus))

    metric_payload = {
        "schema_version": "uaa-taw00-baseline-receipt.v1",
        "metrics": ["not-a-metric-object"],
    }
    assert list(validator.iter_errors(metric_payload))

    candidate_lock = _candidate_lock()
    pair_manifest = _bound_pair_manifest(1, candidate_lock=candidate_lock)
    power_payload = _power_receipt(_locked_protocol(pair_manifest)).model_dump(
        mode="json"
    )
    assert not list(validator.iter_errors(power_payload))
    oversized_power_payload = copy.deepcopy(power_payload)
    oversized_power_payload["cells"][0]["minimum_denominator"] = (
        TAW00_MAX_BINOMIAL_DENOMINATOR + 1
    )
    assert list(validator.iter_errors(oversized_power_payload))
    power_payload["cells"][0]["untyped_override"] = True
    assert list(validator.iter_errors(power_payload))

    randomization_payload = _randomization_bundle(
        pair_manifest, candidate_lock
    ).model_dump(mode="json")
    assert not list(validator.iter_errors(randomization_payload))
    randomization_payload["receipts"][0]["raw_prompt"] = "forbidden"
    assert list(validator.iter_errors(randomization_payload))


def test_acceptance_oriented_cli_commands_remain_non_authoritative(
    tmp_path, monkeypatch, capsys
) -> None:
    pair_manifest = _pair_manifest(1)
    commitment = build_holdout_commitment(
        cycle_ref="cycle-ref:taw00:test",
        custodian_ref="custodian-ref:taw00:independent",
        creation_order_evidence_ref="evidence-ref:taw00:pre-candidate",
        custodian_attestation_ref="attestation-ref:taw00:independent-custodian",
        secret_key=b"k" * 32,
        private_manifest=(
            '{"schema_version":"uaa-taw00-private-holdout.v1",'
            '"cycle_ref":"cycle-ref:taw00:test",'
            '"corpus_ref":"corpus-ref:taw00:holdout-v1",'
            '"deterministic_seed_ref":"seed-ref:taw00:holdout-v1",'
            f'"seed_material_hex":"{"ab" * 32}",'
            '"cases":[{"case_ref":"case-ref:taw00:holdout-1",'
            '"category_ref":"category-ref:taw00:ordinary-chat",'
            '"rubric_ref":"rubric-ref:taw00:ordinary-chat-quality-v1",'
            '"parameter_refs":["parameter-ref:taw00:neutral-tone"],'
            '"variant_index":1}],"synthetic_only":true}'
        ).encode(),
    )
    metric = BaselineMetric(
        metric_ref="metric-ref:any",
        stratum_ref="stratum-ref:taw00:test",
        denominator=1,
        point_estimate=0,
        lower_bound=0,
        upper_bound=0,
        estimator_ref="estimator-ref:taw00:paired-bootstrap",
        estimand_ref="estimand-ref:taw00:binomial-one-sided-upper",
        evidence_digest_ref="sha256:" + "3" * 64,
    )
    projection_payload = verifier._load(verifier.SOURCE_PROJECTION)
    receipt_payload = {
        "schema_version": "uaa-taw00-baseline-receipt.v1",
        "baseline_ref": "baseline-ref:taw00:test",
        "cycle_ref": "cycle-ref:taw00:initial",
        "evaluator_revision_ref": projection_payload["source_revision_ref"],
        "evaluator_environment_digest_ref": "sha256:" + "4" * 64,
        "catalog_digest_ref": "sha256:" + "5" * 64,
        "model_artifact_digest_ref": "sha256:" + "6" * 64,
        "tokenizer_digest_ref": "sha256:" + "7" * 64,
        "inference_config_digest_ref": "sha256:" + "8" * 64,
        "prompt_format_digest_ref": "sha256:" + "9" * 64,
        "ttft_ordering_receipt_digest_ref": "sha256:" + "a" * 64,
        "cache_state_receipt_digest_ref": "sha256:" + "b" * 64,
        "baseline_payload_digest_ref": "sha256:" + "c" * 64,
        "candidate_payload_digest_ref": "sha256:" + "d" * 64,
        "metrics": [metric.model_dump(mode="json")],
        "failure_refs": [],
        "artifact_census_digest_ref": "sha256:" + "e" * 64,
        "source_projection_digest_ref": projection_payload["projection_digest_ref"],
        "pair_manifest_digest_ref": pair_manifest.manifest_digest_ref,
        "accepted_current": True,
        "acceptance_receipt_ref": "acceptance-ref:taw00:test",
        "complete": True,
        "raw_content_persisted": False,
        "runtime_authority_added": False,
    }
    receipt = BaselineReceipt(
        **receipt_payload,
        receipt_digest_ref=canonical_digest(receipt_payload),
    )
    scores = BlindScoreBundle(
        pair_manifest_digest_ref=pair_manifest.manifest_digest_ref,
        scores=(_score(1, 1, 2), _score(1, 2, 2)),
    )
    adjudications = AdjudicationBundle(
        pair_manifest_digest_ref=pair_manifest.manifest_digest_ref,
        adjudications=(),
    )

    def write(name: str, payload: object):
        path = tmp_path / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    commitment_path = write("commitment.json", commitment.model_dump(mode="json"))
    receipt_path = write("receipt.json", receipt.model_dump(mode="json"))
    protocol_path = write("protocol.json", verifier._load(verifier.PROTOCOL))
    projection_path = write("projection.json", projection_payload)
    pair_path = write("pairs.json", pair_manifest.model_dump(mode="json"))
    scores_path = write("scores.json", scores.model_dump(mode="json"))
    adjudications_path = write(
        "adjudications.json", adjudications.model_dump(mode="json")
    )

    monkeypatch.setattr(
        baseline_cli.sys,
        "argv",
        [
            "run_tool_aware_baseline.py",
            "verify-public-commitment",
            "--commitment",
            str(commitment_path),
        ],
    )
    assert baseline_cli.main() == 2
    assert "structure_valid_but_acceptance_blocked" in capsys.readouterr().out

    monkeypatch.setattr(
        baseline_cli.sys,
        "argv",
        [
            "run_tool_aware_baseline.py",
            "verify-baseline-receipt",
            "--receipt",
            str(receipt_path),
            "--protocol",
            str(protocol_path),
            "--source-projection",
            str(projection_path),
            "--pair-manifest",
            str(pair_path),
        ],
    )
    assert baseline_cli.main() == 2
    baseline_output = capsys.readouterr().out
    assert "receipt_consistency_only_acceptance_blocked" in baseline_output
    assert all(word not in baseline_output for word in ('"ready"', '"verified"'))

    monkeypatch.setattr(
        baseline_cli.sys,
        "argv",
        [
            "run_tool_aware_baseline.py",
            "verify-score-receipts",
            "--scores",
            str(scores_path),
            "--adjudications",
            str(adjudications_path),
            "--pair-manifest",
            str(pair_path),
        ],
    )
    assert baseline_cli.main() == 2
    score_output = capsys.readouterr().out
    assert "receipt_consistency_only_acceptance_blocked" in score_output
    assert '"valid"' not in score_output


def test_bound_acceptance_cli_commands_remain_non_authoritative(
    tmp_path, monkeypatch, capsys
) -> None:
    candidate_lock = _candidate_lock()
    pair_manifest = _bound_pair_manifest(1, candidate_lock=candidate_lock)
    commitment = build_holdout_commitment(
        cycle_ref="cycle-ref:taw00:test",
        custodian_ref="custodian-ref:taw00:independent",
        creation_order_evidence_ref="evidence-ref:taw00:pre-candidate",
        custodian_attestation_ref="attestation-ref:taw00:independent-custodian",
        secret_key=b"k" * 32,
        private_manifest=(
            '{"schema_version":"uaa-taw00-private-holdout.v1",'
            '"cycle_ref":"cycle-ref:taw00:test",'
            '"corpus_ref":"corpus-ref:taw00:holdout-v1",'
            '"deterministic_seed_ref":"seed-ref:taw00:holdout-v1",'
            f'"seed_material_hex":"{"ab" * 32}",'
            '"cases":[{"case_ref":"case-ref:taw00:holdout-1",'
            '"category_ref":"category-ref:taw00:ordinary-chat",'
            '"rubric_ref":"rubric-ref:taw00:ordinary-chat-quality-v1",'
            '"parameter_refs":["parameter-ref:taw00:neutral-tone"],'
            '"variant_index":1}],"synthetic_only":true}'
        ).encode(),
    )
    metric = BaselineMetric(
        metric_ref="metric-ref:any",
        stratum_ref="stratum-ref:taw00:test",
        denominator=1,
        event_count=0,
        point_estimate=0,
        lower_bound=0,
        upper_bound=binomial_one_sided_upper_bound(0, 1),
        estimator_ref="estimator-ref:taw00:paired-bootstrap",
        estimand_ref="estimand-ref:taw00:binomial-one-sided-upper",
        evidence_digest_ref="sha256:" + "3" * 64,
    )
    projection_payload = verifier._load(verifier.SOURCE_PROJECTION)
    receipt_payload = {
        "schema_version": "uaa-taw00-baseline-receipt.v1",
        "baseline_ref": "baseline-ref:taw00:test",
        "cycle_ref": "cycle-ref:taw00:initial",
        "evaluator_revision_ref": projection_payload["source_revision_ref"],
        "evaluator_environment_digest_ref": "sha256:" + "4" * 64,
        "catalog_digest_ref": "sha256:" + "5" * 64,
        "model_artifact_digest_ref": "sha256:" + "6" * 64,
        "tokenizer_digest_ref": "sha256:" + "7" * 64,
        "inference_config_digest_ref": "sha256:" + "8" * 64,
        "prompt_format_digest_ref": "sha256:" + "9" * 64,
        "ttft_ordering_receipt_digest_ref": "sha256:" + "a" * 64,
        "cache_state_receipt_digest_ref": "sha256:" + "b" * 64,
        "baseline_payload_digest_ref": "sha256:" + "c" * 64,
        "candidate_payload_digest_ref": "sha256:" + "d" * 64,
        "metrics": [metric.model_dump(mode="json")],
        "failure_refs": [],
        "artifact_census_digest_ref": "sha256:" + "e" * 64,
        "source_projection_digest_ref": projection_payload["projection_digest_ref"],
        "pair_manifest_digest_ref": pair_manifest.manifest_digest_ref,
        "accepted_current": True,
        "acceptance_receipt_ref": "acceptance-ref:taw00:test",
        "complete": True,
        "raw_content_persisted": False,
        "runtime_authority_added": False,
    }
    receipt = BaselineReceipt(
        **receipt_payload,
        receipt_digest_ref=canonical_digest(receipt_payload),
    )
    scores = BlindScoreBundle(
        pair_manifest_digest_ref=pair_manifest.manifest_digest_ref,
        scores=(
            _bound_score(1, 1, 2, pair_manifest=pair_manifest),
            _bound_score(1, 2, 2, pair_manifest=pair_manifest),
        ),
    )
    adjudications = AdjudicationBundle(
        pair_manifest_digest_ref=pair_manifest.manifest_digest_ref,
        adjudications=(),
    )

    def write(name: str, payload: object):
        path = tmp_path / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    commitment_path = write("commitment.json", commitment.model_dump(mode="json"))
    receipt_path = write("receipt.json", receipt.model_dump(mode="json"))
    protocol_path = write("protocol.json", verifier._load(verifier.PROTOCOL))
    projection_path = write("projection.json", projection_payload)
    pair_path = write("pairs.json", pair_manifest.model_dump(mode="json"))
    scores_path = write("scores.json", scores.model_dump(mode="json"))
    adjudications_path = write(
        "adjudications.json", adjudications.model_dump(mode="json")
    )
    power_protocol = _locked_protocol(pair_manifest)
    power_path = write(
        "power.json", _power_receipt(power_protocol).model_dump(mode="json")
    )
    power_protocol_path = write(
        "power-protocol.json", power_protocol.model_dump(mode="json")
    )
    candidate_path = write("candidate.json", candidate_lock.model_dump(mode="json"))
    randomization_path = write(
        "randomization.json",
        _randomization_bundle(pair_manifest, candidate_lock).model_dump(mode="json"),
    )

    monkeypatch.setattr(
        baseline_cli.sys,
        "argv",
        [
            "run_tool_aware_baseline.py",
            "verify-public-commitment",
            "--commitment",
            str(commitment_path),
        ],
    )
    assert baseline_cli.main() == 2
    assert "structure_valid_but_acceptance_blocked" in capsys.readouterr().out

    monkeypatch.setattr(
        baseline_cli.sys,
        "argv",
        [
            "run_tool_aware_baseline.py",
            "verify-power-analysis",
            "--receipt",
            str(power_path),
            "--protocol",
            str(power_protocol_path),
            "--pair-manifest",
            str(pair_path),
        ],
    )
    assert baseline_cli.main() == 2
    assert "receipt_consistency_only_acceptance_blocked" in capsys.readouterr().out

    monkeypatch.setattr(
        baseline_cli.sys,
        "argv",
        [
            "run_tool_aware_baseline.py",
            "verify-randomization",
            "--bundle",
            str(randomization_path),
            "--pair-manifest",
            str(pair_path),
            "--candidate-lock",
            str(candidate_path),
        ],
    )
    assert baseline_cli.main() == 2
    assert "receipt_consistency_only_acceptance_blocked" in capsys.readouterr().out

    monkeypatch.setattr(
        baseline_cli.sys,
        "argv",
        [
            "run_tool_aware_baseline.py",
            "verify-baseline-receipt",
            "--receipt",
            str(receipt_path),
            "--protocol",
            str(protocol_path),
            "--source-projection",
            str(projection_path),
            "--pair-manifest",
            str(pair_path),
        ],
    )
    assert baseline_cli.main() == 2
    baseline_output = capsys.readouterr().out
    assert "receipt_consistency_only_acceptance_blocked" in baseline_output
    assert all(word not in baseline_output for word in ('"ready"', '"verified"'))

    monkeypatch.setattr(
        baseline_cli.sys,
        "argv",
        [
            "run_tool_aware_baseline.py",
            "verify-score-receipts",
            "--scores",
            str(scores_path),
            "--adjudications",
            str(adjudications_path),
            "--pair-manifest",
            str(pair_path),
            "--randomization",
            str(randomization_path),
        ],
    )
    assert baseline_cli.main() == 2
    score_output = capsys.readouterr().out
    assert "receipt_consistency_only_acceptance_blocked" in score_output
    assert '"valid"' not in score_output
