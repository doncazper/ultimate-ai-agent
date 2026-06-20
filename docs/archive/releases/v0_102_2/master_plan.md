# v0.102.2 Master Plan

Release: v0.102.2 - Founder Command Center strategy-spine hardening baseline.

The active product and package baseline is v0.102.2 / 0.102.2. This is a
docs-only hardening slice for the Founder Command Center / macOS-of-agents
strategy spine. It aligns current product direction without adding runtime
authority.

## Goals

- Make Founder Command Center the explicit product wedge while preserving the
  contract-first, disabled-by-default UAA posture.
- Treat UAA-P1-011 as the accepted readable-loop baseline and point future work
  at local Control Center macOS-first Setup Assistant hardening, first product
  loop readability, Action Inbox / approval envelope UX, Morning Briefing
  skeleton, and read-only email/calendar integration contracts later.
- Preserve planning-only permission vocabulary without creating approval refs,
  standing grants, enabled controls, background sessions, connector writes, or
  kill-switch mutations.
- Restore memory direction as reviewed recall layers: profile, project,
  relationship, episodic, business, and semantic-local knowledge.
- Restore first-party integration direction as contract planning only, including
  future contacts lookup contract planning, task creation proposals, governed
  article/evidence capture, GitHub read-only project status, and CRM-lite local
  lead/follow-up store.
- Update active version, baseline, release packet, and verifier currentness
  metadata.

## Non-Goals

- No native macOS app implementation, signed packaging, signed installer,
  notarization, public release, public beta, public distribution, or production
  readiness claim.
- No backend route, Control Center control, connector runtime, account auth,
  connector write, contacts read/search/lookup runtime, browser automation,
  plugin runtime import, shell/subprocess execution, memory write, context
  injection, model/provider authority, raw prompt export, raw provider payload
  export, credential/cookie handling, or broad autonomy.

## Verification

- `.venv/bin/python scripts/release/check_version_truth.py`
- `.venv/bin/python scripts/verify_current_baseline.py --skip-static-scans`
- `PYTHONPATH=src .venv/bin/python scripts/verify_documentation_integrity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- `PYTHONPATH=src .venv/bin/python scripts/run_foundation_gate.py --command-mode report-only`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_documentation_integrity_verifier.py`
