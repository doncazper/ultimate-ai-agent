Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.14.3

Status: Active baseline after the open-source-first private mesh taxonomy patch.

## v0.14.3 Change Log

This is a patch release on top of the accepted v0.14.2 M10.5 foundation. It does not start M11.

Taxonomy changes:

- private mesh/tailnet language is vendor-neutral.
- Headscale is represented as planned self-hosted/open-source metadata.
- generic WireGuard/private mesh is represented as planned metadata.
- Tailscale remains planned metadata and is not the default control-plane assumption.
- open-source-first and self-hosted-control-plane-first selection policy metadata is present.
- Foundation Gate checks prove planned mesh transports remain disabled and no live mesh integrations exist.

No live networking exists in this patch.
No job dispatch exists in this patch.
No remote approvals exist in this patch.
No Headscale, Tailscale, tailscaled, WireGuard, or `wg` integration exists in this patch.

Future remote networking work must compare Headscale, generic WireGuard/private mesh, and Tailscale before choosing an implementation, evaluating free/open-source/self-hosted options first where practical.
