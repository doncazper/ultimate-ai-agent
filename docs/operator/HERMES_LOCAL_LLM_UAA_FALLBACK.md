# Hermes + Local LLM UAA Fallback

Status: active manual fallback setup and handoff instructions

Purpose: prepare a local Hermes Agent plus a local, OpenAI-compatible model so
the operator can launch UAA and continue bounded repository work when the
preferred coding assistant is unavailable or its usage allowance is exhausted.

This is a manual fallback, not an automatic quota watcher or unattended
failover. It does not grant Hermes, a local model, OpenWebUI, or model output
authority over UAA. `AGENTS.md`, Python Agent Core, PolicyEngine,
LocalApprovalAuthority, AuthorityLease, exact approvals, receipts, redaction,
safe-disable, the kill switch, and the queue instructions remain authoritative.

The fallback has two separate surfaces:

1. UAA runs normally through its local launcher and Control Center.
2. Hermes uses a local model as an operator-invoked coding assistant.

UAA's guarded Hermes bridge is preferred for one bounded query. A direct
interactive Hermes coding session is outside UAA runtime governance and must
therefore use an isolated worktree, Hermes checkpoints, normal approval
prompts, and the repository rules below. Never use `--yolo`,
`--ignore-rules`, dangerous bypass flags, or broad unattended authority.

## Variables Used Below

Set these in the terminal without storing their resolved values in queue
artifacts, receipts, screenshots, or durable evidence:

```bash
export UAA_REPO="<your Ultimate AI Agent checkout>"
export UAA_QUEUE_DIR="<the queued-prompts directory>"
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
```

The queue directory must contain:

- `manifest.json`
- `CHECKPOINT_TAG_PLAN.md`
- this fallback runbook
- the 11 recorded prompt files

## One-Time UAA Preparation

Run from the UAA repository:

```bash
cd "$UAA_REPO"
python3 --version
npm --version
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
npm --prefix apps/control-center install
./scripts/dev/uaa doctor
PYTHONPATH=src .venv/bin/python scripts/inspect_build_identity.py
```

Do not use a local development bypass as production authority. Do not run an
installer, model download, Docker image pull, provider login, or credential
operation merely because this runbook exists.

## One-Time Hermes Preparation

Confirm Hermes is already installed and inspect its version:

```bash
command -v hermes
hermes version
hermes chat --help
```

If Hermes is absent, use the current official Hermes Agent installation
documentation and review the installer before running it. Do not pipe an
unreviewed remote script directly into a shell, do not install plugins or
skills for this fallback, and do not place credentials in this file.

Official references:

- https://hermes-agent.nousresearch.com/docs/reference/cli-commands
- https://hermes-agent.nousresearch.com/docs/user-guide/configuring-models
- https://hermes-agent.nousresearch.com/docs/guides/local-ollama-setup
- https://github.com/NousResearch/hermes-agent

## Configure A Local Model

The local model must support tool calling and must have enough context for
agentic repository work. Hermes's current local-model guidance calls for a
64,000-token context window for full agentic use. Configure the runtime and
Hermes to the same actual context limit. A smaller or non-tool-capable model is
acceptable for read-only summaries but must not be trusted to edit, test,
review, merge, or tag the repository.

### Recommended Simple Path: Existing Ollama

Use an already-reviewed local Ollama installation:

```bash
ollama --version
ollama list
curl --fail --silent --show-error http://127.0.0.1:11434/api/tags >/dev/null
```

If no suitable tool-capable model is present, model acquisition is a separate
explicit operator action. Select a model that fits the machine, supports tool
calls, and can run with the configured context window. Do not silently add a
cloud fallback.

Configure Hermes interactively:

```bash
hermes model
```

Choose a custom/local endpoint and enter:

```text
Base URL: http://127.0.0.1:11434/v1
API key: no-key
Model: <the exact local model ID>
Context length: <the runtime's actual context, at least 64000 for agentic work>
```

The resulting model section should have this shape:

```yaml
model:
  default: "<local-model-id>"
  provider: "custom"
  base_url: "http://127.0.0.1:11434/v1"
  context_length: 64000
```

