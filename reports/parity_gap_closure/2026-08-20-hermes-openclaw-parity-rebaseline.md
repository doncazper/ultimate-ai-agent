# Queue V2 Q10 Hermes And OpenClaw Parity Rebaseline

Status: current-source, point-in-time gap audit; no runtime authority grant

- UAA inventory base: `commit:eaa89916c5b2198bb48d63219b59e3f2b07cbbc8`
- Inventory date: `2026-08-20`
- Canonical machine-readable ledger:
  `reports/parity_gap_closure/2026-08-20-hermes-openclaw-parity-rebaseline.json`
- Scope: compare current public source, identify only product-relevant UAA gaps,
  and route each gap without implementing it in Q10.

This report supersedes the July 22 convergence ledger only for current-source
comparison and owner routing. The July ledger remains an immutable historical
record of its earlier repository state.

## Pinned Comparison Sources

| Source | Exact revision | Commit time | Reproducible source view |
|---|---|---|---|
| Hermes Agent | `4a5b6dd4512a10c3c18da3e5b9e5c7fb681cbfbb` | `2026-08-20T14:07:53-05:00` | [Hermes tree at the audited revision](https://github.com/NousResearch/hermes-agent/tree/4a5b6dd4512a10c3c18da3e5b9e5c7fb681cbfbb) |
| OpenClaw | `15f33d9edc697cf879cce48e3a5f1f64e6493981` | `2026-08-21T03:16:22+08:00` | [OpenClaw tree at the audited revision](https://github.com/openclaw/openclaw/tree/15f33d9edc697cf879cce48e3a5f1f64e6493981) |

Source refs in the ledger resolve as
`<source-id>:<repository-relative-path>` against these exact revisions. The
canonical JSON records the complete audited path allowlist. UAA refs resolve
against the inventory-base commit above. Mutable repository home pages,
marketing claims, plans, mocks, and unmerged branches do not upgrade UAA truth.

## Method And Finite Boundary

The audit used the pinned default-branch source trees, UAA's current capability
map, current product truth, implementation files, focused tests, and Queue V2
owner contracts. A comparator feature becomes a UAA gap only when it supports
the local single-operator Founder Command Center direction. Each grouped gap
has exactly one terminal disposition:

- `close`: an accepted later Queue V2 item owns a bounded UAA-native slice;
- `defer`: the direction is useful, but an accepted dependency or exact
  authority gate must be satisfied first; or
- `intentionally_exclude`: the comparator behavior is not an accepted UAA
  parity target.

Q10 does not fix any gap. Upstream changes after the pinned revisions do not
reopen this task. The next comparison refresh occurs before Q31 or when an
accepted owner changes a recorded disposition.

## Current UAA Convergence

UAA is not starting from the July baseline. Current main already proves these
UAA-native foundations:

- durable goals and bounded, integrity-linked run events with cursor replay
  (`src/ultimate_ai_agent/core/runtime_gateway/goal_runtime.py`,
  `src/ultimate_ai_agent/core/runtime_gateway/run_events.py`,
  `tests/test_goal_runtime_durable_events.py`);
- macOS-first Setup Assistant lifecycle contracts and truthful diagnostics
  (`src/ultimate_ai_agent/core/macos_setup_assistant/lifecycle.py`,
  `tests/test_macos_setup_assistant.py`);
- reviewed memory plus rights-gated cited lexical knowledge retrieval
  (`src/ultimate_ai_agent/core/memory/workbench.py`,
  `docs/knowledge/KNOWLEDGE_DUMP.md`);
- verified offline Founder Loop backup and restore
  (`src/ultimate_ai_agent/core/storage/founder_loop_recovery.py`,
  `tests/test_founder_loop_recovery.py`);
- a backend-bound Today and Plan -> Action -> Decision -> Receipt product path
  (`apps/control-center/src/northstar/SecondarySurfaces.tsx`,
  `apps/control-center/src/northstar/WiredSurfaces.test.tsx`); and
- a durable system capability map and revision-bound evaluation lab
  (`src/ultimate_ai_agent/core/system_map/`, `tests/test_system_map.py`,
  `src/ultimate_ai_agent/core/evals/capability_lab.py`,
  `tests/test_capability_evaluation_lab.py`).

These are current UAA strengths, not claims that UAA matches the comparators'
broad provider, browser, connector, device, plugin, or autonomy surfaces.

## Gap Disposition Ledger

| Gap | Current UAA truth and bounded delta | Disposition | Later owner or boundary | Current-source evidence |
|---|---|---|---|---|
| `Q10-G01` cross-platform setup and recovery | `partial`: macOS-first lifecycle and diagnostics exist; comparator-wide cross-platform installation and unattended mutation are not UAA targets. | `intentionally_exclude` | `owner-ref:none-intentional`; macOS-first and no-setup-mutation boundaries | `hermes:README.md`; `openclaw:README.md`; `src/ultimate_ai_agent/core/macos_setup_assistant/lifecycle.py`; `tests/test_macos_setup_assistant.py` |
| `Q10-G02` tasks, projects, recurrence, dependencies, and boards | `partial`: durable goals and plan/action links exist; one complete Tasks and Boards model does not. | `close` | Q12 Tasks and missions; Q13 Boards | `hermes:web/src/pages/CronPage.tsx`; `openclaw:docs/automation/tasks.md`; `openclaw:docs/cli/workboard.md`; `src/ultimate_ai_agent/core/runtime_gateway/goal_runtime.py`; `src/ultimate_ai_agent/core/control_center/plans_to_actions.py` |
| `Q10-G03` durable task, run, event, and session recovery | `partial`: bounded event replay and safe-ref session search are proven; delegated mission recovery and end-user recovery UX remain incomplete. | `close` | Q12 durable missions; Q21 private dogfood | `hermes:gateway/session_state.py`; `hermes:tools/session_search_tool.py`; `openclaw:docs/automation/tasks.md`; `openclaw:docs/concepts/session-search.md`; `src/ultimate_ai_agent/core/runtime_gateway/run_events.py`; `tests/test_hermes_runtime_session_search.py` |
| `Q10-G04` reviewed memory, search, and cited knowledge | `partial`: reviewed memory and cited lexical retrieval exist; unified library lifecycle and cited chat context remain incomplete. | `close` | Q18 Knowledge Workbench | `hermes:tools/memory_tool.py`; `hermes:tools/session_search_tool.py`; `openclaw:docs/concepts/memory.md`; `openclaw:docs/concepts/session-search.md`; `src/ultimate_ai_agent/core/memory/workbench.py`; `docs/knowledge/KNOWLEDGE_DUMP.md` |
| `Q10-G05` reviewable self-improvement proposals | `planned`: UAA targets evidence-backed proposals and outcome receipts, not autonomous code or skill promotion. | `defer` | Q29 governed self-improvement | `hermes:README.md`; `hermes:tools/skill_manager_tool.py`; `openclaw:docs/tools/skills.md`; `docs/control_center/SKILL_WORKBENCH_DISCOVERY_AND_ADOPTION.md`; `docs/prompts/governed_self_improvement_intake.md` |
| `Q10-G06` exact scheduled briefing source refresh | `blocked`: the comparators support broad scheduled work; UAA's narrower target has background-job posture but no accepted exact worker authority lane. | `defer` | Q16 Today/Briefing; Q23 read-only sources; `authority-gate-ref:background-autonomy-scoped` | `hermes:cron/scheduler.py`; `hermes:web/src/pages/CronPage.tsx`; `openclaw:docs/automation/cron-jobs.md`; `openclaw:docs/automation/standing-orders.md`; `docs/runtime/UAA_HERMES_RUNTIME_BACKGROUND_JOBS.md` |
| `Q10-G07` messaging product and delivery lifecycle | `partial`: bounded local communications and Matrix evidence exist; broad channels and general send authority do not. | `defer` | Q20 Communications and Messenger | `hermes:README.md`; `hermes:gateway/platform_registry.py`; `openclaw:README.md`; `openclaw:docs/channels/index.md`; `docs/connectors/MESSENGER_MATRIX_ACCEPTANCE_PACKET.md` |
| `Q10-G08` exact read-only account and source connectors | `planned`: source-readiness metadata exists; live account data, provenance, and revocation adapters do not. | `defer` | Q23 exact read-only connector platform | `hermes:gateway/platform_registry.py`; `openclaw:README.md`; `openclaw:docs/channels/index.md`; `docs/control_center/route_status_manifest.json` |
| `Q10-G09` broad provider and model routing | `partial`: narrow exact-approved experiments and read-only routing evidence exist; standing credentials, broad fan-out, and provider-output authority are not parity targets. | `intentionally_exclude` | `owner-ref:none-intentional`; no-broad-provider boundary | `hermes:README.md`; `openclaw:README.md`; `src/ultimate_ai_agent/core/providers/invocation.py`; `tests/test_tiny_provider_invocation_lane.py` |
| `Q10-G10` tool-aware cognition and uncertainty | `partial`: governed capability metadata and decomposition proposals exist; ordinary chat familiarity and uncertainty behavior remains incomplete. | `close` | Q22 Tool-Aware Cognition | `hermes:README.md`; `hermes:tools/skill_manager_tool.py`; `openclaw:docs/tools/skills.md`; `docs/strategy/UAA_TOOL_AWARE_COGNITION_AND_CHAT_QUALITY_PLAN.md`; `src/ultimate_ai_agent/core/task_decomposition/proposals.py` |
| `Q10-G11` live browser control and general shell execution | `blocked`: UAA browser contracts remain inactive or exact-read-only; unrestricted browser and shell behavior are not accepted parity targets. | `intentionally_exclude` | `owner-ref:none-intentional`; no-unrestricted-browser and no-unrestricted-shell boundaries | `hermes:tools/browser_tool.py`; `openclaw:docs/tools/browser.md`; `openclaw:docs/gateway/sandboxing.md`; `docs/browser/GOVERNED_EXTERNAL_ACTIONS_QUEUE_01.md`; `docs/network/WEB_ACCESS_GATEWAY.md` |
| `Q10-G12` autonomous delegation, subagents, and managed worktrees | `blocked`: isolation and worktree posture are modeled, but broad autonomous delegation and worktree-derived authority are not UAA targets. | `intentionally_exclude` | `owner-ref:none-intentional`; no-broad-autonomy boundary | `hermes:README.md`; `hermes:tools/subagent_worktree.py`; `openclaw:docs/concepts/delegate-architecture.md`; `openclaw:docs/concepts/managed-worktrees.md`; `src/ultimate_ai_agent/core/runtime_gateway/subagent_isolation.py` |
| `Q10-G13` remote execution and device companion actions | `blocked`: remote and device capabilities remain maps/posture without execution. | `intentionally_exclude` | `owner-ref:none-intentional`; no-remote-execution and no-device-control boundaries | `hermes:README.md`; `openclaw:README.md`; `src/ultimate_ai_agent/core/runtime_gateway/remote_execution_posture.py`; `docs/runtime/UAA_HERMES_RUNTIME_REMOTE_EXECUTION_POSTURE.md` |
| `Q10-G14` complete local data backup, restore, and integrity | `partial`: Founder Loop offline snapshots are verified; complete-store migrations, retention, atomicity, and recovery are not yet unified. | `close` | Q11 shared local data platform | `hermes:README.md`; `openclaw:docs/cli/backup.md`; `src/ultimate_ai_agent/core/storage/founder_loop_recovery.py`; `tests/test_founder_loop_recovery.py` |
| `Q10-G15` readable cockpit and complete daily loop | `partial`: Q08 and Q09 improve Today and review transitions; Briefing sources, carry-forward, Weekly Review, and private dogfood remain incomplete. | `close` | Q16 Today/Briefing; Q21 Weekly Review/private trial | `hermes:README.md`; `openclaw:README.md`; `openclaw:docs/web/control-ui.md`; `apps/control-center/src/northstar/SecondarySurfaces.tsx`; `apps/control-center/src/northstar/WiredSurfaces.test.tsx` |
| `Q10-G16` plugin and skill marketplace installation/runtime import | `intentionally_absent`: UAA supports reviewable discovery metadata, not automatic marketplace runtime authority. | `intentionally_exclude` | `owner-ref:none-intentional`; no-plugin-runtime-import boundary | `hermes:tools/skill_manager_tool.py`; `openclaw:docs/tools/skills.md`; `docs/control_center/SKILL_WORKBENCH_DISCOVERY_AND_ADOPTION.md`; `docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md` |
| `Q10-G17` local calendar and source-artifact intake | `planned`: source readiness exists; complete local calendar and manual artifact triage products do not. | `close` | Q14 local Calendar; Q17 source-artifact workbench | `hermes:README.md`; `openclaw:README.md`; `openclaw:docs/channels/index.md`; `docs/control_center/UI_WIRING_REPORT.md`; `docs/control_center/route_status_manifest.json` |
| `Q10-G18` publishing proposals and dry-run evidence | `planned`: the accepted target is proposals and dry-run receipts only; live publishing remains excluded. | `defer` | Q30 publishing proposal/dry-run only | `hermes:README.md`; `hermes:gateway/platform_registry.py`; `openclaw:README.md`; `openclaw:docs/channels/index.md`; `docs/browser/GOVERNED_EXTERNAL_ACTIONS_QUEUE_01.md` |

Disposition totals are finite: 7 `close`, 5 `defer`, and 6
`intentionally_exclude`. No row is `unknown`, no gap is bundled into Q10, and
no open-ended parity score is asserted.

## Owner Routing

- Q11 owns complete shared local data integrity and recovery.
- Q12 and Q13 own Tasks, durable missions, and Board projections.
- Q14 and Q17 own the local Calendar and manual source-artifact products.
- Q16 and Q21 own the remaining readable daily/weekly loop and private proof.
- Q18 owns knowledge-library lifecycle and cited chat context.
- Q20 owns the bounded communications product while broad sends stay blocked.
- Q22 owns tool-aware cognition without authority escalation.
- Q23 owns exact read-only source adapters without connector writes or standing
  account authority.
- Q29 owns reviewable improvement proposals without self-modifying code.
- Q30 owns publishing proposals and dry-run receipts without live publishing.

Generic scheduler promotion has no implicit owner: it remains behind
`authority-gate-ref:background-autonomy-scoped`. Intentional exclusions have
`owner-ref:none-intentional` so they cannot silently re-enter the queue as
parity debt.

## Authority And Product-Truth Result

This audit grants no runtime model or broad provider calls, live unrestricted
web or browser execution, connector writes or broad message sends,
unrestricted shell or remote execution, plugin runtime import, unreviewed skill
installation, background autonomy, public beta, public release, production
readiness, or production authority.

The Q10 acceptance result is therefore documentation and verifier evidence
only: both comparator sources are exact-revision pinned, every grouped gap has
current source and UAA evidence, every gap has one permitted disposition, and
every non-excluded gap is routed to a later owner or explicit authority gate.
