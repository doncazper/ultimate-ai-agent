# Foundation Gate Implementation Plan v0.60.0

v0.60.0 implements M56 Agent Eval Regression Harness.

All skills are untrusted packages by default. Coverage continues the Skill
Package Security Rule language requiring a manifest, declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker
permission mapping, Event Ledger logging, version pinning, revocation/disable
support, and human approval for high-risk capabilities.

Foundation Gate coverage requires:

- deterministic local eval regression contracts.
- policy validation for model call, provider call, tool execution, shell
  execution, browser automation, network access, memory write, context
  injection, raw prompt capture, raw provider payload capture, external dataset
  fetch, backend route, dependency, production authority, and M57 denial.
- OpenAPI route-boundary checks for no eval run/execute/raw/model/provider
  routes.
- documentation-integrity checks for M56 docs and M57 future status.

The Skill Package Security Rule, Tool Broker permission mapping, and
revocation/disable support remain unchanged by M56.
