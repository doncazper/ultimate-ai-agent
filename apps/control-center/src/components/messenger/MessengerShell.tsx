import { useEffect, useState, type ReactNode } from "react";
import { NorthStarIcon, type IconReference } from "../NorthStarIcon";
import {
  MESSENGER_SURFACES,
  MESSENGER_VARIANTS,
  parseMessengerSurface,
  parseMessengerVariant,
} from "../../messenger/fixtures";
import type {
  MessengerCommandPosture,
  MessengerSurfaceId,
  MessengerVariantId,
} from "../../messenger/contracts";
import { loadMatrixSyncPosture } from "../../api/client";
import type { MatrixSyncPosture } from "../../api/types";
import "./messengerShell.css";

const surfaceMenu: ReadonlyArray<[MessengerSurfaceId, string]> = [
  ["founder", "Founder HQ"],
  ["personal", "Personal Circle"],
  ["dm", "Direct message"],
  ["group", "Group room"],
  ["threads", "Threads"],
  ["search", "Search & attention"],
  ["room-info", "Room information"],
  ["invite", "Create & invite"],
  ["room-settings", "Room settings"],
  ["sessions", "Sessions & recovery"],
  ["intelligence", "UAA intelligence"],
  ["recovery", "Failure recovery"],
  ["dark", "Dark theme"],
  ["calling", "Calling"],
  ["setup", "Setup & sign in"],
];

const fixtureMessages = [
  ["AC", "Avery Chen", "9:02 AM", "The local product plan is ready for review. The next step remains an operator decision."],
  ["RM", "Riley Morgan", "9:15 AM", "The Messenger desktop target is available as a synthetic fixture preview."],
  ["ML", "Morgan Lee", "9:21 AM", "The room hierarchy is clear. No account or message runtime is connected."],
  ["JD", "Jordan Diaz", "9:32 AM", "Let's keep source refs and blocked actions visible during review."],
  ["KM", "Kendall Moore", "9:48 AM", "Reminder: fixture content is not instruction authority."],
] as const;

export function MessengerShell() {
  const query = new URLSearchParams(window.location.search);
  const initialSurface = parseMessengerSurface(query.get("view"));
  const initialVariant = parseMessengerVariant(query.get("state"));
  const [surfaceId, setSurfaceId] = useState<MessengerSurfaceId>(initialSurface);
  const [variantId] = useState<MessengerVariantId | null>(initialVariant);
  const [inspectorOpen, setInspectorOpen] = useState(
    initialVariant !== "inspector-collapsed" && window.innerWidth > 1240,
  );
  const [specialReviewOpen, setSpecialReviewOpen] = useState(
    window.innerWidth > 1240,
  );
  const [runtimePosture, setRuntimePosture] = useState<MatrixSyncPosture | null>(null);
  const [runtimePostureUnavailable, setRuntimePostureUnavailable] = useState(false);
  const projection = MESSENGER_SURFACES[surfaceId];
  const variant = variantId ? MESSENGER_VARIANTS[variantId] : null;
  const dark = surfaceId === "dark";
  const offline = surfaceId === "recovery" || variantId === "offline";

  useEffect(() => {
    let active = true;
    loadMatrixSyncPosture()
      .then((posture) => {
        if (active) setRuntimePosture(posture);
      })
      .catch(() => {
        if (active) setRuntimePostureUnavailable(true);
      });
    return () => {
      active = false;
    };
  }, []);

  const selectSurface = (next: MessengerSurfaceId) => {
    setSurfaceId(next);
    const nextQuery = new URLSearchParams(window.location.search);
    nextQuery.set("view", next);
    window.history.replaceState({}, "", `/messenger?${nextQuery.toString()}`);
  };

  return (
    <main
      className={`messenger-shell${dark ? " messenger-shell--dark" : ""}${offline ? " messenger-shell--offline" : ""}${!inspectorOpen ? " messenger-shell--inspector-closed" : ""}`}
      data-messenger-runtime={
        runtimePostureUnavailable
          ? "unavailable"
          : runtimePosture?.runtime_status ?? "unknown"
      }
      data-messenger-surface={projection.render_ref}
      data-messenger-variant={variantId ?? "default"}
    >
      {offline ? (
        <div className="messenger-offline-banner" role="status">
          <NorthStarIcon name="wifi-off" size="sm" />
          <strong>Offline preview</strong>
          <span>No server connection or automatic retry exists.</span>
        </div>
      ) : null}
      <MatrixSyncPostureBanner
        posture={runtimePosture}
        unavailable={runtimePostureUnavailable}
      />
      <GlobalRail current={surfaceId} onSelect={selectSurface} />
      <TopBar current={surfaceId} onSelect={selectSurface} />
      {isSpecialSurface(surfaceId) ? (
        <SpecialSurface
          reviewOpen={specialReviewOpen}
          surfaceId={surfaceId}
          variantId={variantId}
          onReviewChange={setSpecialReviewOpen}
          onSelect={selectSurface}
        />
      ) : (
        <ConversationSurface
          inspectorOpen={inspectorOpen}
          onInspectorChange={setInspectorOpen}
          onSelect={selectSurface}
          surfaceId={surfaceId}
          variantId={variantId}
        />
      )}
      {variant ? <VariantBanner variantId={variantId!} /> : null}
      <footer className="messenger-statusbar" aria-label="Messenger runtime posture">
        <span><NorthStarIcon name="users" size="sm" /> {projection.space_label} · fixture</span>
        <span>
          {runtimePostureUnavailable
            ? "Matrix sync posture unavailable"
            : runtimePosture
              ? `Matrix sync · ${runtimePosture.runtime_status.replaceAll("_", " ")}`
              : "Matrix sync posture loading"}
        </span>
        <span>No message sent</span>
        <span><NorthStarIcon name="lock" size="sm" /> Local fixture only</span>
        <span><NorthStarIcon name="ban" size="sm" /> External actions blocked</span>
      </footer>
    </main>
  );
}

