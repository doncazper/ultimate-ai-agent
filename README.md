# Ultimate AI Agent

Status: active
Current through: v0.30.1
Purpose: Root entrypoint for the current contract-first Python Agent Core workspace.

The active project baseline is v0.30.1. This release hardens M26: Grounded
Recall Router + Evidence-Linked Context Pack Builder by enforcing recall
source_ref/source_kind consistency before candidate selection or context-pack
planning.

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
docs/archive/releases/v0_30_1/README_IMPORT.md
docs/archive/releases/v0_30_1/master_plan.md
docs/release_notes/v0_30_1.md
docs/implementation/foundation_gate_implementation_plan_v0_30_1.md
docs/recall/GROUNDED_RECALL_ROUTER.md
docs/recall/CONTEXT_PACK_BUILDER.md
docs/recall/RECALL_SOURCE_PRIORITY.md
docs/recall/CONTEXT_PACK_SAFETY.md
docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md
```

Core rule:

> Python Agent Core is the brain. OpenWebUI is the preferred conversational web
> shell, not the agent brain. CCC means Control Center Clients and is the
> governance/control client family. Model output is not truth authority. Memory
> is recall, not authority.

v0.30.1 adds M26 recall source identity hardening only. It adds no backend
routes, frontend features, vector search, embeddings, semantic search, RAG
ingestion, web search, external retrieval, source crawling, arbitrary file
reads, model/provider calls, local LLM calls, memory writes, evidence mutation,
Event Ledger mutation, context injection runtime, OpenWebUI runtime bridge,
dependencies, tool execution, or production authority. OpenAPI path count
remains `74`. M27 remains planned/provisional.

Developer verification:

```bash
make doctor
make test
make verify
make frontend-check
```

Use `.venv/bin/python`, not bare `python`, for repo verification commands.
