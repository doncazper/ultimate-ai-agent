# README Import v0.21.2

Status: Current import README for v0.21.2.

Start from:

- `README.md`.
- `VERSION.md`.
- `ultimate_ai_agent_master_plan_v0_21_2.md`.
- `docs/DOCUMENTATION_INDEX.md`.
- `docs/canonical/09_roadmap.md`.
- `docs/canonical/CANONICAL_DOC_MAP.md`.
- `docs/testing/test_strategy_v0.md`.
- `docs/maintenance/documentation_integrity_checklist.md`.
- `docs/release_notes/v0_21_2.md`.

v0.21.2 normalizes developer environment commands only. It adds repo-local Makefile targets and `scripts/verify_dev_environment.py` so Codex and local shells use `.venv/bin/python` instead of depending on a bare `python` binary on PATH.

Preferred verification commands:

```text
make doctor
make test
make verify
make frontend-check
```

Shell aliases are not reliable for Codex and other non-interactive shells. No global Python alias is required.

This release adds no M18 surface, runtime feature, frontend feature, backend API route, dependency, global tool install, application behavior change, runtime/model/provider call, network call, mobile/native/browser/computer-use functionality, plugin enablement, or production capability.
