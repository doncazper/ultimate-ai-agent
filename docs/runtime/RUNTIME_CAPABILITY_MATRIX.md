# Runtime Capability Matrix

Status: Active M11 matrix contract, v0.15.0

The runtime capability matrix is a deterministic typed contract. It records what the current baseline can validate and what remains blocked, planned-disabled, manual-only, simulated-only, or dry-run-only.

Required M11 statuses:

| Surface | Status |
|---|---|
| simulated model runtime | simulated_only |
| local loopback policy | supported validation only |
| manual loopback smoke | manual_only |
| remote worker foundation | dry_run_only |
| private mesh planned | planned_disabled |
| tailnet planned | planned_disabled |
| Headscale planned | planned_disabled |
| generic WireGuard planned | planned_disabled |
| Tailscale planned | planned_disabled |
| mobile companion planned | planned_disabled |
| Device Capability Broker planned | planned_disabled |
| Codex plugin governance | planned_disabled, documentation/policy only |
| cloud provider runtime | blocked |

Every entry must keep:

- `real_model_call_allowed=false`
- `cloud_allowed=false`
- `secrets_allowed=false`
- Foundation Gate coverage enabled

The matrix is not a runtime dispatcher and does not inspect live Codex tools, keychains, provider credentials, remote hosts, local runtimes, mobile devices, or network state.
