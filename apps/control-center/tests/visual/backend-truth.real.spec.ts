import { expect, test } from "@playwright/test";
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
let backend: ChildProcess | null = null;

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
        UAA_BUILD_COMMIT: "1".repeat(40),
        UAA_BACKEND_TRUTH_TEST_CORRUPT_RECEIPT: corruptReceipt ? "1" : "0",
      },
      stdio: "ignore",
    },
  );
}

async function waitForBackend(): Promise<void> {
  for (let attempt = 0; attempt < 80; attempt += 1) {
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

test("critical founder loop fails closed on backend loss and survives durable restart", async ({
  page,
  request,
}) => {
  test.setTimeout(120_000);
  await page.goto("/today");
  await expect(
    page.getByRole("region", { name: "Today" }),
  ).toBeVisible({ timeout: 30_000 });

  const initialTruthResponse = await request.get(
    `${backendBaseUrl}/control-center/backend-truth`,
  );
  expect(initialTruthResponse.ok()).toBe(true);
  const initialTruth = await initialTruthResponse.json();
  expect(initialTruth.data.evidence_binding.status).toBe("verified_complete");
  expect(initialTruth.data.backend_revision_ref).toBe(
    `commit-ref:git:${"1".repeat(40)}`,
  );

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
        UAA_BUILD_COMMIT: "1".repeat(40),
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
  await page.getByRole("button", { name: "Retry backend truth" }).click();
  await expect(
    page.getByRole("region", { name: "Today" }),
  ).toBeVisible({ timeout: 30_000 });
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
    page.getByRole("heading", {
      name: "Today is not showing unverified product state",
    }),
  ).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("BACKEND_TRUTH_EVIDENCE_INVALID")).toBeVisible();
  await expect(page.getByText("Backend-owned proof pass")).toHaveCount(0);
  const corruptedTruth = await request.get(
    `${backendBaseUrl}/control-center/backend-truth`,
  );
  expect(corruptedTruth.ok()).toBe(true);
  expect((await corruptedTruth.json()).data.evidence_binding.status).toBe(
    "invalid_evidence",
  );
});