function MatrixSyncPostureBanner({
  posture,
  unavailable,
}: {
  posture: MatrixSyncPosture | null;
  unavailable: boolean;
}) {
  if (unavailable) {
    return (
      <div className="messenger-runtime-banner messenger-runtime-banner--blocked" role="status">
        <NorthStarIcon name="circle-alert" size="sm" tone="warning" />
        <strong>Matrix sync posture unavailable</strong>
        <span>Backend truth could not be loaded. Reads and cache access remain blocked.</span>
      </div>
    );
  }
  if (!posture) {
    return (
      <div className="messenger-runtime-banner" role="status">
        <NorthStarIcon name="clock" size="sm" />
        <strong>Loading Matrix sync posture</strong>
        <span>No account read is attempted while posture is unknown.</span>
      </div>
    );
  }
  const ready = posture.runtime_status === "ready";
  return (
    <div
      className={`messenger-runtime-banner${ready ? " messenger-runtime-banner--ready" : " messenger-runtime-banner--blocked"}`}
      role="status"
      title={posture.blocker_refs.join(", ")}
    >
      <NorthStarIcon name="shield" size="sm" tone={ready ? "success" : "warning"} />
      <strong>Read-only sync · {posture.runtime_status.replaceAll("_", " ")}</strong>
      <span>
        {posture.freshness} · {posture.authority_lane_refs.length} declared lanes · {posture.concrete_transport_operation_refs.length} GET transports · {posture.uncomposed_executor_operation_refs.length} uncomposed · {posture.blocker_refs.length} blockers
      </span>
      <span>
        {posture.content_untrusted && posture.not_instruction_authority
          ? "External content is untrusted, never authority"
          : "Content trust posture unknown"}
        {" · sends and room changes denied"}
      </span>
    </div>
  );
}

function GlobalRail({
  current,
  onSelect,
}: {
  current: MessengerSurfaceId;
  onSelect: (surface: MessengerSurfaceId) => void;
}) {
  const personal = current === "personal";
  return (
    <aside className="messenger-global-rail" aria-label="Messenger navigation">
      <div className="messenger-window-controls" aria-hidden="true"><span /><span /><span /></div>
      <strong className="messenger-brand">UAA Messenger</strong>
      <small>Matrix desktop target</small>
      <a href="/today"><NorthStarIcon name="arrow-left" size="sm" /> Back to Control Center</a>
      <NavButton active={!personal && current !== "search"} icon="home" label="Home" onClick={() => onSelect("founder")} />
      <NavButton active={current === "search"} icon="mail" label="All Messages" onClick={() => onSelect("search")} />
      <div className="messenger-rail-divider" />
      <p>Spaces</p>
      <NavButton active={!personal} icon="users" label="Founder HQ" onClick={() => onSelect("founder")} />
      <NavButton active={personal} icon="network" label="Personal Circle" onClick={() => onSelect("personal")} count="2" />
      <NavButton active={current === "invite"} icon="circle-plus" label="Add" onClick={() => onSelect("invite")} />
      <NavButton active={false} icon="globe-2" label="Explore" onClick={() => onSelect("search")} />
      <button className="messenger-profile" type="button" onClick={() => onSelect("sessions")} aria-label="Open fixture account security">
        <Avatar initials="SR" tone="slate" />
      </button>
    </aside>
  );
}