For a slow local model, add only this non-secret timeout setting to the Hermes
environment file:

```text
HERMES_API_TIMEOUT=1800
```

Remove or disable cloud fallback providers if the goal is a fully local
session. Confirm no external API credential will be selected by provider
auto-detection.

### UAA llama.cpp Path

UAA can prepare a loopback llama.cpp/OpenWebUI plan:

```bash
cd "$UAA_REPO"
./scripts/dev/uaa setup --profile local-llama --plan --explain
```

The command is preview-only. Follow its current generated plan only after the
GGUF, `llama-server`, provenance, integrity, local lifecycle, rollback, and
approval requirements are satisfied. Configure Hermes as a custom provider
against the reviewed loopback llama.cpp `/v1` endpoint and use the exact model
alias exposed by that server. Keep any local API key in the approved secret
location or transient environment, never in this runbook.

Do not use UAA's fixed-response M151 smoke gateway as a coding model. It exists
to prove shell compatibility and intentionally does not provide general model
or tool execution.

## Verify Hermes Is Actually Local

From a directory containing no sensitive or uncommitted work:

```bash
hermes chat \
  --query "Reply with a short local-readiness acknowledgement and perform no tools." \
  --quiet \
  --source uaa-local-fallback
```

Confirm from Hermes's model/provider display that the selected provider is the
intended loopback endpoint. Stop if it selects a cloud provider, asks for a
remote credential, cannot fit the configured context, or cannot produce valid
tool calls.

## Launch UAA With Hermes Visibility

In the UAA repository:

```bash
cd "$UAA_REPO"
export UAA_ENV=local
export UAA_HERMES_INTERFACE_MODE_ENABLED=1
export UAA_HERMES_CLI_PATH="$(command -v hermes)"
./scripts/dev/uaa doctor
./scripts/dev/uaa trial-boot
./scripts/dev/uaa status
./scripts/dev/uaa runtime inspect-interface-mode
./scripts/dev/uaa runtime inspect-hermes-context-pack
```

Control Center is the first-party product surface. OpenWebUI, when available,
remains a secondary shell. Neither UI can mint authority.

## Optional Governed One-Shot Hermes Query

Guarded Hermes chat requires an active, time-bounded
`workspace/execute` AuthorityLease. The operator may issue one only after
reviewing the exact scope:

```bash
./scripts/dev/uaa runtime select-authority-mode \
  --mode approved_safe_local_work_session \
  --domain workspace:execute \
  --scope session \
  --reason-ref reason-ref:operator:hermes-local-fallback \
  --idempotency-ref idempotency-ref:operator:hermes-local-fallback-lease \
  --duration-minutes 60 \
  --approve \
  --approved-by-actor-ref actor-ref:operator:local \
  --summary "Allow one bounded local Hermes fallback session."
```

Then submit one transient query:

```bash
./scripts/dev/uaa runtime hermes-chat \
  --mode shell_guarded \
  --query "Inspect the current UAA handoff posture and identify the next safe step." \
  --idempotency-ref idempotency-ref:operator:hermes-local-fallback-query
```

Approval identifiers alone grant nothing. The bridge still rechecks the exact
lease, mode, adapter, kill switch, safe-disable, query posture, and idempotency
before invoking Hermes.

## Continue Repository Work Directly With Hermes

Use this only when a bounded one-shot query is insufficient.

First inventory without mutation:

```bash
cd "$UAA_REPO"
git status --short --branch
git worktree list
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
gh pr list --state open
```

Never begin in a dirty root checkout. If a dedicated task worktree contains
intentional in-progress changes, continue there only after the operator
confirms it is the intended handoff. Otherwise start from synchronized clean
`origin/main` and let Hermes create an isolated worktree:

```bash
hermes chat \
  --worktree \
  --checkpoints \
  --source uaa-local-fallback
```

If already inside the confirmed dedicated task worktree, omit `--worktree`:

```bash
hermes chat \
  --checkpoints \
  --source uaa-local-fallback
```

