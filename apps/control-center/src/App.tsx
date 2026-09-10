import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "./components/AppShell";
import {
  ErrorState,
  LoadingState,
  RouteStatePanel,
} from "./components/DataState";
import { SafeAlert } from "./components/SafeAlert";
import { MacOSSetupAssistantPanel } from "./components/MacOSSetupAssistantPanel";
import { MessengerShell } from "./components/messenger/MessengerShell";
import { SkillWorkbench } from "./components/skillWorkbench/SkillWorkbench";
import { useControlCenterData } from "./hooks/useControlCenterData";
import {
  type CriticalBackendTruthState,
  useCriticalBackendTruth,
} from "./hooks/useCriticalBackendTruth";
import { useSkillMarketplacePosture } from "./hooks/useSkillMarketplacePosture";
import { useMacOSSetupAssistant } from "./hooks/useMacOSSetupAssistant";
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
  FounderLoopActionsInbox,
  RuntimeInterfaceModeReadModel,
} from "./api/types";
import {
  ACTION_INBOX_REVISION_REFRESH_EVENT,
  fetchFounderActionsInbox,
  fetchNorthStarDecisionsInbox,
  founderLoopLocalTaskRef,
  localTaskCommitReceiptRefForIdempotency,
  submitActionCancellation,
  type BackendTruthReadBinding,
} from "./api/client";
import { isNorthStarPath } from "./northstar/model";
import {
  canonicalizeControlCenterPath,
  isCriticalControlCenterPath,
} from "./api/backendTruth";
import { BackendTruthMutationBindingProvider } from "./backendTruthMutationBinding";

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

  if (activePath === "/setup") {
    return <SetupControlCenterRoute activePath={activePath} />;
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

function SetupControlCenterRoute({ activePath }: { activePath: string }) {
  const truthState = useCriticalBackendTruth(true);
  const truthAdmitted = criticalTruthAllowsRoute(activePath, truthState);
  const truthReadBinding = useMemo<BackendTruthReadBinding | null>(
    () =>
      truthAdmitted && truthState.truth
        ? {
            snapshotRef: truthState.truth.envelope_integrity_ref,
            backendRevisionRef: truthState.truth.backend_revision_ref,
            backendInstanceRef: truthState.truth.backend_instance_ref,
          }
        : null,
    [
      truthAdmitted,
      truthState.truth?.envelope_integrity_ref,
      truthState.truth?.backend_revision_ref,
      truthState.truth?.backend_instance_ref,
    ],
  );
  const setupState = useMacOSSetupAssistant(
    truthAdmitted,
    truthReadBinding,
  );
  const retry = async () => {
    await truthState.retry();
    setupState.retry();
  };

  if (!truthAdmitted) {
    return (
      <CriticalBackendTruthUnavailable
        activePath={activePath}
        retry={retry}
        state={truthState}
        surfaceLabel="Setup"
      />
    );
  }

  if (setupState.status === "loading") {
    return (
      <AppShell activePath={activePath}>
        <RouteStatePanel
          state={{
            kind: "loading",
            statusLabel: "loading",
            surfaceLabel: "Setup",
            title: "Setup is loading its local readiness summary",
            message:
              "Control Center is reading the one Python-owned Setup contract needed for this screen.",
            nextSafeAction:
              "Wait for the local Setup summary; no installer or model action is running.",
            sourceLabel:
              "Route truth: GET /control-center/setup-assistant/summary",
          }}
        />
        <LoadingState surfaceLabel="Setup" />
      </AppShell>
    );
  }

  if (setupState.status === "error") {
    return (
      <CriticalBackendTruthUnavailable
        activePath={activePath}
        retry={retry}
        state={{
          ...truthState,
          status: "degraded",
          truth: null,
          errorRef: setupState.errorRef,
        }}
        surfaceLabel="Setup"
      />
    );
  }

  const nextSafeAction =
    setupState.data.diagnostics.find(
      (diagnostic) => diagnostic.status === "missing",
    )?.nextSafeAction ??
    setupState.data.diagnostics.find(
      (diagnostic) => diagnostic.status === "blocked",
    )?.nextSafeAction ??
    setupState.data.nextSteps[0] ??
    "Inspect the current local Setup summary.";
  const routeState: ControlCenterData["routeStates"][string] = {
    route: "/setup",
    surfaceLabel: "Setup",
    state: "backend_owned",
    statusLabel: "backend-owned",
    sourceLabel: "Python Agent Core",
    safeSummary: setupState.data.repoSafeScope,
    backendRouteRefs: ["GET /control-center/setup-assistant/summary"],
    warningRefs: [],
    blockedAuthorityRefs: setupState.data.blockedCapabilities,
    nextSafeAction,
  };

  return (
    <AppShell activePath={activePath} routeState={routeState}>
      <RouteStatePanel
        state={{
          kind: "success",
          statusLabel: "backend-owned",
          surfaceLabel: "Setup",
          title: "Local Setup readiness is available",
          message:
            "This screen is bound directly to the Python-owned Setup summary instead of waiting for unrelated Control Center data.",
          nextSafeAction,
          sourceLabel:
            "Route truth: GET /control-center/setup-assistant/summary",
        }}
      />
      <BackendTruthMutationBindingProvider binding={truthReadBinding}>
        <MacOSSetupAssistantPanel setup={setupState.data} />
      </BackendTruthMutationBindingProvider>
    </AppShell>
  );
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

  const criticalPath = isCriticalControlCenterPath(activePath);
  const truthState = useCriticalBackendTruth(
    moduleStatus === "ready" && criticalPath,
  );
  const truthAdmitted =
    !criticalPath || criticalTruthAllowsRoute(activePath, truthState);
  const truthReadBinding = useMemo<BackendTruthReadBinding | null>(
    () =>
      truthAdmitted && truthState.truth
        ? {
            snapshotRef: truthState.truth.envelope_integrity_ref,
            backendRevisionRef: truthState.truth.backend_revision_ref,
            backendInstanceRef: truthState.truth.backend_instance_ref,
          }
        : null,
    [
      truthAdmitted,
      truthState.truth?.envelope_integrity_ref,
      truthState.truth?.backend_revision_ref,
      truthState.truth?.backend_instance_ref,
    ],
  );
  const dataScope = canonicalizeControlCenterPath(activePath) === "/workspace/decisions"
    ? "north-star-decisions"
    : "full";
  const state = useControlCenterData(
    moduleStatus === "ready" && truthAdmitted,
    truthReadBinding,
    dataScope,
  );
  const loadedActionInbox =
    state.status === "ready" ? state.data.founderActionsInbox : null;
  const loadedActionInboxSnapshotKey = loadedActionInbox
    ? loadedActionInbox.items
        .map(
          (item) =>
            `${item.item_ref}:${item.action_revision_ref ?? item.expected_revision_ref ?? "missing"}:${item.status}`,
        )
        .join("|")
    : "unavailable";
  const [actionInboxOverride, setActionInboxOverride] =
    useState<FounderLoopActionsInbox | null>(null);
  const [revisionRefreshFailed, setRevisionRefreshFailed] = useState(false);
  const [pendingLocalTaskCommitItemRefs, setPendingLocalTaskCommitItemRefs] =
    useState<string[]>([]);
  const [pendingCancellationItemRefs, setPendingCancellationItemRefs] =
    useState<string[]>([]);
  const updateLocalTaskCommitFence = useCallback(
    (itemRef: string, pending: boolean) => {
      setPendingLocalTaskCommitItemRefs((current) => {
        const next = pending
          ? Array.from(new Set([...current, itemRef]))
          : current.filter((candidate) => candidate !== itemRef);
        return next.length === current.length
          && next.every((candidate, index) => candidate === current[index])
          ? current
          : next;
      });
    },
    [],
  );
  const updateCancellationFence = useCallback(
    (itemRef: string, pending: boolean) => {
      setPendingCancellationItemRefs((current) => {
        const next = pending
          ? Array.from(new Set([...current, itemRef]))
          : current.filter((candidate) => candidate !== itemRef);
        return next.length === current.length
          && next.every((candidate, index) => candidate === current[index])
          ? current
          : next;
      });
    },
    [],
  );

  useEffect(() => {
    setActionInboxOverride(null);
    setRevisionRefreshFailed(false);
    if (loadedActionInbox) {
      setPendingLocalTaskCommitItemRefs((current) =>
        reconcilePendingLocalTaskCommitItemRefs(current, loadedActionInbox),
      );
    }
  }, [loadedActionInboxSnapshotKey]);

  useEffect(() => {
    const canonicalPath = canonicalizeControlCenterPath(activePath);
    if (
      !["/actions", "/workspace/decisions"].includes(canonicalPath) ||
      !truthReadBinding
    )
      return;
    let active = true;
    const refreshAfterConflict = () => {
      setRevisionRefreshFailed(false);
      void fetchFounderActionsInbox(truthReadBinding)
        .then((inbox) => {
          if (active) setActionInboxOverride(inbox);
        })
        .catch(() => {
          if (active) setRevisionRefreshFailed(true);
        });
    };
    window.addEventListener(
      ACTION_INBOX_REVISION_REFRESH_EVENT,
      refreshAfterConflict as EventListener,
    );
    return () => {
      active = false;
      window.removeEventListener(
        ACTION_INBOX_REVISION_REFRESH_EVENT,
        refreshAfterConflict as EventListener,
      );
    };
  }, [activePath, truthReadBinding]);
  const retryCriticalRoute = async () => {
    await truthState.retry();
    state.retry();
  };
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

  if (criticalPath && !truthAdmitted) {
    return (
      <CriticalBackendTruthUnavailable
        activePath={activePath}
        retry={retryCriticalRoute}
        state={truthState}
        surfaceLabel={activeSurfaceLabel}
      />
    );
  }

  if (state.status === "loading") {
    if (criticalPath) {
      return (
        <AppShell activePath={activePath}>
          <RouteStatePanel
            state={{
              kind: "loading",
              statusLabel: "loading",
              surfaceLabel: activeSurfaceLabel,
              title: `${activeSurfaceLabel} is loading local route state`,
              message:
                "The workspace is waiting for backend-owned read models before rendering critical product content.",
              nextSafeAction:
                "Wait for the local backend read or inspect CLI/verifier evidence before relying on this surface.",
              sourceLabel: "Route truth: pending local backend read.",
            }}
          />
          <LoadingState surfaceLabel={activeSurfaceLabel} />
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

  if (
    criticalPath &&
    !criticalRouteDataIsBackendOwned(activePath, state.data)
  ) {
    return (
      <CriticalBackendTruthUnavailable
        activePath={activePath}
        retry={retryCriticalRoute}
        state={{
          ...truthState,
          status: "degraded",
          truth: null,
          errorRef: "CRITICAL_ROUTE_READ_MODEL_UNVERIFIED",
        }}
        surfaceLabel={activeSurfaceLabel}
      />
    );
  }

  const visibleData = actionInboxOverride
    ? { ...state.data, founderActionsInbox: actionInboxOverride }
    : state.data;

  return (
    <Suspense
      fallback={
        <div aria-live="polite" className="app-loading" role="status">
          Loading workspace representation…
        </div>
      }
    >
      <BackendTruthMutationBindingProvider binding={truthReadBinding}>
        {revisionRefreshFailed ? (
          <SafeAlert
            message="The authoritative Action Inbox refresh failed. The last confirmed backend snapshot remains visible; retry the backend read before making another decision."
            title="Action revision refresh unavailable"
            tone="warning"
          />
        ) : null}
        {canonicalizeControlCenterPath(activePath) === "/workspace/decisions" ? (
          <ActionInboxCancellationControl
            binding={truthReadBinding}
            data={visibleData}
            pendingLocalTaskCommitItemRefs={pendingLocalTaskCommitItemRefs}
            onCancellationFenceChange={updateCancellationFence}
            onAuthoritativeRefresh={(inbox) => {
              setActionInboxOverride(inbox);
              setPendingLocalTaskCommitItemRefs((current) =>
                reconcilePendingLocalTaskCommitItemRefs(current, inbox),
              );
              setRevisionRefreshFailed(false);
            }}
          />
        ) : null}
        <NorthStarControlCenter
          activePath={activePath}
          data={visibleData}
          pendingCancellationItemRefs={pendingCancellationItemRefs}
          onLocalTaskCommitFenceChange={updateLocalTaskCommitFence}
          onActionInboxRefresh={(inbox) => {
            setActionInboxOverride(inbox);
            setPendingLocalTaskCommitItemRefs((current) =>
              reconcilePendingLocalTaskCommitItemRefs(current, inbox),
            );
            setRevisionRefreshFailed(false);
          }}
        />
      </BackendTruthMutationBindingProvider>
    </Suspense>
  );
}

export function ActionInboxCancellationControl({
  binding,
  data,
  pendingLocalTaskCommitItemRefs,
  onCancellationFenceChange,
  onAuthoritativeRefresh,
}: {
  binding: BackendTruthReadBinding | null;
  data: ControlCenterData;
  pendingLocalTaskCommitItemRefs: readonly string[];
  onCancellationFenceChange?: (itemRef: string, pending: boolean) => void;
  onAuthoritativeRefresh: (inbox: FounderLoopActionsInbox) => void;
}) {
  const inbox = data.founderActionsInbox;
  const [selectedItemRef, setSelectedItemRef] = useState(
    inbox.items[0]?.item_ref ?? "",
  );
  const [pending, setPending] = useState(false);
  const [pendingCancellationReceipt, setPendingCancellationReceipt] = useState<{
    itemRef: string;
    receiptRef: string;
    resultRevisionRef: string;
  } | null>(null);
  const [feedback, setFeedback] = useState(
    "Cancel is revision-bound and invalidates every earlier backend-owned approval.",
  );
  const selectedItem =
    inbox.items.find((item) => item.item_ref === selectedItemRef) ??
    inbox.items[0];
  const expectedRevisionRef =
    selectedItem?.action_revision_ref ?? selectedItem?.expected_revision_ref;
  const authoritative =
    data.connection.state === "online" &&
    !data.connection.usingMockData &&
    data.routeStates["/actions"]?.state === "backend_owned";
  const localTaskCommitted = Boolean(
    selectedItem?.local_task_commit_receipt_ref?.startsWith("receipt:"),
  );
  const localTaskCommitPending = Boolean(
    selectedItem && pendingLocalTaskCommitItemRefs.includes(selectedItem.item_ref),
  );
  const canCancel = Boolean(
    authoritative &&
      binding &&
      inbox.mutating_controls_enabled &&
      inbox.expected_revision_required &&
      inbox.cancel_decision_enabled &&
      selectedItem &&
      selectedItem.action_revision_decision_eligible === true &&
      selectedItem.status !== "cancelled" &&
      !localTaskCommitted &&
      !localTaskCommitPending &&
      !pendingCancellationReceipt &&
      expectedRevisionRef,
  );

  useEffect(() => {
    if (
      !inbox.items.some((item) => item.item_ref === selectedItemRef)
    ) {
      setSelectedItemRef(inbox.items[0]?.item_ref ?? "");
    }
  }, [inbox.items, selectedItemRef]);

  useEffect(() => {
    if (!pendingCancellationReceipt) return;
    const reconciledItem = inbox.items.find(
      (item) => item.item_ref === pendingCancellationReceipt.itemRef,
    );
    if (
      reconciledItem?.status === "cancelled"
      && reconciledItem.action_revision_ref
        === pendingCancellationReceipt.resultRevisionRef
      && reconciledItem.receipt_refs.includes(
        pendingCancellationReceipt.receiptRef,
      )
    ) {
      onCancellationFenceChange?.(pendingCancellationReceipt.itemRef, false);
      setPendingCancellationReceipt(null);
      setFeedback(
        `Cancellation confirmed by the refreshed backend read model · ${pendingCancellationReceipt.receiptRef}.`,
      );
    }
  }, [inbox.items, onCancellationFenceChange, pendingCancellationReceipt]);

  async function cancelSelectedRevision() {
    if (!selectedItem || !expectedRevisionRef || !canCancel || pending) return;
    const submittedItemRef = selectedItem.item_ref;
    setPending(true);
    onCancellationFenceChange?.(submittedItemRef, true);
    setFeedback("Recording the cancellation against the exact displayed revision…");
    try {
      const receipt = await submitActionCancellation(
        selectedItem.item_ref,
        {
          expected_revision_ref: expectedRevisionRef,
          decision_reason_ref:
            "decision-reason-ref:control-center:action-inbox-cancel",
          metadata_refs: [
            "metadata-ref:control-center:action-inbox-cancel",
            selectedItem.item_ref,
          ],
        },
        binding,
      );
      setPendingCancellationReceipt({
        itemRef: submittedItemRef,
        receiptRef: receipt.receipt_ref,
        resultRevisionRef: receipt.result_revision_ref,
      });
      try {
        const refreshed = await fetchNorthStarDecisionsInbox(binding);
        const refreshedItem = refreshed.items.find(
          (item) => item.item_ref === submittedItemRef,
        );
        const reconciled = Boolean(
          refreshedItem?.status === "cancelled" &&
            refreshedItem.action_revision_ref === receipt.result_revision_ref &&
            refreshedItem.receipt_refs.includes(receipt.receipt_ref),
        );
        if (!reconciled) {
          setFeedback(
            "A cancellation receipt was returned, but authoritative reconciliation is still pending. The displayed state was not marked committed.",
          );
          return;
        }
        onCancellationFenceChange?.(submittedItemRef, false);
        setPendingCancellationReceipt(null);
        onAuthoritativeRefresh(refreshed);
        setFeedback(
          `Cancellation confirmed by the refreshed backend read model · ${receipt.receipt_ref}.`,
        );
      } catch {
        setFeedback(
          "A cancellation receipt was returned, but the authoritative refresh failed. The last confirmed Action Inbox remains visible and no unconfirmed state is shown as committed.",
        );
      }
    } catch (error) {
      onCancellationFenceChange?.(submittedItemRef, false);
      setFeedback(
        error instanceof Error
          ? error.message
          : "The cancellation was not recorded safely.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <section
      aria-label="Revision-bound Action cancellation"
      className="route-state-panel"
    >
      <p className="eyebrow">Action Inbox · exact revision lifecycle</p>
      <h2>Cancel a pending action safely</h2>
      <p>
        {localTaskCommitted
          ? "This Action is terminal because its local task is already committed. Cancellation remains blocked; the durable task receipt is unchanged."
          : localTaskCommitPending
            ? "A validated local task commit receipt is waiting for backend reconciliation. Cancellation remains blocked until the exact committed projection is visible."
          : "Python Core validates the displayed revision and invalidates earlier approvals atomically. This control never executes the action."}
      </p>
      <label>
        Action
        <select
          aria-label="Action to cancel"
          disabled={pending || inbox.items.length === 0}
          onChange={(event) => setSelectedItemRef(event.target.value)}
          value={selectedItem?.item_ref ?? ""}
        >
          {inbox.items.map((item) => (
            <option key={item.item_ref} value={item.item_ref}>
              {item.title}
            </option>
          ))}
        </select>
      </label>
      <p>
        Revision: <code>{expectedRevisionRef ?? "revision-ref:unavailable"}</code>
      </p>
      <button
        disabled={!canCancel || pending}
        onClick={() => void cancelSelectedRevision()}
        type="button"
      >
        {pending
          ? "Recording cancellation…"
          : localTaskCommitted
            ? "Cancellation unavailable · local task committed"
            : localTaskCommitPending
              ? "Cancellation unavailable · local task commit pending"
            : "Cancel exact revision"}
      </button>
      <p aria-live="polite">{feedback}</p>
    </section>
  );
}

function localTaskCommitProjectionIsExactlyBound(
  item: FounderLoopActionsInbox["items"][number] | undefined,
): boolean {
  const projection = item?.receipt_visibility;
  const idempotencyRef = projection?.local_task_commit_idempotency_key_ref;
  if (!item || !projection || typeof idempotencyRef !== "string") return false;
  const localTaskRef = founderLoopLocalTaskRef(item.item_ref);
  const receiptRef = localTaskCommitReceiptRefForIdempotency(
    item.item_ref,
    idempotencyRef,
  );
  const missingStatesAreClear =
    projection.missing_field_states.length === 0
    || (
      projection.missing_field_states.length === 1
      && projection.missing_field_states[0] === "none"
    );
  return projection.schema_version
      === "founder_loop_action_receipt_visibility.v1"
    && projection.contract_ref
      === "contract-ref:founder-loop-action-receipt-visibility:v1"
    && projection.source === "python_core_action_inbox_read_model"
    && projection.backend_owned === true
    && missingStatesAreClear
    && item.local_task_ref === localTaskRef
    && projection.local_task_ref === localTaskRef
    && item.local_task_commit_receipt_ref === receiptRef
    && projection.local_task_commit_receipt_ref === receiptRef
    && item.receipt_refs.includes(receiptRef);
}

export function reconcilePendingLocalTaskCommitItemRefs(
  current: readonly string[],
  inbox: FounderLoopActionsInbox,
): string[] {
  const next = current.filter((itemRef) => {
    const item = inbox.items.find((candidate) => candidate.item_ref === itemRef);
    return !localTaskCommitProjectionIsExactlyBound(item);
  });
  return next.length === current.length
    && next.every((candidate, index) => candidate === current[index])
    ? current as string[]
    : next;
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
  const criticalPath = isCriticalControlCenterPath(activePath);
  const truthState = useCriticalBackendTruth(
    criticalPath,
  );
  const truthAdmitted =
    !criticalPath || criticalTruthAllowsRoute(activePath, truthState);
  const truthReadBinding = useMemo<BackendTruthReadBinding | null>(
    () =>
      truthAdmitted && truthState.truth
        ? {
            snapshotRef: truthState.truth.envelope_integrity_ref,
            backendRevisionRef: truthState.truth.backend_revision_ref,
            backendInstanceRef: truthState.truth.backend_instance_ref,
          }
        : null,
    [
      truthAdmitted,
      truthState.truth?.envelope_integrity_ref,
      truthState.truth?.backend_revision_ref,
      truthState.truth?.backend_instance_ref,
    ],
  );
  const state = useControlCenterData(
    truthAdmitted,
    truthReadBinding,
  );
  const loadedActionInbox =
    state.status === "ready" ? state.data.founderActionsInbox : null;
  const loadedActionInboxSnapshotKey = loadedActionInbox
    ? loadedActionInbox.items
        .map(
          (item) =>
            `${item.item_ref}:${item.action_revision_ref ?? item.expected_revision_ref ?? "missing"}:${item.status}`,
        )
        .join("|")
    : "unavailable";
  const [actionInboxOverride, setActionInboxOverride] =
    useState<FounderLoopActionsInbox | null>(null);
  const [revisionRefreshFailed, setRevisionRefreshFailed] = useState(false);

  useEffect(() => {
    setActionInboxOverride(null);
    setRevisionRefreshFailed(false);
  }, [loadedActionInboxSnapshotKey]);

  useEffect(() => {
    if (
      canonicalizeControlCenterPath(activePath) !== "/actions" ||
      !truthReadBinding
    )
      return;
    let active = true;
    const refreshAfterConflict = () => {
      setRevisionRefreshFailed(false);
      void fetchFounderActionsInbox(truthReadBinding)
        .then((inbox) => {
          if (active) setActionInboxOverride(inbox);
        })
        .catch(() => {
          if (active) setRevisionRefreshFailed(true);
        });
    };
    window.addEventListener(
      ACTION_INBOX_REVISION_REFRESH_EVENT,
      refreshAfterConflict as EventListener,
    );
    return () => {
      active = false;
      window.removeEventListener(
        ACTION_INBOX_REVISION_REFRESH_EVENT,
        refreshAfterConflict as EventListener,
      );
    };
  }, [activePath, truthReadBinding]);
  const retryCriticalRoute = async () => {
    await truthState.retry();
    state.retry();
  };
  const activeSurfaceLabel = useMemo(
    () => getRouteSurfaceLabel(activePath),
    [activePath],
  );

  if (criticalPath && !truthAdmitted) {
    return (
      <CriticalBackendTruthUnavailable
        activePath={activePath}
        retry={retryCriticalRoute}
        state={truthState}
        surfaceLabel={activeSurfaceLabel}
      />
    );
  }

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

  if (
    criticalPath &&
    !criticalRouteDataIsBackendOwned(activePath, state.data)
  ) {
    return (
      <CriticalBackendTruthUnavailable
        activePath={activePath}
        retry={retryCriticalRoute}
        state={{
          ...truthState,
          status: "degraded",
          truth: null,
          errorRef: "CRITICAL_ROUTE_READ_MODEL_UNVERIFIED",
        }}
        surfaceLabel={activeSurfaceLabel}
      />
    );
  }

  const visibleData = actionInboxOverride
    ? { ...state.data, founderActionsInbox: actionInboxOverride }
    : state.data;
  const routeState = state.data.routeStates[activePath];

  return (
    <AppShell
      activePath={activePath}
      authorityMode={visibleData.settingsStatus.authority_lease_state.active_mode}
      authorityModeAuthoritative={
        visibleData.routeStates["/settings"]?.state === "backend_owned"
      }
      connection={visibleData.connection}
      killSwitchEngaged={
        visibleData.settingsStatus.authority_lease_state.kill_switch_engaged
      }
      killSwitchVisible={
        visibleData.settingsStatus.authority_lease_state.kill_switch_visible
      }
      routeState={routeState}
    >
      {revisionRefreshFailed ? (
        <SafeAlert
          message="The authoritative Action Inbox refresh failed. The last confirmed backend snapshot remains visible; retry the backend read before making another decision."
          title="Action revision refresh unavailable"
          tone="warning"
        />
      ) : null}
      <ConnectionStatus
        connection={visibleData.connection}
        routeState={routeState}
      />
      {visibleData.runtimeInterfaceMode.interface_enabled ? (
        <RuntimeInterfaceModeBanner mode={visibleData.runtimeInterfaceMode} />
      ) : null}
      <RouteStatePanel
        state={getRouteStateDescriptor(
          activePath,
          visibleData.connection,
          routeState,
        )}
      />
      <BackendTruthMutationBindingProvider binding={truthReadBinding}>
        {renderRoute(activePath, visibleData)}
      </BackendTruthMutationBindingProvider>
    </AppShell>
  );
}

const FOUNDER_LOOP_SPINE_ROUTE_KEYS = [
  "/today",
  "/actions",
  "/evidence",
  "/settings",
];

const NORTH_STAR_SHELL_ROUTE_KEYS = [
  "/critical/dashboard-read-model",
  "/chat",
  "/settings",
];

const FIRST_RUN_CRITICAL_PATHS = new Set([
  "/actions",
  "/settings",
  "/start",
  "/setup",
  "/workspace/onboarding",
]);

function criticalTruthAllowsRoute(
  activePath: string,
  state: CriticalBackendTruthState,
): boolean {
  return (
    state.status === "ready" ||
    (state.status === "onboarding" &&
      FIRST_RUN_CRITICAL_PATHS.has(canonicalizeControlCenterPath(activePath)))
  );
}

const CRITICAL_ROUTE_KEYS: Record<string, string[]> = {
  "/": ["/critical/dashboard-read-model", "/settings"],
  "/start": ["/start", ...FOUNDER_LOOP_SPINE_ROUTE_KEYS],
  "/today": [...FOUNDER_LOOP_SPINE_ROUTE_KEYS, "/chat"],
  "/plans": [
    "/plans",
    ...FOUNDER_LOOP_SPINE_ROUTE_KEYS,
    "/critical/dashboard-read-model",
  ],
  "/actions": [
    ...FOUNDER_LOOP_SPINE_ROUTE_KEYS,
    "/approvals",
    "/critical/dashboard-read-model",
  ],
  "/approvals": [
    "/approvals",
    "/critical/dashboard-read-model",
    "/settings",
  ],
  "/work-board": ["/work-board", "/settings"],
  "/briefing": ["/briefing", ...FOUNDER_LOOP_SPINE_ROUTE_KEYS],
  "/morning-briefing": ["/briefing", ...FOUNDER_LOOP_SPINE_ROUTE_KEYS],
  "/memory": ["/memory", ...FOUNDER_LOOP_SPINE_ROUTE_KEYS],
  "/proof": ["/proof", ...FOUNDER_LOOP_SPINE_ROUTE_KEYS],
  "/evidence": [
    ...FOUNDER_LOOP_SPINE_ROUTE_KEYS,
    "/runs",
    "/critical/dashboard-read-model",
    "/runtime",
  ],
  "/setup": [
    "/setup",
    "/critical/dashboard-read-model",
    "/critical/provider-catalog-read-model",
    "/settings",
  ],
  "/chat": [
    "/chat",
    "/today",
    "/critical/dashboard-read-model",
    "/settings",
  ],
  "/runs": ["/runs", "/settings"],
  "/runtime": ["/runtime"],
  "/settings": [
    ...FOUNDER_LOOP_SPINE_ROUTE_KEYS,
    "/critical/dashboard-read-model",
    "/critical/manifest-read-model",
    "/critical/provider-catalog-read-model",
  ],
  "/workspace/settings": [
    "/settings",
    ...NORTH_STAR_SHELL_ROUTE_KEYS,
    "/critical/manifest-read-model",
    "/critical/provider-catalog-read-model",
  ],
  "/workspace": ["/today", ...NORTH_STAR_SHELL_ROUTE_KEYS],
  "/workspace/today": ["/today", ...NORTH_STAR_SHELL_ROUTE_KEYS],
  "/workspace/decisions": [
    "/actions",
  ],
  "/workspace/work-board": [
    "/work-board",
    "/actions",
    ...NORTH_STAR_SHELL_ROUTE_KEYS,
  ],
  "/workspace/knowledge": [
    "/memory",
    ...NORTH_STAR_SHELL_ROUTE_KEYS,
  ],
  "/workspace/activity-trust": [
    "/trust",
    "/actions",
    "/evidence",
    "/runs",
    ...NORTH_STAR_SHELL_ROUTE_KEYS,
  ],
  "/workspace/onboarding": ["/setup", "/inbox"],
  "/workspace/crm": ["/crm", "/settings"],
};

export function criticalRouteDataIsBackendOwned(
  activePath: string,
  data: ControlCenterData,
): boolean {
  const routeKeys =
    CRITICAL_ROUTE_KEYS[canonicalizeControlCenterPath(activePath)] ?? [];
  return (
    routeKeys.length > 0 &&
    routeKeys.every((route) => data.routeStates[route]?.state === "backend_owned")
  );
}

function CriticalBackendTruthUnavailable({
  activePath,
  retry,
  state,
  surfaceLabel,
}: {
  activePath: string;
  retry: () => Promise<void>;
  state: CriticalBackendTruthState;
  surfaceLabel: string;
}) {
  const lastVerified = state.lastVerified;
  const pending = state.status === "loading";
  const firstRun = state.status === "onboarding";
  const backendRevision =
    lastVerified?.backendRevisionRef ??
    state.truth?.backend_revision_ref ??
    "revision-ref:unavailable";
  return (
    <AppShell activePath={activePath}>
      <section
        aria-labelledby="critical-backend-truth-title"
        aria-live="polite"
        className="route-state-panel"
        data-critical-backend-truth={pending ? "loading" : "unavailable"}
      >
        <p className="eyebrow">
          Backend truth · {pending ? "checking" : firstRun ? "setup required" : "unavailable"}
        </p>
        <h1 id="critical-backend-truth-title">
          {surfaceLabel} is not showing unverified product state
        </h1>
        <p>
          {pending
            ? "Checking the current Python-owned revision and evidence envelope before rendering this critical surface."
            : firstRun
              ? "The backend revision is valid, but this fresh local state has not produced complete durable loop evidence yet. Start Here, Setup, Action Inbox, and the exact Settings authority lane remain available; other critical product claims stay hidden."
            : "The backend truth envelope or a required route read model is unavailable, malformed, stale, out of order, or contract-incompatible. Mock and placeholder success content remains hidden."}
        </p>
        <dl>
          <div>
            <dt>Last verified</dt>
            <dd>{lastVerified?.verifiedAt ?? "No verified snapshot in this session"}</dd>
          </div>
          <div>
            <dt>Source ref</dt>
            <dd>{lastVerified?.sourceRef ?? "source-ref:backend-truth:unavailable"}</dd>
          </div>
          <div>
            <dt>Backend revision</dt>
            <dd>{backendRevision}</dd>
          </div>
          <div>
            <dt>Authority</dt>
            <dd>Read-only local inspection; this UI cannot grant authority.</dd>
          </div>
          {!pending ? (
            <div>
              <dt>Failure ref</dt>
              <dd>{state.errorRef}</dd>
            </div>
          ) : null}
        </dl>
        <button
          disabled={pending}
          onClick={() => {
            void retry();
          }}
          type="button"
        >
          Retry backend and route data
        </button>
        <p>
          Next safe action:{" "}
          {firstRun ? (
            <>
              open <a href="/start">Start Here</a>, <a href="/setup">Setup</a>,
              or the exact <a href="/settings">Settings authority lane</a> to
              establish the first local evidence packet.
            </>
          ) : (
            <>
              restore the local backend or inspect{" "}
              <code>python scripts/dev/uaa_founder_loop.py inspect-backend-truth</code>.
            </>
          )}
        </p>
      </section>
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
  return canonicalizeControlCenterPath(path);
}
