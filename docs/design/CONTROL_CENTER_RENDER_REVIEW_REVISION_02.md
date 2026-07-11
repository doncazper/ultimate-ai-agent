# Control Center Render Review Revision 02

Status: accepted revision brief, documentation and renders only

Revision ID: `CC-REVIEW-R2-2026-07-11`

Parent contracts: `CONTROL_CENTER_UI_UX_SPEC.md` and
`CONTROL_CENTER_PRODUCT_IA_AND_CALENDAR_CONTRACT.md`

This brief records the second target-render review and the corrections that
must be visible in later renders. It does not add routes, connector authority,
telephony, terminal execution, model calls, web fetching, or runtime behavior.

## Locked Corrections

### Stable standard toolbar

Every normal workspace uses the same two shell rows:

1. the global posture strip; and
2. a 64 px route toolbar with title/subtitle at left, route search in the same
   center-right slot, route-local filters/actions after search, and the
   workload-aware `Review N decisions` control fixed at the far right.

Search never wraps below the decision control. At narrower desktop widths it
collapses to a search icon/`Command-K` affordance instead of moving to another
row. A route without collection search leaves the search slot unused or uses a
route-appropriate command field in that same geometry.

### Primary News workspace

News becomes a primary workspace between Calendar and Studio. It provides
For You, Business, Technology, Markets, Saved, and Sources views. Every story
shows source, type, publication/freshness time, and why it was selected. News
may be curated from explicit interests, business/relationship watchlists,
reviewed settings, and read-only bulletins. It is situational context, not
completable work, and it never hides provenance or claims unrestricted web
fetching.

### Immersive Studio shell

Studio no longer squeezes a coding UI into the ordinary Control Center shell.
Entering Studio switches to a familiar Codex/Claude-style workbench:

- the top-left identity becomes `UAA Studio`;
- a visible `Back to Control Center` command restores the product shell;
- the light workspace rail contains New task, Search, Scheduled, Code review,
  Pull requests, project folders, threads/tasks, and a bottom Settings item;
- no operator-name footer is required;
- the central task/transcript/editor is the dominant surface;
- changes, files, checks, context, and proof use optional drawers or a
  collapsible inspector rather than remaining permanently crowded;
- one anchored composer serves the Studio task; the global composer is not
  duplicated; and
- a Terminal command opens the governed embedded terminal or explicitly pops
  out the macOS Terminal app.

Studio is an intentional shell exception. It preserves visible local/private,
authority, branch/worktree, change, and receipt posture in compact workbench
chrome rather than the normal route toolbar.

### CRM calling

CRM relationship rows and detail headers may expose `Call`. The command first
opens a method chooser populated only from actual availability, for example
System default/iPhone, FaceTime Audio, WhatsApp, Telegram, Google Voice, or a
future approved calling adapter. Each method is labeled `Available`, `Not
connected`, `Planned`, or `Blocked`; the render must not present every example
as live.

The exact call envelope includes contact safe ref, destination safe ref,
method, selected account/device, time, relationship/follow-up ref, recording
posture, authority, and expiry. Launching an external dialer or placing a call
is an external action and uses the applicable approval lane. Opening or
launching a dialer never marks the call or follow-up complete. `Connected`,
`Completed`, `No answer`, `Declined`, `Failed`, and `Cancelled` require an
adapter result or explicit operator confirmation with provenance. Recording is
off unless a later exact legal/consent-aware lane is separately promoted.

The current CRM target remains a placeholder pending review of earlier
specialty CRM variants. No specialty vertical is locked by this revision.

### Governed terminal access

Developer Tools gains a Terminal tab with sessions, allowed command lanes,
working-context safe refs, exit state, and redacted output. Studio has `Open
Terminal` and `Pop out Terminal` commands. Launching the macOS Terminal app is
a user-initiated local UI action; it does not grant UAA shell authority.
Executing a command remains separately classified, exact-scoped,
approval-bound where required, auditable, and receipt-backed. Arbitrary shell
execution remains blocked.

### Trust cockpit

Activity & Trust includes a full Trust cockpit view inspired by the accepted
authority-matrix reference: mode/domain matrix, exact active lease, live policy
decisions, receipts, audit refs, revoke/pause/kill controls, and safe-disable
posture. The matrix displays backend-owned authority truth; it cannot mint or
broaden authority. High-consequence commands require explicit confirmation and
show their exact scope and resulting receipt.

### Work Board color grammar

Work Board uses the same restrained semantic family as Calendar:

- column header bars and counts identify workflow state;
- a 3-4 px card edge and text label identify priority;
- optional project color appears as a small secondary marker; and
- color is never the only signal.

The Group/Color control chooses one visible grammar at a time (`Status`,
`Priority`, or `Project`) so cards do not accumulate conflicting rainbows.

### Compact navigation

The standard rail supports `Expanded` and `Compact` presentation modes.
Compact mode shows the same items and order as icons with tooltips,
focus-visible labels, badges, active indication, and accessible names. Today
remains fixed first; Settings and Developer Tools remain anchored at the
bottom. Compact mode never hides safety posture or changes capability.

## Revision Render Set

- `BOARD-01` v2 — restrained column and priority color grammar.
- `CRM-01` v2 — placeholder relationship workspace with governed Call chooser.
- `STUDIO-01` v2 — immersive familiar coding-agent workbench.
- `NEWS-01` v1 — dedicated curated, sourced News workspace.
- `TRUST-01` v1 — full authority matrix and lease/policy cockpit.
- `TERMINAL-01` v1 — embedded governed terminal with pop-out command.
- `SHELL-COMPACT-01` v1 — icon-only standard shell state.

All earlier versions remain available in the review gallery and are never
overwritten.