function TopBar({
  current,
  onSelect,
}: {
  current: MessengerSurfaceId;
  onSelect: (surface: MessengerSurfaceId) => void;
}) {
  return (
    <header className="messenger-topbar">
      <label className="messenger-search-field">
        <span className="sr-only">Search messages, people, and rooms</span>
        <NorthStarIcon name="search" size="sm" />
        <input aria-describedby="messenger-search-posture" readOnly placeholder="Search messages, people, and rooms" />
        <small id="messenger-search-posture">Planned</small>
      </label>
      <button type="button" onClick={() => onSelect("search")}><NorthStarIcon name="mail-open" size="sm" /> Unread <b>7</b></button>
      <button type="button" onClick={() => onSelect("search")}><NorthStarIcon name="at-sign" size="sm" /> Mentions</button>
      <span><NorthStarIcon name={current === "recovery" ? "wifi-off" : "circle-check"} size="sm" tone={current === "recovery" ? "warning" : "success"} /> Local fixture</span>
      <span><NorthStarIcon name="shield" size="sm" tone="warning" /> Changes blocked · fixture</span>
      <span><NorthStarIcon name="lock" size="sm" /> Private target</span>
      <PostureButton label="Review 3 decisions" posture="Preview" />
    </header>
  );
}

function ConversationSurface({
  inspectorOpen,
  onInspectorChange,
  onSelect,
  surfaceId,
  variantId,
}: {
  inspectorOpen: boolean;
  onInspectorChange: (open: boolean) => void;
  onSelect: (surface: MessengerSurfaceId) => void;
  surfaceId: MessengerSurfaceId;
  variantId: MessengerVariantId | null;
}) {
  const projection = MESSENGER_SURFACES[surfaceId];
  return (
    <>
      <RoomRail current={surfaceId} onSelect={onSelect} />
      <section className="messenger-conversation" aria-label="Human conversation fixture">
        <header className="messenger-conversation-header">
          <div>
            <h1>{projection.title}</h1>
            <p>{projection.subtitle} <TruthTag label="Fixture-only preview" tone="info" /></p>
          </div>
          <nav aria-label="Conversation fixture views">
            <IconNav label="Call preflight" icon="phone" onClick={() => onSelect("calling")} />
            <IconNav label="Search fixture" icon="search" onClick={() => onSelect("search")} />
            <IconNav label="Thread fixture" icon="message-square" onClick={() => onSelect("threads")} />
            <IconNav label="Room information fixture" icon="info" onClick={() => onSelect("room-info")} />
            <button className="messenger-inspector-toggle" type="button" onClick={() => onInspectorChange(!inspectorOpen)}>
              {inspectorOpen ? "Hide inspector" : "Show inspector"}
            </button>
          </nav>
        </header>
        <Timeline surfaceId={surfaceId} variantId={variantId} />
        <HumanComposer roomLabel={projection.room_label} disabled={variantId === "room-archived-left"} />
      </section>
      <Inspector
        open={inspectorOpen}
        onClose={() => onInspectorChange(false)}
        onSelect={onSelect}
        surfaceId={surfaceId}
      />
    </>
  );
}

