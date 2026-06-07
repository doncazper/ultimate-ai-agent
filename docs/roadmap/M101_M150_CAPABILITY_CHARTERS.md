# M101-M150 Capability Charters

Status: Active roadmap maintained through v1.7.1 after the accepted M103
baseline and post-M103 versioning repair.

M101 is implemented/released as Mobile Sensor Contract Review. M102 is
implemented/released as Location Sensor, Off by Default. M103 is
implemented/released as Camera/Photos Metadata-Only Contract. v1.7.1 repairs
the post-M100 versioning policy only. M104-M150 remain planned/provisional.
Future work must continue the authority-tier model:

Capability exists -> disabled by default -> dry-run first -> limited allowlist
-> explicit approval -> scoped autonomy window -> audit/replay -> revocation ->
only then broader autonomy.

There is no global "be autonomous" switch, no jump from Mode 0 to broad
autonomy, and no production authority in this roadmap. Every milestone remains
planned/provisional until implemented, validated, pushed, strictly reviewed, and
accepted Green.

## Versioning Policy

The already-pushed v1.0.0 through v1.7.0 tags remain immutable historical
internal milestone tags. They are not the public product alpha/beta channel.
Starting after v1.7.1, future M104-M149 conveyor snapshots use incremental
v1.7.x internal tags so the version line stays boring and reviewable. M150 is
the first public alpha target: **v1.0.0-alpha**. Beta begins only after the
alpha UI and supporting safety/product work are reviewed, accepted, and
explicitly promoted by a later roadmap patch. Do not rewrite, move, or reuse
existing tags.

