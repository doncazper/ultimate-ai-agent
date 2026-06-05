# Context Handoff No-Injection Policy

Status: active M40 no-injection policy.
Release: **v0.44.0 / M40 - Context Handoff Approval, No Injection**.

M40 approval decisions are no-injection decisions. A successful approval means
only that a safe context proposal is approved for future handoff review. It does
not inject context into a prompt, chat shell, OpenWebUI session, runtime,
provider, model, memory store, task, action, or tool.

## Denied Flags

The evaluator denies any request or proposal whose current fields enable:

- context handoff execution.
- context injection.
- OpenWebUI handoff execution.
- model calls.
- memory writes.
- export.
- execution.
- raw file access.
- raw content storage.
- full-file content storage.
- unredacted preview storage.
- backend route behavior.
- Control Center mutation behavior.
- production authority.

Evaluator boundaries revalidate these safety-critical fields even when an
object was constructed safely and then changed with `model_copy`.

## Decision Invariants

All M40 decisions keep context injection, OpenWebUI handoff, model call, memory
write, export, and execution authorization false. All performed flags remain
false.

M41 remains future.
