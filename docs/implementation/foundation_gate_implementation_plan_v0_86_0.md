# Foundation Gate Implementation Plan v0.86.0

v0.86.0 adds M82 Command Proposal Contracts to Foundation Gate.

Gate coverage:

- `m82_command_proposal_contract`
- `m82_command_proposal_static_safety`
- `m82_command_proposal_route_boundary`
- `m82_roadmap_currentness`

The gate verifies proposal-only, review-only, deterministic, local command
proposal contracts; structured argv preview; no shell string; safe summary only
receipt plans; evaluator revalidation; no command execution; no subprocess
execution; no shell execution; no process spawn; no filesystem mutation; no
network access; no tool execution; no browser automation; no plugin execution;
no remote execution; no model call; no memory write; no context injection; no
background worker; no backend route; no Control Center control; no dependency;
no production authority; and M83 remains future.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill or plugin-related
package review requires a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

M82 does not install, enable, execute, import, or trust any skill package,
plugin package, OpenWebUI tool, browser tool, network tool, shell tool, command
tool, runtime sandbox, or external package runtime.
