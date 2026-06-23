import type { ReactNode } from "react";
import type { BackendConnectionSummary } from "../api/types";
import {
  primaryNavItems,
  supportingNavItems,
  type NavItem,
} from "../routes";
import { CommandPalette } from "./CommandPalette";

interface AppShellProps {
  children: ReactNode;
  activePath: string;
  connection?: BackendConnectionSummary;
}

const visibleSupportingLabels = new Set([
  "Briefing",
  "Trial Packet",
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
  const activeRoute =
    [...primaryNavItems, ...supportingNavItems].find(
      (item) => item.path === activePath,
    )?.label ?? "Control Center";

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Control Center navigation">
        <div className="window-controls" aria-hidden="true">
          <span className="window-dot red" />
          <span className="window-dot yellow" />
          <span className="window-dot green" />
        </div>
        <div className="brand">
          <span className="brand-mark">FCC</span>
          <span>
            <strong>Founder Command Center</strong>
            <small><span className="live-dot" /> Local loop active</small>
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
                <NavLink activePath={activePath} compact item={item} key={item.path} />
              ))}
            </div>
          </div>
        </nav>
        <div className="sidebar-posture" aria-label="Local safety posture">
          <PostureRow label="Privacy posture" value="Private by default" tone="green" />
          <PostureRow label="Kill-switch" value="Armed" tone="orange" />
          <PostureRow label="Local-first" value="All data stays on this Mac" tone="blue" />
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="topbar-route">
            <span className="chrome-arrow" aria-hidden="true">{"<"}</span>
            <span className="chrome-arrow" aria-hidden="true">{">"}</span>
            <strong>{activeRoute}</strong>
          </div>
          <div
            className="topbar-actions"
            aria-label="Control Center safety status"
          >
            <CommandPalette activePath={activePath} />
            <StatusChip
              tone="green"
              label="API boundary stable"
              detail={connection?.apiBaseLabel}
            />
            <StatusChip tone="blue" label="Runtime local" />
            <StatusChip tone="orange" label="No generic execution" />
            <StatusChip
              tone="green"
              label="Local task authority gated by backend approval"
            />
            <StatusChip tone="red" label="Sources 2 blocked" />
            <StatusChip tone="green" label="Evidence healthy" />
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
  const visibleLabel =
    compact && activePath === item.path ? `${item.label} navigation` : item.label;

  return (
    <a
      aria-current={activePath === item.path ? "page" : undefined}
      aria-label={item.label}
      className={className}
      href={item.path}
    >
      <span className="nav-icon" aria-hidden="true">{navIconForLabel(item.label)}</span>
      <span>{visibleLabel}</span>
      <small>{item.releaseStatus}</small>
    </a>
  );
}

function navIconForLabel(label: string): string {
  const icons: Record<string, string> = {
    Today: "TD",
    Inbox: "IN",
    Plans: "PL",
    Actions: "AC",
    Memory: "ME",
    Evidence: "EV",
    Settings: "SE",
    Briefing: "BR",
    Chat: "CH",
    Setup: "ST",
    Runtime: ">_",
  };
  return icons[label] ?? "-";
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
  return (
    <span className={`top-status-chip ${tone}`} title={detail}>
      <span className="chip-icon" aria-hidden="true" />
      {label}
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
      <span className={`posture-icon ${tone}`} aria-hidden="true" />
      <span>
        <strong>{label}</strong>
        <small>{value}</small>
      </span>
      <span className="posture-chevron" aria-hidden="true">{">"}</span>
    </div>
  );
}
