# Ultimate AI Agent

Status: active
Current through: v0.29.5
Purpose: Root entrypoint for the current contract-first Python Agent Core workspace.

The active project baseline is v0.29.5. This release accepts the pushed
documentation organization policy polish after v0.29.4, keeps the repository
root current, preserves historical release packets under `docs/archive/`, and
keeps active verifiers independent from moved root release artifacts.

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
docs/archive/releases/v0_29_5/README_IMPORT.md
docs/archive/releases/v0_29_5/master_plan.md
docs/release_notes/v0_29_5.md
docs/implementation/foundation_gate_implementation_plan_v0_29_5.md
docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md
```

Core rule:

> Python Agent Core is the brain. OpenWebUI is the preferred conversational web
> shell, not the agent brain. CCC means Control Center Clients and is the
> governance/control client family. Model output is not truth authority. Memory
> is recall, not authority.

v0.29.5 is documentation policy polish only. It removes duplicated wording from
the self-maintaining documentation organization policy and keeps v0.29.4 as the
archive reference repair release and v0.29.2 as the accepted pre-M26 security
hardening baseline.

It adds no M26 Grounded Recall Router, Context Pack Builder, backend routes,
frontend features, runtime/model/provider calls, memory writes, tool execution,
dependencies, or production authority. OpenAPI path count remains `74`. M26
remains planned/provisional.

Developer verification:

```bash
make doctor
make test
make verify
make frontend-check
```

Use `.venv/bin/python`, not bare `python`, for repo verification commands.
