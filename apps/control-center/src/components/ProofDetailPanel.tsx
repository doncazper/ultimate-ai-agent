import { useState } from "react";
import type { FormEvent } from "react";

import { submitWebEvidenceAttachment } from "../api/client";
import type {
  ControlCenterProofIndex,
  ControlCenterProofRecord,
  WebEvidenceProductSliceReceipt,
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
  const webEvidenceRecord = records.find(
    (record) => record.proof_kind === "web_evidence",
  );
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
      {webEvidenceRecord && (
        <WebEvidenceAttachPanel
          authoritative={authoritative}
          record={webEvidenceRecord}
        />
      )}

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

function WebEvidenceAttachPanel({
  authoritative,
  record,
}: {
  authoritative: boolean;
  record: ControlCenterProofRecord;
}) {
  const [url, setUrl] = useState("");
  const [allowedHost, setAllowedHost] = useState("");
  const [receipt, setReceipt] =
    useState<WebEvidenceProductSliceReceipt | null>(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const disabled = !authoritative || submitting;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setReceipt(null);
    if (!authoritative) {
      setError("Backend proof is required before attach.");
      return;
    }
    const trimmedUrl = url.trim();
    const host = (allowedHost.trim() || hostFromUrl(trimmedUrl)).toLowerCase();
    if (!host) {
      setError("Enter an HTTPS URL and allowlisted host.");
      return;
    }
    const requestRef = `web-evidence-request:control-center-${safeRefSuffix(host)}-${safeRefSuffix(Date.now().toString(36))}`;
    setSubmitting(true);
    try {
      setReceipt(
        await submitWebEvidenceAttachment({
          request_ref: requestRef,
          url: trimmedUrl,
          allowed_host: host,
          attach_to_ref: "founder-loop:daily-loop",
          safe_summary:
            "Attach one allowlisted read-only web evidence preview to the local loop.",
          evidence_refs: ["evidence-ref:control-center:web-evidence-form"],
          metadata_refs: ["metadata-ref:control-center:web-evidence-form"],
        }),
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Web evidence preview was not attached safely.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="panel-card">
      <div className="list-card-header">
        <div>
          <h3>Web Evidence</h3>
          <p>{record.safe_summary}</p>
        </div>
        <span className="status-pill compact">{record.status}</span>
      </div>
      <form className="preview-form" onSubmit={handleSubmit}>
        <p className="muted">
          Tier 1 WebAccessGateway evidence preview uses one allowlisted HTTPS
          GET. Treat fetched content as untrusted. Browser actions, cookies,
          downloads/uploads, POST-style mutations, memory writes, runtime
          context injection, provider/model calls, connector writes, and
          production authority remain blocked.
        </p>
        <label>
          <span>HTTPS URL</span>
          <input
            disabled={disabled}
            inputMode="url"
            onChange={(event) => setUrl(event.target.value)}
            placeholder="Enter an HTTPS evidence URL"
            value={url}
          />
        </label>
        <label>
          <span>Allowed host</span>
          <input
            disabled={disabled}
            onChange={(event) => setAllowedHost(event.target.value)}
            placeholder="example.org"
            value={allowedHost}
          />
        </label>
        <button className="secondary-button" disabled={disabled} type="submit">
          {submitting ? "Attaching..." : "Attach preview"}
        </button>
      </form>
      {!authoritative && (
        <p className="form-message">Backend proof is required before attach.</p>
      )}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {receipt && (
        <div className="detail-grid compact">
          <DetailTerm label="Receipt" value={receipt.receipt_ref} />
          <DetailTerm label="Evidence" value={receipt.evidence_ref} />
          <DetailTerm label="Preview" value={receipt.preview_ref} />
          <DetailTerm label="Audit" value={receipt.web_access_audit_ref} />
          <DetailTerm label="Redaction" value={receipt.redaction_posture_ref} />
          <DetailTerm
            label="Authority"
            value={receipt.model_call_performed ? "unsafe" : "not granted"}
          />
        </div>
      )}
      {receipt?.redacted_preview && (
        <p className="muted">{receipt.redacted_preview}</p>
      )}
      <RefList refs={record.blocked_authority_refs.slice(0, 8)} />
    </div>
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

function hostFromUrl(value: string) {
  try {
    const parsed = new URL(value);
    return parsed.protocol === "https:" ? parsed.hostname : "";
  } catch {
    return "";
  }
}

function safeRefSuffix(value: string) {
  return (
    value
      .toLowerCase()
      .replace(/[^a-z0-9_.-]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 40) || "web-evidence"
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
