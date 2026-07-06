import type {
  BackendConnectionSummary,
  ControlCenterData,
  ControlCenterRouteReadState,
} from "./api/types";
import type { RouteStateDescriptor } from "./components/DataState";
import { ActionPreviewForm } from "./components/ActionPreviewForm";
import { ApprovalQueuePanel } from "./components/ApprovalQueuePanel";
import { ApiRouteInventoryPanel } from "./components/ApiRouteInventoryPanel";
import { CodingCockpitPanel } from "./components/CodingCockpitPanel";
import { ContextProposalSurfacePanel } from "./components/ContextProposalSurfacePanel";
import { CrmM1FixtureShellPanel } from "./components/CrmM1FixtureShellPanel";
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
  FounderLoopSpinePanel,
  FounderLoopStoragePanel,
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
import { ProofDetailPanel } from "./components/ProofDetailPanel";
import { PrivateOperatorTrialPanel } from "./components/PrivateOperatorTrialPanel";
import { ReceiptViewerPanel } from "./components/ReceiptViewerPanel";
import { RuntimeReadinessPanel } from "./components/RuntimeReadinessPanel";
import { InboxSurfacePanel } from "./components/SourceInboxSurfacePanel";
import { StartHerePanel } from "./components/StartHerePanel";
import {
  MobilePlanningPanel,
  PluginGovernancePanel,
  RemoteWorkerSummaryPanel,
} from "./components/SummaryPanels";
import { TrustAuthorityPanel } from "./components/TrustAuthorityPanel";
import { WorkBoardPanel } from "./components/WorkBoardPanel";

export type NavGroup =
  | "Founder Loop"
  | "Review"
  | "Runtime"
  | "Evidence"
  | "System";

export type NavRole = "primary" | "supporting";
export type ReleaseSurfaceStatus = "ship" | "partial" | "blocked" | "experimental";

