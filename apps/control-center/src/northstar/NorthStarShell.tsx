import { useState, type ReactNode } from "react";
import type { ControlCenterData } from "../api/types";
import { Icon, Button, Badge, StatusDot } from "./primitives";
import {
  WORKSPACE_PREFIX,
  workspaceNavItems,
  workspaceSurfaceLabels,
  type WorkspaceSurfaceId,
} from "./model";

const backendRouteBySurface: Partial<Record<WorkspaceSurfaceId, string>> = {
  today: "/today",
  communications: "/inbox",
  "work-board": "/work-board",
  crm: "/crm",
  studio: "/coding",
  knowledge: "/memory",
  "activity-trust": "/trust",
  settings: "/settings",
  "developer-tools": "/runtime",
  decisions: "/actions",
  onboarding: "/setup",
};

export function NorthStarShell({
  activeSurface,
  children,
  data,
}: {
  activeSurface: WorkspaceSurfaceId;
  children: ReactNode;
  data: ControlCenterData;
}) {
  const [sidecarOpen, setSidecarOpen] = useState(() =>
    new URLSearchParams(window.location.search).get("sidecar") === "open",
  );
  const backendRoute = backendRouteBySurface[activeSurface];
  const routeState = backendRoute ? data.routeStates[backendRoute] : undefined;
  const backendReady = data.connection.state === "online" && !data.connection.usingMockData;
  const routeBacked = routeState?.state === "backend_owned";
  const previewOnly = !routeBacked;

  return (
    <div className={`ns-app ${sidecarOpen ? "sidecar-open" : ""}`}>
      <aside className="ns-sidebar" aria-label="Control Center navigation">
        <div className="ns-window-controls" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <a className="ns-brand" href={`${WORKSPACE_PREFIX}/today`}>
          <Icon name="shield-check" size={34} />
          <span>
            <strong>Control Center</strong>
            <small>Founder Command Center</small>
          </span>
        </a>
        <WorkspaceNav activeSurface={activeSurface} />
        <div className="ns-sidebar-runtime">
          <StatusDot tone={backendReady ? "green" : "orange"} />
          <span>
            <strong>{backendReady ? "Local ready" : "Preview mode"}</strong>
            <small>{backendReady ? "Backend connection verified" : "No authority inferred"}</small>
          </span>
        </div>
      </aside>

      <div className="ns-workspace">
        <GlobalPostureBar data={data} previewOnly={previewOnly} />
        {previewOnly ? (
          <div className="ns-preview-banner" role="status">
            <Icon name="info" size={15} />
            <span>
              <strong>Preview data</strong> · Pixel-accurate product surface; compatible backend contract is deferred.
            </span>
          </div>
        ) : null}
        <main className="ns-main">{children}</main>
        <ComposerRail activeSurface={activeSurface} onOpenSidecar={() => setSidecarOpen(true)} />
      </div>

      {sidecarOpen ? (
        <UaaSidecar activeSurface={activeSurface} data={data} onClose={() => setSidecarOpen(false)} />
      ) : null}
    </div>
  );
}

function WorkspaceNav({ activeSurface }: { activeSurface: WorkspaceSurfaceId }) {
  return (
    <nav className="ns-nav">
      <div className="ns-nav-group">
        {workspaceNavItems
          .filter((item) => item.section === "primary")
          .map((item) => (
            <NavItem active={activeSurface === item.id} item={item} key={item.id} />
          ))}
      </div>
      <div className="ns-nav-divider" />
      <div className="ns-nav-group">
        {workspaceNavItems
          .filter((item) => item.section === "supporting")
          .map((item) => (
            <NavItem active={activeSurface === item.id} item={item} key={item.id} />
          ))}
      </div>
      <div className="ns-nav-divider" />
      <div className="ns-nav-group utilities">
        {workspaceNavItems
          .filter((item) => item.section === "utility")
          .map((item) => (
            <NavItem active={activeSurface === item.id} item={item} key={item.id} />
          ))}
      </div>
    </nav>
  );
}

function NavItem({
  active,
  item,
}: {
  active: boolean;
  item: (typeof workspaceNavItems)[number];
}) {
  return (
    <a
      aria-current={active ? "page" : undefined}
      className={active ? "active" : ""}
      href={item.href}
      title={item.label}
    >
      <Icon name={item.icon} size={20} />
      <span>{item.label}</span>
      {item.count ? <small>{item.count}</small> : null}
    </a>
  );
}

function GlobalPostureBar({
  data,
  previewOnly,
}: {
  data: ControlCenterData;
  previewOnly: boolean;
}) {
  const backendReady = data.connection.state === "online" && !data.connection.usingMockData;
  const authorityRouteBacked = data.routeStates["/settings"]?.state === "backend_owned";
  const mode = authorityRouteBacked
    ? data.settingsStatus.authority_lease_state.active_mode.replaceAll("_", " ")
    : "Unknown in preview";
  const authorityState = data.settingsStatus.authority_lease_state;
  const activeLease = authorityRouteBacked
    ? authorityState.active_leases.find((lease) => lease.status === "active")
    : undefined;
  const gate = data.dashboard.foundation_gate_summary;

  const items = [
    { icon: "shield-check" as const, label: "Local runtime", value: backendReady ? "Ready" : "Preview", tone: backendReady ? "green" : "orange" },
    { icon: "shield" as const, label: "Authority mode", value: mode, tone: "orange" },
    { icon: "clock" as const, label: "Active lease", value: activeLease ? activeLease.mode.replaceAll("_", " ") : "No active lease", tone: activeLease ? "orange" : "blue" },
    { icon: "receipt-text" as const, label: "Receipts", value: authorityRouteBacked && authorityState.receipts_required ? "Required" : previewOnly ? "Unverified" : "Not required", tone: "blue" },
    { icon: "shield-alert" as const, label: "Foundation Gate", value: previewOnly ? "Unverified" : gate.status.replaceAll("_", " "), tone: gate.failed_count > 0 ? "orange" : "green" },
  ];
  return (
    <header className="ns-posture-bar">
      {items.map((item) => (
        <div className="ns-posture-item" key={item.label}>
          <Icon name={item.icon} size={20} tone={item.tone === "green" ? "success" : item.tone === "orange" ? "warning" : "info"} />
          <span>
            <small>{item.label}</small>
            <strong className={`tone-${item.tone}`}>{item.value}</strong>
          </span>
        </div>
      ))}
      <div className="ns-posture-item operator">
        <Icon name="user" size={20} />
        <span>
          <small>Operator</small>
          <strong>You</strong>
        </span>
      </div>
    </header>
  );
}

