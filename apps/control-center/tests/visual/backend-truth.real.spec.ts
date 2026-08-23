import { expect, test, type Page, type Request } from "@playwright/test";
import { spawn, spawnSync, type ChildProcess } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { backendTruthPort } from "./ports";

const repoRoot = resolve(import.meta.dirname, "../../../..");
const python =
  process.env.UAA_TEST_PYTHON ?? resolve(repoRoot, ".venv/bin/python");
const stateDir = mkdtempSync(join(tmpdir(), "uaa-backend-truth-browser-"));
const backendBaseUrl = `http://127.0.0.1:${backendTruthPort}`;
const backendTruthTestNow = "2026-07-22T18:00:00Z";
const backendSourceCommit = resolveBackendSourceCommit();
let backend: ChildProcess | null = null;

const backendOwnedVisualSurfaces = [
  ["overview", "/"],
  ["start", "/start"],
  ["today", "/today"],
  ["actions", "/actions"],
  ["plans", "/plans"],
  ["proof", "/proof"],
  ["memory", "/memory"],
  ["evidence", "/evidence"],
  ["setup", "/setup"],
] as const;

const foundationVisualSurfaces = [
  ["work-board", "/work-board", "/control-center/work-board"],
  ["crm", "/crm", "/control-center/crm/summary"],
] as const;

function resolveBackendSourceCommit(): string {
  const result = spawnSync(
    "/usr/bin/git",
    ["rev-parse", "--verify", "HEAD"],
    {
      cwd: repoRoot,
      encoding: "utf8",
    },
  );
  const commit = result.stdout.trim();
  if (result.status !== 0 || !/^[0-9a-f]{40}$/.test(commit)) {
    throw new Error("BACKEND_TRUTH_TEST_SOURCE_COMMIT_UNAVAILABLE");
  }
  return commit;
}

function isPageBackendRead(request: Request): boolean {
  if (request.method() !== "GET") return false;
  const path = new URL(request.url()).pathname;
  return (
    path.startsWith("/control-center/") ||
    path.startsWith("/api/runtime/") ||
    path.startsWith("/runtime/")
  );
}

function observePageBackendReads(page: Page) {
  const inFlight = new Set<Request>();
  let failureRef: string | null = null;
  let completedReadCount = 0;
  let cleanupCancellationCount = 0;
  let teardownStarted = false;

  page.on("request", (request) => {
    if (isPageBackendRead(request)) inFlight.add(request);
  });
  page.on("response", (response) => {
    if (isPageBackendRead(response.request()) && !response.ok()) {
      failureRef = "BACKEND_READ_HTTP_FAILURE";
    }
  });
  page.on("requestfinished", (request) => {
    if (inFlight.delete(request)) completedReadCount += 1;
  });
  page.on("requestfailed", (request) => {
    if (inFlight.delete(request)) {
      const errorText = request.failure()?.errorText;
      if (teardownStarted && errorText === "net::ERR_ABORTED") {
        cleanupCancellationCount += 1;
      } else {
        failureRef = "BACKEND_READ_TRANSPORT_FAILURE";
      }
    }
  });

  return {
    beginTeardown() {
      expect(failureRef, "BACKEND_READ_PRE_BOUNDARY_FAILURE").toBeNull();
      expect(
        completedReadCount,
        "BACKEND_READ_ACCOUNTING_MISSING",
      ).toBeGreaterThan(0);
      teardownStarted = true;
    },
    finishTeardown() {
      expect(failureRef, "BACKEND_READ_TEARDOWN_FAILURE").toBeNull();
      expect(page.isClosed(), "BACKEND_READ_PAGE_CLOSE_REQUIRED").toBe(true);
      cleanupCancellationCount += inFlight.size;
      inFlight.clear();
      expect(inFlight.size, "BACKEND_READ_TEARDOWN_INCOMPLETE").toBe(0);
      return { cleanupCancellationCount, completedReadCount };
    },
  };
}

function startBackend({ corruptReceipt = false } = {}): void {
  backend = spawn(
    python,
    [resolve(repoRoot, "scripts/dev/run_backend_truth_test_server.py")],
    {
      cwd: repoRoot,
      env: {
        ...process.env,
        PYTHONPATH: resolve(repoRoot, "src"),
        UAA_BACKEND_TRUTH_TEST_STATE_DIR: stateDir,
        UAA_BACKEND_TRUTH_TEST_PORT: String(backendTruthPort),
        UAA_BACKEND_TRUTH_TEST_NOW: backendTruthTestNow,
        UAA_BUILD_COMMIT: backendSourceCommit,
        UAA_BACKEND_TRUTH_TEST_CORRUPT_RECEIPT: corruptReceipt ? "1" : "0",
      },
      stdio: "ignore",
    },
  );
}

