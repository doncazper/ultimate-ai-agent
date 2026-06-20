# Foundation Gate Implementation Plan v0.102.0

v0.102.0 keeps Foundation Gate coverage aligned with the corrected pre-1.0
Operator Runtime Excellence baseline.

## Required Currentness Checks

- Active docs must preserve the current v0.102.0 / 0.102.0 baseline.
- Active docs must preserve checkpoint-m168 as the latest accepted repository
  checkpoint.
- Active docs must preserve checkpoint-m166 and checkpoint-m167 as accepted
  local model lane checkpoints.
- Product release-truth, public security posture, API docs, Control Center
  route/status docs, release evidence docs, and version metadata must agree on
  the corrected baseline.
- Historical v1.x and v2.0.0 tags must remain immutable audit records and must
  not be treated as current release authority.

## Required Commands

```bash
.venv/bin/python scripts/release/check_version_truth.py
.venv/bin/python scripts/verify_current_baseline.py
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_all.py
.venv/bin/python scripts/run_foundation_gate.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest
```

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must
have a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before any future enablement.

## Denials

This plan does not add production authority, public release, public beta,
external distribution, dependency changes, backend route authority, Control
Center authority, model/provider calls, shell/subprocess execution,
unrestricted network/browser automation, plugin execution, mobile sensor
runtime, memory write, context injection, raw prompt export, raw provider
payload export, tag creation, tag movement, tag deletion, remote repair, or
history rewrite.
