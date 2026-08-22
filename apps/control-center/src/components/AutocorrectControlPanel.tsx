import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  fetchAutocorrectStatus,
  submitAutocorrectProposalPreview,
  submitAutocorrectReviewPreview,
} from "../api/client";
import { containsSecretLike, sanitizeForDisplay } from "../api/redaction";
import type {
  AutocorrectControlStatus,
  AutocorrectOwner,
  AutocorrectProposal,
  AutocorrectProposalRequest,
  AutocorrectReviewReceipt,
  AutocorrectReviewRequest,
  AutocorrectTargetKind,
} from "../api/types";
import { SafeAlert } from "./SafeAlert";

const targetOptions: Array<{
  label: string;
  kind: AutocorrectTargetKind;
  owner: AutocorrectOwner;
}> = [
  { label: "Task", kind: "task", owner: "tasks" },
  { label: "Task occurrence", kind: "task_occurrence", owner: "tasks" },
  { label: "Board", kind: "board", owner: "boards" },
  { label: "Board template", kind: "board_template", owner: "boards" },
  { label: "Calendar set", kind: "calendar_set", owner: "calendar" },
];

const initialForm = {
  workspaceRef: "workspace-ref:local",
  sourceProposalRef: "proposal-ref:reviewed-candidate",
  targetKind: "task" as AutocorrectTargetKind,
  targetRef: "task-ref:review-target",
  expectedRevisionRef: "revision-ref:target:1",
  currentRevisionRef: "revision-ref:target:1",
  fieldRef: "field-ref:title",
  beforeFingerprintRef: "fingerprint-ref:before",
  afterFingerprintRef: "fingerprint-ref:after",
  evidenceRef: "evidence-ref:review-source",
  reasonRef: "reason-ref:operator-correction",
  confidencePercent: 88,
};

