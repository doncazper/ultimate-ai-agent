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
- `POST /control-center/chat/threads/{thread_ref}/approval`
- `POST /control-center/chat/threads/{thread_ref}/draft-checkpoint`
- `POST /control-center/chat/threads/{thread_ref}/lifecycle`

The read-only `python scripts/inspect_chat_workspace.py` command projects the
same content-free workspace contract without creating local state or printing
the inspected path.

The server stores only the thread ref, generated display name, lifecycle state,
revision, draft-present flag, character count, and an opaque random session
fingerprint that is not derived from the draft text. It
does not receive or store the draft body. The current browser tab may retain up
to 100 unsent drafts in memory, including while the operator navigates away
from and back to Chat, and keeps each non-empty local conversation reachable
from the rail. Draft bodies are discarded on reload. If a tab-local body is
missing or its fingerprint does not match the backend checkpoint, the UI
reports that re-entry is required instead of inventing a recovery.

Draft checkpoints and archive/recover requests require the existing Control
Center backend-truth binding, explicit operator confirmation, exact
`LocalApprovalAuthority` scope validation, expected current revision, exact
idempotency input, targeted local rate limits, bounded request size and JSON
depth, durable replay/conflict handling, private no-store responses, and
content-free receipt/audit refs. Creation stops at the same 100-thread bound
published by the read contract. A separate durable approval route captures the
exact operator-confirmed grant before the mutation request; approval capture
alone does not mutate the workspace. The Python mutation service can only load
and validate that already captured exact grant and cannot issue authority for
itself. Active approvals expire after five minutes and are capped at 512. Each
approval capture attempt is exact-idempotent and cannot renew its own expired
tombstone. An unused expired attempt may be replaced by one fresh, separately
identified approval attempt while the mutation keeps its original durable
idempotency identity. A completed exact mutation can still replay its immutable
receipt after the governing approval expires; this recovery path performs no
new state change. The combined approval history is capped at the same
10,000-record bound as workspace mutations. Every supplied idempotency alias
must be individually valid and equal.

The workspace accepts at most 10,000 unique mutation records. Once that bound
is reached, old keys still replay exactly while new keys fail before state is
changed. A transactional evidence outbox repairs a failed JSONL append on exact
replay. Fresh delivery appends directly; the full log is consulted only after
an ambiguous interrupted delivery, including legacy crash rows migrated as
already attempted. Stored replay receipts are reconstructed through the
governing contract before they can be returned. Each checkpoint overwrite
receipt also carries an exact, content-free snapshot and fingerprint of the
immediately prior thread revision, so the overwritten state remains reviewable
without retaining a draft body or granting a rollback mutation.

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
