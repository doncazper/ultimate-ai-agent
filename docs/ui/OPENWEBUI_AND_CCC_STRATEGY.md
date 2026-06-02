# OpenWebUI and CCC Strategy

Status: Active UI strategy clarification for v0.19.1. Documentation only.

OpenWebUI is the preferred conversational web shell for local LLM chat. It is a chat surface, not the agent brain, and it must not bypass Python Agent Core.

CCC means Control Center Clients. CCC is the governance/control layer for custom client surfaces that inspect status, governance, approvals, receipts, previews, and safe control workflows through Python Agent Core APIs.

Authority boundaries:

- Python Agent Core remains the brain and authority layer.
- OpenWebUI is not the agent brain.
- CCC is the governance/control layer, not the agent brain.
- OpenWebUI must not bypass Python Agent Core.
- OpenWebUI must not bypass Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, Redaction, or Foundation Gate.
- CCC clients must not bypass Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, Redaction, or Foundation Gate.
- secrets must never enter UI snapshots, browser storage, mobile storage, logs, screenshots, build artifacts, prompts, receipts, or user-visible output.

Future bridge posture:

- OpenWebUI may later connect to Agent Core through a reviewed adapter or bridge.
- any future OpenWebUI bridge must use stable API/OpenAPI contracts.
- any future OpenWebUI bridge must remain approval-gated, receipt-backed, and auditable.
- OpenWebUI plugins, functions, pipelines, and tools are high-risk until governed.

Open Design relationship:

- Open Design does not replace OpenWebUI.
- Open Design governs custom CCC surfaces, including CCC Web and future native CCC clients.
- OpenWebUI remains the preferred conversational web shell.
- CCC remains the custom governance/control client family.

Explicit non-implementation statement:

- no OpenWebUI integration is implemented in this patch.
- no OpenWebUI deployment config is added in this patch.
- no OpenWebUI plugin, function, pipeline, or tool bridge is enabled in this patch.
- no backend API route is added in this patch.
- no frontend feature is added in this patch.
- no runtime execution, model/provider call, network call, remote execution, plugin enablement, dependency, native build workflow, mobile sensor access, OS permission integration, or production authority is added in this patch.
## M19 Mobile Companion Contract Planning

v0.23.0 / M19 adds Mobile Companion Contract/API Planning only. OpenWebUI
remains the preferred conversational web shell and is not the agent brain. CCC
means Control Center Clients, including CCC Web, CCC iOS, CCC Android, and CCC
macOS. CCC is the governance/control layer and must use Python Agent Core
authority.

M19 adds no OpenWebUI integration, no OpenWebUI deployment config, no backend
API route, no native CCC implementation, no Android app, no iOS app, no macOS
app, no native build workflow, no mobile sensor access, and no OS permission
integration. Device Capability Broker is required before sensors. Capture
cannot silently become memory. M20 is implemented as contract-only planning and
validation. v0.25.0 implements M21 OpenWebUI Bridge + Chat Shell Integration
Contract as contract/planning/validation only. It adds no OpenWebUI
integration, no OpenWebUI deployment config, no backend API route, no frontend
feature, no runtime execution, no local LLM call, no model/provider call, no
tool execution, no memory write, no file access, no remote execution, no
browser automation, no Computer Use, no mobile sensor access, no plugin
enablement, no dependency, and no production authority. v0.26.0 implements
M22 Local Model Runtime Activation Contract as contract/planning/validation
only. M23 is implemented/released by v0.27.0 as manual fixed-prompt local call
only and does not add OpenWebUI runtime integration or CCC execution authority.
