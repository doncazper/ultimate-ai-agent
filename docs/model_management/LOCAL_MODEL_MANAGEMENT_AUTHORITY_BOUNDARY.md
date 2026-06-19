# Local Model Management Authority Boundary

M152 local model management is contract-only and review-only. It records safe
metadata and safe refs for a future local model manager, but it does not make the
manager live.

Allowed in M152:

- Injected hardware capability buckets.
- GGUF model artifact refs and license/provenance refs.
- Inert Hugging Face search preview terms such as `qwopus`.
- Deterministic selection previews from injected candidate refs only.
- llama.cpp settings-plan refs for ctx size, GPU layer plan, fit, batch,
  ubatch, threads, KV cache type, mmap/mlock, prompt cache, and Flash Attention.
- Redacted local observability summaries for settings, lag, error, crash, and
  suggested adjustment refs.
- No-effect receipt-plan refs.

Denied in M152:

- No network access.
- No subprocess.
- No llama.cpp import.
- No llama.cpp server.
- No Hugging Face hub import.
- No Hugging Face hub download.
- No downloads.
- No model load.
- No model unload.
- No model delete.
- No model/provider call.
- No backend route.
- No Control Center execute control.
- No dependency.
- No memory write.
- No context injection.
- No tool execution.
- No production authority.

Any future live behavior must be introduced by a later reviewed milestone that
explicitly changes this boundary.