export type NavItem = {
  path: string;
  label: string;
  group: NavGroup;
  status: string;
  releaseStatus: ReleaseSurfaceStatus;
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
  { path: "/start", label: "Start Here", group: "Founder Loop", status: "backend-owned start loop", releaseStatus: "partial", role: "primary" },
  { path: "/today", label: "Today", group: "Founder Loop", status: "storage-backed", releaseStatus: "partial", role: "primary" },
  { path: "/inbox", label: "Source Inbox", group: "Founder Loop", status: "supporting source readiness", releaseStatus: "partial", role: "primary" },
  { path: "/plans", label: "Plans", group: "Founder Loop", status: "partial", releaseStatus: "partial", role: "primary" },
  { path: "/work-board", label: "Work Board", group: "Founder Loop", status: "backend-owned kanban", releaseStatus: "partial", role: "primary" },
  { path: "/actions", label: "Action Inbox", group: "Founder Loop", status: "storage-backed", releaseStatus: "ship", role: "primary" },
  { path: "/proof", label: "Proof", group: "Founder Loop", status: "backend-owned proof detail", releaseStatus: "partial", role: "primary" },
  { path: "/trust", label: "Trust", group: "Founder Loop", status: "authority map", releaseStatus: "partial", role: "primary" },
  { path: "/memory", label: "Memory", group: "Founder Loop", status: "memory diagnostics and context manifest", releaseStatus: "ship", role: "primary" },
  { path: "/evidence", label: "Evidence", group: "Founder Loop", status: "timeline", releaseStatus: "ship", role: "primary" },
  { path: "/settings", label: "Settings", group: "Founder Loop", status: "status-backed", releaseStatus: "partial", role: "primary" },
  { path: "/briefing", label: "Briefing", group: "Founder Loop", status: "storage-backed", releaseStatus: "partial", role: "supporting" },
  { path: "/crm", label: "CRM", group: "Founder Loop", status: "backend-owned local", releaseStatus: "partial", role: "supporting" },
  { path: "/private-trial", label: "Trial Packet", group: "Founder Loop", status: "087.2a-2c packet", releaseStatus: "experimental", role: "supporting" },
  { path: "/operator-loop", label: "Operator Loop", group: "Review", status: "readable proof", releaseStatus: "partial", role: "supporting" },
  { path: "/setup", label: "Setup", group: "Review", status: "dry-run", releaseStatus: "partial", role: "supporting" },
  { path: "/coding", label: "Coding", group: "Review", status: "read-only cockpit", releaseStatus: "partial", role: "supporting" },
  { path: "/chat", label: "Chat", group: "Review", status: "local gated", releaseStatus: "ship", role: "supporting" },
  { path: "/models", label: "Models", group: "Review", status: "partial", releaseStatus: "partial", role: "supporting" },
  { path: "/approvals", label: "Approvals", group: "Review", status: "summary", releaseStatus: "partial", role: "supporting" },
  { path: "/files", label: "Files", group: "Review", status: "safe refs", releaseStatus: "partial", role: "supporting" },
  { path: "/files/review", label: "File Review", group: "Review", status: "review-only", releaseStatus: "experimental", role: "supporting" },
  { path: "/context/proposals", label: "Context Proposals", group: "Review", status: "review-only", releaseStatus: "experimental", role: "supporting" },
  { path: "/action-preview", label: "Action Preview", group: "Review", status: "preview-only", releaseStatus: "experimental", role: "supporting" },
  { path: "/runtime", label: "Runtime", group: "Runtime", status: "summary", releaseStatus: "partial", role: "supporting" },
  { path: "/storage", label: "Storage", group: "Runtime", status: "local state", releaseStatus: "partial", role: "supporting" },
  { path: "/runtime/local", label: "Local Runtime", group: "Runtime", status: "manual", releaseStatus: "partial", role: "supporting" },
  { path: "/runtime/manual-smoke", label: "Manual Smoke", group: "Runtime", status: "validation", releaseStatus: "partial", role: "supporting" },
  { path: "/remote-workers", label: "Remote Workers", group: "Runtime", status: "dry-run", releaseStatus: "experimental", role: "supporting" },
  { path: "/mobile-planning", label: "Mobile Planning", group: "Runtime", status: "planned", releaseStatus: "experimental", role: "supporting" },
  { path: "/plugin-governance", label: "Plugin Governance", group: "Runtime", status: "planned", releaseStatus: "experimental", role: "supporting" },
  { path: "/foundation-gate", label: "Foundation Gate", group: "Evidence", status: "summary", releaseStatus: "partial", role: "supporting" },
  { path: "/receipts", label: "Receipts", group: "Evidence", status: "summary", releaseStatus: "partial", role: "supporting" },
  { path: "/events", label: "Events", group: "Evidence", status: "summary", releaseStatus: "partial", role: "supporting" },
  { path: "/events/timeline", label: "Timeline", group: "Evidence", status: "mock", releaseStatus: "experimental", role: "supporting" },
  { path: "/", label: "Overview", group: "System", status: "read-only", releaseStatus: "partial", role: "supporting" },
  { path: "/dashboard", label: "Dashboard", group: "System", status: "read-only", releaseStatus: "partial", role: "supporting" },
  { path: "/api-routes", label: "API Routes", group: "System", status: "contract", releaseStatus: "partial", role: "supporting" },
  { path: "/differentiators", label: "Differentiators", group: "System", status: "operator proof", releaseStatus: "partial", role: "supporting" },
];

export const primaryNavItems = navItems.filter((item) => item.role === "primary");
export const supportingNavItems = navItems.filter(
  (item) => item.role === "supporting",
);

export function getRouteSurfaceLabel(path: string): string {
  return navItems.find((item) => item.path === path)?.label ?? "Control Center";
}

