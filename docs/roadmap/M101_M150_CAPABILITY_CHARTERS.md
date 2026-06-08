# M101-M150 Capability Charters

Status: Active roadmap maintained through Checkpoint M118 after the accepted
v1.7.2 post-M103 versioning repair follow-up.

M101 is implemented/released as Mobile Sensor Contract Review. M102 is
implemented/released as Location Sensor, Off by Default. M103 is
implemented/released as Camera/Photos Metadata-Only Contract. Checkpoint M104
is implemented/released as Notification Planning, No Push Execution. Checkpoint
M105 is implemented/released as Background Task Contract, No Execution. v1.7.2
is the current product baseline. Checkpoint M106 is implemented/released as
Mobile Background Read-Only Status Sync. Checkpoint M107 is implemented/released
as Mobile Approval Renewal UX. Checkpoint M108 is implemented/released as Mobile
Kill Switch + Revocation. Checkpoint M109 is implemented/released as Mobile
Sensor Audit Ledger. Checkpoint M110 is implemented/released as Mobile Sensor
Hardening Freeze. Checkpoint M111 is implemented/released as Production Threat
Model. Checkpoint M112 is implemented/released as User/Workspace Identity
Model. Checkpoint M113 is implemented/released as Secrets Boundary +
Credential Vault Contract. Checkpoint M114 is implemented/released as Account
Connector Contract Review. Checkpoint M115 is implemented/released as
Production Audit Retention Policy. Checkpoint M116 is implemented/released as
Role-Based Authority Model. Checkpoint M117 is implemented/released as Remote
Agent Coordination Contract. Checkpoint M118 is implemented/released as
Deployment Mode Matrix. M119-M150 remain planned/provisional.
Future work must continue the authority-tier model:

Capability exists -> disabled by default -> dry-run first -> limited allowlist
-> explicit approval -> scoped autonomy window -> audit/replay -> revocation ->
only then broader autonomy.

There is no global "be autonomous" switch, no jump from Mode 0 to broad
autonomy, no broad unsandboxed autonomy, and no production authority in this
roadmap. Every milestone remains planned/provisional until implemented,
validated, pushed, strictly reviewed, and accepted Green.

## Versioning Policy

The already-pushed v1.0.0 through v1.7.1 tags remain immutable historical
internal milestone tags. They are not the public product alpha/beta channel.
Starting after v1.7.2, M104-M149 conveyor milestones use checkpoint
labels instead of product SemVer tags. M150 is the next product release target:
**v1.0.0-alpha**. Beta begins only after the alpha UI and supporting
safety/product work are reviewed, accepted, and explicitly promoted by a later
roadmap patch. Do not rewrite, move, or reuse existing tags.

