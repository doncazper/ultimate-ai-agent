Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# README Import v0.25.1

Status: Current import README for v0.25.1 / M21 hardening.

v0.25.1 hardens M21 OpenWebUI Bridge + Chat Shell Integration Contract safety
while keeping the OpenWebUI bridge contract/planning/validation only.
OpenWebUI is the preferred conversational web shell. OpenWebUI is not the agent
brain. Python Agent Core remains authority.

Start with:

- `VERSION.md`
- `ultimate_ai_agent_master_plan_v0_25_1.md`
- `docs/release_notes/v0_25_1.md`
- `docs/implementation/foundation_gate_implementation_plan_v0_25_1.md`
- `docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md`
- `docs/openwebui/CHAT_SHELL_INTEGRATION_CONTRACT.md`
- `docs/openwebui/SESSION_TRANSCRIPT_REF_POLICY.md`
- `docs/openwebui/OPENWEBUI_SECURITY_MODEL.md`
- `docs/openwebui/OPENWEBUI_AUTHORITY_BOUNDARY.md`
- `docs/openwebui/OPENWEBUI_NON_GOALS.md`
- `docs/openwebui/OPENWEBUI_FUTURE_INTEGRATION_STAGES.md`
- `docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md`
- `docs/ui/CLIENT_SURFACE_ROLES.md`
- `docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md`
- `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`
- `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`
- `docs/canonical/09_roadmap.md`

M21 remains contract-only. v0.25.1 clarifies blocked raw-content modes, keeps
safe summary/ref/redacted-preview content modes valid, allows negated authority
boundary text, rejects positive OpenWebUI authority claims, and strengthens
static verifier/Foundation Gate coverage for forbidden OpenWebUI runtime/config
drift.

This patch adds no OpenWebUI integration, no deployment config, no Docker
config, no OpenWebUI plugin/function/pipeline/tool/admin/auth/cookie/API key or
admin token workflow, no browser profile access, no live OpenWebUI connection,
no backend API route, no frontend feature, no runtime execution, no local LLM
call, no model/provider call, no tool execution, no memory write, no file
access, no remote execution, no browser automation, no Computer Use, no mobile
sensor access, no plugin enablement, no dependency, and no production authority.

OpenAPI path count remains `74`. M22 Local Model Runtime Activation Contract
and M23 First Real Local LLM Call remain planned/provisional.
