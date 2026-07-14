import { useEffect, useState } from "react";
import {
  loadRuntimeSkillMarketplacePosture,
  type RuntimeSkillMarketplacePostureLoadResult,
} from "../api/client";

type SkillMarketplaceLoadState =
  | { status: "loading"; data: null }
  | { status: "ready"; data: RuntimeSkillMarketplacePostureLoadResult };

export function useSkillMarketplacePosture(): SkillMarketplaceLoadState {
  const [state, setState] = useState<SkillMarketplaceLoadState>({
    status: "loading",
    data: null,
  });

  useEffect(() => {
    let active = true;
    loadRuntimeSkillMarketplacePosture().then((data) => {
      if (active) {
        setState({ status: "ready", data });
      }
    });
    return () => {
      active = false;
    };
  }, []);

  return state;
}
