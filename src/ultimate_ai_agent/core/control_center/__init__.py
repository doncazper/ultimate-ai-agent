from typing import TYPE_CHECKING, Any

from ultimate_ai_agent.core.control_center.action_decisions import (
    ACTION_DECISION_REQUESTED_ACTION,
    FOUNDER_LOOP_ACTION_DECISION_BLOCKED_REFS,
    FOUNDER_LOOP_ACTION_DECISION_KINDS,
    FOUNDER_LOOP_ACTION_DECISION_ROUTE_REFS,
    FOUNDER_LOOP_ACTION_ENVELOPE_PROMOTION_STATUS,
    FOUNDER_LOOP_ACTION_ENVELOPE_ROUTE_REFS,
    FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
    FOUNDER_LOOP_ACTION_STATUSES,
    FOUNDER_LOOP_VERTICAL_SLICE_CONTRACT_REF,
    FounderLoopActionDecisionReceipt,
    FounderLoopActionDecisionRequest,
    FounderLoopActionEnvelope,
    FounderLoopActionEnvelopePromotionReceipt,
    FounderLoopActionEnvelopePromotionRequest,
)
from ultimate_ai_agent.core.control_center.local_tasks import (
    FOUNDER_LOOP_LOCAL_TASK_BLOCKED_REFS,
    FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF,
    FOUNDER_LOOP_LOCAL_TASK_COMMIT_ROUTE_REF,
    FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
    FounderLoopLocalTaskCommitReceipt,
    FounderLoopLocalTaskCommitRequest,
)
from ultimate_ai_agent.core.control_center.today_loop import (
    TODAY_LOOP_LANE_ORDER,
    TODAY_LOOP_READ_MODEL_SOURCE,
    TODAY_LOOP_REQUIRED_BLOCKED_REFS,
    TODAY_LOOP_TIGHTENING_CONTRACT_REF,
    TodayLoopDigestItem,
    TodayLoopLane,
    TodayLoopReadModel,
    build_today_loop_read_model,
)
from ultimate_ai_agent.core.control_center.follow_up_tracker import (
    FOLLOW_UP_TRACKER_CATEGORY_ORDER,
    FOLLOW_UP_TRACKER_CONTRACT_REF,
    FOLLOW_UP_TRACKER_READ_MODEL_SOURCE,
    FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS,
    FollowUpTrackerItem,
    FollowUpTrackerReadModel,
    build_follow_up_tracker_read_model,
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
    "FOUNDER_LOOP_ACTION_ENVELOPE_PROMOTION_STATUS",
    "FOUNDER_LOOP_ACTION_ENVELOPE_ROUTE_REFS",
    "FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF",
    "FOUNDER_LOOP_ACTION_STATUSES",
    "FOUNDER_LOOP_VERTICAL_SLICE_CONTRACT_REF",
    "FOUNDER_LOOP_LOCAL_TASK_BLOCKED_REFS",
    "FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF",
    "FOUNDER_LOOP_LOCAL_TASK_COMMIT_ROUTE_REF",
    "FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND",
    "FOLLOW_UP_TRACKER_CATEGORY_ORDER",
    "FOLLOW_UP_TRACKER_CONTRACT_REF",
    "FOLLOW_UP_TRACKER_READ_MODEL_SOURCE",
    "FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS",
    "TODAY_LOOP_LANE_ORDER",
    "TODAY_LOOP_READ_MODEL_SOURCE",
    "TODAY_LOOP_REQUIRED_BLOCKED_REFS",
    "TODAY_LOOP_TIGHTENING_CONTRACT_REF",
    "FounderLoopControlCenterService",
    "FounderLoopActionDecisionReceipt",
    "FounderLoopActionDecisionRequest",
    "FounderLoopActionEnvelope",
    "FounderLoopActionEnvelopePromotionReceipt",
    "FounderLoopActionEnvelopePromotionRequest",
    "FounderLoopLocalTaskCommitReceipt",
    "FounderLoopLocalTaskCommitRequest",
    "FollowUpTrackerItem",
    "FollowUpTrackerReadModel",
    "TodayLoopDigestItem",
    "TodayLoopLane",
    "TodayLoopReadModel",
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
    "build_follow_up_tracker_read_model",
    "build_today_loop_read_model",
    "preview_control_center_action",
]
