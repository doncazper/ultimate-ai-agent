import { useCallback, useEffect, useRef, useState } from "react";
import { loadControlCenterBackendTruth } from "../api/client";
import type { ControlCenterBackendTruth } from "../api/types";

const REFRESH_DELAY_MS = 20_000;

export interface LastVerifiedBackendTruth {
  verifiedAt: string;
  sourceRef: string;
  backendRevisionRef: string;
}

export type CriticalBackendTruthState =
  | {
      status: "loading";
      truth: null;
      errorRef: null;
      lastVerified: LastVerifiedBackendTruth | null;
      retry: () => void;
    }
  | {
      status: "ready";
      truth: ControlCenterBackendTruth;
      errorRef: null;
      lastVerified: LastVerifiedBackendTruth;
      retry: () => void;
    }
  | {
      status: "degraded";
      truth: null;
      errorRef: string;
      lastVerified: LastVerifiedBackendTruth | null;
      retry: () => void;
    };

export function useCriticalBackendTruth(
  enabled = true,
  loader: () => Promise<ControlCenterBackendTruth> = loadControlCenterBackendTruth,
): CriticalBackendTruthState {
  const generation = useRef(0);
  const activation = useRef(0);
  const previousEnabled = useRef(enabled);
  const lastVerified = useRef<LastVerifiedBackendTruth | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [state, setState] = useState<
    Omit<CriticalBackendTruthState, "retry"> & { activation: number }
  >({
    status: "loading",
    truth: null,
    errorRef: null,
    lastVerified: null,
    activation: 0,
  });

  if (previousEnabled.current !== enabled) {
    previousEnabled.current = enabled;
    activation.current += 1;
  }

  const refresh = useCallback(() => {
    if (!enabled) return;
    const requestGeneration = ++generation.current;
    const requestActivation = activation.current;
    if (timer.current) clearTimeout(timer.current);
    loader()
      .then((truth) => {
        if (requestGeneration !== generation.current) return;
        if (truth.evidence_binding.status !== "verified_complete") {
          throw new Error(
            truth.evidence_binding.status === "invalid_evidence"
              ? "BACKEND_TRUTH_EVIDENCE_INVALID"
              : "BACKEND_TRUTH_EVIDENCE_INCOMPLETE",
          );
        }
        const verified = {
          verifiedAt: new Date().toISOString(),
          sourceRef: truth.source_ref,
          backendRevisionRef: truth.backend_revision_ref,
        };
        lastVerified.current = verified;
        setState({
          status: "ready",
          truth,
          errorRef: null,
          lastVerified: verified,
          activation: requestActivation,
        });
      })
      .catch((error: unknown) => {
        if (requestGeneration !== generation.current) return;
        setState({
          status: "degraded",
          truth: null,
          errorRef:
            error instanceof Error && /^[A-Z0-9_:-]+$/.test(error.message)
              ? error.message
              : "BACKEND_TRUTH_UNAVAILABLE",
          lastVerified: lastVerified.current,
          activation: requestActivation,
        });
      })
      .finally(() => {
        if (requestGeneration === generation.current) {
          timer.current = setTimeout(refresh, REFRESH_DELAY_MS);
        }
      });
  }, [enabled, loader]);

  useEffect(() => {
    if (!enabled) return;
    refresh();
    return () => {
      generation.current += 1;
      if (timer.current) clearTimeout(timer.current);
    };
  }, [enabled, refresh]);

  if (!enabled || state.activation !== activation.current) {
    return {
      status: "loading",
      truth: null,
      errorRef: null,
      lastVerified: lastVerified.current,
      retry: refresh,
    };
  }

  const { activation: _activation, ...visibleState } = state;
  return { ...visibleState, retry: refresh } as CriticalBackendTruthState;
}
