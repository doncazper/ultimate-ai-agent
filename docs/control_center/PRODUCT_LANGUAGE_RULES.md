# Control Center Product Language Rules

Status: active UAA-P1-031 product language rules
Baseline: v0.103.0 / 0.103.0
Source plan: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md` M172
Scope: Control Center UI strings and release-facing product docs
Readiness taxonomy: `docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md`

This ruleset is an enforceable language contract for production-facing copy. It
does not add runtime authority, backend routes, frontend controls,
shell/subprocess behavior, unrestricted network or browser automation,
connector writes, plugin runtime import, mobile control, autonomous background
execution, public distribution, or production readiness claims.

Control Center and OpenWebUI remain shells. Python Agent Core, PolicyEngine,
LocalApprovalAuthority, route side-effect classification, OpenAPI checks, and
Foundation Gate checks remain the authority boundaries.

Control Center / Founder Command Center is the first-party product UI for
Today, Inbox, Plans, Actions, Memory, Evidence, Settings, Models, and future
first-party Chat. OpenWebUI is a supported local/dev conversational shell and
compatibility surface only; copy must not imply that OpenWebUI owns product
state or is where every UAA workflow will be wired.

Today, Inbox, Plans, Actions, Memory, Evidence, and Settings remain the core
operator loop surfaces for product-language enforcement.

CLI is a first-class operator surface. Product behavior must not live only in
React state; UI-only state is limited to presentation concerns such as filters,
expanded panels, selected tabs, and layout preferences. If the UI can trigger or
mutate an operator-relevant workflow, the same underlying operation must have a
Python core/API contract and a command-line or repo-local script inspection path
with tests and redacted evidence.

## Rules

| Rule | Required wording behavior | Release blocker |
|---|---|---|
| No hidden authority | Operator-critical copy must name or link the route, side-effect class, approval requirement, authority boundary, and evidence output. | Any visible action that implies authority without a route/status manifest entry is blocked. |
| No fake completion | Preview, validation, mock fallback, local UI state, and status-only views must say what did not happen. | Any unimplemented, blocked, skipped, or local-only action described as completed is blocked. |
| No standalone module completion | Module state visible in Today, Actions, Evidence, or Memory is necessary but not sufficient for completion. Copy must still name the typed contract, tests, redaction/policy gates, route/API or CLI inspection path, and blocked follow-on work. | Any module described as complete solely because it appears in the Today loop is blocked. |
| No raw JSON as primary UI for operator-critical flows | Human summaries, safe refs, route status, evidence refs, and blockers must appear before developer payload inspection. | Any chat, plan, model, approval, file, settings, evidence, latency, or rollback flow that relies on JSON as the main operator view is blocked. |
| No frontend-only product behavior | Operator-relevant workflows must identify the backing Python core/API contract and command-line or repo-local script inspection path. | Any Today, Inbox, Plans, Actions, Memory, Evidence, or Settings workflow that exists only in Control Center React state is blocked. |
| No production/public distribution claims without evidence | Copy must say production readiness and public distribution are not claimed unless an accepted release packet proves otherwise. | Any public or production claim without source, test, verifier, release note, and rollback evidence is blocked. |
| No model/provider output as authority | Model, provider, OpenWebUI, runtime, memory, and preview outputs may inform review but cannot authorize work. | Any copy that treats output as approval, truth authority, or execution authority is blocked. |
| No memory-derived execution claims | Memory review, L1/L2/L3 indexes, context packs, and Phase 6 execution-hook contracts must be described as recall, inspection, proposal, or blocked proof surfaces only. | Any copy implying memory/context packs execute actions or that Phase 6 hooks are shipped/available is blocked. |
| No model lifecycle completion words without backend receipts | Words such as loaded, running, switched, and updated identity require backend receipt/evidence refs from Python Agent Core. Without those refs, use planned, blocked, unknown, or status-only language. | Any Control Center or OpenWebUI copy that treats React state, `/v1/models`, logs, or model output as proof of local model lifecycle completion is blocked. |
| No completed-state language for blocked/skipped/pending work | Blocked, skipped, pending, mock-only, local-state-only, and partial states must keep that state visible. | Any blocked, skipped, pending, mock-only, or partial item labeled done, finished, succeeded, or completed is blocked. |

## Approved State Language

Use the canonical operator-readiness taxonomy in
`docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md`. These words are approved
when they match the implementation and evidence:

- shipped
- planned
- status available
- preview only
- validation only
- review only
- local UI state only
- mock only
- partial
- blocked
- pending evidence
- skipped prerequisite
- not scoped
- status-only
- unknown
- needs review
- accepted failure

Completion words are allowed only when the implementation produced accepted
durable evidence for the exact work described. A route returning a preview,
validation decision, local UI state change, mock fallback, or skipped
prerequisite is never completion evidence.

## UI Requirements

Operator-critical surfaces must show a human-readable state first. Safe refs,
route names, side-effect classes, approval requirements, and evidence refs can
support that state, but they cannot replace it.

Buttons and menu labels must describe the real action available in the current
UI. Preview-only controls use preview/review/view wording. Local-state-only
controls must say review-only or local state. Disabled or missing work must stay
blocked, partial, or not scoped.

Future Founder Command Center surfaces for Today, Inbox, Plans, Actions, Memory,
Evidence, Settings, Models, and first-party Chat must remain inspectable through
backend/core contracts and, where appropriate, CLI commands or repo-local
scripts. The frontend can make those workflows easier to operate, but it cannot
become the only access path.

Status panels must avoid standalone readiness claims. When a backend field uses
a readiness-shaped name, the UI must frame it as a claim status or evidence
status and keep false/unproven values visibly unclaimed.

## Current Gaps

The current Control Center still has blocked, mock-only, local-state-only, and
partial surfaces. The route status manifest is the current release evidence for
visible action truth, not evidence that the full operator loop is complete.
FCC-V1-007 proofed only `/actions`, `/chat`, `/memory`, and `/evidence` for
their exact backend-owned route-surface behavior. Chat handoff execution,
Models lifecycle controls, Settings, Inbox, broader Today-spine completion,
connector workflows, public beta, public release, and production authority
remain blocked or partial until later gates add reviewed routes, UI, evidence,
and rollback proof.

## Enforcement

These checks enforce the rules:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py
make frontend-check
```

`scripts/verify_control_center_frontend.py` checks the Control Center copy,
route status manifest, and required product-language documentation. The
documentation integrity verifier checks release-facing doc links, product-truth
claims, Kanban status, and unsafe public or production language.

## Rollback

Rollback is to remove this document, remove its active links, remove the
P1-031 verifier/test assertions, restore the previous two runtime status
labels, and move UAA-P1-031 out of Done on the Kanban board. No runtime state,
route, authority, migration, or persistent user data is changed.
