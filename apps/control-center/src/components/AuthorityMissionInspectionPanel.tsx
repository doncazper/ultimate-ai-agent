import { useEffect, useState } from "react";

import {
  fetchAuthorityMissionCompletions,
  fetchAuthorityMissionWorkerState,
} from "../api/client";
import type {
  AuthorityMissionCompletionReadModel,
  AuthorityMissionWorkerReadModel,
  AuthorityMissionWorkerStepRecovery,
} from "../api/types";
import { EmptyState, ErrorState, LoadingState } from "./DataState";

interface AuthorityMissionInspectionPanelProps {
  loadWorkerState?: () => Promise<AuthorityMissionWorkerReadModel>;
  loadCompletions?: () => Promise<AuthorityMissionCompletionReadModel>;
}

export function AuthorityMissionInspectionPanel({
  loadWorkerState = fetchAuthorityMissionWorkerState,
  loadCompletions = fetchAuthorityMissionCompletions,
}: AuthorityMissionInspectionPanelProps) {
  const [readModel, setReadModel] =
    useState<AuthorityMissionWorkerReadModel>();
  const [error, setError] = useState<string>();
  const [completions, setCompletions] =
    useState<AuthorityMissionCompletionReadModel>();
  const [completionError, setCompletionError] = useState(false);
  const [completionLoading, setCompletionLoading] = useState(true);

  useEffect(() => {
    let active = true;
    void loadWorkerState()
      .then((value) => {
        if (active) {
          setReadModel(value);
          setError(undefined);
        }
      })
      .catch(() => {
        if (active) {
          setReadModel(undefined);
          setError(
            "Backend mission inspection is unavailable. No mission capability is treated as active.",
          );
        }
      });
    return () => {
      active = false;
    };
  }, [loadWorkerState]);

  useEffect(() => {
    let active = true;
    setCompletionLoading(true);
    void loadCompletions()
      .then((value) => {
        if (active) {
          setCompletions(value);
          setCompletionError(false);
          setCompletionLoading(false);
        }
      })
      .catch(() => {
        if (active) {
          setCompletions(undefined);
          setCompletionError(true);
          setCompletionLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [loadCompletions]);

  if (error) {
    return (
      <ErrorState message={error} surfaceLabel="Authority mission inspection" />
    );
  }
  if (!readModel) {
    return <LoadingState surfaceLabel="authority mission inspection" />;
  }

  const posture = readModel.kill_switch_engaged
    ? "kill switch engaged"
    : readModel.configuration_enabled
      ? "configured"
      : "disabled by default";

  return (
    <section
      className="panel"
      aria-labelledby="authority-mission-inspection-heading"
    >
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Read-only Python Core truth</p>
          <h3 id="authority-mission-inspection-heading">
            Authority mission worker
          </h3>
        </div>
        <span className="status-pill compact">{posture}</span>
      </div>
      <p>{readModel.operator_summary}</p>
      <p className="muted">
        Approval waits, retries, dead letters, and cancellation are durable
        states—not authority. Every resumed start still requires fresh
        request-scoped policy, lease, approval, budget, kill-switch, adapter,
        and target evaluation.
      </p>

      <div className="metric-grid">
        <MissionMetric label="Queued" value={readModel.queued_job_count} />
        <MissionMetric label="Active claims" value={readModel.active_claim_count} />
        <MissionMetric label="Stale claims" value={readModel.stale_claim_count} />
        <MissionMetric label="Observed" value={readModel.total_job_count} />
      </div>

      <dl className="metadata-list">
        <div>
          <dt>Canonical platform</dt>
          <dd>macOS</dd>
        </div>
        <div>
          <dt>Observed platform</dt>
          <dd>{formatStatus(readModel.observed_platform)}</dd>
        </div>
        <div>
          <dt>Linux</dt>
          <dd>{formatStatus(readModel.linux_surface_posture)}</dd>
        </div>
        <div>
          <dt>Windows</dt>
          <dd>{formatStatus(readModel.windows_surface_posture)}</dd>
        </div>
        <div>
          <dt>Remote queue</dt>
          <dd>{readModel.remote_queue_enabled ? "enabled" : "blocked"}</dd>
        </div>
        <div>
          <dt>Authority granted</dt>
          <dd>{readModel.execution_authority_granted ? "yes" : "no"}</dd>
        </div>
      </dl>

      {readModel.jobs.length === 0 ? (
        <EmptyState
          title="No durable authority missions observed"
          message="The local worker inspection is healthy and has no queued, waiting, retrying, cancelled, or terminal mission jobs to show."
        />
      ) : (
        <div
          className="review-list authority-mission-jobs"
          aria-label="Authority mission jobs"
        >
          {readModel.jobs.map((job) => (
            <article className="review-card" key={job.job_safe_ref}>
              <div className="review-card-heading">
                <div>
                  <h3>{job.mission_safe_ref}</h3>
                  <p>
                    {formatStatus(job.durable_status)} · recovery {" "}
                    {formatStatus(job.recovery_status)}
                  </p>
                </div>
                <span className="status-pill compact">
                  {formatStatus(job.heartbeat_freshness)}
                </span>
              </div>
              <dl className="metadata-list">
                <div>
                  <dt>Plan</dt>
                  <dd>{job.plan_safe_ref}</dd>
                </div>
                <div>
                  <dt>Run</dt>
                  <dd>{job.run_safe_ref}</dd>
                </div>
                <div>
                  <dt>Generation</dt>
                  <dd>{job.generation}</dd>
                </div>
                <div>
                  <dt>Retry not before</dt>
                  <dd>{job.retry_not_before ?? "not scheduled"}</dd>
                </div>
              </dl>
              <ul className="compact-list" aria-label="Authority mission steps">
                {job.steps.map((step) => (
                  <li key={step.step_safe_ref}>
                    <strong>{stepStatusLabel(step)}</strong>
                    <small>{step.step_safe_ref}</small>
                    <small>Claim: {formatStatus(step.claim_freshness)}</small>
                    <small>
                      Adapter reinvocation: {" "}
                      {step.adapter_reinvocation_allowed ? "allowed" : "blocked"}
                    </small>
                  </li>
                ))}
              </ul>
              <SafeRefList label="Blocked reasons" refs={job.reason_refs} />
              <SafeRefList label="Evidence" refs={job.evidence_refs} />
            </article>
          ))}
        </div>
      )}

      <div className="panel-subsection" aria-label="Mission completion evidence">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Content-free completion truth</p>
            <h3>Mission completion evidence</h3>
          </div>
          <span className="status-pill compact">
            {completionLoading
              ? "loading"
              : completionError
                ? "unavailable"
                : `${completions?.completion_count ?? 0} recorded`}
          </span>
        </div>
        {completions ? (
          <div className="summary-strip" aria-label="Completion integrity posture">
            <span>
              Completion chain: {completions.completion_count === 0 ? "no evidence recorded" : completions.integrity_summary.hash_chain_verified ? "local SHA-256 verified" : "invalid"}
            </span>
            <span>
              Portable evidence: {formatStatus(completions.portable_evidence_summary.status)}
            </span>
            <span>
              Source records bound: {completions.portable_evidence_summary.source_receipts_bound ? "yes" : "no"}
            </span>
            <span>Signing: blocked, not implemented</span>
            <span>Authenticity verified: false</span>
          </div>
        ) : null}
        {completionLoading ? (
          <p className="muted">Completion evidence is loading.</p>
        ) : completionError ? (
          <p className="muted">
            Completion evidence is unavailable; no mission is presented as
            verified.
          </p>
        ) : completions && completions.latest_manifests.length > 0 ? (
          <div className="review-list">
            {completions.latest_manifests.map((manifest) => (
              <article className="review-card" key={manifest.completion_ref}>
                <div className="review-card-heading">
                  <div>
                    <h3>{manifest.mission_ref}</h3>
                    <p>
                      {manifest.step_bindings.length} settled step
                      {manifest.step_bindings.length === 1 ? "" : "s"} ·
                      content-free hash chain
                    </p>
                  </div>
                  <span className="status-pill compact">completed</span>
                </div>
                <dl className="metadata-list">
                  <div>
                    <dt>Completion</dt>
                    <dd>{manifest.completion_ref}</dd>
                  </div>
                  <div>
                    <dt>Lease</dt>
                    <dd>{manifest.lease_ref}</dd>
                  </div>
                  <div>
                    <dt>Budget</dt>
                    <dd>{manifest.budget_bindings.length} settled</dd>
                  </div>
                  <div>
                    <dt>Memory</dt>
                    <dd>review required, recall only</dd>
                  </div>
                </dl>
                <SafeRefList
                  label="Completion evidence"
                  refs={[manifest.entry_hash_ref, manifest.memory_candidate_ref]}
                />
              </article>
            ))}
          </div>
        ) : (
          <p className="muted">
            No content-free mission completion manifests are recorded.
          </p>
        )}
        <p className="muted">
          Completion evidence records what happened. The backend validated this
          local content-free SHA-256 chain. It is not cryptographically signed,
          externally anchored, or independently source-ledger verified, and it
          cannot grant future authority, accept memory as truth, or enable
          another run.
        </p>
      </div>

      <p className="muted">
        Inspection ref: {readModel.inspection_ref}. Raw task inputs, paths,
        logs, provider payloads, and worker identities are omitted.
      </p>
    </section>
  );
}

function MissionMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SafeRefList({ label, refs }: { label: string; refs: string[] }) {
  if (refs.length === 0) {
    return null;
  }
  return (
    <div className="note-list" aria-label={label}>
      {refs.map((ref) => (
        <span key={ref}>{ref}</span>
      ))}
    </div>
  );
}

function stepStatusLabel(step: AuthorityMissionWorkerStepRecovery): string {
  if (
    step.reason_refs.some(
      (ref) => ref.includes("dead-letter") || ref.includes("attempts-exhausted"),
    )
  ) {
    return "Dead letter";
  }
  return formatStatus(step.status);
}

function formatStatus(value: string): string {
  return value.replaceAll("_", " ");
}
