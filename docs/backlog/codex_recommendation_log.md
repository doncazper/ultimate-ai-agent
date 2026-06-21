# Codex Recommendation Log

Status: Active backlog note
Purpose: Track Codex recommendations, follow-up prompts, decisions, completed work, and unfinished revisions across multi-prompt work.

This log is an operating aid only. It is not an implementation claim, milestone
charter, approval record, release gate, authority grant, memory write, context
injection surface, or production runtime feature.

## Use

Add one entry per recommendation thread or prompt chain. Keep entries concise
and evidence-linked. Prefer file paths, command names, issue IDs, or report refs
over pasted raw content.

Status values:

```text
proposed
accepted
in_progress
done
deferred
rejected
```

Each entry should record:

```text
Date:
Thread:
Recommendation:
Next prompt:
Decision:
Status:
Completed:
Not done:
Evidence:
```

## Entries

### 2026-06-21 - Local Model Manager / Memory-Aware Runtime Control

Date: 2026-06-21

Thread: User-provided model changer roadmap review.

Recommendation: Add a later governed Local Model Manager lane for llama.cpp
that keeps Python Agent Core as the authority for installed GGUF discovery,
current loaded-model status, memory-fit planning, start/stop, safe switching,
one-big-model enforcement, UAA/OpenWebUI identity receipts, redacted status/logs,
and rollback. Control Center and OpenWebUI should render the cockpit and request
governed actions only.

Next prompt:

```text
Implement UAA-P1-062 as a docs-only roadmap and product-truth update. Keep it in
Spec Draft after cleanup/product-truth work; add no routes, CLI commands,
process control, downloads, dependencies, model calls, or runtime authority.
```

Decision: Accepted as roadmap/task-shaping guidance.

Status: accepted

Completed: Mapped the recommendation to `UAA-P1-062` in the Operator Runtime
Excellence roadmap, current Kanban Spec Draft, Control Center gap map, product
truth packet, and product language rules.

Not done: No runtime implementation, backend route, CLI command, process
control, download authority, model call, dependency, Control Center execute
control, or production authority was added.

Evidence: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`,
`docs/kanban/current_board.md`, `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`,
`docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`,
`docs/control_center/PRODUCT_LANGUAGE_RULES.md`.

### 2026-06-21 - Branch Cleanup Triage

Date: 2026-06-21

Thread: Repository cleanup across stale Codex branches and local worktrees.

Recommendation: Treat `codex/uaa-p1-053-ci-lane-workflow`,
`codex/uaa-p1-054-control-center-screens`,
`codex/latency-lane-hardening`, and
`origin/codex/uaa-p1-055-security-redaction` as superseded by the current
mainline squash commits and verification lanes rather than merging stale branch
heads. Defer `codex/typescript-7-rc-upgrade` because it only upgrades the
Control Center to a TypeScript 7 release candidate from an older frontend
baseline. Reject the untracked local `scripts/dev/start_*.sh` launcher scripts
from the repo because they hardcode local paths, direct process launches, an
external routing proxy, and local API-key literals outside the governed local
model manager lane.

Next prompt:

```text
Fold any surviving branch-cleanup ideas into active docs only, keep runtime
authority blocked, and delete stale local/remote branch refs after main passes
verification.
```

Decision: Accepted as cleanup guidance.

Status: accepted

Completed: Preserved the useful model lifecycle idea in `UAA-P1-062` and kept
stale branch/runtime launcher work out of the active code path.

Not done: No TypeScript RC upgrade, direct llama.cpp launch script, external
routing proxy script, or branch-head merge was added to main.

Evidence: `docs/kanban/current_board.md`,
`docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`,
`docs/control_center/OPERATOR_SHELL_GAP_MAP.md`.

### 2026-06-19 - Two-Layer Product Direction Prompt

Date: 2026-06-19

Thread: Direction update for building both the governance kernel and operator
shell/cockpit layers.

Recommendation: Ask ChatGPT to review UAA's direction as a two-layer product:
governance kernel as automated guardrails and operator shell as the
developer/user cockpit. The guardrails should allow scoped product actions only
through reviewed gates, not broad runtime authority.

Next prompt:

```text
Use the ChatGPT Direction Update Prompt in
docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md to review the roadmap direction and
return scoped roadmap/Kanban/task updates for building both the governance
kernel and operator cockpit layers.
```

Decision: Accepted as direction-review prompt.

Status: accepted

Completed: Added two-layer product wording to the Operator Runtime Excellence
roadmap and added a ChatGPT direction-update prompt to the Operator Excellence
loop.

Not done: No runtime implementation or authority expansion was added.

Evidence: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`,
`docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md`.

### 2026-06-19 - Peer Catch-Up Recommendations Layered Into Roadmap

Date: 2026-06-19

Thread: UAA versus GoatCitadel catch-up/surpass recommendations.

Recommendation: Layer the accepted recommendations into the Operator Runtime
Excellence roadmap and current Kanban board: decide product posture, prioritize
the first full operator loop, modularize the API, expand named CI/release
lanes, add product-grade Control Center differentiator screens, preserve UAA's
stricter authority model, add security automation and artifact redaction
checks, productize extension trust before execution, defer installer/public
distribution catch-up until local loop usability, and keep readiness language
honest.

Next prompt:

