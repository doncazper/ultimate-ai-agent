import type { ReactNode } from "react";
import {
  primaryNavItems,
  supportingNavItems,
  type NavGroup,
  type NavItem,
} from "../routes";
import { CommandPalette } from "./CommandPalette";

interface AppShellProps {
  children: ReactNode;
  activePath: string;
}

const supportingGroupOrder: NavGroup[] = [
  "Founder Loop",
  "Review",
  "Runtime",
  "Evidence",
  "System",
];

export function AppShell({ children, activePath }: AppShellProps) {
  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Control Center navigation">
        <div className="brand">
          <span className="brand-mark">UAA</span>
          <span>
            <strong>Control Center</strong>
            <small>read-only shell</small>
          </span>
        </div>
        <nav className="nav-stack">
          <div className="nav-section" aria-label="Primary Founder Loop">
            <p className="nav-section-label">Founder Loop</p>
            <div className="primary-nav-list">
              {primaryNavItems.map((item) => (
                <NavLink activePath={activePath} item={item} key={item.path} />
              ))}
            </div>
          </div>
          <div className="nav-section" aria-label="Supporting surfaces">
            <p className="nav-section-label">Supporting Surfaces</p>
            {supportingGroupOrder.map((group) => {
              const items = supportingNavItems.filter(
                (item) => item.group === group,
              );
              if (items.length === 0) {
                return null;
              }
              return (
                <div className="supporting-nav-group" key={group}>
                  <p className="supporting-nav-label">{group}</p>
                  <div className="supporting-nav-list">
                    {items.map((item) => (
                      <NavLink
                        activePath={activePath}
                        compact
                        item={item}
                        key={item.path}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </nav>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">current local operator shell</p>
            <h1>Governed local operator cockpit</h1>
          </div>
          <div
            className="topbar-actions"
            aria-label="Control Center safety status"
          >
            <CommandPalette activePath={activePath} />
            <span className="status-pill">Read-only</span>
            <span className="status-pill">No authority to run actions</span>
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

  return (
    <a
      aria-current={activePath === item.path ? "page" : undefined}
      aria-label={item.label}
      className={className}
      href={item.path}
    >
      <span>{item.label}</span>
      <small>{item.releaseStatus}</small>
    </a>
  );
}
