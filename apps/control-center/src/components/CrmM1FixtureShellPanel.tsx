import type {
  CrmM1FixtureShell,
  CrmM1VerticalFixture,
} from "../api/types";

export function CrmM1FixtureShellPanel({
  fixture,
}: {
  fixture: CrmM1FixtureShell;
}) {
  const blockedCount = fixture.blocked_authority_refs.length;
  const verticalCount = fixture.verticals.length;

  return (
    <section
      aria-labelledby="crm-m1-fixture-heading"
      className="page-section crm-fixture-shell"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">CRM M1</p>
          <h2 id="crm-m1-fixture-heading">CRM M1 fixture-only shell</h2>
        </div>
        <span className="status-pill compact">{fixture.state}</span>
      </div>
      <p className="section-copy">
        This Control Center route shows the accepted Python-core CRM M1 fixture
        contract as screen structure only. No backend CRM read model, backend
        CRM route, connector runtime, external CRM write, send, calendar write,
        provider/model call, live web, browser automation, hidden context
        injection, public release, or production authority is available here.
      </p>

      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Fixture contract</h3>
            <span>{fixture.fixture_only ? "fixture-only" : "blocked"}</span>
          </div>
          <p>{fixture.contract_ref}</p>
          <p className="safe-ref">{fixture.control_center_route_ref}</p>
          <dl className="metric-grid">
            <Metric label="Verticals" value={String(verticalCount)} />
            <Metric
              label="Backend read model"
              value={fixture.backend_read_model_added ? "present" : "blocked"}
            />
            <Metric
              label="Backend route"
              value={fixture.backend_route_added ? "present" : "blocked"}
            />
            <Metric label="Blocked refs" value={String(blockedCount)} />
          </dl>
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>Authority boundary</h3>
            <span>blocked</span>
          </div>
          <p>No CRM write controls are available</p>
          <dl className="metric-grid">
            <Metric
              label="Connector runtime"
              value={fixture.connector_runtime_enabled ? "enabled" : "blocked"}
            />
            <Metric
              label="Account sync"
              value={fixture.account_sync_enabled ? "enabled" : "blocked"}
            />
            <Metric
              label="Sends/calendar"
              value={
                fixture.send_enabled || fixture.calendar_write_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
            <Metric
              label="Provider/model"
              value={fixture.provider_model_call_enabled ? "enabled" : "blocked"}
            />
          </dl>
        </article>
      </div>

      <div aria-label="CRM M1 vertical fixtures" className="crm-fixture-grid">
        {fixture.verticals.map((vertical) => (
          <CrmVerticalCard key={vertical.workspace_kind} vertical={vertical} />
        ))}
      </div>

      <section className="panel" aria-labelledby="crm-m1-blocked-heading">
        <div className="panel-heading">
          <h3 id="crm-m1-blocked-heading">Blocked CRM capabilities</h3>
          <span>no runtime authority</span>
        </div>
        <p>
          Missing backend/API/core execution contracts stay blocked rather than
          being faked in React state. Use the fixture refs for review only.
        </p>
        <ul className="safe-ref-list">
          {fixture.blocked_authority_refs.slice(0, 8).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </section>
    </section>
  );
}

function CrmVerticalCard({ vertical }: { vertical: CrmM1VerticalFixture }) {
  return (
    <article className="status-card crm-fixture-card">
      <div className="status-card-header">
        <h3>{vertical.safe_display_label}</h3>
        <span>{vertical.state}</span>
      </div>
      <p>
        {vertical.pipeline_lanes.length} fixture pipeline lanes,{" "}
        {vertical.work_queue_refs.length} work queue refs, and{" "}
        {vertical.screen_sections.length} screen sections.
      </p>
      <dl className="metric-grid">
        <Metric
          label="CRM writes"
          value={vertical.connector_write_enabled ? "enabled" : "blocked"}
        />
        <Metric
          label="Contact import"
          value={vertical.contact_import_enabled ? "enabled" : "blocked"}
        />
        <Metric
          label="Identity merge"
          value={vertical.silent_identity_merge_enabled ? "enabled" : "blocked"}
        />
        <Metric
          label="Live web"
          value={vertical.live_web_enabled ? "enabled" : "blocked"}
        />
      </dl>
      <div className="crm-fixture-lanes" aria-label={`${vertical.safe_display_label} lanes`}>
        {vertical.pipeline_lanes.map((lane) => (
          <span className="status-pill compact" key={lane.lane_ref}>
            {lane.safe_label}
          </span>
        ))}
      </div>
      <p className="safe-ref">{vertical.evidence_refs[0]}</p>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card" role="status">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
