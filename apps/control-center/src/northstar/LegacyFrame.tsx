import type { ReactNode } from "react";
import type { ControlCenterData } from "../api/types";
import type { IconReference } from "../components/NorthStarIcon";
import { Badge, Button, Icon, StatusDot } from "./primitives";
import {
  legacySurfaceDefinitions,
  type LegacyNavPreset,
  type LegacySurfaceDefinition,
} from "./legacyModel";

interface LegacyNavItem {
  label: string;
  icon: IconReference;
}

const coreNav: LegacyNavItem[] = [
  { label: "Start Here", icon: "home" },
  { label: "Today", icon: "calendar-days" },
  { label: "Action Inbox", icon: "inbox" },
  { label: "Plans", icon: "clipboard-list" },
  { label: "Work Board", icon: "table-2" },
  { label: "Proof", icon: "shield-check" },
  { label: "Trust", icon: "shield" },
  { label: "Memory", icon: "brain" },
  { label: "Evidence", icon: "file-check-2" },
  { label: "Files", icon: "folder" },
  { label: "Models", icon: "box" },
  { label: "Runtime", icon: "server" },
  { label: "Remote / Plugins", icon: "workflow" },
  { label: "Operator Loop", icon: "refresh-cw" },
  { label: "Trial Packet", icon: "clipboard-check" },
  { label: "Settings", icon: "settings" },
];

const todayNav: LegacyNavItem[] = coreNav.filter((item) => [
  "Today", "Action Inbox", "Plans", "Work Board", "Proof", "Trust", "Memory", "Evidence", "Settings",
].includes(item.label));

const actionInboxNav: LegacyNavItem[] = [
  { label: "Overview", icon: "home" },
  { label: "Action Inbox", icon: "inbox" },
  { label: "Agents", icon: "bot" },
  { label: "Workspaces", icon: "folder" },
  { label: "Policies", icon: "shield" },
  { label: "Receipts", icon: "receipt-text" },
  { label: "Audit", icon: "clipboard-check" },
  { label: "Settings", icon: "settings" },
  { label: "Help", icon: "circle-help" },
];

const trustNav: LegacyNavItem[] = [
  { label: "Overview", icon: "table-2" },
  { label: "Leases", icon: "file-text" },
  { label: "Policy", icon: "shield" },
  { label: "Receipts", icon: "receipt-text" },
  { label: "Audit", icon: "clock" },
  { label: "Agents", icon: "users" },
  { label: "Domains", icon: "network" },
  { label: "Rules", icon: "database" },
  { label: "Settings", icon: "settings" },
];

const settingsNav: LegacyNavItem[] = [
  ...coreNav.filter((item) => [
    "Today", "Action Inbox", "Plans", "Work Board", "Proof", "Trust", "Memory", "Evidence",
  ].includes(item.label)),
  { label: "Chat", icon: "message-square" },
  { label: "Coding", icon: "code-2" },
  { label: "Source Inbox", icon: "mail" },
  { label: "CRM", icon: "users" },
  { label: "Morning Briefing", icon: "cloud-sun" },
  { label: "Settings", icon: "settings" },
];

const operatorLoopNav: LegacyNavItem[] = coreNav.filter((item) => [
  "Today", "Action Inbox", "Plans", "Work Board", "Proof", "Trust", "Memory", "Evidence", "Operator Loop", "Settings",
].includes(item.label));

const coreNavPaths: Record<string, string> = {
  "Start Here": "/workspace/reference/11-start-overview",
  Today: "/workspace/reference/01-today",
  "Action Inbox": "/workspace/reference/02-action-inbox",
  Plans: "/workspace/reference/03-plans-work-board",
  "Work Board": "/workspace/reference/03-plans-work-board",
  Proof: "/workspace/reference/05-evidence-proof",
  Trust: "/workspace/reference/04-trust",
  Memory: "/workspace/reference/06-memory",
  Evidence: "/workspace/reference/05-evidence-proof",
  Files: "/workspace/reference/14-files-context",
  Models: "/workspace/reference/13-models",
  Runtime: "/workspace/reference/16-runtime-storage",
  "Remote / Plugins": "/workspace/reference/17-future-governance",
  "Operator Loop": "/workspace/reference/19-operator-loop",
  "Trial Packet": "/workspace/reference/18-private-trial",
  Settings: "/workspace/reference/12-settings-authority",
  Overview: "/workspace/reference/11-start-overview",
  Agents: "/workspace/reference/08-coding",
  Workspaces: "/workspace/reference/03-plans-work-board",
  Policies: "/workspace/reference/04-trust",
  Receipts: "/workspace/reference/05-evidence-proof",
  Audit: "/workspace/reference/05-evidence-proof",
  Help: "/workspace/reference/11-start-overview",
  Leases: "/workspace/reference/04-trust",
  Policy: "/workspace/reference/04-trust",
  Domains: "/workspace/reference/04-trust",
  Rules: "/workspace/reference/04-trust",
  Chat: "/workspace/reference/10-chat-handoff",
  Coding: "/workspace/reference/08-coding",
  "Source Inbox": "/workspace/reference/09-sources-crm-briefing",
  CRM: "/workspace/reference/09-sources-crm-briefing",
  "Morning Briefing": "/workspace/reference/09-sources-crm-briefing",
};

