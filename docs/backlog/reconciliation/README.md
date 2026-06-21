# Morning Reconciliation Artifact Instances

Status: active UAA-P1-061 artifact instance ledger

This folder stores safe JSON reconciliation artifacts for documented conveyor
runs. Each artifact is created from
`docs/backlog/MORNING_RECONCILIATION_TEMPLATE.json` and checked by
`scripts/verify_morning_reconciliation_artifact.py`.

Allowed content:

- safe recommendation refs
- milestone or task refs
- short redacted summaries
- reason codes
- evidence refs to docs, tests, scripts, reports, commits, boards, or roadmaps

Forbidden content:

- raw prompt content
- raw response content
- raw provider payloads
- raw local paths
- raw logs
- usernames, hostnames, serials, or environment dumps
- credential material or private content

The ledger is a memory aid and cleanup checkpoint only. It does not create
milestones, approve runtime authority, accept failures, or mark product work
shipped without separate evidence.
