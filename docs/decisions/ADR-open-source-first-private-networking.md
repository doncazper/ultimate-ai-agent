# ADR: Open-Source-First Private Networking

Status: Accepted for v0.14.3 taxonomy only.

Decision:

Use an open-source-first private networking policy for future private mesh evaluation.

- Evaluate free/open-source/self-hosted private mesh options first where practical.
- Treat Headscale as the first planned self-hosted/open-source control-plane option to evaluate.
- Treat generic WireGuard/private mesh as a planned option.
- Keep Tailscale as planned provider metadata, not the default assumption.
- Keep all private mesh providers disabled and planned-only until a later reviewed milestone.

This ADR does not implement Headscale, Tailscale, WireGuard, mesh discovery, node enrollment, network calls, job dispatch, remote execution, remote approvals, file transfer, personal-data access, write/send actions, listeners, daemons, workers, schedulers, pollers, credentials, or production persistence.
