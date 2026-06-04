# README Import v0.35.0

Status: historical release packet. Do not use as current baseline.

Historical baseline: **v0.35.0**

v0.35.0 implements M31 Real Tool Runtime Adapter, Single Safe No-Op Tool. It
adds a governed no-op-only runtime adapter, one deterministic no-op tool,
safe invocation contracts, no-op result envelopes, replay protection, receipt
plans, documentation, documentation-integrity checks, static verification, and
Foundation Gate coverage.

The only allowed runtime invocation is `tool:no_op.v1`. No arbitrary,
dynamic, side-effecting, shell, file, memory, network, model, browser, mobile,
remote, or plugin tools are enabled.

OpenAPI path count remains `74`. M32-M40 remain planned/provisional.
