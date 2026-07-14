# Control Center Capability Surface Coverage

The capability surface also renders the backend-owned capability maturity
evidence gate. Each of the 16 comparison components shows its baseline, exact
one-point target capped at ten, and empirical verification posture. The normal
read-only route never runs tests and therefore retains the baseline until the
bounded repo-local evaluator proves runtime, test, recovery/replay, evidence,
and operator-surface requirements. Score visibility never grants authority.

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

This is not a new roadmap, product claim, or authority grant. It adds one
read-only backend route and one read-only Control Center view for bounded
capability coverage, but it does not add action execution, approval grants,
provider/model calls, web fetching, browser automation, connector writes,
shell/subprocess execution, memory writes, context injection, public
distribution, public beta, production readiness, or production authority.

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

`GET /control-center/capabilities/surface` exposes a bounded Python/API-owned
read model over the human capability manifest, generated source-truth overlay,
and live API manifest metadata. `scripts/dev/uaa_capability_surface.py inspect`
prints the same safe read model for CLI parity.

The `/capabilities` Control Center route renders operator-readable counts,
status groups, source-truth posture, route refs, CLI refs, missing reasons, and
blocked authority refs. It is not a raw JSON dump and does not expose action
execution, approval grants, provider/model calls, connector writes, browser
automation, shell/subprocess execution, memory writes, context injection,
public beta, production readiness, or production authority.

Visual proof remains blocked until a later scoped visual-regression lane
captures redacted desktop/mobile baselines for `/capabilities`.

## Rollback

Rollback is to remove this document, remove
`docs/control_center/capability_surface_manifest.json`, remove
`docs/control_center/capability_surface_generated_overlay.json`, remove
`docs/schemas/control_center_capability_surface.schema.json`, remove the
generator, focused verifier/test files, remove
`GET /control-center/capabilities/surface`, remove
`scripts/dev/uaa_capability_surface.py`, remove the `/capabilities` route, and
remove documentation cross-links. No runtime state, authority, migration, or
persistent user data is changed.
