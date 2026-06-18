# M162 GGUF Model Acquisition

M162 GGUF model acquisition is a core-only, stdlib-only, exact-approved live
capability for acquiring Hugging Face GGUF artifacts into a UAA-owned cache.

Allowed in M162:

- Exact user approval for each acquisition request.
- Exact Hugging Face repo ID.
- Pinned revision, using an exact commit SHA.
- Exact `.gguf` filename.
- Explicit primary artifact refs.
- Explicit sharded artifact refs.
- Explicit `mmproj*.gguf` artifact refs.
- UAA-owned cache writes.
- Optional expected size and SHA-256 verification.
- Unauthenticated HTTPS GET by default.
- Fake transport tests and optional environment-gated live smoke.

Denied in M162:

- No auth by default.
- No token use.
- No broad model search during acquisition.
- No implicit shard expansion.
- No implicit mmproj discovery.
- No raw URL storage.
- No raw local path storage in receipts.
- No raw response storage.
- No model file read for inference or inspection.
- No model/provider call.
- No prompt processing.
- No llama.cpp process.
- No subprocess.
- No shell string.
- No backend route.
- No Control Center control.
- No dependency.
- No memory write.
- No context injection.
- No tool execution.
- No production authority.

M162 live exact-approved GGUF acquisition only downloads artifacts after the
request supplies an exact approval ref, pinned revision, and exact GGUF
filename. It writes to the UAA-owned cache and returns safe cache artifact refs,
sizes, and SHA-256 refs. It does not expose local filesystem paths, start
llama.cpp, load models, call models, or wire OpenWebUI.
