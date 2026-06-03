Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.21.2

Status: Current master plan for v0.21.2.

v0.21.2 is a developer environment command normalization patch. It keeps the accepted v0.21.1 product/runtime/API baseline intact while making repo verification commands deterministic for Codex and local non-interactive shells.

Implemented scope:

- `scripts/verify_dev_environment.py` checks `.venv/bin/python`, package importability, pytest, Ruff, Control Center package metadata, and npm availability without modifying files.
- `Makefile` provides repo-local `doctor`, `test`, `verify`, `frontend-check`, `openapi`, and `ruff` targets.
- docs tell contributors to prefer `.venv/bin/python` or Makefile targets instead of bare `python`.
- release/version docs move the accepted baseline to v0.21.2.

Developer command baseline:

```text
make doctor
make test
make verify
make frontend-check
```

Architecture boundary:

- Python Agent Core remains the brain.
- OpenAPI path count remains unchanged at `74`.
- v0.21.2 adds no backend route and changes no application behavior.
- no global Python alias is required.
- no dependency is added or installed by the verifier.

Not implemented in v0.21.2:

- M18 Local Runtime Status + Manual Smoke Control Surface.
- runtime features, frontend features, backend API routes, OpenAPI path changes, dependencies, global tool installs, or application behavior changes.
- runtime execution, model/provider calls, network calls, remote execution, mobile/native/browser/computer-use functionality, plugin enablement, or production capability.