const presetNav: Record<Exclude<LegacyNavPreset, "core">, LegacyNavItem[]> = {
  setup: [
    { label: "Setup", icon: "settings" },
    { label: "Runtime health", icon: "heart-pulse" },
    { label: "Local model readiness", icon: "box" },
    { label: "Model selection", icon: "list-filter" },
    { label: "Setup questions", icon: "circle-help" },
    { label: "Approvals", icon: "shield-check" },
    { label: "Receipts / audit", icon: "receipt-text" },
  ],
  coding: [
    { label: "Cockpit", icon: "code-2" },
    { label: "Work threads", icon: "workflow" },
    { label: "Proposals", icon: "file-text" },
    { label: "Receipts", icon: "receipt-text" },
    { label: "Foundation Gate", icon: "shield-check" },
    { label: "Policy", icon: "shield" },
    { label: "Runtime", icon: "server" },
    { label: "Audit log", icon: "clock" },
    { label: "Settings", icon: "settings" },
  ],
  sources: [
    { label: "Source Inbox", icon: "mail" },
    { label: "CRM", icon: "users" },
    { label: "Morning Briefing", icon: "cloud-sun" },
    { label: "Memory", icon: "brain" },
    { label: "Tasks", icon: "list-todo" },
    { label: "Settings", icon: "settings" },
  ],
  chat: [
    { label: "Chat", icon: "message-square" },
    { label: "Handoffs", icon: "forward" },
    { label: "Memory", icon: "brain" },
    { label: "Evidence", icon: "file-check-2" },
    { label: "Tools", icon: "wrench" },
    { label: "Settings", icon: "settings" },
  ],
};

export function LegacyFrame({
  children,
  data,
  definition,
}: {
  children: ReactNode;
  data: ControlCenterData;
  definition: LegacySurfaceDefinition;
}) {
  const nav = navigationFor(definition);
  const backendReady = data.connection.state === "online" && !data.connection.usingMockData;
  const index = legacySurfaceDefinitions.findIndex((item) => item.id === definition.id);
  const previous = legacySurfaceDefinitions[index - 1];
  const next = legacySurfaceDefinitions[index + 1];
  const postureItems = postureItemsFor(definition);

  return (
    <div className="legacy-app" data-surface={definition.id}>
      <aside className="legacy-sidebar" aria-label="Reference surface navigation">
        <div className="legacy-window-controls" aria-hidden="true"><span /><span /><span /></div>
        <a className="legacy-brand" href="/workspace/today">
          <Icon name="shield-check" size={30} />
          <span><strong>Control Center</strong><small>Founder Loop</small></span>
        </a>
        <nav>
          {nav.map((item) => (
            <a
              className={item.label === definition.activeNav ? "active" : ""}
              href={coreNavPaths[item.label]
                ?? legacySurfaceDefinitions.find((surface) => surface.activeNav === item.label)?.path
                ?? definition.path}
              key={item.label}
            >
              <Icon name={item.icon} size={18} /><span>{item.label}</span>
              {item.label === "Action Inbox" ? <small>8</small> : null}
            </a>
          ))}
        </nav>
        <div className="legacy-sidebar-status">
          <StatusDot tone={backendReady ? "green" : "orange"} />
          <span><strong>{backendReady ? "Local runtime" : "Preview mode"}</strong><small>{backendReady ? "Connection verified" : "No backend inferred"}</small></span>
        </div>
      </aside>

      <section className="legacy-workspace">
        <header className="legacy-posture-bar">
          {postureItems.map((item) => <div key={item.label}><Icon name={item.icon} size={22} tone={item.tone} /><span><small>{item.label}</small><strong>{item.value}</strong></span></div>)}
          <div className="legacy-operator"><Icon name="user" size={20} /><span><small>Operator</small><strong>You</strong></span></div>
        </header>
        <div className="legacy-preview-strip" role="status">
          <span><strong>Reference build {String(definition.number).padStart(2, "0")}/19</strong> · Preview fixtures · No action authority</span>
          <Badge tone="orange">Not backend-wired</Badge>
        </div>
        <main className="legacy-main">
          <fieldset className="legacy-preview-controls" disabled>
            <legend className="legacy-sr-only">
              Preview controls are disabled until the owning backend contract is wired.
            </legend>
            {children}
          </fieldset>
        </main>
        <footer className="legacy-footer">
          <span><Icon name="lock" size={15} /> Local presentation only · external actions blocked</span>
          <div>
            {previous ? <a href={previous.path}><Icon name="chevron-left" size={14} /> {previous.label}</a> : <span />}
            <a href="/workspace/today">Current surfaces</a>
            {next ? <a href={next.path}>{next.label} <Icon name="chevron-right" size={14} /></a> : <span />}
          </div>
        </footer>
      </section>
    </div>
  );
}

