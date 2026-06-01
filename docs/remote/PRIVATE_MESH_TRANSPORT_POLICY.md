# Private Mesh Transport Policy

v0.14.3 keeps private mesh and tailnet terminology vendor-neutral and open-source-first.

Headscale is the preferred planned self-hosted/open-source control-plane option to evaluate first. Generic WireGuard/private mesh is also a planned option. Tailscale remains a planned proprietary-control-plane option to evaluate later, not the default assumption.

All entries are metadata only:

- `private_mesh_planned`
- `headscale_planned`
- `generic_wireguard_planned`
- `tailscale_planned`
- `tailnet_planned`
- `lan_planned`

No live networking exists in this patch.
No Headscale support is implemented.
No Tailscale support is implemented.
No WireGuard support is implemented.
No mesh discovery, node enrollment, control-plane API call, CLI call, listener, daemon, job dispatch, remote execution, remote approval, personal-data access, write/send action, or background service is implemented.

No node keys, auth keys, tailnet names, hostnames, private IPs, credentials, OAuth values, tokens, or private keys belong in the repository.

v0.14.5 documentation integrity does not implement private mesh execution. Headscale, generic WireGuard, Tailscale, private mesh, tailnet, and LAN remain planned/disabled metadata only.
