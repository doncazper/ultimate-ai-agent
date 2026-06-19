# Roadmap Docs

Status: active
Current through: v0.100.0
Purpose: Entry point for active roadmap docs and historical roadmap references.

Current roadmap sources of truth:

```text
docs/canonical/09_roadmap.md
docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md
docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md
docs/kanban/current_board.md
```

Active roadmap support docs:

```text
docs/roadmap/MILESTONE_CHARTERS.md
docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md
docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md
docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md
docs/roadmap/M61_M100_ROADMAP.md
docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md
docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md
docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md
docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md
docs/roadmap/ECOSYSTEM_WATCHLIST.md
docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md
```

Historical roadmap snapshots live under `docs/roadmap/archive/` or
`docs/archive/roadmap_snapshots/` when they are no longer required at their
original paths.

`docs/roadmap/NEXT_SEQUENCE_v0_17_5.md` remains in place for compatibility with
active verifier and Foundation Gate checks, but it is a historical roadmap
projection and not the current roadmap source of truth.

M25 is implemented/hardened. M26 is implemented/released by v0.30.0 as deterministic local grounded recall/context-pack contracts and hardened by v0.30.1 for source_ref/source_kind consistency. M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. v0.31.1 is docs-only README polish baseline normalization. M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion policy-only contracts. M29 is implemented/released by v0.33.0 as Agent Task Planning Engine. M30-M33 are implemented/released. v0.37.4 supersedes the old active post-M33 projection, v0.38.0 implements M34 Broader File Capability Review as planning/docs/verifier only, v0.39.0 implements M35 Safe File Review Workflow Contracts, v0.40.0 implements M36 CCC File Review Surface, Review-Only, v0.40.1 hardens M36 read-only surface safety, v0.41.0 implements M37 Review Approval Capture, Review-Only Persistence, v0.42.0 implements M38 Safe Context Proposal From Approved Review, v0.43.0 implements M39 CCC Context Proposal Surface, v0.44.0 implements M40 Context Handoff Approval, No Injection, v0.45.0 implements M41 Local Prototype Safety Freeze, v0.46.0 implements M42 Mobile Companion Product Contract Refresh, v0.47.0 implements M43 Mobile API Boundary, Read-Only, v0.48.0 implements M44 CCC iOS Skeleton, No Authority, v0.48.1 hardens the M44 verifier allowance, v0.49.0 implements M45 CCC iOS Local Read-Only Connection, v0.50.0 implements M46 iOS Review/Receipt Read-Only Surfaces, v0.51.0 implements M47 TestFlight Pipeline, Internal Only, v0.52.0 implements M48 First Internal TestFlight Build, v0.53.0 implements M49 Mobile Review Approval Capture, v0.54.0 implements M50 Mobile Approval Audit Hardening, v0.55.0 implements M51 OpenWebUI Bridge Adapter Pilot, v0.56.0 implements M52 OpenWebUI Safe Conversation Surface, v0.57.0 implements M53 Controlled Tool Expansion Review, v0.58.0 implements M54 Safe Media Metadata Inspector, v0.59.0 implements M55 Redacted Observability Export, v0.60.0 implements M56 Agent Eval Regression Harness, v0.61.0 implements M57 Runtime Sandbox Architecture Review, v0.62.0 implements M58 Dry-Run Execution Audit Harness, v0.63.0 implements M59 Public GitHub Readiness as review-only public-readiness contracts, v0.64.0 implements M60 Local Developer Beta Freeze, v0.65.0 implements M61 Autonomy Mode Charter + Authority Levels, v0.66.0 implements M62 Scoped Autonomy Session Contracts, v0.67.0 implements M63 Autonomy Policy Engine v1, v0.68.0 implements M64 Autonomous Plan Simulator, v0.69.0 implements M65 Autonomy Audit + Replay Viewer, v0.70.0 implements M66 Scoped Approval Bundles, v0.71.0 implements M67 Revocation + Kill Switch, v0.72.0 implements M68 Autonomy Risk Classifier, v0.73.0 implements M69 Low-Risk Autonomous Dry Run, v0.74.0 implements M70 Autonomy Foundation Freeze, v0.75.0 implements M71 Network Tool Contract Review, v0.76.0 implements M72 Read-Only HTTP Fetch Tool, Allowlisted, v0.77.0 implements M73 Browser Automation Contract Review, v0.78.0 implements M74 Browser Observe-Only Adapter, v0.79.0 implements M75 Browser Action Dry-Run Planner, v0.80.0 implements M76 OpenWebUI Runtime Bridge v1, v0.81.0 implements M77 OpenWebUI Safe Handoff Execution, v0.82.0 implements M78 Plugin Manifest Security Model, v0.83.0 implements M79 Plugin Install Review, Disabled by Default, v0.84.0 implements M80 Network/Browser/OpenWebUI Hardening Freeze, v0.84.1 repairs M80 active currentness wording, v0.85.0 implements M81 Runtime Sandbox Spec, v0.86.0 implements M82 Command Proposal Contracts, v0.87.0 implements M83 Shell Dry-Run Classifier, v0.88.0 implements M84 Sandboxed Echo/No-Op Command, v0.89.0 implements M85 Read-Only Command Allowlist, v0.90.0 implements M86 Shell Approval Gate v1, v0.91.0 implements M87 Sandboxed Command Audit Replay, v0.92.0 implements M88 Mutating Command Proposal, No Execution, v0.93.0 implements M89 Emergency Stop + Process Kill Safety, v0.94.0 implements M90 Shell/Subprocess Hardening Freeze, v0.95.0 implements M91 Autonomous Tool Execution Contract, v0.96.0 implements M92 Low-Risk Tool Autonomy, Single Session, v0.97.0 implements M93 Multi-Tool Dry-Run to Real Run Promotion, v0.98.0 implements M94 Autonomous Browser Clicks, Low-Risk Only, v0.99.0 implements M95 Network Tool Expansion, Authless Only, v1.0.0 implements M96 Plugin Execution Sandbox, No External Plugins, v1.1.0 implements M97 Recurring Automation Contracts, and v1.2.0 implements M98 Scoped Recurring Low-Risk Automation. M99 is implemented/released by v1.3.0 as Autonomy v1 Safety Freeze, M100 is implemented/released by v1.4.0 as Mobile Permission Model v1, and v1.4.1 adds post-M100 review plus M101-M150 planned/provisional roadmap reconciliation. Checkpoint M104 is implemented/released as Notification Planning, No Push Execution, Checkpoint M105 is implemented/released as Background Task Contract, No Execution, Checkpoint M106 is implemented/released as Mobile Background Read-Only Status Sync, Checkpoint M107 is implemented/released as Mobile Approval Renewal UX, Checkpoint M108 is implemented/released as Mobile Kill Switch + Revocation, Checkpoint M109 is implemented/released as Mobile Sensor Audit Ledger, Checkpoint M110 is implemented/released as Mobile Sensor Hardening Freeze, Checkpoint M111 is implemented/released as Production Threat Model, Checkpoint M112 is implemented/released as User/Workspace Identity Model, Checkpoint M113 is implemented/released as Secrets Boundary + Credential Vault Contract, Checkpoint M114 is implemented/released as Account Connector Contract Review, Checkpoint M115 is implemented/released as Production Audit Retention Policy, Checkpoint M116 is implemented/released as Role-Based Authority Model, Checkpoint M117 is implemented/released as Remote Agent Coordination Contract, Checkpoint M118 is implemented/released as Deployment Mode Matrix, Checkpoint M119 is implemented/released as Production Red-Team Harness, Checkpoint M120 is implemented/released as Production Authority Readiness Review, Checkpoint M121 is implemented/released as Email Connector Contract Refresh, Checkpoint M122 is implemented/released as Calendar Connector Contract Refresh, Checkpoint M123 is implemented/released as Contacts Connector Contract Refresh, Checkpoint M124 is implemented/released as Messages Connector Contract Review, Checkpoint M125 is implemented/released as Connector Read-Only Runtime, Checkpoint M126 is implemented/released as Connector Approval Capture, Checkpoint M127 is implemented/released as Connector Write Dry-Run Planner, Checkpoint M128 is implemented/released as Connector Write Execution, Low-Risk Only, Checkpoint M129 is implemented/released as Connector Audit + Revocation Hardening, Checkpoint M130 is implemented/released as Connector Safety Freeze, Checkpoint M131 is implemented/released as Autonomy Mode 4, Scoped Work Session, Checkpoint M132 is implemented/released as Autonomy Mode 5, Trusted Recurring Workflow, Checkpoint M133 is implemented/released as Long-Running Task Supervisor, Checkpoint M134 is implemented/released as Human Checkpoint Scheduling, Checkpoint M135 is implemented/released as Autonomous Recovery Planner, Checkpoint M136 is implemented/released as Cross-Tool Dependency Execution, Checkpoint M137 is implemented/released as Autonomous Browser + Connector Combined Workflows, Checkpoint M138 is implemented/released as Autonomous Error Handling Guardrails, Checkpoint M139 is implemented/released as Autonomy Abuse/Loop Detection, Checkpoint M142 remains implemented/released as Alpha Privacy Review. Checkpoint M141 remains implemented/released as Multi-User Product Boundary. Checkpoint M140 remains implemented/released as Higher-Autonomy Red-Team Freeze. Checkpoint M143 remains implemented/released as Alpha UI and App Readiness. Checkpoint M145 is implemented/released as Enterprise/Pro Safety Modes under the v1.7.2 checkpoint baseline. Checkpoint M144 remains implemented/released as Plugin Marketplace Policy Draft. Checkpoint M149 is implemented/released as Alpha Release Candidate Freeze. M150 is implemented/released as Ultimate AI Agent v1.2.0-alpha target acceptance; beta begins later after alpha UI and supporting safety/product work are reviewed and promoted.

