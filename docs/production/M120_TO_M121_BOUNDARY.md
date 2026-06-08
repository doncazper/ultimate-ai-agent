# M120 to M121 Boundary

M120 implements Production Authority Readiness Review as contract-only,
review-only planning. It may define safe refs and no-effect receipt plans for
readiness check refs, launch blocker refs, rollback readiness refs, audit refs,
replay refs, and source Production Red-Team Harness refs.

M121 Email Connector Contract Refresh remains future. M120 must not add email
connector runtime, connector credentials, connector network access, account
action, production authority, production runtime, go-live, production
deployment, traffic routing, credential handling, model call, memory write,
context injection, execution, backend routes, Control Center controls,
dependencies, beta release, or production authority.

The product baseline remains v1.7.2. M120 uses the checkpoint-m120 tag rather
than a product SemVer tag. M150 remains the planned v1.0.0-alpha target.
