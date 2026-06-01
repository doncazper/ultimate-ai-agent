# Local Loopback Model Runtime

M9 adds a dev-only local loopback runtime adapter harness.

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

Tests and Foundation Gate use `FakeModelRuntimeTransport`. The default `DisabledNetworkTransport` never sends network traffic.

M9 does not add cloud models, provider SDKs, API keys, remote OpenAI-compatible APIs, tokenizers, billing APIs, web fetchers, browser automation, production persistence, production auth/OAuth, or external actions.

Model output is not authoritative evidence. Local loopback responses and simulated fallback responses include metadata marking `truth_authority=false`.