function RoomRail({ current, onSelect }: { current: MessengerSurfaceId; onSelect: (surface: MessengerSurfaceId) => void }) {
  const personal = current === "personal";
  const rooms = personal
    ? [["family-plans", "personal"], ["weekend-trip", "personal"], ["home-projects", "personal"], ["photos", "personal"]] as const
    : [["uaa-development", "founder"], ["founder-ops", "group"], ["customer-alpha", "intelligence"], ["product-design", "room-info"], ["announcements", "founder"]] as const;
  return (
    <aside className="messenger-room-rail" aria-label="Fixture rooms and direct messages">
      <header><strong>{personal ? "Personal Circle" : "Founder HQ"}</strong><TruthTag label="Preview data" tone="neutral" /></header>
      <label className="messenger-room-filter"><NorthStarIcon name="search" size="sm" /><input readOnly placeholder="Find people and rooms" /><small>Preview</small></label>
      <p>Rooms</p>
      {rooms.map(([room, target], index) => (
        <button aria-pressed={roomIsActive(current, room)} className={roomIsActive(current, room) ? "active" : ""} key={room} onClick={() => onSelect(target)} type="button" title={room}>
          <NorthStarIcon name="hash" size="sm" /><span>{room}</span>{index === 1 ? <b>2</b> : null}
        </button>
      ))}
      <p>Direct messages</p>
      <button aria-pressed={current === "dm" || current === "calling"} className={current === "dm" || current === "calling" ? "active" : ""} onClick={() => onSelect("dm")} type="button"><Avatar initials="ML" tone="amber" /><span>Morgan Lee</span><b>1</b></button>
      <button aria-pressed={false} type="button" onClick={() => onSelect("dm")}><Avatar initials="JD" tone="teal" /><span>Jordan Diaz</span></button>
      <p>Low priority</p>
      <div className="messenger-room-row"><NorthStarIcon name="hash" size="sm" /><span>archive-2024</span><TruthTag label="Preview" tone="neutral" /></div>
      <div className="messenger-room-row"><NorthStarIcon name="hash" size="sm" /><span>random</span><TruthTag label="Preview" tone="neutral" /></div>
    </aside>
  );
}

function Timeline({ surfaceId, variantId }: { surfaceId: MessengerSurfaceId; variantId: MessengerVariantId | null }) {
  if (variantId === "loading") {
    return <div className="messenger-timeline messenger-skeleton" aria-label="Loading fixture"><span /><span /><span /></div>;
  }
  if (variantId === "empty-room") {
    return <div className="messenger-empty"><NorthStarIcon name="message-square" size="2xl" /><h2>No fixture messages</h2><p>This synthetic room contains no history.</p></div>;
  }
  const rows = variantId === "redacted"
    ? fixtureMessages.map((row, index) => index === 2 ? [row[0], row[1], row[2], "Message redacted · body unavailable"] as const : row)
    : fixtureMessages;
  return (
    <div className="messenger-timeline" aria-label="Synthetic message timeline">
      <div className="messenger-day-divider">Today · synthetic fixture</div>
      {rows.map(([initials, name, time, body], index) => {
        const selected = index === rows.length - 1;
        const eventState = messageStateFor(index, variantId);
        return (
          <article className={`${selected ? "selected" : ""}${eventState.tone ? ` ${eventState.tone}` : ""}`} key={`${name}-${time}`}>
            <Avatar initials={initials} tone={avatarTone(index)} />
            <div>
              <header><strong>{name}</strong><time>{time}</time>{variantId === "edited" && index === 2 ? <small>Edited fixture version</small> : null}</header>
              <p>{variantId === "undecryptable" && index === 3 ? "Unable to decrypt · fixture event body unavailable" : body}</p>
              {surfaceId === "group" && index === 2 ? <PollPreview /> : null}
              {eventState.label ? <TruthTag label={eventState.label} tone={eventState.tagTone} /> : <div className="messenger-reactions"><span>👍 {index + 1}</span><span>☺</span></div>}
            </div>
          </article>
        );
      })}
    </div>
  );
}

function HumanComposer({ roomLabel, disabled }: { roomLabel: string; disabled: boolean }) {
  return (
    <form className="messenger-human-composer" aria-label="Human message composer" onSubmit={(event) => event.preventDefault()}>
      <label><span className="sr-only">Human message draft</span><input readOnly placeholder={disabled ? "Room is read-only" : `Message ${roomLabel}`} /></label>
      <NorthStarIcon name="paperclip" size="md" />
      <NorthStarIcon name="circle-plus" size="md" />
      <button disabled type="submit"><NorthStarIcon name="send" size="md" /><span>Blocked</span></button>
      <small>No message will be sent.</small>
    </form>
  );
}

