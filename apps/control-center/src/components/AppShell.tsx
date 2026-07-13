import type { ReactNode } from "react";
import type {
  AuthorityTrustMode,
  BackendConnectionSummary,
  ControlCenterRouteReadState,
} from "../api/types";
import {
  primaryNavItems,
  supportingNavItems,
  type NavItem,
  visibleReleaseStatus,
} from "../routes";
import { CommandPalette } from "./CommandPalette";
import { NorthStarIcon } from "./NorthStarIcon";

interface AppShellProps {
  children: ReactNode;
  activePath: string;
  authorityMode?: AuthorityTrustMode;
  authorityModeAuthoritative?: boolean;
  connection?: BackendConnectionSummary;
  killSwitchEngaged?: boolean;
  killSwitchVisible?: boolean;
  routeState?: ControlCenterRouteReadState;
}

const visibleSupportingLabels = new Set([
  "CRM",
  "Trial Packet",
  "Source Inbox",
  "Operator Loop",
  "Setup",
  "Chat",
  "Coding",
  "Briefing",
  "Action Preview",
  "Runtime",
  "Foundation Gate",
  "Overview",
  "Dashboard",
  "API Routes",
  "Differentiators",
]);

export function AppShell({
  activePath,
  authorityMode,
  authorityModeAuthoritative = false,
  children,
  connection,
  killSwitchEngaged = false,
  killSwitchVisible = false,
  routeState,
}: AppShellProps) {
  const visiblePrimaryLabels = new Set([
    "Start Here",
    "Today",
    "Source Inbox",
    "Plans",
    "Work Board",
    "Action Inbox",
    "Proof",
    "Trust",
    "Memory",
    "Evidence",
    "Settings",
  ]);
  const primaryItems = primaryNavItems.filter((item) =>
    visiblePrimaryLabels.has(item.label),
  );
  const supportingItems = supportingNavItems.filter((item) =>
    visibleSupportingLabels.has(item.label),
  );
  const activeRouteLabel =
    [...primaryNavItems, ...supportingNavItems].find(
      (item) => item.path === activePath,
    )?.label ?? "Control Center";
  const activeRoute =
    activePath === "/actions"
      ? "Action Inbox"
      : activePath === "/inbox"
        ? "Source Inbox"
      : activePath === "/setup"
        ? "Setup Assistant"
        : activePath === "/api-routes"
          ? "Route Inventory"
          : activeRouteLabel;
  const backendAuthoritative =
    connection?.state === "online" && connection.usingMockData === false;
  const routeAuthoritative = routeState?.state === "backend_owned";
  const backendUnavailable =
    connection?.state === "mock_fallback" || connection?.usingMockData === true;
  const backendDegraded = connection?.state === "degraded";
  const loopStatusLabel = backendAuthoritative
    ? "Repo-safe local loop active"
    : routeAuthoritative
      ? "Current route is backend-owned"
    : backendDegraded
      ? "Backend degraded; verify refs"
      : backendUnavailable
        ? "Mock fallback; non-authoritative"
        : "Backend state unverified";
  const apiBoundaryLabel = backendAuthoritative
    ? "API boundary route-verified"
    : "API boundary unverified";
  const apiBoundaryTone = backendAuthoritative
    ? "green"
    : backendDegraded
      ? "orange"
      : "blue";
  const evidenceLabel = backendAuthoritative
    ? "Evidence refs available"
    : "Evidence refs unverified";
  const routeTruthLabel = routeAuthoritative
    ? "Backend-owned route read model"
    : backendAuthoritative
      ? "Backend-connected operator view"
      : backendDegraded
        ? "Backend degraded · verify exact refs"
        : backendUnavailable
          ? "Mock fallback · non-authoritative"
          : "Backend ownership unverified";
  const authorityModeLabel =
    authorityModeAuthoritative && authorityMode
      ? `Mode: ${humanize(authorityMode)}`
      : "Authority mode unknown";
  const killSwitchStatus = authorityModeAuthoritative
    ? killSwitchEngaged
      ? "engaged"
      : killSwitchVisible
        ? "available"
        : "not visible"
    : "unverified in fallback";

  const surfaceClass = `surface-${activePath.replace(/^\//, "").replaceAll("/", "-") || "overview"}`;

  return (
    <div className={`app-shell ${surfaceClass}`}>
      <aside className="sidebar" aria-label="Control Center navigation">
        <div className="window-controls" aria-hidden="true">
          <span className="window-dot red" />
          <span className="window-dot yellow" />
          <span className="window-dot green" />
        </div>
        <div className="brand">
          <span className="brand-mark">U</span>
          <span>
            <strong>AI Agent Control Center</strong>
            <small>Founder Loop</small>
          </span>
        </div>
        <nav className="nav-stack">
          <div className="nav-section" aria-label="Primary Founder Loop">
            <div className="primary-nav-list">
              {primaryItems.map((item) => (
                <NavLink activePath={activePath} item={item} key={item.path} />
              ))}
            </div>
          </div>
          <div className="nav-section" aria-label="Supporting surfaces">
            <p className="nav-section-label">Supporting Surfaces</p>
            <div className="supporting-nav-list">
              {supportingItems.map((item) => (
                <NavLink
                  activePath={activePath}
                  compact
                  item={item}
                  key={item.path}
                />
              ))}
            </div>
          </div>
        </nav>
        <div className="sidebar-runtime" aria-label="Local runtime posture">
          <span className={`runtime-orb ${backendAuthoritative ? "online" : "check"}`} />
          <span>
            <strong>{routeAuthoritative ? "Local route ready" : backendAuthoritative ? "Local runtime" : "Runtime check"}</strong>
            <small>{loopStatusLabel}</small>
          </span>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="topbar-route" aria-label="Current surface">
            <strong>{activeRoute}</strong>
            <small>{routeTruthLabel}</small>
            <div className="topbar-safety-floor" aria-label="Visible safety floor">
              <span>No generic execution</span>
              <span>Local task authority requires backend approval</span>
              <span>Sources blocked/status-only</span>
              {!authorityModeAuthoritative ? (
                <span>Unverified in fallback</span>
              ) : null}
              <span>
                <span>Kill-switch posture</span>: {killSwitchStatus}
              </span>
            </div>
          </div>
          <div className="topbar-postures" aria-label="Control Center safety status">
            <StatusChip
              tone={routeAuthoritative || backendAuthoritative ? "green" : "orange"}
              label={routeAuthoritative ? "Route backed" : backendAuthoritative ? "Local runtime" : "Runtime check"}
              detail={connection?.safeMessage}
            />
            <StatusChip
              tone={authorityModeAuthoritative ? "blue" : "orange"}
              label={authorityModeLabel}
            />
            <StatusChip
              tone={backendAuthoritative ? "green" : "blue"}
              label={evidenceLabel}
            />
            <StatusChip tone={apiBoundaryTone} label={apiBoundaryLabel} />
            <CommandPalette activePath={activePath} />
          </div>
        </header>
        <main className="app-main">{children}</main>
      </div>
    </div>
  );
}

