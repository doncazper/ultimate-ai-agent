# UAA Runtime Capability Foundation Action Tool Code Capabilities

Status: Phase 04 implemented as backend-owned catalog/read-model hardening only.

## Full-Strength Version

UAA should make action, tool, runtime, and code-workflow capability posture
legible in one operator surface: what can be inspected, what can propose work,
what exact AuthorityLease capabilities can produce receipts, what needs
approval, what can roll back or safe-disable, and what remains blocked. Future
callable tools, code apply, Git, preview, and expanded command capabilities
must stay exact-scoped and receipt-backed.

## Repo-Safe Version

Phase 04 adds Python Core Action/Tool/Code capability catalog contract
`contract-ref:runtime-action-tool-code-catalog:v1`:

- Core builder:
  `src/ultimate_ai_agent/core/control_center/action_tool_code_catalog.py`
- API embedding:
  `GET /control-center/actions/inbox`
- CLI:
  `scripts/dev/uaa_founder_loop.py inspect-action-tool-code-catalog`
- Control Center:
  Action Inbox renders a read-only catalog panel with preview-only tools, exact
  local task and runtime authority capabilities, the approval-required Coding
  validation command lane, remaining blocked Coding capabilities, receipt refs,
  evidence/proof refs, blocked authority refs, and unblock prompt refs.

The catalog separates inspectable metadata from callable execution. It shows
Tool Broker v2 entries as preview-only, Action Inbox `local_task_create` as an
exact local mutation authority capability, RuntimeGateway focused pytest,
repo-verifier, frontend-check, and repo-doctor as exact approval-required
runtime capabilities, Coding patch proposal as proposal-only, Coding
allowlisted validation commands as an approval-required RuntimeGateway-backed
lane, and Coding patch apply, Git review, and live preview as blocked until
later exact AuthorityLease capability implementation.

All fields are backend-owned safe refs and bounded summaries. The read model
does not persist raw prompt content, raw response content, provider payloads,
raw local paths, raw logs, account material, credentials, or private data.

## Blocked / Needs Authority

Generic tool execution remains blocked. These also remain blocked:

- unrestricted shell/subprocess execution
- arbitrary command strings
- unapproved code mutation or patch apply
- broad tool invocation
- connector writes
- browser automation
- plugin runtime import
- remote execution
- provider/model calls
- background autonomy
- production authority
- public release or public beta claims

## Exact Promotion Path

Any future authority capability must add exact scope, approval binding,
idempotency, receipt/proof refs, rollback or safe-disable posture, redaction,
CLI/API/Core parity, route classification, focused tests, and Control Center
truth labels.

Patch apply needs checkpoint creation, selected file/hunk apply, exact patch
body validation, sensitive-diff guards, applied patch receipt refs, and rollback
refs before it can mutate files.

The Coding validation command lane now points at the existing RuntimeGateway
focused pytest, repo-verifier, frontend-check, and repo-doctor intents. Any
future command expansion still needs argv-only allowlists, cwd jail, timeout,
env scrub, bounded redacted output, receipt refs, safe-disable posture, and
focused tests before it can run.

Callable tool catalog work needs separate inspectable and callable catalogs,
policy decisions, approval envelopes, idempotency, side-effect classes, receipt
plans, rollback/safe-disable posture, CLI/API/Core parity, and verifier coverage
before any tool invocation is allowed.
