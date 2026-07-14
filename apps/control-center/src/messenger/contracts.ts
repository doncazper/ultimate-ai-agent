export const MESSENGER_SURFACE_IDS = [
  "founder",
  "personal",
  "dm",
  "group",
  "threads",
  "search",
  "room-info",
  "invite",
  "room-settings",
  "sessions",
  "intelligence",
  "recovery",
  "dark",
  "calling",
  "setup",
] as const;

export type MessengerSurfaceId = (typeof MESSENGER_SURFACE_IDS)[number];

export const MESSENGER_VARIANT_IDS = [
  "loading",
  "initial-sync",
  "empty-room",
  "no-search-results",
  "invite-pending",
  "join-failed",
  "local-echo",
  "queued-send",
  "failed-send",
  "retry",
  "edited",
  "redacted",
  "undecryptable",
  "verification-requested",
  "verification-failed",
  "backup-unavailable",
  "offline",
  "reconnecting",
  "rate-limited",
  "permission-denied",
  "room-archived-left",
  "inspector-collapsed",
] as const;

export type MessengerVariantId = (typeof MESSENGER_VARIANT_IDS)[number];
export type MessengerCommandPosture = "Preview" | "Planned" | "Blocked";
export type MessengerTone = "neutral" | "info" | "warning" | "danger";

export interface MessengerCommandProjection {
  command_ref: string;
  label: string;
  posture: MessengerCommandPosture;
  safe_summary: string;
}

export interface MessengerSurfaceProjection {
  surface_id: MessengerSurfaceId;
  render_ref: `COMMS-MX-${string}`;
  fixture_ref: string;
  title: string;
  subtitle: string;
  space_label: "Founder HQ" | "Personal Circle";
  room_label: string;
  source_posture: "synthetic_fixture";
  runtime_posture: "blocked";
  safe_summary: string;
  commands: readonly MessengerCommandProjection[];
}

export interface MessengerVariantProjection {
  variant_id: MessengerVariantId;
  fixture_ref: string;
  label: string;
  tone: MessengerTone;
  safe_summary: string;
}
