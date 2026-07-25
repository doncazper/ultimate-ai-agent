import { useEffect, useState } from "react";
import { loadControlCenterData } from "../api/client";
import type { ControlCenterData } from "../api/types";

export type ControlCenterDataLoadState =
  | { status: "loading"; data: null; error: null; snapshotRef: null; retry: () => void }
  | {
      status: "ready";
      data: ControlCenterData;
      error: null;
      snapshotRef: string | null;
      retry: () => void;
    }
  | { status: "error"; data: null; error: string; snapshotRef: null; retry: () => void };

type InternalLoadState =
  | { status: "loading"; data: null; error: null; snapshotRef: null }
  | {
      status: "ready";
      data: ControlCenterData;
      error: null;
      snapshotRef: string | null;
    }
  | { status: "error"; data: null; error: string; snapshotRef: null };

const MOCK_FALLBACK_RETRY_DELAYS_MS = [250, 750, 1500, 3000, 5000];

export function useControlCenterData(
  enabled = true,
  snapshotRef: string | null = null,
): ControlCenterDataLoadState {
  const [reloadGeneration, setReloadGeneration] = useState(0);
  const [state, setState] = useState<InternalLoadState>({
    status: "loading",
    data: null,
    error: null,
    snapshotRef: null,
  });
  const retry = () => setReloadGeneration((generation) => generation + 1);

  useEffect(() => {
    if (!enabled) {
      return;
    }
    setState({ status: "loading", data: null, error: null, snapshotRef: null });
    let active = true;
    let retryTimeout: ReturnType<typeof setTimeout> | undefined;
    const load = () => loadControlCenterData();
    const scheduleMockFallbackRetry = (attemptIndex: number) => {
      if (!active || attemptIndex >= MOCK_FALLBACK_RETRY_DELAYS_MS.length) {
        return;
      }
      retryTimeout = setTimeout(() => {
        load()
          .then((retryData) => {
            if (!active) {
              return;
            }
            if (!shouldRetryMockFallback(retryData)) {
              setState({
                status: "ready",
                data: retryData,
                error: null,
                snapshotRef,
              });
              return;
            }
            scheduleMockFallbackRetry(attemptIndex + 1);
          })
          .catch(() => {
            if (active) {
              scheduleMockFallbackRetry(attemptIndex + 1);
            }
          });
      }, MOCK_FALLBACK_RETRY_DELAYS_MS[attemptIndex]);
    };
    load()
      .then((data) => {
        if (active) {
          setState({ status: "ready", data, error: null, snapshotRef });
        }
        if (active && shouldRetryMockFallback(data)) {
          scheduleMockFallbackRetry(0);
        }
      })
      .catch(() => {
        if (active) {
          setState({
            status: "error",
            data: null,
            error:
              "Control Center data could not be loaded safely. Check local backend status and use redacted summaries only.",
            snapshotRef: null,
          });
        }
      });
    return () => {
      active = false;
      if (retryTimeout !== undefined) {
        clearTimeout(retryTimeout);
      }
    };
  }, [enabled, reloadGeneration, snapshotRef]);

  if (
    enabled &&
    state.status === "ready" &&
    state.snapshotRef !== snapshotRef
  ) {
    return {
      status: "loading",
      data: null,
      error: null,
      snapshotRef: null,
      retry,
    };
  }
  return { ...state, retry } as ControlCenterDataLoadState;
}

function shouldRetryMockFallback(data: ControlCenterData): boolean {
  return (
    data.connection.state === "mock_fallback" &&
    data.connection.warnings.includes("LOCAL_BACKEND_UNAVAILABLE")
  );
}
