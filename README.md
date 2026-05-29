# Ultimate AI Agent v0.4.5 Canonical Bundle

This bundle extends v0.4 by making the foundation-first build order operational.

The v0.4 master plan already stated that scanners, companion proactivity, skill factory, and self-improving code must wait until the foundation works. v0.4.5 adds the files that enforce that decision:

- `docs/canonical/05_development_workflow.md`
- `docs/canonical/09_roadmap.md`
- `docs/kanban/current_board.md`
- `docs/operating/foundation_first_build_policy.md`
- `docs/definitions/definition_of_ready.md`
- `docs/definitions/definition_of_done.md`
- `docs/registry/capability_registry_v0_4_1.json`
- `docs/registry/dependency_graph_v0_4_1.md`

Core rule:

> Do not build scanners, companion proactivity, skill factory, or self-improving code before the kernel, memory/file system, event ledger, permission model, tool broker, and contract tests work.


## v0.4.5 Update

This bundle upgrades Model Routing from a draft module into a foundation-level implementation spec. It adds model routing schemas, routing evals, an updated ADR, dependency graph updates, Capability Registry updates, Kanban updates, and a module-readiness audit.

Key new rule:

> No high-volume scanners, proactive alerts, skill acquisition, self-improving code, or autopilot workflows until the Model Router, Cost Governor, Event Ledger, privacy routing policy, fallback behavior, and routing evals work.
