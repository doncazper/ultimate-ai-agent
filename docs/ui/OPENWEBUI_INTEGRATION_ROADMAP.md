# OpenWebUI Integration Roadmap

Status: Future roadmap clarification for v0.18.3. Documentation only.

OpenWebUI is the preferred conversational web shell. Integration with Python Agent Core is future work and must advance through reviewed milestones. Every stage must preserve Python Agent Core authority, Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, Redaction, Foundation Gate, and stable API/OpenAPI contracts.

## Stage 0: Docs and Strategy Only

Purpose: record OpenWebUI and CCC roles.

Must not add:

- authority bypass.
- direct tool execution.
- direct credential access.
- hidden remote execution.
- external hosted OpenWebUI dependency.
- public exposure without security review.
- OpenWebUI integration code.
- OpenWebUI deployment config.

## Stage 1: OpenWebUI Deployment Evaluation, No Integration

Purpose: evaluate local deployment options and operational risks without connecting OpenWebUI to Agent Core.

Must not add:

- authority bypass.
- direct tool execution.
- direct credential access.
- hidden remote execution.
- external hosted OpenWebUI dependency.
- public exposure without security review.
- Docker Compose or deployment config without a dedicated milestone.

## Stage 2: OpenWebUI Local-Only Connection Contract

Purpose: define a local-only connection contract before any bridge.

Must not add:

- authority bypass.
- direct tool execution.
- direct credential access.
- hidden remote execution.
- external hosted OpenWebUI dependency.
- public exposure without security review.
- non-loopback OpenWebUI control paths.

## Stage 3: OpenWebUI Bridge to Agent Core, Validation-Only

Purpose: design a validation-only bridge that can inspect contracts without executing actions.

Must not add:

- authority bypass.
- direct tool execution.
- direct credential access.
- hidden remote execution.
- external hosted OpenWebUI dependency.
- public exposure without security review.
- model/provider execution authority.

## Stage 4: OpenWebUI Chat-to-Agent Adapter, Approval-Gated

Purpose: allow reviewed chat-to-agent handoff only through Python Agent Core and Approval Authority.

Must not add:

- authority bypass.
- direct tool execution.
- direct credential access.
- hidden remote execution.
- external hosted OpenWebUI dependency.
- public exposure without security review.
- approval bypass or arbitrary approval strings as authority.

## Stage 5: OpenWebUI to CCC Context Links

Purpose: link chat context to CCC status, approval, receipt, and trace views without moving authority into UI clients.

Must not add:

- authority bypass.
- direct tool execution.
- direct credential access.
- hidden remote execution.
- external hosted OpenWebUI dependency.
- public exposure without security review.
- secret-bearing URLs, browser storage, mobile storage, or receipts.

## Stage 6: Advanced Chat and Task Handoff

Purpose: consider advanced chat/task handoff only after approval, event, receipt, and redaction gates are proven.

Must not add:

- authority bypass.
- direct tool execution.
- direct credential access.
- hidden remote execution.
- external hosted OpenWebUI dependency.
- public exposure without security review.
- autonomous execution outside Python Agent Core.
