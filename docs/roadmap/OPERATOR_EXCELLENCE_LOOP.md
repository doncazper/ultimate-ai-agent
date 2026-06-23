# Operator Excellence Catch-Up and Surpass Loop

Status: active planning and review loop
Baseline: v0.103.0 / 0.103.0
Source roadmap: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`
Current board: `docs/kanban/current_board.md`
Recommendation log: `docs/backlog/codex_recommendation_log.md`

This document defines the repeatable review loop for turning peer-product
comparisons, Codex recommendations, ChatGPT reviews, and operator ideas into
small, scoped, verifiable work items.

It is not an automation runtime. It does not grant production authority,
autonomous background execution, unrestricted shell or subprocess behavior,
unrestricted network/browser automation, connector writes, plugin runtime
import, mobile control, model/provider authority, public distribution, or raw
data capture. It is a planning artifact for human-reconciled product hardening.

## Why This Exists

The current product comparison shows a useful tension:

- Ultimate AI Agent is stronger as a contract-first governance foundation:
  disabled by default, exact approval boundaries, OpenAPI discipline,
  Foundation Gate checks, safe refs, redaction, and local model evidence gates.
- Mature peer operator consoles are ahead as shipped products: broader operator
  surfaces, packaging, release workflows, visual proof, installer paths,
  runtime feature breadth, and public product polish.

The goal is not to copy a peer console. The goal is to catch up where product
maturity is missing while preserving UAA's stronger authority model, then
surpass peers by making every useful operator workflow safer, more inspectable,
and more evidence-backed.

## Source Order

Every loop iteration must read or preserve these sources in order:

1. `AGENTS.md`
2. `README.md`
3. `VERSION.md`
4. `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
5. `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`
6. `docs/kanban/current_board.md`
7. `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
8. `docs/control_center/ROUTE_STATUS_MANIFEST.md`
9. `docs/production/RELEASE_VERIFICATION_LANES.md`
10. `docs/backlog/codex_recommendation_log.md`
11. This document

If these sources disagree, stop and repair currentness before implementing
product work.

## Loop Roles

| Role | Output | Hard boundary |
|---|---|---|
| ChatGPT product reviewer | Gap analysis, priority ordering, task proposal, wording review | May not claim shipped behavior or grant runtime authority |
| Codex implementer | Small scoped patch, tests, verifier results, rollback notes | May implement only the current scoped task |
| Human reconciler | Accepts, edits, defers, or rejects recommendations | Required for authority expansion, blocked gates, or product-position changes |
| Foundation Gate and verifiers | Contract proof, drift detection, safe failure output | Must not be weakened to make a task pass |

## Iteration Protocol

Run the loop one item at a time. A long session may process multiple items, but
each item must complete its own scope, tests, and report before the next item
begins.

1. Intake
   - Read the source order above.
   - Read the newest comparison notes or recommendation.
   - Identify whether the item is catch-up, surpass, preserve, blocked, or
     rejected.

2. Classify
   - `catch_up`: closes a peer-product maturity gap without weakening UAA.
   - `surpass`: extends UAA's stronger contract-first posture into a product
     feature peers do not clearly prove.
   - `preserve`: protects an existing UAA advantage from regression.
   - `blocked`: useful, but missing authority scope, evidence, or verifier lane.
   - `rejected`: would weaken safety, evidence, or product truth.

3. Charter
   - Convert accepted work into one scoped task with exact capability name,
     authority boundary, risk ceiling, approval model, persistence model,
     redaction/audit requirements, test plan, verifier updates, rollback plan,
     docs impact, and stop conditions.
   - If those fields cannot be filled, record a recommendation-log entry
     instead of implementing.

4. Implement
   - Make the smallest patch that satisfies the current scoped task.
   - Prefer existing repo patterns and validators.
   - Do not bundle unrelated cleanups.

5. Verify
   - Run the scoped commands listed by the task.
   - Run documentation integrity for docs-only changes.
   - Run OpenAPI checks when routes or API-facing models change.
   - Run Foundation Gate when release evidence, route truth, or verifier
     behavior changes.

6. Harden
   - Do one safety pass for redaction, product language, authority boundaries,
     rollback, idempotency, and stale docs.
   - Do one focused code/test pass for changed files.

7. Reconcile
   - Update the Kanban board only if the task reaches its Done criteria.
   - Update `docs/backlog/codex_recommendation_log.md` for follow-ups,
     deferrals, accepted gaps, and rejected shortcuts.
   - Report changed files, tests, blockers, residual risk, and rollback notes.

8. Stop Or Continue
   - Continue only if the next item is already Ready and does not require human
     approval for new authority.
   - Stop if any core verifier fails, source-of-truth docs contradict each
     other, a task needs unscoped authority, or the next item is ambiguous.

## Stop Conditions

The loop must stop for human reconciliation when any item would add or imply:

- production/public distribution readiness without release evidence
- broad autonomy or autonomous background sessions by default
- shell/subprocess execution outside an explicitly scoped milestone
- unrestricted network or browser automation
- connector writes without exact approval and audited rollback
- plugin runtime import or arbitrary plugin execution
- mobile sensor runtime or mobile control
- model/provider output as production authority
- raw prompt, raw response, raw provider payload, raw path, raw log, username,
  hostname, serial, environment dump, credential material, or private content in
  durable evidence, reports, release docs, tests, or logs
- bypasses around PolicyEngine, LocalApprovalAuthority, route side-effect
  classification, OpenAPI checks, or Foundation Gate checks

## Catch-Up And Surpass Priority Queue

This queue is the current suggested order for closing the gap shown in the
latest UAA-versus-peer comparison. Each item still needs its own scoped prompt.

| Rank | Item | Type | Why it matters | Next gate |
|---:|---|---|---|---|
| 1 | Task decomposition operator loop (`UAA-P1-011`) | catch_up + surpass | Proves the first real operator flow: runtime health, model readiness, UAA `/v1` chat, plan, approve, receipt/audit/latency/rollback | Control Center flow tests plus task decomposition API tests |
| 2 | Control Center differentiator screens (`UAA-P1-054`) | catch_up + surpass | Makes UAA's strengths visible: route authority, approval state, evidence receipts, safe previews, model status, observability timeline | Frontend tests, route manifest checks, no raw JSON primary UI |
| 3 | Rich observability review surface over M167 summaries | catch_up | Makes startup failures, slow actions, and task/capability failures visible without raw logs | New scoped UI/API doc and frontend tests |
| 4 | Session-log retention enforcement design | preserve + surpass | Turns redacted observability into an operational practice without destructive cleanup surprises | Retention model, verifier checks, no raw-data proof |
| 5 | Static package review (`UAA-P2-048`) | catch_up | Completes inspectable extension trust before runtime import exists | Schema/docs/tests plus documentation integrity |
| 6 | Frontend render timing runner | catch_up | Removes the current safe skipped Control Center render-timing row from latency evidence | Performance harness update and Foundation Gate latency report |
| 7 | CI lane workflow expansion (`UAA-P1-053`) | catch_up | Makes named release lanes visible in CI while preserving local verifier strictness | Safe CI lane reports |
| 8 | Security automation and artifact redaction lane (`UAA-P1-055`) | catch_up | Peer products often show more CI security automation; UAA should add it without public audit claims | Security scan and artifact redaction checks |
| 9 | Route grouping and side-effect consolidation (`UAA-P1-021`, `UAA-P1-052`) | preserve + surpass | Keeps 131-path API truth understandable as surfaces grow | OpenAPI contract and route manifest checks |
| 10 | PolicyEngine consolidation map (`UAA-P1-020`) | preserve | Finds parallel authority paths before product work expands | Authority map doc and focused tests |
| 11 | Product truth regression checks (`UAA-P1-057`) | preserve + surpass | Keeps blocked, skipped, planned, and not-scoped work honest in docs/UI/reports | Documentation integrity plus product language checks |
| 12 | Packaging proof expansion, signed/public distribution lane shaping only (`UAA-P2-047`) | catch_up | Mature peers have installer workflows; UAA should shape proof after local loop usability | Future scoped packaging milestone |
| 13 | Extension trust product surface (`UAA-P2-056`) | surpass | Productizes trust/provenance before plugin execution exists | Catalog/schema/UI checks; runtime import disabled |
| 14 | MCP/A2A runtime contract review, no runtime support yet | catch_up | Keeps ecosystem strategy current without enabling broad tool invocation | Watchlist-to-contract milestone |
| 15 | Memory lifecycle visibility, no hidden context injection | surpass | Builds product memory in a way that stays inspectable and deny-wins | Separate memory policy/UI milestone |

## Recommendation Status Table

Use this table for the active loop cursor. Move details into
`docs/backlog/codex_recommendation_log.md` when a row needs a longer decision
record.

| ID | Recommendation | Status | Owner | Evidence/ref | Next action |
|---|---|---|---|---|---|
| OEL-001 | Implement `UAA-P1-011` task decomposition operator loop | accepted baseline | Codex | `docs/kanban/current_board.md` Done; Founder Command Center docs use it as the readable-loop baseline | Continue readability/hardening in the next Founder Command Center lane |
| OEL-002 | Add richer M167 observability UI over safe summaries | proposed | ChatGPT/Codex | `docs/backlog/codex_recommendation_log.md` | Shape exact UI/API boundary |
| OEL-003 | Define retention enforcement for session logs | proposed | ChatGPT/Codex | `docs/observability/SESSION_LOGGING_M167.md` | Draft retention milestone |
| OEL-004 | Complete `UAA-P2-048` static package review | proposed | Codex | `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md` | Implement docs/schema/tests |
| OEL-005 | Add frontend render timing runner | proposed | Codex | Foundation Gate latency skipped row | Scope runner without browser/network overreach |
| OEL-006 | Add security automation lane | proposed | ChatGPT/Codex | `docs/production/RELEASE_VERIFICATION_LANES.md` | Shape lane and safe report contract |
| OEL-007 | Build route grouping and side-effect consolidation map | proposed | Codex | `docs/api/route_inventory.md` | Draft `UAA-P1-021` task |
| OEL-008 | Build PolicyEngine consolidation map | proposed | Codex | `docs/approvals/ACTION_POLICY.md` | Draft `UAA-P1-020` task |
| OEL-009 | Keep UAA's product posture as two layers: governance kernel plus operator cockpit | accepted | Human/Codex | `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md` | Prioritize first full operator loop |
| OEL-010 | Expand CI lane workflow visibility | proposed | Codex | `docs/production/RELEASE_VERIFICATION_LANES.md` | Draft `UAA-P1-053` task |
| OEL-011 | Add product truth regression checks | proposed | Codex | `docs/control_center/PRODUCT_LANGUAGE_RULES.md` | Draft `UAA-P1-057` task |

## ChatGPT Review Prompt Template

Use this template when asking ChatGPT to review the roadmap and propose the
next safe task. The response should be pasted back into Codex or converted into
a patch proposal.

```text
Review the Ultimate AI Agent Operator Excellence Catch-Up and Surpass Loop.
Use AGENTS.md, README.md, VERSION.md, PRODUCT_RELEASE_TRUTH_PACKET.md,
OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md, current_board.md,
OPERATOR_SHELL_GAP_MAP.md, ROUTE_STATUS_MANIFEST.md,
RELEASE_VERIFICATION_LANES.md, codex_recommendation_log.md, and
OPERATOR_EXCELLENCE_LOOP.md as the source order.

