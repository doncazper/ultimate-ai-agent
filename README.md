# Ultimate AI Agent

Status: active
Current through: v0.30.0
Purpose: Root entrypoint for the current contract-first Python Agent Core workspace.

The active project baseline is v0.30.0. This release implements M26: Grounded
Recall Router + Evidence-Linked Context Pack Builder as deterministic local
contracts over provided safe candidates only.

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
docs/archive/releases/v0_30_0/README_IMPORT.md
docs/archive/releases/v0_30_0/master_plan.md
docs/release_notes/v0_30_0.md
docs/implementation/foundation_gate_implementation_plan_v0_30_0.md
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

v0.30.0 adds local recall/context-pack planning contracts only. It adds no
backend routes, frontend features, vector search, embeddings, semantic search,
RAG ingestion, web search, external retrieval, source crawling, arbitrary file
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
