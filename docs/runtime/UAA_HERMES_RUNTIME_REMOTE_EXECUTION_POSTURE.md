# UAA Hermes Runtime Remote Execution Posture

Status: Phase 43 repo-safe Python Core read model.
Route: `GET /api/runtime/remote-execution-posture`
CLI: `scripts/dev/uaa_runtime.py inspect-remote-execution-posture`  
Core: `src/ultimate_ai_agent/core/runtime_gateway/remote_execution_posture.py`

## Full-Strength

UAA should eventually supervise local, container, SSH, cloud sandbox,
serverless, and remote GPU execution backends through exact policy. Mature
lanes would bind workspace boundaries, credential refs, network policy, budget,
receipts, rollback, kill switches, and proof before any remote execution can
start.

## Repo-Safe

The current implementation is a Python Core read model, API route, CLI
inspection path, and Control Center display only. The read model is now bound to
AuthorityState as `lane-ref:runtime-remote-execution-posture-read-model`, which
evaluates as Workspace/read under the active read-only lease. That allowed
decision applies only to inspecting safe backend labels, boundary refs, policy
refs, receipt refs, budget refs, rollback refs, kill-switch refs, proof refs,
blocked refs, and unsupported adapter refs.

- local workspace backend posture
- local container backend posture
- SSH host backend posture
- cloud sandbox backend posture
- serverless worker backend posture
- remote GPU backend posture

Every backend is blocked until authority. The map exposes workspace boundary,
credential policy, network policy, receipt, budget, rollback, kill-switch,
proof, blocked authority, promotion path, and next-safe-action refs. It does
not start processes, create containers, connect over SSH, sync files, touch
remote credentials, control remote processes, or execute remote work.

## AuthorityState

The safe inspection capability is governed by:

- route: `GET /api/runtime/remote-execution-posture`
- CLI: `repo-local-command:uaa-runtime-inspect-remote-execution-posture`
- AuthorityState route: `GET /api/runtime/authority-state`
- AuthorityState CLI: `repo-local-command:uaa-runtime-inspect-authority-state`
- mapping ref: `lane-ref:runtime-remote-execution-posture-read-model`
- domain/capability: `workspace/read`
- required mode: `read_only`

Known authority inside the active lease allows only posture inspection. Local
container, SSH, secure host, cloud sandbox, serverless worker, remote GPU, and
file-sync adapters remain unsupported and do not become executable from this
read model.

## Blocked / Needs Authority

The following remain blocked:

- SSH
- cloud sandboxes
- remote shells
- file sync
- remote secrets
- remote process control
- credential material persistence
- Control Center authority minting

## Exact Authority Path

Execution authority requires later, exact AuthorityLease-governed adapter lanes
for each backend action. Those later lanes must prove:

1. remote policy and backend-specific scope
2. credential refs without raw credential persistence
3. workspace boundary and network policy
4. receipt and cost/budget posture
5. rollback and kill-switch posture
6. CLI/API/Core parity before Control Center initiation
7. route side-effect classification for any future API route
8. verifier coverage for remote paths, logs, hostnames, usernames,
   credentials, tokens, and secret-like material

Planning text and capability-map visibility do not grant remote execution
authority.
