import { privateOperatorTrialPacket } from "../mocks/privateOperatorTrialPacket";

export function PrivateOperatorTrialPanel() {
  const packet = privateOperatorTrialPacket;
  const counts = packet.checklistItems.reduce(
    (acc, item) => {
      acc[item.trialState] += 1;
      return acc;
    },
    { blocked: 0, needs_operator_review: 0, partial: 0, pass: 0 },
  );

  return (
    <section
      className="page-section"
      aria-labelledby="private-operator-trial-heading"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">087.2a packet</p>
          <h2 id="private-operator-trial-heading">Private Operator Trial</h2>
        </div>
        <span className="status-pill compact">local/private only</span>
      </div>
      <p className="section-copy">
        UAA-P1-087.2a prepares the local Control Center trial packet as safe
        refs: boot evidence, manual smoke checklist state, friction findings,
        UI/copy tasks, and core loop gaps. Full UAA-P1-087.2 still needs
        local/private acceptance findings.
      </p>

      <div className="metric-grid">
        <Metric label="Pass" value={counts.pass} />
        <Metric label="Partial" value={counts.partial} />
        <Metric label="Blocked" value={counts.blocked} />
        <Metric label="Review" value={counts.needs_operator_review} />
      </div>

      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Trial contract</h3>
            <span>{packet.status}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm label="Contract ref" value={packet.contractRef} />
            <DetailTerm label="Milestone" value={packet.milestoneRef} />
            <DetailTerm label="Boot command" value={packet.bootCommandRef} />
            <DetailTerm label="Scope" value={packet.trialScopeRef} />
          </dl>
          <p>{packet.nextSafeAction}</p>
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>Authority boundary</h3>
            <span>blocked</span>
          </div>
          <p>
            The packet adds no backend route, public beta, production authority,
            connector write, memory write, provider/model authority, Code apply,
            shell execution, or OpenWebUI product-state ownership.
          </p>
          <RefList refs={packet.blockedStateRefs} />
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>Evidence refs</h3>
            <span>{packet.evidenceRefs.length}</span>
          </div>
          <RefList refs={packet.evidenceRefs} />
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>UI/copy tasks</h3>
            <span>{packet.uiCopyTaskRefs.length}</span>
          </div>
          <RefList refs={packet.uiCopyTaskRefs} />
        </article>
      </div>

      <div className="review-grid">
        {packet.checklistItems.map((item) => (
          <article className="review-card" key={item.itemRef}>
            <div className="review-card-heading">
              <h3>{item.surface}</h3>
              <span>{item.trialState}</span>
            </div>
            <p>{item.safeSummary}</p>
            <dl className="detail-list">
              <DetailTerm label="Checklist ref" value={item.itemRef} />
              <DetailTerm label="Next safe action" value={item.nextSafeAction} />
            </dl>
            <RefList refs={item.evidenceRefs} />
            <RefList refs={item.frictionRefs} />
            <RefList refs={item.uiCopyTaskRefs} />
          </article>
        ))}
      </div>

      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Friction findings</h3>
            <span>{packet.frictionFindingRefs.length}</span>
          </div>
          <RefList refs={packet.frictionFindingRefs} />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Core loop gaps</h3>
            <span>{packet.coreLoopGapRefs.length}</span>
          </div>
          <RefList refs={packet.coreLoopGapRefs} />
        </article>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function DetailTerm({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  );
}

function RefList({ refs }: { refs: string[] }) {
  if (refs.length === 0) {
    return <p>No refs recorded.</p>;
  }
  return (
    <ul className="ref-list">
      {refs.map((ref) => (
        <li key={ref}>{ref}</li>
      ))}
    </ul>
  );
}
