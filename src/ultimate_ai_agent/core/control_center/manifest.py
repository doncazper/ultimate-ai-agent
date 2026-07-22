from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent import __version__
from ultimate_ai_agent.core.build_identity import build_identity
from ultimate_ai_agent.core.control_center.enums import ControlCenterCapabilityStatus, ControlCenterSurface
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.time import utc_now


CONTROL_CENTER_ROUTES = [
    "/control-center/actions/preview",
    "/control-center/actions/inbox",
    "/control-center/backend-truth",
    "/control-center/approvals/summary",
    "/control-center/capabilities/surface",
    "/control-center/dashboard",
    "/control-center/foundation-gate/summary",
    "/control-center/manifest",
    "/control-center/local-models/status",
    "/control-center/morning-briefing/summary",
    "/control-center/routes",
    "/control-center/runtime-readiness/summary",
    "/control-center/setup-assistant/summary",
    "/control-center/settings/status",
    "/control-center/status",
    "/control-center/storage/status",
    "/control-center/today/summary",
    "/control-center/trust-authority/matrix",
]


class ControlCenterSurfaceManifest(BaseModel):
    surface: ControlCenterSurface
    status: ControlCenterCapabilityStatus
    description: str = Field(..., min_length=1)
    read_only: bool = True
    preview_only: bool = False
    execution_allowed: bool = False
    route_refs: list[str] = Field(default_factory=list)
    blocked_capabilities: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def no_execution_surface(self) -> Any:
        if self.execution_allowed:
            raise ValueError("CONTROL_CENTER_SURFACE_EXECUTION_NOT_ALLOWED")
        if contains_secret_like(self.model_dump(mode="json")):
            raise ValueError("CONTROL_CENTER_SURFACE_SECRET_LIKE_VALUE_REJECTED")
        return self


class ControlCenterManifest(BaseModel):
    manifest_id: str = "control_center_manifest_m12"
    baseline_version: str = Field(default_factory=lambda: __version__)
    generated_at: str = Field(default_factory=lambda: utc_now().replace(microsecond=0).isoformat())
    api_version: str = Field(default_factory=lambda: __version__)
    title: str = "Ultimate AI Agent Control Center Contract"
    description: str = "Read-only and preview-only backend contract for a future Control Center UI."
    surfaces: list[ControlCenterSurfaceManifest]
    allowed_capabilities: list[str] = Field(default_factory=list)
    blocked_capabilities: list[str] = Field(default_factory=list)
    read_only_surfaces: list[ControlCenterSurface] = Field(default_factory=list)
    preview_only_surfaces: list[ControlCenterSurface] = Field(default_factory=list)
    requires_approval_for: list[str] = Field(default_factory=list)
    route_refs: list[str] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def no_execution_capability(self) -> Any:
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump):
            raise ValueError("CONTROL_CENTER_MANIFEST_SECRET_LIKE_VALUE_REJECTED")
        if any("execute capability" == capability for capability in self.allowed_capabilities):
            raise ValueError("CONTROL_CENTER_EXECUTE_CAPABILITY_NOT_ALLOWED")
        return self


