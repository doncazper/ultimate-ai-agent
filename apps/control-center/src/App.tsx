import { useMemo } from "react";
import { AppShell } from "./components/AppShell";
import { ErrorState, LoadingState } from "./components/DataState";
import { SafeAlert } from "./components/SafeAlert";
import { useControlCenterData } from "./hooks/useControlCenterData";
import { renderRoute } from "./routes";

export function App() {
  const state = useControlCenterData();
  const activePath = useMemo(() => normalizePath(window.location.pathname), []);

  if (state.status === "loading") {
    return (
      <AppShell activePath={activePath}>
        <LoadingState />
      </AppShell>
    );
  }

  if (state.status === "error" || !state.data) {
    return (
      <AppShell activePath={activePath}>
        <ErrorState message={state.error ?? "Unable to load Control Center data."} />
      </AppShell>
    );
  }

  return (
    <AppShell activePath={activePath}>
      {state.data.source === "mock" ? (
        <SafeAlert
          title="Mock fallback"
          message="Backend data is unavailable, so this shell is showing non-authoritative mock data."
          tone="warning"
        />
      ) : (
        <SafeAlert
          title="Connected"
          message="Data came from local read-only/preview-only backend API routes."
          tone="info"
        />
      )}
      {renderRoute(activePath, state.data)}
    </AppShell>
  );
}

function normalizePath(path: string): string {
  return path === "" ? "/" : path;
}
