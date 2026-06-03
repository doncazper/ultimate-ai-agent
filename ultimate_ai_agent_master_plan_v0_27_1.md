# Ultimate AI Agent Master Plan v0.27.1

Status: Current master plan for v0.27.1 / M23 Local LLM Call Safety Hardening.

Hardened:

- M23 fixed-prompt-only policy and docs.
- loopback-only endpoint tests, including hostile query keys and non-loopback
  IPv6 denial.
- safe endpoint labels so labels do not echo raw URL details.
- response contract tests for raw response storage and secret-like summaries.
- approval boundary checks so forged allowed-looking approval decisions do not
  authorize transport calls.
- CLI guardrails for prompt, auth, cookie, and output-file arguments.
- static verifier coverage for granular M23 docs and forbidden CLI expansion.
- Foundation Gate checks for endpoint labels, secret-like responses, forged
  approval decisions, and M23 policy docs.
- Foundation Gate report writing with same-directory temp files and atomic
  `os.replace` publication.

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

The Foundation Gate report-write hardening is tooling/test hardening only and
was not a v0.27.0 release blocker. A real manual local call is not required for
release validation. Tests and Foundation Gate use fake transport only. OpenAPI
path count remains `74`. M24 remains future.
