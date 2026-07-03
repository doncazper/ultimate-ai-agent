export function LoadingState({
  surfaceLabel = "Control Center",
}: {
  surfaceLabel?: string;
}) {
  return (
    <div className="data-state" role="status">
      <strong>Loading local {surfaceLabel}</strong>
      <span>
        Checking local backend connection state for this route's read-only
        contract data and preview-only summaries.
      </span>
    </div>
  );
}

export function ErrorState({
  message,
  surfaceLabel = "Control Center",
}: {
  message: string;
  surfaceLabel?: string;
}) {
  return (
    <div className="data-state error" role="alert" aria-labelledby="control-center-error-heading">
      <strong id="control-center-error-heading">
        {surfaceLabel} data unavailable
      </strong>
      <span>{message}</span>
      <small>
        Next safe action: verify the local backend before trusting this route's
        controls, receipts, or proof claims.
      </small>
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
