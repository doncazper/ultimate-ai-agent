import { configDefaults, defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const rootDirectory = fileURLToPath(new URL(".", import.meta.url));

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
