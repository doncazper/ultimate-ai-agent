# Local Loopback Model Runtime

M9 adds a dev-only local loopback runtime adapter harness. v0.14.0 preserves endpoint hardening and adds an M10 manual smoke harness for explicit local/dev readiness checks.

The default runtime posture remains validate-only or simulated fallback. Real local loopback execution is available only through library code when all of these are true:

- endpoint host is loopback (`127.0.0.1`, `localhost`, or `::1`)
- endpoint URL has no username or password
- endpoint query has no secret-like parameter names
- endpoint is enabled
- policy explicitly sets `allow_real_loopback_execution=true`
- request uses local loopback dev safety mode
- selected route metadata exists
- validated local approval decision is supplied
- no credentials or secret handles are present
- token estimates fit policy and adapter limits
- transport is explicitly injected

Caller-supplied `allowed_hosts` values can narrow loopback endpoints, but they cannot expand the boundary to remote, private LAN, or public IP hosts. `deny_non_loopback=false` is rejected as an attempted override and does not permit non-loopback destinations. Adapter validation still denies non-loopback hosts unconditionally as defense in depth.

Tests and Foundation Gate use `FakeModelRuntimeTransport`. The default `DisabledNetworkTransport` never sends network traffic.

M10 manual smoke:

- disabled by default
- CLI-only for real local HTTP smoke calls
- uses `local_stub` runtime kind metadata
- requires an explicit manual enable flag and scoped local approval grant
- sends only the fixed prompt `Respond with exactly UAA_LOCAL_SMOKE_OK. This is a local smoke test. Do not include secrets.`
- must not process user prompts, memory, files, context packs, secrets, or task content
- is not production model execution and is not authoritative evidence
- is not called by tests, CI, `verify_all.py`, or Foundation Gate

The API exposes `/model-runtime/local/smoke/validate` for validation only. It does not expose a smoke execute route.

M9 does not add cloud models, provider SDKs, API keys, remote OpenAI-compatible APIs, tokenizers, billing APIs, web fetchers, browser automation, production persistence, production auth/OAuth, or external actions.

Model output is not authoritative evidence. Local loopback responses and simulated fallback responses include metadata marking `truth_authority=false`.

v0.14.5 documentation integrity adds no runtime readiness implementation, no general model execution, and no new local loopback execution path.
