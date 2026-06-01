# Foundation Gate Implementation Plan v0.14.3

v0.14.3 extends the M10.5 Foundation Gate with open-source-first private mesh taxonomy checks.

Skill Package Security Rule:

All skills are untrusted packages by default. Before any skill package can become an executable or high-trust capability it must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

Gate additions:

- private mesh taxonomy includes planned Headscale metadata.
- private mesh taxonomy includes planned generic WireGuard metadata.
- private mesh taxonomy includes planned Tailscale metadata without enabling it.
- open-source-first and self-hosted-control-plane-first policy metadata exists.
- planned private mesh transports remain disabled, planned-only, no-network, no-credential, and no-dispatch.
- no Headscale, Tailscale, tailscaled, WireGuard, or `wg` command/API integration exists.
- no private mesh auth keys, node keys, hostnames, private IPs, tailnet names, tokens, OAuth data, or credentials are present in remote-worker docs or runtime metadata.

Gate continuations:

- remote worker files exist.
- risky remote capabilities default false.
- unknown nodes and transports are denied.
- dry-runs dispatch nothing.
- remote worker source has no live network, process, listener, private transport call, or background runtime imports.
- remote subagents, remote tool execution, remote approvals, personal-data access, write/send actions, and critical actions remain denied.
- remote output is untrusted.
- API exposes validation/status/dry-run only.
- docs say foundation-only.

No live networking exists in this patch.
No job dispatch exists in this patch.
No remote approvals exist in this patch.
