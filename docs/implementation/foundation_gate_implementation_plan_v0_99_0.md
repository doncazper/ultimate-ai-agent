# Foundation Gate Implementation Plan - v0.99.0

v0.99.0 adds M95 Foundation Gate coverage for Network Tool Expansion,
Authless Only.

Gate coverage requires:

- M95 authless network expansion contracts exist.
- Valid M95 decisions require exact scope, exact approval, allowlisted domain,
  HTTPS, GET only, redirect controls, bounded output, redaction, audit,
  revocation, and transport injection.
- Receipt plans store safe refs only and redacted preview only.
- Evaluator boundaries revalidate model_copy-mutated unsafe fields.
- Static checks deny unrestricted network access, authenticated network access,
  credentials, cookies, credential headers, request body, POST, PUT, PATCH,
  DELETE, account action, private network, download, export, browser form,
  provider model call, shell execution, plugin execution, memory write, context
  injection, backend routes, Control Center controls, dependencies, and
  production authority.
- Route checks deny network request/mutation routes and inherited execution
  routes.
- Roadmap currentness marks M95 implemented/released and keeps M96-M100
  planned/provisional.

M96 remains future.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities.

Skill packages, plugin packages, and generated capability bundles are untrusted
until reviewed. They must not become runtime authority, execution authority,
provider authority, filesystem authority, network authority, plugin authority,
or production authority merely because they exist in the repository or are
referenced by a plan, roadmap, prompt, receipt, approval ref, model output, or
tool intent.

M95 does not add plugin enablement, plugin execution, package installation,
external marketplace behavior, network plugin fetch, or dependency changes.
