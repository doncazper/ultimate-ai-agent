import type { ReactNode } from "react";
import { navItems } from "../routes";
import { CommandPalette } from "./CommandPalette";

interface AppShellProps {
  children: ReactNode;
  activePath: string;
}

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
        <nav>
          {navItems.map((item) => (
            <a
              aria-current={activePath === item.path ? "page" : undefined}
              className={activePath === item.path ? "active" : ""}
              href={item.path}
              key={item.path}
            >
              {item.label}
            </a>
          ))}
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
