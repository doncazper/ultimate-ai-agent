# Foundation Gate Implementation Plan v2.0.0

v2.0.0 keeps Foundation Gate coverage aligned with the accepted Operator Runtime
Excellence P0 currentness baseline.

Gate coverage:

- Current baseline labels are derived from `VERSION.md` and checked across
  active README, roadmap, docs index, canonical map, release notes, implementation
  plan, and archived release packet paths.
- Active docs must preserve the current v2.0.0 baseline, checkpoint-m168
  repository checkpoint, checkpoint-m166/checkpoint-m167 local model checkpoint
  context, Operator Runtime Excellence roadmap links, current Kanban board link,
  and the 97-path OpenAPI route count.
- Product release-truth, public security posture, M167 live-evidence matrix,
  local model E2E smoke harness, performance baseline harness, and Control
  Center operator-shell gap map remain verifier-checked.
- Release-facing docs are checked for unsafe public-readiness claims and
  unsafe raw-data language.
- OpenAPI route-count currentness and route side-effect metadata remain guarded
  by the existing OpenAPI and API manifest verification lanes.

## Skill Package Security Rule

All skills are untrusted packages by default. Before any later scoped
enablement, a skill package requires:

- a manifest
- declared permissions
- source/provenance metadata
- static review
- sandbox test execution
- Tool Broker permission mapping
- Event Ledger logging
- version pinning
- revocation/disable support
- human approval for high-risk capabilities

This rule does not enable plugin runtime import, arbitrary skill execution, or
external plugin execution.

No runtime authority changes are introduced by this Foundation Gate plan. It
adds no shell/subprocess execution, unrestricted network access, browser
automation, connector writes, plugin runtime import, mobile control, autonomous
background execution, provider/model call, memory write, context injection,
public distribution, beta release, or production authority.
