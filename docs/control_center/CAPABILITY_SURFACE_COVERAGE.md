# Control Center Capability Surface Coverage

Status: active capability-first coverage seed, no new runtime authority.

This document introduces a capability-first companion to the existing Control
Center route-status and release-surface manifests. The machine-checkable source
is:

```text
docs/control_center/capability_surface_manifest.json
```

It answers a different question from the route manifests:

```text
Given an operator-facing capability, where is it exposed in Python core/API,
CLI or repo-local script inspection, Control Center UI, and visible controls?
```

This is not a new roadmap, product claim, or authority grant. It does not add
backend routes, frontend controls, provider/model calls, web fetching, browser
automation, connector writes, shell/subprocess execution, memory writes,
context injection, public distribution, public beta, production readiness, or
production authority.

## Scope

The manifest covers operator-facing product capabilities only. Internal helper
functions, private implementation details, and library-level utilities are out
of scope unless they become a user/operator-facing workflow.

Each row records:

- `capability_id`
- `python_core_owner`
- `api_routes`
- `cli_paths`
- `ui_routes`
- `control_action_ids`
- `authority_posture`
- `status`
- `missing_reason`
- `tests_evidence_refs`

## Status Values

| Status | Meaning |
|---|---|
| `ui_api_cli_wired` | The exact current capability has Python/API, CLI or repo-local script inspection, and UI/control coverage. This is not public release or production readiness. |
| `partial_surface_coverage` | Some surfaces exist, but a CLI path, backend read model, UI binding, or authority lane remains missing or intentionally limited. |
| `backend_or_cli_only` | The capability is intentionally inspectable outside the main UI or does not yet have a Control Center surface. |
| `mock_or_static_only` | The capability is static, design-only, mock-only, or manual-review-only. |
| `blocked_intentionally` | The capability class is intentionally unavailable or future-scoped until a later exact authority milestone. |

`missing_reason` must be `none` only for `ui_api_cli_wired` rows. Every other
status must explain the gap or intentional limitation.

## Relationship To Existing Truth

The capability manifest references, rather than replaces:

- `docs/control_center/route_status_manifest.json`
- `docs/control_center/release_surface_manifest.json`
- `docs/control_center/UI_WIRING_REPORT.md`
- `/api/manifest`

The verifier requires every visible Control Center route and every visible
action id from the route-status manifest to be covered by at least one
capability row. API routes in capability rows must match the live API manifest
operation ids.

## Verification

Required focused checks:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_capability_surface.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_capability_surface_manifest.py
```

## Rollback

Rollback is to remove this document, remove
`docs/control_center/capability_surface_manifest.json`, remove
`docs/schemas/control_center_capability_surface.schema.json`, remove the
focused verifier/test files, and remove documentation cross-links. No runtime
state, route, authority, migration, or persistent user data is changed.
