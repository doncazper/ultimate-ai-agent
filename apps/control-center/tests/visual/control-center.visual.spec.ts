import { expect, test, type Route } from "@playwright/test";

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
