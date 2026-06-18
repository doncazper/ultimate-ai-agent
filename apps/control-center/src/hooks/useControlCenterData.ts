import { useEffect, useState } from "react";
import { loadControlCenterData } from "../api/client";
import type { ControlCenterData } from "../api/types";

type LoadState =
  | { status: "loading"; data: null; error: null }
  | { status: "ready"; data: ControlCenterData; error: null }
  | { status: "error"; data: ControlCenterData; error: string };

export function useControlCenterData(): LoadState {
  const [state, setState] = useState<LoadState>({ status: "loading", data: null, error: null });

  useEffect(() => {
    let active = true;
    loadControlCenterData()
      .then((data) => {
        if (active) {
          setState({ status: "ready", data, error: null });
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setState({
            status: "error",
            data: {
              ...({} as unknown as ControlCenterData),
              source: "mock",
            },
            error: error instanceof Error ? error.message : "Unable to load Control Center data.",
          });
        }
      });
    return () => {
      active = false;
    };
  }, []);

  return state;
}
