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

const matrixCryptoPosture = {
  schema_version: "uaa-matrix-crypto-posture.v1",
  posture_ref: "posture-ref:matrix-crypto:adapter-required-v1",
  runtime_status: "adapter_required",
  freshness: "unknown",
  authority_lane_refs: Array.from(
    { length: 17 },
    (_, index) => `authority-lane-ref:matrix-crypto:lane-${index}`,
  ),
  accepted_authority_operation_refs: Array.from(
    { length: 17 },
    (_, index) => `operation-ref:matrix-crypto:accepted-${index}`,
  ),
  live_executor_operation_refs: [],
  blocked_operation_refs: Array.from(
    { length: 17 },
    (_, index) => `operation-ref:matrix-crypto:blocked-${index}`,
  ),
  provider_ref: "provider-ref:communications:matrix",
  runtime_ref: "runtime-ref:matrix-rust-crypto:adapter-required-v1",
  store_backend_ref:
    "crypto-store-backend-ref:matrix:persistent-rust-store-required-v1",
  key_backend_ref:
    "credential-backend-ref:matrix:device-only-keychain-crypto-v1",
  backup_backend_ref:
    "backup-backend-ref:matrix:dedicated-wrapping-key-required-v1",
  reason_refs: ["reason-ref:matrix-crypto:exact-authority-contracts-accepted"],
  blocker_refs: ["blocker-ref:matrix-crypto:persistent-rust-backend-required"],
  evidence_refs: ["evidence-ref:matrix-crypto:authority-contract-tests"],
  single_owner_required: true,
  request_scoped_evaluation_required: true,
  recovery_material_included: false,
  raw_crypto_payload_included: false,
  element_interoperability_status: "external_facility_required",
  desktop_only: true,
  safe_summary:
    "Exact crypto authorities are accepted, while persistent execution remains blocked.",
  redaction_status: "safe_refs_only",
};

const matrixMessagingPosture = {
  schema_version: "uaa-matrix-messaging-posture.v1",
  posture_ref: "posture-ref:matrix-messaging:configuration-required-v1",
  runtime_status: "configuration_required",
  authority_lane_refs: Array.from(
    { length: 15 },
    (_, index) => `authority-lane-ref:matrix-messaging:lane-${index}`,
  ),
  live_executor_operation_refs: Array.from(
    { length: 15 },
    (_, index) => `operation-ref:matrix-messaging:live-${index}`,
  ),
  blocked_operation_refs: Array.from(
    { length: 15 },
    (_, index) => `operation-ref:matrix-messaging:blocked-${index}`,
  ),
  broker_ref: "component-ref:matrix-rust-broker:v1",
  provider_ref: "provider-ref:communications:matrix",
  sdk_ref: "sdk-ref:matrix-rust-sdk:0.18.0",
  crypto_store_ref: "crypto-store-ref:matrix:encrypted-sqlite-v1",
  outbox_store_ref: "outbox-store-ref:matrix:encrypted-dedicated-v1",
  reason_refs: ["reason-ref:matrix-messaging:runtime-enrollment-required"],
  element_interoperability_status: "external_facility_required",
  request_scoped_evaluation_required: true,
  approval_ref_is_authority: false,
  autonomous_send_enabled: false,
  remote_homeservers_enabled: false,
  desktop_only: true,
  raw_content_included: false,
  safe_summary:
    "Exact manual messaging executors exist, while runtime enrollment remains required.",
};

const matrixRoomsMediaPosture = {
  schema_version: "uaa-matrix-rooms-media-posture.v1",
  posture_ref: "posture-ref:matrix-rooms-media:configuration-required-v1",
  runtime_status: "configuration_required",
  authority_lane_refs: Array.from(
    { length: 20 },
    (_, index) => `authority-lane-ref:matrix-rooms-media:lane-${index}`,
  ),
  implemented_core_operation_refs: Array.from(
    { length: 20 },
    (_, index) => `operation-ref:matrix-rooms-media:implemented-${index}`,
  ),
  blocked_live_operation_refs: Array.from(
    { length: 20 },
    (_, index) => `operation-ref:matrix-rooms-media:blocked-${index}`,
  ),
  media_max_bytes: 24576,
  media_type_policy_ref: "media-type-policy-ref:matrix:allowlist-v1",
  quarantine_policy_ref: "quarantine-policy-ref:matrix-media:before-preview-v1",
  preview_policy_ref: "preview-policy-ref:matrix-media:metadata-allowlist-v1",
  progress_policy_ref: "progress-policy-ref:matrix-media:content-free-v1",
  cancel_policy_ref: "cancel-policy-ref:matrix-media:bounded-process-termination-v1",
  retry_policy_ref: "retry-policy-ref:matrix-media:manual-idempotent-no-auto-uncertain-v1",
  search_index_policy_ref: "search-index-policy-ref:matrix:encrypted-hmac-v1",
  element_interoperability_status: "external_facility_required",
  reason_refs: ["reason-ref:matrix-rooms-media:runtime-enrollment-required"],
  request_scoped_evaluation_required: true,
  standing_authority_granted: false,
  multi_account_enabled: false,
  raw_content_included: false,
};

