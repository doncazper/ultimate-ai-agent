# Ultimate AI Agent Docs

Status: active
Current through: v0.31.0
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
docs/archive/releases/v0_31_0/README_IMPORT.md
docs/archive/releases/v0_31_0/master_plan.md
docs/release_notes/v0_31_0.md
docs/implementation/foundation_gate_implementation_plan_v0_31_0.md
docs/tools/TOOL_BROKER_V2.md
docs/tools/SAFE_TOOL_INTENT_CONTRACTS.md
docs/tools/TOOL_AUTHORITY_BOUNDARY.md
docs/tools/TOOL_INTENT_RECEIPT_PLAN.md
docs/tools/M27_TO_M28_BOUNDARY.md
```

Use active canonical docs and active roadmap docs for current work. Use archive
docs only for historical review. Git tags and release history preserve exact
historical snapshots.

v0.29.5 is documentation policy polish only. It accepts the pushed duplicate
wording cleanup from `374bb1e` and remains the cleanup baseline before M26.

v0.31.0 implements M27 Tool Broker v2 + Safe Tool Intent Contracts as
validation-only and preview-only contract logic. It adds no backend execution
routes, frontend execution controls, real tool execution, file mutation, memory
writes, network calls, model/provider calls, plugin enablement, browser
automation, context injection runtime, dependencies, M28 work, or production
authority. M28-M40 remain planned/provisional.
