# Social Read-Only Integration Foundation Profile

Status: partial implementation; Q25 remains deferred.

Contract ref: `contract-ref:social-read-only-foundation-profile:v1`.

This profile is the narrow activation gate for the first read-only Social
Media Intelligence milestone. It proves only the owner-backed read interfaces,
API/CLI parity, tested Control Center projections, visual evidence, and
truthful source/freshness states required by that milestone. It does not mark
Work Board, CRM, Communications, Messenger, or Social globally complete.

## Current evidence

| Owner foundation | Required Social integration | Current state |
|---|---|---|
| Work Board | Backend-owned board plus a typed `Social Content` saved projection | Implemented locally. Python Core owns a strict read-only saved projection and the Control Center can filter it; independent visual and profile acceptance remain missing. |
| CRM | Backend-owned relationship context and stable deep-link refs | Partial. The local CRM owner foundation exists; Social relationship projection acceptance remains missing. |
| Communications | Canonical reviewed conversation summaries, typed source/freshness posture, API/CLI parity, `Social Media` and `Needs attention` UI projections | Implemented locally for a read-only reviewed-manual-import projection; independent visual acceptance remains missing. |

Q25 is not eligible until every row is accepted on one exact revision with
tests, current product truth, and desktop/narrow visual evidence.

## Work Board foundation contract

The existing Python Agent Core Work Board now owns
`contract-ref:work-board-social-content-saved-projection:v1`:

- `work-board-saved-projection:social-content` selects existing board cards by
  the exact `social-content` tag while Work Board retains lifecycle, ordering,
  card, and task ownership;
- the projection publishes typed link contracts for originating signal,
  campaign, evidence, and schedule refs without fabricating linked records;
- the Control Center exposes `Social Content` as a saved-view filter and labels
  it backend-owned and read-only;
- copied task lifecycle, social publishing, connector writes, background sync,
  and production authority are structurally rejected.

The projection uses the existing `GET /control-center/work-board` route and
`scripts/dev/uaa_work_board.py inspect-board` CLI. It adds no route or mutation
lane.

## Communications foundation contract

The Python Agent Core owns `uaa-communications-reviewed-projection.v1`:

- `ConversationSourcePosture` declares the reviewed manual-import source,
  observed freshness, coverage, retention, privacy, and evidence refs;
- `ReviewedCommunicationThread` carries canonical thread, channel,
  participant, bounded item, attention, evidence, and reviewed summary fields;
- `ReviewedCommunicationItem` carries canonical item, sender, timestamp,
  fingerprint, relation, evidence, and reviewed redacted summary fields;
- list and detail envelopes are bounded and explicitly block send, reply,
  delete, moderation, connector sync, and every external action;
- `GET /control-center/communications/conversations` and
  `GET /control-center/communications/conversations/{conversation_ref}` expose
  the same Python truth as `uaa_communications.py conversations` and
  `uaa_communications.py conversation`;
- the local file loader rejects symlinks, non-regular files, oversized or
  malformed JSON, unknown fields, unsafe refs, broken links, and authority
  claims without echoing rejected content.

The loader reads only `reviewed_projection.json` from
`UAA_COMMUNICATIONS_PROJECTION_STATE_DIR` (or the local default state
directory). This slice intentionally adds no import/commit route. Operators
must prepare the bounded reviewed projection outside the runtime and retain
their own rollback copy. A later mutation lane would require exact approval,
idempotency, a Messages-domain lease, single-writer coordination, rollback,
and receipts.

## Non-authority posture

This profile grants no live account access, OAuth, connector configuration,
background synchronization, raw message storage, provider/model calls,
publishing, reply, delete, moderation, CRM write, calendar write, public
release, or production authority. Reviewed summaries remain untrusted source
data and cannot act as instructions or authority.

## Remaining acceptance work

1. Independently accept the Work Board `Social Content` saved projection and
   its desktop/narrow evidence.
2. Accept the CRM relationship-context projection and deep links.
3. Capture and independently review desktop and narrow visual evidence for the
   backend-owned Communications states: ready, empty, stale, blocked, error,
   and `Needs attention` filtering.
4. Publish a strict profile ledger/verifier bound to the exact evidence set.
5. Only then evaluate Q25 priority; passing this profile does not make Social
   automatically next.
