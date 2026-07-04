# Phase 07: Review, Fix, Harden, And Release Truth

Goal: perform repeated adversarial review and hardening before tagging the
governed runtime pilot.

This phase is not optional. The pilot promotes real runtime authority, so it
must receive deeper review than a docs or UI-only lane.

## Required Review Passes

Run at least three full passes. Fix issues and repeat any failed pass.

### Pass 1: Security And Authority

Review:

- runtime profile default and downgrade behavior;
- model endpoint allowlist;
- command allowlist and argv-only execution;
- cwd and env restrictions;
- approval scope validation;
- idempotency and replay;
- safe-disable;
- redaction;
- evidence persistence;
- API auth;
- route side-effect classes;
- OpenAPI and manifest truth;
- no browser/web/connector/plugin/remote authority.

### Pass 2: Product And UX

Review:

- no raw JSON primary UX for operator-critical flows;
- implemented/partial/planned/blocked labels;
- Chat, Action Inbox, Evidence, Runtime, Settings flow clarity;
- model output treated as proposal, not authority;
- command execution explained before approval;
- failure states clear and actionable;
- no public beta, production, broad autonomy, or unrestricted runtime claims.

### Pass 3: Verification And Release

Review:

- focused tests for every adapter and route;
- manifest/OpenAPI checks;
- docs integrity;
- frontend checks;
- Foundation Gate report-only;
- redaction leak tests;
- release truth packet;
- current branch, commit, status;
- tag discipline.

## Required Final Checks

Run all applicable checks:

```bash
git diff --check
make doctor
make test
make verify
make frontend-check
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

If the repo cannot run the full suite, record exact blockers. Do not claim
success for blocked checks.

## Release Truth Updates

Update the smallest relevant docs and boards:

- `README.md`
- `VERSION.md`
- `docs/README.md`
- `docs/DOCUMENTATION_INDEX.md`
- `docs/kanban/current_board.md`
- `docs/kanban/founder_command_center_board.md`
- relevant strategy or control-center truth docs

Only update files needed to reflect the implemented pilot. Do not create a
competing roadmap.

## Finalization

When green:

1. Commit final hardening changes.
2. Push the branch.
3. Merge to `main` with a merge commit.
4. Pull `main`.
5. Create an annotated milestone tag only if release truth and verification
   support it.
6. Push `main` and the new tag.

Never force-push. Never mutate existing tags.

## Final Report

Include:

- authority promoted;
- authority still blocked;
- hardening faults found and fixed;
- tests/verifiers run;
- blocked/skipped checks;
- release truth files updated;
- baseline tag;
- milestone tag;
- merge commits;
- remaining risks;
- recommended next steps.