Goal: choose the next single safest, highest-leverage task that helps UAA catch
up to mature peer operator consoles or surpass them while preserving UAA's
contract-first foundation.

Return:
- decision: implement, shape, defer, or reject
- classification: catch_up, surpass, preserve, blocked, or rejected
- exact capability/surface
- authority boundary
- risk ceiling
- approval model
- persistence model
- redaction/audit requirements
- test plan
- verifier updates
- rollback plan
- docs impact
- stop conditions
- a Codex-ready implementation prompt

Do not propose public distribution, broad autonomy, unscoped shell/subprocess,
unrestricted network/browser automation, connector writes, plugin runtime import,
mobile control, raw prompt/provider payload logging, or model/provider output as
authority unless a later scoped milestone explicitly authorizes it.
```

## ChatGPT Direction Update Prompt

Use this prompt when asking ChatGPT to review and update the product direction
so development guardrails support both layers: governance kernel and operator
cockpit. The review should produce scoped roadmap edits and task proposals, not
runtime authority by itself.

```text
Act as an expert AI product architect, governance lead, security architect, and
enterprise AI risk advisor.

Review the Ultimate AI Agent roadmap direction and propose safe updates for a
two-layer product architecture:

1. Governance Kernel
   - automated guardrails
   - contract-first API and manifests
   - PolicyEngine and LocalApprovalAuthority
   - route authority and side-effect classes
   - redaction, safe refs, no-secret-output invariants
   - audit receipts, replay refs, rollback refs
   - release evidence and Foundation Gate checks