export function getRouteStateDescriptor(
  path: string,
  connection?: BackendConnectionSummary,
  readState?: ControlCenterRouteReadState,
): RouteStateDescriptor {
  const item = navItems.find((candidate) => candidate.path === path);
  const surfaceLabel = readState?.surfaceLabel ?? item?.label ?? "Control Center";
  const connectionState = connection?.state ?? "checking";
  const sourceLabel = readState
    ? `Route truth: ${readState.sourceLabel}; connection: ${connectionState}.`
    : `Route truth: release surface metadata; connection: ${connectionState}.`;
  const fallbackCopy = connection?.usingMockData
    ? " Current route data includes non-authoritative mock or degraded fallback."
    : " Current route data is bounded to local backend read models and safe refs.";
  const routeProofCopy = readState
    ? ` ${readState.safeSummary} Backend route refs: ${readState.backendRouteRefs.join(", ")}.`
    : "";

  if (readState?.state === "mock_fallback") {
    return {
      kind: "partial",
      statusLabel: readState.statusLabel,
      surfaceLabel,
      title: `${surfaceLabel} is using fallback route state`,
      message:
        "The local backend contract for this route did not return authoritative route data." +
        routeProofCopy +
        fallbackCopy,
      nextSafeAction: readState.nextSafeAction,
      sourceLabel,
    };
  }

  if (readState?.state === "degraded") {
    return {
      kind: "partial",
      statusLabel: readState.statusLabel,
      surfaceLabel,
      title: `${surfaceLabel} is partially degraded`,
      message:
        "The route has backend-owned data plus missing fields or fallback sections." +
        routeProofCopy +
        fallbackCopy,
      nextSafeAction: readState.nextSafeAction,
      sourceLabel,
    };
  }

  if (readState?.state === "blocked") {
    return {
      kind: "blocked",
      statusLabel: readState.statusLabel,
      surfaceLabel,
      title: `${surfaceLabel} remains blocked`,
      message:
        "The route read state marks runtime or mutation authority as blocked." +
        routeProofCopy +
        fallbackCopy,
      nextSafeAction: readState.nextSafeAction,
      sourceLabel,
    };
  }

  if (readState?.state === "planned") {
    return {
      kind: "empty",
      statusLabel: readState.statusLabel,
      surfaceLabel,
      title: `${surfaceLabel} is planned`,
      message:
        "The route read state is visible for planning only and does not claim release-ready workflow state." +
        routeProofCopy +
        fallbackCopy,
      nextSafeAction: readState.nextSafeAction,
      sourceLabel,
    };
  }

  if (!item) {
    return {
      kind: "empty",
      statusLabel: "empty",
      surfaceLabel,
      title: "No route state record",
      message:
        "This route is not listed in the Control Center release surface metadata.",
      nextSafeAction:
        "Return to a listed Control Center route or add a backend-owned route record before claiming readiness.",
      sourceLabel,
    };
  }

  if (item.releaseStatus === "ship") {
    return {
      kind: "success",
      statusLabel: "success",
      surfaceLabel,
      title: `${item.label} has exact route proof`,
      message:
        "This route has release-surface proof metadata for its current read-only or exact-scoped contract. " +
        "It does not grant broader runtime authority." +
        routeProofCopy +
        fallbackCopy,
      nextSafeAction:
        "Inspect proof, receipts, and blocked authority refs before relying on any operator-relevant claim.",
      sourceLabel,
    };
  }

  if (item.releaseStatus === "partial") {
    return {
      kind: "partial",
      statusLabel: "partial",
      surfaceLabel,
      title: `${item.label} is partially usable`,
      message:
        "This route renders backend-owned read models where they exist and keeps missing or ungraduated authority visibly blocked." +
        routeProofCopy +
        fallbackCopy,
      nextSafeAction:
        "Use safe refs and proof links as review aids; promote missing authority through a scoped verifier-backed lane.",
      sourceLabel,
    };
  }

  if (item.releaseStatus === "blocked") {
    return {
      kind: "blocked",
      statusLabel: "blocked",
      surfaceLabel,
      title: `${item.label} remains blocked`,
      message:
        "This route can show planned, fixture, or blocker posture only; it cannot claim workflow execution or runtime authority." +
        routeProofCopy +
        fallbackCopy,
      nextSafeAction:
        "Keep the blocker visible and use the authority board before adding any mutation or external side effect.",
      sourceLabel,
    };
  }

  return {
    kind: "empty",
    statusLabel: "empty/planned",
    surfaceLabel,
    title: `${item.label} is not release-ready`,
    message:
      "This supporting route is visible for planning or review, but no release-ready workflow state is claimed." +
      routeProofCopy +
      fallbackCopy,
    nextSafeAction:
      "Add backend contracts, proof refs, visual rationale, and product-language checks before promotion.",
    sourceLabel,
  };
}

export function visibleReleaseStatus(status: ReleaseSurfaceStatus): string {
  return status === "ship" ? "exact route proof" : status;
}

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
    status: visibleReleaseStatus(item.releaseStatus),
    keywords: [
      item.path,
      item.group,
      item.status,
      visibleReleaseStatus(item.releaseStatus),
    ],
  })),
  ...disabledCommandItems,
];