async function waitForBackend(): Promise<void> {
  for (let attempt = 0; attempt < 300; attempt += 1) {
    if (backend?.exitCode !== null) {
      throw new Error("BACKEND_TRUTH_TEST_SERVER_EXITED_EARLY");
    }
    try {
      const response = await fetch(`${backendBaseUrl}/health`);
      if (response.ok) return;
    } catch {
      // Bounded readiness polling only.
    }
    await new Promise((resolveWait) => setTimeout(resolveWait, 100));
  }
  throw new Error("BACKEND_TRUTH_TEST_SERVER_NOT_READY");
}

async function stopBackend(): Promise<void> {
  const processToStop = backend;
  backend = null;
  if (!processToStop || processToStop.exitCode !== null) return;
  processToStop.kill("SIGTERM");
  await new Promise<void>((resolveExit) => {
    const timeout = setTimeout(() => {
      processToStop.kill("SIGKILL");
      resolveExit();
    }, 5_000);
    processToStop.once("exit", () => {
      clearTimeout(timeout);
      resolveExit();
    });
  });
}

test.beforeAll(async () => {
  startBackend();
  await waitForBackend();
});

test.afterAll(async () => {
  await stopBackend();
  rmSync(stateDir, { recursive: true, force: true });
});

test("foundation visual baselines stay backend-owned", async ({
  context,
  request,
}) => {
  test.setTimeout(180_000);
  const truthResponse = await request.get(
    `${backendBaseUrl}/control-center/backend-truth`,
  );
  expect(truthResponse.ok()).toBe(true);
  const truth = await truthResponse.json();
  expect(truth.data.evidence_binding.status).toBe("verified_complete");
  expect(truth.data.backend_revision_ref).toBe(
    `commit-ref:git:${backendSourceCommit}`,
  );
  const fixedNow = new Date(truth.data.generated_at).getTime() + 1_000;

  for (const [name, route, prioritizedEndpoint] of foundationVisualSurfaces) {
    await test.step(`capture backend-owned ${name}`, async () => {
      const page = await context.newPage();
      await page.route(`**${prioritizedEndpoint}`, async (backendRoute) => {
        const response = await backendRoute.fetch({
          url: `${backendBaseUrl}${prioritizedEndpoint}`,
        });
        await backendRoute.fulfill({ response });
      });
      const backendReads = observePageBackendReads(page);
      await page.addInitScript((timestamp) => {
        const RealDate = Date;
        class FixedDate extends RealDate {
          constructor(...args: unknown[]) {
            if (args.length === 0) {
              super(timestamp);
              return;
            }
            super(...(args as [number]));
          }

          static now() {
            return timestamp;
          }
        }
        globalThis.Date = FixedDate as DateConstructor;
      }, fixedNow);
      await page.goto(route);
      await expect(
        page.getByRole("heading", {
          name: /is not showing unverified product state$/,
        }),
      ).toHaveCount(0, { timeout: 30_000 });
      await expect(page.getByText("Mock fallback active")).toHaveCount(0);
      if (name === "work-board") {
        await expect(page.getByTestId("work-board")).toBeVisible({
          timeout: 30_000,
        });
        await expect(page.getByText("Backend-owned Work Board")).toBeVisible();
      } else {
        await expect(
          page.getByRole("heading", { name: "UAA CRM local command center" }),
        ).toBeVisible({ timeout: 30_000 });
        await expect(
          page.getByText("backend-owned", { exact: true }),
        ).toBeVisible();
      }
      await expect(page).toHaveScreenshot(`${name}.png`, {
        animations: "disabled",
        fullPage: true,
      });
      backendReads.beginTeardown();
      await page.close();
      backendReads.finishTeardown();
    });
  }
});

test("critical founder-loop baselines stay backend-owned", async (
  { context, request },
  testInfo,
) => {
  test.skip(
    testInfo.project.name === "mobile",
    "Mobile uses scoped foundation baselines only",
  );
  test.setTimeout(300_000);
  const initialTruthResponse = await request.get(
    `${backendBaseUrl}/control-center/backend-truth`,
  );
  expect(initialTruthResponse.ok()).toBe(true);
  const initialTruth = await initialTruthResponse.json();
  expect(initialTruth.data.evidence_binding.status).toBe("verified_complete");
  expect(initialTruth.data.backend_revision_ref).toBe(
    `commit-ref:git:${backendSourceCommit}`,
  );
  const fixedNow = new Date(initialTruth.data.generated_at).getTime() + 1_000;

  for (const [name, route] of backendOwnedVisualSurfaces) {
    await test.step(`capture backend-owned ${name}`, async () => {
      const page = await context.newPage();
      const backendReads = observePageBackendReads(page);
      await page.addInitScript((timestamp) => {
        const RealDate = Date;
        class FixedDate extends RealDate {
          constructor(...args: unknown[]) {
            if (args.length === 0) {
              super(timestamp);
              return;
            }
            super(...(args as [number]));
          }

          static now() {
            return timestamp;
          }
        }
        globalThis.Date = FixedDate as DateConstructor;
      }, fixedNow);
      await page.goto(route);
      await expect(
        page.getByRole("heading", {
          name: /is not showing unverified product state$/,
        }),
      ).toHaveCount(0, { timeout: 30_000 });
      await expect(page.getByText("Mock fallback active")).toHaveCount(0);
      await expect(page.locator("main")).toBeVisible();
      await expect(page).toHaveScreenshot(`${name}.png`, {
        animations: "disabled",
        fullPage: true,
      });
      backendReads.beginTeardown();
      await page.close();
      const accounting = backendReads.finishTeardown();
      test.info().annotations.push({
        type: "backend-read-cleanup",
        description:
          `content-free:completed=${accounting.completedReadCount};` +
          `cleanup-cancelled=${accounting.cleanupCancellationCount}`,
      });
    });
  }
});

