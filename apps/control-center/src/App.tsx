import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { AppShell } from "./components/AppShell";
import {
  ErrorState,
  LoadingState,
  RouteStatePanel,
} from "./components/DataState";
import { SafeAlert } from "./components/SafeAlert";
import { MessengerShell } from "./components/messenger/MessengerShell";
import { SkillWorkbench } from "./components/skillWorkbench/SkillWorkbench";
import { useControlCenterData } from "./hooks/useControlCenterData";
import { useSkillMarketplacePosture } from "./hooks/useSkillMarketplacePosture";
import {
  getRouteStateDescriptor,
  getRouteSurfaceLabel,
  renderRoute,
  renderStaticPreviewRoute,
} from "./routes";
import { mockControlCenterData } from "./mocks/controlCenterData";
import type {
  BackendConnectionSummary,
  ControlCenterData,
  RuntimeInterfaceModeReadModel,
} from "./api/types";
import { isNorthStarPath } from "./northstar/model";

const loadNorthStarControlCenter = () =>
  import("./northstar/NorthStarControlCenter");

const NorthStarControlCenter = lazy(async () => {
  const module = await loadNorthStarControlCenter();
  return { default: module.NorthStarControlCenter };
});

export function App() {
  const activePath = useActivePath();

  if (activePath === "/messenger" || activePath === "/workspace/messenger") {
    return <MessengerShell />;
  }

  if (isNorthStarPath(activePath)) {
    return <NorthStarRoute activePath={activePath} />;
  }

  if (activePath === "/studio" || activePath === "/studio/skills") {
    return <StudioRoute />;
  }

  const staticPreviewRoute = renderStaticPreviewRoute(activePath);
  if (staticPreviewRoute) {
    return (
      <AppShell activePath={activePath}>
        {staticPreviewRoute}
      </AppShell>
    );
  }

  return <ControlCenterRoute activePath={activePath} />;
}