function Inspector({
  onClose,
  onSelect,
  open,
  surfaceId,
}: {
  onClose: () => void;
  onSelect: (surface: MessengerSurfaceId) => void;
  open: boolean;
  surfaceId: MessengerSurfaceId;
}) {
  const thread = surfaceId === "threads";
  const intelligence = surfaceId === "intelligence";
  const info = surfaceId === "room-info";
  const recovery = surfaceId === "recovery";
  return (
    <aside className={`messenger-inspector${open ? " is-open" : ""}`} hidden={!open} aria-label={thread ? "Thread fixture inspector" : intelligence ? "UAA intelligence fixture" : "Room fixture inspector"}>
      <header><h2>{thread ? "Threads · 4" : intelligence ? "UAA Intelligence" : info ? "Room information" : recovery ? "Recovery" : "Room · UAA"}</h2><button type="button" onClick={onClose} aria-label="Close inspector"><NorthStarIcon name="x" size="sm" /></button></header>
      {thread ? <ThreadInspector /> : intelligence ? <IntelligenceInspector /> : info ? <RoomInfoInspector onSelect={onSelect} /> : recovery ? <RecoveryInspector /> : <DefaultInspector />}
    </aside>
  );
}

function DefaultInspector() {
  return (
    <>
      <InspectorCard title="Unread summary"><strong>7 fixture messages</strong><p>Most recent synthetic event at 9:48 AM.</p></InspectorCard>
      <InspectorCard title="Open questions"><p>1. Which exact source refs support this review?</p><p>2. What remains blocked before runtime?</p></InspectorCard>
      <InspectorCard title="Decision"><p>Continue fixture review without treating it as execution evidence.</p></InspectorCard>
      <InspectorCard title="Commitments"><p>☑ Keep Matrix runtime blocked</p><p>☑ Preserve safe fixture refs</p></InspectorCard>
      <UaaComposer />
    </>
  );
}

function ThreadInspector() {
  return <>{["Right rail density", "Composer posture", "Safe fixture refs", "Desktop fit"].map((item, index) => <div className={`messenger-thread-row${index === 0 ? " selected" : ""}`} key={item}><Avatar initials={["ML", "AC", "RM", "JD"][index]} tone="purple" /><span><strong>{item}</strong><small>{4 - index} fixture replies</small></span><TruthTag label="Preview" tone="neutral" /></div>)}<InspectorCard title="Right rail density"><p>The thread drawer preserves conversation context and remains fixture-only.</p></InspectorCard><UaaComposer /></>;
}

function RoomInfoInspector({ onSelect }: { onSelect: (surface: MessengerSurfaceId) => void }) {
  return <><div className="messenger-room-profile"><Avatar initials="PD" tone="purple" /><h3>Product Design</h3><p>Private target · 18 synthetic members</p></div><InspectorCard title="About"><KeyValue label="Space" value="Founder HQ" /><KeyValue label="Access" value="Private target" /><KeyValue label="Encryption" value="Planned" /></InspectorCard><div className="messenger-inspector-grid"><span>People · 18</span><span>Files · 12</span><span>Links · 9</span><span>Pins · 4</span></div><button type="button" onClick={() => onSelect("room-settings")}><NorthStarIcon name="settings" size="sm" /> Open settings preview</button><UaaComposer /></>;
}

function IntelligenceInspector() {
  return <><div className="messenger-intelligence-grid"><InspectorCard title="Unread summary"><strong>4</strong><small>Source refs: 4</small></InspectorCard><InspectorCard title="Open questions"><strong>2</strong><small>Confidence: high</small></InspectorCard><InspectorCard title="Decisions"><strong>1</strong><small>Review only</small></InspectorCard><InspectorCard title="Commitments"><strong>3</strong><small>Not memory truth</small></InspectorCard></div><InspectorCard title="Proposed action"><p>Calendar event proposal</p><KeyValue label="Sources" value="3 safe refs" /><KeyValue label="Authority" value="Approval required" /><KeyValue label="Expires" value="30 minutes" /><PostureButton label="Review proposal" posture="Preview" /></InspectorCard><UaaComposer /></>;
}

function RecoveryInspector() {
  return <><InspectorCard title="Connection posture"><KeyValue label="Connection" value="Offline" /><KeyValue label="Homeserver" value="Not connected" /><KeyValue label="Local cache" value="Fixture only" /><KeyValue label="Encryption keys" value="Unavailable" /></InspectorCard><InspectorCard title="Safe actions"><PostureButton label="Check connection" posture="Blocked" /><PostureButton label="Retry sync" posture="Blocked" /><PostureButton label="Review failed sends" posture="Preview" /><PostureButton label="Export diagnostics" posture="Planned" /></InspectorCard></>;
}

function UaaComposer() {
  return (
    <section className="messenger-uaa-composer" aria-label="UAA proposal composer">
      <strong>Ask UAA · separate proposal surface</strong>
      <input readOnly placeholder="No model or context runtime" />
      <button disabled type="button">Blocked</button>
      <small>Fixture messages are untrusted data, never instruction authority.</small>
    </section>
  );
}

