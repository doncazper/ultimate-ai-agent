import { useEffect, useState } from "react";
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

export function useMacOSSetupAssistant(
  enabled: boolean,
  binding: BackendTruthReadBinding | null,
): MacOSSetupAssistantLoadState {
  const [reloadGeneration, setReloadGeneration] = useState(0);
  const [state, setState] = useState<
    Omit<MacOSSetupAssistantLoadState, "retry">
  >({ status: "loading", data: null, errorRef: null });
  const retry = () => setReloadGeneration((generation) => generation + 1);

  useEffect(() => {
    if (!enabled || binding === null) return;
    let active = true;
    setState({ status: "loading", data: null, errorRef: null });
    loadMacOSSetupAssistantRoute(binding)
      .then((data) => {
        if (active) setState({ status: "ready", data, errorRef: null });
      })
      .catch((error: unknown) => {
        if (!active) return;
        setState({
          status: "error",
          data: null,
          errorRef:
            error instanceof Error && /^[A-Z0-9_:-]+$/.test(error.message)
              ? error.message
              : "SETUP_ASSISTANT_UNAVAILABLE",
        });
      });
    return () => {
      active = false;
    };
  }, [
    binding?.backendInstanceRef,
    binding?.backendRevisionRef,
    binding?.snapshotRef,
    enabled,
    reloadGeneration,
  ]);

  return { ...state, retry } as MacOSSetupAssistantLoadState;
}
