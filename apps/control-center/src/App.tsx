import { useMemo } from "react";
import { AppShell } from "./components/AppShell";
import { ErrorState, LoadingState } from "./components/DataState";
import { SafeAlert } from "./components/SafeAlert";
import { useControlCenterData } from "./hooks/useControlCenterData";
import { renderRoute } from "./routes";
import type { BackendConnectionSummary } from "./api/types";

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
      <ConnectionStatus connection={state.data.connection} />
      {renderRoute(activePath, state.data)}
    </AppShell>
  );
}

function ConnectionStatus({ connection }: { connection: BackendConnectionSummary }) {
  const titleByState: Record<BackendConnectionSummary["state"], string> = {
    unknown: "Backend state unknown",
    checking: "Checking backend connection",
    online: "Backend online",
    degraded: "Backend degraded",
    offline: "Backend offline",
    mock_fallback: "Mock fallback active"
  };
  const warnings = connection.warnings.length > 0 ? ` Warnings: ${connection.warnings.join(", ")}.` : "";
  return (
    <SafeAlert
      title={titleByState[connection.state]}
      message={`${connection.safeMessage} API base: ${connection.apiBaseLabel}. Checked: ${connection.checkedAt}.${warnings}`}
      tone={connection.state === "online" ? "info" : "warning"}
    />
  );
}

function normalizePath(path: string): string {
  return path === "" ? "/" : path;
}
