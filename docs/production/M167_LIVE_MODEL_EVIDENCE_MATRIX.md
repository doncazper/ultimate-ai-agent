# M167 Live Model Evidence Matrix

Status: active UAA-P0-004 evidence scaffold
Source checkpoint: checkpoint-m167
Authority source: M166 exact-scope local model production gate

This matrix records the required live local model evidence rows for the M167
hardening lane. It is safe-ref-only scaffolding. It does not start llama.cpp,
call OpenWebUI, download a model, run a load test, add a backend route, add a
Control Center control, add dependencies, grant new production authority, or
claim public distribution.

M166 remains the authority gate. M167 can only harden that gate with reviewed,
redacted, localhost-only evidence for the exact local llama.cpp and OpenWebUI
shell scope.

UAA-P0-005 adds the local/dev E2E smoke harness documented in
`docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md`. Matrix rows may cite
that harness by safe verification ref, but a smoke result does not by itself
promote any row to Proven without reviewed live evidence.

## Status Semantics

- Proven: reviewed live evidence exists, all blockers are cleared, rollback is
  ready, and verifier refs pass.
- Pending: the row is scoped, but reviewed live evidence has not been attached.
- Blocked: the row is scoped, but a named blocker ref must be cleared first.
- Not-scoped: the behavior is outside this task and requires a later accepted
  scoped milestone before it can be claimed.

Current state: no hardware row is Proven in this patch. The matrix is ready for
reviewed safe evidence attachment.

## Matrix

| Profile | Safe evidence ref | Reviewer ref | Hardware profile summary | Approved GGUF/model ref | llama.cpp/OpenWebUI shell status | Blocker status | Verification command/result ref | Rollback status | Production-readiness status |
|---|---|---|---|---|---|---|---|---|---|
| Apple Silicon | `evidence-ref:m167:matrix:apple-silicon` | `review-ref:m167:apple-silicon:pending` | Apple Silicon local profile bucket; no serial, hostname, username, or raw path material. | `model-ref:m167:approved-gguf:pending` | Pending; shell evidence must remain localhost-only, bearer-gated, and no tools/functions. | Pending - `blocker-ref:m167:apple-silicon:live-review-pending` | `verification-ref:m167:apple-silicon:pending` | Pending - `rollback-ref:m167:known-good-local-model:pending` | Pending; not production-ready until reviewed live evidence passes. |
| CPU-only | `evidence-ref:m167:matrix:cpu-only` | `review-ref:m167:cpu-only:pending` | CPU-only local profile bucket; processor identity and host details are redacted. | `model-ref:m167:approved-gguf:pending` | Pending; shell evidence must prove safe fallback and no tools/functions. | Pending - `blocker-ref:m167:cpu-only:live-review-pending` | `verification-ref:m167:cpu-only:pending` | Pending - `rollback-ref:m167:known-good-local-model:pending` | Pending; not production-ready until reviewed live evidence passes. |
| Low RAM | `evidence-ref:m167:matrix:low-ram` | `review-ref:m167:low-ram:pending` | Low RAM local profile bucket; exact memory and environment details are redacted. | `model-ref:m167:approved-gguf:pending` | Pending; shell evidence must prove safe memory-pressure behavior. | Blocked - `blocker-ref:m167:low-ram:pressure-threshold-pending` | `verification-ref:m167:low-ram:pending` | Pending - `rollback-ref:m167:known-good-local-model:pending` | Blocked; memory-pressure threshold evidence is missing. |
| Discrete GPU | `evidence-ref:m167:matrix:discrete-gpu` | `review-ref:m167:discrete-gpu:pending` | Local discrete GPU profile bucket; vendor, device id, and driver details are redacted. | `model-ref:m167:approved-gguf:pending` | Pending; local GPU evidence only, remote GPU and cloud GPU are not-scoped. | Pending - `blocker-ref:m167:discrete-gpu:live-review-pending` | `verification-ref:m167:discrete-gpu:pending` | Pending - `rollback-ref:m167:known-good-local-model:pending` | Pending; not production-ready until reviewed live evidence passes. |
| Limited disk | `evidence-ref:m167:matrix:limited-disk` | `review-ref:m167:limited-disk:pending` | Limited disk local profile bucket; volume names, raw paths, and exact capacity are redacted. | `model-ref:m167:approved-gguf:pending` | Pending; shell evidence must prove safe cache and rollback behavior. | Blocked - `blocker-ref:m167:limited-disk:capacity-threshold-pending` | `verification-ref:m167:limited-disk:pending` | Pending - `rollback-ref:m167:known-good-local-model:pending` | Blocked; limited-disk threshold evidence is missing. |

## Not-Scoped Cases

The matrix does not scope remote model servers, cloud GPUs, public benchmark
publication, external distribution, non-local OpenWebUI profiles, OpenWebUI
admin flows, OpenWebUI plugins, streaming authority, tool/function calling,
connector writes, plugin runtime import, mobile control, browser automation, or
autonomous background execution.

## Safety Rules

Rows may only attach safe refs and redacted summaries. Durable evidence must
not contain raw prompts, raw responses, raw provider payloads, raw local paths,
raw logs, usernames, hostnames, serials, environment dumps, credentials, or
secret-like values.

Any transition from Pending or Blocked to Proven requires reviewed live
evidence, reviewer refs, blocker clearance, verifier result refs, rollback refs,
and M166 authority-gate binding.
