from typing import List

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.gate.enums import FoundationGateCategory


class FoundationGateCriterion(BaseModel):
    criterion_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    severity: str = Field(..., min_length=1)
    required: bool = True
    category: FoundationGateCategory
    evaluator_ref: str = Field(..., min_length=1)
    pass_condition: str = Field(..., min_length=1)
    failure_message: str = Field(..., min_length=1)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


def _criterion(
    criterion_id: str,
    name: str,
    category: FoundationGateCategory,
    evaluator_ref: str,
    pass_condition: str,
    failure_message: str,
    severity: str = "high",
) -> FoundationGateCriterion:
    return FoundationGateCriterion(
        criterion_id=criterion_id,
        name=name,
        description=pass_condition,
        severity=severity,
        required=True,
        category=category,
        evaluator_ref=evaluator_ref,
        pass_condition=pass_condition,
        failure_message=failure_message,
    )



from ultimate_ai_agent.core.gate.criteria_families import (
    foundation_core,
    runtime_authority_bootstrap,
    control_center_shell,
    product_spine_m21_m66,
    safety_expansion_m67_m98,
    post_m100_m99_m130,
    autonomy_alpha_m131_m150,
    local_model_m151_m167,
    cross_release_docs,
)

CRITERION_FAMILIES = (
    foundation_core.criteria,
    runtime_authority_bootstrap.criteria,
    control_center_shell.criteria,
    product_spine_m21_m66.criteria,
    safety_expansion_m67_m98.criteria,
    post_m100_m99_m130.criteria,
    autonomy_alpha_m131_m150.criteria,
    local_model_m151_m167.criteria,
    cross_release_docs.criteria,
)


def default_foundation_gate_criteria() -> List[FoundationGateCriterion]:
    criteria: List[FoundationGateCriterion] = []
    for family in CRITERION_FAMILIES:
        criteria.extend(family(_criterion))
    return criteria
