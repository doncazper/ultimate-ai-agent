# Authority Graduation Board

Status: active planning board, does not grant authority
Baseline: UAA local-first governed Agent Core

This board exists to stop authority work from living forever as prompt
theatre while still preventing broad, unearned runtime power. Every lane moves
by evidence, not optimism:

```text
contract-only -> read-only / dry-run -> manual foreground action
-> scoped repeatable action -> limited automation -> broader capability
```

Each promotion must be implemented in a focused PR, reviewed, hardened, tested,
merged to `main`, and dogfooded before the next promotion. If a blocker cannot
be safely removed in the lane PR, the lane records why it remains blocked and
produces the next unblock prompt.

This board is overlap-aware. Earlier prompt packs may have already started or
completed pieces of a lane. Existing work should be verified and hardened, not
duplicated. A lane's current level is whatever the Python Core/API/CLI/tests,
release-surface truth, and dogfood evidence prove on `main`, not whatever a
roadmap or unmerged branch says.

## Global Promotion Rules

- Python Agent Core owns product truth.
- Control Center and OpenWebUI are presentation shells.
- No UI-only operator truth.
- No raw prompt, response, provider payload, source body, local path, credential,
  token, cookie, account, contact, or raw connector payload persistence.
- Approval refs are identifiers only until exact LocalApprovalAuthority scope
  validates.
- Every mutating lane must be exact-scoped, approval-bound, idempotent,
  auditable, redacted, rollback/safe-disable aware, CLI/API/core aligned, and
  tested.
- Every promotion must say what it still does not allow.
- The next move after a lane opens is: measure, dogfood, promote or freeze.

## Graduation Levels

| Level | Meaning | Minimum proof |
|---|---|---|
| 0. Contract-only | Docs, schemas, blocked UI, tests, no runtime authority. | Manifest entry, no-authority tests, product-language guard. |
| 1. Read-only / dry-run | Real inputs may be inspected or simulated, no external mutation. | Redacted receipts, safe refs, replay/idempotency posture where relevant. |
| 2. Manual foreground action | The operator explicitly approves one exact action. | Exact scope validation, receipt, evidence, rollback/safe-disable plan. |
| 3. Scoped repeatable action | The same exact action can repeat safely. | Idempotency, replay, conflict handling, dogfood evidence, failure posture. |
| 4. Limited automation | Scheduled/background only for the exact proven action. | Pause/cancel/revoke, run observability, approval renewal, alerting, receipts. |
| 5. Broader capability | More targets/providers/connectors/autonomy after evidence. | Promotion review, expanded tests, explicit new upper boundary. |

## Lane Board

