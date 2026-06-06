# Foundation Gate Implementation Plan v0.73.0

v0.73.0 implements M69 Low-Risk Autonomous Dry Run.

Foundation Gate coverage:

- M69 low-risk autonomous dry-run contracts exist.
- M69 request, step, and record contracts exist.
- M69 binds records to exact M68 Autonomy Risk Classifier decisions.
- M69 enforces a low risk ceiling.
- Higher-risk M68 decisions are denied.
- Higher-risk dry-run steps are denied.
- Approval refs are identifiers only.
- Evaluator boundaries revalidate current object fields and model-copy mutated
  fields are denied.
- M69 adds no backend route, Control Center control, dependency, execution,
  memory write, context injection, model/provider authority, background worker,
  policy activation, session start, M70 work, or production authority.

Skill Package Security Rule:

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before any future enablement.
