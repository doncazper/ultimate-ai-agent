import type { ReactNode } from "react";
import type { BackendConnectionSummary } from "../api/types";
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
  connection?: BackendConnectionSummary;
}

const visibleSupportingLabels = new Set([
  "Briefing",
  "CRM",
  "Trial Packet",
  "Source Inbox",
  "Operator Loop",
  "Setup",
  "Chat",
  "Action Preview",
  "Runtime",
  "Foundation Gate",
  "Overview",
  "Dashboard",
  "API Routes",
  "Differentiators",
]);

export function AppShell({ children, activePath, connection }: AppShellProps) {
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
  const backendUnavailable =
    connection?.state === "mock_fallback" || connection?.usingMockData === true;
  const backendDegraded = connection?.state === "degraded";
  const loopStatusLabel = backendAuthoritative
    ? "Repo-safe local loop active"
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
  const runtimeLabel = "Runtime status-only";
  const sourcesLabel = "Sources blocked/status-only";
  const killSwitchPosture = backendAuthoritative
    ? "Backend status visible"
    : "Unverified in fallback";
  const actionAuthorityLabel = backendAuthoritative
    ? "No generic execution; no authority to run actions outside local task"
    : "No generic execution; no authority to run actions without backend approval";
  const localTaskAuthorityLabel = backendAuthoritative
    ? "Local task authority gated by backend approval"
    : "Local task authority requires backend approval";

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Control Center navigation">
        <div className="window-controls" aria-hidden="true">
          <span className="window-dot red" />
          <span className="window-dot yellow" />
          <span className="window-dot green" />
        </div>
        <div className="brand">
          <span className="brand-mark">CC</span>
          <span>
            <strong>Control Center</strong>
            <small><span className="live-dot" /> {loopStatusLabel}</small>
          </span>
        </div>
        <nav className="nav-stack">
          <div className="nav-section" aria-label="Primary Founder Loop">
            <div className="primary-nav-list">
              {primaryNavItems.map((item) => (
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
        <div className="sidebar-posture" aria-label="Local safety posture">
          <PostureRow label="Privacy posture" value="Private by default" tone="green" />
          <PostureRow
            label="Kill-switch posture"
            value={killSwitchPosture}
            tone="orange"
          />
          <PostureRow label="Local-first" value="Status + exact backend lanes" tone="blue" />
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="topbar-title-block">
            <div className="topbar-title-row">
              <h1>Control Center</h1>
              <span>Founder Loop</span>
              <span>Operator Shell</span>
              <span>Backend Truth</span>
              <span>Safety First</span>
            </div>
            <p>
              Operate with facts. Act with confidence. Every item shows why,
              what it affects, and backend evidence.
            </p>
            <div className="topbar-route" aria-label="Current surface">
              <NorthStarIcon className="chrome-arrow" name="chevron-left" />
              <NorthStarIcon className="chrome-arrow" name="chevron-right" />
              <strong>{activeRoute}</strong>
            </div>
          </div>
          <div
            className="topbar-actions"
            aria-label="Control Center safety status"
          >
            <div className="authority-legend" aria-label="Operator state legend">
              <LegendItem
                detail="Requires your action"
                label="Blocked"
                tone="red"
              />
              <LegendItem
                detail="No receipt yet"
                label="Proposal Only"
                tone="orange"
              />
              <LegendItem
                detail="Verified by source"
                label="Receipt-Backed"
                tone="green"
              />
              <LegendItem detail="Read-only" label="Info Only" tone="gray" />
            </div>
            <div className="topbar-control-row">
              <CommandPalette activePath={activePath} />
              <StatusChip
                tone={apiBoundaryTone}
                label={apiBoundaryLabel}
                detail={connection?.apiBaseLabel}
              />
            </div>
            <div className="topbar-status-strip" aria-label="Backend boundary summary">
              <StatusChip tone="blue" label={runtimeLabel} />
              <StatusChip tone="red" label={sourcesLabel} />
              <StatusChip
                tone={backendAuthoritative ? "green" : "blue"}
                label={evidenceLabel}
              />
              <StatusChip tone="orange" label={actionAuthorityLabel} />
              <StatusChip
                tone={backendAuthoritative ? "green" : "orange"}
                label={localTaskAuthorityLabel}
              />
            </div>
          </div>
        </header>
        <main>{children}</main>
      </div>
    </div>
  );
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

function LegendItem({
  detail,
  label,
  tone,
}: {
  detail: string;
  label: string;
  tone: "green" | "gray" | "orange" | "red";
}) {
  return (
    <span className="legend-item">
      <span className={`legend-swatch ${tone}`} aria-hidden="true" />
      <span>
        <strong>{label}</strong>
        <small>{detail}</small>
      </span>
    </span>
  );
}

function PostureRow({
  label,
  tone,
  value,
}: {
  label: string;
  tone: "green" | "blue" | "orange";
  value: string;
}) {
  return (
    <div className="posture-row">
      <NorthStarIcon
        className={`posture-icon ${tone}`}
        name={
          label.includes("Privacy")
            ? "lock"
            : label.includes("Kill")
              ? "shield"
              : "database"
        }
      />
      <span>
        <strong>{label}</strong>
        <small>{value}</small>
      </span>
      <NorthStarIcon
        className="posture-chevron"
        name="chevron-right"
      />
    </div>
  );
}
