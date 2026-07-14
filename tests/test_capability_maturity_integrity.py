from __future__ import annotations

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.evals import build_capability_maturity_read_model


@pytest.mark.parametrize(
    ("field_name", "value", "error"),
    [
        ("verified_weighted_score", 0.0, "verified weighted score drift"),
        ("uplift_proven_count", 16, "aggregate count drift"),
        ("verification_posture", "targets_proven", "verification posture drift"),
    ],
)
def test_maturity_read_model_rejects_aggregate_drift(
    field_name: str,
    value: object,
    error: str,
) -> None:
    read_model = build_capability_maturity_read_model()
    payload = read_model.model_dump(mode="python")
    payload[field_name] = value

    with pytest.raises(ValidationError, match=error):
        type(read_model).model_validate(payload)


def test_maturity_read_model_rejects_component_definition_drift() -> None:
    read_model = build_capability_maturity_read_model()
    payload = read_model.model_dump(mode="python")
    payload["components"][0]["weight"] = 1

    with pytest.raises(ValidationError, match="component definition drift"):
        type(read_model).model_validate(payload)
