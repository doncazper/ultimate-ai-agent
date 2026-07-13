# ECO-000 Application Ecosystem Threat Model

Status: accepted design threat model. ECO-000 stores no private app data and
adds no runtime route or authority.

## Assets and trust boundaries

| Asset | Boundary | Required future protection | Fail-closed condition |
|---|---|---|---|
| Calendar/Event values | Encrypted private data plane | Workspace keys, time-zone-safe versions, export/delete controls | Locked key, corrupt schema, uncertain workspace |
| Task/Commitment values | Encrypted private data plane | Exact owner refs, versions, archive/delete, no board copies | Missing owner/version or duplicate canonical task |
| CRM/private relationship data | Restricted workspace plane | Default exclusion from transcripts, enrichment, models, wallboards, shared search | Scope or exclusion uncertainty |
| Messages/meeting/transcript content | Highest-sensitivity source plane | Explicit retention, selected-source access, bounded context, no Evidence copies | Missing consent, retention, or destination eligibility |
| Lists/household data | Private organizer plane | Single-user isolation until shared-space contracts exist | Any implicit sharing or public display uncertainty |
| Links/search indexes | Derived encrypted plane | Source privacy inheritance, workspace partitioning, deletion/rebuild | Orphan link, stale ACL, plaintext index, corrupt rebuild |
| Receipts/evidence/metrics | Redacted governance plane | Safe refs/hashes only, bounded summaries, redaction scanning | Raw value or sensitive identifier present |
| Backups/exports | Separate protected boundary | Encryption, scoped manifests, expiry/deletion status, restore preview | Key unavailable, unknown scope, unverified integrity |

## Threats and controls

| Threat | Example failure | Required control and acceptance evidence |
|---|---|---|
| Workspace isolation bypass | Cross-app search returns a private relationship in a work workspace | Workspace/privacy bound refs, query scope mandatory, adversarial cross-workspace tests |
| Entity-link leakage | A private relationship links to a visible Task and reveals context | Restricted links cannot cross workspaces; projections show a blocked/private placeholder only |
| Duplicate truth | CRM copies Event or Task state and diverges | Unique ownership registry; projections reject domain authority and copied state |
| Source retention escape | Deleted message remains in context, index, or backup claim | Exact deletion graph, index rebuild, cache purge, backup-expiry posture, content-free receipts |
| Transcript overreach | Meeting transcript enters Evidence, memory, or model context by default | Transcript-specific high-sensitivity eligibility; default deny; source refs only outside source plane |
| Import poisoning | Malformed or adversarial import changes ownership or authority | Preview-only parser, schema/version bounds, untrusted-content marking, exact operator approval for commit |
| Export over-disclosure | Support export includes contact/task/message values | Separate private encrypted export and redacted support export; field allowlist and scan |
| Backup disclosure | Database is encrypted but WAL/backup/index is plaintext | Encryption proof for database, WAL, journal, temp, index, backup; plaintext scanning |
| Notification disclosure | Lock-screen or wallboard reveals private title or relationship | Privacy-tiered templates, locked-state redaction, view-only wallboard, synthetic visual tests |
| Search side channel | Counts/timing reveal existence of excluded private records | Partitioned indexes, constant bounded response shapes where practical, no excluded counts |
| ChangeSet confused deputy | One approval is treated as authority for every operation | Exact per-operation policy/approval/lease/resource evaluation at future pre-start boundary |
| False external atomicity | Local task applies, external event fails, UI says all rolled back | External-compensating posture, per-operation terminal states, partial/recovery UI |
| Unsafe compensation | Automatic delete/send attempts to undo a failed external action | Compensation is a new exact governed operation, never assumed or silently executed |
| Log/diagnostic leakage | Crash report contains task title, person, message, or path | Governance-plane allowlists, safe refs, redaction scanner, bounded error codes |
| Screenshot/visual leakage | Visual regression captures real contacts/calendar | Synthetic datasets only; asset manifest records dataset ref and review status |
| CLI leakage | Search/inspect commands print private raw values by default | Human-readable bounded summaries, explicit unlock/scope, no raw JSON primary, no-store posture |
| Model authority escalation | Suggested change is treated as fact or approval | Model output remains cited proposal; canonical truth and authority flags are rejected |
| Memory authority escalation | Reviewed recall silently changes CRM/Task/Event | Memory can propose a correction with citations; owning app mutation remains exact and reviewed |
| Future collaboration widening | Shared board grants access to linked private CRM record | Sharing a projection never broadens source visibility; explicit identity/role/consent model required |

## Private Relationships and Dating floor

These workspaces default to: no transcript ingestion, no enrichment, no cloud
model disclosure, no wallboard detail, no shared search, no cross-workspace
links, no background automation, and no export inclusion. A future exact
milestone may relax one dimension only with consent, policy, receipt, deletion,
and operator-visible scope proof.

## Required ECO-001 threat-review gates

- Selected dependency and key-lifecycle evidence.
- Database/WAL/journal/temp/index/backup plaintext scans.
- Corrupt, locked, unsupported-version, low-disk, interrupted-migration, lost-key,
  restore, rekey, and deletion drills.
- Workspace/query/link isolation property tests.
- Redacted logging, metrics, crash, CLI, screenshot, and support-export tests.
- External operations remain absent; ChangeSet storage still cannot mint authority.
