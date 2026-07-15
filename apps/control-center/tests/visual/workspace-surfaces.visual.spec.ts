import { expect, test, type Route } from "@playwright/test";

const workspaceSurfaces = [
  ["today", "/workspace/today", "Today"],
  ["communications", "/workspace/communications", "Communications"],
  ["messenger", "/workspace/messenger", "UAA Development"],
  ["work-board", "/workspace/work-board", "Work Board"],
  ["crm", "/workspace/crm", "CRM"],
  ["calendar", "/workspace/calendar", "Calendar"],
  ["news", "/workspace/news", "News"],
  ["studio", "/workspace/studio", "Skill Workbench"],
  ["knowledge", "/workspace/knowledge", "Knowledge"],
  ["activity-trust", "/workspace/activity-trust", "Trust"],
  ["customize", "/workspace/customize", "Customize"],
  ["settings", "/workspace/settings", "Settings"],
  ["developer-tools", "/workspace/developer-tools", "Developer Tools"],
  ["terminal", "/workspace/developer-tools/terminal", "Developer Tools · Terminal"],
  ["decisions", "/workspace/decisions", "Review 5 decisions"],
  ["onboarding", "/workspace/onboarding", "Set up your Control Center"],
] as const;

const legacyRenderSurfaces = [
  ["01-today", "Morning Briefing"],
  ["02-action-inbox", "Approval Envelope"],
  ["03-plans-work-board", "Q2 Platform Hardening"],
  ["04-trust", "Mode / Domain authority matrix"],
  ["05-evidence-proof", "Receipt (selected)"],
  ["06-memory", "Reviewed recall"],
  ["07-setup", "System prerequisites"],
  ["08-coding", "Safe diff summary"],
  ["09-sources-crm-briefing", "Morning Briefing"],
  ["10-chat-handoff", "Plan proposal"],
  ["11-start-overview", "Start Here"],
  ["12-settings-authority", "Configure local autonomy guardrails."],
  ["13-models", "Model candidates"],
  ["14-files-context", "Context Proposals"],
  ["15-action-preview", "Potential issues"],
  ["16-runtime-storage", "Command lanes (approval-bound)"],
  ["17-future-governance", "Maturity matrix"],
  ["18-private-trial", "Acceptance ledger"],
  ["19-operator-loop", "No hidden authority"],
] as const;

test.beforeEach(async ({ page }) => {
  const unavailable = async (route: Route) => {
    await route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ success: false, error: { message: "workspace-visual-fixture" } }),
    });
  };
  await page.route("**/control-center/**", unavailable);
  await page.route("**/runtime/**", unavailable);
});

for (const [name, route, visibleText] of workspaceSurfaces) {
  test(`${name} workspace representation renders`, async ({ page }) => {
    await page.goto(route);
    await expect(page.getByText(visibleText, { exact: true }).first()).toBeVisible();
    await expect(page.locator("body")).not.toContainText("Unknown Control Center icon");
    await expect(page.locator("body")).not.toContainText("Something went wrong");
    const horizontalOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > window.innerWidth,
    );
    expect(horizontalOverflow).toBe(false);
  });
}

test("workspace preview renders while every backend read is pending", async ({ page }) => {
  const keepPending = async () => undefined;
  await page.route("**/control-center/**", keepPending);
  await page.route("**/runtime/**", keepPending);

  await page.goto("/workspace/crm", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "CRM v3" })).toBeVisible({
    timeout: 2_500,
  });
  await expect(page.getByText("Preview data", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /^Call$/i })).toBeDisabled();
});

for (const [route, visibleText] of legacyRenderSurfaces) {
  test(`legacy render ${route} has a code-native representation`, async ({ page }) => {
    await page.setViewportSize({ width: 1586, height: 992 });
    await page.goto(`/workspace/reference/${route}`);
    await expect(page.getByText(visibleText, { exact: true }).first()).toBeVisible();
    await expect(page.getByText(/Reference build \d{2}\/19/)).toBeVisible();
    await expect(page.getByText("Not backend-wired", { exact: true })).toBeVisible();
    await expect(page.locator(".legacy-main button").first()).toBeDisabled();
    await expect(page.locator("body")).not.toContainText("Unknown Control Center icon");
    await expect(page.locator("body")).not.toContainText("Something went wrong");
    const horizontalOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > window.innerWidth,
    );
    expect(horizontalOverflow).toBe(false);
  });
}