| Checkpoint | Product target | Milestone | Title | Status |
| --- | --- | --- | --- | --- |
| v1.5.0 | pre-alpha internal | M101 | Mobile Sensor Contract Review | Implemented/released |
| v1.6.0 | pre-alpha internal | M102 | Location Sensor, Off by Default | Implemented/released |
| v1.7.0 | pre-alpha internal | M103 | Camera/Photos Metadata-Only Contract | Implemented/released |
| Checkpoint M104 | pre-alpha checkpoint | M104 | Notification Planning, No Push Execution | Implemented/released |
| Checkpoint M105 | pre-alpha checkpoint | M105 | Background Task Contract, No Execution | Implemented/released |
| Checkpoint M106 | pre-alpha checkpoint | M106 | Mobile Background Read-Only Status Sync | Implemented/released |
| Checkpoint M107 | pre-alpha checkpoint | M107 | Mobile Approval Renewal UX | Implemented/released |
| Checkpoint M108 | pre-alpha checkpoint | M108 | Mobile Kill Switch + Revocation | Implemented/released |
| Checkpoint M109 | pre-alpha checkpoint | M109 | Mobile Sensor Audit Ledger | Implemented/released |
| Checkpoint M110 | pre-alpha checkpoint | M110 | Mobile Sensor Hardening Freeze | Implemented/released |
| Checkpoint M111 | pre-alpha checkpoint | M111 | Production Threat Model | Implemented/released |
| Checkpoint M112 | pre-alpha checkpoint | M112 | User/Workspace Identity Model | Implemented/released |
| Checkpoint M113 | pre-alpha checkpoint | M113 | Secrets Boundary + Credential Vault Contract | Implemented/released |
| Checkpoint M114 | pre-alpha checkpoint | M114 | Account Connector Contract Review | Implemented/released |
| Checkpoint M115 | pre-alpha checkpoint | M115 | Production Audit Retention Policy | Implemented/released |
| Checkpoint M116 | pre-alpha checkpoint | M116 | Role-Based Authority Model | Implemented/released |
| Checkpoint M117 | pre-alpha checkpoint | M117 | Remote Agent Coordination Contract | Implemented/released |
| Checkpoint M118 | pre-alpha checkpoint | M118 | Deployment Mode Matrix | Implemented/released |
| Checkpoint M119 | pre-alpha checkpoint | M119 | Production Red-Team Harness | Planned/provisional |
| Checkpoint M120 | pre-alpha checkpoint | M120 | Production Authority Readiness Review | Planned/provisional |
| Checkpoint M121 | pre-alpha checkpoint | M121 | Email Connector Contract Refresh | Planned/provisional |
| Checkpoint M122 | pre-alpha checkpoint | M122 | Calendar Connector Contract Refresh | Planned/provisional |
| Checkpoint M123 | pre-alpha checkpoint | M123 | Contacts Connector Contract Refresh | Planned/provisional |
| Checkpoint M124 | pre-alpha checkpoint | M124 | Messages Connector Contract Review | Planned/provisional |
| Checkpoint M125 | pre-alpha checkpoint | M125 | Connector Read-Only Runtime | Planned/provisional |
| Checkpoint M126 | pre-alpha checkpoint | M126 | Connector Approval Capture | Planned/provisional |
| Checkpoint M127 | pre-alpha checkpoint | M127 | Connector Write Dry-Run Planner | Planned/provisional |
| Checkpoint M128 | pre-alpha checkpoint | M128 | Connector Write Execution, Low-Risk Only | Planned/provisional |
| Checkpoint M129 | pre-alpha checkpoint | M129 | Connector Audit + Revocation Hardening | Planned/provisional |
| Checkpoint M130 | pre-alpha checkpoint | M130 | Connector Safety Freeze | Planned/provisional |
| Checkpoint M131 | pre-alpha checkpoint | M131 | Autonomy Mode 4, Scoped Work Session | Planned/provisional |
| Checkpoint M132 | pre-alpha checkpoint | M132 | Autonomy Mode 5, Trusted Recurring Workflow | Planned/provisional |
| Checkpoint M133 | pre-alpha checkpoint | M133 | Long-Running Task Supervisor | Planned/provisional |
| Checkpoint M134 | pre-alpha checkpoint | M134 | Human Checkpoint Scheduling | Planned/provisional |
| Checkpoint M135 | pre-alpha checkpoint | M135 | Autonomous Recovery Planner | Planned/provisional |
| Checkpoint M136 | pre-alpha checkpoint | M136 | Cross-Tool Dependency Execution | Planned/provisional |
| Checkpoint M137 | pre-alpha checkpoint | M137 | Autonomous Browser + Connector Combined Workflows | Planned/provisional |
| Checkpoint M138 | pre-alpha checkpoint | M138 | Autonomous Error Handling Guardrails | Planned/provisional |
| Checkpoint M139 | pre-alpha checkpoint | M139 | Autonomy Abuse/Loop Detection | Planned/provisional |
| Checkpoint M140 | pre-alpha checkpoint | M140 | Higher-Autonomy Red-Team Freeze | Planned/provisional |
| Checkpoint M141 | pre-alpha checkpoint | M141 | Multi-User Product Boundary | Planned/provisional |
| Checkpoint M142 | pre-alpha checkpoint | M142 | Alpha Privacy Review | Planned/provisional |
| Checkpoint M143 | pre-alpha checkpoint | M143 | Alpha UI and App Readiness | Planned/provisional |
| Checkpoint M144 | pre-alpha checkpoint | M144 | Plugin Marketplace Policy Draft | Planned/provisional |
| Checkpoint M145 | pre-alpha checkpoint | M145 | Enterprise/Pro Safety Modes | Planned/provisional |
| Checkpoint M146 | pre-alpha checkpoint | M146 | Billing/Plan Boundary, If Needed | Planned/provisional |
| Checkpoint M147 | pre-alpha checkpoint | M147 | Public Docs + Wiki Readiness | Planned/provisional |
| Checkpoint M148 | pre-alpha checkpoint | M148 | External Security Review | Planned/provisional |
| Checkpoint M149 | pre-alpha checkpoint | M149 | Alpha Release Candidate Freeze | Planned/provisional |
| v1.0.0-alpha | alpha | M150 | Ultimate AI Agent v1.0.0-alpha | Planned/provisional |

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

No M151+ extension is required by the v1.7.2 versioning repair. Beta begins
after the alpha UI and other alpha findings are ironed out through later
reviewed roadmap promotion. If future review finds missed M1-M100 work that
should not displace M101-M150, add a separate planned/provisional M151+
extension roadmap through a reviewed patch.
