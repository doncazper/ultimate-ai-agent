import { useCallback, useEffect, useRef, useState } from "react";
import type { BackendTruthReadBinding } from "../api/client";
import {
  commitFinance, loadFinance, prepareFinance, refreshFinance,
  type FinanceCommit, type FinanceDecision, type FinanceIntent,
  type FinanceOperation, type FinancePreparation, type FinanceView,
} from "../api/financeWorkspace";
import { useBackendTruthMutationBinding } from "../backendTruthMutationBinding";
import { AppShell } from "./AppShell";
import "./financeWorkspace.css";

const states = { needs_review: "Needs review", confirmed: "Confirmed", rejected: "Rejected", deferred: "Deferred" };
const actions: Record<FinanceOperation, string> = {
  create: "Create sample book", import_commit: "Import sample transactions",
  review_decision: "Save review decision", review_undo: "Undo review decision",
};
const decisionLabels: Record<FinanceDecision, string> = { confirm: "Confirm", reject: "Reject", defer: "Defer" };
const setupMessages: Record<FinanceView["status"], string> = {
  configuration_missing: "Finance setup is missing. Configure a private sample-book location and the pinned native key helper on this backend, then reload.",
  configuration_invalid: "Finance configuration needs attention. No sample book was opened. Check the configured private location and helper fingerprint.",
  helper_unavailable: "The native key helper is unavailable on this computer. Check the macOS helper setup; no substitute encryption or demo success is used.",
  book_setup_required: "Start with a protected sample book. Review the change before creating it on this computer.",
  ready: "Your saved sample book is open.",
  outcome_uncertain: "An interrupted save needs attention. Reading does not recover it. Review the retained action, then explicitly confirm that same action; do not create a replacement request.",
  unavailable: "The saved book could not be read safely. Check the existing book and key setup; do not overwrite it or create a replacement book.",
};

type Pending = { preparation: FinancePreparation; intent: FinanceIntent; label: string };

export function FinanceWorkspacePanel() {
  const binding = useBackendTruthMutationBinding();
  if (!binding) return <section className="panel"><h1>Finance &amp; Compliance</h1><p>Current backend identity is required before opening Finance.</p></section>;
  return <BoundFinanceWorkspacePanel key={`${binding.backendRevisionRef}:${binding.backendInstanceRef}`} binding={binding} />;
}

