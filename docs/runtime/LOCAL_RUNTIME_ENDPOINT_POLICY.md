# Local Runtime Endpoint Policy

Status: Active M22 contract documentation for v0.26.0. Contract-only.

M22 endpoint descriptors are metadata-only. They may describe future relative refs or loopback-only refs, but they must not contact an endpoint.

Allowed descriptor shapes:

- relative metadata ref.
- localhost loopback metadata ref.
- `127.0.0.1` loopback metadata ref.
- `::1` loopback metadata ref when represented safely.

Rejected descriptor shapes:

- external absolute hosts.
- public IP hosts.
- private LAN hosts.
- URL credentials.
- secret-like query strings.
- endpoint probe flags.
- endpoint contacted flags.
- activation allowed flags.

No model was called. No runtime was activated. No endpoint was contacted.

M22 adds no backend API route and keeps OpenAPI path count at `74`. M23 is
implemented/released by v0.27.0 as a separate manual fixed-prompt local call
path and does not authorize runtime activation or endpoint probes.
