# Control Center Capability Surface Coverage

Status: active capability-first coverage seed, no new runtime authority.

This document introduces a capability-first companion to the existing Control
Center route-status and release-surface manifests. The machine-checkable source
is:

```text
docs/control_center/capability_surface_manifest.json
```

Generated/source-owned route truth is maintained as a companion overlay:

```text
docs/control_center/capability_surface_generated_overlay.json
```

Generate or check it with:

```bash
PYTHONPATH=src .venv/bin/python scripts/generate_control_center_capability_surface.py --check
PYTHONPATH=src .venv/bin/python scripts/generate_control_center_capability_surface.py --write
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

The human manifest owns product judgment fields such as labels, grouping,
owners, authority posture, status, missing reasons, and evidence refs. The
generated overlay owns source-derived facts: live API operation IDs,
side-effect classes, route classifications, approval posture, release-surface
route labels/statuses, and route-status visible action posture. This keeps
source drift machine-checkable without silently rewriting human annotations.

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
PYTHONPATH=src .venv/bin/python scripts/generate_control_center_capability_surface.py --check
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_capability_surface.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_capability_surface_manifest.py
```

The capability-surface verifier also runs from the broader static verifier
stack through `scripts/verification/run_all_legacy.py`, adjacent to the Control
Center release-surface scan.

## Control Center View Posture

A dedicated Control Center capability-surface UI route is intentionally not
added in this pass. The source truth is now available through the human
manifest, generated overlay, verifier, and broader verifier stack, but adding a
visible route would require coordinated changes to the frontend route registry,
release-surface manifest, route-status manifest, typed client, mock data, and
frontend tests. Several of those frontend files already carry unrelated
uncommitted work in the current tree, so this pass stops at verifier-backed
Python/source truth instead of staging a mixed UI commit. The next safe UI lane
should add a bounded read-only route backed by the generated overlay and render
operator-readable capability rows, not raw JSON.

## Rollback

Rollback is to remove this document, remove
`docs/control_center/capability_surface_manifest.json`, remove
`docs/control_center/capability_surface_generated_overlay.json`, remove
`docs/schemas/control_center_capability_surface.schema.json`, remove the
generator, focused verifier/test files, and remove documentation cross-links.
No runtime state, route, authority, migration, or persistent user data is
changed.
