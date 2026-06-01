interface StatusCardProps {
  label: string;
  status: string;
  summary: string;
}

export function StatusCard({ label, status, summary }: StatusCardProps) {
  return (
    <article className="status-card">
      <div className="status-card-header">
        <h3>{label}</h3>
        <span>{status}</span>
      </div>
      <p>{summary}</p>
    </article>
  );
}