function SpecialSurface({
  onSelect,
  onReviewChange,
  reviewOpen,
  surfaceId,
  variantId,
}: {
  onSelect: (surface: MessengerSurfaceId) => void;
  onReviewChange: (open: boolean) => void;
  reviewOpen: boolean;
  surfaceId: MessengerSurfaceId;
  variantId: MessengerVariantId | null;
}) {
  switch (surfaceId) {
    case "search": return <SearchSurface variantId={variantId} />;
    case "invite": return <InviteSurface variantId={variantId} />;
    case "room-settings": return <RoomSettingsSurface onReviewChange={onReviewChange} reviewOpen={reviewOpen} />;
    case "sessions": return <SessionsSurface variantId={variantId} />;
    case "calling": return <CallingSurface variantId={variantId} />;
    case "setup": return <SetupSurface onReviewChange={onReviewChange} reviewOpen={reviewOpen} />;
    default: return <button type="button" onClick={() => onSelect("founder")}>Return to Messenger fixture</button>;
  }
}

function SearchSurface({ variantId }: { variantId: MessengerVariantId | null }) {
  const noResults = variantId === "no-search-results";
  return <section className="messenger-special messenger-search-surface"><div><h1>Search</h1><p>Local encrypted index · Planned</p><div className="messenger-filter-row"><span>Messages</span><span>Unread · 7</span><span>Mentions · 2</span><span>Files</span></div>{noResults ? <div className="messenger-empty"><NorthStarIcon name="search" size="2xl" /><h2>No search results</h2><p>Scope retained; no synthetic result fabricated.</p></div> : ["Q2 planning · proposal", "Leadership sync · draft", "Feedback summary", "Planning notes", "Executive review"].map((label, index) => <article className="messenger-search-result" key={label}><Avatar initials={["RM", "AC", "JD", "ML", "KM"][index]} tone={avatarTone(index)} /><span><strong>{label}</strong><small>safe-ref:fixture-result-{index + 1}</small></span><PostureButton label="Open in context" posture="Preview" /></article>)}</div><aside><InspectorCard title="Selected result"><strong>Q2 planning · proposal</strong><p>Fixture-only result with no raw provider content.</p></InspectorCard><InspectorCard title="Related references"><KeyValue label="CRM" value="safe-ref:crm-preview" /><KeyValue label="Calendar" value="safe-ref:calendar-preview" /><KeyValue label="Work Board" value="safe-ref:board-preview" /></InspectorCard><UaaComposer /></aside></section>;
}

function InviteSurface({ variantId }: { variantId: MessengerVariantId | null }) {
  return <section className="messenger-special"><div><h1>New conversation</h1><p>Direct message · Preview. No directory query occurs.</p><label className="messenger-special-field">Find people<input readOnly placeholder="Safe Matrix identifier" /></label>{["Avery Chen", "Riley Morgan", "Morgan Lee"].map((name, index) => <div className="messenger-directory-row" key={name}><Avatar initials={["AC", "RM", "ML"][index]} tone={avatarTone(index)} /><strong>{name}</strong><span>Synthetic fixture person</span><PostureButton label="Add" posture="Preview" /></div>)}<InspectorCard title="Room option preview"><KeyValue label="Space" value="Founder HQ" /><KeyValue label="Visibility" value="Private target" /><KeyValue label="Encryption" value="Planned" /></InspectorCard></div><aside><InspectorCard title="Invitation review"><KeyValue label="Destination" value="Founder HQ" /><KeyValue label="Recipients" value="2 safe refs" /><KeyValue label="AI access" value="Off" /><KeyValue label="Autonomous send" value="Never" />{variantId === "invite-pending" ? <TruthTag label="Pending · not sent" tone="warning" /> : null}<PostureButton label="Review invitation" posture="Planned" /></InspectorCard></aside></section>;
}

