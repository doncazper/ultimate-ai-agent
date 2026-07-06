# UAA Hermes Runtime Skill Bundle Proposals

Status: Hermes Runtime Adoption Phase 15 repo-safe proposal posture

## Full-Strength Version

UAA can support reusable task profiles that combine reviewed skills, context
packs, toolsets, authority profiles, proof expectations, and verification
requirements. A future operator can inspect a bundle, understand what it would
load or call, approve the exact lane, run it with receipts, and safely disable
or roll it back when applicable.

## Repo-Safe Version

Phase 15 adds a backend-owned Skill Bundle Proposal Posture read model inside
the inspectable extension catalog and CLI inspection:

- `skill_bundle_proposal_posture` in `GET /extensions/catalog`
- `scripts/dev/uaa_extensions.py inspect-skill-bundles`
- proposal refs for reusable task-profile bundles
- constituent skill refs
- context-pack refs
- toolset refs
- authority-profile refs
- verifier and proof refs
- blocked authority refs
- Control Center Plugin Governance summary fields

This is metadata/proposal UI only. Bundles do not install, import, enable,
inject context, execute tools, call providers/models, write connectors, run
shell commands, use browser automation, or claim production authority.

## Blocked / Needs Authority

- activating bundles
- enabling constituent skills
- hidden or automatic skill instruction loading
- context injection into runtime turns
- tool execution from bundle membership
- plugin or skill runtime import
- provider/model calls
- connector writes
- shell/subprocess execution
- browser automation
- production authority

## Exact Promotion Path

Future promotion requires bundle review, constituent skill trust records,
toolset mapping, exact `LocalApprovalAuthority` scope, authority-profile
binding, approval envelope, safe-disable posture, rollback or rollback-readiness
posture, idempotency, redaction, receipts, proof refs, CLI/API/Core parity, and
focused tests that prove only the reviewed bundle lane can activate.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_skill_bundles.py tests/test_inspectable_extension_catalog.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_15.py
```
