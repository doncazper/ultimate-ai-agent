import { configDefaults, defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    proxy: {
      "/control-center": {
        target: "http://127.0.0.1:8000",
        changeOrigin: false,
      },
      "/runtime/readiness": {
        target: "http://127.0.0.1:8000",
        changeOrigin: false,
      },
      "/runtime/capability-matrix": {
        target: "http://127.0.0.1:8000",
        changeOrigin: false,
      },
      "/runtime/smoke-reports": {
        target: "http://127.0.0.1:8000",
        changeOrigin: false,
      },
    },
  },
  test: {
    environment: "jsdom",
    exclude: [...configDefaults.exclude, "tests/visual/**", "tests/smoke/**"],
    globals: true,
    setupFiles: "./src/test/setup.ts",
  },
});
