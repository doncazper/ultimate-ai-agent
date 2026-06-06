# v0.80.0 Master Plan

v0.80.0 implements M76 OpenWebUI Runtime Bridge v1.

Scope:

- Add OpenWebUI runtime bridge v1 contracts.
- Add safe-ref-only bridge requests.
- Add deterministic review-only bridge envelopes.
- Add policy validation and request validation.
- Add receipt plans with no side effects performed.
- Add stable reason codes.
- Add tests for denied runtime calls, authority refs, raw payloads, and unsafe fields.
- Add evaluator revalidation coverage for model-copy mutated fields.
- Add static verifier and Foundation Gate coverage.
- Add documentation and release notes.

Safety boundaries:

- no live OpenWebUI connection.
- no OpenWebUI runtime call.
- no OpenWebUI handoff execution.
- no provider call.
- no model call.
- no model authority.
- no tool execution.
- no memory write.
- no context injection.
- no network call.
- no credentials or cookies.
- no raw prompt.
- no raw provider payload.
- no raw content.
- no backend route.
- no Control Center control.
- no dependency.
- no production authority.

M77 remains future.
