from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts import verify_tool_aware_cognition_taw07 as verifier

from ultimate_ai_agent.core.capabilities.chat_shadow import (
    ChatShadowDecision,
    ShadowChatAction,
)
from ultimate_ai_agent.core.evals.tool_aware_corpus import (
    DevelopmentCaseSpec,
    DevelopmentCorpusManifest,
    HoldoutCommitment,
    build_development_corpus_manifest,
    reconstruct_development_case_payload,
)
import ultimate_ai_agent.core.evals.tool_aware_hardening as hardening
from ultimate_ai_agent.core.evals.tool_aware_hardening import (
    CatalogState,
    HardeningStatus,
    ReplayMode,
    TAW07_ACCEPTED_DEVELOPMENT_CORPUS_DIGEST,
    TAW07_CATALOG_STATES,
    TAW07_CATEGORY_ACTIONS,
    TAW07_CATEGORY_CENSUS,
    TAW07_REPLAY_MODES,
    TAW07DevelopmentObservation,
    TAW07HardeningPolicy,
    TAW07HardeningReport,
    TAW07LegacyCaseBinding,
    TAW07PairedQualityObservation,
    TAW07QualityDelta,
    bind_taw07_observation,
    bind_taw07_quality_observation,
    build_taw07_source_decision,
    evaluate_taw07_hardening,
)


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "docs/evals/tool_aware_cognition_taw07_development_corpus_v1.json"
CANDIDATE_REVISION = "git-sha:" + "7" * 40
CANDIDATE_DIGEST = "sha256:" + "8" * 64


def _corpus() -> DevelopmentCorpusManifest:
    return DevelopmentCorpusManifest.model_validate(
        json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    )


def _policy(corpus: DevelopmentCorpusManifest) -> TAW07HardeningPolicy:
    return TAW07HardeningPolicy(
        candidate_revision_ref=CANDIDATE_REVISION,
        candidate_manifest_digest_ref=CANDIDATE_DIGEST,
        development_corpus_digest_ref=corpus.corpus_digest,
        holdout_commitment=HoldoutCommitment(
            cycle_ref="cycle-ref:taw00:initial",
            custodian_ref="custodian-ref:taw07:test-only",
            commitment_digest="sha256:" + "9" * 64,
            creation_order_evidence_ref="evidence-ref:taw00:created-before-taw07",
            custodian_attestation_ref="attestation-ref:taw00:test-custodian",
        ),
    )


def _binding(case_ref: str) -> TAW07LegacyCaseBinding:
    slug = case_ref.rsplit(":", 1)[-1]
    return TAW07LegacyCaseBinding(
        case_ref=case_ref,
        payload_fingerprint_ref=f"payload-ref:taw07:{slug}",
        response_fingerprint_ref=f"response-ref:taw07:{slug}",
        durable_evidence_fingerprint_ref=f"evidence-set-ref:taw07:{slug}",
    )


def _expected_action(case, state: CatalogState, mode: ReplayMode):
    if mode == ReplayMode.safe_disabled_replay or state != CatalogState.healthy:
        return ShadowChatAction.preserve_direct_chat
    if "parameter-ref:taw07:reviewed-write-operation" in case.parameter_refs:
        return ShadowChatAction.block_capability_proposal
    return TAW07_CATEGORY_ACTIONS[case.category_ref]


