# Foundation Gate Implementation Plan v0.18.4

Status: Active for post-M20 roadmap projection and M21-M40 capability-layer charters.

v0.18.4 is docs/roadmap/canonical planning only. It adds Foundation Gate coverage for post-M20 roadmap projection docs without implementing any M21-M40 capability.

Post-M20 roadmap projection criteria:

- active import, master plan, release notes, and Foundation Gate implementation plan exist for v0.18.4.
- `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md` exists.
- `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md` exists.
- `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md` exists.
- `docs/roadmap/ECOSYSTEM_WATCHLIST.md` exists.
- `docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md` exists.
- M21-M40 are present and marked planned/provisional.
- docs do not claim M21-M40 are implemented.

The gate must continue to fail if roadmap docs imply runtime execution, model/provider calls, tool execution, MCP runtime support, Agent Skills runtime support, AGENTS.md runtime loading, sandbox execution, browser automation, Computer Use, remote execution, mobile sensor access, native app implementation, native build workflows, plugin enablement, dependencies, external network integrations, or production authority.

## Skill Package Security Rule

v0.18.4 does not change the Skill Package Security Rule. MCP, Agent Skills, AGENTS.md runtime loading, plugin installers, OpenWebUI plugins/functions/pipelines/tools, browser automation tools, sandbox providers, and native build plugins remain disabled until dedicated future milestones explicitly approve them.

All skills are untrusted packages by default. Before any future skill or plugin package can be trusted, it must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.
