from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent import __version__
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.time import utc_now


class StatusCard(BaseModel):
    label: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class GateSummary(BaseModel):
    status: str = "unknown"
    passed_count: int = Field(0, ge=0)
    failed_count: int = Field(0, ge=0)
    summary: str = "Foundation Gate status summary only."

    model_config = ConfigDict(extra="forbid")


class RuntimeReadinessSummary(BaseModel):
    status: str = "ready_for_manual_smoke"
    production_ready: bool = False
    real_model_runtime_ready: bool = False
    remote_execution_ready: bool = False
    mobile_sensor_ready: bool = False
    plugin_or_native_build_ready: bool = False

    model_config = ConfigDict(extra="forbid")


class ApprovalSummary(BaseModel):
    pending_count: int = Field(0, ge=0)
    approval_grants_created: bool = False
    arbitrary_approval_ref_authority: bool = False
    summary: str = "Approval summary only; no approval is granted."

    model_config = ConfigDict(extra="forbid")


class ApiSummary(BaseModel):
    route_count: int = Field(0, ge=0)
    control_center_route_count: int = Field(8, ge=0)
    operation_ids_unique: bool = True
    execution_routes_present: bool = False

    model_config = ConfigDict(extra="forbid")


class RemoteWorkerSummary(BaseModel):
    status: str = "dry_run_only"
    execution_enabled: bool = False
    dispatch_enabled: bool = False

    model_config = ConfigDict(extra="forbid")


class PrivateMeshSummary(BaseModel):
    status: str = "planned_disabled"
    headscale_integrated: bool = False
    tailscale_integrated: bool = False
    wireguard_integrated: bool = False

    model_config = ConfigDict(extra="forbid")


class MobilePlanningSummary(BaseModel):
    status: str = "planned_disabled"
    sensor_access_enabled: bool = False
    mobile_app_implemented: bool = False

    model_config = ConfigDict(extra="forbid")


class PluginGovernanceSummary(BaseModel):
    status: str = "planned_disabled"
    plugin_enablement_allowed: bool = False
    native_build_tools_enabled: bool = False

    model_config = ConfigDict(extra="forbid")


class ControlCenterDashboardSnapshot(BaseModel):
    snapshot_id: str = "control_center_dashboard_m12"
    baseline_version: str = Field(default_factory=lambda: __version__)
    generated_at: str = Field(default_factory=lambda: utc_now().replace(microsecond=0).isoformat())
    system_status: StatusCard
    foundation_gate_summary: GateSummary
    runtime_readiness_summary: RuntimeReadinessSummary
    approval_summary: ApprovalSummary
    api_summary: ApiSummary
    remote_worker_summary: RemoteWorkerSummary
    private_mesh_summary: PrivateMeshSummary
    mobile_planning_summary: MobilePlanningSummary
    plugin_governance_summary: PluginGovernanceSummary
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    next_recommended_action: str = "review_status_and_previews_only"
    metadata: dict[str, bool | str] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def dashboard_snapshot_must_be_safe(self):
        if contains_secret_like(self.model_dump(mode="json")):
            raise ValueError("CONTROL_CENTER_DASHBOARD_SECRET_LIKE_VALUE_REJECTED")
        return self


def build_control_center_dashboard(
    baseline_version: str | None = None,
    api_route_count: int = 0,
    foundation_gate_status: str = "unknown",
) -> ControlCenterDashboardSnapshot:
    return ControlCenterDashboardSnapshot(
        baseline_version=baseline_version or __version__,
        system_status=StatusCard(
            label="Control Center",
            status="available_read_only",
            summary="Backend dashboard contract is read-only and preview-only.",
        ),
        foundation_gate_summary=GateSummary(status=foundation_gate_status),
        runtime_readiness_summary=RuntimeReadinessSummary(),
        approval_summary=ApprovalSummary(),
        api_summary=ApiSummary(route_count=api_route_count),
        remote_worker_summary=RemoteWorkerSummary(),
        private_mesh_summary=PrivateMeshSummary(),
        mobile_planning_summary=MobilePlanningSummary(),
        plugin_governance_summary=PluginGovernanceSummary(),
        warnings=["No UI, frontend tooling, runtime execution, or plugin enablement is implemented."],
        metadata={
            "read_only": True,
            "preview_only": True,
            "frontend_implemented": False,
            "execution_allowed": False,
        },
    )
