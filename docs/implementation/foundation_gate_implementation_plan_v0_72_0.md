# Foundation Gate Implementation Plan v0.72.0

v0.72.0 implements M68 Autonomy Risk Classifier.

Foundation Gate coverage:

- M68 risk classifier contracts exist.
- M68 risk signal contracts exist.
- Derived risk is highest declared/bundle/signal risk.
- Risk downgrade is denied.
- Approval refs are identifiers only.
- Scoped approval bundles and Revocation + Kill Switch records are revalidated
  at evaluator boundaries.
- M68 adds no backend route, Control Center control, dependency, execution,
  memory write, context injection, model/provider authority, background worker,
  policy activation, session start, M69 work, or production authority.

Skill Package Security Rule:

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities before any future enablement.
