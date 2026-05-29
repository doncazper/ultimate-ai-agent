# Module Readiness Audit v0.4.5

Status: Planning review for programming readiness

## Summary

The v0.4.5 update upgrades Model Routing from a draft concept into a foundation spec. Several other modules remain draft-level and should be detailed before implementation begins, especially foundation modules that other layers will depend on.

## Readiness categories

```text
Implementation-ready: enough contract detail exists to start coding.
Needs foundation spec: must be expanded before coding dependent systems.
Can remain draft: should stay conceptual until Foundation Gate passes.
```

## Must detail before actual foundation programming

| Priority | Module | Current issue | Why it matters | Required next artifact |
|---:|---|---|---|---|
| 1 | Execution Contract | Needs final schema and contract tests | Every orchestrated run depends on it | `execution_contract.schema.json` + contract eval |
| 2 | Context Pack | Needs final schema and retrieval boundaries | Controls how memory/files/specs enter tasks | `context_pack.schema.json` + precedence tests |
| 3 | Event Ledger / Observability | Needs exact event taxonomy and trace completeness | Debugging, audit, replay, cost, approvals, routing all depend on it | `event_ledger.schema.json` + trace tests |
| 4 | Consent and Permissions Ledger | Needs permission scopes/actions/expiry/revocation semantics | Required before scanners, email/messages, tools, cloud routing | `permission.schema.json` + consent evals |
| 5 | Tool Broker | Needs tool manifest, risk categories, dry-run/approval contract | All tools/files/code/web/actions depend on it | `tool_manifest.schema.json` + approval tests |
| 6 | File Manager | Needs diff/patch/versioning API and protected-file policy | Canonical files are source of truth | `file_operation.schema.json` + rollback tests |
| 7 | Memory Service | Needs memory schema, recall policy, supersession rules, source references | Long-term learning and context rely on it | `memory.schema.json` + recall/supersession evals |
| 8 | Model Router | Upgraded in v0.4.5 but needs implementation tasks | Required for efficient multi-model delegation | Model routing implementation spec |
| 9 | Cost Governor | Still draft-level and tightly coupled to model routing/scanners | Prevents runaway LLM/API/scanner costs | `budget_policy.schema.json` + cost evals |
| 10 | Rollback and Recovery | Needs rollback metadata and per-action undo contracts | Mutating systems need recovery | `rollback_plan.schema.json` + rollback drill |
| 11 | Capability Registry / Dependency Graph | Needs manifest schema and dependency enforcement rules | Prevents foundation changes from toppling higher modules | `capability_manifest.schema.json` + dependency tests |
| 12 | Security Threat Model | Needs threat cases and red-team evals | Prompt injection and tool misuse are central risks | `threat_model.md` + red-team evals |
| 13 | Data Lifecycle and Privacy | Needs retention/export/delete/pause semantics | Companion memory and scanners will collect sensitive data | `data_retention_policy.schema.json` |
| 14 | Agent Constitution | Needs final behavior rules and enforcement points | Foundation behavioral contract for all modules | Constitution acceptance tests |
| 15 | Shadow Mode and Contract Testing | Needs replay harness design and golden trace format | Safe foundation changes require replay/testing | `golden_trace.schema.json` + harness spec |

## Can remain draft until after Foundation Gate

| Module | Why it can wait |
|---|---|
| Source Credibility and Rumor Protocol | Needed before Web Research and breaking alerts, but not before kernel contracts. |
| Proactive Intelligence | Blocked until memory, notifications, consent, model routing, and source credibility exist. |
| Scanner Modules | Blocked until Tool Broker, consent, source credibility, model routing, and cost controls exist. |
| Companion Layer | Blocked until memory, data lifecycle, user controls, and safety evals exist. |
| Skill Factory | Blocked until Tool Broker, Capability Registry, Code Workspace, and skill trust pipeline exist. |
| Self-Improving Coding Framework | Blocked until Code Workspace, contract tests, rollback, model routing, and approval gates exist. |
| Agent Interoperability | Important later; not required for the first vertical slice. |
| Autopilot Workflows | Blocked until almost everything else is stable. |

## Recommended next expansion order

```text
1. Execution Contract + Context Pack
2. Event Ledger / Observability
3. Consent and Permissions Ledger
4. Tool Broker
5. File Manager
6. Memory Service
7. Cost Governor
8. Rollback and Recovery
9. Capability Registry / Dependency Graph
10. Security Threat Model
11. Shadow Mode / Contract Testing
12. Orchestrator MVP
```

## Programming readiness verdict

Do not start broad product programming yet. It is safe to start implementation only for the first foundation slice after the Execution Contract, Context Pack, Event Ledger, Consent Ledger, Tool Broker, File Manager, Memory Service, Model Router, Cost Governor, and contract-test interfaces have implementation-ready specs.

The first code should be the kernel, schemas, event ledger, and test harness — not scanners, companion UX, skill creation, or self-improving code.