test("critical founder loop fails closed on backend loss and survives durable restart", async (
  { page, request },
  testInfo,
) => {
  test.skip(
    testInfo.project.name === "mobile",
    "Mobile uses scoped foundation baselines only",
  );
  test.setTimeout(180_000);
  const initialTruthResponse = await request.get(
    `${backendBaseUrl}/control-center/backend-truth`,
  );
  expect(initialTruthResponse.ok()).toBe(true);
  const initialTruth = await initialTruthResponse.json();
  expect(initialTruth.data.evidence_binding.status).toBe("verified_complete");
  expect(initialTruth.data.backend_revision_ref).toBe(
    `commit-ref:git:${backendSourceCommit}`,
  );
  const fixedNow = new Date(initialTruth.data.generated_at).getTime() + 1_000;
  await page.addInitScript((timestamp) => {
    const RealDate = Date;
    class FixedDate extends RealDate {
      constructor(...args: unknown[]) {
        if (args.length === 0) {
          super(timestamp);
          return;
        }
        super(...(args as [number]));
      }

      static now() {
        return timestamp;
      }
    }
    globalThis.Date = FixedDate as DateConstructor;
  }, fixedNow);
  await page.goto("/today");
  await expect(
    page.getByRole("region", { name: "Today" }),
  ).toBeVisible({ timeout: 30_000 });
  await expect(
    page.getByRole("heading", {
      name: /is not showing unverified product state$/,
    }),
  ).toHaveCount(0, { timeout: 30_000 });

  const cli = spawnSync(
    python,
    [
      resolve(repoRoot, "scripts/dev/uaa_founder_loop.py"),
      "--state-dir",
      stateDir,
      "inspect-backend-truth",
    ],
    {
      cwd: repoRoot,
      env: {
        ...process.env,
        PYTHONPATH: resolve(repoRoot, "src"),
        UAA_BUILD_COMMIT: backendSourceCommit,
      },
      encoding: "utf8",
    },
  );
  expect(cli.status, cli.stderr).toBe(0);
  const cliTruth = JSON.parse(cli.stdout).backend_truth;
  expect(cliTruth.evidence_binding.status).toBe("verified_complete");
  expect(cliTruth.backend_revision_ref).toBe(
    initialTruth.data.backend_revision_ref,
  );

  await stopBackend();
  await expect(
    page.getByRole("heading", {
      name: "Today is not showing unverified product state",
    }),
  ).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText(initialTruth.data.backend_revision_ref)).toBeVisible();
  await expect(page.getByText("Mock fallback active")).toHaveCount(0);
  await expect(page).toHaveScreenshot("backend-truth-unavailable.png", {
    animations: "disabled",
    fullPage: true,
    mask: [
      page.locator(
        '[data-critical-backend-truth] dt:has-text("Last verified") + dd',
      ),
    ],
  });

  startBackend();
  await waitForBackend();
  const restartedActions = await request.get(
    `${backendBaseUrl}/control-center/actions/inbox`,
  );
  expect(restartedActions.ok()).toBe(true);
  await page
    .getByRole("button", { name: "Retry backend and route data" })
    .click();
  await expect(
    page.getByRole("region", { name: "Today" }),
  ).toBeVisible({ timeout: 30_000 });
  await expect(
    page.getByRole("heading", {
      name: /is not showing unverified product state$/,
    }),
  ).toHaveCount(0, { timeout: 30_000 });
  const reloadedTruth = await request.get(
    `${backendBaseUrl}/control-center/backend-truth`,
  );
  expect(reloadedTruth.ok()).toBe(true);
  expect((await reloadedTruth.json()).data.evidence_binding.status).toBe(
    "verified_complete",
  );

  await stopBackend();
  startBackend({ corruptReceipt: true });
  await waitForBackend();
  await page.reload();
  await expect(
    page.getByText("BACKEND_TRUTH_EVIDENCE_INVALID"),
  ).toBeVisible({ timeout: 30_000 });
  await expect(
    page.getByRole("heading", {
      name: "Today is not showing unverified product state",
    }),
  ).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("Backend-owned proof pass")).toHaveCount(0);
  const corruptedTruth = await request.get(
    `${backendBaseUrl}/control-center/backend-truth`,
  );
  expect(corruptedTruth.ok()).toBe(true);
  expect((await corruptedTruth.json()).data.evidence_binding.status).toBe(
    "invalid_evidence",
  );
});
