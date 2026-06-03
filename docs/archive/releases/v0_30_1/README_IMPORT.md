# README Import v0.30.1

Status: active release packet
Current through: v0.30.1
Purpose: Import checklist for the M26 recall source identity hardening release.

Read first:

```text
README.md
VERSION.md
AGENTS.md
docs/README.md
docs/DOCUMENTATION_INDEX.md
docs/canonical/09_roadmap.md
docs/canonical/CANONICAL_DOC_MAP.md
docs/recall/GROUNDED_RECALL_ROUTER.md
docs/recall/CONTEXT_PACK_BUILDER.md
docs/recall/RECALL_SOURCE_PRIORITY.md
docs/recall/CONTEXT_PACK_SAFETY.md
docs/release_notes/v0_30_1.md
docs/implementation/foundation_gate_implementation_plan_v0_30_1.md
```

v0.30.1 hardens deterministic local recall/context-pack contracts only. It
enforces source_ref/source_kind consistency and prevents caller-declared
source_kind from upgrading memory/model/runtime/OpenWebUI refs into trusted
sources. It adds no recall execution route, context injection route,
vector/embedding runtime, model/provider call, memory write, dependency, or
production authority.
