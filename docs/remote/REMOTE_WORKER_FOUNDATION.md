# Remote Worker Foundation

M10.5 is foundation-only. It defines local schemas, mock registries, static status metadata, and dry-run result contracts for future remote workers.

No live networking exists in this milestone.
No job dispatch exists in this milestone.
No remote approvals exist in this milestone.
No remote subagents, remote tools, listeners, background services, file transfer, shell execution, write/send actions, personal-data access, or critical actions are enabled.

Remote worker output is always untrusted remote output. It is never trusted control input, never truth authority, and never approval authority.

v0.14.2 hardens the M10.5 policy contract: `remote_tailnet_enabled=true` and `remote_personal_data_enabled=true` are rejected as unsupported in M10.5. Remote-worker API wrapper payloads reject unexpected top-level fields, and validation errors remain sanitized.

v0.14.3 adds open-source-first private mesh taxonomy only. Planned Headscale, generic WireGuard, Tailscale, private mesh, tailnet, and LAN metadata remains disabled, planned-only, and no-network. Headscale is a future self-hosted/open-source option to evaluate first; it is not installed, called, configured, or integrated. Tailscale and WireGuard are also not installed, called, configured, or integrated.

v0.14.5 documentation integrity does not change remote worker behavior. Remote workers remain validation/status/dry-run only and cannot dispatch jobs, execute remotely, approve actions, access personal data, or perform write/send actions.

## v0.18.4 Post-M20 Remote Boundary

v0.18.4 adds post-M20 roadmap projection docs only. M21-M40 do not authorize remote worker dispatch or remote execution. Future sandbox, browser, tool, or observability milestones must still keep remote worker output untrusted unless a dedicated reviewed milestone changes the contract.