Do not add `--yolo`. Do not add `--ignore-rules`. Paste this handoff request:

```text
You are the operator-invoked local fallback implementation agent for Ultimate
AI Agent.

Before editing, read AGENTS.md completely. Then read the queue manifest,
CHECKPOINT_TAG_PLAN.md, HERMES_LOCAL_LLM_UAA_FALLBACK.md, the exact current
queue prompt, and every repository reference named by that prompt.

Reconcile the current repository, origin/main, exact SHA, current branch,
worktrees, dirty and staged files, open PRs, recent merges, CI, and unresolved
review threads. Treat old SHAs, PR numbers, branch names, and status messages
as historical. Derive the first incomplete scope from current code, tests,
receipts, docs, and merged history.

Preserve all unrelated work and historical tags. Never reset, clean, stash,
overwrite, force-push, bypass AGENTS.md, use paid GitHub compute, expose
secrets/private content, or work in the user's dirty root checkout. Use one
isolated worktree, scoped branch, and merge-gated PR per required item or
phase. Do not skip, combine, reorder, or silently broaden queue work.

Python Agent Core remains authority. UI state, Hermes output, local model
output, memory, evidence refs, approval refs, and this handoff do not mint
runtime authority. Keep unknown authority denied. Preserve exact policy,
LocalApprovalAuthority, AuthorityLease, target, budget, readiness, deadline,
kill-switch, safe-disable, idempotency, replay, receipt, rollback, redaction,
OpenAPI, CLI/API/UI parity, and Foundation Gate boundaries.

Work focused-test first. Adversarially review each diff. Fix every actionable
in-scope finding. Commit, push, open/review/land the scoped PR only when the
queue grants that action and required exact-SHA checks are green. Synchronize
cleanly to origin/main before the next scope.

Create every annotated checkpoint tag required by CHECKPOINT_TAG_PLAN.md only
at its exact completed, merged, green, clean boundary. Never move an existing
tag. Install and smoke-test each checkpoint separately as required by that
plan.

Continue without routine prompts only inside the exact accepted queue scope.
Stop for an authority conflict, unsafe ambiguity, external-facility blocker,
failed required verification that cannot be repaired safely, tag conflict, or
missing queue item. Report exact evidence and blockers without claiming
unproved success.
```

Local models are more error-prone than strong hosted coding models. Keep
changes smaller, inspect diffs before approval, require tests before commit,
and perform human review before merge or tag creation.

## Stop And Revoke

Stop launcher-owned UAA services:

```bash
cd "$UAA_REPO"
./scripts/dev/uaa status
./scripts/dev/uaa stop
```

Revoke the fallback lease using the exact lease ref returned at issue time:

```bash
./scripts/dev/uaa runtime revoke-authority-lease \
  --lease-ref "<issued-lease-ref>" \
  --reason-ref reason-ref:operator:hermes-local-fallback-complete \
  --idempotency-ref idempotency-ref:operator:hermes-local-fallback-revoke \
  --summary "End the bounded local Hermes fallback session."
```

If Ollama was used, unload only the exact selected model when desired:

```bash
ollama stop "<local-model-id>"
```

Do not delete a task worktree until its intentional changes are committed,
reviewed, merged or otherwise preserved, and the corresponding main state is
verified.

## Fail-Closed Conditions

Do not continue if any of these is true:

- Hermes or the local model version/provenance is unknown.
- Hermes selects a cloud provider unexpectedly.
- The model lacks reliable tool calling or sufficient context.
- The UAA repository or intended worktree has unexplained changes.
- The queue manifest or supplemental plan digest does not verify.
- `origin/main`, the current branch, or an open PR cannot be reconciled.
- Required authority, approval, lease, safe-disable, kill-switch, budget,
  deadline, or adapter readiness is missing.
- Raw prompts, responses, logs, paths, credentials, provider payloads, or
  private source material would enter durable evidence.
- A required check is failing and no bounded in-scope repair is available.
- A checkpoint tag name already points to a different commit.

When blocked, preserve the current state, stop mutating work, and produce a
redacted evidence-backed handoff for the next operator or coding assistant.
