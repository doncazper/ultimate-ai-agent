import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MessengerShell } from "./MessengerShell";
import {
  MESSENGER_SURFACE_IDS,
  MESSENGER_VARIANT_IDS,
} from "../../messenger/contracts";
import {
  MESSENGER_SURFACES,
  MESSENGER_VARIANTS,
} from "../../messenger/fixtures";

const matrixSyncPosture = {
  schema_version: "uaa-matrix-sync-posture.v1",
  provider_ref: "provider-ref:communications:matrix",
  adapter_ref: "adapter-ref:communications:matrix-sync-v1",
  runtime_status: "configuration_required",
  freshness: "unavailable",
  credential_posture_ref:
    "credential-posture-ref:matrix:one-use-broker-not-enrolled",
  cache_posture_ref:
    "cache-posture-ref:matrix:protected-cache-helper-not-installed",
  authority_lane_refs: [
    "sync-read",
    "timeline-paginate-read",
    "room-state-read",
    "receipt-project-read",
    "typing-project-read",
    "cache-read",
    "cache-write",
    "cache-migrate",
    "cache-purge",
    "cache-key-create",
    "cache-key-rotate",
    "cache-key-delete",
  ].map((name) => `authority-lane-ref:matrix-${name}`),
  concrete_transport_operation_refs: [
    "operation-ref:matrix-sync:sync-read",
    "operation-ref:matrix-sync:timeline-paginate-read",
  ],
  uncomposed_executor_operation_refs: [
    "room_state_read",
    "receipt_project_read",
    "typing_project_read",
    "cache_read",
    "cache_write",
    "cache_migrate",
    "cache_purge",
    "cache_key_create",
    "cache_key_rotate",
    "cache_key_delete",
  ].map((name) => `operation-ref:matrix-sync:${name.replaceAll("_", "-")}`),
  blocker_refs: [
    "blocker-ref:matrix-sync:credential-broker-enrollment-required",
  ],
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
};

beforeEach(() => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(
      JSON.stringify({ success: true, data: matrixSyncPosture }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    ),
  );
});

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

  it.each(MESSENGER_SURFACE_IDS)("renders the %s desktop target with backend-owned posture only", async (surfaceId) => {
    window.history.replaceState({}, "", `/messenger?view=${surfaceId}`);
    const view = render(<MessengerShell />);

    const shell = screen.getByRole("main");
    expect(shell).toHaveAttribute(
      "data-messenger-surface",
      MESSENGER_SURFACES[surfaceId].render_ref,
    );
    await waitFor(() =>
      expect(shell).toHaveAttribute(
        "data-messenger-runtime",
        "configuration_required",
      ),
    );
    expect(screen.getByText(/Read-only sync · configuration required/i)).toBeInTheDocument();
    expect(screen.getByText(/External actions blocked/i)).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    expect(screen.getByText(/External content is untrusted/i)).toBeInTheDocument();

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
