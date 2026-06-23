# Portfolio Screenshots

Status: static visual-test snapshot gallery
Scope: documentation-only portfolio preview

These images are existing Control Center visual regression snapshots copied
from `apps/control-center/tests/visual/__snapshots__/desktop/` into a
portfolio-friendly docs asset folder.

They are sanitized visual-test snapshots of the local Control Center shell.
They are not production screenshots, public beta evidence, public distribution
evidence, or claims that every displayed workflow is complete. Several views
intentionally show mock/degraded fallback, read-only posture, blocked
authority, and safe-ref-only states.

## Gallery

### Setup Assistant

Dry-run setup posture, model-choice preview, receipt/rollback refs, and blocked
installer authority.

![Setup Assistant](assets/control-center-setup.png)

### Today

Founder Loop overview showing Action Inbox, Plans, Morning Briefing, Memory
Review, and explicit blocked states.

![Today](assets/control-center-today.png)

### Action Inbox

Review queue posture for safe Action proposals. Generic execution and external
authority remain blocked unless backend-owned exact scope and approval exist.

![Action Inbox](assets/control-center-actions.png)

### Evidence

Safe-ref Evidence view with redacted summaries. Source bodies, raw logs,
credentials, provider payloads, and private content are not displayed.

![Evidence](assets/control-center-evidence.png)

### Memory

Recall-only memory viewer that keeps canonical sources and governed evidence
above memory recall.

![Memory](assets/control-center-memory.png)

## Snapshot Boundaries

- Static visual-test snapshots only.
- No backend route, frontend control, runtime authority, connector runtime, or
  product behavior is added by this gallery.
- Mock/degraded UI state remains mock/degraded UI state.
- Memory is recall, not truth or authority.
- Approval refs are identifiers until exact backend scope is validated.
- Evidence uses safe refs and redacted summaries only.

