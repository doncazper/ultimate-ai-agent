# Ultimate AI Agent Master Plan v0.9.0

Status: Active project baseline after Milestone M5 (Minimum Lovable Kernel foundation).

## v0.9.0 change log

v0.9.0 implements the first governed end-to-end local/dev kernel slice.

M5 Minimum Lovable Kernel added:

```text
src/ultimate_ai_agent/core/kernel/
tests/test_kernel_request.py
tests/test_kernel_minimum_lovable_happy_path.py
tests/test_kernel_denied_without_consent.py
tests/test_kernel_denied_without_approval.py
tests/test_kernel_denied_without_idempotency.py
tests/test_kernel_secret_blocking.py
tests/test_kernel_rollback.py
tests/test_kernel_event_trace.py
tests/test_kernel_world_state.py
tests/test_kernel_api_routes.py
```

Updated:

```text
README.md
VERSION.md
pyproject.toml
src/ultimate_ai_agent/__init__.py
src/ultimate_ai_agent/api/app.py
scripts/verify_current_baseline.py
scripts/verify_all.py
```

## Rule

M5 connects existing foundation pieces without expanding autonomy. It can perform a local/dev workspace file mutation only through the governed path: Execution Contract, Context Pack, Consent Ledger, Tool Broker, Event Ledger, LocalFileManager proposal/diff/apply, World State, optional source-linked Memory, receipt generation, and rollback support.

The kernel does not call models, providers, network APIs, scanners, shell/subprocess, external tools, browser automation, SDK/A2A runtimes, production databases, pgvector, embeddings, or production secret stores.

## Roadmap pointer

The active roadmap lives at `docs/canonical/09_roadmap.md`. Versioned master plans are historical context. If this master plan and a canonical file disagree, the active canonical file wins.
