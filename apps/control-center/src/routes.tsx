import type { ControlCenterData } from "./api/types";
import { ActionPreviewForm } from "./components/ActionPreviewForm";
import { ApiRouteInventoryPanel } from "./components/ApiRouteInventoryPanel";
import { DashboardSummary } from "./components/DashboardSummary";
import { FoundationGatePanel } from "./components/FoundationGatePanel";
import { RuntimeReadinessPanel } from "./components/RuntimeReadinessPanel";
import {
  ApprovalSummaryPanel,
  MobilePlanningPanel,
  PluginGovernancePanel,
  RemoteWorkerSummaryPanel
} from "./components/SummaryPanels";

export const navItems = [
  { path: "/", label: "Overview" },
  { path: "/dashboard", label: "Dashboard" },
  { path: "/runtime", label: "Runtime" },
  { path: "/foundation-gate", label: "Foundation Gate" },
  { path: "/api-routes", label: "API Routes" },
  { path: "/approvals", label: "Approvals" },
  { path: "/remote-workers", label: "Remote Workers" },
  { path: "/mobile-planning", label: "Mobile Planning" },
  { path: "/plugin-governance", label: "Plugin Governance" },
  { path: "/action-preview", label: "Action Preview" }
] as const;

export function renderRoute(path: string, data: ControlCenterData) {
  switch (path) {
    case "/runtime":
      return <RuntimeReadinessPanel report={data.runtimeReadiness} matrix={data.capabilityMatrix} />;
    case "/foundation-gate":
      return <FoundationGatePanel summary={data.dashboard.foundation_gate_summary} />;
    case "/api-routes":
      return <ApiRouteInventoryPanel routes={data.routes} />;
    case "/approvals":
      return <ApprovalSummaryPanel summary={data.dashboard.approval_summary} />;
    case "/remote-workers":
      return (
        <RemoteWorkerSummaryPanel
          remote={data.dashboard.remote_worker_summary}
          privateMesh={data.dashboard.private_mesh_summary}
        />
      );
    case "/mobile-planning":
      return <MobilePlanningPanel summary={data.dashboard.mobile_planning_summary} />;
    case "/plugin-governance":
      return <PluginGovernancePanel summary={data.dashboard.plugin_governance_summary} />;
    case "/action-preview":
      return <ActionPreviewForm />;
    case "/dashboard":
    case "/":
    default:
      return <DashboardSummary dashboard={data.dashboard} />;
  }
}
