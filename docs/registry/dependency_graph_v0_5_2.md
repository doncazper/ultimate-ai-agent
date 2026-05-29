# Dependency Graph v0.5.2

```text
Agent API Boundary
  -> OpenWebUI Chat Shell
  -> TypeScript Control Center
  -> CLI/Workers/Future Clients

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
  -> Control Center Activity Log

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

OpenWebUI
  -> Agent API Boundary only
  -X Memory direct writes
  -X Tool direct execution
  -X Canonical file direct mutation

TypeScript Control Center
  -> Agent API Boundary only
  -> Generated API client
  -X Database direct access
  -X Tool direct execution

Foundation Gate
  -> Web Research
  -> Scanners
  -> Proactive Intelligence
  -> Companion Layer
  -> Skill Factory
  -> Self-Improving Coding Framework
  -> Autopilot Workflows
```

Rule: higher layers depend on stable contracts, not implementation details. UI clients must not bypass the Agent Core.
