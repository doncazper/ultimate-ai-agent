# Morning Reconciliation Artifact

Status: active UAA-P1-061 morning reconciliation artifact check
Baseline: v0.102.3 / 0.102.3
Source plan: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md` M177

This artifact format keeps looped ChatGPT/Codex recommendation work reviewable.
It records what completed, what was deferred, what was rejected, and what
remains blocked before the next roadmap progression.

It is an operating and evidence contract only. It does not add routes, runtime
authority, model/provider calls, web fetching, dependencies, shell/subprocess
behavior, connector writes, plugin runtime import, mobile control, public
distribution, or production authority.

Canonical files:

```text
docs/backlog/MORNING_RECONCILIATION_TEMPLATE.json
docs/backlog/reconciliation/
docs/schemas/morning_reconciliation_artifact.schema.json
scripts/verify_morning_reconciliation_artifact.py
tests/test_morning_reconciliation_artifact.py
```

## Purpose

A reconciliation artifact answers four questions for one work-session loop:

| Bucket | Meaning |
|---|---|
| `completed_recommendations` | Scoped recommendations finished in the repo with safe evidence refs. |
| `deferred_recommendations` | Useful ideas intentionally left for later because they are outside the current milestone or not yet ready. |
| `rejected_recommendations` | Ideas not accepted because they are stale, unsafe, superseded, not aligned, or outside project invariants. |
| `blocked_recommendations` | Work that cannot progress without user judgment, missing scope, missing evidence, environment state, or a later milestone. |

The artifact is a companion to `docs/backlog/codex_recommendation_log.md`. The
recommendation log can capture the running history; the reconciliation artifact
is the checkpoint summary before proceeding.

## Artifact Instances

Actual conveyor reconciliation artifacts live under:

```text
docs/backlog/reconciliation/
```

Each conveyor pass should create or update one JSON artifact from
`docs/backlog/MORNING_RECONCILIATION_TEMPLATE.json`. Instance files must use
safe refs and summaries only. They must not store raw session transcripts,
raw prompts, raw responses, raw provider payloads, raw local paths, raw logs,
account data, private content, or credential material.

Use a stable, date-prefixed filename such as:

```text
docs/backlog/reconciliation/2026-06-21-conveyor-reconciliation-durability.json
```

## Required Fields

| Field | Meaning |
|---|---|
| `schema_version` | Must be `uaa_morning_reconciliation_artifact.v1`. |
| `task_ref` | Must be `UAA-P1-061`. |
| `reconciliation_id` | Safe reconciliation ref for this checkpoint. |
| `created_at_utc` | Timestamp for the checkpoint. |
| `source_loop_ref` | Safe ref for the loop/session being reconciled. |
| `operator_readiness_taxonomy_ref` | Ref to `docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md`. |
| `recommendation_log_ref` | Ref to `docs/backlog/codex_recommendation_log.md`. |
| `safe_summary` | Redacted summary of the checkpoint. |
| `completed_recommendations` | Completed recommendation refs and evidence refs. |
| `deferred_recommendations` | Deferred recommendation refs, reason codes, and next action refs. |
| `rejected_recommendations` | Rejected recommendation refs and safe reason codes. |
| `blocked_recommendations` | Blocked recommendation refs, blocking gates, and needed user/scope action refs. |
| `next_prompt_ref` | Safe ref or summary ref for the next prompt, not the raw prompt body. |
| `reconciliation_safety` | Safety flags proving raw/private material was not stored. |

## Safety Rules

- Store safe refs, short summaries, reason codes, and evidence refs only.
- Do not store raw prompt content, raw response content, raw provider payloads,
  raw local paths, raw logs, usernames, hostnames, serials, environment dumps,
  credential material, account data, private content, or raw branch command
  output.
- Do not use this artifact to create roadmap scope, grant authority, accept
  failures, or mark work shipped without separate evidence.
- Use `deferred` for useful work outside the current milestone.
- Use `rejected` for stale, unsafe, superseded, or non-aligned work.
- Use `blocked` when user judgment, missing scope, missing evidence, or a later
  accepted milestone is required.
- Use `completed` only when the exact scoped work has safe evidence refs and
  the relevant checks passed or blockers are documented.

## Verification

Run:

```bash
.venv/bin/python scripts/verify_morning_reconciliation_artifact.py
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py --root .
```

The verifier is deterministic and inspection-only. It validates the schema,
template, artifact instances, required buckets, safety flags, safe-ref posture,
and active docs links. It does not execute prompts, inspect private conversation
content, call models, fetch the web, or create artifacts.

## Rollback

Rollback is to remove this document, template, schema, verifier, tests,
`verify_all` hook, active docs links, and the UAA-P1-061 Done entry on the
current board. No runtime state, route, authority, migration, or persistent user
data is changed.
