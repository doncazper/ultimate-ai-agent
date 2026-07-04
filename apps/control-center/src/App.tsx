import { useMemo } from "react";
import { AppShell } from "./components/AppShell";
import {
  ErrorState,
  LoadingState,
  RouteStatePanel,
} from "./components/DataState";
import { SafeAlert } from "./components/SafeAlert";
import { useControlCenterData } from "./hooks/useControlCenterData";
import {
  getRouteStateDescriptor,
  getRouteSurfaceLabel,
  renderRoute,
} from "./routes";
import type { BackendConnectionSummary } from "./api/types";

export function App() {
  const state = useControlCenterData();
  const activePath = useMemo(() => normalizePath(window.location.pathname), []);
  const activeSurfaceLabel = useMemo(
    () => getRouteSurfaceLabel(activePath),
    [activePath],
  );

  if (state.status === "loading") {
    return (
      <AppShell activePath={activePath}>
        <RouteStatePanel
          state={{
            kind: "loading",
            statusLabel: "loading",
            surfaceLabel: activeSurfaceLabel,
            title: `${activeSurfaceLabel} is loading local route state`,
            message:
              "Control Center is checking backend-owned read models before rendering route claims.",
            nextSafeAction:
              "Wait for local backend posture or inspect CLI/verifier evidence before relying on this surface.",
            sourceLabel: "Route truth: pending local backend read.",
          }}
        />
        <LoadingState surfaceLabel={activeSurfaceLabel} />
      </AppShell>
    );
  }

  if (state.status === "error" || !state.data) {
    return (
      <AppShell activePath={activePath}>
        <RouteStatePanel
          state={{
            kind: "error",
            statusLabel: "error",
            surfaceLabel: activeSurfaceLabel,
            title: `${activeSurfaceLabel} route state unavailable`,
            message:
              "This route is not rendering authoritative product state because the local data load failed closed.",
            nextSafeAction:
              "Check the local backend and use only redacted CLI/verifier evidence until route data returns.",
            sourceLabel: "Route truth: unavailable local backend read.",
          }}
        />
        <ErrorState
          message={state.error ?? "Unable to load Control Center data."}
          surfaceLabel={activeSurfaceLabel}
        />
      </AppShell>
    );
  }

  return (
    <AppShell activePath={activePath} connection={state.data.connection}>
      <ConnectionStatus connection={state.data.connection} />
      <RouteStatePanel
        state={getRouteStateDescriptor(
          activePath,
          state.data.connection,
          state.data.routeStates[activePath],
        )}
      />
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
    mock_fallback: "Mock fallback active",
  };
  const warnings =
    connection.warnings.length > 0 ? ` Warnings: ${connection.warnings.join(", ")}.` : "";
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