def _passing_inputs(corpus: DevelopmentCorpusManifest):
    bindings = tuple(_binding(case.case_ref) for case in corpus.cases)
    by_case = {item.case_ref: item for item in bindings}
    observations = []
    for case in corpus.cases:
        binding = by_case[case.case_ref]
        case_payload = reconstruct_development_case_payload(corpus, case.case_ref)
        for state_ref in TAW07_CATALOG_STATES:
            state = CatalogState(state_ref)
            for mode_ref in TAW07_REPLAY_MODES:
                mode = ReplayMode(mode_ref)
                source_decision = build_taw07_source_decision(
                    case_payload=case_payload,
                    catalog_state=state,
                    replay_mode=mode,
                )
                observations.append(
                    bind_taw07_observation(
                        case_ref=case.case_ref,
                        category_ref=case.category_ref,
                        candidate_revision_ref=CANDIDATE_REVISION,
                        candidate_manifest_digest_ref=CANDIDATE_DIGEST,
                        development_corpus_digest_ref=corpus.corpus_digest,
                        catalog_state=state,
                        replay_mode=mode,
                        source_decision=source_decision,
                        observed_action=_expected_action(case, state, mode),
                        payload_fingerprint_ref=binding.payload_fingerprint_ref,
                        response_fingerprint_ref=binding.response_fingerprint_ref,
                        durable_evidence_fingerprint_ref=(
                            binding.durable_evidence_fingerprint_ref
                        ),
                        routing_latency_milliseconds=5,
                        hydration_latency_milliseconds=(
                            10
                            if source_decision.hydration_fingerprint_ref is not None
                            and state == CatalogState.healthy
                            and mode == ReplayMode.candidate_shadow
                            else 0
                        ),
                        baseline_ttft_milliseconds=100,
                        candidate_ttft_milliseconds=100,
                        model_visible_context_tokens=0,
                        safe_disable_engaged=(
                            mode == ReplayMode.safe_disabled_replay
                            or state != CatalogState.healthy
                        ),
                        evidence_ref=f"evidence-ref:taw07:{case.case_ref.rsplit(':', 1)[-1]}:{state.value}:{mode.value}",
                    )
                )
    quality = tuple(
        bind_taw07_quality_observation(
            case_ref=case.case_ref,
            candidate_revision_ref=CANDIDATE_REVISION,
            candidate_manifest_digest_ref=CANDIDATE_DIGEST,
            development_corpus_digest_ref=corpus.corpus_digest,
            baseline_response_fingerprint_ref=by_case[
                case.case_ref
            ].response_fingerprint_ref,
            candidate_response_fingerprint_ref=by_case[
                case.case_ref
            ].response_fingerprint_ref,
            dimension_deltas=TAW07QualityDelta(
                helpfulness=0,
                instruction_following=0,
                tone=0,
                response_relevance=0,
            ),
            evidence_ref=f"evidence-ref:taw07:founder-score:{case.case_ref.rsplit(':', 1)[-1]}",
        )
        for case in corpus.cases
        if case.category_ref == "category-ref:taw07:ordinary-chat"
    )
    return bindings, tuple(observations), quality


def _evaluate(
    corpus: DevelopmentCorpusManifest,
    *,
    bindings=None,
    observations=None,
    quality=None,
):
    defaults = _passing_inputs(corpus)
    return evaluate_taw07_hardening(
        policy=_policy(corpus),
        corpus=corpus,
        legacy_bindings=bindings if bindings is not None else defaults[0],
        observations=observations if observations is not None else defaults[1],
        quality_observations=quality if quality is not None else defaults[2],
    )


