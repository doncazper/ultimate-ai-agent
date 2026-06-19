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