function navigationFor(definition: LegacySurfaceDefinition): LegacyNavItem[] {
  if (definition.id === "01-today") return todayNav;
  if (definition.id === "02-action-inbox") return actionInboxNav;
  if (definition.id === "04-trust") return trustNav;
  if (definition.id === "12-settings-authority") return settingsNav;
  if (definition.id === "19-operator-loop") return operatorLoopNav;
  return definition.navPreset === "core" ? coreNav : presetNav[definition.navPreset];
}

function postureItemsFor(definition: LegacySurfaceDefinition): Array<{ icon: IconReference; label: string; tone: "info" | "success" | "warning" | "danger"; value: string }> {
  if (definition.id === "08-coding") return [
    { icon: "layers-3", label: "Repo / branch", tone: "info", value: "acme-app · feature/checkout-fixes" },
    { icon: "folder", label: "Worktree", tone: "info", value: "wt/agent-42" },
    { icon: "shield-check", label: "Authority mode", tone: "warning", value: "Governed · approval required" },
    { icon: "cpu", label: "Runtime profile", tone: "success", value: "Local · no network" },
  ];
  if (definition.id === "07-setup") return [
    { icon: "network", label: "Local API", tone: "success", value: "Connected" },
    { icon: "server", label: "Launcher", tone: "success", value: "Running" },
    { icon: "shield-check", label: "Security posture", tone: "warning", value: "Partial" },
    { icon: "database", label: "Model availability", tone: "warning", value: "3 local · 1 missing" },
  ];
  if (definition.id === "09-sources-crm-briefing") return [
    { icon: "shield", label: "Authority", tone: "info", value: "Read-only sources · no writes" },
    { icon: "calendar", label: "Briefing date", tone: "info", value: "May 23, 2025" },
    { icon: "target", label: "Focus", tone: "info", value: "Revenue · Key Accounts · Risks" },
    { icon: "clock", label: "Timebox", tone: "info", value: "30 min prep" },
  ];
  if (definition.id === "10-chat-handoff") return [
    { icon: "server", label: "Runtime profile", tone: "success", value: "Local runtime" },
    { icon: "shield", label: "Authority mode", tone: "warning", value: "No provider authority" },
    { icon: "box", label: "Model status", tone: "success", value: "Local model ready" },
    { icon: "ban", label: "Tool denial truth", tone: "danger", value: "External actions denied" },
  ];
  if (definition.id === "04-trust") return [
    { icon: "shield", label: "Active mode", tone: "info", value: "Delegated mission" },
    { icon: "octagon-alert", label: "Kill switch", tone: "danger", value: "Operator control" },
    { icon: "clock", label: "Active lease", tone: "info", value: "01:42:37 remaining" },
    { icon: "receipt-text", label: "Receipts required", tone: "success", value: "All receipts verified" },
  ];
  return [
    { icon: definition.icon, label: "Surface", tone: "info", value: definition.label },
    { icon: "shield", label: "Authority mode", tone: "warning", value: "Ask before changes" },
    { icon: "fingerprint", label: "Safe refs", tone: "success", value: "Available" },
    { icon: "shield-check", label: "Foundation Gate", tone: "success", value: "Cautious" },
  ];
}

export function LegacySurfaceHeader({
  actions,
  definition,
}: {
  actions?: ReactNode;
  definition: LegacySurfaceDefinition;
}) {
  return (
    <header className="legacy-surface-header">
      <div><Icon name={definition.icon} size={23} /><span><h1>{definition.title}</h1><p>{definition.subtitle}</p></span></div>
      <div>{actions ?? <Button icon="refresh-cw">Refresh preview</Button>}</div>
    </header>
  );
}
