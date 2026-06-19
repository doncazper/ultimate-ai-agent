# M153-M165 Local Model Management Progression

M153-M165 extend local model management through the completed local llama.cpp
model layer. M160 live bounded read-only HF GGUF search only may query public
Hugging Face model metadata. M161 live bounded read-only local system capability
probing only may produce redacted hardware buckets. M162 live exact-approved
GGUF acquisition only may fetch exact user-approved `.gguf` artifacts into a
UAA-owned cache. M163 live loopback llama.cpp supervisor only may start
`llama-server` with structured argv and redacted logs. M164 live local `/v1`
gateway only may expose approved llama.cpp models to OpenWebUI. M165 live
approved settings tuning only may recommend one adjustment at a time and apply
exact approved settings with rollback.

The completed M165 baseline still denies unapproved downloads, non-loopback
servers, shell strings, OpenWebUI plugins, Control Center execute controls,
dependencies, memory writes, context injection, tool execution, and production
authority.

## M153-M159 Safe Contract Lane

- M153 records injected hardware summaries, GGUF artifact refs, Hugging Face repo
  refs, license refs, provenance refs, model fit constraints, and no-effect
  receipt plans.
- M154 records llama.cpp settings-plan refs for ctx-size, n-gpu-layers, device,
  fit, batch, ubatch, threads, KV cache type, mmap, mlock, prompt cache, Flash
  Attention, and preset refs.
- M155 records inert Hugging Face search preview terms such as `qwopus`, query
  pool refs, and alternative pool refs without live search.
- M156 records a review-only Control Center Local Models settings surface and
  OpenWebUI settings guidance with no install controls.
- M157 records deterministic model selection previews from injected candidate
  refs only, including query matches, alternatives, hard rejections, and fixed
  ranking weights.
- M158 records redacted local observability and audit refs for settings, errors,
  lag, crashes, and suggested adjustment refs.
- M159 freezes the accepted M152-M158 local model management foundation.

## Live Lanes

- M160 enables bounded read-only Hugging Face GGUF metadata search through a
  core-only stdlib transport. It is unauthenticated, HTTPS GET only,
  metadata-only, route-free, dependency-free, and cannot download, load, or call
  models.
- M161 enables redacted local system capability probing through core-only stdlib
  calls. It reports OS/arch bucket, CPU core bucket, RAM bucket, VRAM bucket when
  safely available, backend/device family bucket, disk budget bucket, and
  power/thermal hints.
- M162 enables exact user-approved GGUF acquisition into a UAA-owned cache. Every
  artifact must name exact repo ID, pinned revision, exact `.gguf` filename,
  optional expected size, and optional expected SHA-256. Sharded refs and
  `mmproj*.gguf` refs are supported only when explicitly listed.
- M163 enables a loopback-only llama.cpp supervisor with structured argv, local
  API key handles, redacted logs, offline mode after cache warmup, and no shell
  strings.
- M164 wires approved llama.cpp models into UAA's local `/v1/models` and
  `/v1/chat/completions` gateway for OpenWebUI. Tools/functions and streaming
  remain disabled.
- M165 enables redacted lag/crash/error tuning recommendations and exact-approved
  settings apply/restart with rollback to the previous known-good preset.

M153-M159 are `safe_contract`. M160-M161 are `live_bounded_read_only`. M162 is
`live_exact_approved_acquisition`. M163 is `live_llama_cpp_supervisor`. M164 is
`live_openai_gateway`. M165 is `live_settings_tuning`. No checkpoints remain in
`future_live_contract_only`.

Exact static guard phrases: M161 live bounded read-only local system capability probing only.
M162 live exact-approved GGUF acquisition only. M163 live loopback llama.cpp
supervisor only. M164 live local `/v1` gateway only. M165 live approved settings
tuning only. no control center execute controls.
