# v0.104.0 Master Plan

Release: v0.104.0 - Founder Command Center functioning-units and
truth-binding hardening baseline.

The active product and package baseline is v0.104.0 / 0.104.0. This is a
currentness and release-truth consolidation slice for backend-owned Control
Center readability, operational maturity verifier coverage, Memory context-pack
proposal visibility, Action Inbox fallback truth-binding, and portfolio status
docs. It aligns current product direction without adding production authority.

## Goals

- Promote the accepted baseline from v0.103.0 to v0.104.0.
- Keep `checkpoint-m169` as the latest accepted repository checkpoint.
- Keep completed FCC-V1-000 through FCC-V1-007 truth consistent across README,
  VERSION, roadmap, board, Control Center, product-language, and release-truth
  docs.
- Make mock/degraded Control Center shell and Action Inbox data visibly
  non-authoritative when backend read models are unavailable.
- Require operational maturity refs and probes for Memory context-pack
  readiness, Local Models read-only status, source readiness, Action Inbox
  envelope/receipt visibility, and Evidence Timeline blocked authority flags.

## Non-Goals

- No production authority, public release, public beta, public distribution,
  signed installer readiness, hosted deployment, runtime model/provider calls,
  unrestricted browser or network authority, shell/subprocess execution,
  connector writes, live email/calendar runtime, account auth, plugin runtime
  import, mobile control, memory writes, context injection, generic execution,
  or raw private-content persistence.

## Verification

- `.venv/bin/python scripts/verify_current_baseline.py --skip-static-scans`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_founder_loop_storage.py`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_operational_maturity_manifest.py`
- `make frontend-check`
