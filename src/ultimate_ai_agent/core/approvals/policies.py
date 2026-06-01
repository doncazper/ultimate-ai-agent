from ultimate_ai_agent.core.approvals.enums import ApprovalRiskLevel


HIGH_RISK_APPROVAL_LEVELS = {ApprovalRiskLevel.high, ApprovalRiskLevel.critical}


def requires_explicit_approval(risk_level: ApprovalRiskLevel) -> bool:
    return risk_level in HIGH_RISK_APPROVAL_LEVELS