function humanize(value: string): string {
  return value.replaceAll("_", " ");
}

function NavLink({
  activePath,
  compact = false,
  item,
}: {
  activePath: string;
  compact?: boolean;
  item: NavItem;
}) {
  const className = [
    activePath === item.path ? "active" : "",
    compact ? "compact" : "",
  ]
    .filter(Boolean)
    .join(" ");
  const visibleLabel = item.label;
  const releaseStatusLabel = visibleReleaseStatus(item.releaseStatus);

  return (
    <a
      aria-current={activePath === item.path ? "page" : undefined}
      aria-label={item.label}
      className={className}
      href={item.path}
    >
      <span className="nav-icon" aria-hidden="true">
        <NorthStarIcon name={navIconForLabel(item.label)} />
      </span>
      <span>{visibleLabel}</span>
      <small>{releaseStatusLabel}</small>
    </a>
  );
}

function navIconForLabel(label: string): string {
  const icons: Record<string, string> = {
    Today: "sun",
    Inbox: "inbox",
    "Source Inbox": "inbox",
    Plans: "list",
    "Work Board": "clipboard",
    Actions: "check-circle",
    "Action Inbox": "check-circle",
    Memory: "brain",
    Evidence: "file-text",
    Settings: "settings",
    Briefing: "map",
    CRM: "briefcase",
    Chat: "chat",
    Setup: "sliders",
    Runtime: "terminal",
  };
  return icons[label] ?? "file";
}

function StatusChip({
  detail,
  label,
  tone,
}: {
  detail?: string;
  label: string;
  tone: "green" | "blue" | "red" | "orange";
}) {
  const icon = label.includes("Evidence")
    ? "heart"
    : label.includes("Runtime")
      ? "cube"
      : label.includes("Sources")
        ? "shield"
        : "shield-check";
  return (
    <span className={`top-status-chip ${tone}`} title={detail}>
      <NorthStarIcon className="chip-icon" name={icon} />
      <span className="top-status-chip-label">{label}</span>
    </span>
  );
}
