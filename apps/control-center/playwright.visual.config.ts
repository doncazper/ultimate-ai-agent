import { defineConfig, devices } from "@playwright/test";

const visualPort = Number(process.env.CONTROL_CENTER_VISUAL_PORT ?? "5177");
const visualBaseUrl = `http://127.0.0.1:${visualPort}`;
const reuseExistingVisualServer =
  process.env.CONTROL_CENTER_VISUAL_REUSE_EXISTING_SERVER === "1";

export default defineConfig({
  testDir: "./tests/visual",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["dot"], ["github"]] : [["list"]],
  snapshotPathTemplate: "{testDir}/__snapshots__/{projectName}/{arg}{ext}",
  use: {
    baseURL: visualBaseUrl,
    colorScheme: "light",
    trace: "retain-on-failure",
  },
  expect: {
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.015,
      threshold: 0.2,
    },
  },
  webServer: {
    command: `npm run dev -- --host 127.0.0.1 --port ${visualPort} --strictPort --clearScreen false`,
    url: visualBaseUrl,
    reuseExistingServer: reuseExistingVisualServer,
    timeout: 120_000,
  },
  projects: [
    {
      name: "desktop",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 1000 },
        deviceScaleFactor: 1,
      },
    },
    {
      name: "mobile",
      use: {
        ...devices["Pixel 5"],
        viewport: { width: 390, height: 844 },
        deviceScaleFactor: 1,
      },
    },
  ],
});