function BoundFinanceWorkspacePanel({ binding }: { binding: BackendTruthReadBinding }) {
  const currentBinding = useRef(binding);
  currentBinding.current = binding;
  const [workspace, setWorkspace] = useState<FinanceView | null>(null);
  const [readFailed, setReadFailed] = useState(false);
  const [selectedRef, setSelectedRef] = useState<string | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);
  const [receipt, setReceipt] = useState<FinanceCommit | null>(null);
  const [uncertain, setUncertain] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const busyRef = useRef(false);
  const generation = useRef(0);
  const mounted = useRef(false);
  const previewHeading = useRef<HTMLHeadingElement>(null);

  const reload = useCallback(async (itemOffset = 0, historyOffset = 0) => {
    const ticket = ++generation.current;
    try {
      const value = await loadFinance(currentBinding.current, itemOffset, historyOffset);
      if (!mounted.current || ticket !== generation.current) return false;
      setWorkspace(value); setReadFailed(false);
      return true;
    } catch {
      if (mounted.current && ticket === generation.current) setReadFailed(true);
      return false;
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    void reload();
    return () => { mounted.current = false; generation.current += 1; };
  }, [reload]);
  useEffect(() => { if (pending) previewHeading.current?.focus(); }, [pending]);

  const selected = workspace?.review_items.find(item => item.review_item_ref === selectedRef)
    ?? workspace?.review_items[0] ?? null;
  const blocked = busy || readFailed || workspace?.safe_disable_engaged === true;
  const canReview = workspace?.status === "ready" && !blocked && !pending;

  function begin(): boolean {
    if (busyRef.current) return false;
    busyRef.current = true; setBusy(true); setError("");
    return true;
  }
  function end() { busyRef.current = false; if (mounted.current) setBusy(false); }

  async function preview(operation: FinanceOperation, decision?: FinanceDecision) {
    if (!workspace?.configuration_ref || workspace.revision === null || blocked || pending || !begin()) return;
    const suffix = crypto.randomUUID();
    const intent: FinanceIntent = {
      operation, expected_revision: workspace.revision,
      request_ref: `request-ref:finance:ui:${suffix}`,
      idempotency_ref: `idempotency-ref:finance:ui:${suffix}`,
      ...(operation === "review_decision" || operation === "review_undo"
        ? { review_item_ref: selected?.review_item_ref } : {}),
      ...(decision ? { decision } : {}),
      ...(operation === "review_undo" && selected?.effective_decision_ref
        ? { compensates_event_ref: selected.effective_decision_ref } : {}),
    };
    try {
      const preparation = await prepareFinance(intent, workspace.configuration_ref, currentBinding.current);
      if (mounted.current) {
        setPending({ preparation, intent, label: decision ? `${decisionLabels[decision]} sample transaction ${selected?.rank}` : actions[operation] });
        setUncertain(false); setNotice("");
      }
    } catch {
      if (mounted.current) setError("A current preview could not be prepared. No save was requested. Reload and check the current book revision and setup.");
    } finally { end(); }
  }

  async function save() {
    if (!pending || busy || workspace?.safe_disable_engaged === true) return;
    if (!uncertain && Date.parse(pending.preparation.bundle.preview.expires_at) <= Date.now()) {
      setError("This preview expired before a save was requested. Close it and prepare a new preview; nothing was sent for saving.");
      return;
    }
    if (!begin()) return;
    try {
      const saved = await commitFinance(pending.preparation, currentBinding.current);
      if (!mounted.current) return;
      // Commit proof survives a failed subsequent read. Never fold both into a
      // single success/error flag or silently submit a replacement request.
      setReceipt(saved); setPending(null); setUncertain(false);
      setNotice(saved.receipt.replayed ? "The same saved action was recovered from its receipt. No duplicate change was made." : "Saved to the protected sample book.");
      if (!await reload()) setError("The save receipt is confirmed, but the refreshed view is unavailable. Keep the receipt and reload; do not repeat the action as a new request.");
    } catch {
      if (mounted.current) {
        setUncertain(true);
        setError("The save outcome is unconfirmed. Inspect saved history or retry this same reviewed action. A timeout or error does not prove that nothing changed.");
        await reload();
      }
    } finally { end(); }
  }

  async function refresh() {
    if (!pending || busy || !begin()) return;
    try {
      const preparation = await refreshFinance(pending.preparation, pending.intent, currentBinding.current);
      if (mounted.current) {
        setPending({ ...pending, preparation });
        setNotice("The same review intent has a fresh preview. Review it again and explicitly confirm; nothing was saved by refreshing.");
      }
    } catch {
      if (mounted.current) setError("The same review could not be refreshed. Preserve its identity and inspect the saved history or the Finance command-line recovery path.");
    } finally { end(); }
  }

  return <AppShell activePath="/finance" routeState={workspace && !readFailed ? {
    route: "/finance", surfaceLabel: "Finance", state: "backend_owned", statusLabel: workspace.status,
    sourceLabel: "Python Agent Core", safeSummary: "Current protected synthetic Finance read; broader runtime and production readiness are not claimed.",
    backendRouteRefs: ["GET /control-center/finance/workspace"], warningRefs: [],
    blockedAuthorityRefs: ["blocked-authority-ref:finance:real-data"], nextSafeAction: setupMessages[workspace.status],
  } : undefined}><section className="finance-workspace" aria-labelledby="finance-title">
    <header className="finance-heading">
      <div><p className="finance-eyebrow">PRIVATE WORKSPACE · SAMPLE DATA ONLY</p><h1 id="finance-title">Finance &amp; Compliance</h1><p>Review a change. Save it locally. Keep its history.</p></div>
      <button type="button" disabled={busy} onClick={() => void reload(workspace?.item_offset, workspace?.history_offset)}>Reload saved book</button>
    </header>
    <div className="finance-boundary"><strong>Synthetic-only preview program</strong><span>No real financial data, bank connection, categorization, payments or filing. Review decisions do not change accounting entries.</span></div>
    {notice ? <p role="status" className="finance-notice">{notice}</p> : null}
    {error ? <p role="alert" className="finance-error">{error}</p> : null}
    {readFailed ? <p role="alert" className="finance-error">The current book view is unavailable. Any previously shown records are stale; new changes are blocked until a successful reload.</p> : null}
    {!workspace && !readFailed ? <p role="status">Opening the protected sample book…</p> : null}
    {workspace ? <>
      {workspace.safe_disable_engaged ? <p role="alert" className="finance-error">Finance safe-disable is engaged. New saves are blocked; saved history remains inspectable.</p> : null}
      <section className="panel finance-setup" aria-labelledby="finance-book-heading">
        <div><h2 id="finance-book-heading">Sample book</h2><p>{setupMessages[workspace.status]}</p></div>
        {workspace.status === "book_setup_required" ? <button type="button" disabled={blocked || !!pending} onClick={() => void preview("create")}>Preview sample book</button> : null}
        {workspace.pending_review ? <button type="button" disabled={blocked || !!pending} onClick={() => {
          const retained = workspace.pending_review;
          if (!retained || blocked || pending) return;
          setPending({ ...retained, label: retained.intent.decision ? `Retry ${decisionLabels[retained.intent.decision]} review` : "Retry review undo" });
          setUncertain(true); setError("");
          setNotice("The exact interrupted review was read from the protected pending generation. Check it before confirming; nothing was recovered by opening this preview.");
        }}>Review interrupted save</button> : null}
        {workspace.status === "ready" ? <div className="finance-book-summary"><span>Saved revision <strong>{workspace.revision}</strong></span><span>{workspace.item_count} review items</span><span>{workspace.history_count} history entries</span>
          {workspace.import_available ? <button type="button" disabled={!canReview} onClick={() => void preview("import_commit")}>Preview sample import</button> : <span>{workspace.safe_disable_engaged ? "Sample import unavailable while safe-disable is engaged" : "Sample import recorded"}</span>}
        </div> : null}
        {["configuration_missing", "configuration_invalid", "helper_unavailable"].includes(workspace.status) ? <details><summary>Setup requirements</summary><p>The backend must have a private sample-book location and a verified macOS native key helper. Windows support is not implemented in this slice. Check the FIN-003 in-app setup guide and the Finance workspace command; this screen cannot choose a filesystem path or replace the encryption helper.</p></details> : null}
      </section>
      {workspace.status === "ready" ? <div className="finance-review-layout">
        <section className="panel" aria-labelledby="finance-review-heading"><header className="finance-section-heading"><h2 id="finance-review-heading">Transaction review</h2><span>{workspace.item_count} items</span></header>
          {workspace.review_items.length ? <ul className="finance-items">{workspace.review_items.map(item => <li key={item.review_item_ref}><button type="button" aria-pressed={selected?.review_item_ref === item.review_item_ref} disabled={busy || !!pending} onClick={() => setSelectedRef(item.review_item_ref)}><span><strong>Sample transaction {item.rank}</strong><small>Allowlisted sample import · evidence linked</small></span><span className="finance-status">{states[item.state]}</span></button></li>)}</ul> : <p>Import the sample transactions to start a review. Nothing is inferred from an empty queue.</p>}
          <div className="finance-pagination"><button type="button" disabled={busy || !!pending || workspace.item_offset === 0} onClick={() => void reload(Math.max(0, workspace.item_offset - 50), workspace.history_offset)}>Previous items</button><button type="button" disabled={busy || !!pending || workspace.item_offset + 50 >= workspace.item_count} onClick={() => void reload(workspace.item_offset + 50, workspace.history_offset)}>Next items</button></div>
        </section>
        <aside className="panel finance-inspector" aria-labelledby="finance-inspector-heading"><h2 id="finance-inspector-heading">{selected ? `Sample transaction ${selected.rank}` : "Review inspector"}</h2>
          {selected ? <><p><strong>{states[selected.state]}</strong> · Confidence not scored</p><p>Confirm acknowledges review; reject records your disposition; defer keeps follow-up open. None changes balances or categories.</p><div className="finance-actions">{(["confirm", "reject", "defer"] as const).map(decision => <button type="button" key={decision} disabled={!canReview} onClick={() => void preview("review_decision", decision)}>{decisionLabels[decision]} review</button>)}</div>
            {selected.effective_decision_ref ? <button type="button" disabled={!canReview} onClick={() => void preview("review_undo")}>Preview undo</button> : null}
            <details><summary>Evidence references</summary><dl><dt>Current review item</dt><dd>{selected.review_item_ref}</dd><dt>Source lineage</dt><dd>{selected.lineage_ref}</dd><dt>Current decision</dt><dd>{selected.effective_decision_ref ?? "No decision recorded"}</dd></dl></details>
          </> : <p>Select a sample transaction to inspect its review posture.</p>}
        </aside>
      </div> : null}
    </> : null}
    {pending ? <section className="panel finance-confirm" aria-labelledby="finance-confirm-heading"><h2 id="finance-confirm-heading" tabIndex={-1} ref={previewHeading}>Review before saving</h2><h3>{pending.label}</h3>
      <p>{pending.intent.operation === "create" ? "Creates one encrypted sample book and its native key on this computer. It does not import real data." : pending.intent.operation === "import_commit" ? "Imports only the two allowlisted synthetic transactions into this sample book. This is not a file upload or bank connection." : pending.intent.operation === "review_undo" ? "Appends a compensating history entry and restores the prior review posture. Existing history and accounting entries are retained." : "Appends this exact review disposition to local history. Accounting entries and balances remain unchanged."}</p>
      <p>Based on revision {pending.intent.expected_revision}. Ask before changes: the Python Core validates exact approval, Workspace write scope, an active lease and safe-disable before saving.</p>
      <p>Preview expires {new Date(pending.preparation.bundle.preview.expires_at).toLocaleTimeString()}.</p>
      {uncertain ? <p>Keep this exact reviewed action while its outcome is unconfirmed. Retrying does not authorize a different change.</p> : null}
      <div className="finance-actions"><button type="button" className="finance-primary" disabled={busy || workspace?.safe_disable_engaged === true} onClick={() => void save()}>{busy ? "Checking…" : uncertain ? "Retry same reviewed save" : "Confirm and save"}</button>
        {pending.intent.operation === "review_decision" || pending.intent.operation === "review_undo" ? <button type="button" disabled={busy || workspace?.safe_disable_engaged === true} onClick={() => void refresh()}>Refresh same review</button> : null}
        <button type="button" disabled={busy || uncertain} onClick={() => { setPending(null); setError(""); }}>Close preview without saving</button>
      </div><details><summary>Exact scope and preview references</summary><dl><dt>Scope</dt><dd>{pending.preparation.bundle.preview.exact_scope_ref}</dd><dt>Preview</dt><dd>{pending.preparation.bundle.preview.preview_ref}</dd><dt>Request</dt><dd>{pending.intent.request_ref}</dd></dl></details>
    </section> : null}
    {receipt ? <section className="panel finance-receipt" aria-label="Confirmed save receipt"><h2>Saved receipt</h2><p>{actions[receipt.receipt.operation]} · revision {receipt.receipt.before_revision} → {receipt.receipt.after_revision}{receipt.receipt.replayed ? " · same-action replay" : ""}</p><details><summary>Receipt reference</summary><p>{receipt.receipt.receipt_ref}</p></details></section> : null}
    {workspace?.status === "ready" ? <section className="panel finance-history" aria-labelledby="finance-history-heading"><h2 id="finance-history-heading">Saved review history</h2><p>Newest first. Undo adds an entry; it does not erase history.</p>
      {workspace.decision_history.length ? <ol>{workspace.decision_history.map(event => <li key={event.event_ref}><span>{event.operation === "review_undo" ? "Review decision undone" : `${decisionLabels[event.decision!]} review recorded`}</span><span>Revision {event.before_revision + 1}</span></li>)}</ol> : <p>No review decisions recorded yet.</p>}
      <div className="finance-pagination"><button type="button" disabled={busy || workspace.history_offset === 0} onClick={() => void reload(workspace.item_offset, Math.max(0, workspace.history_offset - 50))}>Newer history</button><button type="button" disabled={busy || workspace.history_offset + 50 >= workspace.history_count} onClick={() => void reload(workspace.item_offset, workspace.history_offset + 50)}>Older history</button></div>
    </section> : null}
    <footer className="finance-footnote"><details><summary>Authority, recovery and command-line parity</summary><p>Python owns the protected book, exact approval, active lease, idempotent receipts and undo. This screen never substitutes for those checks. After reopening, a valid interrupted review can be inspected from its encrypted pending generation and separately confirmed. If it cannot be verified, new writes stay blocked; preserve the book and inspect the Finance command-line recovery path.</p><p>Inspection: scripts/dev/uaa_finance.py workspace, including pending_review. Preview: workspace-prepare. Confirm: workspace-run --confirmed. Review retry: workspace-refresh, then separately confirm. API: /control-center/finance/workspace; preview and refresh are local-sensitive; commit requires authority. All use local_dev_workspace_only side effects and remain blocked from production.</p></details></footer>
  </section></AppShell>;
}
