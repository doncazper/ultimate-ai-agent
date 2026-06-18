# M160 Bounded Hugging Face GGUF Search

M160 bounded Hugging Face GGUF search is the first live local model management
capability. It is core-only and has no backend route or Control Center control.

Allowed:

- Bounded read-only public Hugging Face model metadata search.
- Unauthenticated HTTPS GET to `https://huggingface.co/api/models`.
- Constructed query parameters only, including `filter=gguf` and a bounded
  result limit.
- Metadata-only parsing for repo IDs, GGUF filenames, file sizes, license refs,
  gated status, likes/download counts, tags, and last-modified refs.
- Fake transport tests and an optional explicit live smoke test.

Denied:

- No downloads.
- No auth.
- No token.
- No cookies.
- No request body.
- No custom request headers.
- No raw response storage.
- No model card storage.
- No raw local paths.
- No model/provider call.
- No prompt processing.
- No subprocess.
- No llama.cpp.
- No cache write.
- No backend route.
- No Control Center control.
- No OpenWebUI authority.
- No memory write.
- No context injection.
- No tool execution.
- No dependency.
- No production authority.

M160 does not load or run a model. It only returns bounded, safe metadata for
GGUF candidates that later milestones may review for acquisition and runtime use.
