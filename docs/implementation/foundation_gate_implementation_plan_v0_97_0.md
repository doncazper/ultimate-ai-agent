# Foundation Gate Implementation Plan - v0.97.0

v0.97.0 adds M93 Foundation Gate coverage for Multi-Tool Dry-Run to Real Run Promotion.

Gate criteria:
- `m93_multi_tool_dry_run_promotion`
- `m93_multi_tool_dry_run_promotion_static_safety`
- `m93_multi_tool_dry_run_promotion_route_boundary`
- `m93_roadmap_currentness`

The gate verifies exact M92 binding, exact promotion approval, wildcard approval denied, dry-run plan and real-run plan equivalence, matching plan hashes, safe refs only receipt plans, no unapproved real execution, no real-run execution, no tool execution, no session start, no routes, no dependencies, and M94 planned/provisional status.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

Skill packages, plugin packages, and generated capability bundles are untrusted
until reviewed. They must not become runtime authority, execution authority,
provider authority, filesystem authority, network authority, plugin authority,
or production authority merely because they exist in the repository or are
referenced by a plan, roadmap, prompt, receipt, approval ref, model output, or
tool intent.

M93 does not add plugin enablement, plugin execution, package installation,
external marketplace behavior, network plugin fetch, or dependency changes.
