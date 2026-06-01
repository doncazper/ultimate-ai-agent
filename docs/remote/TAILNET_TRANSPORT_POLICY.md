# Tailnet Transport Policy

M10.5 includes planned tailnet and LAN transport metadata only. It is foundation-only and does not configure or call any private networking system.

No live networking exists in this milestone.
No job dispatch exists in this milestone.
No remote approvals exist in this milestone.

The planned tailnet transport is disabled by default, marked planned-only, and cannot support dispatch, file transfer, subagents, credentials, or live network access. Status endpoints report static planned/disabled metadata only.

v0.14.2 rejects `remote_tailnet_enabled=true` as unsupported in M10.5. Tailnet support remains planned metadata only; no tailnet networking, Tailscale call, Serve/Funnel configuration, hostname, private IP, auth key, node key, or network transport is introduced.
