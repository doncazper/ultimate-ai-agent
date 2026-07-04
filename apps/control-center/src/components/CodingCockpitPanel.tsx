import type { ReactNode } from "react";
import type {
  CodingCockpitPreviewPanel,
  CodingCockpitRefItem,
  CodingCockpitSessionReadModel,
  CodingWorkspaceContextReadModel,
} from "../api/types";
import { SafeAlert } from "./SafeAlert";

interface CodingCockpitPanelProps {
  context: CodingWorkspaceContextReadModel;
  session: CodingCockpitSessionReadModel;
  authoritative: boolean;
}

export function CodingCockpitPanel({
  authoritative,
  context,
  session,
}: CodingCockpitPanelProps) {
  const backendOwned =
    authoritative &&
    session.backend_owned &&
    !session.mock_fallback &&
    session.local_read_model_only &&
    session.safe_refs_only &&
    context.backend_owned &&
    context.read_only &&
    context.preview_only &&
    context.safe_refs_only;
  const currentAuthorityMode =
    session.authority_modes.find((mode) => mode.state === "current") ??
    session.authority_modes[0];

  return (
    <section
      className="page-section coding-cockpit"
      aria-labelledby="coding-cockpit-heading"
      data-testid="coding-cockpit"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Read-only coding command center</p>
          <h2 id="coding-cockpit-heading">Coding Cockpit</h2>
        </div>
        <span className="status-pill compact">
          {backendOwned ? session.status : "non-authoritative mock fallback"}
        </span>
      </div>

      <SafeAlert
        tone={backendOwned ? "info" : "warning"}
        title={
          backendOwned
            ? "Backend-owned coding session"
            : "Non-authoritative Coding fallback"
        }
        message={
          backendOwned
            ? "Python Core owns this read model. Control Center is rendering safe refs only and grants no mutation authority."
            : "The coding cockpit is rendering fallback data only. It is not workflow truth and no coding authority is enabled."
        }
      />

      <div className="coding-command-bar" aria-label="Coding cockpit status">
        <DetailTile label="Workspace" value={session.workspace_ref} />
        <DetailTile label="Branch" value={session.branch_label} />
        <DetailTile label="Active agent" value={session.active_agent_label} />
        <DetailTile label="Task status" value={session.task_status} />
        <label className="coding-authority-select">
          <span>Authority Mode</span>
          <select
            aria-label="Coding authority mode"
            disabled
            value={currentAuthorityMode?.label ?? session.authority_mode}
          >
            {session.authority_modes.map((mode) => (
              <option key={mode.mode_ref} value={mode.label}>
                {mode.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="coding-grid">
        <aside className="coding-pane workspace-pane" aria-label="Workspace context">
          <PanelHeader
            eyebrow="Workspace"
            title="Context"
            state={session.workspace_context.state}
          />
          <PanelBody panel={session.workspace_context} />
          <ContextPackPreview context={context} authoritative={backendOwned} />
          <RefStack title="Context refs" refs={session.same_ref_spine.slice(0, 5)} />
        </aside>

        <div className="coding-main-pane" aria-label="Task diff and proof preview">
          <PreviewPanel panel={session.task_timeline} eyebrow="Workflow" />
          <PreviewPanel panel={session.diff_preview} eyebrow="Patch preview">
            <div className="coding-action-row" aria-label="Patch actions">
              <DisabledAction label="Accept all" />
              <DisabledAction label="Accept file" />
              <DisabledAction label="Accept hunk" />
              <DisabledAction label="Apply patch" />
            </div>
          </PreviewPanel>
          <PreviewPanel panel={session.proof_preview} eyebrow="Proof" />
        </div>

        <aside className="coding-pane chat-pane" aria-label="Agent chat and task thread">
          <PanelHeader
            eyebrow="Agent thread"
            title="Chat"
            state={session.chat_thread.state}
          />
          <PanelBody panel={session.chat_thread} />
          <div className="coding-authority-stack" aria-label="Authority profiles">
            {session.authority_modes.map((mode) => (
              <article className="coding-authority-card" key={mode.mode_ref}>
                <div>
                  <strong>{mode.label}</strong>
                  <p>{mode.safe_summary}</p>
                </div>
                <span className="status-pill compact">
                  {mode.allowed_now ? "current" : mode.state.replaceAll("_", " ")}
                </span>
              </article>
            ))}
          </div>
        </aside>
      </div>

      <div className="coding-bottom-drawer" aria-label="Coding preview drawer">
        <DrawerPanel panel={session.terminal_preview} actionLabel="Run command" />
        <DrawerPanel panel={session.git_preview} actionLabel="Commit" />
        <DrawerPanel panel={session.test_output_preview} actionLabel="Run tests" />
        <DrawerPanel panel={session.live_preview} actionLabel="Open browser" />
      </div>

      <div className="coding-boundary-strip" aria-label="Blocked coding authority">
        <div>
          <strong>Blocked authority</strong>
          <span>
            File writes, shell/subprocess execution, Git mutation, provider/model
            calls, browser automation, connector writes, background autonomy, and
            production authority remain blocked.
          </span>
        </div>
        <RefStack title="Blocked refs" refs={session.blocked_authority_refs} />
      </div>
    </section>
  );
}

function ContextPackPreview({
  authoritative,
  context,
}: {
  authoritative: boolean;
  context: CodingWorkspaceContextReadModel;
}) {
  return (
    <div className="coding-context-pack" aria-label="Coding context pack preview">
      <div className="coding-context-budget">
        <DetailTile label="Context pack" value={context.context_pack_ref} />
        <DetailTile label="Budget" value={context.budget_state.replaceAll("_", " ")} />
        <DetailTile
          label="Tokens"
          value={`${context.token_estimate_total}/${context.token_budget_limit}`}
        />
      </div>
      <p className="safe-copy">
        {authoritative
          ? "Context preview is backend-owned, read-only, and safe-ref only."
          : "Context preview is non-authoritative fallback data only."}
      </p>
      <div className="coding-item-stack">
        {context.context_refs.slice(0, 4).map((item) => (
          <article className="coding-item-row" key={item.context_ref}>
            <div>
              <strong>{item.label}</strong>
              <p>{item.include_reason}</p>
            </div>
            <span className="status-pill compact">
              {item.status.replaceAll("_", " ")}
            </span>
          </article>
        ))}
      </div>
      <div className="coding-context-comparison">
        {context.comparison.map((item) => (
          <p className="safe-copy" key={item.comparison_ref}>
            {item.label}: {item.safe_summary}
          </p>
        ))}
      </div>
    </div>
  );
}

function PreviewPanel({
  children,
  eyebrow,
  panel,
}: {
  children?: ReactNode;
  eyebrow: string;
  panel: CodingCockpitPreviewPanel;
}) {
  return (
    <article className="coding-pane coding-preview-panel">
      <PanelHeader eyebrow={eyebrow} title={panel.title} state={panel.state} />
      <PanelBody panel={panel} />
      {children}
    </article>
  );
}

function DrawerPanel({
  actionLabel,
  panel,
}: {
  actionLabel: string;
  panel: CodingCockpitPreviewPanel;
}) {
  return (
    <article className="coding-drawer-panel">
      <PanelHeader eyebrow="Preview only" title={panel.title} state={panel.state} />
      <PanelBody panel={panel} compact />
      <DisabledAction label={actionLabel} />
    </article>
  );
}

function PanelHeader({
  eyebrow,
  state,
  title,
}: {
  eyebrow: string;
  state: string;
  title: string;
}) {
  return (
    <div className="coding-panel-header">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h3>{title}</h3>
      </div>
      <span className="status-pill compact">{state.replaceAll("_", " ")}</span>
    </div>
  );
}

function PanelBody({
  compact = false,
  panel,
}: {
  compact?: boolean;
  panel: CodingCockpitPreviewPanel;
}) {
  return (
    <div className={compact ? "coding-panel-body compact" : "coding-panel-body"}>
      <p className="muted">{panel.safe_summary}</p>
      <div className="coding-item-stack">
        {panel.items.map((item) => (
          <CodingItem item={item} key={item.item_ref} />
        ))}
      </div>
      <p className="safe-copy">Next safe action: {panel.next_safe_action}</p>
      <RefStack title="Proof refs" refs={panel.proof_refs} />
    </div>
  );
}

function CodingItem({ item }: { item: CodingCockpitRefItem }) {
  return (
    <article className="coding-item-row">
      <div>
        <strong>{item.label}</strong>
        <p>{item.safe_summary}</p>
      </div>
      <span className="status-pill compact">{item.status}</span>
    </article>
  );
}

function DisabledAction({ label }: { label: string }) {
  return (
    <button className="coding-disabled-action" disabled type="button">
      {label}
    </button>
  );
}

function DetailTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="coding-detail-tile">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RefStack({ refs, title }: { refs: string[]; title: string }) {
  if (refs.length === 0) {
    return null;
  }

  return (
    <div className="coding-ref-stack">
      <span>{title}</span>
      <div>
        {refs.map((ref) => (
          <code key={ref}>{ref}</code>
        ))}
      </div>
    </div>
  );
}
