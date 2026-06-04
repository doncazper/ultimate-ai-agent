import type { ControlCenterData } from "./api/types";
import { ActionPreviewForm } from "./components/ActionPreviewForm";
import { ApprovalQueuePanel } from "./components/ApprovalQueuePanel";
import { ApiRouteInventoryPanel } from "./components/ApiRouteInventoryPanel";
import { DashboardSummary } from "./components/DashboardSummary";
import {
  EvidenceViewerPanel,
  FileReferenceViewerPanel,
  MemoryViewerPanel
} from "./components/EvidenceFileMemoryViewerPanel";
import { EventViewerPanel } from "./components/EventViewerPanel";
import { EventTimelineTracePanel } from "./components/EventTimelineTracePanel";
import { FileReviewSurfacePanel } from "./components/FileReviewSurfacePanel";
import { FoundationGatePanel } from "./components/FoundationGatePanel";
import {
  LocalRuntimeStatusPanel,
  ManualSmokeControlSurfacePanel
} from "./components/LocalRuntimeStatusPanel";
import { ReceiptViewerPanel } from "./components/ReceiptViewerPanel";
import { RuntimeReadinessPanel } from "./components/RuntimeReadinessPanel";
import {
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
  { path: "/receipts", label: "Receipts" },
  { path: "/events", label: "Events" },
  { path: "/events/timeline", label: "Timeline" },
  { path: "/evidence", label: "Evidence" },
  { path: "/files", label: "Files" },
  { path: "/files/review", label: "File Review" },
  { path: "/memory", label: "Memory" },
  { path: "/runtime/local", label: "Local Runtime" },
  { path: "/runtime/manual-smoke", label: "Manual Smoke" },
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
      return <ApprovalQueuePanel review={data.m15Review} />;
    case "/receipts":
      return <ReceiptViewerPanel review={data.m15Review} />;
    case "/events":
      return <EventViewerPanel review={data.m15Review} />;
    case "/events/timeline":
      return <EventTimelineTracePanel trace={data.m16Trace} />;
    case "/evidence":
      return <EvidenceViewerPanel knowledge={data.m17Knowledge} />;
    case "/files":
      return <FileReferenceViewerPanel knowledge={data.m17Knowledge} />;
    case "/files/review":
      return <FileReviewSurfacePanel review={data.m36FileReview} />;
    case "/memory":
      return <MemoryViewerPanel knowledge={data.m17Knowledge} />;
    case "/runtime/local":
      return (
        <LocalRuntimeStatusPanel
          report={data.runtimeReadiness}
          matrix={data.capabilityMatrix}
          runtime={data.m18Runtime}
        />
      );
    case "/runtime/manual-smoke":
      return <ManualSmokeControlSurfacePanel runtime={data.m18Runtime} />;
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
