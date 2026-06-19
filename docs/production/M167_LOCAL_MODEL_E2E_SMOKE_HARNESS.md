# M167 Local Model E2E Smoke Harness

Status: active UAA-P0-005 smoke harness

Source checkpoint: checkpoint-m167

Authority gate: checkpoint-m166 exact-scope local llama.cpp/OpenWebUI shell gate

This document defines the repo-owned local model E2E smoke harness for the
M160-M167 local model lane. The harness proves the reviewed local loop where
prerequisites exist and emits safe skipped or blocked states where they do not.
It does not grant model authority beyond the M166 local llama.cpp/OpenWebUI
shell scope.

## Scope

The harness covers:

- approved GGUF readiness or skipped because prerequisite unavailable
- llama.cpp supervisor discovery/status through the reviewed M163 lifecycle
- local `/v1/models`
- local `/v1/chat/completions`
- OpenWebUI shell compatibility
- auth failure
- safe failure
- rollback
- tools/functions/streaming denial unless a later scoped milestone changes it

The implementation entry point is
`run_local_model_e2e_smoke_harness` in the local model management core. The
required regression lane is
`PYTHONPATH=src .venv/bin/python -m pytest tests/test_m151_openwebui_local_gateway_api.py`.

## Local Prerequisites

The default local/dev run may execute without live local prerequisites. In that
case, GGUF readiness, llama.cpp lifecycle, local `/v1/models`, local
`/v1/chat/completions`, and rollback may report skipped or blocked while
OpenWebUI shell compatibility, auth failure, safe failure, and
tools/functions/streaming denial remain testable.

A full local proof requires:

- an approved GGUF/model safe ref
- a reviewer ref
- reviewed local llama.cpp runtime hints
- reviewed `llama-server` packaging/provenance refs from
  `docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md`
- local operational recovery refs from
  `docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md`
- explicit local lifecycle approval for the run
- loopback-only local `/v1` gateway configuration
- rollback plan ref

No runtime hint, evidence row, or release-facing report may contain raw local
paths, raw logs, environment dumps, username, hostname, serial, credentials, raw
prompt content, raw response content, or raw provider payload content.

## Status Semantics

| Status | Meaning |
|---|---|
| pass | The step completed inside the approved local scope and produced safe-ref-only evidence. |
| fail | The step contradicted the required safety or compatibility condition. |
| blocked | The step is scoped but cannot run until the named blocker is resolved. |
| skipped | The step did not run because a prerequisite was unavailable or not approved. |

The overall report is failed if any step fails, blocked if any step is blocked,
skipped if any step is skipped and none failed or blocked, and passed only when
all steps pass.

## Evidence Rules

Harness output is redacted summary only and safe-ref-only. Evidence fields are
structured refs such as `evidence-ref:p0-005:v1_models`,
`result-ref:p0-005:v1_models:passed`, `blocker-ref:p0-005:*`, and
`skipped-ref:p0-005:*`. When the reviewed local lifecycle actually starts, the
report records safe side-effect refs such as
`side-effect-ref:p0-005:llama-cpp-lifecycle-started` and
`side-effect-ref:p0-005:llama-cpp-lifecycle-stopped`.

Durable evidence must preserve these invariants:

- no raw prompt
- no raw response
- no raw provider payload
- no raw path
- no raw log
- no credential material
- no public distribution claim
- no new production authority claim

## OpenWebUI Shell Contract

OpenWebUI remains a shell. The smoke harness validates OpenAI-compatible local
shapes for the M151 shell and the M164 local `/v1` gateway, but it does not let
OpenWebUI become the agent brain, does not treat model output as authority, and
does not enable tools, functions, streaming, memory writes, context injection,
or external network behavior.

## Safe Failure Contract

Auth failure must deny incorrect local values with redacted detail. Unsafe chat
request shapes must fail safely. Tools/functions/streaming remain denied unless
a later accepted milestone names the exact authority boundary, approval model,
evidence plan, and rollback plan.

## Rollback

When the reviewed llama.cpp lifecycle starts during a local/dev proof, the
harness must stop it through the M163 supervisor path and report rollback by
safe ref and summary only. If no lifecycle starts, rollback reports skipped
instead of fabricating evidence.

## Non-Goals

UAA-P0-005 does not add unrestricted shell/subprocess execution, unrestricted
network or browser automation, connector writes, plugin runtime import, mobile
control, autonomous background execution, public distribution, provider/model
output authority, raw evidence export, or production readiness claims.
