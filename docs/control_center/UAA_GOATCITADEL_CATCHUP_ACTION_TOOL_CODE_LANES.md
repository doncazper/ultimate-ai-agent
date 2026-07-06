# UAA GoatCitadel Catch-Up Action Tool Code Lanes

Status: Phase 04 implemented as backend-owned catalog/read-model hardening only.

## Full-Strength Version

UAA should make action, tool, runtime, and code-workflow capability posture
legible in one operator surface: what can be inspected, what can propose work,
what exact lanes can produce receipts, what needs approval, what can roll back
or safe-disable, and what remains blocked. Future callable tools, code apply,
test command, Git, and preview lanes must stay exact-scoped and receipt-backed.

## Repo-Safe Version

Phase 04 adds Python Core Action/Tool/Code Lane Catalog contract
`contract-ref:goatcitadel-catchup-action-tool-code-catalog:v1`:

- Core builder:
  `src/ultimate_ai_agent/core/control_center/action_tool_code_catalog.py`
- API embedding:
  `GET /control-center/actions/inbox`
- CLI:
  `scripts/dev/uaa_founder_loop.py inspect-action-tool-code-catalog`
- Control Center:
  Action Inbox renders a read-only catalog panel with preview-only tools, exact
  local/task and runtime micro-lanes, blocked Coding lanes, receipt refs,
  evidence/proof refs, blocked authority refs, and unblock prompt refs.

The catalog separates inspectable metadata from callable execution. It shows
Tool Broker v2 entries as preview-only, Action Inbox `local_task_create` as an
exact local mutation lane, RuntimeGateway focused pytest, repo-verifier,
frontend-check, and repo-doctor as exact approval-required lanes, Coding patch proposal as
proposal-only, and Coding patch apply, allowlisted test command, Git review,
and live preview as blocked until later exact authority graduation.

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

Any future lane must add exact scope, approval binding, idempotency,
receipt/proof refs, rollback or safe-disable posture, redaction, CLI/API/Core
parity, route classification, focused tests, and Control Center truth labels.

Patch apply needs checkpoint creation, selected file/hunk apply, exact patch
body validation, sensitive-diff guards, applied patch receipt refs, and rollback
refs before it can mutate files.

Allowlisted test commands need argv-only allowlists, cwd jail, timeout, env
scrub, bounded redacted output, receipt refs, and safe-disable posture before
any command can run.

Callable tool catalog work needs separate inspectable and callable catalogs,
policy decisions, approval envelopes, idempotency, side-effect classes, receipt
plans, rollback/safe-disable posture, CLI/API/Core parity, and verifier coverage
before any tool invocation is allowed.
