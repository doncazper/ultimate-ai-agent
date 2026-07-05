import { useEffect, useState } from "react";
import { loadControlCenterData } from "../api/client";
import type { ControlCenterData } from "../api/types";

type LoadState =
  | { status: "loading"; data: null; error: null }
  | { status: "ready"; data: ControlCenterData; error: null }
  | { status: "error"; data: null; error: string };

const MOCK_FALLBACK_RETRY_DELAYS_MS = [250, 750, 1500, 3000, 5000];

export function useControlCenterData(): LoadState {
  const [state, setState] = useState<LoadState>({ status: "loading", data: null, error: null });

  useEffect(() => {
    let active = true;
    let retryTimeout: ReturnType<typeof setTimeout> | undefined;
    const scheduleMockFallbackRetry = (attemptIndex: number) => {
      if (!active || attemptIndex >= MOCK_FALLBACK_RETRY_DELAYS_MS.length) {
        return;
      }
      retryTimeout = setTimeout(() => {
        loadControlCenterData()
          .then((retryData) => {
            if (!active) {
              return;
            }
            if (!shouldRetryMockFallback(retryData)) {
              setState({ status: "ready", data: retryData, error: null });
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
    loadControlCenterData()
      .then((data) => {
        if (active) {
          setState({ status: "ready", data, error: null });
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
          });
        }
      });
    return () => {
      active = false;
      if (retryTimeout !== undefined) {
        clearTimeout(retryTimeout);
      }
    };
  }, []);

  return state;
}

function shouldRetryMockFallback(data: ControlCenterData): boolean {
  return (
    data.connection.state === "mock_fallback" &&
    data.connection.warnings.includes("LOCAL_BACKEND_UNAVAILABLE")
  );
}
