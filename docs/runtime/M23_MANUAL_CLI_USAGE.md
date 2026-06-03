# M23 Manual CLI Usage

Status: Active M23 CLI documentation for v0.27.1.

M23 is available only through `scripts/manual_local_model_call.py`.

The CLI defaults dry-run. A real manual local call attempt requires:

- `--execute-local-call`.
- `--fixed-prompt-id m23_fixed_local_model_smoke_v1`.
- loopback-only HTTP endpoint.
- validated local approval.

The CLI has no arbitrary prompt option, no prompt-file option, no stdin prompt
mode, no memory prompt mode, no OpenWebUI transcript prompt mode, no API key
option, no Authorization option, no Cookie option, and no output-file option.

The CLI adds no backend API route, no Control Center execution, no OpenWebUI
runtime bridge, no tool execution, no memory write, no file write, no
dependency, and no production authority. Tests and Foundation Gate use fake
transport. M24 remains future.