export function AutocorrectControlPanel() {
  const [form, setForm] = useState(initialForm);
  const [status, setStatus] = useState<AutocorrectControlStatus | null>(null);
  const [proposalRequest, setProposalRequest] =
    useState<AutocorrectProposalRequest | null>(null);
  const [proposal, setProposal] = useState<AutocorrectProposal | null>(null);
  const [receipt, setReceipt] = useState<AutocorrectReviewReceipt | null>(null);
  const [supersedingProposalRef, setSupersedingProposalRef] = useState(
    "correction-proposal-ref:replacement",
  );
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchAutocorrectStatus()
      .then((value) => {
        if (!cancelled) setStatus(value);
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(
            sanitizeForDisplay(
              caught instanceof Error
                ? caught.message
                : "Autocorrect status was unavailable safely.",
            ),
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const owner = useMemo(
    () => targetOptions.find((option) => option.kind === form.targetKind)?.owner ?? "tasks",
    [form.targetKind],
  );

  function updateForm<Key extends keyof typeof form>(key: Key, value: (typeof form)[Key]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handlePreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setProposal(null);
    setProposalRequest(null);
    setReceipt(null);
    const request: AutocorrectProposalRequest = {
      workspace_ref: form.workspaceRef,
      source_proposal_ref: form.sourceProposalRef,
      target_kind: form.targetKind,
      target_owner: owner,
      target_ref: form.targetRef,
      expected_revision_ref: form.expectedRevisionRef,
      current_revision_ref: form.currentRevisionRef,
      confidence_percent: form.confidencePercent,
      field_diffs: [
        {
          operation_ref: "operation-ref:autocorrect:review-field",
          target_ref: form.targetRef,
          field_ref: form.fieldRef,
          change_kind: "updated",
          before_fingerprint_ref: form.beforeFingerprintRef,
          after_fingerprint_ref: form.afterFingerprintRef,
          raw_value_included: false,
        },
      ],
      evidence_refs: [form.evidenceRef],
      reason_refs: [form.reasonRef],
      rejection_history_refs: [],
      safe_disabled: false,
      model_generated: false,
      raw_content_included: false,
    };
    if (containsSecretLike(request)) {
      setError("Secret-like input was blocked before submission.");
      return;
    }
    setBusy(true);
    try {
      const nextProposal = await submitAutocorrectProposalPreview(request);
      setProposalRequest(request);
      setProposal(nextProposal);
    } catch (caught) {
      setError(
        sanitizeForDisplay(
          caught instanceof Error
            ? caught.message
            : "Correction preview was rejected safely.",
        ),
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleReview(decision: AutocorrectReviewRequest["decision"]) {
    if (!proposal || !proposalRequest) return;
    setError(null);
    setReceipt(null);
    const digest = proposal.proposal_ref.split(":").at(-1) ?? "proposal";
    const request: AutocorrectReviewRequest = {
      proposal: proposalRequest,
      proposal_ref: proposal.proposal_ref,
      proposal_fingerprint_ref: proposal.proposal_fingerprint_ref,
      decision,
      reviewer_ref: "reviewer-ref:local-operator",
      idempotency_ref: `idempotency-ref:autocorrect:${digest}:${decision}`,
      superseding_proposal_ref:
        decision === "supersede" ? supersedingProposalRef : null,
    };
    if (containsSecretLike(request)) {
      setError("Secret-like review input was blocked before submission.");
      return;
    }
    setBusy(true);
    try {
      setReceipt(await submitAutocorrectReviewPreview(request));
    } catch (caught) {
      setError(
        sanitizeForDisplay(
          caught instanceof Error
            ? caught.message
            : "Correction review was rejected safely.",
        ),
      );
    } finally {
      setBusy(false);
    }
  }

  const reviewEnabled = proposal?.state === "ready_for_review" && !busy;

  return (
    <section className="page-section" aria-labelledby="autocorrect-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Q28 governed correction review</p>
          <h2 id="autocorrect-heading">Autocorrect Controls</h2>
        </div>
        <span className="status-pill compact">proposal-only</span>
      </div>
      <p className="section-copy">
        Compare content-free field fingerprints against one exact canonical revision. Review
        outcomes cannot edit the record, create a ChangeSet, grant approval, or execute rollback.
      </p>
      {status ? (
        <SafeAlert
          title="Backend-owned authority boundary"
          message={`${status.safe_summary} Minimum review confidence: ${status.minimum_review_confidence}%. Process-local replay capacity: ${status.process_local_review_capacity}.`}
        />
      ) : null}
      {error ? <SafeAlert title="Safe rejection" message={error} tone="warning" /> : null}

      <div className="review-layout autocorrect-layout">
        <form className="panel preview-form" onSubmit={handlePreview}>
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Exact candidate binding</p>
              <h3>Prepare comparison</h3>
            </div>
            <span>safe refs only</span>
          </div>
          <label>
            Target kind
            <select
              value={form.targetKind}
              onChange={(event) =>
                updateForm("targetKind", event.target.value as AutocorrectTargetKind)
              }
            >
              {targetOptions.map((option) => (
                <option key={option.kind} value={option.kind}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Workspace ref
            <input
              value={form.workspaceRef}
              onChange={(event) => updateForm("workspaceRef", event.target.value)}
            />
          </label>
          <label>
            Source proposal ref
            <input
              value={form.sourceProposalRef}
              onChange={(event) => updateForm("sourceProposalRef", event.target.value)}
            />
          </label>
          <label>
            Target ref
            <input
              value={form.targetRef}
              onChange={(event) => updateForm("targetRef", event.target.value)}
            />
          </label>
          <label>
            Expected revision ref
            <input
              value={form.expectedRevisionRef}
              onChange={(event) => updateForm("expectedRevisionRef", event.target.value)}
            />
          </label>
          <label>
            Current revision ref
            <input
              value={form.currentRevisionRef}
              onChange={(event) => updateForm("currentRevisionRef", event.target.value)}
            />
          </label>
          <label>
            Field ref
            <input
              value={form.fieldRef}
              onChange={(event) => updateForm("fieldRef", event.target.value)}
            />
          </label>
          <label>
            Before fingerprint ref
            <input
              value={form.beforeFingerprintRef}
              onChange={(event) => updateForm("beforeFingerprintRef", event.target.value)}
            />
          </label>
          <label>
            Proposed fingerprint ref
            <input
              value={form.afterFingerprintRef}
              onChange={(event) => updateForm("afterFingerprintRef", event.target.value)}
            />
          </label>
          <label>
            Evidence ref
            <input
              value={form.evidenceRef}
              onChange={(event) => updateForm("evidenceRef", event.target.value)}
            />
          </label>
          <label>
            Reason ref
            <input
              value={form.reasonRef}
              onChange={(event) => updateForm("reasonRef", event.target.value)}
            />
          </label>
          <label>
            Confidence: {form.confidencePercent}%
            <input
              min={0}
              max={100}
              type="range"
              value={form.confidencePercent}
              onChange={(event) =>
                updateForm("confidencePercent", Number(event.target.value))
              }
            />
          </label>
          <button disabled={busy} type="submit">
            {busy ? "Checking exact bindings…" : "Preview correction"}
          </button>
        </form>

        <section className="panel review-detail" aria-live="polite">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Content-free comparison</p>
              <h3>{proposal ? "Review candidate" : "No candidate prepared"}</h3>
            </div>
            <span>{proposal?.state ?? "waiting"}</span>
          </div>
          {proposal ? (
            <>
              <dl className="detail-grid">
                <dt>Target owner</dt>
                <dd>{proposal.target_owner}</dd>
                <dt>Exact revision</dt>
                <dd>{proposal.comparison.exact_revision_match ? "matched" : "stale"}</dd>
                <dt>Confidence</dt>
                <dd>{proposal.confidence_percent}% · {proposal.confidence}</dd>
                <dt>Raw values</dt>
                <dd>{proposal.comparison.raw_values_included ? "included" : "omitted"}</dd>
                <dt>Rollback</dt>
                <dd>{proposal.rollback.rollback_ready ? "plan ready" : "blocked"}</dd>
                <dt>Canonical write</dt>
                <dd>{proposal.canonical_state_mutated ? "performed" : "not performed"}</dd>
              </dl>
              <article className="status-card">
                <div className="status-card-header">
                  <h4>{proposal.comparison.field_diffs[0]?.field_ref}</h4>
                  <span>fingerprints only</span>
                </div>
                <p>Before: {proposal.comparison.field_diffs[0]?.before_fingerprint_ref}</p>
                <p>Proposed: {proposal.comparison.field_diffs[0]?.after_fingerprint_ref}</p>
              </article>
              <p className="safe-copy">{proposal.next_safe_action}</p>
              <label>
                Superseding proposal ref
                <input
                  value={supersedingProposalRef}
                  onChange={(event) => setSupersedingProposalRef(event.target.value)}
                />
              </label>
              <div className="button-row">
                <button disabled={!reviewEnabled} onClick={() => handleReview("accept")} type="button">
                  Accept for ChangeSet review
                </button>
                <button disabled={!reviewEnabled} onClick={() => handleReview("reject")} type="button">
                  Reject
                </button>
                <button disabled={!reviewEnabled} onClick={() => handleReview("supersede")} type="button">
                  Supersede
                </button>
              </div>
            </>
          ) : (
            <p className="empty-copy">
              Prepare a safe-ref candidate to see exact revision and field-fingerprint truth.
            </p>
          )}
          {receipt ? (
            <article className="status-card" aria-label="Correction review receipt">
              <div className="status-card-header">
                <h4>{receipt.outcome}</h4>
                <span>{receipt.replayed ? "replayed" : "new review"}</span>
              </div>
              <p>{receipt.next_safe_action}</p>
              <p className="safe-copy">Receipt: {receipt.receipt_ref}</p>
              <p className="safe-copy">
                Canonical mutation: no · ChangeSet created: no · Rollback executed: no
              </p>
            </article>
          ) : null}
        </section>
      </div>
    </section>
  );
}
