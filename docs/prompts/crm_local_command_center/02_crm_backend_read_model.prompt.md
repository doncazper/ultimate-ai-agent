# Phase 02: Backend-Owned CRM Read Model M2

Branch: `codex/crm-02-read-model`

Commit: `Add backend-owned CRM read model`

Goal: Graduate CRM from fixture-only shell to backend-owned read-only CRM read
models owned by Python Agent Core.

Implement Python Core contracts:

- `CrmLocalCommandCenterReadModel`
- `CrmPersonReadModel`
- `CrmOrganizationReadModel`
- `CrmRelationshipReadModel`
- `CrmOpportunityReadModel`
- `CrmFollowUpReadModel`
- `CrmTimelineEventReadModel`
- `CrmSmartListReadModel`
- `CrmPipelineReadModel`
- CRM proof/evidence refs

Routes:

- `GET /control-center/crm/summary`
- `GET /control-center/crm/relationships`
- `GET /control-center/crm/timeline`
- `GET /control-center/crm/follow-ups`
- `GET /control-center/crm/pipelines`
- `GET /control-center/crm/smart-lists`

CLI:

- `scripts/dev/uaa_crm.py inspect-summary`
- `scripts/dev/uaa_crm.py inspect-relationships`
- `scripts/dev/uaa_crm.py inspect-follow-ups`
- `scripts/dev/uaa_crm.py inspect-pipelines`

Rules:

- Read-only.
- Safe refs only.
- No raw private contact details.
- No connector reads or writes.
- No CRM mutation.
- Control Center may render but cannot own durable CRM truth.

Verification:

- focused CRM read-model pytest
- route tests
- CLI tests
- OpenAPI verifier
- release-surface verifier if `/crm` release surface changes
- `git diff --check`