```text
Implement UAA-P1-011 Task decomposition operator loop. Start with the current
board, OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md, OPERATOR_EXCELLENCE_LOOP.md,
OPERATOR_SHELL_GAP_MAP.md, ROUTE_STATUS_MANIFEST.md, task decomposition API
tests, durable run binding tests, and Control Center tests. Build only the first
scoped operator loop: runtime health, local model readiness, UAA /v1 chat state,
task plan creation, approval of one safe registered capability, and
receipt/audit/latency/rollback inspection. Preserve PolicyEngine,
LocalApprovalAuthority, route side-effect classification, OpenAPI checks,
Foundation Gate checks, redaction, and no hidden authority.
```

Decision: Accepted as roadmap/task-shaping guidance.

Status: accepted

Completed: Recommendations were mapped to `UAA-STRAT-001`, `UAA-P1-011`,
`UAA-P1-020`, `UAA-P1-021`, `UAA-P1-052`, `UAA-P1-053`, `UAA-P1-054`,
`UAA-P1-055`, `UAA-P1-057`, `UAA-P1-058`, `UAA-P1-059`, `UAA-P1-060`,
`UAA-P1-061`, `UAA-P2-047`, and `UAA-P2-056`.

Not done: No runtime/product implementation was added by this roadmap patch.
`UAA-P1-011` remains the next implementation unit.

Evidence: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`,
`docs/kanban/current_board.md`, `docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md`.

### 2026-06-19 - Operator Excellence Catch-Up Loop

Date: 2026-06-19

Thread: Human-reconciled ChatGPT/Codex recommendation loop for catching up to
or surpassing mature peer operator-console systems.

Recommendation: Use `docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md` as the
repo-owned loop contract for turning peer comparisons and model recommendations
into one scoped, verifiable task at a time. Keep the loop tied to AGENTS.md,
the product truth packet, Operator Runtime Excellence roadmap, current board,
route status manifest, release lanes, and this recommendation log.

Next prompt:

```text
Read docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md and select the next single
highest-leverage scoped task. Return the classification, authority boundary,
risk ceiling, approval model, persistence model, redaction/audit requirements,
test plan, verifier updates, rollback plan, docs impact, stop conditions, and a
Codex-ready implementation prompt. Do not implement more than one task.
```

Decision: Accepted as an operating aid.

Status: accepted

Completed: Added the loop spec and linked it from active docs.

Not done: No product gap is implemented by this planning artifact. The current
suggested loop cursor remains `UAA-P1-011 Task decomposition operator loop`
unless the human reconciler selects another scoped item.

Evidence: `docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md`.

### 2026-06-19 - Verifier Latency Deep Dive

Date: 2026-06-19

Thread: `verify_all.py` and adjacent validator latency review.

Recommendation: Ask Codex to inspect `scripts/verify_all.py`, verifier scripts,
pytest configuration, Foundation Gate, OpenAPI checks, duplicated scans,
subprocess invocations, parsing work, and safe opportunities for caching,
batching, deterministic memoization, shared parsed artifacts, narrower
changed-file discovery, or safe parallelism.

Next prompt:

```text
Deeply inspect scripts/verify_all.py and adjacent test/validator
infrastructure for semantic-preserving latency reductions. Treat faster but
less strict as a failure. Preserve Foundation Gate, OpenAPI, documentation
integrity, and contract-first behavior. Return a verifier-flow map, ranked
hotspots, safe recommendations, risky/rejected shortcuts, a minimal patch plan,
and a verification plan with before/after timing evidence.
```

Decision: Proposed for follow-up.

Status: proposed

Completed: A reusable deep-dive prompt was drafted.

Not done: No repository latency changes have been implemented from this thread
yet. No timing baseline has been captured for this specific prompt chain yet.

Evidence: User request in the Codex thread on 2026-06-19.

### 2026-06-19 - M167 Operator Observability Follow-Up

Date: 2026-06-19

Thread: M167 redacted session logging spine follow-up gaps.

Recommendation: Separately scope richer operator UI over the bounded
safe-summary observability API and retention policy enforcement for session
logging artifacts. Keep the follow-up exact-scope, redacted-only, and aligned
with the existing M167 limitation that no destructive retention cleanup or rich
Control Center observability dashboard was claimed.

Next prompt:

```text
Design a separately scoped follow-up for M167 redacted session logging that
adds richer operator UI over the existing safe-summary API and defines
retention policy enforcement without weakening redaction, raw-content denial,
or authority boundaries. Start by reading
docs/observability/SESSION_LOGGING_M167.md,
src/ultimate_ai_agent/core/observability/session_logs.py,
src/ultimate_ai_agent/api/app.py, Control Center route docs, and existing tests.
Return the exact capability scope, non-goals, UI/API boundaries, retention
model, approval and audit implications, verifier updates, tests, rollback plan,
and risks. Do not implement destructive cleanup, raw log access, external
telemetry/export, background monitors, or new runtime authority unless a later
milestone explicitly authorizes those behaviors.
```

Decision: Proposed for follow-up.

Status: proposed

Completed: The gap was identified as a known M167 limitation after the session
logging commit.

Not done: No richer Control Center observability surface has been implemented.
No retention enforcement has been implemented.

Evidence: `docs/observability/SESSION_LOGGING_M167.md` documents no
destructive retention cleanup and no rich Control Center observability
dashboard in M167.
