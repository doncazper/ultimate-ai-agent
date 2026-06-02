# Runtime Capability Matrix

Status: Active M11 matrix contract, surfaced in CCC Web by v0.22.0 / M18.

The runtime capability matrix is a deterministic typed contract. It records what the current baseline can validate and what remains blocked, planned-disabled, manual-only, simulated-only, or dry-run-only.

Required M11 statuses:

| Surface | Status |
|---|---|
| simulated model runtime | simulated_only |
| local loopback policy | supported validation-only contract; real smoke execution remains manual-only, approval-gated, fixed-prompt-only, and non-authoritative |
| manual loopback smoke | manual_only |
| M23 fixed-prompt local model call | manual_only, dry-run default, approval-gated, loopback-only, non-authoritative |
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

v0.15.1 keeps the `local_loopback_policy` status as `supported` because policy validation is implemented. That status must not be read as readiness for automated smoke execution, production runtime execution, provider calls, or evidence authority.

v0.22.0 surfaces this matrix in `/runtime/local` as read-only metadata. It adds no backend route, no runtime execution, no model/provider calls, no manual smoke execution, and no production readiness claim. OpenAPI path count remains `74`.

v0.27.0 adds M23 manual fixed-prompt local model call contracts and CLI-only
execution gating. It does not change `/runtime/local`, add backend routes,
activate runtimes, probe endpoints, enable arbitrary prompts, write memory or
files, execute tools, or make model output authoritative.
