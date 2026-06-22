import type { ControlCenterData } from "./api/types";
import { ActionPreviewForm } from "./components/ActionPreviewForm";
import { ApprovalQueuePanel } from "./components/ApprovalQueuePanel";
import { ApiRouteInventoryPanel } from "./components/ApiRouteInventoryPanel";
import { ContextProposalSurfacePanel } from "./components/ContextProposalSurfacePanel";
import { DashboardSummary } from "./components/DashboardSummary";
import { DifferentiatorScreensPanel } from "./components/DifferentiatorScreensPanel";
import {
  FileReferenceViewerPanel,
} from "./components/EvidenceFileMemoryViewerPanel";
import { EventViewerPanel } from "./components/EventViewerPanel";
import { EventTimelineTracePanel } from "./components/EventTimelineTracePanel";
import { FileReviewSurfacePanel } from "./components/FileReviewSurfacePanel";
import { FoundationGatePanel } from "./components/FoundationGatePanel";
import {
  ActionInboxSurfacePanel,
  EvidenceTimelineSurfacePanel,
  FounderLoopStoragePanel,
  InboxSurfacePanel,
  MemoryReviewSurfacePanel,
  MorningBriefingPanel,
  TodaySurfacePanel,
} from "./components/FounderLoopPanels";
import {
  LocalRuntimeStatusPanel,
  ManualSmokeControlSurfacePanel,
} from "./components/LocalRuntimeStatusPanel";
import { MacOSSetupAssistantPanel } from "./components/MacOSSetupAssistantPanel";
import {
  ChatOperatorPanel,
  EvidenceOperatorPanel,
  ModelsOperatorPanel,
  PlansOperatorPanel,
  SettingsOperatorPanel,
} from "./components/OperatorFlowPanels";
import { OperatorLoopPanel } from "./components/OperatorLoopPanel";
import { PrivateOperatorTrialPanel } from "./components/PrivateOperatorTrialPanel";
import { ReceiptViewerPanel } from "./components/ReceiptViewerPanel";
import { RuntimeReadinessPanel } from "./components/RuntimeReadinessPanel";
import {
  MobilePlanningPanel,
  PluginGovernancePanel,
  RemoteWorkerSummaryPanel,
} from "./components/SummaryPanels";

export type NavGroup =
  | "Founder Loop"
  | "Review"
  | "Runtime"
  | "Evidence"
  | "System";

export type NavRole = "primary" | "supporting";

export type NavItem = {
  path: string;
  label: string;
  group: NavGroup;
  status: string;
  role: NavRole;
};

export type CommandPaletteItem = {
  id: string;
  label: string;
  group: NavGroup;
  path?: string;
  status: string;
  keywords: string[];
  disabledReason?: string;
};

export const navItems: NavItem[] = [
  { path: "/today", label: "Today", group: "Founder Loop", status: "storage-backed", role: "primary" },
  { path: "/inbox", label: "Inbox", group: "Founder Loop", status: "blocked/planned", role: "primary" },
  { path: "/plans", label: "Plans", group: "Founder Loop", status: "partial", role: "primary" },
  { path: "/actions", label: "Actions", group: "Founder Loop", status: "storage-backed", role: "primary" },
  { path: "/memory", label: "Memory", group: "Founder Loop", status: "review queue", role: "primary" },
  { path: "/evidence", label: "Evidence", group: "Founder Loop", status: "timeline", role: "primary" },
  { path: "/settings", label: "Settings", group: "Founder Loop", status: "blocked", role: "primary" },
  { path: "/briefing", label: "Briefing", group: "Founder Loop", status: "storage-backed", role: "supporting" },
  { path: "/private-trial", label: "Trial Packet", group: "Founder Loop", status: "087.2a packet", role: "supporting" },
  { path: "/operator-loop", label: "Operator Loop", group: "Review", status: "readable proof", role: "supporting" },
  { path: "/setup", label: "Setup", group: "Review", status: "dry-run", role: "supporting" },
  { path: "/chat", label: "Chat", group: "Review", status: "local gated", role: "supporting" },
  { path: "/models", label: "Models", group: "Review", status: "partial", role: "supporting" },
  { path: "/approvals", label: "Approvals", group: "Review", status: "summary", role: "supporting" },
  { path: "/files", label: "Files", group: "Review", status: "safe refs", role: "supporting" },
  { path: "/files/review", label: "File Review", group: "Review", status: "review-only", role: "supporting" },
  { path: "/context/proposals", label: "Context Proposals", group: "Review", status: "review-only", role: "supporting" },
  { path: "/action-preview", label: "Action Preview", group: "Review", status: "preview-only", role: "supporting" },
  { path: "/runtime", label: "Runtime", group: "Runtime", status: "summary", role: "supporting" },
  { path: "/storage", label: "Storage", group: "Runtime", status: "local state", role: "supporting" },
  { path: "/runtime/local", label: "Local Runtime", group: "Runtime", status: "manual", role: "supporting" },
  { path: "/runtime/manual-smoke", label: "Manual Smoke", group: "Runtime", status: "validation", role: "supporting" },
  { path: "/remote-workers", label: "Remote Workers", group: "Runtime", status: "dry-run", role: "supporting" },
  { path: "/mobile-planning", label: "Mobile Planning", group: "Runtime", status: "planned", role: "supporting" },
  { path: "/plugin-governance", label: "Plugin Governance", group: "Runtime", status: "planned", role: "supporting" },
  { path: "/foundation-gate", label: "Foundation Gate", group: "Evidence", status: "summary", role: "supporting" },
  { path: "/receipts", label: "Receipts", group: "Evidence", status: "summary", role: "supporting" },
  { path: "/events", label: "Events", group: "Evidence", status: "summary", role: "supporting" },
  { path: "/events/timeline", label: "Timeline", group: "Evidence", status: "mock", role: "supporting" },
  { path: "/", label: "Overview", group: "System", status: "read-only", role: "supporting" },
  { path: "/dashboard", label: "Dashboard", group: "System", status: "read-only", role: "supporting" },
  { path: "/api-routes", label: "API Routes", group: "System", status: "contract", role: "supporting" },
  { path: "/differentiators", label: "Differentiators", group: "System", status: "operator proof", role: "supporting" },
];