export function NorthStarRoute({
  activePath,
  loadModule = loadNorthStarControlCenter,
}: {
  activePath: string;
  loadModule?: typeof loadNorthStarControlCenter;
}) {
  const [moduleStatus, setModuleStatus] = useState<"loading" | "ready" | "failed">("loading");

  useEffect(() => {
    let active = true;
    loadModule()
      .then(() => {
        if (active) setModuleStatus("ready");
      })
      .catch(() => {
        if (active) setModuleStatus("failed");
      });
    return () => {
      active = false;
    };
  }, [loadModule]);

  const state = useControlCenterData(moduleStatus === "ready");
  const activeSurfaceLabel = getRouteSurfaceLabel(activePath);

  if (moduleStatus === "loading") {
    return (
      <div aria-live="polite" className="app-loading" role="status">
        Loading workspace representation…
      </div>
    );
  }

  if (moduleStatus === "failed") {
    return (
      <AppShell activePath={activePath}>
        <RouteStatePanel
          state={{
            kind: "error",
            statusLabel: "error",
            surfaceLabel: activeSurfaceLabel,
            title: `${activeSurfaceLabel} representation unavailable`,
            message: "The local workspace representation could not load and failed closed.",
            nextSafeAction: "Use the existing backend-owned Control Center routes until the representation is available.",
            sourceLabel: "Route truth: local representation unavailable.",
          }}
        />
      </AppShell>
    );
  }

  if (state.status === "loading") {
    return (
      <Suspense
        fallback={
          <div aria-live="polite" className="app-loading" role="status">
            Loading workspace representation…
          </div>
        }
      >
        <NorthStarControlCenter
          activePath={activePath}
          data={mockControlCenterData}
        />
      </Suspense>
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
    <Suspense
      fallback={
        <div aria-live="polite" className="app-loading" role="status">
          Loading workspace representation…
        </div>
      }
    >
      <NorthStarControlCenter activePath={activePath} data={state.data} />
    </Suspense>
  );
}

function StudioRoute() {
  const state = useSkillMarketplacePosture();

  if (state.status === "loading") {
    return (
      <AppShell activePath="/studio/skills">
        <LoadingState surfaceLabel="Studio" />
      </AppShell>
    );
  }

  return (
    <SkillWorkbench
      backendValidated={state.data.backendValidated}
      catalogDisplayable={state.data.catalogDisplayable}
      posture={state.data.posture}
    />
  );
}

function ControlCenterRoute({ activePath }: { activePath: string }) {
  const state = useControlCenterData();
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
    <AppShell
      activePath={activePath}
      authorityMode={state.data.settingsStatus.authority_lease_state.active_mode}
      authorityModeAuthoritative={
        state.data.routeStates["/settings"]?.state === "backend_owned"
      }
      connection={state.data.connection}
      killSwitchEngaged={
        state.data.settingsStatus.authority_lease_state.kill_switch_engaged
      }
      killSwitchVisible={
        state.data.settingsStatus.authority_lease_state.kill_switch_visible
      }
      routeState={state.data.routeStates[activePath]}
    >
      <ConnectionStatus
        connection={state.data.connection}
        routeState={state.data.routeStates[activePath]}
      />
      {state.data.runtimeInterfaceMode.interface_enabled ? (
        <RuntimeInterfaceModeBanner mode={state.data.runtimeInterfaceMode} />
      ) : null}
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

function RuntimeInterfaceModeBanner({
  mode,
}: {
  mode: RuntimeInterfaceModeReadModel;
}) {
  return (
    <SafeAlert
      tone="info"
      title={`Runtime interface mode: ${mode.active_mode}`}
      message={`UAA-native agent execution is ${mode.uaa_execution_enabled ? "enabled" : "off"}; Hermes context is ${mode.context_pack_ref}; memory updates are ${mode.memory_update_policy}.`}
    />
  );
}

function useActivePath(): string {
  const [activePath, setActivePath] = useState(() =>
    normalizePath(window.location.pathname),
  );

  useEffect(() => {
    const syncActivePath = () => {
      setActivePath(normalizePath(window.location.pathname));
    };
    const handleDocumentClick = (event: MouseEvent) => {
      if (
        event.defaultPrevented ||
        event.button !== 0 ||
        event.altKey ||
        event.ctrlKey ||
        event.metaKey ||
        event.shiftKey
      ) {
        return;
      }
      const target = event.target;
      if (!(target instanceof Element)) {
        return;
      }
      const anchor = target.closest("a[href]");
      if (!(anchor instanceof HTMLAnchorElement)) {
        return;
      }
      if (
        anchor.target !== "" ||
        anchor.hasAttribute("download") ||
        anchor.getAttribute("rel")?.includes("external")
      ) {
        return;
      }
      const nextUrl = new URL(anchor.href, window.location.href);
      if (nextUrl.origin !== window.location.origin) {
        return;
      }

      event.preventDefault();
      const nextPath = `${nextUrl.pathname}${nextUrl.search}${nextUrl.hash}`;
      window.history.pushState({}, "", nextPath);
      syncActivePath();
      try {
        if (!navigator.userAgent.toLowerCase().includes("jsdom")) {
          window.scrollTo({ top: 0, behavior: "auto" });
        }
      } catch {
        // Older browser hosts may expose navigation without scroll APIs.
      }
    };

    window.addEventListener("popstate", syncActivePath);
    document.addEventListener("click", handleDocumentClick);
    return () => {
      window.removeEventListener("popstate", syncActivePath);
      document.removeEventListener("click", handleDocumentClick);
    };
  }, []);

  return activePath;
}

function ConnectionStatus({
  connection,
  routeState,
}: {
  connection: BackendConnectionSummary;
  routeState?: ControlCenterData["routeStates"][string];
}) {
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
  if (
    connection.state !== "online" &&
    routeState?.state === "backend_owned"
  ) {
    return (
      <SafeAlert
        title="Backend degraded"
        message={`${connection.safeMessage} ${routeState.surfaceLabel} remains backed by ${routeState.sourceLabel}; inspect its exact refs independently. ${warnings}`}
        tone="warning"
      />
    );
  }
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