2. Operator Shell / Cockpit
   - developer/user cockpit over those guardrails
   - runtime health
   - local model readiness
   - UAA /v1 chat shell state
   - task plans and approvals
   - safe workspace previews and patch proposals
   - evidence receipts, audit summaries, latency, rollback, observability
   - settings and safe defaults

Goal:
Update the roadmap direction so development guardrails explicitly allow building
both layers together. Guardrails should permit scoped product actions only when
the action has exact capability scope, authority boundary, risk ceiling,
approval model, persistence model, redaction/audit requirements, tests,
verifier updates, and rollback plan.

Do not loosen safety. Treat "allow" as "allow through reviewed gates", not as
"allow broad runtime authority." Do not propose unscoped shell/subprocess
execution, unrestricted network/browser automation, connector writes, plugin
runtime import, mobile control, autonomous background execution, public
distribution, model/provider authority, raw prompt capture, raw provider payload
capture, raw file/log/path capture, credentials, or private-content capture.

Read these sources in order:
- AGENTS.md
- README.md
- VERSION.md
- docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md
- docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md
- docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md
- docs/kanban/current_board.md
- docs/control_center/OPERATOR_SHELL_GAP_MAP.md
- docs/control_center/ROUTE_STATUS_MANIFEST.md
- docs/production/RELEASE_VERIFICATION_LANES.md
- docs/backlog/codex_recommendation_log.md

