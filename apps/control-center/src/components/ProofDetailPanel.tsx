import type {
  ControlCenterProofIndex,
  ControlCenterProofRecord,
} from "../api/types";

interface ProofDetailPanelProps {
  proofIndex: ControlCenterProofIndex;
  authoritative: boolean;
}

export function ProofDetailPanel({
  authoritative,
  proofIndex,
}: ProofDetailPanelProps) {
  const records = proofIndex.records.slice(0, 12);
  const selected = records[0];
  return (
    <section className="page-section" aria-labelledby="proof-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Universal proof spine</p>
          <h2 id="proof-heading">Proof Detail</h2>
        </div>
        <span className="status-pill compact">
          {authoritative ? proofIndex.status : "mock fallback"}
        </span>
      </div>

      <div className="metric-grid">
        <MetricCard label="Proof records" value={String(proofIndex.proof_count)} />
        <MetricCard label="Source" value={proofIndex.source} />
        <MetricCard label="Runtime authority" value="not granted" />
      </div>

      {selected && <SelectedProof record={selected} />}

      <div className="stacked-list" aria-label="Proof record index">
        {records.map((record) => (
          <article className="list-card" key={record.proof_ref}>
            <div className="list-card-header">
              <div>
                <strong>{record.title}</strong>
                <p>{record.safe_summary}</p>
              </div>
              <span className="status-pill compact">{record.proof_kind}</span>
            </div>
            <div className="detail-grid compact">
              <DetailTerm label="Proof" value={record.proof_ref} />
              <DetailTerm label="Status" value={record.status} />
              <DetailTerm label="Redaction" value={record.redaction_state} />
              <DetailTerm label="Next" value={record.next_safe_action} />
            </div>
          </article>
        ))}
      </div>

      <div className="two-column-grid">
        <div className="panel-card">
          <h3>Index Routes</h3>
          <RefList refs={[proofIndex.index_route_ref, proofIndex.detail_route_ref]} />
        </div>
        <div className="panel-card">
          <h3>Still Blocked</h3>
          <RefList refs={proofIndex.blocked_authority_refs} />
        </div>
      </div>
    </section>
  );
}

function SelectedProof({ record }: { record: ControlCenterProofRecord }) {
  return (
    <div className="hero-panel">
      <div>
        <p className="eyebrow">Selected detail</p>
        <h3>{record.title}</h3>
        <p className="muted">{record.authority_posture}</p>
      </div>
      <div className="detail-grid compact">
        <DetailTerm label="Run" value={record.run_refs[0] ?? "none"} />
        <DetailTerm label="Receipt" value={record.receipt_refs[0] ?? "none"} />
        <DetailTerm label="Evidence" value={record.evidence_refs[0] ?? "none"} />
        <DetailTerm label="Approval" value={record.approval_refs[0] ?? "none"} />
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card blue">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
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

function RefList({ refs }: { refs: string[] }) {
  if (refs.length === 0) {
    return <p className="muted">none</p>;
  }
  return (
    <ul className="ref-list compact">
      {refs.slice(0, 12).map((ref) => (
        <li key={ref}>{ref}</li>
      ))}
    </ul>
  );
}

