# M101-M150 Capability Charters

Status: Active roadmap maintained through v1.7.0 after the accepted M103
baseline.

M101 is implemented/released as Mobile Sensor Contract Review. M102 is
implemented/released as Location Sensor, Off by Default. M103 is
implemented/released as Camera/Photos Metadata-Only Contract. M104-M150 remain
planned/provisional. Future work must continue the authority-tier model:

Capability exists -> disabled by default -> dry-run first -> limited allowlist
-> explicit approval -> scoped autonomy window -> audit/replay -> revocation ->
only then broader autonomy.

There is no global "be autonomous" switch, no jump from Mode 0 to broad
autonomy, and no production authority in this roadmap. Every milestone remains
planned/provisional until implemented, validated, pushed, strictly reviewed, and
accepted Green.

| Version | Milestone | Title | Status |
| --- | --- | --- | --- |
| v1.5.0 | M101 | Mobile Sensor Contract Review | Implemented/released |
| v1.6.0 | M102 | Location Sensor, Off by Default | Implemented/released |
| v1.7.0 | M103 | Camera/Photos Metadata-Only Contract | Implemented/released |
| v1.8.0 | M104 | Notification Planning, No Push Execution | Planned/provisional |
| v1.9.0 | M105 | Background Task Contract, No Execution | Planned/provisional |
| v1.10.0 | M106 | Mobile Background Read-Only Status Sync | Planned/provisional |
| v1.11.0 | M107 | Mobile Approval Renewal UX | Planned/provisional |
| v1.12.0 | M108 | Mobile Kill Switch + Revocation | Planned/provisional |
| v1.13.0 | M109 | Mobile Sensor Audit Ledger | Planned/provisional |
| v1.14.0 | M110 | Mobile Sensor Hardening Freeze | Planned/provisional |
| v1.15.0 | M111 | Production Threat Model | Planned/provisional |
| v1.16.0 | M112 | User/Workspace Identity Model | Planned/provisional |
| v1.17.0 | M113 | Secrets Boundary + Credential Vault Contract | Planned/provisional |
| v1.18.0 | M114 | Account Connector Contract Review | Planned/provisional |
| v1.19.0 | M115 | Production Audit Retention Policy | Planned/provisional |
| v1.20.0 | M116 | Role-Based Authority Model | Planned/provisional |
| v1.21.0 | M117 | Remote Agent Coordination Contract | Planned/provisional |
| v1.22.0 | M118 | Deployment Mode Matrix | Planned/provisional |
| v1.23.0 | M119 | Production Red-Team Harness | Planned/provisional |
| v1.24.0 | M120 | Production Authority Readiness Review | Planned/provisional |
| v1.25.0 | M121 | Email Connector Contract Refresh | Planned/provisional |
| v1.26.0 | M122 | Calendar Connector Contract Refresh | Planned/provisional |
| v1.27.0 | M123 | Contacts Connector Contract Refresh | Planned/provisional |
| v1.28.0 | M124 | Messages Connector Contract Review | Planned/provisional |
| v1.29.0 | M125 | Connector Read-Only Runtime | Planned/provisional |
| v1.30.0 | M126 | Connector Approval Capture | Planned/provisional |
| v1.31.0 | M127 | Connector Write Dry-Run Planner | Planned/provisional |
| v1.32.0 | M128 | Connector Write Execution, Low-Risk Only | Planned/provisional |
| v1.33.0 | M129 | Connector Audit + Revocation Hardening | Planned/provisional |
| v1.34.0 | M130 | Connector Safety Freeze | Planned/provisional |
| v1.35.0 | M131 | Autonomy Mode 4, Scoped Work Session | Planned/provisional |
| v1.36.0 | M132 | Autonomy Mode 5, Trusted Recurring Workflow | Planned/provisional |
| v1.37.0 | M133 | Long-Running Task Supervisor | Planned/provisional |
| v1.38.0 | M134 | Human Checkpoint Scheduling | Planned/provisional |
| v1.39.0 | M135 | Autonomous Recovery Planner | Planned/provisional |
| v1.40.0 | M136 | Cross-Tool Dependency Execution | Planned/provisional |
| v1.41.0 | M137 | Autonomous Browser + Connector Combined Workflows | Planned/provisional |
| v1.42.0 | M138 | Autonomous Error Handling Guardrails | Planned/provisional |
| v1.43.0 | M139 | Autonomy Abuse/Loop Detection | Planned/provisional |
| v1.44.0 | M140 | Higher-Autonomy Red-Team Freeze | Planned/provisional |
| v1.45.0 | M141 | Multi-User Product Boundary | Planned/provisional |
| v1.46.0 | M142 | External Beta Privacy Review | Planned/provisional |
| v1.47.0 | M143 | App Store / Public Beta Readiness | Planned/provisional |
| v1.48.0 | M144 | Plugin Marketplace Policy Draft | Planned/provisional |
| v1.49.0 | M145 | Enterprise/Pro Safety Modes | Planned/provisional |
| v1.50.0 | M146 | Billing/Plan Boundary, If Needed | Planned/provisional |
| v1.51.0 | M147 | Public Docs + Wiki Readiness | Planned/provisional |
| v1.52.0 | M148 | External Security Review | Planned/provisional |
| v1.53.0 | M149 | Release Candidate Freeze | Planned/provisional |
| v1.54.0 | M150 | Ultimate AI Agent Beta 1 | Planned/provisional |

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
multi-user, beta, marketplace, billing, public docs, security review, and beta
freeze readiness.

No M151+ extension is required by the v1.7.0 M103 release. If future
review finds missed M1-M100 work that should not displace M101-M150, add a
separate planned/provisional M151+ extension roadmap through a reviewed patch.
