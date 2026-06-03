Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.27.0

Status: Historical master plan for v0.27.0 / M23 First Real Local LLM Call,
Non-Tool, Non-Authoritative. Superseded by v0.27.1.

Implemented:

- M23 fixed-prompt local model call contracts.
- loopback-only endpoint validation with URL credential and secret query
  rejection.
- fixed prompt `m23_fixed_local_model_smoke_v1`.
- dry-run-only default result path.
- explicit `--execute-local-call` requirement for manual execution.
- local approval validation for execution attempts.
- fake transport for tests and Foundation Gate.
- manual stdlib loopback transport for CLI-only use.
- capped/redacted safe response summaries.
- non-authoritative receipts that record no tool, memory, file, provider, or
  remote execution.
- M23 docs, tests, static verifier coverage, and Foundation Gate criteria.

Still not implemented:

- backend API route for local calls.
- Control Center execution controls.
- OpenWebUI runtime bridge.
- runtime activation.
- endpoint probes.
- arbitrary prompt input.
- user-content model calls.
- stdin/file/clipboard/memory/OpenWebUI transcript prompts.
- provider SDK imports.
- runtime package imports.
- tokenizer packages.
- billing APIs.
- model loading.
- tool execution.
- memory writes.
- file writes.
- remote execution.
- dependencies.
- production authority.

A real manual local call was not run for release validation. Tests and
Foundation Gate use fake transport only. OpenAPI path count remains `74`.
M24-M40 remain planned/provisional.
