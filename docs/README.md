# Ultimate AI Agent Docs

Status: active
Current through: v0.30.1
Purpose: Human-facing entrypoint for active documentation and historical archive navigation.

Active docs are few, indexed, and current. Historical docs are preserved under
`docs/archive/`, clearly treated as audit artifacts, and are not current source
of truth.

Start with:

```text
docs/DOCUMENTATION_INDEX.md
docs/canonical/09_roadmap.md
docs/canonical/CANONICAL_DOC_MAP.md
docs/roadmap/README.md
docs/archive/README.md
docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md
```

Current release packet:

```text
docs/archive/releases/v0_30_1/README_IMPORT.md
docs/archive/releases/v0_30_1/master_plan.md
docs/release_notes/v0_30_1.md
docs/implementation/foundation_gate_implementation_plan_v0_30_1.md
docs/recall/GROUNDED_RECALL_ROUTER.md
docs/recall/CONTEXT_PACK_BUILDER.md
docs/recall/RECALL_SOURCE_PRIORITY.md
docs/recall/CONTEXT_PACK_SAFETY.md
```

Use active canonical docs and active roadmap docs for current work. Use archive
docs only for historical review. Git tags and release history preserve exact
historical snapshots.

v0.29.5 is documentation policy polish only. It accepts the pushed duplicate
wording cleanup from `374bb1e` and remains the cleanup baseline before M26.

v0.30.1 hardens M26 Grounded Recall Router + Evidence-Linked Context Pack
Builder source identity checks. It adds no backend routes, frontend features,
vector search, embeddings, external retrieval, model/provider calls, memory
writes, context injection runtime, dependencies, tool execution, or production
authority. M27 remains planned/provisional and future.
