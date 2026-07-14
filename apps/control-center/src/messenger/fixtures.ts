import type {
  MessengerCommandPosture,
  MessengerSurfaceId,
  MessengerSurfaceProjection,
  MessengerVariantId,
  MessengerVariantProjection,
} from "./contracts";

const command = (
  surface: MessengerSurfaceId,
  index: number,
  label: string,
  posture: MessengerCommandPosture,
  safeSummary: string,
) => ({
  command_ref: `command-ref:msg-mx-002:${surface}:${index}`,
  label,
  posture,
  safe_summary: safeSummary,
});

const surface = (
  surfaceId: MessengerSurfaceId,
  ordinal: number,
  title: string,
  subtitle: string,
  spaceLabel: "Founder HQ" | "Personal Circle",
  roomLabel: string,
  commands: readonly [string, MessengerCommandPosture, string][],
): MessengerSurfaceProjection => ({
  surface_id: surfaceId,
  render_ref: `COMMS-MX-${String(ordinal).padStart(2, "0")}`,
  fixture_ref: `fixture-ref:msg-mx-002:comms-mx-${String(ordinal).padStart(2, "0")}`,
  title,
  subtitle,
  space_label: spaceLabel,
  room_label: roomLabel,
  source_posture: "synthetic_fixture",
  runtime_posture: "blocked",
  safe_summary:
    "Synthetic desktop fixture only. No Matrix account, network, sync, encryption session, or message operation is active.",
  commands: commands.map(([label, posture, summary], index) =>
    command(surfaceId, index + 1, label, posture, summary),
  ),
});

export const MESSENGER_SURFACES: Record<
  MessengerSurfaceId,
  MessengerSurfaceProjection
> = {
  founder: surface("founder", 1, "UAA Development", "Engineering, product, and design", "Founder HQ", "uaa-development", [
    ["Send message", "Blocked", "Messaging requires separately accepted connector-write authority."],
    ["Review decisions", "Preview", "Opens synthetic fixture detail only."],
  ]),
  personal: surface("personal", 2, "Family Plans", "Schedules, errands, and shared plans", "Personal Circle", "family-plans", [
    ["Send message", "Blocked", "Personal messages cannot be sent in this fixture milestone."],
    ["Propose event", "Planned", "Proposal runtime is not connected to retained messages."],
  ]),
  dm: surface("dm", 3, "Morgan Lee", "Direct message · encryption target", "Founder HQ", "dm-morgan", [
    ["Start call", "Blocked", "Calling and media permission authority are not accepted."],
    ["Send message", "Blocked", "No Matrix session or send authority exists."],
  ]),
  group: surface("group", 4, "Founder Ops", "Weekly planning, decisions, and operating rhythm", "Founder HQ", "founder-ops", [
    ["Invite member", "Blocked", "Room membership changes require future exact authority."],
    ["Send message", "Blocked", "The fixture timeline cannot send events."],
  ]),
  threads: surface("threads", 5, "UAA Development", "Thread preview", "Founder HQ", "uaa-development", [
    ["Reply in thread", "Blocked", "No synchronized thread or send runtime exists."],
    ["Return to room", "Preview", "Changes the local fixture selection only."],
  ]),
  search: surface("search", 6, "Search", "Local index preview", "Founder HQ", "search-results", [
    ["Open in context", "Preview", "Opens a synthetic fixture reference only."],
    ["Draft follow-up", "Planned", "No message or action proposal is created."],
  ]),
  "room-info": surface("room-info", 7, "Room information", "Inspectable synthetic metadata", "Founder HQ", "product-design", [
    ["Review invitation", "Planned", "Membership inspection is fixture-only."],
    ["Open room settings", "Preview", "Changes the local fixture selection only."],
  ]),
  invite: surface("invite", 8, "New conversation", "Exact invitation review preview", "Founder HQ", "invitation-review", [
    ["Search directory", "Blocked", "No directory or network query is permitted."],
    ["Review invitation", "Planned", "No invitation or room creation occurs."],
  ]),
  "room-settings": surface("room-settings", 9, "Room settings", "Before-and-after change preview", "Founder HQ", "founder-ops", [
    ["Preview room change", "Preview", "Shows a synthetic diff and performs no mutation."],
    ["Apply room change", "Blocked", "No approval, lease, connector, or rollback runtime exists."],
  ]),
  sessions: surface("sessions", 10, "Account security", "Sessions, verification, and recovery targets", "Founder HQ", "security", [
    ["Review verification setup", "Planned", "No device is registered or verified."],
    ["Reset identity", "Blocked", "Identity and key operations are not implemented."],
  ]),
  intelligence: surface("intelligence", 11, "customer-alpha", "UAA intelligence fixture", "Founder HQ", "customer-alpha", [
    ["Review proposal", "Preview", "Proposal review does not grant approval or execute an action."],
    ["Ask UAA", "Blocked", "No model call or hidden context materialization exists."],
  ]),
  recovery: surface("recovery", 12, "Recovery", "Offline and failure-state preview", "Founder HQ", "cached-home", [
    ["Retry sync", "Blocked", "Retry is a fixture posture and cannot contact a server."],
    ["Export diagnostics", "Planned", "No raw logs or provider payloads are available."],
  ]),
  dark: surface("dark", 13, "UAA Development", "Dark appearance preview", "Founder HQ", "uaa-development", [
    ["Send message", "Blocked", "Appearance never changes runtime authority."],
    ["Review decisions", "Preview", "Opens synthetic fixture detail only."],
  ]),
  calling: surface("calling", 14, "Start a call", "Blocked media preflight", "Founder HQ", "dm-morgan", [
    ["Test devices", "Blocked", "No microphone, camera, or media permission is requested."],
    ["Review call launch", "Planned", "No call provider or launch authority exists."],
  ]),
  setup: surface("setup", 15, "Connect Messenger", "Blocked setup target", "Founder HQ", "setup", [
    ["Check compatibility", "Blocked", "No homeserver discovery or network contact occurs."],
    ["Review connection", "Planned", "No credential, session, or crypto store is created."],
  ]),
};

