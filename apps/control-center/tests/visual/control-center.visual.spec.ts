import { readFileSync } from "node:fs";
import { expect, test, type Route } from "@playwright/test";
import {
  MESSENGER_SURFACE_IDS,
  MESSENGER_VARIANT_IDS,
  type MessengerSurfaceId,
  type MessengerVariantId,
} from "../../src/messenger/contracts";
import { MESSENGER_VARIANTS } from "../../src/messenger/fixtures";

const studioSkillMarketplaceFixture: unknown = JSON.parse(
  readFileSync(
    new URL("./fixtures/studio-skill-marketplace-posture.json", import.meta.url),
    "utf8",
  ),
);

const FIXED_ISO_NOW = "2026-01-01T00:00:00.000Z";

const surfaces = [
  { name: "overview", route: "/" },
  { name: "start", route: "/start" },
  { name: "today", route: "/today" },
  { name: "inbox", route: "/inbox" },
  { name: "actions", route: "/actions" },
  { name: "plans", route: "/plans" },
  { name: "proof", route: "/proof" },
  { name: "trust", route: "/trust" },
  { name: "memory", route: "/memory" },
  { name: "evidence", route: "/evidence" },
  { name: "settings", route: "/settings" },
  { name: "setup", route: "/setup" },
] as const;

const routeStateScenarios = [
  { name: "state-loading", kind: "loading", label: "Loading" },
  { name: "state-empty", kind: "empty", label: "Empty planned" },
  { name: "state-error", kind: "error", label: "Error" },
  { name: "state-blocked", kind: "blocked", label: "Blocked" },
  { name: "state-partial", kind: "partial", label: "Partial" },
  { name: "state-success", kind: "success", label: "Success" },
] as const;

const messengerSurfaces = MESSENGER_SURFACE_IDS;
const messengerStates = MESSENGER_VARIANT_IDS;

const messengerStateSurface: Partial<Record<MessengerVariantId, MessengerSurfaceId>> = {
  "no-search-results": "search",
  "invite-pending": "invite",
  "join-failed": "invite",
  "verification-requested": "sessions",
  "verification-failed": "sessions",
  "backup-unavailable": "sessions",
  "permission-denied": "calling",
};

const messengerDesktopViewports = [
  { name: "wide", width: 1440, height: 900 },
  { name: "compact", width: 1180, height: 800 },
] as const;

test.beforeEach(async ({ page }) => {
  await page.addInitScript((fixedIsoNow) => {
    const fixedTime = new Date(fixedIsoNow).getTime();
    const RealDate = Date;
    class FixedDate extends RealDate {
      constructor(...args: unknown[]) {
        if (args.length === 0) {
          super(fixedTime);
          return;
        }
        super(...(args as [number]));
      }

      static now() {
        return fixedTime;
      }
    }
    globalThis.Date = FixedDate as DateConstructor;
  }, FIXED_ISO_NOW);

  const fulfillMissingBackend = async (route: Route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/control-center/communications/matrix-sync/posture") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: {
            schema_version: "uaa-matrix-sync-posture.v1",
            provider_ref: "provider-ref:communications:matrix",
            adapter_ref: "adapter-ref:communications:matrix-sync-v1",
            runtime_status: "configuration_required",
            freshness: "unavailable",
            credential_posture_ref: "credential-posture-ref:matrix:one-use-broker-not-enrolled",
            cache_posture_ref: "cache-posture-ref:matrix:protected-cache-helper-not-installed",
            authority_lane_refs: [
              "sync-read", "timeline-paginate-read", "room-state-read",
              "receipt-project-read", "typing-project-read", "cache-read",
              "cache-write", "cache-migrate", "cache-purge", "cache-key-create",
              "cache-key-rotate", "cache-key-delete",
            ].map((name) => `authority-lane-ref:matrix-${name}`),
            concrete_transport_operation_refs: [
              "operation-ref:matrix-sync:sync-read",
              "operation-ref:matrix-sync:timeline-paginate-read",
            ],
            uncomposed_executor_operation_refs: [
              "room-state-read", "receipt-project-read", "typing-project-read",
              "cache-read", "cache-write", "cache-migrate", "cache-purge",
              "cache-key-create", "cache-key-rotate", "cache-key-delete",
            ].map((name) => `operation-ref:matrix-sync:${name}`),
            blocker_refs: ["blocker-ref:matrix-sync:credential-broker-enrollment-required"],
            evidence_refs: ["evidence-ref:matrix-sync:loopback-tests"],
            safe_summary: "Matrix sync requires local configuration.",
            sync_enabled: false,
            connector_writes_enabled: false,
            message_sends_enabled: false,
            browser_automation_enabled: false,
            encrypted_content_materialization_enabled: false,
            content_untrusted: true,
            not_instruction_authority: true,
            raw_content_included: false,
            desktop_only: true,
          },
        }),
      });
      return;
    }
    if (!path.startsWith("/control-center/") && !path.startsWith("/runtime/")) {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({
        success: false,
        error: {
          message: "visual-fixture-backend-unavailable",
        },
      }),
    });
  };
  await page.route("**/control-center/**", fulfillMissingBackend);
  await page.route("**/runtime/**", fulfillMissingBackend);
});

