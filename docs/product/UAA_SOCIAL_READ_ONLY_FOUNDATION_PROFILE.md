# Social Read-Only Integration Foundation Profile

Status: founder direction accepted for private dogfood; all three owner
foundation projections implemented locally; independent promotion pending.

Contract ref: `contract-ref:social-read-only-foundation-profile:v1`.

Founder direction acceptance:
`docs/product/UAA_PRIVATE_DOGFOOD_DIRECTION_ACCEPTANCE.md`.

This profile is the narrow activation gate for the first read-only Social
Media Intelligence milestone. It proves only the owner-backed read interfaces,
API/CLI parity, tested Control Center projections, visual evidence, and
truthful source/freshness states required by that milestone. It does not mark
Work Board, CRM, Communications, Messenger, or Social globally complete.

## Current evidence

| Owner foundation | Required Social integration | Current state |
|---|---|---|
| Work Board | Backend-owned board plus a typed `Social Content` saved projection | Implemented locally. Python Core owns a strict read-only saved projection and the Control Center can filter it; the displayed direction is founder-accepted for private dogfood while independent promotion remains pending. |
| CRM | Backend-owned relationship context and stable deep-link refs | Implemented locally. CRM owns an exact tag-selected read-only Social relationship projection on the existing protected relationships route, exposes the same projection through CLI parity, and provides stable safe deep-link refs without connector, provider, publishing, or write authority. |
| Communications | Canonical reviewed conversation summaries, typed source/freshness posture, API/CLI parity, `Social Media` and `Needs attention` UI projections | Implemented locally for a read-only reviewed-manual-import projection; the displayed direction is founder-accepted for private dogfood while independent promotion remains pending. |

Founder approval removes pixel-perfect visual direction as a prerequisite for
private-dogfood iteration. All three owner projection contracts now have local
implementation evidence, but that does not independently promote the full Q25
milestone. The digest-bound promotion ledger remains fail-closed until external
human identity authority and the exact independent role decisions exist.

## CRM foundation contract

CRM owns
`contract-ref:crm-social-relationship-projection:v1`:

- the exact `social-context` person tag selects reviewed CRM relationships;
- every projection item binds the canonical relationship, person, optional
  organization, evidence, memory provenance, health, and freshness refs;
- stable `control-center-deep-link-ref:crm:*` refs let later Social surfaces
  point back to CRM without copying relationship truth;
- `GET /control-center/crm/relationships` and
  `uaa_crm.py inspect-social-relationships` expose the same Python Core
  projection;
- the CRM Control Center inspector labels the projection CRM-owned and
  read-only only when both route truth and nested ownership truth are current;
- raw content, account sync, live source access, connector runtime,
  provider/model calls, publishing, external actions, external writes, and
  production authority remain structurally false.

## Promotion evidence contract

`docs/product/social_read_only_foundation_promotion_v1.json` binds the exact
Work Board, Communications, CRM, frontend, test, schema, verifier, and profile
files into one acceptance-subject digest. The strict schema and
`scripts/verify_social_read_only_foundation_profile.py` reject inventory drift,
digest tampering, duplicate ownership, missing foundation evidence,
self-asserted decisions, secret-like durable values, and any authority
broadening. Default verification proves implementation evidence only.
`--require-promoted` deliberately exits nonzero while the external human
identity authority and all independent role decisions remain unavailable.

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

1. Obtain independent role decisions for product/design, CRM ownership,
   privacy/security, accessibility, and implementation through a separately
   trusted human identity authority. Candidate-authored refs do not count.
2. Bind those decisions to the current acceptance-subject digest. Any changed
   normative file makes prior decisions stale.
3. Run the verifier with `--require-promoted`; keep Q25 blocked until it passes.
4. Only then evaluate the full Q25 read-only milestone; passing this profile
   does not make Social automatically next. Cosmetic divergence from the
   founder-approved direction is allowed, while ownership, workflow-purpose,
   data-boundary, or authority changes require a new decision.