function ComposerRail({
  activeSurface,
  onOpenSidecar,
}: {
  activeSurface: WorkspaceSurfaceId;
  onOpenSidecar: () => void;
}) {
  return (
    <footer className="ns-composer-rail">
      <div className="ns-surface-picker" aria-label="Current surface">
        <Icon name="house" size={18} />
        <span>{workspaceSurfaceLabels[activeSurface]}</span>
      </div>
      <span className="ns-safe-ref-count">
        <Icon name="shield-check" size={17} /> 3 safe refs
      </span>
      <button className="ns-composer" onClick={onOpenSidecar} type="button">
        <Icon name="sparkles" size={18} tone="accent" />
        <span>Open UAA context for this screen</span>
        <Badge tone="blue">{workspaceSurfaceLabels[activeSurface]}</Badge>
        <span className="ns-send-button"><Icon name="external-link" size={18} /></span>
      </button>
      <div className="ns-privacy" aria-label="Privacy posture">
        <Icon name="shield-check" size={18} />
        <span>Local only · External actions blocked · Private</span>
      </div>
    </footer>
  );
}

function UaaSidecar({
  activeSurface,
  data,
  onClose,
}: {
  activeSurface: WorkspaceSurfaceId;
  data: ControlCenterData;
  onClose: () => void;
}) {
  const thread = data.founderAgentLoopThread;
  const authoritative = data.routeStates["/today"]?.state === "backend_owned" && thread.backend_owned && thread.safe_refs_only;
  const proposal = thread.proposed_actions[0];
  const refs = [...thread.evidence.evidence_refs, ...thread.evidence.proof_refs].slice(0, 3);
  return (
    <aside className="ns-sidecar" aria-label="UAA sidecar">
      <header>
        <div>
          <Icon name="sparkles" size={20} tone="accent" />
          <strong>UAA</strong>
        </div>
        <button aria-label="Close UAA sidecar" onClick={onClose} type="button">
          <Icon name="x" size={18} />
        </button>
      </header>
      <div className="ns-sidecar-context">
        <span>{workspaceSurfaceLabels[activeSurface]}</span> · <span>{authoritative ? "Backend thread" : "Preview thread"}</span> · <span>{refs.length} safe refs</span>
      </div>
      <div className="ns-sidecar-thread">
        <div className="ns-chat-bubble user">
          <small>Current request</small>
          {thread.work_request.safe_summary}
        </div>
        <div className="ns-chat-bubble assistant">
          <small>UAA</small>
          {thread.current_state.next_safe_operator_decision} No action has been taken from this sidecar.
          <div className="ns-sidecar-refs">
            <strong>Safe references</strong>
            {refs.map((ref, index) => <span key={ref} title={ref}><Icon name={index === refs.length - 1 ? "file-check-2" : "link"} size={14} /> {ref}</span>)}
            {refs.length === 0 ? <span><Icon name="info" size={14} /> No backend evidence refs reported</span> : null}
          </div>
        </div>
        <section className="ns-proposal-card">
          <header><Icon name="sparkles" size={16} /> Proposed next step</header>
          <strong>{proposal?.title ?? "No backend proposal selected"}</strong>
          <p>{proposal?.next_safe_action ?? "Proposal handoff is unavailable."}</p>
          <Badge tone={proposal?.approval_required ? "orange" : "neutral"}>{proposal?.approval_required ? "Approval required" : "Read-only"}</Badge>
          <div>
            <a className="ns-button primary" href={`${WORKSPACE_PREFIX}/decisions`}><Icon name="clipboard-check" size={16} /> Review in Action Inbox</a>
            <Button disabled title="No sidecar proposal-edit contract is connected">Edit unavailable</Button>
            <Button disabled title="No sidecar dismissal receipt contract is connected">Dismiss unavailable</Button>
          </div>
        </section>
      </div>
      <div className="ns-sidecar-prompts">
        <button disabled title="No sidecar question contract is connected" type="button">Find the source</button>
        <button disabled title="No sidecar question contract is connected" type="button">Show related work</button>
        <button disabled title="No sidecar question contract is connected" type="button">What can I safely do?</button>
      </div>
      <label className="ns-sidecar-input">
        <span className="sr-only">Ask UAA</span>
        <input disabled placeholder="Sidecar conversation contract not connected" />
        <button aria-label="Send to UAA unavailable" disabled title="No sidecar conversation contract is connected" type="button"><Icon name="send" size={17} /></button>
      </label>
    </aside>
  );
}
