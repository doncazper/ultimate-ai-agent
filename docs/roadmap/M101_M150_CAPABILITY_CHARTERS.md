# M101-M150 Capability Charters

Status: Active roadmap maintained through M150 and the v1.7.3 post-M150
local file-manager hardening baseline.

M101 is implemented/released as Mobile Sensor Contract Review. M102 is
implemented/released as Location Sensor, Off by Default. M103 is
implemented/released as Camera/Photos Metadata-Only Contract. Checkpoint M104
is implemented/released as Notification Planning, No Push Execution. Checkpoint
M105 is implemented/released as Background Task Contract, No Execution. v1.7.3
is the current package baseline after post-M150 local file-manager hardening.
Checkpoint M106 is implemented/released as
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
Deployment Mode Matrix. Checkpoint M119 is implemented/released as Production
Red-Team Harness. Checkpoint M120 is implemented/released as Production
Authority Readiness Review. Checkpoint M121 is implemented/released as Email
Connector Contract Refresh. Checkpoint M122 is implemented/released as Calendar
Connector Contract Refresh. Checkpoint M123 is implemented/released as Contacts
Connector Contract Refresh. Checkpoint M124 is implemented/released as Messages
Connector Contract Review. Checkpoint M125 is implemented/released as Connector
Read-Only Runtime. Checkpoint M126 is implemented/released as Connector
Approval Capture. Checkpoint M127 is implemented/released as Connector Write
Dry-Run Planner. Checkpoint M128 is implemented/released as Connector Write
Execution, Low-Risk Only. Checkpoint M129 is implemented/released as Connector
Audit + Revocation Hardening. Checkpoint M130 is implemented/released as
Connector Safety Freeze. Checkpoint M131 is implemented/released as Autonomy
Mode 4, Scoped Work Session. Checkpoint M132 is implemented/released as Autonomy
Mode 5, Trusted Recurring Workflow. Checkpoint M133 is implemented/released as
Long-Running Task Supervisor. Checkpoint M134 is implemented/released as Human
Checkpoint Scheduling. Checkpoint M135 is implemented/released as Autonomous
Recovery Planner. Checkpoint M136 is implemented/released as Cross-Tool
Dependency Execution. Checkpoint M137 is implemented/released as Autonomous
Browser + Connector Combined Workflows. Checkpoint M138 is implemented/released
as Autonomous Error Handling Guardrails. Checkpoint M139 is
implemented/released as Autonomy Abuse/Loop Detection. Checkpoint M140 is
implemented/released as Higher-Autonomy Red-Team Freeze. Checkpoint M141 is
implemented/released as Multi-User Product Boundary. Checkpoint M142 is
implemented/released as Alpha Privacy Review. Checkpoint M143 is
implemented/released as Alpha UI and App Readiness. Checkpoint M144 is
implemented/released as Plugin Marketplace Policy Draft. Checkpoint M145 is
implemented/released as Enterprise/Pro Safety Modes. Checkpoint M146 is
implemented/released as Billing/Plan Boundary. Checkpoint M147 is
implemented/released as Public Docs + Wiki Readiness. Checkpoint M148 is
implemented/released as External Security Review. Checkpoint M149 is
implemented/released as Alpha Release Candidate Freeze. M150 is
implemented/released as Ultimate AI Agent v1.0.0-alpha target acceptance.
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
labels instead of product SemVer tags. M150 records the product alpha target:
**v1.0.0-alpha**. It does not create a tag, publish a release, build or upload
artifacts, distribute externally, or begin beta. Beta begins only after the
alpha UI and supporting safety/product work are reviewed, accepted, and
explicitly promoted by a later roadmap patch. Do not rewrite, move, or reuse
existing tags.

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
| Checkpoint M119 | pre-alpha checkpoint | M119 | Production Red-Team Harness | Implemented/released |
| Checkpoint M120 | pre-alpha checkpoint | M120 | Production Authority Readiness Review | Implemented/released |
| Checkpoint M121 | pre-alpha checkpoint | M121 | Email Connector Contract Refresh | Implemented/released |
| Checkpoint M122 | pre-alpha checkpoint | M122 | Calendar Connector Contract Refresh | Implemented/released |
| Checkpoint M123 | pre-alpha checkpoint | M123 | Contacts Connector Contract Refresh | Implemented/released |
| Checkpoint M124 | pre-alpha checkpoint | M124 | Messages Connector Contract Review | Implemented/released |
| Checkpoint M125 | pre-alpha checkpoint | M125 | Connector Read-Only Runtime | Implemented/released |
| Checkpoint M126 | pre-alpha checkpoint | M126 | Connector Approval Capture | Implemented/released |
| Checkpoint M127 | pre-alpha checkpoint | M127 | Connector Write Dry-Run Planner | Implemented/released |
| Checkpoint M128 | pre-alpha checkpoint | M128 | Connector Write Execution, Low-Risk Only | Implemented/released |
| Checkpoint M129 | pre-alpha checkpoint | M129 | Connector Audit + Revocation Hardening | Implemented/released |
| Checkpoint M130 | pre-alpha checkpoint | M130 | Connector Safety Freeze | Implemented/released |
| Checkpoint M131 | pre-alpha checkpoint | M131 | Autonomy Mode 4, Scoped Work Session | Implemented/released |
| Checkpoint M132 | pre-alpha checkpoint | M132 | Autonomy Mode 5, Trusted Recurring Workflow | Implemented/released |
| Checkpoint M133 | pre-alpha checkpoint | M133 | Long-Running Task Supervisor | Implemented/released |
| Checkpoint M134 | pre-alpha checkpoint | M134 | Human Checkpoint Scheduling | Implemented/released |
| Checkpoint M135 | pre-alpha checkpoint | M135 | Autonomous Recovery Planner | Implemented/released |
| Checkpoint M136 | pre-alpha checkpoint | M136 | Cross-Tool Dependency Execution | Implemented/released |
| Checkpoint M137 | pre-alpha checkpoint | M137 | Autonomous Browser + Connector Combined Workflows | Implemented/released |
| Checkpoint M138 | pre-alpha checkpoint | M138 | Autonomous Error Handling Guardrails | Implemented/released |
| Checkpoint M139 | pre-alpha checkpoint | M139 | Autonomy Abuse/Loop Detection | Implemented/released |
| Checkpoint M140 | pre-alpha checkpoint | M140 | Higher-Autonomy Red-Team Freeze | Implemented/released |
| Checkpoint M141 | pre-alpha checkpoint | M141 | Multi-User Product Boundary | Implemented/released |
| Checkpoint M142 | pre-alpha checkpoint | M142 | Alpha Privacy Review | Implemented/released |
| Checkpoint M143 | pre-alpha checkpoint | M143 | Alpha UI and App Readiness | Implemented/released |
| Checkpoint M144 | pre-alpha checkpoint | M144 | Plugin Marketplace Policy Draft | Implemented/released |
| Checkpoint M145 | pre-alpha checkpoint | M145 | Enterprise/Pro Safety Modes | Implemented/released |
| Checkpoint M146 | pre-alpha checkpoint | M146 | Billing/Plan Boundary, If Needed | Implemented/released |
| Checkpoint M147 | pre-alpha checkpoint | M147 | Public Docs + Wiki Readiness | Implemented/released |
| Checkpoint M148 | pre-alpha checkpoint | M148 | External Security Review | Implemented/released |
| Checkpoint M149 | pre-alpha checkpoint | M149 | Alpha Release Candidate Freeze | Implemented/released |
| v1.0.0-alpha | alpha | M150 | Ultimate AI Agent v1.0.0-alpha | Implemented/released |

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
autonomy only after prior scoped, auditable safety foundations. M141 records the
multi-user product boundary as contract-only product-readiness work. M142
records alpha privacy review as contract-only product-readiness work. M143
records alpha UI and app readiness as contract-only product-readiness work. M144
records plugin marketplace policy draft as contract-only product-readiness work.
M145 records enterprise/pro safety modes as contract-only product-readiness
work. M146 records billing/plan boundary as contract-only product-readiness
work. M147 records public docs + wiki readiness as contract-only
product-readiness work. M148 records external security review as contract-only
product-readiness work. M149 records alpha release candidate freeze as
contract-only product-readiness work. M150 records the v1.0.0-alpha target as
contract-only product-readiness work.

No M151+ extension is required by the v1.7.3 hardening baseline. Beta begins
after the alpha UI and other alpha findings are ironed out through later
reviewed roadmap promotion. If future review finds missed M1-M100 work that
should not displace M101-M150, add a separate planned/provisional M151+
extension roadmap through a reviewed patch.
