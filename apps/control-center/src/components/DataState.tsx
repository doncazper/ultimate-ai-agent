export function LoadingState() {
  return <div className="data-state">Loading local Control Center contract data...</div>;
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="data-state error" role="alert">
      {message}
    </div>
  );
}
