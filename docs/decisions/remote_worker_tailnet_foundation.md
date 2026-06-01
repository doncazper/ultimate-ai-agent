# Decision: Remote Worker and Tailnet/Private Mesh Foundation

M10.5 adds REMOTE-01 as a foundation-only boundary for future remote workers and planned private transports. v0.14.3 clarifies that private mesh/tailnet taxonomy is vendor-neutral and open-source-first.

Decision:

- Add remote worker schemas, registries, policies, dry-run contracts, and validation/status API routes.
- Keep all live remote worker behavior disabled.
- Mark remote worker output untrusted.
- Require future high-risk remote work to create local approval requests rather than remote approvals.
- Evaluate Headscale and generic WireGuard/private mesh before proprietary control-plane options where practical.
- Keep Tailscale as planned metadata, not the default assumption.

No live networking exists in this milestone.
No job dispatch exists in this milestone.
No remote approvals exist in this milestone.

This decision does not add mesh networking, tailnet transport, remote execution, remote tools, remote subagents, file transfer, listeners, schedulers, daemons, shell execution, personal-data access, or write/send actions.

This decision does not add Headscale support, Tailscale support, WireGuard support, control-plane API calls, CLI calls, node enrollment, credentials, tokens, node keys, hostnames, private IPs, or tailnet names.