const variant = (
  variantId: MessengerVariantId,
  label: string,
  tone: MessengerVariantProjection["tone"],
  safeSummary: string,
): MessengerVariantProjection => ({
  variant_id: variantId,
  fixture_ref: `fixture-ref:msg-mx-002:state-${variantId}`,
  label,
  tone,
  safe_summary: safeSummary,
});

export const MESSENGER_VARIANTS: Record<
  MessengerVariantId,
  MessengerVariantProjection
> = {
  loading: variant("loading", "Loading fixture preview", "neutral", "No runtime result is available."),
  "initial-sync": variant("initial-sync", "Initial sync planned", "info", "Synthetic progress only; no account is connected."),
  "empty-room": variant("empty-room", "Empty room preview", "neutral", "No message history is present in this fixture."),
  "no-search-results": variant("no-search-results", "No search results", "neutral", "Search scope is retained; no result is fabricated."),
  "invite-pending": variant("invite-pending", "Invitation review pending", "warning", "No invitation has been sent."),
  "join-failed": variant("join-failed", "Join failed", "danger", "No room membership was created."),
  "local-echo": variant("local-echo", "Local echo · not sent", "warning", "Synthetic local-only event; no remote acknowledgement."),
  "queued-send": variant("queued-send", "Queued · not sent", "warning", "No queue worker or connector is active."),
  "failed-send": variant("failed-send", "Send failed", "danger", "No message was delivered and no retry ran."),
  retry: variant("retry", "Retry preview", "warning", "A retry is proposed only; no operation executed."),
  edited: variant("edited", "Edited fixture event", "info", "Synthetic version posture; no source event changed."),
  redacted: variant("redacted", "Redacted event", "neutral", "The synthetic event body is intentionally absent."),
  undecryptable: variant("undecryptable", "Unable to decrypt", "danger", "No key request or recovery operation ran."),
  "verification-requested": variant("verification-requested", "Verification requested", "warning", "Request posture only; no device is verified."),
  "verification-failed": variant("verification-failed", "Verification failed", "danger", "No trust state was established."),
  "backup-unavailable": variant("backup-unavailable", "Secure backup unavailable", "danger", "Recovery capability is unknown and fails closed."),
  offline: variant("offline", "Offline · cached fixture only", "danger", "No server connection or background retry exists."),
  reconnecting: variant("reconnecting", "Reconnecting preview", "warning", "In-progress fixture posture; not a connected claim."),
  "rate-limited": variant("rate-limited", "Rate limited · wait required", "warning", "No automatic retry is scheduled."),
  "permission-denied": variant("permission-denied", "Media permission denied", "danger", "Call preflight remains blocked."),
  "room-archived-left": variant("room-archived-left", "Room archived or left", "warning", "Timeline is read-only and composer unavailable."),
  "inspector-collapsed": variant("inspector-collapsed", "Inspector collapsed", "neutral", "Conversation remains primary; inspector can be reopened locally."),
};

export function parseMessengerSurface(value: string | null): MessengerSurfaceId {
  return value && value in MESSENGER_SURFACES
    ? (value as MessengerSurfaceId)
    : "founder";
}

export function parseMessengerVariant(
  value: string | null,
): MessengerVariantId | null {
  return value && value in MESSENGER_VARIANTS
    ? (value as MessengerVariantId)
    : null;
}
