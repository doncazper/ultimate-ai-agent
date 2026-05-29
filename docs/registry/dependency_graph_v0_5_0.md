# Dependency Graph v0.5.0

```text
Execution Contract
  -> Context Pack
  -> Model Router
  -> Tool Broker
  -> Memory Service
  -> File Manager
  -> QA/Evals

Context Pack
  -> Orchestrator
  -> Verifier
  -> Memory Recall
  -> Tool Execution Context

Event Ledger
  -> Receipts
  -> Replay
  -> Rollback
  -> Cost Governor
  -> Self-Improvement Safety

Consent Ledger
  -> Context Pack filtering
  -> Model Router privacy policy
  -> Tool Broker authorization
  -> Scanner permissions
  -> Companion memory boundaries

Tool Broker
  -> File operations
  -> Memory operations
  -> Code execution
  -> Web access
  -> External actions

Memory Service + File Manager
  -> Spec SDLC
  -> Long-term learning
  -> Canonical truth
  -> Context Pack retrieval

Foundation Gate
  -> Scanners
  -> Proactive Intelligence
  -> Companion Layer
  -> Skill Factory
  -> Self-Improving Coding Framework
  -> Autopilot Workflows
```

Rule: higher layers depend on stable contracts, not implementation details.
