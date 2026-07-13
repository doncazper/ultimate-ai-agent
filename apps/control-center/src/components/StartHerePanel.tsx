import type {
  AuthorityTrustMode,
  ControlCenterStartHereSummary,
} from "../api/types";

interface StartHerePanelProps {
  startHere: ControlCenterStartHereSummary;
  authoritative: boolean;
  authorityMode: AuthorityTrustMode;
  authorityModeAuthoritative: boolean;
}

export function StartHerePanel({
  authoritative,
  authorityMode,
  authorityModeAuthoritative,
  startHere,
}: StartHerePanelProps) {
  const visibleSteps = startHere.steps.slice(0, 8);
  const overviewItems = [
    ["Today", "/today", "Daily priorities and source-backed attention"],
    ["Action Inbox", "/actions", "Exact decisions and receipt posture"],
    ["Plans", "/plans", "Immutable plan and work review"],
    ["Memory", "/memory", "Review queue; recall is not truth"],
    ["Evidence", "/evidence", "Receipts and safe evidence refs"],
    ["Trust", "/trust", "AuthorityLease and blocked domains"],
  ] as const;
  return (
    <section className="page-section start-here-surface" aria-labelledby="start-here-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Local governed loop</p>
          <h2 id="start-here-heading">Start Here</h2>
        </div>
        <span className="status-pill compact">
          {authoritative ? startHere.readiness_state : "mock fallback"}
        </span>
      </div>

      <div className="start-here-dashboard-grid">
        <article className="north-star-panel start-setup-card">
          <div className="north-star-panel-header">
            <div>
              <p className="eyebrow">First-run setup</p>
              <h3>Founder Loop readiness</h3>
            </div>
            <span>{visibleSteps.length} checks</span>
          </div>
          <div className="start-check-list">
            {visibleSteps.map((step, index) => (
              <a href={safeRouteHref(step.route_ref)} key={step.step_id}>
                <span className={`start-check-dot ${statusTone(step.status)}`} />
                <small>{index + 1}</small>
                <strong>{step.label}</strong>
                <span>{humanize(step.status)}</span>
              </a>
            ))}
          </div>
        </article>

        <article className="north-star-panel start-overview-card">
          <div className="north-star-panel-header">
            <div>
              <p className="eyebrow">Overview</p>
              <h3>Founder Loop surfaces</h3>
            </div>
            <span>{authoritative ? "backend-owned" : "fallback"}</span>
          </div>
          <div className="start-overview-grid">
            {overviewItems.map(([label, href, summary]) => (
              <a href={href} key={href}>
                <strong>{label}</strong>
                <span>{summary}</span>
                <small>{authoritative ? "Ready to inspect" : "Verify backend"}</small>
              </a>
            ))}
          </div>
          <dl className="detail-list compact">
            <DetailTerm
              label="Mode"
              value={
                authoritative && authorityModeAuthoritative
                  ? humanize(authorityMode)
                  : "unverified fallback"
              }
            />
            <DetailTerm label="Runtime authority" value="not granted" />
            <DetailTerm label="Receipts" value="required" />
          </dl>
          <span className="sr-only">{startHere.local_loop_status}</span>
        </article>

        <article className="north-star-panel start-dashboard-card">
          <div className="north-star-panel-header">
            <div>
              <p className="eyebrow">Dashboard</p>
              <h3>Current route truth</h3>
            </div>
            <span>{authoritative ? "verified" : "check"}</span>
          </div>
          <p>{startHere.operator_goal}</p>
          <div className="start-next-step">
            <strong>Next safe action</strong>
            <span>{startHere.next_safe_action}</span>
          </div>
          <dl className="detail-list compact">
            <DetailTerm label="Loop" value={humanize(startHere.local_loop_status)} />
            <DetailTerm label="Run" value={startHere.primary_run_ref} />
            <DetailTerm label="Proof" value={startHere.primary_proof_ref} />
          </dl>
          {startHere.missing_prerequisite_refs.length > 0 ? (
            <div className="start-blocked-list">
              <strong>Blocked / needs attention</strong>
              <RefList refs={startHere.missing_prerequisite_refs} />
            </div>
          ) : null}
        </article>
      </div>

      <div className="start-here-proof-strip">
        <div>
          <strong>Evidence</strong>
          <RefList refs={[startHere.action_proposal_ref, ...startHere.evidence_refs]} />
        </div>
        <div>
          <strong>Authority stays bounded</strong>
          <RefList refs={startHere.blocked_authority_refs.slice(0, 4)} />
        </div>
      </div>
    </section>
  );
}

function DetailTerm({ label, value }: { label: string; value: string }) {
  return (
    <div className="detail-term">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function humanize(value: string): string {
  return value.replaceAll("_", " ");
}

function statusTone(value: string): "green" | "orange" | "red" | "gray" {
  const normalized = value.toLowerCase();
  if (
    normalized.includes("blocked") ||
    normalized.includes("error") ||
    normalized.includes("invalid") ||
    normalized.includes("missing") ||
    normalized.includes("not_ready") ||
    normalized.includes("unavailable") ||
    normalized.includes("unhealthy") ||
    normalized.includes("unknown") ||
    normalized.includes("stale")
  ) {
    return "red";
  }
  if (
    normalized.includes("ready") ||
    normalized.includes("complete") ||
    normalized.includes("done") ||
    normalized.includes("implemented") ||
    normalized.includes("healthy")
  ) {
    return "green";
  }
  if (
    normalized.includes("partial") ||
    normalized.includes("pending") ||
    normalized.includes("review")
  ) {
    return "orange";
  }
  return "gray";
}

function safeRouteHref(routeRef: string): string {
  if (START_HERE_LOCAL_ROUTES.has(routeRef)) {
    return routeRef;
  }
  return START_HERE_ROUTE_REFS[routeRef] ?? "/start";
}

const START_HERE_LOCAL_ROUTES = new Set([
  "/start",
  "/today",
  "/actions",
  "/evidence",
  "/memory",
]);

const START_HERE_ROUTE_REFS: Readonly<Record<string, string>> = {
  "route-ref:control-center:start": "/start",
  "route-ref:control-center:today": "/today",
  "route-ref:control-center:action-inbox": "/actions",
  "route-ref:control-center:actions": "/actions",
  "route-ref:control-center:decision-receipt": "/actions",
  "route-ref:control-center:evidence-timeline": "/evidence",
  "route-ref:control-center:evidence": "/evidence",
  "route-ref:control-center:memory-review": "/memory",
  "route-ref:control-center:memory": "/memory",
  "route-ref:control-center:weekly-review": "/today",
};

function RefList({ refs }: { refs: string[] }) {
  if (refs.length === 0) {
    return <p className="muted">none</p>;
  }
  return (
    <ul className="ref-list compact">
      {refs.slice(0, 10).map((ref) => (
        <li key={ref}>{ref}</li>
      ))}
    </ul>
  );
}
