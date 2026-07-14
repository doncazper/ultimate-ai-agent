import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MessengerShell } from "./MessengerShell";
import {
  MESSENGER_SURFACE_IDS,
  MESSENGER_VARIANT_IDS,
} from "../../messenger/contracts";
import {
  MESSENGER_SURFACES,
  MESSENGER_VARIANTS,
} from "../../messenger/fixtures";

afterEach(() => {
  cleanup();
  window.history.replaceState({}, "", "/");
  Object.defineProperty(window, "innerWidth", {
    configurable: true,
    value: 1440,
  });
  vi.restoreAllMocks();
});

describe("MessengerShell", () => {
  it("keeps the fixture inventory exact, safe, and non-authorizing", () => {
    expect(MESSENGER_SURFACE_IDS).toHaveLength(15);
    expect(MESSENGER_VARIANT_IDS).toHaveLength(22);
    expect(new Set(MESSENGER_SURFACE_IDS).size).toBe(15);
    expect(new Set(MESSENGER_VARIANT_IDS).size).toBe(22);

    for (const surfaceId of MESSENGER_SURFACE_IDS) {
      const projection = MESSENGER_SURFACES[surfaceId];
      expect(projection.fixture_ref).toMatch(/^fixture-ref:msg-mx-002:/);
      expect(projection.source_posture).toBe("synthetic_fixture");
      expect(projection.runtime_posture).toBe("blocked");
      expect(projection).not.toHaveProperty("authorized");
      expect(projection).not.toHaveProperty("callable");
      for (const command of projection.commands) {
        expect(["Preview", "Planned", "Blocked"]).toContain(command.posture);
        expect(command.command_ref).toMatch(/^command-ref:msg-mx-002:/);
      }
    }
  });

  it.each(MESSENGER_SURFACE_IDS)("renders the %s desktop target without backend reads", (surfaceId) => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    window.history.replaceState({}, "", `/messenger?view=${surfaceId}`);
    const view = render(<MessengerShell />);

    const shell = screen.getByRole("main");
    expect(shell).toHaveAttribute(
      "data-messenger-surface",
      MESSENGER_SURFACES[surfaceId].render_ref,
    );
    expect(shell).toHaveAttribute("data-messenger-runtime", "blocked");
    expect(screen.getByText(/No Matrix account connected/i)).toBeInTheDocument();
    expect(screen.getByText(/External actions blocked/i)).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();

    for (const control of view.container.querySelectorAll<HTMLButtonElement>(
      ".messenger-posture-button",
    )) {
      expect(control).toBeDisabled();
      expect(control.textContent).toMatch(/Preview|Planned|Blocked/);
    }
  });

  it.each(MESSENGER_VARIANT_IDS)("renders the %s fixture state without claiming success", (variantId) => {
    window.history.replaceState({}, "", `/messenger?view=founder&state=${variantId}`);
    render(<MessengerShell />);

    const status = screen
      .getAllByRole("status")
      .find((candidate) =>
        candidate.textContent?.includes(MESSENGER_VARIANTS[variantId].fixture_ref),
      );
    expect(status).not.toBeNull();
    expect(status).toHaveTextContent(MESSENGER_VARIANTS[variantId].label);
    expect(status).toHaveTextContent(
      MESSENGER_VARIANTS[variantId].fixture_ref,
    );
    expect(status).not.toHaveTextContent(/successfully sent|connected account|verified session/i);
  });

  it("separates the human composer from UAA proposal UI and blocks both runtimes", () => {
    window.history.replaceState({}, "", "/messenger?view=founder");
    render(<MessengerShell />);

    const humanComposer = screen.getByRole("form", {
      name: "Human message composer",
    });
    const uaaComposer = screen.getByRole("region", {
      name: "UAA proposal composer",
    });
    expect(humanComposer).not.toBe(uaaComposer);
    expect(within(humanComposer).getByRole("button")).toBeDisabled();
    expect(within(uaaComposer).getByRole("button")).toBeDisabled();
    expect(
      within(uaaComposer).getByText(/untrusted data, never instruction authority/i),
    ).toBeInTheDocument();
  });

  it("collapses the inspector at the narrower accepted desktop width", () => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1180,
    });
    window.history.replaceState({}, "", "/messenger?view=founder");
    render(<MessengerShell />);

    const inspector = screen.getByLabelText("Room fixture inspector");
    expect(inspector).not.toBeVisible();
    const show = screen.getByRole("button", { name: "Show inspector" });
    fireEvent.click(show);
    expect(inspector).toBeVisible();
  });

  it("honors the collapsed state and close control at the wide desktop width", () => {
    window.history.replaceState({}, "", "/messenger?view=founder&state=inspector-collapsed");
    const { unmount } = render(<MessengerShell />);

    expect(screen.getByLabelText("Room fixture inspector")).not.toBeVisible();
    unmount();

    window.history.replaceState({}, "", "/messenger?view=founder");
    render(<MessengerShell />);
    const inspector = screen.getByLabelText("Room fixture inspector");
    expect(inspector).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Close inspector" }));
    expect(inspector).not.toBeVisible();
  });

  it("keeps compact settings review available as local fixture state", () => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1180,
    });
    window.history.replaceState({}, "", "/messenger?view=room-settings");
    render(<MessengerShell />);

    const review = screen.getByText("Change inspector").closest("aside");
    expect(review).not.toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Show review" }));
    expect(review).toBeVisible();
  });

  it("labels fixture authority truth without claiming a live mode", () => {
    window.history.replaceState({}, "", "/messenger?view=founder");
    render(<MessengerShell />);

    expect(screen.getByText("Changes blocked · fixture")).toBeInTheDocument();
    expect(screen.queryByText("Ask before changes")).not.toBeInTheDocument();
  });
});
