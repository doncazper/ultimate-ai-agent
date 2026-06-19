# M167 Live Model Production Hardening Runbook

Use this runbook to collect reviewed evidence before building an M167 report.
Every result should be converted to safe refs and redacted summaries.

## Model Matrix

Run the same HF search, download, selection, llama.cpp launch, OpenWebUI chat,
and tuning flow across Apple Silicon, CPU-only, low RAM, discrete GPU, and
limited disk profiles. Record profile buckets, quant choice, context size,
GPU-layer setting, batch/ubatch setting, prompt cache state, Flash Attention
state, pass/fail status, latency, tokens per second, memory pressure, reloads,
crashes, and errors as safe refs.

## Installer And Runtime

Verify llama-server discovery, supported version checks, binary provenance,
checksum/signature review, arch compatibility, update handling, rollback,
offline mode, structured argv, and clear failure messages. Never store raw
local paths in evidence.

## Selection Quality

Calibrate fixed ranking weights against labeled real GGUF repos. Confirm hard
rejects override popularity, gated model handling requires approval, license
and provenance confidence is explicit, quant choice fits the hardware profile,
and disk/RAM/VRAM estimates match observed pressure.

## Tuning Advisor

Detect lag, crashes, OOM, repeated reloads, memory pressure, and slow tokens per
second. Suggest one change at a time. Apply changes only with approval-bound
evidence. Restart safely. Rollback to the previous known-good preset after any
restart failure, crash loop, or worse metric delta.

## OpenWebUI Real E2E

Point OpenWebUI at UAA's local `/v1` gateway. Verify auth, `/v1/models`,
`/v1/chat/completions`, redacted failure messages, reconnects, no raw
prompt/log leaks, and shell-only behavior. OpenWebUI must not become the agent
brain, install a plugin, use admin APIs, or gain tools/functions authority.

## Load And Soak

Run sustained localhost-only load and soak tests for concurrent requests,
repeated reloads, context pressure, bad model files, crash loops, port
conflicts, memory pressure, slow tokens per second, queue/backpressure, clean
shutdown, and rollback.

## Operational Controls

Keep operational controls ready for cache cleanup, model removal, stuck
downloads, corrupted GGUFs, rollback, credential rotation, metrics/log review,
safe offline mode, health checks, readiness checks, revocation, and kill switch
handoff to the approved production gate.

