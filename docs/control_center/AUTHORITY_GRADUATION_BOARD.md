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
| Web Evidence Lane | 1, implemented exact configured host allowlist HTTPS GET preview through `WebAccessGateway` only | `POST /control-center/web-evidence/attach` and `scripts/dev/uaa_founder_loop.py attach-web-evidence` attach one bounded redacted preview receipt to the local loop only when `UAA_WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS` includes the host and the safe-disable env is not active; durable Today/Evidence/Proof records keep safe refs, request-ref idempotency posture, and redacted WebAccessGateway audit summaries only and omit page text | `tests/test_web_evidence_product_slice.py`, `tests/test_beta_08_web_evidence_product_slice_verifier.py`, `scripts/verify_beta_08_web_evidence_product_slice.py`, WebAccessGateway contract/static guard tests, read-only fetch tests, redaction tests, OpenAPI/API manifest checks | Gateway deny-by-default, route rate limit, configured host allowlist, request-ref replay/conflict posture, per-request audit refs, local receipt suppression posture, safe-disable ref | `docs/control_center/authority_graduation_evidence/web_evidence_level1_2026_07_03.md`; new product-slice receipt/proof refs remain required before any wider web lane | No broad runtime authority, browser observe/action, auth/cookies, downloads/uploads, POST-style mutation, connector reads, memory/context injection, provider/model call, or production authority |
| Browser Lane | 1, injected observe-only/dry-run through `WebAccessGateway`; live browser runtime blocked | Live observe remains blocked until a later accepted lane; current proof only converts injected local/test observation metadata into redacted refs | Browser gateway ladder tests, no-click/no-form/no-cookie tests, visual/status tests if UI appears | Browser lane feature flag off, deny clicks/forms/auth/download/upload | `docs/control_center/authority_graduation_evidence/browser_observe_level1_2026_07_03.md`; live browser receipts remain blocked | No clicks, forms, authenticated browsing, downloads, uploads, live browser runtime, or browser action execution |
| Provider / Model Invocation Lane | 1-2 for exact scoped validation/tiny lanes plus fixture-proven provider draft/summarize core/CLI wrapper; broad provider/model calls blocked | Promote only after a real operator-approved test credential, exact approval, cost receipt, and live adapter proof are supplied for the same wrapper | `tests/test_provider_draft_summarize_lane.py`, `tests/test_beta_09_provider_draft_preview_verifier.py`, `scripts/verify_beta_09_provider_draft_preview.py`, Provider invocation lane tests, CostGovernor tests, credential readiness tests, no raw prompt/response tests | Provider kill switch, budget cap, credential revocation, per-call safe-disable | `docs/control_center/PROVIDER_DRAFT_SUMMARIZE_MICRO_LANE.md`; `docs/control_center/authority_graduation_blockers/provider_model_invocation_live_call_2026_07_03.md`; tiny lane posture inspected, live call blocked pending exact test credential/approval/cost receipt; `/proof` and `/trust` expose inspection-only refs | No autonomous model calls, broad router fallback, default Control Center provider invocation, default live provider network, durable draft preview persistence, provider SDK calls, model-output-as-truth, memory write, context injection, action execution, connector write, background provider calls, or production claims |
| Connector Read Lane | 0-1, metadata/readiness posture only; runtime sync blocked | Test-account read-only sync for one connector with OAuth scope proof, redacted metadata refs, no raw body/contact persistence | Connector read contract tests, OAuth scope tests, no raw account/contact/body tests | Revoke OAuth, disable connector adapter, purge local test-account cache refs | `docs/control_center/authority_graduation_blockers/connector_read_test_account_sync_2026_07_03.md`; source readiness verified as proposal/readiness only | No sends, writes, archive/delete/label/move, CRM writes, calendar writes, broad account sync, production account access, or production data |
| Connector Write / Send Lane | 1, backend-owned Connector Draft-Only Proposal refs implemented; live write/send blocked | Send-to-self/test target with exact approval, idempotency, receipt, and safe-disable proof | `tests/test_connector_draft_proposals.py`, `tests/test_beta_10_connector_draft_only_verifier.py`, `scripts/verify_beta_10_connector_draft_only.py`, Connector delivery queue tests, no-send UI tests, send-to-self receipt tests when promoted | Adapter off switch, send target allowlist, idempotency replay, revocation | `docs/control_center/CONNECTOR_DRAFT_ONLY_PROPOSALS.md`; `docs/control_center/authority_graduation_blockers/connector_write_send_test_target_2026_07_03.md`; Connector Delivery review queue and draft proposals remain no-send/no-live-runtime posture; live connector runtime remains blocked; Source Readiness, Inbox, Proof, Trust, and CLI expose review-only safe refs | No real external recipients, batches, destructive writes, auto-send, production account access, live connector runtime, OAuth/account sync, auth-material collection, or production connector writes |
| Local Shell / Subprocess Lane | 0-1, dry-run/contract/freeze only; execution blocked | Allowlisted foreground command with exact approval, bounded cwd/env, redacted output, receipt, and no arbitrary shell | Command proposal tests, allowlist tests, output redaction tests, no unrestricted subprocess tests | Disable allowlist entry, cwd/env sandbox, timeout, kill receipt | `docs/control_center/authority_graduation_blockers/local_shell_subprocess_allowlisted_command_2026_07_03.md`; M85/M90 verify read-only/freeze posture only | No arbitrary shell, package installs without review, background processes, network shell, privileged commands, or subprocess execution |
| Filesystem Mutation Lane | 2 for Python-core exact temp-workspace artifact patch/rollback; visible Files apply route blocked | Diff proposal plus exact approved write for one safe path class with rollback patch and receipt | File review approval tests, path policy tests, secret/path redaction tests, rollback tests | Revert patch, safe path policy, write safe-disable | `docs/control_center/authority_graduation_evidence/filesystem_mutation_level2_core_temp_workspace_2026_07_03.md`; `scripts/inspect_filesystem_mutation_lane.py` | No broad delete/export, home-directory writes, secret writes, unreviewed generated changes, shell/subprocess mutation, or Control Center apply-route claim |
| Memory Write / Context Injection Lane | Reviewed memory accept/correct recall-write and read-only context-pack preview implemented; runtime context injection blocked | Separate memory-write promotions from context-pack preview/materialization; context may only become reviewable refs first | Memory decision tests, context no-injection tests, citation/source tests, no raw memory tests | Memory supersede/correct receipt, context-pack safe-disable, no hidden injection | `docs/control_center/authority_graduation_evidence/memory_write_context_preview_2026_07_03.md`; context manifest CLI reports safe refs only and runtime injection false | No automatic memory write, memory-as-truth, hidden prompt injection, connector-derived context, runtime prompt/model context injection, or broad context injection |
| Action Execution Lane | `local_task_create` rank 5 local lane exists; additional Action kinds blocked | One additional exact Action kind proves approval, idempotency, receipt, evidence, rollback/safe-disable | Action Inbox state machine tests, local task commit tests, approval scope tests, evidence timeline tests | Action kind disable, rollback/safe-disable ref, receipt replay | `docs/control_center/FCC_ACTION_001_APPROVAL_BOUND_LOCAL_MICRO_LANES.md`; `docs/control_center/authority_graduation_blockers/action_execution_additional_exact_kind_2026_07_03.md` | No broad approve-all, external effects, connector writes, shell execution, provider/model calls, memory/context authority, or autonomous action execution |
| Background Worker / Scheduler Lane | 0, contract-only/metadata-only blocked | Only schedule an exact level-3 proven foreground action with pause/cancel/revoke and run observability | Worker contract tests, scheduler tests, approval renewal tests, pause/cancel tests | Global worker off switch, per-job disable, revocation, timeout | `docs/control_center/authority_graduation_blockers/background_worker_scheduler_limited_automation_2026_07_03.md`; coworker worker contracts remain metadata/read-only | No open-ended autonomy, self-selection of tasks, background provider calls, connector sends, queue consumers, worker runtime, or hidden loops |
| Streaming / Realtime Transport Lane | 1, read-model/status-only; live transport blocked | SSE/WebSocket progress stream for existing run refs only, no control channel | Streaming progress read-model tests, auth/local tests, no mutation over stream tests | Close stream, disable transport, fall back to polling | `docs/control_center/authority_graduation_blockers/streaming_realtime_read_only_transport_2026_07_03.md`; progress read model and CLI remain safe-ref metadata only | No streamed tool execution, no live control, no provider streaming by default, no external transport authority, and no SSE/WebSocket claim |
| Credential / OAuth / Account Lane | 0-1, credential posture/vault refs and exact validation only; OAuth/account runtime blocked | Test-account OAuth or credential enrollment with least scopes, redacted storage, revocation, and no secret display | Credential vault tests, OAuth scope tests, revocation tests, no secret leakage tests | Revoke grant, rotate/delete token, disable account adapter | `docs/control_center/authority_graduation_blockers/credential_oauth_account_test_enrollment_2026_07_03.md`; vault refs and exact provider validation are not account/OAuth authority | No production accounts, broad scopes, secret export, OAuth/token runtime, account sync beyond scoped read lane, or connector writes |
| Packaging / Distribution Lane | 1, local unsigned Docker/local-runtime proof plus local unsigned `.app` bundle artifact proof; app launch is not executed by verifier | Manual local app-launch smoke receipt only after safe foreground launch proof is scoped; public distribution stays blocked | Package proof tests, local macOS app bundle proof tests, visual/setup tests, product-language tests | Remove local bundle, delete ignored proof state, disable launcher lane | `docs/control_center/authority_graduation_evidence/packaging_distribution_local_macos_app_bundle_2026_07_03.md`; local runtime packaging proof remains loopback-only | No signing, notarization, public installer, auto-update, daemon/LaunchAgent, app-store/TestFlight flow, or distribution claim |
| Production Authority Lane | 0, blocked; release decision only, not a feature lane | No default promotion; only a separate accepted release milestone with completed dogfood evidence, full release gates, and manual signoff can grant one exact claim | Release surface verifier, product truth verifier, security/redaction gates, full regression suite, visual baseline acceptance | Public-release freeze switch, rollback plan, release blocklist, claim revocation | `docs/control_center/authority_graduation_blockers/production_authority_release_decision_2026_07_03.md`; private dogfood progress does not equal production authority | No public beta, public release, public distribution, reliable unattended-operation, broad autonomy, or production claim until explicitly approved as its own release milestone |

Beta 08 Web Evidence beta slice is the current hardening label for the Web
Evidence Lane row above. It adds configured host allowlist, durable safe-ref
audit summary, request-ref replay/conflict posture, and
`scripts/verify_beta_08_web_evidence_product_slice.py` without granting broad
runtime authority.

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
