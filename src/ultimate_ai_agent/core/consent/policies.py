from typing import List
from pydantic import BaseModel, Field
from ultimate_ai_agent.core.consent.enums import PermissionAction, PermissionRisk, ApprovalRequirement

class StandingApprovalPolicy(BaseModel):
    policy_id: str
    actor_id: str
    allowed_actions: List[PermissionAction] = Field(default_factory=list)
    max_risk_allowed: PermissionRisk = PermissionRisk.low
    allowed_purposes: List[str] = Field(default_factory=list)

    def evaluates_to_standing(self, action: PermissionAction, risk: PermissionRisk, purpose: str) -> bool:
        # Rules:
        # High/critical risk actions cannot use standing approval
        if risk in [PermissionRisk.high, PermissionRisk.critical, PermissionRisk.forbidden]:
            return False
            
        if action not in self.allowed_actions:
            return False
            
        # Must be purpose-scoped where possible
        if self.allowed_purposes and purpose not in self.allowed_purposes:
            return False
            
        return True

class ApprovalPolicy(BaseModel):
    policy_id: str
    risk_level: PermissionRisk
    requirement: ApprovalRequirement
    human_override_required: bool = False
