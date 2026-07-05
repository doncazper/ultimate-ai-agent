# UAA Hermes Runtime Adoption Prompt Pack

Status: stored execution prompts, not runtime authority

Purpose: turn the Hermes Agent scan into a disciplined UAA-native adoption
program. The goal is not to copy Hermes or make UAA a Hermes skin. The goal is
to make UAA a governed operator control center that can supervise Hermes,
future Codex, Claude, local, and other runtimes while preserving UAA's authority
spine, proof posture, and local-first product direction.

Use the wrapper prompt:

```bash
docs/prompts/hermes_runtime_adoption/00_execute_all_45_review_fix_merge_harden.prompt.md
```

The wrapper executes every phase below as its own merge-gated lane. Each phase
must inspect UAA first, implement a UAA-native slice only when safe, review,
fix, harden, test, commit, push, open a PR, merge only when green, sync `main`,
and continue.

## Reference Boundary

Hermes is a read-only reference and optional governed runtime target. Do not
copy Hermes code, import Hermes packages, or let Hermes bypass UAA policy.

UAA owns:

- operator authority and approvals;
- Trust, Action Inbox, receipts, Evidence, Proof, and Memory governance;
- route side-effect classification, OpenAPI/API manifest truth, and CLI/API
  parity;
- redaction, safe refs, rollback posture, and product-language honesty.

Hermes may provide, when explicitly configured and approved:

- a runtime endpoint to inspect;
- capability, model, skill, toolset, session, run, and event metadata;
- delegated task execution only through UAA-approved exact lanes.

## Phase Order

