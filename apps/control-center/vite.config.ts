import { configDefaults, defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const rootDirectory = fileURLToPath(new URL(".", import.meta.url));
const configuredProxyTarget = process.env.VITE_UAA_PROXY_TARGET ?? "";
const localProxyTarget = /^http:\/\/(?:127\.0\.0\.1|localhost):\d{2,5}$/.test(
  configuredProxyTarget,
)
  ? configuredProxyTarget
  : "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        controlCenter: resolve(rootDirectory, "index.html"),
        iconLibrary: resolve(rootDirectory, "icon-library.html"),
      },
    },
  },
  server: {
    host: "127.0.0.1",
    proxy: {
      "/api": {
        target: localProxyTarget,
        changeOrigin: false,
      },
      "/control-center": {
        target: localProxyTarget,
        changeOrigin: false,
      },
      "/runtime/readiness": {
        target: localProxyTarget,
        changeOrigin: false,
      },
      "/runtime/capability-matrix": {
        target: localProxyTarget,
        changeOrigin: false,
      },
      "/runtime/smoke-reports": {
        target: localProxyTarget,
        changeOrigin: false,
      },
    },
  },
  test: {
    environment: "jsdom",
    exclude: [...configDefaults.exclude, "tests/visual/**", "tests/smoke/**"],
    globals: true,
    setupFiles: "./src/test/setup.ts",
    testTimeout: 15_000,
  },
});
