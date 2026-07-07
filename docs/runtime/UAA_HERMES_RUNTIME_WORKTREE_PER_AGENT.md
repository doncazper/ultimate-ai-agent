# UAA Hermes Runtime Worktree Per Agent

Phase 33 adds backend-owned worktree-per-agent posture for the Hermes Runtime
Adoption program. It is read/proposal only, not Git worktree creation, branch
mutation, file mutation, commit, or push authority.

## Full-Strength

Coding agents work in isolated branches and worktrees with checkpoint and
rollback proof. A mature lane would let UAA supervise exact per-agent
workspaces, branch names, checkpoints, Git receipts, rollback refs, and review
state while keeping every mutation approval-bound and auditable.

## Repo-Safe

The current implementation is read/proposal only:

- Python Agent Core owns `RuntimeWorktreePerAgentReadModel`.
- API route: `GET /api/runtime/worktree-per-agent`.
- CLI inspection: `scripts/dev/uaa_runtime.py inspect-worktree-per-agent`.
- Each lane is now bound to an AuthorityState capability mapping and evaluated
  against the active AuthorityLease set:
  `lane-ref:runtime-worktree-implementer-proposal`,
  `lane-ref:runtime-worktree-reviewer-compare`, and
  `lane-ref:runtime-worktree-verifier-proof`.
- Control Center renders lane refs, workspace scope refs, branch proposal refs,
  branch name refs, worktree refs, checkpoint plans, Git receipt plans,
  rollback plans, proof refs, AuthorityState decision refs/outcomes, and
  blocked authority refs.
- Mock fallback is visibly non-authoritative and keeps the same blocked Git and
  file mutation posture.
- No branch, worktree, file, commit, push, shell, provider, or raw-path action
  is performed.

## Blocked / Needs Authority

These remain blocked:

- Git worktree create/delete
- branch mutation
- file writes
- commits
- pushes
- shell execution
- provider calls
- Control Center minting authority
- raw path, raw file-content, or raw Git-output persistence

## Exact Promotion Path

Promotion requires all of the following before any real per-agent worktree lane
can run:

- exact workspace grant
- branch naming policy
- checkpoint plan and receipt
- Git receipt
- rollback plan
- approval binding
- idempotency
- safe-disable posture
- CLI/API/Core parity
- focused tests and verifier coverage
- route side-effect classification
- Control Center labels that distinguish proposal, review-ready, blocked, and
  executable states

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_worktree_per_agent.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_33.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
npm run test --prefix apps/control-center -- --run src/App.test.tsx src/routes.test.ts src/api/client.summaryEndpoints.test.ts
```

The verifier fails if the route is missing, classification drifts, CLI parity is
lost, or any Git worktree create/delete, branch mutation, file write, commit,
push, shell execution, provider call, raw path persistence, or Control Center
authority flag is enabled.
