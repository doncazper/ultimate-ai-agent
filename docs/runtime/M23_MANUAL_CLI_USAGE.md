# M23 Manual CLI Usage

Status: Active M23 CLI documentation for v0.27.1.

M23 is available only through `scripts/manual_local_model_call.py`.

The CLI defaults dry-run. A real manual local call attempt requires:

- `--execute-local-call`.
- `--fixed-prompt-id m23_fixed_local_model_smoke_v1`.
- loopback-only HTTP endpoint.
- validated local approval.

For llama.cpp server, use the OpenAI-compatible completions endpoint and the
llama.cpp planned runtime kind:

```bash
python scripts/manual_local_model_call.py \
  --runtime-kind llama_cpp_planned \
  --endpoint http://127.0.0.1:8080/v1/completions \
  --model local-gguf-model \
  --fixed-prompt-id m23_fixed_local_model_smoke_v1
```

This dry-run command validates the request without contacting the endpoint. If
`--execute-local-call` is later used with a validated local approval, UAA sends
only the fixed M23 smoke prompt with `stream=false`, receives a capped/redacted
safe completion summary, and treats model output as non-authoritative.

Reference: llama.cpp server documents OpenAI-compatible `/v1/completions` and
`/v1/chat/completions` endpoints in
[`tools/server/README.md`](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).

The CLI has no arbitrary prompt option, no prompt-file option, no stdin prompt
mode, no memory prompt mode, no OpenWebUI transcript prompt mode, no API key
option, no Authorization option, no Cookie option, and no output-file option.

The CLI adds no backend API route, no Control Center execution, no OpenWebUI
runtime bridge, no tool execution, no memory write, no file write, no
dependency, and no production authority. Tests and Foundation Gate use fake
transport. M24 remains future.
