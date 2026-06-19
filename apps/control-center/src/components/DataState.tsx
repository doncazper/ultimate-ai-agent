export function LoadingState() {
  return (
    <div className="data-state" role="status">
      <strong>Loading local Control Center</strong>
      <span>
        Checking local backend connection state for read-only contract data and preview-only
        summaries.
      </span>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="data-state error" role="alert">
      {message}
    </div>
  );
}

export function EmptyState({ title, message }: { title: string; message: string }) {
  return (
    <div className="data-state empty" role="status">
      <strong>{title}</strong>
      <span>{message}</span>
    </div>
  );
}