export function renderRoute(path: string, data: ControlCenterData) {
  switch (path) {
    case "/start":
      return (
        <>
          <FounderLoopSpinePanel
            activeSurface="Start Here"
            actionReadModelAuthoritative={isAuthoritativeConnection(data)}
            evidence={data.founderEvidenceTimeline}
            inbox={data.founderActionsInbox}
            settingsStatus={data.settingsStatus}
            today={data.founderToday}
          />
          <StartHerePanel
            authoritative={isAuthoritativeConnection(data)}
            startHere={data.founderStartHere}
          />
        </>
      );
    case "/today":
      return (
        <>
          <TodaySurfacePanel
            actionReadModelAuthoritative={isAuthoritativeConnection(data)}
            agentLoopThread={data.founderAgentLoopThread}
            today={data.founderToday}
          />
          <FounderLoopSpinePanel
            activeSurface="Today"
            actionReadModelAuthoritative={isAuthoritativeConnection(data)}
            evidence={data.founderEvidenceTimeline}
            inbox={data.founderActionsInbox}
            settingsStatus={data.settingsStatus}
            today={data.founderToday}
          />
        </>
      );
    case "/inbox":
      return (
        <>
          <FounderLoopSpinePanel
            activeSurface="Inbox"
            actionReadModelAuthoritative={isAuthoritativeConnection(data)}
            evidence={data.founderEvidenceTimeline}
            inbox={data.founderActionsInbox}
            settingsStatus={data.settingsStatus}
            today={data.founderToday}
          />
          <InboxSurfacePanel sourceReadiness={data.founderSourceReadiness} />
        </>
      );
    case "/actions":
      return (
        <>
          <FounderLoopSpinePanel
            activeSurface="Actions"
            actionReadModelAuthoritative={isAuthoritativeConnection(data)}
            evidence={data.founderEvidenceTimeline}
            inbox={data.founderActionsInbox}
            settingsStatus={data.settingsStatus}
            today={data.founderToday}
          />
          <ActionInboxSurfacePanel
            actionReadModelAuthoritative={isAuthoritativeConnection(data)}
            approvalReview={data.runAttachedApprovalQueue}
            inbox={data.founderActionsInbox}
            providerCredentialReadiness={
              data.dashboard.provider_credential_readiness
            }
            today={data.founderToday}
          />
        </>
      );
    case "/proof":
      return (
        <>
          <FounderLoopSpinePanel
            activeSurface="Proof"
            actionReadModelAuthoritative={isAuthoritativeConnection(data)}
            evidence={data.founderEvidenceTimeline}
            inbox={data.founderActionsInbox}
            settingsStatus={data.settingsStatus}
            today={data.founderToday}
          />
          <ProofDetailPanel
            authoritative={isAuthoritativeConnection(data)}
            proofIndex={data.proofIndex}
          />
        </>
      );
    case "/trust":
      return (
        <>
          <FounderLoopSpinePanel
            activeSurface="Trust"
            actionReadModelAuthoritative={isAuthoritativeConnection(data)}
            evidence={data.founderEvidenceTimeline}
            inbox={data.founderActionsInbox}
            settingsStatus={data.settingsStatus}
            today={data.founderToday}
          />
          <TrustAuthorityPanel
            authoritative={isTrustAuthorityAuthoritative(data)}
            matrix={data.trustAuthorityMatrix}
          />
        </>
      );
    case "/briefing":
      return (
        <>
          <FounderLoopSpinePanel
            activeSurface="Briefing"
            actionReadModelAuthoritative={isAuthoritativeConnection(data)}
            evidence={data.founderEvidenceTimeline}
            inbox={data.founderActionsInbox}
            settingsStatus={data.settingsStatus}
            today={data.founderToday}
          />
          <MorningBriefingPanel briefing={data.founderMorningBriefing} />
        </>
      );
    case "/crm":
      return <CrmM1FixtureShellPanel crm={data.crmLocalCommandCenter} />;
    case "/private-trial":
      return <PrivateOperatorTrialPanel />;
    case "/storage":
      return <FounderLoopStoragePanel storage={data.founderStorageStatus} />;
    case "/setup":
      return (
        <MacOSSetupAssistantPanel
          providerCatalog={data.providerCatalog}
          providerCredentialReadiness={
            data.dashboard.provider_credential_readiness
          }
          setup={data.macosSetupAssistant}
        />
      );
    case "/coding":
      return (
        <CodingCockpitPanel
          context={data.codingContext}
          gitReview={data.codingGitReview}
          livePreview={data.codingLivePreview}
          multiAgentReview={data.codingMultiAgentReview}
          patchApplyReadiness={data.codingPatchApplyReadiness}
          patchProposal={data.codingPatchProposal}
          authoritative={isAuthoritativeConnection(data)}
          session={data.codingSession}
          testCommandReadiness={data.codingTestCommandReadiness}
        />
      );
    case "/chat":
      return <ChatOperatorPanel data={data} />;
    case "/plans":
      return (
        <>
          <FounderLoopSpinePanel
            activeSurface="Plans"
            actionReadModelAuthoritative={isAuthoritativeConnection(data)}
            evidence={data.founderEvidenceTimeline}
            inbox={data.founderActionsInbox}
            settingsStatus={data.settingsStatus}
            today={data.founderToday}
          />
          <PlansOperatorPanel data={data} />
        </>
      );
    case "/work-board":
      return (
        <WorkBoardPanel
          authoritative={isAuthoritativeConnection(data)}
          board={data.workBoard}
        />
      );
    case "/models":
      return <ModelsOperatorPanel data={data} />;
    case "/runtime":
      return (
        <RuntimeReadinessPanel
          report={data.runtimeReadiness}
          matrix={data.capabilityMatrix}
          delegationAdapter={data.runtimeDelegationAdapter}
          capabilityDiscovery={data.runtimeCapabilityDiscovery}
          runEvents={data.runtimeRunEvents}
          approvalBridge={data.runtimeApprovalBridge}
          streamingProgress={data.runtimeStreamingProgress}
          profiles={data.runtimeProfiles}
          toolRegistry={data.runtimeToolRegistry}
          virtualProviderMoa={data.runtimeVirtualProviderMoa}
          usageCostAnalytics={data.runtimeUsageCostAnalytics}
          promptStabilityTiers={data.runtimePromptStabilityTiers}
          contextBudgetPressure={data.runtimeContextBudgetPressure}
          hardlineCommandBlocklist={data.runtimeHardlineCommandBlocklist}
          managedScopePolicy={data.runtimeManagedScopePolicy}
          doctorDiagnostics={data.runtimeDoctorDiagnostics}
          sessionContinuity={data.runtimeSessionContinuity}
          mcpCatalogFiltering={data.runtimeMcpCatalogFiltering}
          backgroundJobs={data.runtimeBackgroundJobs}
          subagentIsolation={data.runtimeSubagentIsolation}
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
      return (
        <ApprovalQueuePanel
          review={data.m15Review}
          summary={data.dashboard.approval_summary}
          queue={data.runAttachedApprovalQueue}
        />
      );
    case "/receipts":
      return <ReceiptViewerPanel review={data.m15Review} />;
    case "/events":
      return <EventViewerPanel review={data.m15Review} />;
    case "/events/timeline":
      return <EventTimelineTracePanel trace={data.m16Trace} />;
    case "/evidence":
      return (
        <>
          <FounderLoopSpinePanel
            activeSurface="Evidence"
            actionReadModelAuthoritative={isAuthoritativeConnection(data)}
            evidence={data.founderEvidenceTimeline}
            inbox={data.founderActionsInbox}
            settingsStatus={data.settingsStatus}
            today={data.founderToday}
          />
          <EvidenceTimelineSurfacePanel
            evidence={data.founderEvidenceTimeline}
            runObservability={data.runObservability}
            today={data.founderToday}
          />
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
      return (
        <>
          <FounderLoopSpinePanel
            activeSurface="Memory"
            actionReadModelAuthoritative={isAuthoritativeConnection(data)}
            evidence={data.founderEvidenceTimeline}
            inbox={data.founderActionsInbox}
            settingsStatus={data.settingsStatus}
            today={data.founderToday}
          />
          <MemoryReviewSurfacePanel
            authoritative={isAuthoritativeConnection(data)}
            citationIntegrity={data.founderMemoryCitationIntegrity}
            contextPacks={data.founderMemoryContextPacks}
            contextManifest={data.founderMemoryContextManifest}
            maintenanceRuns={data.founderMemoryMaintenanceRuns}
            memoryReview={data.founderMemoryReview}
            qualityIssues={data.founderMemoryQualityIssues}
            retrievalDiagnostics={data.founderMemoryRetrievalDiagnostics}
            today={data.founderToday}
            workbench={data.founderMemoryWorkbench}
          />
        </>
      );
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
      return (
        <>
          <FounderLoopSpinePanel
            activeSurface="Settings"
            actionReadModelAuthoritative={isAuthoritativeConnection(data)}
            evidence={data.founderEvidenceTimeline}
            inbox={data.founderActionsInbox}
            settingsStatus={data.settingsStatus}
            today={data.founderToday}
          />
          <SettingsOperatorPanel data={data} />
        </>
      );
    case "/action-preview":
      return <ActionPreviewForm />;
    case "/dashboard":
    case "/":
    default:
      return <DashboardSummary dashboard={data.dashboard} />;
  }
}

function isAuthoritativeConnection(data: ControlCenterData): boolean {
  return data.connection.state === "online" && !data.connection.usingMockData;
}

function isTrustAuthorityAuthoritative(data: ControlCenterData): boolean {
  return (
    data.trustAuthorityMatrix.backend_owned === true &&
    data.trustAuthorityMatrix.local_read_model_only === true &&
    data.trustAuthorityMatrix.control_center_grants_authority === false &&
    !data.connection.warnings.includes("TRUST_AUTHORITY_MATRIX_MOCK_FALLBACK")
  );
}
