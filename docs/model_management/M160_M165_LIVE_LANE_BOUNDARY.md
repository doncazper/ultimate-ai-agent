# M160-M165 Live Lane Boundary

M160-M165 describe the completed local model management live lane.

Allowed:

- M160 bounded read-only Hugging Face GGUF metadata search.
- M161 bounded read-only local system capability probing with redacted buckets.
- M162 exact-approved GGUF acquisition into a UAA-owned cache.
- M163 loopback-only llama.cpp supervisor with structured argv and redacted logs.
- M164 local OpenAI-compatible `/v1` gateway for approved llama.cpp models.
- M165 tuning advisor plus exact-approved settings apply/restart/rollback.

Denied:

- No unapproved downloads.
- No authenticated Hugging Face request by default.
- No token use by default.
- No raw response storage.
- No raw model card storage.
- No raw local path in receipts.
- No raw paths.
- No serial, username, hostname, or environment dump.
- No broad scans.
- No non-loopback llama.cpp server.
- No shell string.
- No OpenWebUI plugin.
- No OpenWebUI admin API use.
- No OpenWebUI authority over UAA.
- No tools/functions through the M164 gateway.
- No streaming through the M164 gateway.
- No raw prompt logging.
- No raw response logging.
- No memory write.
- No context injection.
- No tool execution.
- No dependency.
- No production authority.

Tools/functions and streaming remain disabled. No serials. No usernames. No raw paths.
No environment dump. No backend route.

M160 live bounded read-only HF GGUF search only. M161 live bounded read-only
local system capability probing only. M162 live exact-approved GGUF acquisition
only. M163 live loopback llama.cpp supervisor only. M164 live local `/v1`
gateway only. M165 live approved settings tuning only.

Exact denial phrases: no serials. no usernames. no raw paths. no environment
dump. no broad scans. no control center execute controls. no dependency. no
memory write. no context injection. no tool execution. no production authority.
