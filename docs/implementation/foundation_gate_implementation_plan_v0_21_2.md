# Foundation Gate Implementation Plan v0.21.2

Status: Current Foundation Gate implementation plan for v0.21.2.

v0.21.2 does not add a new runtime, API, frontend, or capability gate. It keeps the existing Foundation Gate criteria intact and documents the developer environment command normalization around `.venv/bin/python` and Makefile targets.

## Skill Package Security Rule

v0.21.2 does not change the Skill Package Security Rule. The repo-local developer command wrapper cannot install, enable, configure, or execute plugins or skills.

All skills are untrusted packages by default until a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.

Developer environment checks:

- `scripts/verify_dev_environment.py` checks `.venv/bin/python` exists.
- it prints the venv Python version.
- it verifies `ultimate_ai_agent`, pytest, and Ruff are importable through the venv Python.
- it checks `apps/control-center/package.json` exists when the Control Center app exists.
- it warns when npm is unavailable without modifying files.
- it prints remediation using `python3 -m venv .venv` and `.venv/bin/python -m pip install -e ".[dev]"`.

Repo-local command targets:

- `make doctor`
- `make test`
- `make verify`
- `make frontend-check`
- `make openapi`
- `make ruff`

This patch adds no M18, runtime execution, frontend feature, backend route, OpenAPI path change, model/provider call, network call, remote dispatch, mobile sensor access, native build workflow, browser automation, Computer Use automation, plugin enablement, dependency, global tool install, application behavior change, or production capability.
