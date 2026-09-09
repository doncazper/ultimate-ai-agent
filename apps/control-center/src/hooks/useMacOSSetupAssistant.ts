import { useEffect, useRef, useState } from "react";
import {
  loadMacOSSetupAssistantRoute,
  type BackendTruthReadBinding,
} from "../api/client";
import type { MacOSSetupAssistantData } from "../api/types";

export type MacOSSetupAssistantLoadState =
  | {
      status: "loading";
      data: null;
      errorRef: null;
      retry: () => void;
    }
  | {
      status: "ready";
      data: MacOSSetupAssistantData;
      errorRef: null;
      retry: () => void;
    }
  | {
      status: "error";
      data: null;
      errorRef: string;
      retry: () => void;
    };

type InternalLoadState =
  | { status: "loading"; data: null; errorRef: null }
  | {
      status: "ready";
      data: MacOSSetupAssistantData;
      errorRef: null;
      backendRevisionRef: string;
      backendInstanceRef: string;
    }
  | { status: "error"; data: null; errorRef: string };

const MACOS_SETUP_SAFE_ERROR_REFS = new Set([
  "BACKEND_RESPONSE_PROVENANCE_MISMATCH",
  "SETUP_ASSISTANT_RESPONSE_INVALID",
]);

export function useMacOSSetupAssistant(
  enabled: boolean,
  binding: BackendTruthReadBinding | null,
): MacOSSetupAssistantLoadState {
  const snapshotRef = binding?.snapshotRef ?? null;
  const backendRevisionRef = binding?.backendRevisionRef ?? null;
  const backendInstanceRef = binding?.backendInstanceRef ?? null;
  const latestSnapshotRef = useRef(snapshotRef);
  latestSnapshotRef.current = snapshotRef;
  const [reloadGeneration, setReloadGeneration] = useState(0);
  const [state, setState] = useState<InternalLoadState>({
    status: "loading",
    data: null,
    errorRef: null,
  });
  const retry = () => setReloadGeneration((generation) => generation + 1);

  useEffect(() => {
    if (!enabled || !backendRevisionRef || !backendInstanceRef) return;
    let active = true;
    setState((current) =>
      current.status === "ready" &&
      current.backendRevisionRef === backendRevisionRef &&
      current.backendInstanceRef === backendInstanceRef
        ? current
        : { status: "loading", data: null, errorRef: null },
    );
    const expectedBinding = latestSnapshotRef.current
      ? {
          snapshotRef: latestSnapshotRef.current,
          backendRevisionRef,
          backendInstanceRef,
        }
      : null;
    loadMacOSSetupAssistantRoute(expectedBinding)
      .then((data) => {
        if (active) {
          setState({
            status: "ready",
            data,
            errorRef: null,
            backendRevisionRef,
            backendInstanceRef,
          });
        }
      })
      .catch((error: unknown) => {
        if (!active) return;
        setState({
          status: "error",
          data: null,
          errorRef:
            error instanceof Error &&
            MACOS_SETUP_SAFE_ERROR_REFS.has(error.message)
              ? error.message
              : "SETUP_ASSISTANT_UNAVAILABLE",
        });
      });
    return () => {
      active = false;
    };
  }, [
    backendInstanceRef,
    backendRevisionRef,
    enabled,
    reloadGeneration,
  ]);

  if (
    enabled &&
    state.status === "ready" &&
    (state.backendRevisionRef !== backendRevisionRef ||
      state.backendInstanceRef !== backendInstanceRef)
  ) {
    return {
      status: "loading",
      data: null,
      errorRef: null,
      retry,
    };
  }
  if (state.status === "ready") {
    const {
      backendRevisionRef: _backendRevisionRef,
      backendInstanceRef: _backendInstanceRef,
      ...visibleState
    } = state;
    return { ...visibleState, retry };
  }
  return { ...state, retry } as MacOSSetupAssistantLoadState;
}