function RoomSettingsSurface({ onReviewChange, reviewOpen }: { onReviewChange: (open: boolean) => void; reviewOpen: boolean }) {
  return <section className="messenger-special messenger-settings-surface"><aside><h1>Room settings</h1>{["General", "Security & Privacy", "Permissions", "Notifications", "History", "UAA access", "Advanced"].map((label, index) => <div className={index === 0 ? "active" : ""} key={label}>{label}<small>{index === 0 ? "Selected" : "Preview"}</small></div>)}</aside><div><div className="messenger-special-heading"><h1>General</h1><button className="messenger-special-review-toggle" type="button" onClick={() => onReviewChange(!reviewOpen)}>{reviewOpen ? "Hide review" : "Show review"}</button></div><label className="messenger-special-field">Room name<input readOnly value="Founder Ops" /></label><label className="messenger-special-field">Topic<textarea readOnly value="Operations and execution fixture." /></label><label className="messenger-special-field">Room alias · safe reference only<input readOnly value="founder-ops" /></label><PostureButton label="Preview room change" posture="Preview" /></div><aside className={`messenger-special-review${reviewOpen ? " is-open" : ""}`} hidden={!reviewOpen}><InspectorCard title="Change inspector"><KeyValue label="Before" value="safe-ref:founder-ops-old" /><KeyValue label="After" value="safe-ref:founder-ops" /><KeyValue label="Authority" value="Approval + lease required" /><PostureButton label="Apply room change" posture="Blocked" /></InspectorCard></aside></section>;
}

function SessionsSurface({ variantId }: { variantId: MessengerVariantId | null }) {
  const posture = variantId === "verification-failed" ? "Verification failed" : variantId === "verification-requested" ? "Verification requested" : "Not registered";
  return <section className="messenger-special messenger-sessions-surface"><div><h1>Account security</h1><p>Desktop fixture · no device registration or key operation.</p><InspectorCard title="Security recommendations"><KeyValue label="Secure backup" value={variantId === "backup-unavailable" ? "Unavailable" : "Not configured"} /><KeyValue label="Current session" value={posture} /></InspectorCard><InspectorCard title="Synthetic device rows"><KeyValue label="Desktop · macOS" value="Verification target" /><KeyValue label="Phone device row" value="Unverified target" /><KeyValue label="Browser row" value="Inactive target" /></InspectorCard></div><aside><InspectorCard title="Recovery posture"><KeyValue label="Cross-signing" value="Planned" /><KeyValue label="Secure backup" value="Not configured" /><KeyValue label="Recovery key" value="Not present" /><KeyValue label="Key storage" value="Backend undecided" /></InspectorCard><PostureButton label="Review verification setup" posture="Planned" /><PostureButton label="Reset identity" posture="Blocked" /></aside></section>;
}

function CallingSurface({ variantId }: { variantId: MessengerVariantId | null }) {
  return <section className="messenger-special messenger-call-surface"><div><h1>Start a call</h1><p>Blocked media preflight · no provider or permission request.</p><InspectorCard title="Participants"><KeyValue label="Target" value="safe-ref:fixture-person-ml" /></InspectorCard><InspectorCard title="Availability"><KeyValue label="Matrix call" value="Planned" /><KeyValue label="External handoff" value="Blocked" /><KeyValue label="Other providers" value="Not connected" /></InspectorCard><InspectorCard title="Device and settings"><KeyValue label="Microphone" value={variantId === "permission-denied" ? "Permission denied" : "Permission not requested"} /><KeyValue label="Camera" value="Permission not requested" /><KeyValue label="Recording" value="Off · cannot be enabled" /></InspectorCard><PostureButton label="Test devices" posture="Blocked" /><PostureButton label="Review call launch" posture="Planned" /></div><aside><InspectorCard title="Authority and review"><KeyValue label="Authority" value="No active lease" /><KeyValue label="External action" value="Blocked" /><KeyValue label="Outcome" value="No call launched" /></InspectorCard></aside></section>;
}

function SetupSurface({ onReviewChange, reviewOpen }: { onReviewChange: (open: boolean) => void; reviewOpen: boolean }) {
  return <section className="messenger-special messenger-setup-surface"><aside><h1>Setup steps</h1>{["1 · Server", "2 · Account", "3 · Security", "4 · Review"].map((label, index) => <div className={index === 0 ? "active" : ""} key={label}>{label}</div>)}</aside><div><div className="messenger-special-heading"><div><h1>Connect Messenger</h1><p>Blocked setup target · no server will be contacted.</p></div><button className="messenger-special-review-toggle" type="button" onClick={() => onReviewChange(!reviewOpen)}>{reviewOpen ? "Hide review" : "Show review"}</button></div><InspectorCard title="Homeserver"><div className="messenger-setup-options"><span>Recommended</span><span>Custom homeserver</span><span>Self-host later</span></div><label className="messenger-special-field">Server<input readOnly value="server-ref:fixture-example" /></label><PostureButton label="Check compatibility" posture="Blocked" /></InspectorCard><InspectorCard title="Sign-in method"><div className="messenger-setup-options"><span>Password · Planned</span><span>Single sign-on · Planned</span><span>Token import · Blocked</span></div></InspectorCard></div><aside className={`messenger-special-review${reviewOpen ? " is-open" : ""}`} hidden={!reviewOpen}><InspectorCard title="Exact connection review"><KeyValue label="Server" value="safe-ref:server-preview" /><KeyValue label="Account" value="Not provided" /><KeyValue label="Credential storage" value="macOS credential vault target" /><KeyValue label="Crypto store" value="Local encrypted target" /><KeyValue label="Network authority" value="Required · absent" /><PostureButton label="Review connection" posture="Planned" /></InspectorCard></aside></section>;
}

