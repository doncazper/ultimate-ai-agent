# Ultimate AI Agent Version

Current active baseline: **v0.27.0**

v0.27.0 implements M23 First Real Local LLM Call, Non-Tool,
Non-Authoritative. It adds a manual/CLI-only, loopback-only, fixed-prompt-only
local model call path with dry-run default, explicit `--execute-local-call`,
local approval validation, fake-transport test/gate coverage, response
redaction, non-authoritative receipts, docs, verifier coverage, and Foundation
Gate criteria.

It adds no backend API route, OpenAPI path count change, runtime activation,
endpoint probe, user-content model call, arbitrary prompt input, provider SDK,
local runtime client package, tokenizer, billing API, OpenWebUI runtime bridge,
Control Center execution control, tool execution, memory write, file write,
remote execution, dependency, or production authority. Tests and Foundation
Gate use fake transport only. A real manual local call was not run for release
validation. OpenAPI path count remains `74`. M24-M40 remain
planned/provisional.