export const primaryNavItems = navItems.filter((item) => item.role === "primary");
export const supportingNavItems = navItems.filter(
  (item) => item.role === "supporting",
);

const disabledCommandItems: CommandPaletteItem[] = [
  {
    id: "action-state-change",
    label: "Action state change",
    group: "Founder Loop",
    status: "disabled",
    keywords: ["inbox", "mutation", "approval", "receipt"],
    disabledReason: "Scoped backend contract required",
  },
  {
    id: "connector-read-contracts",
    label: "Email and calendar contracts",
    group: "Founder Loop",
    status: "disabled",
    keywords: ["briefing", "connector", "calendar", "email"],
    disabledReason: "Read-only integration contracts are not scoped",
  },
  {
    id: "desktop-package-proof",
    label: "Desktop package proof",
    group: "Runtime",
    status: "planned",
    keywords: ["packaging", "desktop", "smoke", "loopback"],
    disabledReason: "Proof lane exists before distribution claims",
  },
];

export const commandPaletteItems: CommandPaletteItem[] = [
  ...navItems.map((item) => ({
    id: `route:${item.path}`,
    label: item.label,
    group: item.group,
    path: item.path,
    status: item.status,
    keywords: [item.path, item.group, item.status],
  })),
  ...disabledCommandItems,
];

export function renderRoute(path: string, data: ControlCenterData) {
  switch (path) {
    case "/today":
      return <TodaySurfacePanel today={data.founderToday} />;
    case "/inbox":
      return <InboxSurfacePanel />;
    case "/actions":
      return <ActionInboxSurfacePanel inbox={data.founderActionsInbox} />;
    case "/briefing":
      return <MorningBriefingPanel briefing={data.founderMorningBriefing} />;
    case "/private-trial":
      return <PrivateOperatorTrialPanel />;
    case "/storage":
      return <FounderLoopStoragePanel storage={data.founderStorageStatus} />;
    case "/setup":
      return <MacOSSetupAssistantPanel setup={data.macosSetupAssistant} />;
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
    case "/differentiators":
      return <DifferentiatorScreensPanel data={data} />;
    case "/approvals":
      return <ApprovalQueuePanel review={data.m15Review} />;
    case "/receipts":
      return <ReceiptViewerPanel review={data.m15Review} />;
    case "/events":
      return <EventViewerPanel review={data.m15Review} />;
    case "/events/timeline":
      return <EventTimelineTracePanel trace={data.m16Trace} />;
    case "/evidence":
      return (
        <>
          <EvidenceTimelineSurfacePanel today={data.founderToday} />
          <EvidenceOperatorPanel data={data} />
        </>
      );
    case "/files":
      return <FileReferenceViewerPanel knowledge={data.m17Knowledge} />;
    case "/files/review":
      return <FileReviewSurfacePanel review={data.m36FileReview} />;
    case "/context/proposals":
      return (
        <ContextProposalSurfacePanel proposals={data.m39ContextProposals} />
      );
    case "/memory":
      return <MemoryReviewSurfacePanel today={data.founderToday} />;
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
