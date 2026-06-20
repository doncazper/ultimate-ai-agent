import type { ControlCenterData } from "./api/types";
import { ActionPreviewForm } from "./components/ActionPreviewForm";
import { ApprovalQueuePanel } from "./components/ApprovalQueuePanel";
import { ApiRouteInventoryPanel } from "./components/ApiRouteInventoryPanel";
import { ContextProposalSurfacePanel } from "./components/ContextProposalSurfacePanel";
import { DashboardSummary } from "./components/DashboardSummary";
import {
  FileReferenceViewerPanel,
  MemoryViewerPanel,
} from "./components/EvidenceFileMemoryViewerPanel";
import { EventViewerPanel } from "./components/EventViewerPanel";
import { EventTimelineTracePanel } from "./components/EventTimelineTracePanel";
import { FileReviewSurfacePanel } from "./components/FileReviewSurfacePanel";
import { FoundationGatePanel } from "./components/FoundationGatePanel";
import {
  LocalRuntimeStatusPanel,
  ManualSmokeControlSurfacePanel,
} from "./components/LocalRuntimeStatusPanel";
import {
  ChatOperatorPanel,
  EvidenceOperatorPanel,
  ModelsOperatorPanel,
  PlansOperatorPanel,
  SettingsOperatorPanel,
} from "./components/OperatorFlowPanels";
import { OperatorLoopPanel } from "./components/OperatorLoopPanel";
import { ReceiptViewerPanel } from "./components/ReceiptViewerPanel";
import { RuntimeReadinessPanel } from "./components/RuntimeReadinessPanel";
import {
  MobilePlanningPanel,
  PluginGovernancePanel,
  RemoteWorkerSummaryPanel,
} from "./components/SummaryPanels";

export const navItems = [
  { path: "/", label: "Overview" },
  { path: "/dashboard", label: "Dashboard" },
  { path: "/operator-loop", label: "Operator Loop" },
  { path: "/chat", label: "Chat" },
  { path: "/plans", label: "Plans" },
  { path: "/models", label: "Models" },
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
  { path: "/context/proposals", label: "Context Proposals" },
  { path: "/memory", label: "Memory" },
  { path: "/runtime/local", label: "Local Runtime" },
  { path: "/runtime/manual-smoke", label: "Manual Smoke" },
  { path: "/remote-workers", label: "Remote Workers" },
  { path: "/mobile-planning", label: "Mobile Planning" },
  { path: "/plugin-governance", label: "Plugin Governance" },
  { path: "/settings", label: "Settings" },
  { path: "/action-preview", label: "Action Preview" },
] as const;

export function renderRoute(path: string, data: ControlCenterData) {
  switch (path) {
    case "/chat":
      return <ChatOperatorPanel data={data} />;
    case "/plans":
      return <PlansOperatorPanel data={data} />;
    case "/models":
      return <ModelsOperatorPanel data={data} />;
    case "/runtime":
      return (
        <RuntimeReadinessPanel
          report={data.runtimeReadiness}
          matrix={data.capabilityMatrix}
        />
      );
    case "/operator-loop":
      return (
        <OperatorLoopPanel summary={data.dashboard.operator_loop_summary} />
      );
    case "/foundation-gate":
      return (
        <FoundationGatePanel summary={data.dashboard.foundation_gate_summary} />
      );
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
      return <EvidenceOperatorPanel data={data} />;
    case "/files":
      return <FileReferenceViewerPanel knowledge={data.m17Knowledge} />;
    case "/files/review":
      return <FileReviewSurfacePanel review={data.m36FileReview} />;
    case "/context/proposals":
      return (
        <ContextProposalSurfacePanel proposals={data.m39ContextProposals} />
      );
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
      return (
        <MobilePlanningPanel summary={data.dashboard.mobile_planning_summary} />
      );
    case "/plugin-governance":
      return (
        <PluginGovernancePanel
          summary={data.dashboard.plugin_governance_summary}
        />
      );
    case "/settings":
      return <SettingsOperatorPanel data={data} />;
    case "/action-preview":
      return <ActionPreviewForm />;
    case "/dashboard":
    case "/":
    default:
      return <DashboardSummary dashboard={data.dashboard} />;
  }
}
