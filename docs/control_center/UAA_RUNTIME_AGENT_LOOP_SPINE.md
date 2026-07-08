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

## High-Maturity Agent Spine

The same API payload now includes `high_maturity_spine_readiness`, a
backend-owned High-Maturity Agent Spine coverage map for W1-W13:

- Contract:
  `contract-ref:high-maturity-agent-spine-coverage:v1`
- Route:
  `GET /control-center/agent-loop/thread#high_maturity_spine_readiness`
- CLI:
  `scripts/dev/uaa_founder_loop.py inspect-high-maturity-spine`
- Control Center:
  the Agent Loop Thread panel renders the W1-W13 rows, score projection,
  evidence refs, test refs, gaps, and next safe action without raw JSON as the
  primary operator workflow.
- Action/tool lane posture:
  `high_maturity_spine_readiness.action_tool_lane_posture` projects the
  Python-owned action/tool/code catalog into preview-only tools, exact local
  mutation, exact approval-bound RuntimeGateway utility lanes, proposal-only
  code workflows, and blocked broad capabilities with receipt, evidence, proof,
  route, CLI, and blocked-authority refs.
- Durable orchestration posture:
  `high_maturity_spine_readiness.durable_orchestration_posture` maps
  append-first durable run records, canonical lifecycle states, run
  observability, approval waits, retry/recovery diagnostics,
  cancellation/dead-letter state, staged checkpoints, one exact approved
  runtime-command step, and blocked autonomous workers/schedulers to safe refs,
  tests, receipts, and no-new-authority invariants.
- External information handling:
  `high_maturity_spine_readiness.external_information_handling` maps trusted
  local evidence, operator-supplied external metadata, the existing
  Browser/read AuthorityLease-gated WebAccessGateway HTTPS GET preview lane,
  untrusted-content quarantine, browser observe, browser action, provider
  search/scrape adapter posture, and external-content authority isolation to
  safe refs, blocked refs, tests, and no-new-authority invariants.
- Model/provider management:
  `high_maturity_spine_readiness.model_provider_management` maps the read-only
  provider control plane, delegated runtime model catalog, model slots,
  role/provider evidence, provider research posture, cost hooks, router traces,
  and local runtime lifecycle posture without provider SDK calls, runtime model
  calls, model-output authority, or raw provider payload persistence.
- System eval coverage:
  `high_maturity_spine_readiness.system_eval_coverage` maps route choice,
  ambiguity handling, task decomposition, approval-needed detection, memory
  citation selection, blocked-state explanation, and evidence completeness to
  existing fixture-backed tests, evidence refs, and no-authority invariants.
  This is strong system-level coverage, not a raw model intelligence benchmark.

This is a deterministic read model over existing UAA code, API, CLI, docs,
tests, and verifier posture. It is not a benchmark of raw model intelligence.
It does not execute tools, run provider/model calls, fetch web data, browse,
write memory, inject context, import plugins, dispatch connectors, run shell
commands, or grant production authority.

The coverage rows are intentionally product-operational:

- W1 product loop
- W2 durable planning and orchestration
- W3 memory retrieval and lifecycle
- W4 operator cockpit UX
- W5 exact action/tool lanes
- W6 Code Mode discipline
- W7 web and external evidence
- W8 model/provider management
- W9 signed evidence receipts
- W10 extensibility/catalog maturity
- W11 end-to-end Founder Loop
- W12 system-level agent evals
- W13 release/product truth alignment

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
