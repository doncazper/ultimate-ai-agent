# Tool Runtime Replay Policy

Status: active M32 documentation.
Current active baseline: **v0.36.1**

M32 runtime invocations require replay-key protection. The evaluator
revalidates the current request object and denies replay-key reuse before
allowing a no-op or filesystem metadata result.

Replay protection is metadata-only. It does not create a scheduler,
background worker, daemon, autonomous loop, persistent execution queue, or
production runtime authority.

Replay-denied decisions keep `execution_performed=False` and
`side_effects_performed=[]`.

M33-M40 remain planned/provisional.
