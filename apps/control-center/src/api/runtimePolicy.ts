export type ControlCenterBackendMode = "fallback" | "strict";

export const STRICT_BACKEND_ERROR_CODE = "STRICT_BACKEND_DATA_UNAVAILABLE";

export class StrictBackendDataError extends Error {
  readonly code = STRICT_BACKEND_ERROR_CODE;

  constructor() {
    super(
      "Strict backend mode blocked non-authoritative or incomplete Control Center data. Check the local backend and use redacted CLI evidence until every required read model is available.",
    );
    this.name = "StrictBackendDataError";
  }
}

export function controlCenterBackendMode(): ControlCenterBackendMode {
  return resolveControlCenterBackendMode(
    import.meta.env.VITE_UAA_BACKEND_MODE,
    import.meta.env.PROD,
  );
}

export function resolveControlCenterBackendMode(
  configured: string | undefined,
  production: boolean,
): ControlCenterBackendMode {
  if (production) {
    return "strict";
  }
  return configured === "strict" ? "strict" : "fallback";
}

export function strictBackendModeEnabled(): boolean {
  return controlCenterBackendMode() === "strict";
}

export function strictBackendDataFailureRequired(
  usingFallback: boolean,
  mode: ControlCenterBackendMode = controlCenterBackendMode(),
): boolean {
  return usingFallback && mode === "strict";
}
