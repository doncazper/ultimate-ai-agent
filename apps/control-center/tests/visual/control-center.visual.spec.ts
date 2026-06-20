import { expect, test, type Route } from "@playwright/test";

const FIXED_ISO_NOW = "2026-01-01T00:00:00.000Z";

const surfaces = [
  { name: "overview", route: "/" },
  { name: "today", route: "/today" },
  { name: "actions", route: "/actions" },
  { name: "plans", route: "/plans" },
  { name: "memory", route: "/memory" },
  { name: "evidence", route: "/evidence" },
  { name: "settings", route: "/settings" },
  { name: "setup", route: "/setup" },
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
