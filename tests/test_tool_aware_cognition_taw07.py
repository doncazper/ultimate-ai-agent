from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.capabilities.chat_shadow import (
    ChatShadowDecision,
    ShadowChatAction,
)
from ultimate_ai_agent.core.evals.tool_aware_corpus import (
    DevelopmentCaseSpec,
    DevelopmentCorpusManifest,
    build_development_corpus_manifest,
    reconstruct_development_case_payload,
)
from ultimate_ai_agent.core.evals.tool_aware_hardening import (
    CatalogState,
    HardeningStatus,
    ReplayMode,
    TAW07_CATALOG_STATES,
    TAW07_CATEGORY_ACTIONS,
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
CORPUS_PATH = (
    ROOT / "docs/evals/tool_aware_cognition_taw07_development_corpus_v1.json"
)
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
    return TAW07_CATEGORY_ACTIONS[case.category_ref]


def _passing_inputs(corpus: DevelopmentCorpusManifest):
    bindings = tuple(_binding(case.case_ref) for case in corpus.cases)
    by_case = {item.case_ref: item for item in bindings}
    observations = []
    for case in corpus.cases:
        binding = by_case[case.case_ref]
        for state_ref in TAW07_CATALOG_STATES:
            state = CatalogState(state_ref)
            for mode_ref in TAW07_REPLAY_MODES:
                mode = ReplayMode(mode_ref)
                observations.append(
                    bind_taw07_observation(
                        case_ref=case.case_ref,
                        category_ref=case.category_ref,
                        candidate_revision_ref=CANDIDATE_REVISION,
                        candidate_manifest_digest_ref=CANDIDATE_DIGEST,
                        development_corpus_digest_ref=corpus.corpus_digest,
                        catalog_state=state,
                        replay_mode=mode,
                        source_decision=build_taw07_source_decision(
                            category_ref=case.category_ref,
                            catalog_state=state,
                            replay_mode=mode,
                        ),
                        observed_action=_expected_action(case, state, mode),
                        payload_fingerprint_ref=binding.payload_fingerprint_ref,
                        response_fingerprint_ref=binding.response_fingerprint_ref,
                        durable_evidence_fingerprint_ref=(
                            binding.durable_evidence_fingerprint_ref
                        ),
                        routing_latency_milliseconds=5,
                        hydration_latency_milliseconds=(
                            10
                            if case.category_ref
                            == "category-ref:taw07:supported-tool"
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


def test_founder_development_matrix_passes_without_authority_or_promotion_claim() -> None:
    corpus = _corpus()
    report = _evaluate(corpus)
    assert report.status == HardeningStatus.passed_founder_development
    assert report.case_count == 24
    assert report.observation_count == 240
    assert report.quality_observation_count == 2
    assert report.safe_disable_equivalence_proven
    assert report.exact_matrix_coverage_proven
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
    next_observations = tuple(changed if item is target else item for item in observations)
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
            **target.model_dump(
                mode="python", exclude={"observation_fingerprint_ref"}
            ),
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
        observations=tuple(changed if item is target else item for item in observations),
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
                **item.model_dump(mode="python", exclude={"observation_fingerprint_ref"}),
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


def test_holdout_and_authority_fields_fail_closed() -> None:
    corpus = _corpus()
    with pytest.raises(ValidationError, match="travel together"):
        TAW07HardeningPolicy(
            candidate_revision_ref=CANDIDATE_REVISION,
            candidate_manifest_digest_ref=CANDIDATE_DIGEST,
            development_corpus_digest_ref=corpus.corpus_digest,
            holdout_commitment_digest_ref="sha256:" + "1" * 64,
        )
    payload = _passing_inputs(corpus)[1][0].model_dump(mode="json")
    payload["holdout_material_accessed"] = True
    with pytest.raises(ValidationError, match="literal_error"):
        TAW07DevelopmentObservation.model_validate(payload)
    policy_payload = _policy(corpus).model_dump(mode="json")
    policy_payload["public_quality_claims_allowed"] = True
    with pytest.raises(ValidationError, match="literal_error"):
        TAW07HardeningPolicy.model_validate(policy_payload)


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


def test_report_fingerprint_and_status_are_recomputed() -> None:
    report = _evaluate(_corpus())
    payload = report.model_dump(mode="json")
    payload["case_count"] -= 1
    with pytest.raises(ValidationError, match="fingerprint binding drift"):
        TAW07HardeningReport.model_validate(payload)
    payload = report.model_dump(mode="json")
    payload["status"] = HardeningStatus.failed.value
    with pytest.raises(ValidationError, match="status does not match"):
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


def test_models_reject_unknown_or_raw_fields_and_use_python310_compatible_enums() -> None:
    corpus = _corpus()
    payload = _passing_inputs(corpus)[1][0].model_dump(mode="json")
    payload["raw_prompt"] = "not allowed"
    with pytest.raises(ValidationError, match="extra_forbidden"):
        TAW07DevelopmentObservation.model_validate(payload)
    assert issubclass(CatalogState, str)
    assert issubclass(ReplayMode, str)
    assert "StrEnum" not in Path(
        ROOT / "src/ultimate_ai_agent/core/evals/tool_aware_hardening.py"
    ).read_text(encoding="utf-8")


def test_manifest_digest_tampering_is_rejected_before_evaluation() -> None:
    payload = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    payload["cases"][0]["variant_index"] += 1
    with pytest.raises(ValidationError, match="generated-content digest binding drift"):
        DevelopmentCorpusManifest.model_validate(payload)
