# OpenWebUI Future Integration Stages

Status: Active M21 contract documentation for v0.25.1. Contract-only.

OpenWebUI is the preferred conversational web shell. Python Agent Core remains authority. Every future stage requires a dedicated milestone and review.

## Stage 0: Docs And Strategy Only

Purpose: record OpenWebUI, CCC, and Agent Core roles.

Must not add: authority bypass, direct tool execution, direct credential access, hidden remote execution, public exposure, direct memory writes, direct model runtime calls, OpenWebUI integration code, or OpenWebUI deployment config.

## Stage 1: Deployment Evaluation, No Integration

Purpose: evaluate local deployment options and operational risk without connecting OpenWebUI to Agent Core.

Must not add: authority bypass, direct tool execution, direct credential access, hidden remote execution, public exposure without security review, direct memory writes, direct model runtime calls, Docker Compose, or deployment config without a dedicated milestone.

## Stage 2: Local-Only Connection Contract

Purpose: define local-only connection constraints before any bridge.

Must not add: authority bypass, direct tool execution, direct credential access, hidden remote execution, public exposure without security review, direct memory writes, direct model runtime calls, non-loopback control paths, or live OpenWebUI calls.

## Stage 3: Validation-Only Bridge

Purpose: validate bridge envelopes without executing actions.

Must not add: authority bypass, direct tool execution, direct credential access, hidden remote execution, public exposure without security review, direct memory writes, direct model runtime calls, model/provider execution authority, or production Control Center authority.

## Stage 4: Chat-To-Agent Adapter

Purpose: allow reviewed chat-to-agent handoff only through Python Agent Core.

Must not add: authority bypass, direct tool execution, direct credential access, hidden remote execution, public exposure without security review, direct memory writes, direct model runtime calls before M22/M23-type gates, approval bypass, or arbitrary approval strings as authority.

## Stage 5: OpenWebUI To CCC Context Links

Purpose: link chat context to CCC status, approval, receipt, and trace views without moving authority into UI clients.

Must not add: authority bypass, direct tool execution, direct credential access, hidden remote execution, public exposure without security review, direct memory writes, direct model runtime calls, secret-bearing URLs, browser storage secrets, mobile storage secrets, or sensitive receipts.

## Stage 6: Advanced Chat And Task Handoff

Purpose: consider advanced chat/task handoff only after approval, event, receipt, and redaction gates are proven.

Must not add: authority bypass, direct tool execution, direct credential access, hidden remote execution, public exposure without security review, direct memory writes, direct model runtime calls before reviewed runtime gates, autonomous execution outside Python Agent Core, or production authority.

M21 implements none of these stages as runtime behavior. M21 adds contracts, validation, docs, tests, verifiers, and Foundation Gate coverage only.
