# M167 Live Model Production Hardening

M167 hardens the already accepted M166 local model production gate. It is the
checkpoint for real live model matrix testing, installer/runtime packaging,
selection quality validation, tuning advisor hardening, OpenWebUI real E2E,
load and soak tests, and operational controls.

The active UAA-P0-004 safe-ref-only matrix lives in
`docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md`. That matrix is evidence
scaffolding only: it records required hardware rows, reviewer refs, blocker
refs, verification result refs, rollback refs, and production-readiness status
without claiming that live evidence is already proven.

The active UAA-P0-005 local/dev E2E smoke harness lives in
`docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md`. It proves the local
loop where prerequisites exist and reports skipped or blocked safe-ref states
where approved GGUF, llama.cpp lifecycle, gateway, or rollback prerequisites
are unavailable.

The active UAA-P0-015 local packaging checklist lives in
`docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md`. Unverified or
unknown-provenance `llama-server` binaries are blocked or not production-ready
for M167 evidence.

The active UAA-P0-017 local operational runbook lives in
`docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md`. It documents safe,
degraded, blocked, and unsupported recovery states for local model operations
without adding runtime authority or public production support.

M167 does not replace M166. Production authority remains inherited from the
M166 production release gate. M167 adds a stricter evidence layer that must be
actual live evidence, reviewed live evidence, redacted summary only,
safe-ref-only, localhost-only, audit-bound, replay-safe, and rollback-bound.
Generated fixture evidence is non-authoritative until every record is bound to
a reviewer ref.

## Required Evidence

The model matrix must cover Apple Silicon, CPU-only, low RAM, discrete GPU, and
limited disk profiles. Each profile must show Hugging Face search, download,
selection, llama.cpp launch, OpenWebUI chat, tuning, and resource-fit coverage.
Metrics such as latency, tokens per second, memory pressure, crashes, reloads,
and errors are recorded as safe refs only.

Installer/runtime packaging must prove llama-server discovery, allowed
locations, supported versions, binary provenance, checksum or signature review,
offline behavior, rollback, cache cleanup, blocked/unknown provenance handling,
and clear failure messages.

Selection quality validation must calibrate ranking weights against real GGUF
repos. It must cover fit accuracy, license/provenance confidence, gated model
handling, quant choice, context limits, disk/RAM/VRAM estimates, and ranking
regression cases.

Tuning advisor hardening must detect lag, out-of-memory pressure, crash loops,
reload loops, and slow tokens per second. It may suggest one safe, bounded,
redacted, operator-confirmable change at a time. The operator rule is one
change at a time, apply only with
approval-bound evidence, restart safely, and rollback to a previous known-good
preset.

OpenWebUI real E2E must run OpenWebUI as a shell against UAA's local `/v1`
gateway. It must verify auth, `/v1/models`, `/v1/chat/completions`, failure
messages, reconnects, shell-only behavior, no OpenWebUI admin flow, no
OpenWebUI plugin, and no functions or tools authority.

Load and soak tests must cover concurrent requests, repeated reloads, context
pressure, bad model files, crash loops, port conflicts, memory pressure, slow
tokens per second, queue/backpressure, and clean shutdown or rollback behavior.

Operational controls must include runbooks for cache cleanup, corrupted GGUFs,
stuck downloads, port conflicts, credential rotation, rollback, offline mode,
safe evidence collection, blocked/unknown model state, safe-disable, metrics
review, and clear blocked or unsupported states.

## Safety

M167 evidence must contain no raw prompt, no raw response, no raw provider
payload, no credential, no raw local path, no raw log, no username, no env dump,
no backend route, no Control Center control, no dependency, and no unreviewed
side effects.
