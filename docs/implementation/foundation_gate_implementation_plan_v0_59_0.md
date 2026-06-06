# Foundation Gate Implementation Plan v0.59.0

v0.59.0 implements M55 Redacted Observability Export.

All skills are untrusted packages by default. Coverage continues the Skill Package Security Rule language requiring a manifest, declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping,
Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

Foundation Gate coverage requires:

- redacted-only observability export contracts.
- policy validation for raw prompt, provider payload, private content, secret,
  SaaS, network, model call, memory write, context injection, backend route,
  dependency, production authority, and M56 denial.
- OpenAPI route-boundary checks for no observability export/raw/SaaS/network
  routes.
- documentation-integrity checks for M55 docs and M56 future status.

The Skill Package Security Rule, Tool Broker permission mapping, and
revocation/disable support remain unchanged by M55.
