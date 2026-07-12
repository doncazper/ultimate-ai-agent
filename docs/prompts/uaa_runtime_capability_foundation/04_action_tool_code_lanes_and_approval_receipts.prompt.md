# Phase 04: Useful Exact Tool And Code Lanes

Goal: promote only individually proven local capabilities through current
request-scoped AuthorityLease evaluation.

## Required Work

1. Inventory existing tool, action, runtime gateway, repository, code-workbench,
   sandbox, approval, dispatcher, CLI/API/UI, receipt, and redaction contracts.
2. Prefer exact low-risk usefulness:
   - bounded repository filesystem metadata;
   - bounded read-only repository inspection;
   - allowlisted repository verification commands;
   - deterministic sealed-sandbox calculation only if a real sandbox exists;
   - proposal-only code diff and validation plans; and
   - exact code apply only with separate approval, lease, target, idempotency,
     rollback, and receipt proof.
3. Every catalog entry distinguishes declaration, runtime availability, and
   eligibility for immediate request-scoped evaluation. Inspectable never
   means callable and no global `authorized` or `callable` state is permitted.
4. Every executable lane uses MissionOrchestrator -> AuthorityMissionRunner ->
   AuthorityDispatcher and independently re-evaluates every authority gate at
   the locked pre-start boundary.
5. Bind typed inputs/outputs, exact target/resource, bounded execution,
   idempotency, budget, safe-disable, rollback readiness, hashes, redaction,
   receipts, and blocked reasons.
6. Record terminal `blocked`, `unsupported`, `adapter required`,
   `configuration required`, `external facility required`, or
   `deferred by authority policy` states; do not create recursive prompts.

## Sandbox Proof Floor

A callable sandbox must prove no network, host filesystem access or mutation,
host environment/secret access, package installation, or subprocess escape.
It must enforce CPU, time, memory, and output limits; bounded redacted
stdout/stderr; code/result hashes; kill switch; safe-disable; and receipts. If
that proof is absent, CodeAct-style execution remains blocked/readiness-only.

## Shell And Development Boundary

Broad host shell remains denied. Repository verification commands run by
developers during this program grant no UAA runtime shell authority. Arbitrary
commands, shell expansion, caller-controlled cwd/environment, package install,
home traversal, and destructive operations remain denied.

## Required Proofs

- exact read-only metadata and inspection boundaries;
- allowlist rejection for command, cwd, env, target, and argument changes;
- approval/lease expiry or revocation produces zero starts;
- idempotent unchanged replay and concurrent-start exclusion;
- sandbox escape and secret/network/host denial, or truthful blocked posture;
- bounded/redacted output and receipt/hash validation;
- code proposal cannot execute; and
- kill switch and safe-disable block new starts.

## Exit

Only proven exact lanes are executable and operator-visible. Broad shell,
browser actions, connector writes, arbitrary plugins/MCP, payments, outbound
messages, production deployment, and fake sandboxing remain denied.