test("legacy preview controls cannot trigger incidental navigation", async ({ page }) => {
  await page.setViewportSize({ width: 1586, height: 992 });
  await page.goto("/workspace/reference/08-coding");
  const routeBefore = page.url();
  const previewControl = page.locator(".legacy-main button").first();

  await expect(previewControl).toBeDisabled();
  await previewControl.click({ force: true });
  await expect(page).toHaveURL(routeBefore);
  await expect(page.getByText("Not backend-wired", { exact: true })).toBeVisible();
});

test("legacy authority matrix keeps every mode inside its pane", async ({ page }) => {
  await page.setViewportSize({ width: 1586, height: 992 });
  await page.goto("/workspace/reference/04-trust");

  const matrix = page.locator(".legacy-trust-matrix");
  await expect(matrix).toBeVisible();
  for (const mode of [
    "Read-only",
    "Ask before changes",
    "Safe local work",
    "Full workspace",
    "Full machine",
    "Delegated mission",
  ]) {
    await expect(page.getByRole("columnheader", { name: mode })).toBeVisible();
  }

  const dimensions = await matrix.evaluate((element) => ({
    clientWidth: element.clientWidth,
    scrollWidth: element.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
});

test("icon library contains its desktop catalog inside the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 1586, height: 992 });
  await page.goto("/icon-library.html");
  await expect(page.getByText("Control Center icon library", { exact: true })).toBeVisible();

  const dimensions = await page.evaluate(() => {
    const catalog = document.querySelector(".icon-catalog-grid");
    const usageCode = document.querySelector(".icon-usage-code");
    return {
      documentClientHeight: document.documentElement.clientHeight,
      documentClientWidth: document.documentElement.clientWidth,
      documentScrollHeight: document.documentElement.scrollHeight,
      documentScrollWidth: document.documentElement.scrollWidth,
      catalogClientHeight: catalog?.clientHeight ?? 0,
      catalogClientWidth: catalog?.clientWidth ?? 0,
      catalogScrollHeight: catalog?.scrollHeight ?? 0,
      catalogScrollWidth: catalog?.scrollWidth ?? 0,
      usageCodeClientWidth: usageCode?.clientWidth ?? 0,
      usageCodeScrollWidth: usageCode?.scrollWidth ?? 0,
    };
  });

  expect(dimensions.documentScrollWidth).toBeLessThanOrEqual(dimensions.documentClientWidth);
  expect(dimensions.documentScrollHeight).toBeLessThanOrEqual(dimensions.documentClientHeight);
  expect(dimensions.catalogScrollWidth).toBeLessThanOrEqual(dimensions.catalogClientWidth);
  expect(dimensions.catalogScrollHeight).toBeGreaterThan(dimensions.catalogClientHeight);
  expect(dimensions.usageCodeScrollWidth).toBeLessThanOrEqual(dimensions.usageCodeClientWidth);

  await page.getByRole("button", { name: /^Trust 25$/ }).click();
  await expect(page.getByText("Showing 25 icons", { exact: true })).toBeVisible();
});

test("UAA sidecar reference state renders", async ({ page }) => {
  await page.goto("/workspace/today?sidecar=open");
  await expect(page.locator(".ns-sidecar")).toBeVisible();
  await expect(page.getByRole("complementary", { name: "UAA sidecar" })).toBeVisible();
});

test("Studio Create, Chat, and Code modes render", async ({ page }) => {
  await page.goto("/workspace/studio");

  await page.getByRole("button", { name: "Presentations" }).click();
  await expect(page.getByRole("heading", { name: "Founder pitch deck" })).toBeVisible();

  await page.getByRole("button", { name: /^Chat.*Talk, decide, hand off$/ }).click();
  await expect(page.getByRole("heading", { name: "Agent loop thread" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Open canonical Chat" })).toBeVisible();

  await page.getByRole("button", { name: /^Code.*Propose, review, validate$/ }).click();
  await expect(page.getByRole("link", { name: "Open canonical Coding" })).toBeVisible();
  await expect(page.getByText(/File writes blocked/)).toBeVisible();
});

test("compact desktop shell stays within the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 1100, height: 800 });
  await page.goto("/workspace/today");
  await expect(page.locator(".ns-sidebar")).toBeVisible();
  const horizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth,
  );
  expect(horizontalOverflow).toBe(false);
});
