import type { ReactNode } from "react";
import { navItems } from "../routes";

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
            <a className={activePath === item.path ? "active" : ""} href={item.path} key={item.path}>
              {item.label}
            </a>
          ))}
        </nav>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">M13 Web Control Center Shell</p>
            <h1>Read-only dashboard and preview API</h1>
          </div>
          <span className="status-pill">No authority to run actions</span>
        </header>
        <main>{children}</main>
      </div>
    </div>
  );
}
