# Ultimate AI Agent

Status: active
Current through: v0.31.0
Purpose: Root entrypoint for the current contract-first Python Agent Core workspace.

The active project baseline is v0.31.0. This release implements M27: Tool
Broker v2 + Safe Tool Intent Contracts as validation-only and preview-only
contract logic.

v0.29.5 is documentation policy polish only. It accepted the duplicate wording
cleanup from `374bb1e` and remains the cleanup baseline before M26.

Start here:

```text
VERSION.md
AGENTS.md
docs/README.md
docs/DOCUMENTATION_INDEX.md
docs/canonical/09_roadmap.md
docs/canonical/CANONICAL_DOC_MAP.md
docs/roadmap/README.md
docs/archive/README.md
docs/archive/releases/v0_31_0/README_IMPORT.md
docs/archive/releases/v0_31_0/master_plan.md
docs/release_notes/v0_31_0.md
docs/implementation/foundation_gate_implementation_plan_v0_31_0.md
docs/tools/TOOL_BROKER_V2.md
docs/tools/SAFE_TOOL_INTENT_CONTRACTS.md
docs/tools/TOOL_AUTHORITY_BOUNDARY.md
docs/tools/TOOL_INTENT_RECEIPT_PLAN.md
docs/tools/M27_TO_M28_BOUNDARY.md
docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md
```

Core rule:

> Python Agent Core is the brain. OpenWebUI is the preferred conversational web
> shell, not the agent brain. CCC means Control Center Clients and is the
> governance/control client family. Model output is not truth authority. Memory
> is recall, not authority.

v0.31.0 adds M27 safe tool intent contracts only. It adds no real tool
execution, shell/subprocess behavior, file mutation, memory writes, Event
Ledger mutation, backend tool execution routes, Control Center execute controls,
external network calls, web search, browser automation, Computer Use, plugin
enablement, model/provider calls, local LLM calls, retrieval/RAG/vector
behavior, context injection runtime, dependencies, M28 work, or production
authority. OpenAPI path count remains `74`. M28-M40 remain
planned/provisional.

Developer verification:

```bash
make doctor
make test
make verify
make frontend-check
```

Use `.venv/bin/python`, not bare `python`, for repo verification commands.
