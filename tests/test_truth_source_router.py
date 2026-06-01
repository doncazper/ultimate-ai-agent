from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.truth import (
    GroundingMode,
    GroundingPolicy,
    TruthAuthorityLevel,
    TruthRouteRequest,
    TruthSourceManifest,
    TruthSourceRouter,
    TruthSourceType,
    TruthTaskClass,
)


def actor():
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="user_123",
        authority_source=AuthoritySource.explicit_user_request,
    )


def source(source_id, source_type, authority, **kwargs):
    return TruthSourceManifest(
        source_id=source_id,
        source_type=source_type,
        authority_level=authority,
        display_name=source_id,
        owner="tests",
        allowed_scopes=["project", "user"],
        allowed_purposes=["project_truth", "answer", "weather", "live_status"],
        data_classification=kwargs.pop("data_classification", "project_private"),
        **kwargs,
    )


def request(task_class, sources, *, policy=None, consent_refs=None):
    return TruthRouteRequest(
        request_id="trr_123",
        run_id="run_123",
        actor_context=actor(),
        task_class=task_class,
        question_or_claim="What source should support this answer?",
        grounding_policy=policy
        or GroundingPolicy(
            policy_id="gp_default",
            task_class=task_class,
            grounding_mode=GroundingMode.sources_required,
            require_freshness=task_class in [TruthTaskClass.live_status, TruthTaskClass.weather],
        ),
        available_sources=sources,
        data_classification="project_private",
        consent_refs=consent_refs or [],
    )


def test_project_truth_selects_canonical_over_memory():
    decision = TruthSourceRouter().route(
        request(
            TruthTaskClass.project_truth,
            [
                source("src_memory", TruthSourceType.memory, TruthAuthorityLevel.medium, memory_ref="mem_123"),
                source("src_canonical", TruthSourceType.canonical_file, TruthAuthorityLevel.authoritative, file_ref="docs/canonical/09_roadmap.md"),
            ],
        )
    )

    assert decision.selected_source_ids == ["src_canonical"]
    assert "MEMORY_SUPPORTING_ONLY" in decision.reason_codes


def test_live_status_refuses_memory_only():
    decision = TruthSourceRouter().route(
        request(
            TruthTaskClass.live_status,
            [source("src_memory", TruthSourceType.memory, TruthAuthorityLevel.medium, memory_ref="mem_123")],
        )
    )

    assert decision.selected_source_ids == []
    assert decision.required_next_action == "ask_for_source"
    assert "REQUIRED_SOURCE_UNAVAILABLE" in decision.reason_codes


def test_weather_requires_provider_or_api_result():
    decision = TruthSourceRouter().route(
        request(
            TruthTaskClass.weather,
            [source("src_provider", TruthSourceType.provider_result, TruthAuthorityLevel.high, provider_id="weather_provider")],
        )
    )

    assert decision.selected_source_ids == ["src_provider"]


def test_model_output_not_selected_as_authoritative():
    decision = TruthSourceRouter().route(
        request(
            TruthTaskClass.factual_answer,
            [source("src_model", TruthSourceType.model_output, TruthAuthorityLevel.not_authority)],
        )
    )

    assert decision.selected_source_ids == []
    assert "MODEL_OUTPUT_NOT_AUTHORITY" in decision.reason_codes


def test_private_source_rejected_without_consent():
    decision = TruthSourceRouter().route(
        request(
            TruthTaskClass.factual_answer,
            [
                source(
                    "src_private",
                    TruthSourceType.approved_document,
                    TruthAuthorityLevel.high,
                    access_requires_consent=True,
                    consent_ref="consent_private",
                )
            ],
        )
    )

    assert decision.selected_source_ids == []
    assert "CONSENT_REQUIRED" in decision.reason_codes


def test_provider_result_accepted_for_live_fact():
    decision = TruthSourceRouter().route(
        request(
            TruthTaskClass.live_status,
            [source("src_api", TruthSourceType.api, TruthAuthorityLevel.authoritative)],
        )
    )

    assert decision.selected_source_ids == ["src_api"]
