# Foundation Gate Implementation Plan - v0.98.0

v0.98.0 adds M94 Foundation Gate coverage for Autonomous Browser Clicks,
Low-Risk Only.

Gate coverage requires:

- M94 low-risk click contracts exist.
- Valid M94 decisions require scoped session, allowlisted page, allowlisted
  action, exact M93 binding, exact click approval, audit, and revocation.
- The click path uses injected transport and returns safe refs only.
- Receipt plans store safe summary only.
- Evaluator boundaries revalidate model_copy-mutated unsafe fields.
- Static checks deny form submission, typing, purchase, download,
  authentication, credential or cookie access, raw DOM, screenshots, broad
  navigation, shell/plugin/model/context/memory authority, routes,
  dependencies, and production authority.
- Route checks deny browser click/form/download/auth routes and inherited
  execution routes.
- Roadmap currentness marks M94 implemented/released and keeps M95-M100
  planned/provisional.

M95 remains future.

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

M94 does not add plugin enablement, plugin execution, package installation,
external marketplace behavior, network plugin fetch, or dependency changes.