for (const surface of surfaces) {
  test(`${surface.name} visual baseline`, async ({ page }) => {
    await page.goto(surface.route);

    await expect(page).toHaveTitle(/Ultimate AI Agent Control Center/);
    await expect(page.getByText("Mock fallback active")).toBeVisible();
    await expect(page.locator("main")).toBeVisible();

    await expect(page).toHaveScreenshot(`${surface.name}.png`, {
      animations: "disabled",
      fullPage: true,
    });
  });
}

for (const scenario of routeStateScenarios) {
  test(`${scenario.name} route state visual baseline`, async ({ page }) => {
    await page.goto("/");
    const main = page.locator("main");
    await expect(page.getByText("Mock fallback active")).toBeVisible();
    await expect(main).toBeVisible();
    await main.evaluate((node, routeStateScenario) => {
      node.innerHTML = `
        <section aria-label="Visual proof route state" class="route-state-panel ${routeStateScenario.kind}" role="${routeStateScenario.kind === "error" ? "alert" : "status"}">
          <div class="route-state-copy">
            <span class="route-state-eyebrow">${routeStateScenario.label}</span>
            <strong>Visual proof ${routeStateScenario.label}</strong>
            <span>Backend-owned route refs are visible when available; blocked and fallback states stay visible.</span>
          </div>
          <div class="route-state-proof">
            <small>Route truth: visual regression fixture.</small>
            <span>Inspect proof, receipts, and blocked authority refs before promotion.</span>
          </div>
        </section>
      `;
    }, scenario);

    await expect(main).toHaveScreenshot(`${scenario.name}.png`, {
      animations: "disabled",
    });
  });
}

for (const viewport of messengerDesktopViewports) {
  for (const surface of messengerSurfaces) {
    test(`messenger ${surface} ${viewport.name} desktop baseline`, async ({ page }, testInfo) => {
      test.skip(testInfo.project.name !== "desktop", "Messenger is macOS desktop only");
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto(`/messenger?view=${surface}`);

      await expect(page.locator(".messenger-brand")).toHaveText("UAA Messenger");
      await expect(page.locator('[data-messenger-runtime="configuration_required"]')).toBeVisible();
      await expectMessengerHasNoHorizontalOverflow(page);
      await expect(page).toHaveScreenshot(`messenger-${surface}-${viewport.name}.png`, {
        animations: "disabled",
      });
    });
  }

  test(`messenger accepted states ${viewport.name} desktop behavior`, async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "desktop", "Messenger is macOS desktop only");
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    const backendRequests: string[] = [];
    page.on("request", (request) => {
      const path = new URL(request.url()).pathname;
      if (path.startsWith("/api/") || path.startsWith("/control-center/") || path.startsWith("/runtime/")) {
        backendRequests.push(path);
      }
    });

    for (const state of messengerStates) {
      const surface = messengerStateSurface[state] ?? "founder";
      await page.goto(`/messenger?view=${surface}&state=${state}`);
      await expect(page.locator('[data-messenger-variant]')).toHaveAttribute("data-messenger-variant", state);
      await expect(page.locator('[data-messenger-runtime="configuration_required"]')).toBeVisible();
      const banner = page.locator(".messenger-variant-banner");
      await expect(banner).toContainText(MESSENGER_VARIANTS[state].label);
      await expect(banner).toContainText(MESSENGER_VARIANTS[state].fixture_ref);
      await expectMessengerStateSemantics(page, state);
      await expectMessengerHasNoHorizontalOverflow(page);
    }
    expect(backendRequests.length).toBeGreaterThan(0);
    expect(new Set(backendRequests)).toEqual(
      new Set([
        "/control-center/communications/matrix-crypto/posture",
        "/control-center/communications/matrix-sync/posture",
      ]),
    );
  });
}

