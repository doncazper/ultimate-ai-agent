# ADR-0022-use-explicit-security-threat-model: Use Explicit Security Threat Model

## Status

Accepted as v0.4 planning baseline.

## Context

The Ultimate AI Agent is expanding into a companion-style, proactive, self-improving, skill-acquiring system with scanners, code execution, file management, memory, external tools, and user-specific learning. This requires strong trust, control, stability, and recovery infrastructure.

## Decision

Adopt: Use Explicit Security Threat Model.

## Consequences

- Improves trust, auditability, and long-term maintainability.
- Adds upfront architecture work before high-autonomy modules can safely ship.
- Requires schemas, evals, user controls, and observability events.
- Must be represented in canonical files and the Capability Registry.

## Related

- /docs/canonical/TBD
- /docs/canonical/31_layered_brain_architecture.md
- /docs/canonical/34_foundation_change_management_and_contract_testing.md
