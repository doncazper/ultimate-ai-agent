# M85 Read-Only Command Allowlist Receipt Plan

The M85 receipt plan stores safe refs only and safe summary only.

Allowed receipt fields are stable refs such as:

- allowlist ref
- sandboxed echo/no-op decision ref
- command proposal ref
- command ref
- safe reason codes

Denied receipt fields:

- no shell string
- no raw command
- no raw output
- no raw prompt
- no secret-like content
- no command execution evidence
- no subprocess execution evidence
- no shell execution evidence
- no process spawn evidence
- no filesystem mutation evidence

Evaluator boundaries revalidate receipt bindings before a decision can be
treated as valid for review. M86 remains future.
