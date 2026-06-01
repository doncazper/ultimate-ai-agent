# Remote Node Security Model

M10.5 remote nodes are foundation-only metadata records. Risky node capabilities default false:

- job execution
- subagent launch
- tool calls
- sandbox use
- network access
- personal-data access
- file writes
- message sends
- action approval
- critical work
- background work

No live networking exists in this milestone.
No job dispatch exists in this milestone.
No remote approvals exist in this milestone.

Remote nodes cannot approve their own actions, cannot approve user approvals, and cannot convert credentials into consent. Unknown nodes are denied.

v0.14.2 rejects `remote_personal_data_enabled=true` as unsupported in M10.5. Remote personal-data access remains disabled, and remote-worker policy validation must not imply that personal-data capability is available.

v0.14.3 private mesh taxonomy does not change node authority. Remote nodes cannot claim Headscale, Tailscale, WireGuard, host, address, key, credential, or tailnet metadata as authority. Future remote HIGH/CRITICAL work must create local approval requests rather than remote approvals.
