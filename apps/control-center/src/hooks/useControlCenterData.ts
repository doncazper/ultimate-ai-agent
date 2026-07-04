import { useEffect, useState } from "react";
import { loadControlCenterData } from "../api/client";
import type { ControlCenterData } from "../api/types";

type LoadState =
  | { status: "loading"; data: null; error: null }
  | { status: "ready"; data: ControlCenterData; error: null }
  | { status: "error"; data: null; error: string };

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
    };
  }, []);

  return state;
}
