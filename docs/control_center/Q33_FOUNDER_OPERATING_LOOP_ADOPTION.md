# Q33 Founder Operating Loop Functional Adoption

Status: bounded implementation slice; Q33 remains active until every accepted
surface in the Queue V2 contract has protected merge and post-merge evidence.

## Implemented Chat workspace slice

The Control Center `/chat` surface now starts with a readable conversation
workspace before the existing readiness and redacted-probe diagnostics. A
clean install can create an unsent draft without credentials or a model. The
conversation rail supports local search, selection, archive, and recovery.

Python Agent Core owns the durable product state through:

- `GET /control-center/chat/workspace`
- `POST /control-center/chat/threads/{thread_ref}/draft-checkpoint`
- `POST /control-center/chat/threads/{thread_ref}/lifecycle`

The read-only `python scripts/inspect_chat_workspace.py` command projects the
same content-free workspace contract without creating local state or printing
the inspected path.

The server stores only the thread ref, generated display name, lifecycle state,
revision, draft-present flag, character count, and a content fingerprint. It
does not receive or store the draft body. The current browser tab may retain an
unsent draft in session storage so route changes and refresh can restore it. If
that tab-local body is missing or its fingerprint does not match the backend
checkpoint, the UI reports that re-entry is required instead of inventing a
recovery.

Draft checkpoints and archive/recover requests require the existing Control
Center backend-truth binding, exact idempotency input, targeted local rate
limits, durable replay/conflict handling, and content-free receipt/audit refs.

## Authority boundary

This slice adds no ordinary Chat send, provider or model call, second model
call, tool execution, memory write, context injection, connector read/write,
web access, shell execution, action execution, approval shortcut, public
release claim, or production authority. The Send control remains unavailable.
The existing separately governed redacted readiness probe remains unchanged.

## Verification

- `tests/test_q33_chat_content_free_workspace.py`
- `tests/test_control_center_mutation_backend_truth_binding.py`
- `apps/control-center/src/components/ChatWorkspacePanel.test.tsx`
- `python scripts/inspect_chat_workspace.py --state-dir <local-state-dir>`
- OpenAPI/API manifest snapshot and documentation-integrity verification

This is the first Q33 slice, not terminal evidence for the full Founder
Operating Loop adoption item.
