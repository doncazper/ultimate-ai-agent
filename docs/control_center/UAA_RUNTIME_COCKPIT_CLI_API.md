# UAA Runtime Cockpit CLI/API Parity

Status: implemented backend-owned read model, no new runtime authority

Contract ref:
`contract-ref:runtime-cockpit-cli-api-parity:v1`

Primary API surface: `GET /control-center/agent-loop/thread`

Primary CLI surface: `scripts/dev/uaa_founder_loop.py inspect-cockpit-parity`

## Full-Strength Version

UAA should feel like one AI cockpit: the operator can see what the agent knows,
what it plans, what it can do, what it cannot do, what it already did, which
approvals are required, and which proof/evidence refs back the current state.
The cockpit should connect Today, Action Inbox, Plans, Evidence, Proof, Memory,
Trust, Runtime, Coding, and Work Board without making the Control Center the
source of workflow truth.

## Repo-Safe Version Implemented

Phase 08 adds an operator decision matrix to the existing backend-owned Agent
Loop thread read model. The matrix gives each cockpit surface:

- operator question;
- capability status;
- backend route ref;
- CLI inspection ref;
- primary safe ref;
- approval posture;
- side-effect class;
- safe action text;
- evidence, proof, receipt, and blocked-state refs;
- mutation-enabled posture.

The same matrix is visible through the API, CLI, and Today cockpit UI. The
matrix is read-only, safe-ref-only, and explicitly states that UI cannot mint
authority.

## Blocked / Needs Authority

This phase does not add runtime model calls, provider SDK calls, live web
fetching, browser automation, connector writes, unrestricted shell/subprocess
execution, plugin runtime import, broad memory writes, background autonomy,
public release claims, production authority, or broad action execution.

Blocked capabilities remain visible in Trust/product truth and in the matrix
blocked refs.

## Exact Promotion Path

Any future cockpit action that mutates state must define a separate exact lane
with:

- Python Core contract ownership;
- route side-effect classification;
- LocalApprovalAuthority exact scope validation;
- idempotency and replay handling;
- receipt/proof/evidence refs;
- rollback or safe-disable posture;
- redaction tests;
- CLI/API/Core parity;
- Control Center presentation-only initiation;
- focused verifier coverage.

## Verification

Focused coverage:

- `tests/test_runtime_agent_loop_spine.py`
- `apps/control-center/src/App.test.tsx`
- `scripts/verify_uaa_runtime_cockpit_cli_api.py`

Required hygiene remains the standard Control Center and product-truth verifier
set. This document is not runtime authority.
