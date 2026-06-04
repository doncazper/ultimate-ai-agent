# Tool Runtime Replay Policy

Status: active M31 documentation.
Current active baseline: **v0.35.0**

M31 no-op runtime invocations require replay-key protection. The evaluator
revalidates the current request object and denies replay-key reuse before
allowing the deterministic no-op invocation.

Replay protection is metadata-only. It does not create a scheduler,
background worker, daemon, autonomous loop, persistent execution queue, or
production runtime authority.

Replay-denied decisions keep `execution_performed=False` and
`side_effects_performed=[]`.

M32-M40 remain planned/provisional.
