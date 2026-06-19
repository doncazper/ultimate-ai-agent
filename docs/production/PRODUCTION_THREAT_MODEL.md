# Production Threat Model

Status: Checkpoint M111. Contract-only and review-only.

Checkpoint M111 Production Threat Model records a safe production threat model
over the Checkpoint M110 Mobile Sensor Hardening Freeze. It uses safe refs,
threat surface refs, mitigation plan refs, audit refs, replay refs, and a
no-effect receipt plan.

M111 is actor-bound, baseline-bound, source-freeze-bound, audit-bound, and
replay-safe. It verifies that M101-M110 checkpoint refs are accepted before
recording the production threat model contract.

M111 requires safe refs only. It records no credential values, raw deployment
payloads, raw runtime payloads, secrets, tokens, cookies, or private production
data.

M111 does not consume a product SemVer version. The current product baseline
remains v1.7.2, M111 is tagged as a checkpoint, and M150 remains the
v1.2.0-alpha target. Beta begins later after the alpha UI and supporting
safety/product work are reviewed and promoted.

M111 adds no production authority, no production runtime, no external
distribution, no deployment, no credential handling, no network access, no
model call, no memory write, no context injection, no execution, no tool
execution, no shell execution, no browser automation, no plugin execution, no
mobile sensor, no background worker, no remote execution, no backend route, no
Control Center control, and no dependency.

M112 remains future.
