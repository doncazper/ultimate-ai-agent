# v0.72.0 Master Plan

Milestone: M68 Autonomy Risk Classifier.

Scope:

- Add autonomy risk classifier contracts.
- Add risk signal contracts.
- Derive highest risk from declared risk, scoped approval bundle risk, and risk
  signals.
- Deny risk downgrade.
- Revalidate scoped approval bundles and Revocation + Kill Switch records at
  evaluator boundaries.
- Add docs, tests, static verification, documentation-integrity checks, and
  Foundation Gate coverage.

Non-goals:

- Do not activate policy.
- Do not start sessions.
- Do not enable autonomous actions or background workers.
- Do not execute tools, shell commands, network tools, browser automation,
  plugins, mobile sensors, or remote work.
- Do not write memory, inject context, call models/providers as authority, add
  backend routes, add Control Center controls, add dependencies, implement M69,
  or grant production authority.