def build_control_center_manifest(baseline_version: str | None = None) -> ControlCenterManifest:
    identity = build_identity()
    surfaces = sorted(
        [
            _surface(
                ControlCenterSurface.dashboard,
                ControlCenterCapabilityStatus.available_read_only,
                "Read-only dashboard snapshot for status and storage-backed Founder Loop summaries.",
                [
                    "/control-center/dashboard",
                    "/control-center/status",
                    "/control-center/today/summary",
                    "/control-center/morning-briefing/summary",
                    "/control-center/storage/status",
                ],
            ),
            _surface(
                ControlCenterSurface.approvals,
                ControlCenterCapabilityStatus.preview_only,
                "Approval queue summary, action inbox summaries, and approval previews only; no grant is created.",
                [
                    "/control-center/approvals/summary",
                    "/control-center/actions/inbox",
                    "/control-center/actions/preview",
                ],
                preview_only=True,
            ),
            _surface(
                ControlCenterSurface.runtime_readiness,
                ControlCenterCapabilityStatus.available_read_only,
                "Runtime readiness summary only; no runtime is started.",
                ["/control-center/runtime-readiness/summary"],
            ),
            _surface(
                ControlCenterSurface.foundation_gate,
                ControlCenterCapabilityStatus.available_read_only,
                "Foundation Gate status summary only.",
                ["/control-center/foundation-gate/summary"],
            ),
            _surface(
                ControlCenterSurface.api_routes,
                ControlCenterCapabilityStatus.available_read_only,
                "API route inventory summary only.",
                ["/control-center/routes"],
            ),
            _surface(
                ControlCenterSurface.macos_setup_assistant,
                ControlCenterCapabilityStatus.preview_only,
                "macOS Setup Assistant dry-run summary only; no installer authority is exposed.",
                ["/control-center/setup-assistant/summary"],
                preview_only=True,
            ),
            _surface(
                ControlCenterSurface.settings_status,
                ControlCenterCapabilityStatus.available_read_only,
                "Settings maturity, feature-flag, kill-switch, and authority-boundary status only; no setting is changed.",
                ["/control-center/settings/status"],
            ),
            _surface(
                ControlCenterSurface.local_models,
                ControlCenterCapabilityStatus.available_read_only,
                "Local model inventory and gateway posture status only; no model is downloaded, started, switched, or called.",
                ["/control-center/local-models/status"],
            ),
            _surface(
                ControlCenterSurface.trust_authority,
                ControlCenterCapabilityStatus.available_read_only,
                "Trust authority matrix explains usable tiers, approval posture, and blocked capabilities; no authority is granted.",
                ["/control-center/trust-authority/matrix"],
            ),
            _surface(ControlCenterSurface.events, ControlCenterCapabilityStatus.available_read_only, "Event summaries only; raw event payloads are not exposed.", []),
            _surface(ControlCenterSurface.receipts, ControlCenterCapabilityStatus.available_read_only, "Receipt summaries only; raw receipts are not exposed.", []),
            _surface(ControlCenterSurface.model_runtime, ControlCenterCapabilityStatus.validation_only, "Model runtime status and validation summary only; no model call is made.", []),
            _surface(ControlCenterSurface.remote_workers, ControlCenterCapabilityStatus.validation_only, "Remote worker status and dry-run metadata only; no dispatch is allowed.", []),
            _surface(ControlCenterSurface.private_mesh, ControlCenterCapabilityStatus.planned_disabled, "Private mesh, Headscale, WireGuard, and Tailscale are planned-disabled metadata only.", []),
            _surface(ControlCenterSurface.mobile_planning, ControlCenterCapabilityStatus.planned_disabled, "Mobile Companion and device sensors remain future planning only.", []),
            _surface(ControlCenterSurface.plugin_governance, ControlCenterCapabilityStatus.planned_disabled, "Codex plugin governance is docs/policy only; no plugin enablement.", []),
        ],
        key=lambda surface: surface.surface,
    )
    return ControlCenterManifest(
        baseline_version=baseline_version or __version__,
        api_version=baseline_version or __version__,
        surfaces=surfaces,
        allowed_capabilities=[
            "read_only_dashboard",
            "safe_action_preview",
            "route_inventory_summary",
            "runtime_readiness_summary",
            "foundation_gate_summary",
            "approval_summary",
            "setup_assistant_summary",
            "settings_status_summary",
            "local_models_status_summary",
            "trust_authority_matrix",
        ],
        blocked_capabilities=[
            "runtime_execution",
            "model_execution",
            "provider_invocation",
            "remote_dispatch",
            "mobile_sensor_access",
            "plugin_enablement",
            "frontend_build_tooling",
        ],
        read_only_surfaces=[surface.surface for surface in surfaces if surface.read_only],
        preview_only_surfaces=[surface.surface for surface in surfaces if surface.preview_only],
        requires_approval_for=["future_high_risk_actions"],
        route_refs=CONTROL_CENTER_ROUTES,
        docs_refs=[
            "docs/control_center/CONTROL_CENTER_CONTRACT.md",
            "docs/control_center/DASHBOARD_SNAPSHOT.md",
            "docs/control_center/ACTION_PREVIEW_POLICY.md",
        ],
        warnings=["Control Center is not the agent brain and cannot create authority."],
        metadata={
            "frontend_implemented": False,
            "production_control_center": False,
            "execution_routes_allowed": False,
            "plugin_enablement_allowed": False,
            "mobile_sensor_access_allowed": False,
            "build_id": identity.build_id,
            "commit_ref": identity.commit_ref,
            "source_revision_bound": identity.source_revision_bound,
            "storage_schema_version": identity.storage_schema_version,
            "capability_profile_version": identity.capability_profile_version,
        },
    )


def _surface(
    surface: ControlCenterSurface,
    status: ControlCenterCapabilityStatus,
    description: str,
    route_refs: list[str],
    preview_only: bool = False,
) -> ControlCenterSurfaceManifest:
    return ControlCenterSurfaceManifest(
        surface=surface,
        status=status,
        description=description,
        route_refs=route_refs,
        preview_only=preview_only,
        blocked_capabilities=["execute", "mutate", "credential_use", "external_action"],
        metadata={"source": "static_m12_contract"},
    )
