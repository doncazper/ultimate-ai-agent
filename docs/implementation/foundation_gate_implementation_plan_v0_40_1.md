# Foundation Gate Implementation Plan v0.40.1

Status: active Foundation Gate plan for v0.40.1.

v0.40.1 hardens M36 CCC File Review Surface, Review-Only as a frontend-only
display surface.

## Gate Coverage

Foundation Gate must cover:

- M36 file review surface exists.
- M36 file review docs exist.
- `/files/review` route exists in the Control Center shell.
- mock data is visibly mock and non-authoritative.
- redacted preview display exists.
- redaction summary display exists.
- exact binding refs are displayed.
- safe refs only are displayed.
- private path-shaped refs are rejected by static verification.
- raw path-shaped labels and traversal fragments are rejected by static
  verification.
- no mutating request is made by the file review surface.
- review-only decision status is displayed.
- approval gate contract status is displayed.
- receipt plan metadata is displayed.
- no approve, deny, submit, save, mark-reviewed, export, download, copy-raw,
  file picker, browse, upload, root selector, context, memory, execute, tool,
  or model-call controls exist.
- no backend routes are added.
- OpenAPI path count remains 74.
- M37 remains planned/provisional.
- M38 remains planned/provisional.

## Blocked Drift

Gate must fail on approval capture, approval persistence, raw file display,
raw file storage, full-file read output, unsafe ref prefixes, private path
refs, traversal refs, mutating file-review requests, file picker/browser/upload
root selector, export/download/copy-raw controls, context proposal, context
injection, memory writes, execution/tool controls, backend route drift,
dependency drift, M37 work, M38 work, or production authority.

## No New Authority

M36 adds no backend API authority. The Control Center remains a display and
preview shell. Python Agent Core remains the authority boundary.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package requires
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be trusted by a runtime boundary.
