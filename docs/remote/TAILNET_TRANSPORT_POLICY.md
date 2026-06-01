# Tailnet / Private Mesh Transport Policy

M10.5 includes planned tailnet/private mesh and LAN transport metadata only. v0.14.3 makes this taxonomy vendor-neutral and open-source-first. It is foundation-only and does not configure or call any private networking system.

No live networking exists in this milestone.
No job dispatch exists in this milestone.
No remote approvals exist in this milestone.

The planned tailnet/private mesh transports are disabled by default, marked planned-only, and cannot support dispatch, file transfer, subagents, credentials, or live network access. Status endpoints report static planned/disabled metadata only.

v0.14.3 keeps Headscale, generic WireGuard/private mesh, Tailscale, tailnet, and LAN support as planned metadata only. Headscale is the preferred planned self-hosted/open-source control-plane option to evaluate first. Tailscale remains a planned proprietary-control-plane option, not the default assumption.

No Headscale support is implemented.
No Tailscale support is implemented.
No WireGuard support is implemented.
No mesh networking, CLI call, control-plane API call, Serve/Funnel configuration, hostname, private IP, auth key, node key, token, credential, or network transport is introduced.
