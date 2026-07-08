# UAA Runtime Agent Loop Spine

Status: Phase 02 implemented as backend-owned read model only.

## Full-Strength Version

UAA should feel like one operator agent loop: user input, intent, plan,
proposed action, approval posture, execution result, evidence, proof, memory
review, and next safe decision stay connected across Chat, Today, Plans,
Action Inbox, Proof, Evidence, Memory, and Trust.

## Repo-Safe Version

Phase 02 adds Python Core Agent Loop Thread contract
`contract-ref:runtime-agent-loop-thread:v1`:

- Core builder:
  `src/ultimate_ai_agent/core/control_center/agent_loop.py`
- API:
  `GET /control-center/agent-loop/thread`
- CLI:
  `scripts/dev/uaa_founder_loop.py inspect-agent-loop`
- Control Center:
  Today renders the Agent Loop Thread as a non-executing product spine.

The read model composes existing safe refs from Today, Action Inbox, Evidence,
Proof, Memory Review, and Trust. It uses bounded summaries and safe refs only.
It does not persist raw request content, raw response content, provider payloads,
logs, local paths, credentials, account material, or private content.

## Blocked / Needs Authority

These remain blocked:

- runtime model calls
- provider SDK calls
- live web fetching
- browser automation
- connector writes
- unrestricted shell/subprocess execution
- plugin runtime import
- memory-write authority beyond existing exact reviewed lanes
- background autonomy
- production authority
- public release or public beta claims

## Exact Promotion Path

Any future promotion must add exact AuthorityLease scope, approval binding,
idempotency, receipt/proof refs, rollback or safe-disable posture, redaction,
CLI/API/Core parity, route classification, focused tests, and Control Center
truth labels.
The Agent Loop Thread may then reference receipts from AuthorityLease-gated
capabilities, but it must not itself mint authority.
