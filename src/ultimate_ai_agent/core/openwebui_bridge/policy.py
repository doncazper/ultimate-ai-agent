from ultimate_ai_agent.core.openwebui_bridge.enums import (
    OpenWebUIBridgeDecisionStatus,
    OpenWebUIContentMode,
    OpenWebUIRiskLevel,
)


def classify_openwebui_bridge_risk(content_mode: OpenWebUIContentMode) -> OpenWebUIRiskLevel:
    if content_mode in {OpenWebUIContentMode.summary_only, OpenWebUIContentMode.ref_only}:
        return OpenWebUIRiskLevel.low
    if content_mode == OpenWebUIContentMode.redacted_preview:
        return OpenWebUIRiskLevel.medium
    if content_mode == OpenWebUIContentMode.raw_content_blocked:
        return OpenWebUIRiskLevel.forbidden
    return OpenWebUIRiskLevel.high


def default_openwebui_bridge_decision_status() -> OpenWebUIBridgeDecisionStatus:
    return OpenWebUIBridgeDecisionStatus.requires_future_bridge
