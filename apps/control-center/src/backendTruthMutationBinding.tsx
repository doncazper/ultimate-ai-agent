import {
  createContext,
  type ReactNode,
  useContext,
} from "react";
import type { BackendTruthReadBinding } from "./api/client";

const BackendTruthMutationBindingContext =
  createContext<BackendTruthReadBinding | null>(null);

export function BackendTruthMutationBindingProvider({
  binding,
  children,
}: {
  binding: BackendTruthReadBinding | null;
  children: ReactNode;
}) {
  return (
    <BackendTruthMutationBindingContext.Provider value={binding}>
      {children}
    </BackendTruthMutationBindingContext.Provider>
  );
}

export function useBackendTruthMutationBinding(): BackendTruthReadBinding | null {
  return useContext(BackendTruthMutationBindingContext);
}
