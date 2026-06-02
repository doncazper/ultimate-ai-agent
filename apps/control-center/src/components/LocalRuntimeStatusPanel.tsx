import type { M18RuntimeData, RuntimeCapabilityMatrix, RuntimeReadinessReport } from "../api/types";

export function LocalRuntimeStatusPanel({
  report,
  matrix,
  runtime
}: {
  report: RuntimeReadinessReport;
  matrix: RuntimeCapabilityMatrix;
  runtime: M18RuntimeData;
}) {
  return (
    <section className="page-section" aria-labelledby="local-runtime-status-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">M18 local runtime surface</p>
          <h2 id="local-runtime-status-heading">Local Runtime Status</h2>
        </div>
        <span className="status-pill compact">{runtime.status}</span>
      </div>
      <p className="section-copy">
        Local runtime status is read-only. No local runtime is started, stopped, connected, or executed from this UI.
      </p>
      <div className="note-list" aria-label="Local runtime safety markers">
        {runtime.warningCodes.map((warning) => (
          <span key={warning}>{warning}</span>
        ))}
      </div>
      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Runtime readiness report</h3>
            <span>{report.status}</span>
          </div>
          <p>Model output remains non-authoritative and production runtime readiness is not claimed.</p>
          <dl className="metadata-list">
            <div>
              <dt>Production ready</dt>
              <dd>{report.production_ready ? "yes" : "no"}</dd>
            </div>
            <div>
              <dt>Real model runtime ready</dt>
              <dd>{report.real_model_runtime_ready ? "yes" : "no"}</dd>
            </div>
            <div>
              <dt>Remote execution ready</dt>
              <dd>{report.remote_execution_ready ? "yes" : "no"}</dd>
            </div>
          </dl>
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Capability sources</h3>
            <span>{matrix.entries.length} entries</span>
          </div>
          <p>{runtime.boundarySummary}</p>
          <ul className="compact-list">
            {runtime.localRuntimeSurfaces.map((surface) => (
              <li key={surface.surfaceRef}>
                <strong>{surface.surfaceRef}</strong>
                <span>{surface.status}</span>
                <small>{surface.safeSummary}</small>
              </li>
            ))}
          </ul>
        </article>
      </div>
      <h3>Runtime capability matrix</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Surface</th>
              <th>Status</th>
              <th>Model call</th>
              <th>Network</th>
              <th>Secrets</th>
            </tr>
          </thead>
          <tbody>
            {matrix.entries.map((entry) => (
              <tr key={entry.surface}>
                <td>{entry.surface}</td>
                <td>{entry.status}</td>
                <td>{entry.real_model_call_allowed ? "yes" : "no"}</td>
                <td>{entry.real_network_allowed ? "yes" : "no"}</td>
                <td>{entry.secrets_allowed ? "yes" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function ManualSmokeControlSurfacePanel({ runtime }: { runtime: M18RuntimeData }) {
  const report = runtime.manualSmokeReports[0];
  return (
    <section className="page-section" aria-labelledby="manual-smoke-control-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">validation-only report surface</p>
          <h2 id="manual-smoke-control-heading">Manual Smoke Control Surface</h2>
        </div>
        <span className="status-pill compact">{runtime.validationOnly ? "validation-only" : "summary-only"}</span>
      </div>
      <p className="section-copy">
        Manual smoke reports are safe summaries. Manual smoke execution remains CLI-only, fixed-prompt-only, approval-gated,
        and non-authoritative.
      </p>
      <div className="note-list" aria-label="Manual smoke safety markers">
        {runtime.warningCodes.map((warning) => (
          <span key={warning}>{warning}</span>
        ))}
      </div>
      {report ? (
        <div className="panel-grid">
          <article className="status-card">
            <div className="status-card-header">
              <h3>{report.reportRef}</h3>
              <span>{report.validationStatus}</span>
            </div>
            <p>{report.safeMessage}</p>
            <dl className="metadata-list">
              <div>
                <dt>Request ref</dt>
                <dd>{report.requestRef}</dd>
              </div>
              <div>
                <dt>Fixed prompt hash</dt>
                <dd>{report.fixedPromptHash}</dd>
              </div>
              <div>
                <dt>Response preview shown</dt>
                <dd>{report.responsePreviewShown ? "yes" : "no"}</dd>
              </div>
              <div>
                <dt>Model output authority</dt>
                <dd>{report.modelOutputAuthoritative ? "yes" : "no"}</dd>
              </div>
              <div>
                <dt>Redaction status</dt>
                <dd>{report.redactionStatus}</dd>
              </div>
            </dl>
          </article>
          <article className="status-card">
            <div className="status-card-header">
              <h3>Validation result</h3>
              <span>{report.responseOrigin}</span>
            </div>
            <p>response preview shown: {report.responsePreviewShown ? "yes" : "no"}</p>
            <ul className="compact-list">
              {report.reasonCodes.map((reason) => (
                <li key={reason}>
                  <strong>{reason}</strong>
                  <small>{report.redactionStatus}</small>
                </li>
              ))}
            </ul>
          </article>
        </div>
      ) : (
        <div className="data-state empty" role="status">
          <strong>No manual smoke reports listed</strong>
          <span>The mock surface has no report validation summaries.</span>
        </div>
      )}
    </section>
  );
}
