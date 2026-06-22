from typing import TYPE_CHECKING, Any

from ultimate_ai_agent.core.control_center.action_decisions import (
    ACTION_DECISION_REQUESTED_ACTION,
    FOUNDER_LOOP_ACTION_DECISION_BLOCKED_REFS,
    FOUNDER_LOOP_ACTION_DECISION_KINDS,
    FOUNDER_LOOP_ACTION_DECISION_ROUTE_REFS,
    FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
    FOUNDER_LOOP_ACTION_STATUSES,
    FounderLoopActionDecisionReceipt,
    FounderLoopActionDecisionRequest,
    FounderLoopActionEnvelope,
)
from ultimate_ai_agent.core.control_center.actions import (
    ControlCenterActionPreviewDecision,
    ControlCenterActionPreviewRequest,
    preview_control_center_action,
)

from ultimate_ai_agent.core.control_center.dashboard import (
    ApiSummary,
    ApprovalSummary,
    ControlCenterDashboardSnapshot,
    GateSummary,
    GovernedProviderInvocationReadiness,
    MobilePlanningSummary,
    OperatorLoopStepSummary,
    OperatorLoopSummary,
    PluginGovernanceSummary,
    PrivateMeshSummary,
    ProviderCredentialEnrollmentReadiness,
    ProviderCredentialReadinessItem,
    ProviderCredentialReadinessSummary,
    ProviderCredentialValidationReadiness,
    ProviderCredentialVaultAdapterReadiness,
    RemoteWorkerSummary,
    RuntimeReadinessSummary,
    StatusCard,
    build_control_center_dashboard,
    build_operator_loop_summary,
    build_provider_credential_readiness_summary,
)
from ultimate_ai_agent.core.control_center.enums import (
    ControlCenterActionDecisionStatus,
    ControlCenterActionKind,
    ControlCenterCapabilityStatus,
    ControlCenterRiskLevel,
    ControlCenterSurface,
)
from ultimate_ai_agent.core.control_center.manifest import (
    CONTROL_CENTER_ROUTES,
    ControlCenterManifest,
    ControlCenterSurfaceManifest,
    build_control_center_manifest,
)

if TYPE_CHECKING:
    from ultimate_ai_agent.core.control_center.founder_loop import (
        FounderLoopControlCenterService,
    )


def __getattr__(name: str) -> Any:
    if name == "FounderLoopControlCenterService":
        from ultimate_ai_agent.core.control_center.founder_loop import (
            FounderLoopControlCenterService,
        )

        return FounderLoopControlCenterService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ACTION_DECISION_REQUESTED_ACTION",
    "ApiSummary",
    "ApprovalSummary",
    "CONTROL_CENTER_ROUTES",
    "ControlCenterActionDecisionStatus",
    "ControlCenterActionKind",
    "ControlCenterActionPreviewDecision",
    "ControlCenterActionPreviewRequest",
    "ControlCenterCapabilityStatus",
    "ControlCenterDashboardSnapshot",
    "ControlCenterManifest",
    "ControlCenterRiskLevel",
    "ControlCenterSurface",
    "ControlCenterSurfaceManifest",
    "FOUNDER_LOOP_ACTION_DECISION_BLOCKED_REFS",
    "FOUNDER_LOOP_ACTION_DECISION_KINDS",
    "FOUNDER_LOOP_ACTION_DECISION_ROUTE_REFS",
    "FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF",
    "FOUNDER_LOOP_ACTION_STATUSES",
    "FounderLoopControlCenterService",
    "FounderLoopActionDecisionReceipt",
    "FounderLoopActionDecisionRequest",
    "FounderLoopActionEnvelope",
    "GateSummary",
    "GovernedProviderInvocationReadiness",
    "MobilePlanningSummary",
    "OperatorLoopStepSummary",
    "OperatorLoopSummary",
    "PluginGovernanceSummary",
    "PrivateMeshSummary",
    "ProviderCredentialEnrollmentReadiness",
    "ProviderCredentialReadinessItem",
    "ProviderCredentialReadinessSummary",
    "ProviderCredentialValidationReadiness",
    "ProviderCredentialVaultAdapterReadiness",
    "RemoteWorkerSummary",
    "RuntimeReadinessSummary",
    "StatusCard",
    "build_control_center_dashboard",
    "build_operator_loop_summary",
    "build_provider_credential_readiness_summary",
    "build_control_center_manifest",
    "preview_control_center_action",
]