const matrixIntelligencePosture = {
  schema_version: "uaa-matrix-intelligence-posture.v1",
  posture_ref: "posture-ref:matrix-intelligence:partial-exact-local-v1",
  runtime_status: "partial_exact_local_lanes",
  family_postures: [
    ["context_materialization", "accepted_request_scoped", true, []],
    [
      "provider_invocation",
      "blocked_missing_exact_authority",
      false,
      ["blocked-reason-ref:msg-mx:model-provider-runtime-prohibited"],
    ],
    ["proposal_persistence", "accepted_request_scoped", true, []],
    [
      "attachment_analysis",
      "blocked_missing_exact_authority",
      false,
      ["blocked-reason-ref:msg-mx:attachment-scanner-adapter-missing"],
    ],
  ].map(([family, status, enabled, blockers], index) => ({
    family,
    authority_lane_refs: [`authority-lane-ref:matrix-intelligence:family-${index}`],
    status,
    stage_b_runtime_enabled: enabled,
    blocker_refs: blockers,
    safe_summary: `Exact family posture ${index}.`,
  })),
  policy_modes: ["off", "ask_each_time", "scoped_allow"],
  proposal_kinds: [
    "unread_summary",
    "period_summary",
    "reply_draft",
    "open_questions",
    "decisions",
    "commitments",
    "task_date_extraction",
    "translation",
    "message",
    "meeting",
    "follow_up",
    "task",
  ],
  cross_surface_link_refs: [
    "surface-ref:crm:safe-link-only",
    "surface-ref:calendar:safe-link-only",
    "surface-ref:work-board:safe-link-only",
    "surface-ref:knowledge:safe-link-only",
    "surface-ref:communications:safe-link-only",
  ],
  request_scoped_evaluation_required: true,
  standing_content_authority: false,
  provider_invocation_enabled: false,
  attachment_analysis_enabled: false,
  autonomous_send_enabled: false,
  automatic_memory_write_enabled: false,
  context_injection_enabled: false,
  raw_content_persisted: false,
  desktop_only: true,
  safe_summary:
    "Exact local context and proposal lanes are available while provider and attachment lanes remain blocked.",
};

const matrixHardeningPosture = {
  schema_version: "uaa-matrix-hardening-posture.v1",
  posture_ref: "posture-ref:matrix-hardening:sha256:fixture",
  runtime_status: "partial_hardening_evidence",
  checks: [
    "large_room_backpressure",
    "cache_queue_bounds",
    "migration_multi_device",
    "rate_limit_malicious_events",
    "retention_deletion_low_disk",
    "restart_offline_recovery",
    "accessibility_keyboard_focus",
    "localization_readiness",
    "telemetry_redaction",
    "dependency_sbom",
    "rollback_safe_disable",
    "element_interoperability",
  ].map((category) => {
    const status = category === "migration_multi_device"
      ? "blocked"
      : category === "localization_readiness"
        ? "partial"
        : category === "element_interoperability"
          ? "external_facility_required"
          : "passed";
    return {
      check_ref: `check-ref:matrix-hardening:${category.replaceAll("_", "-")}`,
      category,
      status,
      evidence_refs: status === "passed" ? ["evidence-ref:msg-mx-011:local-check"] : [],
      blocker_refs: status === "passed" ? [] : ["blocker-ref:msg-mx-011:explicit-gap"],
      safe_summary: "Content-free local hardening evidence.",
      raw_content_included: false,
    };
  }),
  budgets: Array.from({ length: 8 }, (_, index) => ({
    budget_ref: `budget-ref:matrix-hardening:bound-${index}`,
    unit: index % 2 ? "events" : "bytes",
    limit: index + 1,
    evidence_ref: `evidence-ref:msg-mx-011:bound-${index}`,
  })),
  blocked_later_lane_refs: [
    "blocked-lane-ref:matrix:calls",
    "blocked-lane-ref:matrix:agent-room-participants",
    "blocked-lane-ref:matrix:hosted-infrastructure",
    "blocked-lane-ref:matrix:public-federation",
    "blocked-lane-ref:matrix:production-deployment",
  ],
  request_scoped_runtime_evaluation_required: true,
  new_runtime_authority_granted: false,
  calls_enabled: false,
  agent_participants_enabled: false,
  hosted_infrastructure_enabled: false,
  public_federation_enabled: false,
  production_deployment_enabled: false,
  element_interoperability_status: "external_facility_required",
  raw_content_included: false,
  local_paths_included: false,
  desktop_only: true,
  safe_summary: "Local hardening evidence is partial and later lanes remain blocked.",
};

