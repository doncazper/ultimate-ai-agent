/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_UAA_API_BASE_URL?: string;
  readonly VITE_UAA_BACKEND_MODE?: "fallback" | "strict";
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
