# UAA GoatCitadel Runtime Prepared Turn Loop

Status: implemented as Phase 05 of the UAA GoatCitadel runtime parity pack.

This lane adapts GoatCitadel's chat-turn preparation shape into a UAA-native
Python Agent Core read model. It does not copy GoatCitadel code or import
GoatCitadel packages. It does not add runtime authority.

## Implemented Repo-Safe Slice

Python Agent Core owns `PreparedTurn`, a safe-ref read model for:

- session, operator, and task refs
- latest user turn ref
- turn contract decision ref
- route-decision binding
- memory and context readiness
- tool/action readiness
- staged orchestration eligibility
- durable run ref
- evidence refs
- blocked authority refs

Prepared turns expose the branch selected by the Turn Contract Router:

- `answer_directly`
- `base_answer`
- `answer_with_reviewed_memory`
- `draft_or_plan`
- `prepare_tool_or_action`
- `approval_required`
- `execute_approved_exact_action`
- `blocked_unsafe`
- `ask_clarifying_question`

The CLI inspection path is:

```bash
.venv/bin/python scripts/dev/uaa_turn_router.py prepare-turn --sample diy-desk --pretty
```

The API inspection path is:

```text
GET /api/runtime/prepared-turn?sample=diy-desk
```

## Boundaries Preserved

Prepared turns never persist raw prompt text, raw model output, provider
payloads, or raw context. Control Center cannot mint authority. The model
performs no hidden context injection, provider/model call, tool execution,
action execution, browser automation, connector write, shell/subprocess work,
production authority, or broad autonomy.

Route decisions are not approval. Approval-required turns expose exact envelope
posture only, and execution remains blocked unless a later exact-approved lane
proves approval binding, idempotency, receipts, rollback or safe-disable
posture, redaction, CLI/API/Core parity, and focused verifier coverage.