| Internal snapshot | Product target | Milestone | Title | Status |
| --- | --- | --- | --- | --- |
| v1.5.0 | pre-alpha internal | M101 | Mobile Sensor Contract Review | Implemented/released |
| v1.6.0 | pre-alpha internal | M102 | Location Sensor, Off by Default | Implemented/released |
| v1.7.0 | pre-alpha internal | M103 | Camera/Photos Metadata-Only Contract | Implemented/released |
| v1.7.2 | pre-alpha | M104 | Notification Planning, No Push Execution | Planned/provisional |
| v1.7.3 | pre-alpha | M105 | Background Task Contract, No Execution | Planned/provisional |
| v1.7.4 | pre-alpha | M106 | Mobile Background Read-Only Status Sync | Planned/provisional |
| v1.7.5 | pre-alpha | M107 | Mobile Approval Renewal UX | Planned/provisional |
| v1.7.6 | pre-alpha | M108 | Mobile Kill Switch + Revocation | Planned/provisional |
| v1.7.7 | pre-alpha | M109 | Mobile Sensor Audit Ledger | Planned/provisional |
| v1.7.8 | pre-alpha | M110 | Mobile Sensor Hardening Freeze | Planned/provisional |
| v1.7.9 | pre-alpha | M111 | Production Threat Model | Planned/provisional |
| v1.7.10 | pre-alpha | M112 | User/Workspace Identity Model | Planned/provisional |
| v1.7.11 | pre-alpha | M113 | Secrets Boundary + Credential Vault Contract | Planned/provisional |
| v1.7.12 | pre-alpha | M114 | Account Connector Contract Review | Planned/provisional |
| v1.7.13 | pre-alpha | M115 | Production Audit Retention Policy | Planned/provisional |
| v1.7.14 | pre-alpha | M116 | Role-Based Authority Model | Planned/provisional |
| v1.7.15 | pre-alpha | M117 | Remote Agent Coordination Contract | Planned/provisional |
| v1.7.16 | pre-alpha | M118 | Deployment Mode Matrix | Planned/provisional |
| v1.7.17 | pre-alpha | M119 | Production Red-Team Harness | Planned/provisional |
| v1.7.18 | pre-alpha | M120 | Production Authority Readiness Review | Planned/provisional |
| v1.7.19 | pre-alpha | M121 | Email Connector Contract Refresh | Planned/provisional |
| v1.7.20 | pre-alpha | M122 | Calendar Connector Contract Refresh | Planned/provisional |
| v1.7.21 | pre-alpha | M123 | Contacts Connector Contract Refresh | Planned/provisional |
| v1.7.22 | pre-alpha | M124 | Messages Connector Contract Review | Planned/provisional |
| v1.7.23 | pre-alpha | M125 | Connector Read-Only Runtime | Planned/provisional |
| v1.7.24 | pre-alpha | M126 | Connector Approval Capture | Planned/provisional |
| v1.7.25 | pre-alpha | M127 | Connector Write Dry-Run Planner | Planned/provisional |
| v1.7.26 | pre-alpha | M128 | Connector Write Execution, Low-Risk Only | Planned/provisional |
| v1.7.27 | pre-alpha | M129 | Connector Audit + Revocation Hardening | Planned/provisional |
| v1.7.28 | pre-alpha | M130 | Connector Safety Freeze | Planned/provisional |
| v1.7.29 | pre-alpha | M131 | Autonomy Mode 4, Scoped Work Session | Planned/provisional |
| v1.7.30 | pre-alpha | M132 | Autonomy Mode 5, Trusted Recurring Workflow | Planned/provisional |
| v1.7.31 | pre-alpha | M133 | Long-Running Task Supervisor | Planned/provisional |
| v1.7.32 | pre-alpha | M134 | Human Checkpoint Scheduling | Planned/provisional |
| v1.7.33 | pre-alpha | M135 | Autonomous Recovery Planner | Planned/provisional |
| v1.7.34 | pre-alpha | M136 | Cross-Tool Dependency Execution | Planned/provisional |
| v1.7.35 | pre-alpha | M137 | Autonomous Browser + Connector Combined Workflows | Planned/provisional |
| v1.7.36 | pre-alpha | M138 | Autonomous Error Handling Guardrails | Planned/provisional |
| v1.7.37 | pre-alpha | M139 | Autonomy Abuse/Loop Detection | Planned/provisional |
| v1.7.38 | pre-alpha | M140 | Higher-Autonomy Red-Team Freeze | Planned/provisional |
| v1.7.39 | pre-alpha | M141 | Multi-User Product Boundary | Planned/provisional |
| v1.7.40 | pre-alpha | M142 | Alpha Privacy Review | Planned/provisional |
| v1.7.41 | pre-alpha | M143 | Alpha UI and App Readiness | Planned/provisional |
| v1.7.42 | pre-alpha | M144 | Plugin Marketplace Policy Draft | Planned/provisional |
| v1.7.43 | pre-alpha | M145 | Enterprise/Pro Safety Modes | Planned/provisional |
| v1.7.44 | pre-alpha | M146 | Billing/Plan Boundary, If Needed | Planned/provisional |
| v1.7.45 | pre-alpha | M147 | Public Docs + Wiki Readiness | Planned/provisional |
| v1.7.46 | pre-alpha | M148 | External Security Review | Planned/provisional |
| v1.7.47 | pre-alpha | M149 | Alpha Release Candidate Freeze | Planned/provisional |
| v1.7.48 | v1.0.0-alpha | M150 | Ultimate AI Agent v1.0.0-alpha | Planned/provisional |

## Shared Non-Goals

Until a future reviewed milestone explicitly implements and accepts a narrower
capability, M101-M150 must not add production authority, broad unsandboxed
autonomy, mobile sensor runtime, runtime permission prompts, native permission
requests, background collection, push execution, arbitrary shell/subprocess,
unrestricted network tools, authenticated account actions, browser forms,
purchases, downloads, external plugin execution, automatic context injection,
no unreviewed memory writes, raw prompt/provider payload exposure, raw file export,
full-file reads, credentials/cookie handling, remote execution, backend routes,
Control Center controls, dependencies, or implementation beyond the target
milestone.

## Planning Notes

M101-M110 stage mobile sensor and mobile-control work from contract review to a
hardening freeze. M111-M120 stage production-readiness contracts without
granting production authority. M121-M130 stage connector safety from contract
refresh through low-risk write execution and freeze. M131-M140 stage higher
autonomy only after prior scoped, auditable safety foundations. M141-M150 stage
multi-user, alpha UI/product readiness, marketplace policy, billing boundaries,
public docs, security review, alpha release candidate freeze, and the
v1.0.0-alpha target.

No M151+ extension is required by the v1.7.1 versioning repair. Beta begins
after the alpha UI and other alpha findings are ironed out through later
reviewed roadmap promotion. If future review finds missed M1-M100 work that
should not displace M101-M150, add a separate planned/provisional M151+
extension roadmap through a reviewed patch.
