# 33 — Shadow Mode, Simulation, and Digital Twin Testing

Status: Foundation testing spec, v0.5.3
Owner: QA / Runtime

## Purpose

Shadow Mode lets the agent exercise workflows without live side effects. It is required before scanners, proactive alerts, self-improvement, external execution, or autopilot.

## Modes

```text
dry_run: produce planned tool calls without executing
shadow_run: execute safe reads, simulate writes
replay: re-run an Event Ledger trace against current code/contracts
canary: limited real execution behind explicit flags
simulation: test against synthetic data/workspaces
digital_twin: mirror user/project state with no live external effects
```

## Required for Foundation Gate

```text
Replay Minimum Lovable Kernel trace.
Detect contract schema changes.
Detect tool-policy changes.
Verify rollback plan can be generated.
Verify receipts redact secrets.
Verify advanced modules remain blocked.
```

## Blocking rule

Any module that performs high-volume scanning, notifications, code self-improvement, or external mutations must pass shadow mode before live mode.