Current M150 alpha note: Checkpoint M149 is implemented/released as
Alpha Release Candidate Freeze. M150 is implemented/released as Ultimate AI
Agent v1.2.0-alpha target acceptance; beta remains future.

Post-M150 accepted checkpoint note: M151 is the Local OpenWebUI Test Shell
milestone. M152-M159 define the local model management contract lane, M160-M165
complete the scoped local model live lane, M166 is the exact-scope local model
production-readiness gate, and M167 hardens that gate with reviewed live
evidence. The latest accepted repository checkpoint tag is `checkpoint-m168`;
the latest accepted local model lane checkpoint tags remain `checkpoint-m166`
and `checkpoint-m167`. The product/package baseline is v0.100.0.

Active program note: M168 starts the Operator Runtime Excellence currentness and
product-truth lane; P0 repair work through UAA-P0-007 adds public security
posture, local model evidence scaffolding, local model smoke scaffolding,
performance baseline reporting, and the Control Center operator-shell gap map.
External benchmark and peer-console context is product-shaping evidence only,
not an implementation dependency or authority source. This work adds no
provider call, tool execution, shell/subprocess execution, unrestricted network
or browser automation, connector writes, plugin runtime import, mobile control,
memory write, context injection, external distribution, raw prompt logging, raw
response logging, raw provider payload logging, beta release, or production
authority.

Documentation organization and historical-roadmap handling rules live in
`docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md`.
