# FCC-POLISH-001 Native And Apple-Grade UX Layer

Status: Implemented as a verified Control Center polish baseline over existing
backend-owned state and checked-in visual regression coverage. No native
runtime, installer, notification, or OS authority is added.
Baseline: v0.104.0 / 0.104.0.

## Current Truth

Polish follows proof. The current slice verifies the first-party Control
Center shell as the Founder Command Center operator surface while keeping
route refs, authority boundaries, blocked states, mock/degraded posture, setup
dry-run posture, and evidence/receipt refs inspectable.

The visual baseline is recorded in:

```text
docs/control_center/visual_regression_manifest.json
apps/control-center/tests/visual/control-center.visual.spec.ts
apps/control-center/tests/visual/__snapshots__/
```

The active visual gate covers the canonical macOS desktop baselines for
Overview, Start Here, Today, Source Inbox, Actions, Plans, Proof, Trust, Memory,
Evidence, Settings, and Setup, plus route-state scenarios for loading, empty,
error, blocked, partial, and success. Older mobile snapshot refs remain frozen
as inactive porting placeholders; they are not an active acceptance surface and
must not be refreshed until mobile porting is separately authorized. All
baselines are redacted test fixtures, not private screenshots and not
implementation evidence for backend workflows by themselves.

## Setup And Blocked-State Posture

`/setup` remains a dry-run macOS-first setup preview. It can show local
prerequisite refs, recommendation-only model choices, dry-run approval
envelopes, receipt plans, rollback refs, optional bridge previews, and blocked
capabilities. It cannot install, start, load, launch, download, sign, notarize,
notify, schedule, mutate the OS, or create native authority.

Normal daily use should feel calmer and more professional through clearer
visual hierarchy, stable panel density, visible top-level posture, readable
blocked states, and inspectable route/authority details. That polish does not
change product authority.

## Safety Boundary

This lane adds no signed/public distribution, no installer mutation, no
LaunchAgent install/load/start, no notification delivery, no background
polling, no native OS authority, no shell/subprocess execution, no
provider/model authority, no connector writes, no hidden authority, no public
beta, no production-readiness claim, and no production authority.

Future native SwiftUI, packaging, signing, notarization, notification, or
installer work requires a separate exact scoped milestone with evidence,
rollback/safe-disable posture, and verifiers.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_polish_001_native_apple_grade_ux_layer.py -q
.venv/bin/python scripts/verify_fcc_polish_001_native_apple_grade_ux_layer.py
npm --prefix apps/control-center run visual:check
make frontend-check
.venv/bin/python scripts/verify_control_center_frontend.py
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py --root .
git diff --check
```
