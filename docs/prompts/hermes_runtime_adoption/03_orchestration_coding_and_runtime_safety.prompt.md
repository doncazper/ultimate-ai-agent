# Phases 19-27: Orchestration, Coding, And Runtime Safety

These phases make UAA better at supervising long-running work, coding projects,
multi-agent routing, and hard authority floors.

## Shared Acceptance For Phases 19-27

- Durable orchestration is inspectable from CLI/API/UI.
- Coding and multi-agent surfaces are proposal/read-only until exact lanes are
  graduated.
- Cost, prompt, context, and safety posture are operator-visible.
- Non-overridable deny floors remain in place.

## Phase 19: Session Lineage And Forks

Branch: `codex/hermes-adoption-19-session-lineage`
Commit: `Add session lineage and fork posture`

Full-strength: UAA can branch sessions/tasks for alternate approaches,
reviews, retries, and comparisons.

Repo-safe: add lineage read models linking user request, task, run, proof,
branch, parent, child, and reason.

Blocked / needs authority: cloning raw transcripts or hidden context into a new
runtime.

Exact promotion path: redacted fork envelope, explicit operator intent, safe
refs, retrieval log, and proof binding.

## Phase 20: Mixture-of-Agents As Virtual Provider

Branch: `codex/hermes-adoption-20-virtual-provider-moa`
Commit: `Add virtual multi-agent provider posture`

Full-strength: UAA can define presets like Codex implementer, Claude reviewer,
Hermes researcher, local verifier, and UAA supervisor.

Repo-safe: add preset contracts and readiness UI. No live model fan-out unless
exact provider/runtime authority exists.

Blocked / needs authority: model calls, provider SDK use, external runtime
dispatch, hidden advisor prompts.

Exact promotion path: route decision trace, cost estimate, approval mode,
per-agent output envelope, comparison proof, and safe-disable.

## Phase 21: Desktop Coding Project Model

Branch: `codex/hermes-adoption-21-coding-project-model`
Commit: `Harden coding project model posture`

Full-strength: UAA coding cockpit supports projects, repos, lanes, branches,
worktrees, files, diffs, tests, preview, terminal, Git, and proof.

Repo-safe: extend existing Coding Cockpit read models and UI without broad
runtime authority.

Blocked / needs authority: file mutation, shell, git mutation, browser preview,
provider calls, background coding agents.

Exact promotion path: patch proposal, checkpoint, exact apply, allowlisted test
commands, Git review lane, and proof receipts.

## Phase 22: Live Model Usage / Cost Analytics

Branch: `codex/hermes-adoption-22-usage-cost-analytics`
Commit: `Add runtime usage cost analytics posture`

Full-strength: UAA shows cost, tokens, latency, model, runtime, and task value
across native and delegated runtimes.

Repo-safe: add redacted accounting read models and manual/diagnostic receipts.

Blocked / needs authority: billing actions, provider calls, raw prompt storage.

Exact promotion path: provider result envelope, cost attribution, token
accounting, redacted receipt, and operator export.

## Phase 23: Prompt Stability Tiers

Branch: `codex/hermes-adoption-23-prompt-stability-tiers`
Commit: `Add prompt stability tier contract posture`

Full-strength: UAA separates stable identity/policy, context, volatile state,
retrieval, and operator turn data for caching and proof.

Repo-safe: add prompt/input contract docs and read models without storing raw
prompts.

Blocked / needs authority: hidden prompt injection, raw prompt persistence, and
model-output authority.

Exact promotion path: safe prompt manifest, hashes, refs, redaction, cache
policy, and proof link.

## Phase 24: Context Compression And Budget Pressure

Branch: `codex/hermes-adoption-24-context-budget-pressure`
Commit: `Add context budget pressure posture`

Full-strength: UAA warns, trims, summarizes, or asks before context exceeds
budget.

Repo-safe: add context budget read models, warnings, trimming proposals, and
blocked hidden compression labels.

Blocked / needs authority: model summarization calls or automatic context
mutation without exact scope.

Exact promotion path: compression proposal, approval/ref, summary receipt,
source coverage, and retrieval log.

## Phase 25: Hardline Command Blocklist Floor

Branch: `codex/hermes-adoption-25-hardline-command-blocklist`
Commit: `Harden hardline command blocklist floor`

Full-strength: UAA has a non-overridable catastrophic deny floor for local,
delegated, and future command lanes.

Repo-safe: define and test hardline command classifications even if command
execution remains blocked.

Blocked / needs authority: any override that bypasses the hardline floor.

Exact promotion path: security review, test corpus, route classification, and
Foundation Gate coverage.

## Phase 26: Fail-Closed Approval Timeouts

Branch: `codex/hermes-adoption-26-fail-closed-approvals`
Commit: `Harden fail closed approval timeout posture`

Full-strength: all approval waits deny by default when expired or ambiguous.

Repo-safe: harden approval envelope state machine, timeout labels, denial
receipts, and UI/CLI parity.

Blocked / needs authority: auto-approve, approve-all, standing broad authority.

Exact promotion path: narrow session-scoped grant, explicit expiration,
receipt, and revoke/safe-disable.

## Phase 27: Managed Scope / Admin-Pinned Config

Branch: `codex/hermes-adoption-27-managed-scope`
Commit: `Add managed scope policy posture`

Full-strength: UAA can pin safe policy defaults for a local operator or team
without hiding what is pinned.

Repo-safe: add local policy profile read model and docs. Do not write system
config or secrets.

Blocked / needs authority: privileged writes, MDM delivery, managed secrets,
or production enforcement claims.

Exact promotion path: local config source, precedence, verification, redacted
secret refs, rollback, and admin/operator proof.

