from __future__ import annotations

import re

from ultimate_ai_agent.core.control_center.agent_loop import (
    build_external_information_handling_posture,
)


def test_external_intake_summary_is_renderable_without_relaxing_content_guard() -> None:
    posture = build_external_information_handling_posture()
    intake = next(
        row for row in posture["rows"]
        if row["category_id"] == "operator_supplied_external_metadata"
    )
    assert "without retaining source bodies" in intake["safe_summary"]
    assert not re.search(
        r"raw[_ -]?(?:prompt|response|page|payload|log)", intake["safe_summary"], re.I
    )
    assert intake["raw_content_included"] is False
    assert intake["external_content_can_grant_authority"] is False
