# Phase 03: Live Local Setup And Packaging

Coverage: H05 and L02.

Objective: replace the dry-run-only Setup Assistant posture with the smallest
real, safe, macOS-first setup lifecycle that installs, launches, health-checks,
repairs, stops, and rolls back the local UAA Control Center/Core package.

## Fresh Delta And Authority Gate

Re-inventory current `main`, Setup/Packaging branches, macOS app work, signing
work, and authority-graduation evidence. This pack is not authority. Before the
first installation, process launch, service mutation, file mutation outside an
already authorized local workspace, or credential write, require an accepted
exact setup/packaging milestone with current PolicyEngine,
LocalApprovalAuthority, AuthorityLease, scope, idempotency, rollback,
safe-disable, and receipt proof.

If that exact authority is absent, complete all independent code and tests, mark
the live activation item `blocked_by_authority`, continue later phases, and do
not call Setup complete. Do not substitute a generated `.app` proof or mocked
installer response.

## Required Outcomes

1. Produce a real local `.app` or accepted native wrapper that launches the
   local Control Center and connects only to the governed Python Core.
2. Implement explicit setup states: prerequisites, ready to install,
   approval-required, installing, installed, starting, healthy, degraded,
   repairable, stopping, rollback-required, rolled back, and failed.
3. Implement one exact local install lane and its inverse. It must be repeatable,
   idempotent, safe on partial failure, and constrained to declared artifacts.
4. Add a real health/readiness check that verifies the process identity, API
   manifest/version, local bind address, Control Center compatibility, and
   absence of forbidden broad authority.
5. Implement safe repair/retry and rollback after interruption at every
   externally visible state.
6. Add human-readable CLI commands for plan, status, install, verify, repair,
   stop, rollback, and receipts. API and Control Center must use the same Python
   service.
7. Do not capture credentials or install models/providers/connectors as part of
   the setup lane unless separately accepted exact milestones already exist.
8. Keep signing, notarization, public installer, auto-update, launch-agent, and
   public distribution claims at their proven states. A local launch proof does
   not prove distribution readiness.

## End-To-End Acceptance

On a supported local macOS environment:

1. start from no installed test artifact;
2. inspect and approve the exact plan;
3. install the local app;
4. launch and verify API/manifest/version readiness;
5. open the real Control Center and complete a read-only first-loop check;
6. repeat install/start to prove idempotency;
7. interrupt one controlled install in a test environment and recover safely;
8. stop and rollback;
9. prove no managed artifacts or processes remain beyond declared retained
   receipts; and
10. inspect the same receipts through CLI, API, Evidence, and Setup UI.

Use redacted safe refs in durable evidence. Do not persist raw paths, process
arguments, environment contents, logs, or account material.

## Verification

Run focused setup tests, app build/launch checks, macOS lifecycle tests,
OpenAPI/API manifest checks, Control Center tests, Foundation Gate, and a
rendered setup walkthrough. Record unsupported platforms honestly.

Commit message:

```text
feat(setup): deliver approval-bound local macOS lifecycle
```
