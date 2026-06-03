Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.25.1

Status: Current master plan for v0.25.1 / M21 hardening.

v0.25.1 hardens M21 OpenWebUI Bridge + Chat Shell Integration Contract safety
while keeping M21 contract/planning/validation only.

Implemented:

- stricter `raw_content_blocked` and `future_requires_contract` validation as
  blocked content-mode sentinels, not usable ref/envelope modes.
- explicit allowance for safe M21 content modes: `summary_only`, `ref_only`,
  and `redacted_preview`.
- authority text validation that permits negated boundary statements and rejects
  positive OpenWebUI authority claims.
- Pydantic model namespace compatibility hardening for OpenWebUI bridge
  contract models.
- Foundation Gate and `verify_all.py` recursive forbidden OpenWebUI config/path
  detection outside docs.
- Foundation Gate and `verify_all.py` scanning of
  `src/ultimate_ai_agent/core/openwebui_bridge/` for forbidden runtime/config
  fragments.
- tests covering raw content-mode semantics, authority text, and verifier scan
  coverage.
- release/version/doc alignment for v0.25.1.

Still not implemented:

- OpenWebUI integration or live connection.
- OpenWebUI deployment config or Docker config.
- OpenWebUI plugins, functions, pipelines, tools, admin, auth, cookies, API
  keys, admin tokens, or browser profile access.
- backend API route additions.
- frontend feature additions.
- M22 Local Model Runtime Activation Contract.
- M23 First Real Local LLM Call.
- runtime execution.
- local LLM call.
- model/provider calls.
- tool execution.
- memory writes.
- file access.
- remote execution.
- browser automation.
- Computer Use.
- mobile sensor access.
- plugin enablement.
- dependencies.
- production authority.

OpenAPI path count remains `74`. M22 and M23 remain planned/provisional.