| Phase | Borrowed Pattern | Prompt Volume | Default Posture |
|---:|---|---|---|
| 01 | Runtime Delegation Adapter | `01_critical_runtime_delegation_and_capabilities.prompt.md` | read-only first |
| 02 | Capabilities discovery endpoint pattern | `01_critical_runtime_delegation_and_capabilities.prompt.md` | read-only |
| 03 | Runs API with events, stop, approval | `01_critical_runtime_delegation_and_capabilities.prompt.md` | read/proposal first |
| 04 | Approval bridge | `01_critical_runtime_delegation_and_capabilities.prompt.md` | exact approval only |
| 05 | Streaming tool progress | `01_critical_runtime_delegation_and_capabilities.prompt.md` | read-only event ingest |
| 06 | Profiles as isolated agents | `01_critical_runtime_delegation_and_capabilities.prompt.md` | metadata/readiness |
| 07 | Model/provider catalog UX | `01_critical_runtime_delegation_and_capabilities.prompt.md` | readiness, no secret exposure |
| 08 | Main vs auxiliary model slots | `01_critical_runtime_delegation_and_capabilities.prompt.md` | planning/config posture |
| 09 | Toolsets | `01_critical_runtime_delegation_and_capabilities.prompt.md` | capability map |
| 10 | Tool registry with availability checks | `02_tools_memory_context_and_rollback.prompt.md` | capability map |
| 11 | Bounded memory design | `02_tools_memory_context_and_rollback.prompt.md` | governed review |
| 12 | Session search separate from memory | `02_tools_memory_context_and_rollback.prompt.md` | safe refs |
| 13 | Progressive-disclosure skills | `02_tools_memory_context_and_rollback.prompt.md` | metadata/read-only |
| 14 | Skill write approval gate | `02_tools_memory_context_and_rollback.prompt.md` | approval required |
| 15 | Skill bundles | `02_tools_memory_context_and_rollback.prompt.md` | proposal/read-only first |
| 16 | Context references | `02_tools_memory_context_and_rollback.prompt.md` | safe refs only |
| 17 | Sensitive path blocking for context refs | `02_tools_memory_context_and_rollback.prompt.md` | mandatory guard |
| 18 | Checkpoint / rollback shadow store | `02_tools_memory_context_and_rollback.prompt.md` | exact mutation lanes only |
| 19 | Session lineage and forks | `03_orchestration_coding_and_runtime_safety.prompt.md` | durable read model |
| 20 | Mixture-of-Agents as virtual provider | `03_orchestration_coding_and_runtime_safety.prompt.md` | proposal/readiness |
| 21 | Desktop coding project model | `03_orchestration_coding_and_runtime_safety.prompt.md` | coding cockpit |
| 22 | Live model usage/cost analytics | `03_orchestration_coding_and_runtime_safety.prompt.md` | redacted accounting |
| 23 | Prompt stability tiers | `03_orchestration_coding_and_runtime_safety.prompt.md` | contract/read model |
| 24 | Context compression + budget pressure | `03_orchestration_coding_and_runtime_safety.prompt.md` | proposal/readiness |
| 25 | Hardline command blocklist floor | `03_orchestration_coding_and_runtime_safety.prompt.md` | always-on deny floor |
| 26 | Fail-closed approval timeouts | `03_orchestration_coding_and_runtime_safety.prompt.md` | mandatory guard |
| 27 | Managed scope / admin-pinned config | `03_orchestration_coding_and_runtime_safety.prompt.md` | local policy profile |
| 28 | Doctor/setup diagnostics | `04_operator_surfaces_extensions_and_diagnostics.prompt.md` | inspect-only |
| 29 | Gateway/multi-surface continuity | `04_operator_surfaces_extensions_and_diagnostics.prompt.md` | state visibility |
| 30 | MCP catalog with filtering | `04_operator_surfaces_extensions_and_diagnostics.prompt.md` | metadata/read-only |
| 31 | Background job model | `04_operator_surfaces_extensions_and_diagnostics.prompt.md` | proposal/approval |
| 32 | Subagent isolation model | `04_operator_surfaces_extensions_and_diagnostics.prompt.md` | delegated posture |
| 33 | Worktree-per-agent pattern | `04_operator_surfaces_extensions_and_diagnostics.prompt.md` | read/proposal first |
| 34 | LSP semantic diagnostics | `04_operator_surfaces_extensions_and_diagnostics.prompt.md` | evidence-only |
| 35 | Right preview rail | `04_operator_surfaces_extensions_and_diagnostics.prompt.md` | UI over backend refs |
| 36 | Slash command registry | `04_operator_surfaces_extensions_and_diagnostics.prompt.md` | centrally classified |
| 37 | Interrupt / redirect current work | `05_advanced_lanes_and_final_report.prompt.md` | run control lane |
| 38 | Verbose/details toggle | `05_advanced_lanes_and_final_report.prompt.md` | redacted logging |
| 39 | Tool/result classification | `05_advanced_lanes_and_final_report.prompt.md` | evidence taxonomy |
| 40 | Trajectory/eval capture | `05_advanced_lanes_and_final_report.prompt.md` | parity evidence |
| 41 | Voice/media handling | `05_advanced_lanes_and_final_report.prompt.md` | future posture |
| 42 | Messaging platform gateway | `05_advanced_lanes_and_final_report.prompt.md` | future posture |
| 43 | Cloud/remote execution backend abstraction | `05_advanced_lanes_and_final_report.prompt.md` | blocked/readiness |
| 44 | Plugin architecture | `05_advanced_lanes_and_final_report.prompt.md` | metadata first |
| 45 | Agent-created skills marketplace flow | `05_advanced_lanes_and_final_report.prompt.md` | reviewed UAA adaptation |

## Required Final Report

The wrapper requires a final Markdown report under
`reports/hermes_runtime_adoption/` with:

- phases completed and phases blocked;
- PR URLs and merge SHAs;
- files changed per phase;
- tests/verifiers run per phase;
- hardening issues found and fixed;
- known gaps and risk ranking;
- authority promoted, if any, by exact lane;
- authority still blocked;
- Hermes patterns borrowed as UAA-native designs;
- Hermes patterns explicitly not borrowed;
- recommendations and next exact PR lanes.