| Lane | Current level | Next promotion condition | Tests required | Rollback / safe-disable | Dogfood evidence | Do not promote past this yet |
|---|---:|---|---|---|---|---|
| Web Evidence Lane | 1, narrow read-only GET candidate through `WebAccessGateway` only | Public HTTPS GET evidence works through gateway with allowlist, bounded redacted preview, audit refs, and no raw body/header persistence | WebAccessGateway contract/static guard tests, read-only fetch tests, redaction tests, OpenAPI/API manifest if route changes | Gateway deny-by-default, allowlist disable, per-request audit refs | `docs/control_center/authority_graduation_evidence/web_evidence_level1_2026_07_03.md`; blocked-domain receipts remain required before any wider web lane | No browser observe/action, auth/cookies, downloads/uploads, POST-style mutation, connector reads, memory/context injection, or production authority |
| Browser Lane | 0, contract-only/blocked | Observe-only browser read model uses gateway policy and produces redacted observation refs | Browser gateway ladder tests, no-click/no-form/no-cookie tests, visual/status tests if UI appears | Browser lane feature flag off, deny clicks/forms/auth/download/upload | Operator observations from safe local/test pages only | No clicks, forms, authenticated browsing, downloads, uploads, or browser action execution |
| Provider / Model Invocation Lane | 1-2 for exact scoped validation/tiny lanes; broad provider/model calls blocked | One capped provider/model call for summarize/classify/draft with cost cap, exact approval, safe prompt envelope, redacted receipt, and no output authority | Provider invocation lane tests, CostGovernor tests, credential readiness tests, no raw prompt/response tests | Provider kill switch, budget cap, credential revocation, per-call safe-disable | Real capped call receipts, cost receipts, output quality/friction notes | No autonomous model calls, broad router fallback, model-output-as-truth, memory write, action execution, or production claims |
| Connector Read Lane | 0-1, metadata/readiness posture only | Test-account read-only sync for one connector with OAuth scope proof, redacted metadata refs, no raw body/contact persistence | Connector read contract tests, OAuth scope tests, no raw account/contact/body tests | Revoke OAuth, disable connector adapter, purge local test-account cache refs | Test-account sync receipts and missing-scope/blocker receipts | No sends, writes, archive/delete/label/move, CRM writes, calendar writes, broad account sync, or production data |
| Connector Write / Send Lane | 0-1, draft/review semantics only | Draft-only outbound proposal, then send-to-self/test target with exact approval and idempotency | Connector delivery queue tests, no-send UI tests, send-to-self receipt tests when promoted | Adapter off switch, send target allowlist, idempotency replay, revocation | Draft receipts, send-to-self receipts, failure/retry posture | No real external recipients, batches, destructive writes, auto-send, or production connector writes |
| Local Shell / Subprocess Lane | 0-1, dry-run/contract and verifier commands only | Allowlisted foreground command with exact approval, bounded cwd/env, redacted output, receipt, and no arbitrary shell | Command proposal tests, allowlist tests, redacted output tests, no unrestricted subprocess tests | Disable allowlist entry, cwd/env sandbox, timeout, kill receipt | Real safe command receipts, denied command receipts, output redaction notes | No arbitrary shell, package installs without review, background processes, network shell, or privileged commands |
| Filesystem Mutation Lane | 1-2 for proposal/exact reviewed writes in narrow repo paths; broad mutation blocked | Diff proposal plus exact approved write for one safe path class with rollback patch and receipt | File review approval tests, path policy tests, secret/path redaction tests, rollback tests | Revert patch, safe path policy, write safe-disable | Approved/rejected diff receipts and rollback drill | No broad delete/export, home-directory writes, secret writes, or unreviewed generated changes |
| Memory Write / Context Injection Lane | Memory accept/correct narrow write exists; context injection contract-only | Separate memory-write promotions from context-pack preview/materialization; context may only become reviewable refs first | Memory decision tests, context no-injection tests, citation/source tests, no raw memory tests | Memory supersede/correct receipt, context-pack safe-disable, no hidden injection | Memory decision receipts, corrected recall friction notes | No automatic memory write, memory-as-truth, hidden prompt injection, connector-derived context, or broad context injection |
| Action Execution Lane | Narrow local task create commit exists; broad execution blocked | One additional exact Action kind proves approval, idempotency, receipt, evidence, rollback/safe-disable | Action Inbox state machine tests, local task commit tests, approval scope tests, evidence timeline tests | Action kind disable, rollback/safe-disable ref, receipt replay | Repeated foreground action receipts and blocked-action receipts | No broad approve-all, external effects, connector writes, shell execution, or autonomous action execution |
| Background Worker / Scheduler Lane | 0, contract-only/blocked | Only schedule an exact level-3 proven foreground action with pause/cancel/revoke and run observability | Worker contract tests, scheduler tests, approval renewal tests, pause/cancel tests | Global worker off switch, per-job disable, revocation, timeout | One safe scheduled dry-run/foreground-equivalent receipt set | No open-ended autonomy, self-selection of tasks, background provider calls, connector sends, or hidden loops |
| Streaming / Realtime Transport Lane | 1, read-model/status-only | SSE/WebSocket progress stream for existing run refs only, no control channel | Streaming progress read-model tests, auth/local tests, no mutation over stream tests | Close stream, disable transport, fall back to polling | Long-run progress receipts, disconnect/reconnect notes | No streamed tool execution, no live control, no provider streaming by default, no external transport authority |
| Credential / OAuth / Account Lane | 0-1, credential posture/vault refs and exact validation only | Test-account OAuth or credential enrollment with least scopes, redacted storage, revocation, and no secret display | Credential vault tests, OAuth scope tests, revocation tests, no secret leakage tests | Revoke grant, rotate/delete token, disable account adapter | Test-account enrollment and revocation receipts | No production accounts, broad scopes, secret export, account sync beyond scoped read lane, or connector writes |
| Packaging / Distribution Lane | 1, local unsigned package proof only | Repeatable local unsigned macOS app bundle proof with explicit not-signed/not-notarized/not-public labels | Package proof tests, visual/setup tests, product-language tests | Remove local bundle, disable launcher lane | Local launch/package proof, setup friction notes | No signing, notarization, public installer, auto-update, daemon/LaunchAgent, or distribution claim |
| Production Authority Lane | 0, blocked | Only after multiple lanes prove safe in dogfood and release truth gates agree | Release surface verifier, product truth verifier, security/redaction gates, full regression suite | Public-release freeze switch, rollback plan, release blocklist | Private dogfood acceptance, failure logs, manual signoff | No public beta/release/production claim until explicitly approved as its own release milestone |

## Blocker Handling

Every lane PR must try to remove blockers that are safe and in scope. If a
blocker cannot be removed, the PR must add or update a blocked report with:

- blocker ref
- why it was not unblocked
- safety or product risk
- missing contract/test/evidence
- smallest next safe action
- prompt path to unblock it next

The blocker report is not a parking lot. It is the next implementation queue.
