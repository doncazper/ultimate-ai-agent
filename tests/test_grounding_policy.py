import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.truth import GroundingMode, GroundingPolicy, TruthTaskClass


def test_factual_task_with_no_grounding_is_rejected() -> None:
    with pytest.raises(ValidationError, match="grounding"):
        GroundingPolicy(
            policy_id="gp_fact",
            task_class=TruthTaskClass.factual_answer,
            grounding_mode=GroundingMode.none,
        )


def test_creative_task_may_have_no_grounding() -> None:
    policy = GroundingPolicy(
        policy_id="gp_creative",
        task_class=TruthTaskClass.creative,
        grounding_mode=GroundingMode.none,
    )

    assert policy.grounding_mode == GroundingMode.none


def test_live_status_requires_freshness() -> None:
    with pytest.raises(ValidationError, match="freshness"):
        GroundingPolicy(
            policy_id="gp_live",
            task_class=TruthTaskClass.live_status,
            grounding_mode=GroundingMode.sources_required,
            require_freshness=False,
        )


def test_high_stakes_requires_human_review_flag() -> None:
    with pytest.raises(ValidationError, match="human_review"):
        GroundingPolicy(
            policy_id="gp_legal",
            task_class=TruthTaskClass.legal,
            grounding_mode=GroundingMode.sources_required,
            require_human_review=False,
        )