beforeEach(() => {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const target = String(input);
    const data = target.includes("matrix-hardening")
      ? matrixHardeningPosture
      : target.includes("matrix-intelligence")
      ? matrixIntelligencePosture
      : target.includes("matrix-rooms-media")
      ? matrixRoomsMediaPosture
      : target.includes("matrix-crypto")
      ? matrixCryptoPosture
      : target.includes("matrix-messaging")
        ? matrixMessagingPosture
        : matrixSyncPosture;
    return new Response(JSON.stringify({ success: true, data }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  });
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
    expect(globalThis.fetch).toHaveBeenCalledTimes(6);
    expect(screen.getByText(/External content is untrusted/i)).toBeInTheDocument();

    for (const control of view.container.querySelectorAll<HTMLButtonElement>(
      ".messenger-posture-button",
    )) {
      expect(control).toBeDisabled();
      expect(control.textContent).toMatch(/Preview|Planned|Blocked/);
    }
  });

  it("shows backend-owned rooms, search, and media posture without granting authority", async () => {
    window.history.replaceState({}, "", "/messenger?view=search");
    render(<MessengerShell />);

    await waitFor(() =>
      expect(screen.getByRole("main")).toHaveAttribute(
        "data-messenger-rooms-media-runtime",
        "configuration_required",
      ),
    );
    expect(screen.getByText(/Core implemented · enrollment required/i)).toBeInTheDocument();
    expect(screen.getByText(/Rooms, search & media · configuration required/i)).toBeInTheDocument();
    expect(screen.queryByText(/standing authority granted/i)).not.toBeInTheDocument();
  });

  it("shows exact local intelligence lanes while provider and attachment generation remain blocked", async () => {
    window.history.replaceState({}, "", "/messenger?view=intelligence");
    render(<MessengerShell />);

    await waitFor(() =>
      expect(screen.getByRole("main")).toHaveAttribute(
        "data-messenger-intelligence-runtime",
        "partial_exact_local_lanes",
      ),
    );
    expect(screen.getByText("Off · default")).toBeInTheDocument();
    expect(screen.getByText(/Transient, content-free, room-scoped, and expiring/i)).toBeInTheDocument();
    expect(screen.getByText(/No model\/provider call or attachment analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/Never automatic/i)).toBeInTheDocument();
    expect(screen.queryByText(/generated successfully/i)).not.toBeInTheDocument();
  });

  it("shows backend-owned hardening evidence and explicit external gaps", async () => {
    window.history.replaceState({}, "", "/messenger?view=recovery");
    render(<MessengerShell />);

    await waitFor(() =>
      expect(screen.getByRole("main")).toHaveAttribute(
        "data-messenger-hardening-runtime",
        "partial_hardening_evidence",
      ),
    );
    const inspector = screen.getByLabelText("Messenger recovery and hardening posture");
    expect(within(inspector).getByText("9 of 12")).toBeInTheDocument();
    expect(within(inspector).getByText("3")).toBeInTheDocument();
    expect(within(inspector).getByText(/external facility required/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Hide inspector" })).toHaveAttribute("aria-expanded", "true");
    expect(screen.queryByText(/production deployment enabled/i)).not.toBeInTheDocument();
  });

  it("shows exact crypto authority without claiming a live executor", async () => {
    window.history.replaceState({}, "", "/messenger?view=sessions");
    render(<MessengerShell />);

    await waitFor(() =>
      expect(screen.getByRole("main")).toHaveAttribute(
        "data-messenger-crypto-runtime",
        "adapter_required",
      ),
    );
    expect(
      screen.getByText(/17 accepted · fresh evaluation required/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/persistent broker required/i)).toBeInTheDocument();
    expect(screen.getByText(/recovery material/i)).toBeInTheDocument();
    expect(screen.queryByText(/recovery key:/i)).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /review verification proposal/i }),
    ).toBeDisabled();
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

  it("separates the human composer from UAA proposal UI and blocks both runtimes", async () => {
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
    await waitFor(() =>
      expect(within(humanComposer).getByText(/manual executor: configuration required/i)).toBeInTheDocument(),
    );
    expect(within(humanComposer).getByText(/synthetic room is not an exact authorized target/i)).toBeInTheDocument();
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
    const show = screen.getByRole("button", { name: "Show inspector" });
    expect(show).toHaveAttribute("aria-expanded", "false");
    expect(show).toHaveFocus();
    fireEvent.click(show);
    expect(inspector).toBeVisible();
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

  it("labels fixture authority truth without claiming a live mode", async () => {
    window.history.replaceState({}, "", "/messenger?view=founder");
    render(<MessengerShell />);

    await waitFor(() =>
      expect(screen.getByText(/Manual send · configuration required/i)).toBeInTheDocument(),
    );
    expect(screen.queryByText("Ask before changes")).not.toBeInTheDocument();
  });
});
