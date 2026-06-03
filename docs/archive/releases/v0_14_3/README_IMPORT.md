Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# README Import v0.14.3

Status: Active baseline after the open-source-first private mesh taxonomy patch.

Import these files first:

```text
README.md
VERSION.md
ultimate_ai_agent_master_plan_v0_14_3.md
docs/remote/REMOTE_WORKER_FOUNDATION.md
docs/remote/REMOTE_NODE_SECURITY_MODEL.md
docs/remote/REMOTE_JOB_ENVELOPE.md
docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md
docs/remote/TAILNET_TRANSPORT_POLICY.md
docs/decisions/remote_worker_tailnet_foundation.md
docs/decisions/ADR-open-source-first-private-networking.md
docs/api/README.md
docs/api/route_inventory.md
docs/implementation/foundation_gate_implementation_plan_v0_14_3.md
```

v0.14.3 is a targeted patch to the accepted v0.14.2 baseline. It does not start M11.

The patch makes private mesh/tailnet taxonomy vendor-neutral and open-source-first. Headscale is planned self-hosted/open-source metadata only, generic WireGuard/private mesh is planned metadata only, and Tailscale remains a planned proprietary-control-plane option rather than the default assumption.

No live networking exists in this patch.
No Headscale, Tailscale, tailscaled, WireGuard, or `wg` integration exists in this patch.
No job dispatch, remote execution, remote Tool Broker execution, remote subagents, file transfer, shell execution, background services, personal-data access, write/send actions, remote approvals, credentials, tokens, node keys, hostnames, or private IPs exist in this patch.
