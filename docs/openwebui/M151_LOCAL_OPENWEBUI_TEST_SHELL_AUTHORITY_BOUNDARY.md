# M151 Local OpenWebUI Test Shell Authority Boundary

M151 Local OpenWebUI Test Shell is local-dev-only, disabled by default, and
localhost-only. It is a smoke-test shell, not a runtime autonomy feature.

OpenWebUI is a shell, not the agent brain. UAA Agent Core remains the boundary
for policy, consent, audit, safety, and future authority decisions.

Allowed in M151:

- expose `GET /v1/models` for the single safe local model
- expose `POST /v1/chat/completions` for deterministic safe responses
- accept simple `system`, `user`, and `assistant` messages
- deny streaming
- deny tool and function call requests
- return safe summary and safety receipt flags
- run OpenWebUI locally through the developer launcher when explicitly started

Denied in M151:

- no provider call
- no model authority
- no tool execution
- no memory write
- no context injection
- no external network
- no raw prompt logging
- no raw provider payload exposure
- no browser automation
- no plugin execution
- no shell authority
- no backend execution route
- no Control Center execute control
- no OpenWebUI package dependency
- no production authority

The bearer value `uaa-local-test` is a local smoke value, not a committed
credential. Do not use this gateway outside local development.
