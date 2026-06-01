# Local Loopback Model Runtime

M9 adds a dev-only local loopback runtime adapter harness. v0.13.2 hardens its endpoint policy so hostile caller-supplied policy fields are rejected before adapter validation.

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

M9 does not add cloud models, provider SDKs, API keys, remote OpenAI-compatible APIs, tokenizers, billing APIs, web fetchers, browser automation, production persistence, production auth/OAuth, or external actions.

Model output is not authoritative evidence. Local loopback responses and simulated fallback responses include metadata marking `truth_authority=false`.