test("studio skills wide desktop visual baseline", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "Studio is macOS desktop only");
  await installStudioSkillMarketplaceFixture(page);
  await page.setViewportSize({ width: 1586, height: 992 });
  await page.goto("/studio/skills");

  await expect(page.getByText("31 skill ideas")).toBeVisible();
  await expect(page.getByText(/Backend validated · Allow/i)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Sonoscli" })).toBeVisible();
  await expectNoStudioHorizontalOverflow(page);
  for (const label of [
    "Skill",
    "Category",
    "Source",
    "Rank",
    "Source signal",
    "Popularity",
    "Updated",
  ]) {
    await expect(page.locator(".skill-list-header").getByText(label, { exact: true }))
      .toBeVisible();
  }
  await expectPrimaryStudioValuesNotEllipsized(page);

  const rows = page.locator(".skill-list-row");
  await rows.nth(1).focus();
  await rows.nth(1).press("Enter");
  await expect(rows.nth(1)).toHaveAttribute("aria-pressed", "true");
  await expect(
    page.getByRole("heading", { name: "Gog", exact: true }),
  ).toBeVisible();
  await rows.nth(1).press("Tab");
  await expect(rows.nth(2)).toBeFocused();

  await expect(page).toHaveScreenshot("studio-skills-wide.png", {
    animations: "disabled",
  });
});

test("studio skills compact desktop visual baseline", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "Studio is macOS desktop only");
  await installStudioSkillMarketplaceFixture(page);
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/studio/skills");

  await expect(page.getByText("31 skill ideas")).toBeVisible();
  await expectNoStudioHorizontalOverflow(page);
  const header = page.locator(".skill-list-header");
  for (const label of ["Skill", "Source", "Rank", "Source signal"]) {
    await expect(header.getByText(label, { exact: true })).toBeVisible();
  }
  for (const label of ["Category", "Popularity", "Updated"]) {
    await expect(header.getByText(label, { exact: true })).toBeHidden();
  }
  await expectPrimaryStudioValuesNotEllipsized(page);

  await expect(page).toHaveScreenshot("studio-skills-compact.png", {
    animations: "disabled",
  });
});

async function installStudioSkillMarketplaceFixture(
  page: import("@playwright/test").Page,
) {
  await page.route("**/api/runtime/skill-marketplace-posture", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(studioSkillMarketplaceFixture),
    });
  });
}

async function expectNoStudioHorizontalOverflow(
  page: import("@playwright/test").Page,
) {
  const selectors = [
    "html",
    ".studio-skill-shell",
    ".skill-results-viewport",
  ];
  for (const selector of selectors) {
    const element = page.locator(selector);
    await expect(element).toBeVisible();
    expect(
      await element.evaluate((node) => node.scrollWidth <= node.clientWidth),
    ).toBe(true);
  }
}

async function expectPrimaryStudioValuesNotEllipsized(
  page: import("@playwright/test").Page,
) {
  const primaryValues = page.locator(
    ".skill-list-row > span:not(.skill-list-identity), .skill-list-identity strong",
  );
  for (let index = 0; index < (await primaryValues.count()); index += 1) {
    const value = primaryValues.nth(index);
    if (!(await value.isVisible())) {
      continue;
    }
    expect(
      await value.evaluate((node) => {
        const style = getComputedStyle(node);
        return (
          style.textOverflow !== "ellipsis" &&
          node.scrollWidth <= node.clientWidth
        );
      }),
    ).toBe(true);
  }
}

async function expectMessengerHasNoHorizontalOverflow(
  page: import("@playwright/test").Page,
) {
  for (const selector of ["html", ".messenger-shell"]) {
    const element = page.locator(selector);
    await expect(element).toBeVisible();
    expect(
      await element.evaluate((node) => node.scrollWidth <= node.clientWidth),
    ).toBe(true);
  }
}

async function expectMessengerStateSemantics(
  page: import("@playwright/test").Page,
  state: MessengerVariantId,
) {
  if (state === "inspector-collapsed") {
    await expect(page.locator(".messenger-inspector")).toBeHidden();
  }
  if (state === "room-archived-left") {
    await expect(page.locator(".messenger-human-composer button")).toBeDisabled();
    await expect(page.getByPlaceholder("Room is read-only")).toBeVisible();
  }
  if (state === "offline") {
    await expect(page.getByText("No server connection or automatic retry exists.")).toBeVisible();
  }
  if (state === "failed-send") {
    await expect(page.getByText("Failed · no retry ran")).toBeVisible();
  }
  if (state === "undecryptable") {
    await expect(page.getByText("Unable to decrypt · fixture event body unavailable")).toBeVisible();
  }
  if (state === "permission-denied") {
    await expect(page.getByText("Permission denied", { exact: true })).toBeVisible();
  }
  if (state === "no-search-results") {
    await expect(page.getByRole("heading", { name: "No search results" })).toBeVisible();
  }
  if (state === "invite-pending") {
    await expect(page.getByText("Pending · not sent")).toBeVisible();
  }
}
