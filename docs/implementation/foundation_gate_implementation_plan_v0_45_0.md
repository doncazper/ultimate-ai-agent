# Foundation Gate Implementation Plan v0.45.0

Status: Active for v0.45.0 / M41 - Local Prototype Safety Freeze.

M41 adds Foundation Gate coverage for the local prototype safety freeze.

Gate coverage:

- M41 local prototype safety freeze docs exist.
- Browser smoke review is local-only.
- Local prototype docs say localhost-only.
- Local prototype docs say review-only.
- Local prototype docs say mock/non-authoritative for sample data.
- Local prototype docs deny raw file browsing.
- Local prototype docs deny raw file export.
- Local prototype docs deny full-file reads.
- Local prototype docs deny arbitrary caller-selected roots.
- Local prototype docs deny shell/subprocess.
- Local prototype docs deny unrestricted network tools.
- Local prototype docs deny provider/model calls as authority.
- Local prototype docs deny background workers.
- Local prototype docs deny mobile sensors.
- Local prototype docs deny plugin enablement.
- Local prototype docs deny production authority.
- Local prototype docs deny unreviewed memory writes.
- Local prototype docs deny automatic context injection.
- Local prototype docs deny raw prompt/provider payload exposure.
- Local prototype docs deny credentials/cookie handling.
- Local prototype docs deny remote execution.
- Local prototype docs deny browser automation execution.
- Approval refs are not authority.
- OpenAPI path count remains 75.
- No new backend routes are added.
- M42 remains future.

This plan adds no runtime capability, backend routes, dependencies, mobile work,
browser automation execution, model calls, memory writes, context injection, or
production authority.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package requires
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities before it can be trusted by a runtime boundary.
