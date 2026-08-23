import { expect, test } from "@playwright/test";
import { spawn, spawnSync, type ChildProcess } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { backendTruthPort } from "./ports";

const repoRoot = resolve(import.meta.dirname, "../../../..");
const python =
  process.env.UAA_TEST_PYTHON ?? resolve(repoRoot, ".venv/bin/python");
const stateDir = mkdtempSync(join(tmpdir(), "uaa-foundation-visuals-"));
const backendBaseUrl = `http://127.0.0.1:${backendTruthPort}`;
const backendTruthTestNow = "2026-07-22T18:00:00Z";
const backendSourceCommit = resolveBackendSourceCommit();
let backend: ChildProcess | null = null;

const foundationVisualSurfaces = [
  ["work-board", "/work-board", "/control-center/work-board"],
  ["crm", "/crm", "/control-center/crm/summary"],
] as const;

function resolveBackendSourceCommit(): string {
  const result = spawnSync("/usr/bin/git", ["rev-parse", "--verify", "HEAD"], {
    cwd: repoRoot,
    encoding: "utf8",
  });
  const commit = result.stdout.trim();
  if (result.status !== 0 || !/^[0-9a-f]{40}$/.test(commit)) {
    throw new Error("FOUNDATION_VISUAL_SOURCE_COMMIT_UNAVAILABLE");
  }
  return commit;
}

function startBackend(): void {
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
        UAA_CRM_STATE_DIR: join(stateDir, "crm"),
        UAA_WORK_BOARD_STATE_DIR: join(stateDir, "work-board"),
      },
      stdio: "ignore",
    },
  );
}

async function waitForBackend(): Promise<void> {
  for (let attempt = 0; attempt < 300; attempt += 1) {
    if (backend?.exitCode !== null) {
      throw new Error("FOUNDATION_VISUAL_BACKEND_EXITED_EARLY");
    }
    try {
      const response = await fetch(`${backendBaseUrl}/health`);
      if (response.ok) return;
    } catch {
      // Bounded readiness polling only.
    }
    await new Promise((resolveWait) => setTimeout(resolveWait, 100));
  }
  throw new Error("FOUNDATION_VISUAL_BACKEND_NOT_READY");
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
      let prioritizedReadCount = 0;
      await page.route(`**${prioritizedEndpoint}`, async (backendRoute) => {
        const response = await backendRoute.fetch({
          url: `${backendBaseUrl}${prioritizedEndpoint}`,
        });
        expect(response.ok()).toBe(true);
        expect(response.headers()["x-uaa-backend-revision-ref"]).toBe(
          `commit-ref:git:${backendSourceCommit}`,
        );
        prioritizedReadCount += 1;
        await backendRoute.fulfill({ response });
      });
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
      expect(prioritizedReadCount).toBeGreaterThan(0);
      await expect(page).toHaveScreenshot(`${name}.png`, {
        animations: "disabled",
        fullPage: true,
      });
      await page.close();
    });
  }
});