def _rebind_report_fingerprint(payload: dict[str, object]) -> None:
    report_payload = {
        key: value for key, value in payload.items() if key != "report_fingerprint_ref"
    }
    digest = hashlib.sha256(
        json.dumps(
            report_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    payload["report_fingerprint_ref"] = f"taw07-hardening-report-ref:sha256:{digest}"


def test_founder_development_matrix_is_clean_but_cannot_self_verify_holdout() -> (
    None
):
    corpus = _corpus()
    report = _evaluate(corpus)
    assert report.status == HardeningStatus.blocked_unverified_holdout_commitment
    assert report.case_count == 24
    assert report.observation_count == 240
    assert report.quality_observation_count == 2
    assert report.safe_disable_equivalence_proven
    assert report.exact_matrix_coverage_proven
    assert report.lower_quality_confidence_bound_by_dimension.helpfulness == 0
    assert all(metric.event_count == 0 for metric in report.metric_results)
    assert report.runtime_model_calls_added is False
    assert report.provider_calls_added is False
    assert report.execution_authority_added is False
    assert report.public_quality_claims_allowed is False
    assert report.independent_promotion_ready is False


def test_development_manifest_is_reconstructible_and_covers_injection_fields() -> None:
    corpus = _corpus()
    assert corpus.synthetic_only
    assert corpus.raw_content_persisted is False
    for case in corpus.cases:
        payload = reconstruct_development_case_payload(corpus, case.case_ref)
        assert payload.system_text
        assert payload.user_text
    _evaluate(corpus)


def test_development_manifest_exactly_binds_case_parameter_mapping() -> None:
    corpus = _corpus()
    assert corpus.corpus_digest == TAW07_ACCEPTED_DEVELOPMENT_CORPUS_DIGEST
    specs = tuple(
        DevelopmentCaseSpec(
            case_ref=case.case_ref,
            category_ref=case.category_ref,
            rubric_ref=case.rubric_ref,
            parameter_refs=(
                ("parameter-ref:taw07:substituted-mapping",)
                if index == 0
                else case.parameter_refs
            ),
            variant_index=case.variant_index,
        )
        for index, case in enumerate(corpus.cases)
    )
    substituted = build_development_corpus_manifest(
        corpus_ref=corpus.corpus_ref,
        deterministic_seed_ref=corpus.deterministic_seed_ref,
        seed_material=bytes.fromhex(corpus.deterministic_seed_material_hex),
        specs=specs,
    )
    with pytest.raises(ValueError, match="accepted TAW-07 manifest"):
        evaluate_taw07_hardening(
            policy=_policy(substituted),
            corpus=substituted,
            legacy_bindings=(),
            observations=(),
            quality_observations=(),
        )


def test_catalog_injection_cases_build_distinct_poisoned_catalog_evidence() -> None:
    corpus = _corpus()
    decisions = []
    for case in corpus.cases:
        if case.category_ref != "category-ref:taw07:catalog-injection":
            continue
        decision = build_taw07_source_decision(
            case_payload=reconstruct_development_case_payload(corpus, case.case_ref),
            catalog_state=CatalogState.healthy,
            replay_mode=ReplayMode.candidate_shadow,
        )
        assert decision.action == ShadowChatAction.record_capability_candidate
        assert len(decision.selected_operation_refs) == 1
        assert decision.hydration_fingerprint_ref is not None
        assert decision.model_context_changed is False
        decisions.append(decision)
    assert len(decisions) == 15
    assert len({item.assessment_fingerprint_ref for item in decisions}) == len(
        decisions
    )


@pytest.mark.parametrize("catalog_state", ["corrupt", "stale", "over_budget"])
def test_degraded_catalog_states_are_detected_by_candidate_boundaries(
    catalog_state: str,
) -> None:
    corpus = _corpus()
    case = corpus.cases[0]
    decision = build_taw07_source_decision(
        case_payload=reconstruct_development_case_payload(corpus, case.case_ref),
        catalog_state=CatalogState(catalog_state),
        replay_mode=ReplayMode.candidate_shadow,
    )
    assert decision.action == ShadowChatAction.preserve_direct_chat
    assert decision.safe_disable_engaged is True


@pytest.mark.parametrize("schema_field", ["input_schema", "output_schema"])
def test_schema_descriptions_are_excluded_from_rendered_hydration(
    schema_field: str,
) -> None:
    corpus = _corpus()
    case = next(
        item
        for item in corpus.cases
        if f"parameter-ref:taw07:catalog-field-{schema_field}" in item.parameter_refs
    )
    payload = reconstruct_development_case_payload(corpus, case.case_ref)
    catalog, operations = hardening._candidate_catalog(injection_field=schema_field)
    read_operation = next(
        item for item in operations if item.operation_id.endswith("reviewed-read")
    )
    hydration = hardening._candidate_hydration(
        payload,
        catalog,
        operations,
        selected_operation_id=read_operation.operation_id,
    )
    assert all(
        hardening._INSTRUCTION_SHAPED_TEXT not in item.rendered_untrusted_data
        for item in hydration.manifests
    )


def test_development_corpus_requires_the_exact_category_census() -> None:
    corpus = _corpus()
    specs = tuple(
        DevelopmentCaseSpec(
            case_ref=case.case_ref,
            category_ref=(
                "category-ref:taw07:ordinary-chat"
                if case.case_ref == "case-ref:taw07:supported-tool-01"
                else case.category_ref
            ),
            rubric_ref=case.rubric_ref,
            parameter_refs=case.parameter_refs,
            variant_index=case.variant_index,
        )
        for case in corpus.cases
    )
    drifted = build_development_corpus_manifest(
        corpus_ref="corpus-ref:taw07:category-drift",
        deterministic_seed_ref="seed-ref:taw07:category-drift",
        seed_material=b"c" * 32,
        specs=specs,
    )
    with pytest.raises(ValueError, match="category census"):
        evaluate_taw07_hardening(
            policy=_policy(drifted),
            corpus=drifted,
            legacy_bindings=(),
            observations=(),
            quality_observations=(),
        )


def test_missing_or_duplicate_matrix_identity_fails_closed() -> None:
    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    with pytest.raises(ValueError, match="exact and duplicate-free"):
        evaluate_taw07_hardening(
            policy=_policy(corpus),
            corpus=corpus,
            legacy_bindings=bindings,
            observations=observations[:-1],
            quality_observations=quality,
        )
    with pytest.raises(ValueError, match="exact and duplicate-free"):
        evaluate_taw07_hardening(
            policy=_policy(corpus),
            corpus=corpus,
            legacy_bindings=bindings,
            observations=(*observations[:-1], observations[0]),
            quality_observations=quality,
        )


def test_candidate_or_corpus_rebinding_is_rejected() -> None:
    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    changed = bind_taw07_observation(
        **{
            **observations[0].model_dump(
                mode="python", exclude={"observation_fingerprint_ref"}
            ),
            "candidate_revision_ref": "git-sha:" + "9" * 40,
        }
    )
    with pytest.raises(ValueError, match="candidate or corpus binding mismatch"):
        evaluate_taw07_hardening(
            policy=_policy(corpus),
            corpus=corpus,
            legacy_bindings=bindings,
            observations=(changed, *observations[1:]),
            quality_observations=quality,
        )


def test_safe_disable_substitution_produces_failed_report() -> None:
    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    target = next(
        item
        for item in observations
        if item.catalog_state == CatalogState.corrupt
        and item.replay_mode == ReplayMode.safe_disabled_replay
    )
    changed = bind_taw07_observation(
        **{
            **target.model_dump(mode="python", exclude={"observation_fingerprint_ref"}),
            "response_fingerprint_ref": "response-ref:taw07:substituted",
        }
    )
    next_observations = tuple(
        changed if item is target else item for item in observations
    )
    report = evaluate_taw07_hardening(
        policy=_policy(corpus),
        corpus=corpus,
        legacy_bindings=bindings,
        observations=next_observations,
        quality_observations=quality,
    )
    assert report.status == HardeningStatus.failed
    assert not report.safe_disable_equivalence_proven
    metric = next(
        item
        for item in report.metric_results
        if item.metric_ref == "metric-ref:taw07:safe-disable-equivalence-failure"
    )
    assert metric.event_count == 1


def test_source_decision_substitution_is_rejected() -> None:
    corpus = _corpus()
    observation = _passing_inputs(corpus)[1][0]
    with pytest.raises(
        ValidationError, match="bind the exact validated TAW-04 decision"
    ):
        bind_taw07_observation(
            **{
                **observation.model_dump(
                    mode="python", exclude={"observation_fingerprint_ref"}
                ),
                "observed_action": ShadowChatAction.block_capability_proposal,
            }
        )


def test_valid_but_rebound_source_decision_is_rejected() -> None:
    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    target = next(
        item
        for item in observations
        if item.catalog_state == CatalogState.healthy
        and item.replay_mode == ReplayMode.candidate_shadow
        and item.category_ref == "category-ref:taw07:supported-tool"
    )
    decision_payload = target.source_decision.model_dump(
        mode="json", exclude={"decision_fingerprint_ref"}
    )
    decision_payload["assessment_fingerprint_ref"] = (
        "assessment-ref:taw07:substituted-development"
    )
    encoded = json.dumps(
        decision_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    rebound = ChatShadowDecision.model_validate(
        {
            **decision_payload,
            "decision_fingerprint_ref": (
                "chat-shadow-decision-ref:taw04:sha256:"
                + hashlib.sha256(encoded).hexdigest()
            ),
        }
    )
    changed = bind_taw07_observation(
        **{
            **target.model_dump(mode="python", exclude={"observation_fingerprint_ref"}),
            "source_decision": rebound,
        }
    )
    with pytest.raises(ValueError, match="exact expected TAW-04 source decision"):
        evaluate_taw07_hardening(
            policy=_policy(corpus),
            corpus=corpus,
            legacy_bindings=bindings,
            observations=tuple(
                changed if item is target else item for item in observations
            ),
            quality_observations=quality,
        )


def test_latency_context_and_quality_failures_are_visible() -> None:
    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    target = observations[0]
    changed = bind_taw07_observation(
        **{
            **target.model_dump(mode="python", exclude={"observation_fingerprint_ref"}),
            "routing_latency_milliseconds": 101,
            "model_visible_context_tokens": 1,
        }
    )
    score = quality[0]
    changed_score = bind_taw07_quality_observation(
        **{
            **score.model_dump(mode="python", exclude={"observation_fingerprint_ref"}),
            "dimension_deltas": TAW07QualityDelta(
                helpfulness=-6,
                instruction_following=0,
                tone=0,
                response_relevance=0,
            ),
        }
    )
    report = evaluate_taw07_hardening(
        policy=_policy(corpus),
        corpus=corpus,
        legacy_bindings=bindings,
        observations=tuple(
            changed if item is target else item for item in observations
        ),
        quality_observations=(changed_score, *quality[1:]),
    )
    assert report.status == HardeningStatus.failed
    failed = {item.metric_ref for item in report.metric_results if not item.passed}
    assert "metric-ref:taw07:performance-budget-failure" in failed
    assert "metric-ref:taw07:context-budget-failure" in failed
    assert "metric-ref:taw07:paired-quality-non-inferiority-failure" in failed


def test_ttft_absolute_and_relative_budget_is_recomputed() -> None:
    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    changed = tuple(
        bind_taw07_observation(
            **{
                **item.model_dump(
                    mode="python", exclude={"observation_fingerprint_ref"}
                ),
                "candidate_ttft_milliseconds": 106,
            }
        )
        for item in observations
    )
    report = evaluate_taw07_hardening(
        policy=_policy(corpus),
        corpus=corpus,
        legacy_bindings=bindings,
        observations=changed,
        quality_observations=quality,
    )
    assert report.p95_ttft_margin_milliseconds == 6
    assert report.status == HardeningStatus.failed


def test_ttft_uses_paired_category_margins() -> None:
    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    target_category = "category-ref:taw07:unsupported-request"
    changed = tuple(
        bind_taw07_observation(
            **{
                **item.model_dump(
                    mode="python", exclude={"observation_fingerprint_ref"}
                ),
                "baseline_ttft_milliseconds": (
                    1_000 if item.category_ref != target_category else 100
                ),
                "candidate_ttft_milliseconds": (
                    1_000 if item.category_ref != target_category else 106
                ),
            }
        )
        for item in observations
    )
    report = evaluate_taw07_hardening(
        policy=_policy(corpus),
        corpus=corpus,
        legacy_bindings=bindings,
        observations=changed,
        quality_observations=quality,
    )
    assert report.p95_ttft_margin_milliseconds == 6
    assert report.status == HardeningStatus.failed


def test_ttft_relative_margin_is_paired_before_category_p95() -> None:
    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    target_category = "category-ref:taw07:unsupported-request"
    target_index = 0
    changed = []
    for item in observations:
        values = item.model_dump(mode="python", exclude={"observation_fingerprint_ref"})
        if item.category_ref == target_category:
            if target_index < 2:
                values["baseline_ttft_milliseconds"] = 100
                values["candidate_ttft_milliseconds"] = 106
            else:
                values["baseline_ttft_milliseconds"] = 1_000
                values["candidate_ttft_milliseconds"] = 1_000
            target_index += 1
        else:
            values["baseline_ttft_milliseconds"] = 1_000
            values["candidate_ttft_milliseconds"] = 1_000
        changed.append(bind_taw07_observation(**values))
    report = evaluate_taw07_hardening(
        policy=_policy(corpus),
        corpus=corpus,
        legacy_bindings=bindings,
        observations=tuple(changed),
        quality_observations=quality,
    )
    assert report.p95_ttft_margin_milliseconds == 6
    assert report.status == HardeningStatus.failed


def test_active_candidate_ttft_is_not_masked_by_safe_disable_strata() -> None:
    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    target = next(
        item
        for item in observations
        if item.category_ref == "category-ref:taw07:catalog-injection"
        and item.catalog_state == CatalogState.healthy
        and item.replay_mode == ReplayMode.candidate_shadow
    )
    changed_target = bind_taw07_observation(
        **{
            **target.model_dump(
                mode="python", exclude={"observation_fingerprint_ref"}
            ),
            "candidate_ttft_milliseconds": 106,
        }
    )
    report = evaluate_taw07_hardening(
        policy=_policy(corpus),
        corpus=corpus,
        legacy_bindings=bindings,
        observations=tuple(
            changed_target if item is target else item for item in observations
        ),
        quality_observations=quality,
    )
    assert report.p95_ttft_margin_milliseconds == 6
    assert report.status == HardeningStatus.failed


def test_severe_relative_ttft_regression_is_bounded_and_fails() -> None:
    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    changed = tuple(
        bind_taw07_observation(
            **{
                **item.model_dump(
                    mode="python", exclude={"observation_fingerprint_ref"}
                ),
                "baseline_ttft_milliseconds": 100,
                "candidate_ttft_milliseconds": 201,
            }
        )
        for item in observations
    )
    report = evaluate_taw07_hardening(
        policy=_policy(corpus),
        corpus=corpus,
        legacy_bindings=bindings,
        observations=changed,
        quality_observations=quality,
    )
    assert report.maximum_p95_ttft_relative_margin_basis_points_observed == 10_001
    assert report.status == HardeningStatus.failed


def test_performance_denominator_counts_every_ttft_stratum_gate() -> None:
    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    changed = tuple(
        bind_taw07_observation(
            **{
                **item.model_dump(
                    mode="python", exclude={"observation_fingerprint_ref"}
                ),
                "routing_latency_milliseconds": 101,
                "candidate_ttft_milliseconds": 106,
            }
        )
        for item in observations
    )
    report = evaluate_taw07_hardening(
        policy=_policy(corpus),
        corpus=corpus,
        legacy_bindings=bindings,
        observations=changed,
        quality_observations=quality,
    )
    metric = next(
        item
        for item in report.metric_results
        if item.metric_ref == "metric-ref:taw07:performance-budget-failure"
    )
    stratum_count = (
        len(TAW07_CATEGORY_CENSUS)
        * len(TAW07_CATALOG_STATES)
        * len(TAW07_REPLAY_MODES)
    )
    assert metric.denominator == len(observations) + stratum_count
    assert metric.event_count == len(observations) + stratum_count


def test_report_binds_the_exact_policy_thresholds_used() -> None:
    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    strict_policy = _policy(corpus)
    relaxed_policy = strict_policy.model_copy(
        update={"maximum_routing_latency_milliseconds": 1_000}
    )
    strict = evaluate_taw07_hardening(
        policy=strict_policy,
        corpus=corpus,
        legacy_bindings=bindings,
        observations=observations,
        quality_observations=quality,
    )
    relaxed = evaluate_taw07_hardening(
        policy=relaxed_policy,
        corpus=corpus,
        legacy_bindings=bindings,
        observations=observations,
        quality_observations=quality,
    )
    assert strict.policy_fingerprint_ref != relaxed.policy_fingerprint_ref


def test_holdout_and_authority_fields_fail_closed() -> None:
    corpus = _corpus()
    with pytest.raises(ValidationError, match="accepted TAW-00 cycle"):
        TAW07HardeningPolicy(
            candidate_revision_ref=CANDIDATE_REVISION,
            candidate_manifest_digest_ref=CANDIDATE_DIGEST,
            development_corpus_digest_ref=corpus.corpus_digest,
            holdout_commitment=HoldoutCommitment(
                cycle_ref="cycle-ref:taw00:substituted",
                custodian_ref="custodian-ref:taw07:test-only",
                commitment_digest="sha256:" + "1" * 64,
                creation_order_evidence_ref="evidence-ref:taw00:created-before-taw07",
                custodian_attestation_ref="attestation-ref:taw00:test-custodian",
            ),
        )
    payload = _passing_inputs(corpus)[1][0].model_dump(mode="json")
    payload["holdout_material_accessed"] = True
    with pytest.raises(ValidationError, match="literal_error"):
        TAW07DevelopmentObservation.model_validate(payload)
    policy_payload = _policy(corpus).model_dump(mode="json")
    policy_payload["public_quality_claims_allowed"] = True
    with pytest.raises(ValidationError, match="literal_error"):
        TAW07HardeningPolicy.model_validate(policy_payload)


def test_missing_holdout_commitment_blocks_passing_posture() -> None:
    corpus = _corpus()
    policy = TAW07HardeningPolicy(
        candidate_revision_ref=CANDIDATE_REVISION,
        candidate_manifest_digest_ref=CANDIDATE_DIGEST,
        development_corpus_digest_ref=corpus.corpus_digest,
    )
    bindings, observations, quality = _passing_inputs(corpus)
    report = evaluate_taw07_hardening(
        policy=policy,
        corpus=corpus,
        legacy_bindings=bindings,
        observations=observations,
        quality_observations=quality,
    )
    assert report.status == HardeningStatus.blocked_missing_holdout_commitment


def test_substituted_legacy_binding_set_is_rejected() -> None:
    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    rebound_bindings = tuple(
        binding.model_copy(
            update={
                "payload_fingerprint_ref": (f"payload-ref:taw07:substituted-{index}"),
                "response_fingerprint_ref": (f"response-ref:taw07:substituted-{index}"),
                "durable_evidence_fingerprint_ref": (
                    f"evidence-set-ref:taw07:substituted-{index}"
                ),
            }
        )
        for index, binding in enumerate(bindings)
    )
    rebound_by_case = {item.case_ref: item for item in rebound_bindings}
    rebound_observations = tuple(
        bind_taw07_observation(
            **{
                **observation.model_dump(
                    mode="python", exclude={"observation_fingerprint_ref"}
                ),
                "payload_fingerprint_ref": rebound_by_case[
                    observation.case_ref
                ].payload_fingerprint_ref,
                "response_fingerprint_ref": rebound_by_case[
                    observation.case_ref
                ].response_fingerprint_ref,
                "durable_evidence_fingerprint_ref": rebound_by_case[
                    observation.case_ref
                ].durable_evidence_fingerprint_ref,
            }
        )
        for observation in observations
    )
    rebound_quality = tuple(
        bind_taw07_quality_observation(
            **{
                **item.model_dump(
                    mode="python", exclude={"observation_fingerprint_ref"}
                ),
                "baseline_response_fingerprint_ref": rebound_by_case[
                    item.case_ref
                ].response_fingerprint_ref,
            }
        )
        for item in quality
    )
    with pytest.raises(ValueError, match="accepted TAW-04 evidence"):
        evaluate_taw07_hardening(
            policy=_policy(corpus),
            corpus=corpus,
            legacy_bindings=rebound_bindings,
            observations=rebound_observations,
            quality_observations=rebound_quality,
        )


def test_quality_census_and_fingerprints_cannot_be_substituted() -> None:
    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    with pytest.raises(ValueError, match="exactly cover ordinary-chat"):
        evaluate_taw07_hardening(
            policy=_policy(corpus),
            corpus=corpus,
            legacy_bindings=bindings,
            observations=observations,
            quality_observations=quality[:-1],
        )
    payload = quality[0].model_dump(mode="json")
    payload["dimension_deltas"]["tone"] = 1
    with pytest.raises(ValidationError, match="fingerprint binding drift"):
        TAW07PairedQualityObservation.model_validate(payload)


def test_candidate_quality_response_is_bound_independently() -> None:
    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    changed = bind_taw07_quality_observation(
        **{
            **quality[0].model_dump(
                mode="python", exclude={"observation_fingerprint_ref"}
            ),
            "candidate_response_fingerprint_ref": (
                "response-ref:taw07:candidate-observed-wording"
            ),
        }
    )
    report = evaluate_taw07_hardening(
        policy=_policy(corpus),
        corpus=corpus,
        legacy_bindings=bindings,
        observations=observations,
        quality_observations=(changed, *quality[1:]),
    )
    assert report.status == HardeningStatus.blocked_unverified_holdout_commitment


def test_report_fingerprint_and_status_are_recomputed() -> None:
    report = _evaluate(_corpus())
    payload = report.model_dump(mode="json")
    payload["p95_routing_latency_milliseconds"] -= 1
    with pytest.raises(ValidationError, match="fingerprint binding drift"):
        TAW07HardeningReport.model_validate(payload)
    payload = report.model_dump(mode="json")
    payload["status"] = HardeningStatus.failed.value
    with pytest.raises(ValidationError, match="status does not match"):
        TAW07HardeningReport.model_validate(payload)
    payload = report.model_dump(mode="json")
    payload["metric_results"] = payload["metric_results"][:-1]
    with pytest.raises(ValidationError, match="exact TAW-07 metric census"):
        TAW07HardeningReport.model_validate(payload)


def test_report_requires_fixed_counts_and_metric_denominators() -> None:
    report = _evaluate(_corpus())
    payload = report.model_dump(mode="json")
    payload["case_count"] = 1
    payload["observation_count"] = 1
    payload["quality_observation_count"] = 1
    with pytest.raises(ValidationError, match="fixed TAW-07 evidence census"):
        TAW07HardeningReport.model_validate(payload)

    payload = report.model_dump(mode="json")
    payload["metric_results"][0]["denominator"] = 1
    with pytest.raises(ValidationError, match="fixed TAW-07 census"):
        TAW07HardeningReport.model_validate(payload)


def test_report_rejects_passing_metrics_with_over_budget_aggregates() -> None:
    report = _evaluate(_corpus())
    payload = report.model_dump(mode="json")
    payload["maximum_context_tokens_observed"] = 128_001
    _rebind_report_fingerprint(payload)
    with pytest.raises(ValidationError, match="context metric contradicts"):
        TAW07HardeningReport.model_validate(payload)

    payload = report.model_dump(mode="json")
    payload["maximum_p95_ttft_relative_margin_basis_points_observed"] = 501
    _rebind_report_fingerprint(payload)
    with pytest.raises(ValidationError, match="performance metric contradicts"):
        TAW07HardeningReport.model_validate(payload)

    payload = report.model_dump(mode="json")
    payload["p95_routing_latency_milliseconds"] = 6
    payload["maximum_routing_latency_milliseconds_observed"] = 5
    _rebind_report_fingerprint(payload)
    with pytest.raises(ValidationError, match="p95 latency cannot exceed"):
        TAW07HardeningReport.model_validate(payload)

    payload = report.model_dump(mode="json")
    payload["lower_quality_confidence_bound_by_dimension"]["helpfulness"] = -6
    _rebind_report_fingerprint(payload)
    with pytest.raises(ValidationError, match="quality metric contradicts"):
        TAW07HardeningReport.model_validate(payload)

    corpus = _corpus()
    bindings, observations, quality = _passing_inputs(corpus)
    one_slow_observation = bind_taw07_observation(
        **{
            **observations[0].model_dump(
                mode="python", exclude={"observation_fingerprint_ref"}
            ),
            "routing_latency_milliseconds": 101,
        }
    )
    failed_report = evaluate_taw07_hardening(
        policy=_policy(corpus),
        corpus=corpus,
        legacy_bindings=bindings,
        observations=(one_slow_observation, *observations[1:]),
        quality_observations=quality,
    )
    payload = failed_report.model_dump(mode="json")
    performance_metric = next(
        item
        for item in payload["metric_results"]
        if item["metric_ref"] == "metric-ref:taw07:performance-budget-failure"
    )
    performance_metric["event_count"] = 0
    performance_metric["passed"] = True
    payload["failure_reason_refs"] = []
    payload["status"] = HardeningStatus.blocked_unverified_holdout_commitment.value
    _rebind_report_fingerprint(payload)
    with pytest.raises(ValidationError, match="performance metric contradicts"):
        TAW07HardeningReport.model_validate(payload)


def test_corpus_bound_is_checked_before_observation_matrix_materialization() -> None:
    specs = tuple(
        DevelopmentCaseSpec(
            case_ref=f"case-ref:taw07:bounded-{index}",
            category_ref="category-ref:taw07:ordinary-chat",
            rubric_ref="rubric-ref:taw07:founder-development-v1",
            parameter_refs=("parameter-ref:taw07:bounded",),
            variant_index=index,
        )
        for index in range(129)
    )
    corpus = build_development_corpus_manifest(
        corpus_ref="corpus-ref:taw07:too-large",
        deterministic_seed_ref="seed-ref:taw07:too-large",
        seed_material=b"b" * 32,
        specs=specs,
    )
    with pytest.raises(ValueError, match="exceeds the TAW-07 case bound"):
        evaluate_taw07_hardening(
            policy=_policy(corpus),
            corpus=corpus,
            legacy_bindings=(),
            observations=(),
            quality_observations=(),
        )


def test_models_reject_unknown_or_raw_fields_and_use_python310_compatible_enums() -> (
    None
):
    corpus = _corpus()
    payload = _passing_inputs(corpus)[1][0].model_dump(mode="json")
    payload["raw_prompt"] = "not allowed"
    with pytest.raises(ValidationError, match="extra_forbidden"):
        TAW07DevelopmentObservation.model_validate(payload)
    assert issubclass(CatalogState, str)
    assert issubclass(ReplayMode, str)
    assert str(ShadowChatAction.preserve_direct_chat) == "preserve_direct_chat"
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            "-c",
            (
                "import enum; hasattr(enum, 'StrEnum') and delattr(enum, 'StrEnum'); "
                "from ultimate_ai_agent.core.capabilities.chat_shadow import "
                "ShadowChatAction; "
                "assert str(ShadowChatAction.preserve_direct_chat) == "
                "'preserve_direct_chat'"
            ),
        ],
        cwd=ROOT,
        check=True,
    )


def test_reconstructed_payload_uses_parameters_not_embedded_category_label() -> None:
    corpus = _corpus()
    case = corpus.cases[0]
    payload = reconstruct_development_case_payload(corpus, case.case_ref)
    relabeled = payload.model_copy(
        update={
            "user_text": payload.user_text.replace(
                "category-ref:taw07:ordinary-chat",
                "category-ref:taw07:supported-tool",
            )
        }
    )
    decision = build_taw07_source_decision(
        case_payload=relabeled,
        catalog_state=CatalogState.healthy,
        replay_mode=ReplayMode.candidate_shadow,
    )
    assert decision.action == ShadowChatAction.preserve_direct_chat

    reparameterized = payload.model_copy(
        update={
            "user_text": payload.user_text.replace(
                "parameter-ref:taw07:neutral-conversation",
                "parameter-ref:taw07:reviewed-read-operation",
            )
        }
    )
    decision = build_taw07_source_decision(
        case_payload=reparameterized,
        catalog_state=CatalogState.healthy,
        replay_mode=ReplayMode.candidate_shadow,
    )
    assert decision.action == ShadowChatAction.record_capability_candidate


def test_reviewed_write_request_uses_write_envelope_and_hydration() -> None:
    corpus = _corpus()
    case = next(
        item
        for item in corpus.cases
        if "parameter-ref:taw07:reviewed-write-operation" in item.parameter_refs
    )
    decision = build_taw07_source_decision(
        case_payload=reconstruct_development_case_payload(corpus, case.case_ref),
        catalog_state=CatalogState.healthy,
        replay_mode=ReplayMode.candidate_shadow,
    )
    assert decision.action == ShadowChatAction.block_capability_proposal
    assert decision.selected_operation_refs == ()
    assert decision.hydration_fingerprint_ref is not None


def test_candidate_manifest_digest_rejects_dirty_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    tracked = repo / "candidate.txt"
    tracked.write_text("committed\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "candidate.txt"], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=TAW07 Test",
            "-c",
            "user.email=taw07@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=repo,
        check=True,
    )
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    monkeypatch.setattr(verifier, "ROOT", repo)
    monkeypatch.setattr(verifier, "CANDIDATE_PATHS", ("candidate.txt",))
    verifier._candidate_manifest_digest_ref(revision)
    tracked.write_text("dirty\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="candidate path is dirty"):
        verifier._candidate_manifest_digest_ref(revision)


def test_candidate_manifest_digest_accepts_git_normalized_crlf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    tracked = repo / "candidate.txt"
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "core.autocrlf", "true"], cwd=repo, check=True)
    tracked.write_bytes(b"committed\n")
    subprocess.run(["git", "add", "candidate.txt"], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=TAW07 Test",
            "-c",
            "user.email=taw07@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=repo,
        check=True,
    )
    tracked.unlink()
    subprocess.run(
        ["git", "checkout-index", "--force", "candidate.txt"],
        cwd=repo,
        check=True,
    )
    assert tracked.read_bytes() == b"committed\r\n"
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    monkeypatch.setattr(verifier, "ROOT", repo)
    monkeypatch.setattr(verifier, "CANDIDATE_PATHS", ("candidate.txt",))
    verifier._candidate_manifest_digest_ref(revision)


def test_manifest_digest_tampering_is_rejected_before_evaluation() -> None:
    payload = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    payload["cases"][0]["variant_index"] += 1
    with pytest.raises(ValidationError, match="generated-content digest binding drift"):
        DevelopmentCorpusManifest.model_validate(payload)
