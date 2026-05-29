# Dependency Graph v0.5.3

```text
Minimum Lovable Kernel
  depends_on: Execution Contract, Context Pack, Consent Ledger, Tool Broker, File Manager, Event Ledger, Rollback, QA, Memory Service

Provider modules
  depend_on: Secret Broker, Provider Registry, Consent Ledger, Tool Broker, Cost Governor, Event Ledger, Provider Normalization

Scanners
  depend_on: Provider modules, Source Credibility, Attention Budget, Event Ledger, Cost Governor, Consent Ledger

Self-improving code
  depends_on: Code Workspace, Sandbox, Tool Broker, Event Ledger, Trusted Computing Base, QA/Evals, Human approval for high-risk changes
```