function VariantBanner({ variantId }: { variantId: MessengerVariantId }) {
  const projection = MESSENGER_VARIANTS[variantId];
  return <aside className={`messenger-variant-banner tone-${projection.tone}`} role="status"><strong>{projection.label}</strong><span>{projection.safe_summary}</span><small>{projection.fixture_ref}</small></aside>;
}

function PostureButton({ label, posture }: { label: string; posture: MessengerCommandPosture }) {
  return <button className="messenger-posture-button" disabled type="button"><span>{label}</span><small>{posture}</small></button>;
}

function NavButton({ active, count, icon, label, onClick }: { active: boolean; count?: string; icon: IconReference; label: string; onClick: () => void }) {
  return <button aria-current={active ? "page" : undefined} className={active ? "active" : ""} type="button" onClick={onClick}><NorthStarIcon name={icon} size="lg" /><span>{label}</span>{count ? <b>{count}</b> : null}</button>;
}

function IconNav({ icon, label, onClick }: { icon: IconReference; label: string; onClick: () => void }) {
  return <button aria-label={label} title={label} type="button" onClick={onClick}><NorthStarIcon name={icon} size="lg" /></button>;
}

function InspectorCard({ children, title }: { children: ReactNode; title: string }) {
  return <section className="messenger-inspector-card"><h3>{title}</h3>{children}</section>;
}

function KeyValue({ label, value }: { label: string; value: string }) {
  return <div className="messenger-key-value"><span>{label}</span><strong>{value}</strong></div>;
}

function TruthTag({ label, tone }: { label: string; tone: "neutral" | "info" | "warning" }) {
  return <span className={`messenger-truth-tag tone-${tone}`}>{label}</span>;
}

function Avatar({ initials, tone }: { initials: string; tone: string }) {
  return <span className={`messenger-avatar tone-${tone}`} aria-hidden="true">{initials}</span>;
}

function PollPreview() {
  return <div className="messenger-poll"><strong>Which review window works?</strong><span>10–11 AM <i style={{ width: "44%" }} /></span><span>2–3 PM <i style={{ width: "56%" }} /></span></div>;
}

function isSpecialSurface(surfaceId: MessengerSurfaceId) {
  return ["search", "invite", "room-settings", "sessions", "calling", "setup"].includes(surfaceId);
}

function roomIsActive(surfaceId: MessengerSurfaceId, room: string) {
  if (surfaceId === "group") return room === "founder-ops";
  if (surfaceId === "intelligence") return room === "customer-alpha";
  if (surfaceId === "room-info") return room === "product-design";
  return room === "uaa-development";
}

function avatarTone(index: number) {
  return ["purple", "teal", "amber", "blue", "green"][index % 5];
}

function messageStateFor(index: number, variantId: MessengerVariantId | null) {
  if (index !== 2 && index !== 3) return { label: "", tone: "", tagTone: "neutral" as const };
  if (variantId === "local-echo" && index === 2) return { label: "Local echo · not sent", tone: "pending", tagTone: "warning" as const };
  if (variantId === "queued-send" && index === 2) return { label: "Queued · not sent", tone: "pending", tagTone: "warning" as const };
  if (variantId === "failed-send" && index === 2) return { label: "Failed · no retry ran", tone: "failed", tagTone: "warning" as const };
  if (variantId === "retry" && index === 2) return { label: "Retry preview · no operation", tone: "pending", tagTone: "warning" as const };
  if (variantId === "undecryptable" && index === 3) return { label: "Key request blocked", tone: "failed", tagTone: "warning" as const };
  return { label: "", tone: "", tagTone: "neutral" as const };
}
