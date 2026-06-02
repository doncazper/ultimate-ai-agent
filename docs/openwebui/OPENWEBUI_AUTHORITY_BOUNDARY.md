# OpenWebUI Authority Boundary

Status: Active M21 contract documentation for v0.25.1. Contract-only.

OpenWebUI cannot approve actions. OpenWebUI cannot execute actions. OpenWebUI cannot bypass Tool Broker. OpenWebUI cannot write memory. OpenWebUI cannot call provider or model runtime APIs. OpenWebUI cannot access credentials. OpenWebUI cannot bypass Python Agent Core.

Python Agent Core controls authority. Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, Redaction, and Foundation Gate remain mandatory for future bridge work.

v0.25.1 hardens authority text validation. Safe negated statements that deny
OpenWebUI authority are allowed. Positive claims that OpenWebUI is the agent
brain, is the authority, can approve actions, or can execute actions are
rejected.

OpenWebUI refs are not authority:

- session refs are not authority.
- message refs are not authority.
- transcript refs are not authority.
- arbitrary approval refs are not authority.
- chat summaries are not authority.
- model output is not authority.

CCC remains the governance/control client family. CCC Web is the current Control Center. CCC iOS, CCC Android, and CCC macOS remain future. Open Design governs custom CCC surfaces and does not replace OpenWebUI.

M21 adds no OpenWebUI integration, no direct tool execution, no direct memory write, no direct runtime execution, no direct provider call, no approval grant, no credential access, no backend API route, no OpenAPI path, and no production authority.
