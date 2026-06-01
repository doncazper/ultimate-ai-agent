import type { RuntimeCapabilityMatrix, RuntimeReadinessReport } from "../api/types";

export function RuntimeReadinessPanel({
  report,
  matrix
}: {
  report: RuntimeReadinessReport;
  matrix: RuntimeCapabilityMatrix;
}) {
  const booleans = [
    ["Production ready", report.production_ready],
    ["Real model runtime ready", report.real_model_runtime_ready],
    ["Remote execution ready", report.remote_execution_ready],
    ["Mobile sensor ready", report.mobile_sensor_ready],
    ["Plugin/native build ready", report.plugin_or_native_build_ready]
  ];
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Runtime Readiness</h2>
        <span>{report.status}</span>
      </div>
      <div className="flag-list">
        {booleans.map(([label, value]) => (
          <div key={label.toString()}>
            <span>{label}</span>
            <strong>{value ? "yes" : "no"}</strong>
          </div>
        ))}
      </div>
      <h3>Capability Matrix</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Surface</th>
              <th>Status</th>
              <th>Risk</th>
              <th>Model call</th>
              <th>Cloud</th>
            </tr>
          </thead>
          <tbody>
            {matrix.entries.map((entry) => (
              <tr key={entry.surface}>
                <td>{entry.surface}</td>
                <td>{entry.status}</td>
                <td>{entry.risk_class}</td>
                <td>{entry.real_model_call_allowed ? "yes" : "no"}</td>
                <td>{entry.cloud_allowed ? "yes" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
