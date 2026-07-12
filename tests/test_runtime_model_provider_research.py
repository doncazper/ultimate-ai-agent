from __future__ import annotations

import pytest

from ultimate_ai_agent.core.providers.control_plane import (
    MODEL_PROVIDER_RESEARCH_POSTURE_CONTRACT_REF,
    ModelProviderResearchPosture,
    build_model_provider_control_plane_read_model,
)


def test_model_provider_research_posture_is_backend_owned_and_blocked() -> None:
    read_model = build_model_provider_control_plane_read_model()
    posture = read_model.model_provider_research_posture

    assert posture.schema_version == "model_provider_research_posture.v1"
    assert posture.contract_ref == MODEL_PROVIDER_RESEARCH_POSTURE_CONTRACT_REF
    assert posture.status == "metadata_read_model_wired"
    assert posture.route_ref == read_model.route_ref
    assert posture.provider_count == len(posture.provider_postures)
    assert posture.provider_postures
    assert posture.provider_sdk_call_enabled is False
    assert posture.remote_model_call_enabled is False
    assert posture.live_web_fetch_enabled is False
    assert posture.browser_automation_enabled is False
    assert posture.production_authority_enabled is False
    assert posture.model_output_truth.model_output_is_proposal is True
    assert posture.model_output_truth.generated_text_is_verified_fact is False
    assert posture.model_output_truth.verified_fact_refs_required is True
    assert posture.external_information.web_access_gateway_required is True
    assert posture.external_information.default_policy_denied is True
    assert posture.external_information.fetched_content_untrusted is True
    assert posture.external_information.browser_action_enabled_by_control_plane is False
    assert (
        "authority-lane-ref:web-access:searxng-search:v1"
        in posture.external_information.allowed_current_lane_refs
    )
    assert (
        "blocked-state:web-access:no-unscoped-provider-search-calls"
        in posture.external_information.blocked_authority_refs
    )


def test_model_provider_research_posture_rejects_authority_creep() -> None:
    posture = (
        build_model_provider_control_plane_read_model().model_provider_research_posture
    )
    payload = posture.model_dump(mode="python")
    payload["provider_sdk_call_enabled"] = True

    with pytest.raises(
        ValueError, match="MODEL_PROVIDER_RESEARCH_POSTURE_AUTHORITY_DRIFT"
    ):
        ModelProviderResearchPosture.model_validate(payload)

    payload = posture.model_dump(mode="python")
    payload["model_output_truth"]["generated_text_is_verified_fact"] = True

    with pytest.raises(ValueError, match="MODEL_OUTPUT_TRUTH_AUTHORITY_DRIFT"):
        ModelProviderResearchPosture.model_validate(payload)

    payload = posture.model_dump(mode="python")
    payload["external_information"]["browser_action_enabled_by_control_plane"] = True

    with pytest.raises(
        ValueError, match="EXTERNAL_INFORMATION_RESEARCH_AUTHORITY_DRIFT"
    ):
        ModelProviderResearchPosture.model_validate(payload)
