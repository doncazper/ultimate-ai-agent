# v0.73.0 Master Plan

Milestone: M69 Low-Risk Autonomous Dry Run.

Scope:

- Add low-risk autonomous dry-run contracts.
- Bind dry-run records to exact M68 Autonomy Risk Classifier decisions.
- Enforce a low risk ceiling.
- Deny higher-risk M68 decisions and higher-risk dry-run steps.
- Keep approval refs as identifiers only.
- Revalidate safety-critical fields at evaluator boundaries.
- Add docs, tests, static verification, documentation-integrity checks, and
  Foundation Gate coverage.

Non-goals:

- Do not activate policy.
- Do not start sessions.
- Do not enable autonomous actions or background workers.
- Do not execute tools, shell commands, network tools, browser automation,
  plugins, mobile sensors, or remote work.
- Do not write memory, inject context, call models/providers as authority, add
  backend routes, add Control Center controls, add dependencies, implement M70,
  or grant production authority.
