# macOS Of Agents Product Principles

Status: planning and product-language artifact

This document guides future Founder Command Center work. It grants no runtime
authority and does not change the active API, Control Center, OpenWebUI,
PolicyEngine, LocalApprovalAuthority, memory, file, connector, plugin, shell,
browser, mobile, or release boundaries.

## Positioning

UAA should feel like the macOS of agents: opinionated, integrated,
human-readable, safe by default, and useful every day. The product should hide
unnecessary complexity without hiding authority, risk, evidence, or blocked
states.

## Principles

### Fewer Surfaces, Deeper Workflows

Prefer Today, Inbox, Plans, Actions, Memory, Evidence, and Settings over many
parallel pages. Add a new surface only when it completes a real workflow or
clearly improves reviewability.

### Proof Before Power

A capability should show evidence, prerequisites, route posture, side-effect
class, approval requirement, and rollback status before it offers mutation.

### Preview Before Mutation

Every non-trivial action starts as a readable proposal or preview. Preview
output must be bounded, redacted, and safe-ref based.

### Approval Before Irreversible Action

Irreversible or mutating work requires exact approval through
LocalApprovalAuthority or its reviewed successor. Approval refs are identifiers,
not authority by themselves.

### Receipt After Action

Every completed scoped action needs a receipt or auditable safe summary that
names what happened, what was denied, what evidence exists, and how rollback or
safe-disable should be reviewed.

### Memory Only With Provenance And Review

Memory is recall, not truth or authority. Memory candidates need source refs,
evidence refs, review state, correction state, and deletion/export/retention
posture before they become useful product memory.

### Local-First But Not Paralyzed

Local-first means user control, safe defaults, redacted local evidence, and
loopback-first operation. It does not mean leaving users with unreadable raw
payloads or blocked screens that do not suggest a next safe action.

### Blocked States Must Suggest The Next Safe Action

Blocked, denied, unavailable, skipped, partial, and mock-only states must be
truthful and useful. The UI should explain what is missing, which authority
boundary applies, and what scoped task can unblock the workflow.

### No Raw JSON As Primary UI

Developer payloads may support debugging, but operator-critical flows need
human summaries first: safe refs, route names, side-effect classes, approval
requirements, evidence refs, state labels, and blockers.

### Every Visible Action Names Authority Boundary And Side-Effect Class

Visible actions must map to a route or explicitly say local UI state only. The
surface must name whether the route is metadata-only, validation-only,
local-dev workspace only, governed read-only network evidence, or blocked.

### Every Feature Distinguishes Implemented, Planned, Partial, Blocked, And Missing

Do not imply completion for work that is route posture, mock fallback, planned,
blocked, skipped, partial, or not scoped. Product copy must follow
`docs/control_center/PRODUCT_LANGUAGE_RULES.md`.

## Design Implications

- The first viewport should show work state, not marketing.
- Primary workflows should expose decision points and receipts, not raw API
  responses.
- Settings should show safe setup, feature flags, kill-switch posture, and
  disabled boundaries without credential collection or authority toggles.
- Evidence should read like a timeline a founder can trust.
- Memory review should feel like a governed inbox, not hidden prompt stuffing.

## Non-Goals

This principle set does not add native macOS app work, OS integration,
unrestricted automation, public distribution, production authority, provider
authority, shell/subprocess authority, connector writes, plugin runtime import,
or broad autonomy.