Return:
- proposed product-direction wording
- guardrail interpretation: what is allowed, denied, and blocked pending a
  scoped milestone
- roadmap sections to update
- Kanban board updates
- clear task IDs and task titles
- for each task: capability/surface, authority boundary, risk ceiling, approval
  model, persistence model, redaction/audit requirements, test plan, verifier
  updates, rollback plan, docs impact, and stop conditions
- the next single implementation prompt for Codex

Prioritize the first full operator loop:
runtime health -> local model readiness -> UAA /v1 chat state -> task plan
creation -> approval of one safe registered capability -> receipt/audit/latency/
rollback inspection.

Preserve UAA's differentiator: every product surface must truthfully show real,
mocked, skipped, blocked, denied, planned, and not-scoped states without fake
completion or hidden authority.
```

## Codex Implementation Prompt Template

Use this template for one implementation iteration. Replace bracketed values
before running it.

```text
You are working in the Ultimate AI Agent repository.

Task:
Implement [TASK_ID] [TASK_TITLE].

Production posture:
Build this as [docs-only / verifier-only / local-only / scoped productionization]
work. Do not add broader production authority.

Global constraints:
- Follow AGENTS.md and the Operator Runtime Excellence roadmap.
- Preserve PolicyEngine, LocalApprovalAuthority, route side-effect
  classification, OpenAPI checks, and Foundation Gate checks.
- Do not add unscoped shell/subprocess execution, unrestricted network/browser
  automation, connector writes, plugin runtime import, mobile control,
  autonomous background execution, public distribution, model/provider authority,
  or raw data capture.
- No raw prompt, raw response, raw provider payload, raw path, raw log,
  username, hostname, serial, environment dump, credential material, or private
  content may appear in durable evidence, reports, release docs, tests, or logs.

Goal:
[ONE-SENTENCE GOAL]

Steps:
1. Inspect existing repo sources before changing files.
2. Make the smallest scoped change.
3. Add or update tests/verifiers/docs required by the roadmap.
4. Update the Kanban board only if Done criteria are met.
5. Run the verification commands below or explain exactly why they cannot run.

Verification:
[COMMANDS]

Report:
- files changed
- behavior added
- tests/verifiers run
- blockers or skipped prerequisites
- remaining risks
- rollback notes
```

## Morning Reconciliation Report Template

Use this when reviewing an overnight or multi-item session.

```text
Date:
Baseline:
Start commit:
End commit:

Completed:
- [task id]: [result]

Changed files:
- [path]: [purpose]

Verification:
- [command]: [pass/fail/skipped/blocker]

New recommendations:
- [id]: [summary]

Deferred or rejected:
- [id]: [reason]

Release blockers:
- [blocker]

Authority review:
- New authority added: no / yes, with scoped milestone
- Public/product claims changed: no / yes, evidence refs
- Raw/private data risk: none found / needs review

Rollback:
- [safe rollback summary]

Next single task:
- [task id and prompt ref]
```

## Rejected Shortcuts

These shortcuts may look faster but weaken the contract-first foundation:

- skipping documentation integrity, OpenAPI, Foundation Gate, or route manifest
  checks to keep the loop moving
- marking planned, blocked, skipped, mock, or not-scoped work as complete
- turning a peer feature into a UAA feature without a scoped authority boundary
- treating OpenWebUI, model output, connector output, plugin metadata, or
  ChatGPT review text as production authority
- adding broad package/installer/public-release claims before artifact proof
- adding browser/network/shell/plugin/mobile runtime behavior to close a
  product gap without explicit milestone approval
- preserving raw debug data because it is useful for troubleshooting

## Current Loop Cursor

`UAA-P1-011` is now the accepted readable operator-loop baseline. The next
recommended Founder Command Center implementation lane is macOS Setup Assistant
hardening, first product loop readability, Action Inbox / approval envelope UX,
Morning Briefing skeleton, and later read-only email/calendar integration
contracts.

Before implementing the next lane, draft an exact milestone prompt that covers:

- Control Center surfaces involved.
- Existing or proposed backend route contracts.
- durable run binding.
- approval model.
- safe registered handler execution scope, if any.
- audit/receipt/replay refs.
- denied hidden authority
- UI language and accessibility states
- tests and verifier lanes
- rollback notes

That task should prove the first real operator loop rather than add broad new
authority.
